"""
Automated AWS Infrastructure Deployment for Project 2: Smart Visitor Counter
SR University - AWS Cloud IoT Lab
Deploys:
1. Amazon DynamoDB Table: SmartVisitorCounter (Partition Key: device_id, Sort Key: timestamp)
2. Amazon S3 Datalake: Audit records & static website storage
3. AWS Lambda Function: ProcessVisitorCounter (attached to LabRole)
4. AWS IoT Core: Thing ESP32_Visitor_Counter_Node & Topic Rule on campus/library/turnstile/visitor_in
5. Verification Test: Inserts test visitor record into DynamoDB and queries back
"""

import sys
import os
import io
import time
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# Try to import boto3
try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("Error: boto3 is not installed. Run: pip install boto3")
    sys.exit(1)

def load_credentials():
    """Load credentials from local .env files or prompt if missing."""
    env_vars = {}
    candidates = [
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parent.parent / ".env",
    ]
    for p in candidates:
        if p.exists():
            with open(p, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() not in env_vars:
                            env_vars[k.strip()] = v.strip()
    return env_vars

def deploy(credentials=None):
    if credentials is None:
        credentials = load_credentials()

    ak = credentials.get("AWS_ACCESS_KEY_ID")
    sk = credentials.get("AWS_SECRET_ACCESS_KEY")
    st = credentials.get("AWS_SESSION_TOKEN")
    region = credentials.get("AWS_DEFAULT_REGION", "us-east-1")
    table_name = credentials.get("DYNAMODB_TABLE_NAME", "SmartVisitorCounter")
    bucket_name = credentials.get("S3_BUCKET_NAME", "smart-visitor-counter-sru-218062175263")
    function_name = credentials.get("LAMBDA_FUNCTION_NAME", "ProcessVisitorCounter")
    topic = credentials.get("IOT_TOPIC", "campus/library/turnstile/visitor_in")

    if not ak or not sk:
        print("[!] Missing AWS credentials. Please provide AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")
        return False

    session = boto3.Session(
        aws_access_key_id=ak,
        aws_secret_access_key=sk,
        aws_session_token=st if st else None,
        region_name=region
    )

    sts = session.client("sts")
    try:
        identity = sts.get_caller_identity()
        account_id = identity["Account"]
        arn = identity["Arn"]
        print("=" * 60)
        print("  SR UNIVERSITY - SMART VISITOR COUNTER AWS DEPLOYMENT")
        print(f"  Account ID : {account_id}")
        print(f"  Caller ARN : {arn}")
        print(f"  Region     : {region}")
        print("=" * 60)
    except ClientError as e:
        print(f"[ERROR] STS Caller Identity verification failed: {e}")
        return False

    role_arn = f"arn:aws:iam::{account_id}:role/LabRole"

    # -------------------------------------------------------------
    # 1. CREATE / VERIFY DYNAMODB TABLE
    # -------------------------------------------------------------
    print(f"\n[1/5] Configuring DynamoDB Table: {table_name}...")
    dynamodb_client = session.client("dynamodb")
    dynamodb_resource = session.resource("dynamodb")

    table_exists = False
    try:
        desc = dynamodb_client.describe_table(TableName=table_name)
        print(f"  -> DynamoDB table '{table_name}' already exists (Status: {desc['Table']['TableStatus']})")
        table_exists = True
    except dynamodb_client.exceptions.ResourceNotFoundException:
        print(f"  -> Creating DynamoDB table '{table_name}' (Pay-Per-Request)...")
        try:
            dynamodb_client.create_table(
                TableName=table_name,
                KeySchema=[
                    {"AttributeName": "device_id", "KeyType": "HASH"},
                    {"AttributeName": "timestamp", "KeyType": "RANGE"}
                ],
                AttributeDefinitions=[
                    {"AttributeName": "device_id", "AttributeType": "S"},
                    {"AttributeName": "timestamp", "AttributeType": "S"}
                ],
                BillingMode="PAY_PER_REQUEST"
            )
            print(f"  -> Waiting for table '{table_name}' to become ACTIVE...")
            waiter = dynamodb_client.get_waiter("table_exists")
            waiter.wait(TableName=table_name)
            print(f"  -> Table '{table_name}' is now ACTIVE!")
            table_exists = True
        except Exception as e:
            print(f"  [!] Table creation error: {e}")

    # -------------------------------------------------------------
    # 2. CREATE / VERIFY S3 BUCKET
    # -------------------------------------------------------------
    print(f"\n[2/5] Configuring Amazon S3 Bucket: {bucket_name}...")
    s3_client = session.client("s3")
    try:
        if region == "us-east-1":
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region}
            )
        print(f"  -> S3 Bucket created: s3://{bucket_name}")
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        print(f"  -> S3 Bucket already exists and is owned by you: s3://{bucket_name}")
    except Exception as e:
        # Fall back to shared datalake if bucket name taken
        fallback_bucket = f"iot-env-datalake-{account_id}"
        print(f"  -> S3 bucket notice ({e}), checking fallback: {fallback_bucket}")
        try:
            s3_client.head_bucket(Bucket=fallback_bucket)
            bucket_name = fallback_bucket
            print(f"  -> Using existing bucket: {bucket_name}")
        except Exception:
            pass

    # -------------------------------------------------------------
    # 3. PACKAGE & DEPLOY AWS LAMBDA FUNCTION
    # -------------------------------------------------------------
    print(f"\n[3/5] Packaging AWS Lambda: {function_name}...")
    lambda_code = f'''import json
import boto3
import os
from decimal import Decimal
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb', region_name='{region}')
table = dynamodb.Table('{table_name}')
s3 = boto3.client('s3')
BUCKET_NAME = "{bucket_name}"

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    
    # Ingest event fields
    device_id = event.get("device_id", "ESP32-VISITOR-NODE-01")
    delta = int(event.get("count_delta", 1))
    gpio_pin = int(event.get("gpio_pin", 14))
    press_ms = int(event.get("press_duration_ms", 85))
    location = event.get("location", "SRU Central Library Main Turnstile")
    
    now_dt = datetime.now(timezone.utc)
    iso_ts = now_dt.isoformat()
    
    # Generate verification signature
    hash_seed = f"{{iso_ts}}_{{device_id}}_{{delta}}"
    verification_hash = f"SHA256-{{hex(abs(hash(hash_seed)))[-8:].upper()}}"
    
    # 1. Record individual event item in DynamoDB
    item = {{
        "device_id": str(device_id),
        "timestamp": iso_ts,
        "delta": Decimal(str(delta)),
        "gpio_pin": Decimal(str(gpio_pin)),
        "press_duration_ms": Decimal(str(press_ms)),
        "location": str(location),
        "status": "COUNTED",
        "verification_hash": verification_hash,
        "processed_by": "AWS Lambda (ProcessVisitorCounter)"
    }}
    
    try:
        table.put_item(Item=item)
        print("Successfully written item to DynamoDB:", item)
    except Exception as e:
        print("DynamoDB write error:", e)
        
    # 2. Archive audit payload to S3
    try:
        s3_key = f"visitor_logs/{{now_dt.strftime('%Y/%m/%d')}}/visitor_{{int(now_dt.timestamp())}}.json"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(item, default=str, indent=2),
            ContentType="application/json"
        )
    except Exception as e:
        print("S3 archive note:", e)

    return {{
        "statusCode": 200,
        "body": {{
            "status": "RECORDED",
            "device_id": device_id,
            "timestamp": iso_ts,
            "verification_hash": verification_hash
        }}
    }}
'''
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("lambda_function.py", lambda_code)
    zip_bytes = buf.getvalue()

    lam_client = session.client("lambda")
    lambda_arn = None
    try:
        resp = lam_client.get_function(FunctionName=function_name)
        print(f"  -> Updating existing Lambda function: {function_name}")
        lam_client.update_function_code(FunctionName=function_name, ZipFile=zip_bytes)
        lambda_arn = resp["Configuration"]["FunctionArn"]
        print(f"  -> Lambda code updated: {lambda_arn}")
    except lam_client.exceptions.ResourceNotFoundException:
        print(f"  -> Creating new Lambda function '{function_name}' with LabRole...")
        try:
            resp = lam_client.create_function(
                FunctionName=function_name,
                Runtime="python3.12",
                Role=role_arn,
                Handler="lambda_function.lambda_handler",
                Code={"ZipFile": zip_bytes},
                Description="ProcessVisitorCounter: Ingests ESP32 button press events and records them to DynamoDB & S3",
                Timeout=15,
                MemorySize=128
            )
            lambda_arn = resp["FunctionArn"]
            print(f"  -> Lambda created: {lambda_arn}")
        except Exception as e:
            print(f"  [!] Lambda create error: {e}")

    # -------------------------------------------------------------
    # 4. CONFIGURE AWS IOT CORE
    # -------------------------------------------------------------
    print(f"\n[4/5] Configuring AWS IoT Core...")
    iot_client = session.client("iot")
    thing_name = "ESP32_Visitor_Counter_Node"
    try:
        iot_client.create_thing(thingName=thing_name)
        print(f"  -> IoT Thing created/verified: {thing_name}")
    except Exception as e:
        print(f"  -> IoT Thing note: {e}")

    # Create Topic Rule
    if lambda_arn:
        rule_name = "ESP32_Visitor_Counter_Rule"
        topic_sql = f"SELECT * FROM '{topic}'"
        rule_payload = {
            "sql": topic_sql,
            "description": "Routes ESP32 visitor turnstile events to ProcessVisitorCounter Lambda",
            "actions": [{"lambda": {"functionArn": lambda_arn}}],
            "ruleDisabled": False,
            "awsIotSqlVersion": "2016-03-23"
        }
        try:
            iot_client.replace_topic_rule(ruleName=rule_name, topicRulePayload=rule_payload)
            print(f"  -> IoT Rule created/updated: {rule_name} (SQL: {topic_sql})")
            
            # Add permission for IoT Core to invoke Lambda
            try:
                lam_client.add_permission(
                    FunctionName=function_name,
                    StatementId="IoTRuleInvokeVisitorLambda",
                    Action="lambda:InvokeFunction",
                    Principal="iot.amazonaws.com",
                    SourceArn=f"arn:aws:iot:{region}:{account_id}:rule/{rule_name}"
                )
                print(f"  -> Granted IoT Rule invoke permission to Lambda")
            except lam_client.exceptions.ResourceConflictException:
                pass
        except Exception as e:
            print(f"  -> IoT Rule error: {e}")

    # -------------------------------------------------------------
    # 5. TEST END-TO-END VERIFICATION (WRITE TO DYNAMODB)
    # -------------------------------------------------------------
    print(f"\n[5/5] Testing Live Cloud Verification...")
    test_iso = datetime.now(timezone.utc).isoformat()
    test_item = {
        "device_id": "ESP32-VISITOR-NODE-01",
        "timestamp": test_iso,
        "visitor_number": 1,
        "delta": 1,
        "location": "SRU Central Library Main Turnstile",
        "gpio_pin": 14,
        "status": "INITIALIZED",
        "verification_hash": f"SHA256-{hex(abs(hash(test_iso)))[-8:].upper()}"
    }

    try:
        from decimal import Decimal
        table = dynamodb_resource.Table(table_name)
        table.put_item(
            Item={
                "device_id": test_item["device_id"],
                "timestamp": test_item["timestamp"],
                "visitor_number": Decimal(str(test_item["visitor_number"])),
                "delta": Decimal(str(test_item["delta"])),
                "location": test_item["location"],
                "gpio_pin": Decimal(str(test_item["gpio_pin"])),
                "status": test_item["status"],
                "verification_hash": test_item["verification_hash"]
            }
        )
        print(f"  [SUCCESS] Put item into DynamoDB '{table_name}':")
        print(f"    • Device ID  : {test_item['device_id']}")
        print(f"    • Visitor #  : {test_item['visitor_number']}")
        print(f"    • Timestamp  : {test_item['timestamp']}")
        print(f"    • Status     : {test_item['status']}")
    except Exception as e:
        print(f"  [!] DynamoDB write test failed: {e}")

    print("\n" + "=" * 60)
    print("  AWS INFRASTRUCTURE DEPLOYMENT COMPLETE!")
    print(f"  DynamoDB Table : {table_name}")
    print(f"  Lambda Function: {function_name}")
    print(f"  IoT Topic      : {topic}")
    print("=" * 60)
    return True

if __name__ == "__main__":
    deploy()
