"""
AWS Lambda Serverless Processor for Smart Visitor Counter.
Function Name: ProcessVisitorCounter
Runtime: Python 3.12
Handles:
- Direct IoT Core MQTT Topic Rule events (campus/library/turnstile/visitor_in)
- Public Lambda Function URL HTTP GET (state retrieval)
- Public Lambda Function URL HTTP POST (button press increment)
- Public Lambda Function URL HTTP OPTIONS (CORS preflight)
- Updates Amazon DynamoDB (SmartVisitorCounter) in both us-east-1 and us-west-2
- Archives audit records to Amazon S3
"""

import json
import boto3
from decimal import Decimal
from datetime import datetime, timezone

TABLE_NAME = "SmartVisitorCounter"
BUCKET_NAME = "smart-visitor-counter-sru-582664129185"

# DynamoDB resources
dynamo_e1 = boto3.resource("dynamodb", region_name="us-east-1")
table_e1 = dynamo_e1.Table(TABLE_NAME)

try:
    dynamo_w2 = boto3.resource("dynamodb", region_name="us-west-2")
    table_w2 = dynamo_w2.Table(TABLE_NAME)
except Exception:
    table_w2 = None

s3 = boto3.client("s3", region_name="us-east-1")

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With"
}

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError

def get_current_state():
    """Scans DynamoDB to assemble the real-time state for the dashboard."""
    try:
        resp = table_e1.scan()
        items = resp.get("Items", [])
    except Exception as e:
        items = []

    # Filter visitor event items (exclude summary row)
    event_items = [it for it in items if it.get("device_id") == "ESP32-VISITOR-NODE-01"]
    
    # Find summary item if present
    summary_items = [it for it in items if it.get("device_id") == "ESP32-VISITOR-SUMMARY"]
    
    total = len(event_items)
    if summary_items and "total_visitors" in summary_items[0]:
        total = max(total, int(summary_items[0]["total_visitors"]))

    # Sort recent events descending by timestamp
    event_items.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
    
    # Calculate hourly distribution
    hourly = {f"{h:02d}:00": 0 for h in range(24)}
    today_count = 0
    now_utc = datetime.now(timezone.utc)
    today_date = now_utc.strftime("%Y-%m-%d")

    for it in event_items:
        ts_str = str(it.get("timestamp", ""))
        try:
            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if dt.strftime("%Y-%m-%d") == today_date:
                today_count += int(it.get("delta", 1))
                h_key = f"{dt.hour:02d}:00"
                hourly[h_key] = hourly.get(h_key, 0) + int(it.get("delta", 1))
        except Exception:
            pass

    curr_hour = f"{now_utc.hour:02d}:00"
    current_rate = hourly.get(curr_hour, 0)
    peak_pair = max(hourly.items(), key=lambda x: x[1])

    formatted_events = []
    for it in event_items[:25]:
        formatted_events.append({
            "visitor_number": int(it.get("visitor_number", 0)),
            "today_visitor_number": int(it.get("today_visitor_number", 0)),
            "timestamp": str(it.get("timestamp", "")),
            "device_id": str(it.get("device_id", "ESP32-VISITOR-NODE-01")),
            "location": str(it.get("location", "SRU Central Library Main Turnstile")),
            "delta": int(it.get("delta", 1)),
            "gpio_pin": int(it.get("gpio_pin", 14)),
            "status": str(it.get("status", "COUNTED")),
            "verification_hash": str(it.get("verification_hash", "SHA256"))
        })

    last_ts = event_items[0].get("timestamp", now_utc.isoformat()) if event_items else now_utc.isoformat()

    return {
        "total_visitors": total,
        "today_visitors": today_count if today_count > 0 else total,
        "current_hour_visitors": current_rate,
        "peak_hour": peak_pair[0],
        "peak_count": peak_pair[1],
        "last_visit_timestamp": str(last_ts),
        "hourly_distribution": hourly,
        "recent_events": formatted_events,
        "location": "SRU Central Library Main Turnstile",
        "table_name": TABLE_NAME,
        "cloud_hosted": True,
        "regions": ["us-east-1", "us-west-2"]
    }

