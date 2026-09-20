from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from config import settings
from database.session import init_db
from api.routes_tasks import router as tasks_router
from api.routes_dashboard import router as dashboard_router
from api.websocket_manager import ws_manager

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Autonomous Ops/Dev Agent with Real Guardrails: Multi-Agent DevOps Platform"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(tasks_router)
app.include_router(dashboard_router)

# Real-Time WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keepalive and incoming commands
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

# Mount Frontend static files
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
frontend_dir.mkdir(parents=True, exist_ok=True)

if (frontend_dir / "css").exists():
    app.mount("/css", StaticFiles(directory=frontend_dir / "css"), name="css")
if (frontend_dir / "js").exists():
    app.mount("/js", StaticFiles(directory=frontend_dir / "js"), name="js")

@app.get("/")
def serve_dashboard():
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"status": "ok", "message": "Autonomous DevOps Agent API is active."}

@app.on_event("startup")
def on_startup():
    init_db()
