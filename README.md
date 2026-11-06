# Smart Visitor Counter (AWS Lab Project 2)
### School of Computer Science & Artificial Intelligence • SR University

## 1. Overview
The **Smart Visitor Counter** is an end-to-end edge-to-cloud IoT system designed to track footfall across campus entrances (e.g., Central Library, Computer Labs). Every physical push button press simulates a visitor walking through a turnstile, which transmits an MQTT event to AWS IoT Core, triggers an AWS Lambda function, atomically updates an Amazon DynamoDB counter, and pushes real-time updates to an Amazon S3-hosted web dashboard.

---

## 2. Architecture & Components
- **ESP32 Edge Microcontroller**:
  - Tactile Momentary Push Button connected to GPIO 14 (active-LOW with pull-up resistor).
  - Built-in / External Status LED on GPIO 2 (flashes upon contact).
  - Software debouncing filter (50ms).
- **AWS IoT Core**:
  - Topic: `campus/library/turnstile/visitor_in` (MQTT QoS 1).
  - IoT Topic Rule routing incoming payloads to Lambda.
- **AWS Lambda**:
  - Function: `ProcessVisitorCounter` (Python 3.11 runtime, 128MB memory).
  - Validates payload and triggers atomic updates.
- **Amazon DynamoDB**:
  - Table: `SmartVisitorCounter` (Partition Key: `counter_id`).
  - Executes atomic `ADD total_visitors :1` expressions without race conditions.
- **Amazon S3**:
  - Static website hosting for the single-page application dashboard.
  - Storage for daily audit log archives.

---

## 3. How to Run Locally

```powershell
# 1. Navigate to the project directory
cd "C:\Users\Roger\Documents\sru\cc project 1\CC PROJECT 2"

# 2. Run the application using the project virtual environment
& "..\.venv\Scripts\python.exe" run_server.py
```

The server will fire up on:
👉 **`http://127.0.0.1:8001`**

---

## 4. Key Features
- **Interactive 3D Push Button**: Click the button on screen or press the `Spacebar` to simulate physical turnstile entrance.
- **Real-Time Glowing Digital Counter**: Odometer display with neon pulse on increment.
- **Interactive SVG Circuit Schematic**: Current pulse animation travels from button to ESP32 to Wi-Fi antenna upon each press.
- **24-Hour Footfall Histogram**: Interactive Chart.js bar chart showing hourly footfall distribution.
- **Live Event Stream Table**: Real-time table streaming recent entries with verification hashes.
- **CSV & JSON Reports**: Download audit records with one click.
- **Dual Themes**: Switch seamlessly between Dark Cyberpunk and Light Clean themes.
