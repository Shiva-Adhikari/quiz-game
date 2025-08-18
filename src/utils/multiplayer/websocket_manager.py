from fastapi import WebSocket
from typing import Dict, List, Set
import json
import asyncio
from datetime import datetime


class ConnectionManager:
    def __init__(self):
        # room_id -> set of websocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # websocket -> (room_id, user_id) mapping
        self.connection_info: Dict[WebSocket, tuple] = {}
    
    async def connect(self, websocket: WebSocket, room_id: int, user_id: int):
        await websocket.accept()
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        
        self.active_connections[room_id].add(websocket)
        self.connection_info[websocket] = (room_id, user_id)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.connection_info:
            room_id, user_id = self.connection_info[websocket]
            
            if room_id in self.active_connections:
                self.active_connections[room_id].discard(websocket)
                
                # Clean up empty rooms
                if not self.active_connections[room_id]:
                    del self.active_connections[room_id]
            
            del self.connection_info[websocket]
            return room_id, user_id
        return None, None
    
    async def send_to_room(self, room_id: int, event_type: str, data: dict):
        if room_id in self.active_connections:
            message = {
                "event": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send to all connections in room
            dead_connections = []
            for connection in self.active_connections[room_id].copy():
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    dead_connections.append(connection)
            
            # Clean up dead connections
            for dead_conn in dead_connections:
                self.disconnect(dead_conn)
    
    async def send_to_user(self, room_id: int, user_id: int, event_type: str, data: dict):
        if room_id in self.active_connections:
            message = {
                "event": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            for connection in self.active_connections[room_id]:
                if connection in self.connection_info:
                    conn_room_id, conn_user_id = self.connection_info[connection]
                    if conn_user_id == user_id:
                        try:
                            await connection.send_text(json.dumps(message))
                        except:
                            self.disconnect(connection)
                        break
    
    def get_room_connections_count(self, room_id: int) -> int:
        return len(self.active_connections.get(room_id, set()))


manager = ConnectionManager()
