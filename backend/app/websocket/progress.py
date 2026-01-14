"""WebSocket endpoint for real-time progress updates."""
import asyncio
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

router = APIRouter()

# Store active connections per project
active_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Manage WebSocket connections for progress updates."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = set()
        self.active_connections[project_id].add(websocket)

    def disconnect(self, websocket: WebSocket, project_id: str):
        """Remove a WebSocket connection."""
        if project_id in self.active_connections:
            self.active_connections[project_id].discard(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]

    async def send_progress(self, project_id: str, data: dict):
        """Send progress update to all connections for a project."""
        if project_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[project_id]:
                try:
                    await connection.send_json(data)
                except Exception:
                    disconnected.append(connection)

            # Clean up disconnected clients
            for conn in disconnected:
                self.active_connections[project_id].discard(conn)

    async def broadcast(self, data: dict):
        """Broadcast to all connected clients."""
        for project_id in list(self.active_connections.keys()):
            await self.send_progress(project_id, data)


# Global manager instance
manager = ConnectionManager()


@router.websocket("/ws/progress/{project_id}")
async def websocket_progress(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for project progress updates."""
    await manager.connect(websocket, project_id)
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # Echo back acknowledgment
            await websocket.send_json({"type": "ack", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)


@router.websocket("/ws/global")
async def websocket_global(websocket: WebSocket):
    """WebSocket for global system events (automations, etc.)."""
    await websocket.accept()
    global_connections: Set[WebSocket] = getattr(
        websocket_global, '_connections', set()
    )
    global_connections.add(websocket)
    websocket_global._connections = global_connections

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        global_connections.discard(websocket)


async def send_progress_update(project_id: str, step: str, progress: int, message: str):
    """Helper to send progress updates from services."""
    await manager.send_progress(project_id, {
        "type": "progress",
        "step": step,
        "progress": progress,
        "message": message
    })


async def send_completion(project_id: str, result: dict):
    """Send completion notification."""
    await manager.send_progress(project_id, {
        "type": "complete",
        "result": result
    })


async def send_error(project_id: str, error: str):
    """Send error notification."""
    await manager.send_progress(project_id, {
        "type": "error",
        "error": error
    })
