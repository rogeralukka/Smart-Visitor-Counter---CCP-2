"""
Standalone Server Starter for Smart Visitor Counter (Project 2).
Runs FastAPI server on http://127.0.0.1:8001.
"""

import sys
import uvicorn
from pathlib import Path

# Add current directory to sys.path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from backend.main import app

if __name__ == "__main__":
    print("=" * 60)
    print("SR UNIVERSITY - AWS LAB PROJECT 2")
    print("Product: Smart Visitor Counter (ESP32 + AWS IoT Core + Lambda + DynamoDB + S3)")
    print("Starting server on: http://127.0.0.1:8001")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
