"""
Cloud Architecture & Pipeline Status Routes.
Returns live health metrics for AWS IoT Core, Lambda, DynamoDB, and S3.
"""

from fastapi import APIRouter
from backend.services.iot_core import iot_core
from backend.services.lambda_processor import lambda_processor
from backend.services.dynamodb_store import dynamodb_store
from backend.services.s3_store import s3_store

router = APIRouter(prefix="/api/cloud", tags=["AWS Cloud Architecture"])

@router.get("/pipeline", summary="Get end-to-end cloud pipeline diagnostics")
def get_pipeline_diagnostics():
    return {
        "status": "HEALTHY",
        "region": "us-east-1",
        "pipeline_nodes": [
            {
                "tier": "1. Perception Edge",
                "service": "ESP32 MCU + Tactile Button",
                "gpio": "GPIO 14 (Pull-Up)",
                "status": "ONLINE",
                "device_id": "ESP32-VISITOR-NODE-01"
            },
            {
                "tier": "2. Ingestion Broker",
                "service": "AWS IoT Core",
                "topic": iot_core.topic,
                "qos": iot_core.qos,
                "status": "ONLINE",
                "total_messages": iot_core.total_messages_received
            },
            {
                "tier": "3. Serverless Compute",
                "service": "AWS Lambda",
                "function": lambda_processor.function_name,
                "avg_duration": f"{lambda_processor.average_duration_ms} ms",
                "status": "ACTIVE",
                "invocations": lambda_processor.total_invocations
            },
            {
                "tier": "4. NoSQL Persistence",
                "service": "Amazon DynamoDB",
                "table": dynamodb_store.table_name,
                "key": "counter_id = LIBRARY-MAIN-TURNSTILE",
                "status": "ACTIVE",
                "total_counted": dynamodb_store.total_count
            },
            {
                "tier": "5. Static Dashboard",
                "service": "Amazon S3",
                "bucket": s3_store.bucket_name,
                "endpoint": s3_store.website_endpoint,
                "status": "HOSTED",
                "objects": s3_store.static_files
            }
        ],
        "services": {
            "iot_core": iot_core.get_metrics(),
            "lambda": lambda_processor.get_metrics(),
            "s3": s3_store.get_metrics()
        }
    }
