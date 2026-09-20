from typing import List, Dict, Any
from fastapi import WebSocket

class WebSocketManager:
    """
    Manages active WebSocket client connections and broadcasts live telemetry:
    - Running agent updates
    - Terminal streaming logs
    - Test execution results
    - Guardrail alerts & confidence scores
    - Human escalation requests
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        message = {
            "event": event_type,
            "data": data
        }
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

ws_manager = WebSocketManager()
