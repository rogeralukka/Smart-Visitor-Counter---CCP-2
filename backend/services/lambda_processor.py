"""
Virtual AWS Lambda Serverless Processor.
Function Name: ProcessVisitorCounter
Runtime: Python 3.11 (Architecture: arm64)
Memory: 128 MB
Execution Timeout: 3 seconds
"""

import time
from datetime import datetime
from typing import Dict, Any
from backend.services.dynamodb_store import dynamodb_store
from backend.events import broadcaster

class VirtualLambdaProcessor:
    def __init__(self):
        self.function_name = "ProcessVisitorCounter"
        self.arn = "arn:aws:lambda:us-east-1:218062175263:function:ProcessVisitorCounter"
        self.total_invocations = 0
        self.total_errors = 0
        self.average_duration_ms = 18.2
        self.last_execution_log = ""

    def process_event(self, iot_event: dict) -> dict:
        t_start = time.time()
        self.total_invocations += 1

        payload = iot_event.get("payload", {})
        device_id = payload.get("device_id", "ESP32-VISITOR-NODE-01")
        count_delta = payload.get("count_delta", 1)

        # Basic input validation
        if count_delta <= 0 or count_delta > 100:
            self.total_errors += 1
            return {
                "statusCode": 400,
                "body": {"error": "Invalid count delta"}
            }

        # Atomic increment in DynamoDB
        result_event = dynamodb_store.increment(device_id=device_id, count_delta=count_delta)

        duration = round((time.time() - t_start) * 1000 + 12.0, 2)  # realistic Lambda exec time
        self.average_duration_ms = round((self.average_duration_ms * 0.9) + (duration * 0.1), 2)
        
        self.last_execution_log = (
            f"START RequestId: {result_event['verification_hash']}\n"
            f"Version: $LATEST\n"
            f"Incrementing counter for {device_id} by {count_delta}. New total: {result_event['visitor_number']}\n"
            f"END RequestId: {result_event['verification_hash']}\n"
            f"REPORT Duration: {duration} ms Billed Duration: 100 ms Memory Size: 128 MB Max Memory Used: 48 MB"
        )

        response = {
            "statusCode": 200,
            "body": {
                "message": "Visitor counted successfully",
                "visitor_event": result_event,
                "current_state": dynamodb_store.get_state(),
                "lambda_meta": {
                    "function": self.function_name,
                    "duration_ms": duration,
                    "billed_ms": 100,
                    "memory_mb": 128
                }
            }
        }

        # Dispatch real-time SSE event to connected dashboard clients
        broadcaster.broadcast_sync("visitor_counted", response["body"])

        return response

    def get_metrics(self) -> dict:
        return {
            "function_name": self.function_name,
            "arn": self.arn,
            "invocations": self.total_invocations,
            "errors": self.total_errors,
            "avg_duration_ms": self.average_duration_ms,
            "last_log": self.last_execution_log
        }

lambda_processor = VirtualLambdaProcessor()
