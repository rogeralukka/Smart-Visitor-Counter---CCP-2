"""
Export Routes for Visitor Counter.
Generates CSV and JSON reports of visitor events.
"""

import io
import csv
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, Response
from backend.services.dynamodb_store import dynamodb_store

router = APIRouter(prefix="/api/export", tags=["Export Reports"])

@router.get("/csv", summary="Export visitor logs as CSV")
def export_csv():
    state = dynamodb_store.get_state()
    events = state.get("recent_events", [])
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Visitor #", "Today #", "Timestamp (UTC)", "Device ID", "Location", "Verification Hash"])
    
    for ev in events:
        writer.writerow([
            ev.get("visitor_number", ""),
            ev.get("today_visitor_number", ""),
            ev.get("timestamp", ""),
            ev.get("device_id", ""),
            ev.get("location", ""),
            ev.get("verification_hash", "")
        ])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=visitor_counter_log.csv"}
    )

@router.get("/json", summary="Export full state snapshot as JSON")
def export_json():
    state = dynamodb_store.get_state()
    json_bytes = json.dumps(state, indent=2).encode("utf-8")
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=visitor_counter_snapshot.json"}
    )
