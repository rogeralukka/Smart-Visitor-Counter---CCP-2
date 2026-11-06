"""
FastAPI Server for Smart Visitor Counter.
Simulates AWS IoT Core -> Lambda -> DynamoDB -> S3 architecture.
Serves frontend static site and real-time SSE stream.
"""

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.routes.visitor import router as visitor_router
from backend.routes.cloud import router as cloud_router
from backend.routes.export import router as export_router

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="Smart Visitor Counter - Virtual AWS IoT Backend",
    description="Physical Button Press Increments a Live Counter on an S3-Hosted Dashboard",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(visitor_router)
app.include_router(cloud_router)
app.include_router(export_router)

# Mount frontend directories
if (FRONTEND_DIR / "css").exists():
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
if (FRONTEND_DIR / "js").exists():
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")

@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path in ["/", "/index.html"]:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

@app.get("/", summary="Serve S3 Static Dashboard")
async def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"status": "Frontend building..."})

@app.get("/api/health", summary="Health check endpoint")
async def health_check():
    return {
        "status": "HEALTHY",
        "product": "Product 1: Smart Visitor Counter",
        "architecture": "ESP32 -> AWS IoT Core -> Lambda -> DynamoDB -> S3"
    }
