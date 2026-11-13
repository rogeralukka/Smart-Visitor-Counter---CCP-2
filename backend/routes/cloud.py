"""
Cloud Architecture & Pipeline Status Routes.
Returns live health metrics for AWS IoT Core, Lambda, DynamoDB, and S3.
Supports dynamic credential updates from AWS Academy Learner Lab console.
"""

from fastapi import APIRouter
from typing import Dict, Any, Optional
from backend.services.iot_core import iot_core
from backend.services.lambda_processor import lambda_processor
from backend.services.dynamodb_store import dynamodb_store
from backend.services.s3_store import s3_store

router = APIRouter(prefix="/api/cloud", tags=["AWS Cloud Architecture"])

@router.get("/pipeline", summary="Get end-to-end cloud pipeline diagnostics")
def get_pipeline_diagnostics():
    return {
        "status": "HEALTHY",
        "region": dynamodb_store.region,
        "aws_connected": dynamodb_store.is_aws_connected,
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
                "key": "device_id + timestamp (plus aggregate summary)",
                "status": "ACTIVE (AWS CONNECTED)" if dynamodb_store.is_aws_connected else "ACTIVE (LOCAL CACHE)",
                "total_counted": dynamodb_store.total_count,
                "aws_connected": dynamodb_store.is_aws_connected
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
            "s3": s3_store.get_metrics(),
            "dynamodb": {
                "table": dynamodb_store.table_name,
                "total_count": dynamodb_store.total_count,
                "aws_connected": dynamodb_store.is_aws_connected
            }
        }
    }

@router.post("/credentials", summary="Update AWS Academy temporary credentials on the fly")
def update_credentials(payload: Dict[str, str]) -> Dict[str, Any]:
    """
    Parses and applies AWS credentials pasted directly from AWS Academy console.
    Accepts raw CLI block or individual fields.
    """
    raw_text = payload.get("raw", "")
    access_key = payload.get("aws_access_key_id", "")
    secret_key = payload.get("aws_secret_access_key", "")
    session_token = payload.get("aws_session_token", "")
    region = payload.get("region", "us-east-1")

    if raw_text:
        for line in raw_text.splitlines():
            line = line.strip()
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip().lower()
                v = v.strip()
                if "access_key_id" in k:
                    access_key = v
                elif "secret_access_key" in k:
                    secret_key = v
                elif "session_token" in k:
                    session_token = v
                elif "region" in k:
                    region = v

    if not access_key or not secret_key:
        return {
            "status": "error",
            "message": "Missing aws_access_key_id or aws_secret_access_key"
        }

    success, message = dynamodb_store.reconfigure(
        access_key=access_key,
        secret_key=secret_key,
        session_token=session_token,
        region=region
    )

    return {
        "status": "success" if success else "error",
        "aws_connected": success,
        "message": message,
        "table": dynamodb_store.table_name,
        "region": region
    }
