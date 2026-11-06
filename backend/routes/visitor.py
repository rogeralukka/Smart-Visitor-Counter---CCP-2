"""
Visitor Counter API Routes.
Exposes endpoints for button press ingestion, state retrieval, burst simulation, and SSE stream.
"""

import asyncio
from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
from backend.services.iot_core import iot_core
from backend.services.lambda_processor import lambda_processor
from backend.services.dynamodb_store import dynamodb_store
from backend.events import broadcaster

router = APIRouter(prefix="/api", tags=["Visitor Counter"])

class ButtonPressPayload(BaseModel):
    device_id: Optional[str] = Field("ESP32-VISITOR-NODE-01", description="Device ID of edge MCU")
    count_delta: Optional[int] = Field(1, ge=1, le=100, description="Number of visitors entering")
    gpio_pin: Optional[int] = Field(14, description="GPIO pin of push button")
    press_duration_ms: Optional[int] = Field(85, description="Physical button contact duration in ms")

@router.post("/button/press", summary="Simulate physical button press on ESP32")
async def handle_button_press(payload: ButtonPressPayload):
    """
    Simulates the physical edge press:
    1. Ingests packet via simulated AWS IoT Core MQTT broker
    2. Triggers AWS Lambda processor
    3. Executes DynamoDB atomic increment
    4. Pushes update to all connected dashboard SSE streams
    """
    mqtt_packet = iot_core.publish_message(payload.dict())
    lambda_response = lambda_processor.process_event(mqtt_packet)
    return lambda_response

@router.post("/visitor/burst", summary="Simulate a rush-hour group entrance")
async def handle_burst_entrance(count: int = 10):
    """Simulates a group of visitors entering through the turnstile."""
    payload = {
        "device_id": "ESP32-VISITOR-NODE-01",
        "count_delta": min(count, 50),
        "gpio_pin": 14,
        "press_duration_ms": 250
    }
    mqtt_packet = iot_core.publish_message(payload)
    return lambda_processor.process_event(mqtt_packet)

@router.get("/visitor/state", summary="Fetch current live visitor counts and analytics")
async def get_visitor_state():
    return dynamodb_store.get_state()

@router.post("/visitor/reset", summary="Reset visitor counter for demonstration")
async def reset_counter():
    dynamodb_store.reset()
    state = dynamodb_store.get_state()
    await broadcaster.broadcast("visitor_reset", state)
    return {"status": "success", "message": "Visitor counter reset", "state": state}

@router.get("/stream", summary="Server-Sent Events (SSE) live data stream")
async def sse_stream(request: Request):
    q = broadcaster.subscribe()

    async def event_generator():
        try:
            # Send initial state snapshot immediately upon connection
            init_data = {"type": "init", "state": dynamodb_store.get_state()}
            yield f"event: init\ndata: {dict_to_json(init_data)}\n\n"

            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield msg
                except asyncio.TimeoutError:
                    # Heartbeat keep-alive
                    yield ": keep-alive\n\n"
        finally:
            broadcaster.unsubscribe(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

def dict_to_json(d: dict) -> str:
    import json
    return json.dumps(d)
