from typing import Dict, List
from fastapi import WebSocket
import json

class ConnectionManager:
    def __init__(self):
        # Maps player_id -> list of active WebSocket connections
        # A player might have multiple tabs open
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, player_id: int, websocket: WebSocket):
        await websocket.accept()
        if player_id not in self.active_connections:
            self.active_connections[player_id] = []
        self.active_connections[player_id].append(websocket)
        print(f"[WS] Player {player_id} connected. Total WS for player: {len(self.active_connections[player_id])}")

    def disconnect(self, player_id: int, websocket: WebSocket):
        if player_id in self.active_connections:
            if websocket in self.active_connections[player_id]:
                self.active_connections[player_id].remove(websocket)
            if len(self.active_connections[player_id]) == 0:
                del self.active_connections[player_id]
        print(f"[WS] Player {player_id} disconnected.")

    async def send_personal_message(self, message: dict, player_id: int):
        if player_id in self.active_connections:
            for connection in self.active_connections[player_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"[WS ERROR] Sending to player {player_id}: {e}")

    async def broadcast(self, message: dict):
        # Convert message to json string once for efficiency
        json_msg = json.dumps(message)
        dead_connections = []
        for player_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_text(json_msg)
                except Exception as e:
                    print(f"[WS ERROR] Broadcast failed to player {player_id}: {e}")
                    dead_connections.append((player_id, connection))
                    
        # Cleanup any dead connections identified during broadcast
        for pid, ws in dead_connections:
            self.disconnect(pid, ws)

manager = ConnectionManager()