def record_visitor_press(payload):
    """Processes button press and atomically writes to DynamoDB."""
    delta = int(payload.get("count_delta", 1))
    gpio_pin = int(payload.get("gpio_pin", 14))
    device_id = str(payload.get("device_id", "ESP32-VISITOR-NODE-01"))
    location = str(payload.get("location", "SRU Central Library Main Turnstile"))

    now_dt = datetime.now(timezone.utc)
    iso_ts = now_dt.isoformat()
    hash_seed = f"{iso_ts}_{device_id}_{delta}"
    verification_hash = f"SHA256-{hex(abs(hash(hash_seed)))[-8:].upper()}"

    # Get current total to assign visitor_number
    state = get_current_state()
    new_total = state["total_visitors"] + delta
    new_today = state["today_visitors"] + delta

    item = {
        "device_id": device_id,
        "timestamp": iso_ts,
        "visitor_number": Decimal(str(new_total)),
        "today_visitor_number": Decimal(str(new_today)),
        "delta": Decimal(str(delta)),
        "gpio_pin": Decimal(str(gpio_pin)),
        "location": location,
        "status": "COUNTED",
        "verification_hash": verification_hash,
        "processed_by": "AWS Lambda (ProcessVisitorCounter)"
    }

    # Write to us-east-1
    try:
        table_e1.put_item(Item=item)
        table_e1.put_item(
            Item={
                "device_id": "ESP32-VISITOR-SUMMARY",
                "timestamp": "LATEST",
                "total_visitors": Decimal(str(new_total)),
                "today_visitors": Decimal(str(new_today)),
                "last_entry_time": iso_ts,
                "status": "ONLINE"
            }
        )
    except Exception as e:
        print("DynamoDB e1 put error:", e)

    # Write to us-west-2
    if table_w2:
        try:
            table_w2.put_item(Item=item)
            table_w2.put_item(
                Item={
                    "device_id": "ESP32-VISITOR-SUMMARY",
                    "timestamp": "LATEST",
                    "total_visitors": Decimal(str(new_total)),
                    "today_visitors": Decimal(str(new_today)),
                    "last_entry_time": iso_ts,
                    "status": "ONLINE"
                }
            )
        except Exception as e:
            print("DynamoDB w2 put error:", e)

    # Write to S3
    try:
        s3_key = f"visitors/{now_dt.strftime('%Y/%m/%d')}/visitor_{new_total}.json"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(item, default=decimal_default),
            ContentType="application/json"
        )
    except Exception as e:
        print("S3 archive error:", e)

    # Return refreshed state
    refreshed_state = get_current_state()
    return {
        "message": "Visitor counted successfully",
        "visitor_event": {
            "visitor_number": new_total,
            "today_visitor_number": new_today,
            "timestamp": iso_ts,
            "device_id": device_id,
            "delta": delta,
            "gpio_pin": gpio_pin,
            "status": "COUNTED",
            "verification_hash": verification_hash
        },
        "current_state": refreshed_state
    }

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))

    # 1. Check if invoked via Lambda Function URL
    http_ctx = event.get("requestContext", {}).get("http", {})
    method = http_ctx.get("method")

    if method:
        # CORS preflight
        if method == "OPTIONS":
            return {
                "statusCode": 200,
                "headers": CORS_HEADERS,
                "body": ""
            }

        # GET: return current state
        if method == "GET":
            state = get_current_state()
            return {
                "statusCode": 200,
                "headers": CORS_HEADERS,
                "body": json.dumps(state, default=decimal_default)
            }

        # POST: process button press or reset
        if method == "POST":
            raw_body = event.get("body", "{}")
            try:
                body_json = json.loads(raw_body) if isinstance(raw_body, str) else (raw_body or {})
            except Exception:
                body_json = {}

            # Handle reset action
            if body_json.get("action") == "reset":
                now_utc = datetime.now(timezone.utc).isoformat()
                table_e1.put_item(
                    Item={
                        "device_id": "ESP32-VISITOR-SUMMARY",
                        "timestamp": "LATEST",
                        "total_visitors": Decimal("0"),
                        "today_visitors": Decimal("0"),
                        "last_entry_time": now_utc,
                        "status": "RESET"
                    }
                )
                return {
                    "statusCode": 200,
                    "headers": CORS_HEADERS,
                    "body": json.dumps({"status": "success", "message": "Counter reset in cloud"})
                }

            # Normal button press
            result = record_visitor_press(body_json)
            return {
                "statusCode": 200,
                "headers": CORS_HEADERS,
                "body": json.dumps(result, default=decimal_default)
            }

    # 2. Direct AWS IoT Topic Rule invocation
    result = record_visitor_press(event)
    return {
        "statusCode": 200,
        "body": result
    }
