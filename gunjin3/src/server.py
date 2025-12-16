import asyncio
import json
import os
import uuid
from typing import Dict, Set, Optional
from aiohttp import web
import aiohttp
from enum import Enum

# Basic Server Setup
PORT = 8080
STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")

class PlayerState(Enum):
    CONNECTED = "CONNECTED"
    IN_LOBBY = "IN_LOBBY"
    IN_ROOM = "IN_ROOM"
    READY = "READY"
    PLAYING = "PLAYING"

class Room:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.players: Dict[str, web.WebSocketResponse] = {} # player_id -> ws
        self.ready_status: Dict[str, bool] = {} # player_id -> is_ready
        self.game_started = False

    def add_player(self, player_id: str, ws: web.WebSocketResponse) -> bool:
        if len(self.players) >= 2:
            return False
        self.players[player_id] = ws
        self.ready_status[player_id] = False
        return True

    def remove_player(self, player_id: str):
        if player_id in self.players:
            del self.players[player_id]
        if player_id in self.ready_status:
            del self.ready_status[player_id]
        self.game_started = False # Reset if someone leaves

    def set_ready(self, player_id: str, is_ready: bool):
        if player_id in self.ready_status:
            self.ready_status[player_id] = is_ready

    def is_full(self):
        return len(self.players) == 2

    def all_ready(self):
        return self.is_full() and all(self.ready_status.values())

    async def broadcast(self, message: dict):
        for ws in self.players.values():
            await ws.send_json(message)

class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.player_room_map: Dict[str, str] = {} # player_id -> room_id

    def create_room(self) -> str:
        room_id = str(uuid.uuid4())[:8]
        self.rooms[room_id] = Room(room_id)
        return room_id

    def join_room(self, room_id: str, player_id: str, ws: web.WebSocketResponse) -> bool:
        if room_id not in self.rooms:
            return False
        room = self.rooms[room_id]
        if room.add_player(player_id, ws):
            self.player_room_map[player_id] = room_id
            return True
        return False

    def leave_room(self, player_id: str):
        if player_id in self.player_room_map:
            room_id = self.player_room_map[player_id]
            if room_id in self.rooms:
                self.rooms[room_id].remove_player(player_id)
                # Cleanup empty rooms
                if not self.rooms[room_id].players:
                    del self.rooms[room_id]
            del self.player_room_map[player_id]

    def get_room(self, player_id: str) -> Optional[Room]:
        room_id = self.player_room_map.get(player_id)
        if room_id:
            return self.rooms.get(room_id)
        return None

room_manager = RoomManager()

async def handle_index(request):
    return web.FileResponse(os.path.join(STATIC_DIR, "index.html"))

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    player_id = str(uuid.uuid4())[:8]
    print(f"Player connected: {player_id}")
    
    # Send welcome message
    await ws.send_json({"type": "WELCOME", "player_id": player_id})

    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                msg_type = data.get("type")
                
                print(f"[{player_id}] Received: {data}")

                if msg_type == "CREATE_ROOM":
                    room_id = room_manager.create_room()
                    if room_manager.join_room(room_id, player_id, ws):
                        await ws.send_json({"type": "ROOM_JOINED", "room_id": room_id, "role": "HOST"})
                    else:
                        await ws.send_json({"type": "ERROR", "msg": "Failed to create/join room"})

                elif msg_type == "JOIN_ROOM":
                    room_id = data.get("room_id")
                    if room_manager.join_room(room_id, player_id, ws):
                        await ws.send_json({"type": "ROOM_JOINED", "room_id": room_id, "role": "GUEST"})
                        # Notify other player
                        room = room_manager.get_room(player_id)
                        await room.broadcast({"type": "PLAYER_JOINED", "count": len(room.players)})
                    else:
                        await ws.send_json({"type": "ERROR", "msg": "Room full or not found"})

                elif msg_type == "READY":
                    room = room_manager.get_room(player_id)
                    if room:
                        room.set_ready(player_id, True)
                        await room.broadcast({"type": "PLAYER_READY", "player_id": player_id})
                        
                        if room.all_ready():
                            room.game_started = True
                            # Assign sides (Host=FRONT, Guest=BACK usually, or random)
                            # For simplicity: First player (Host) is FRONT
                            players = list(room.players.keys())
                            p1 = players[0]
                            p2 = players[1]
                            
                            await room.players[p1].send_json({"type": "GAME_START", "side": "FRONT", "opponent": p2})
                            await room.players[p2].send_json({"type": "GAME_START", "side": "BACK", "opponent": p1})

                elif msg_type == "CHAT":
                    room = room_manager.get_room(player_id)
                    if room:
                        await room.broadcast({"type": "CHAT", "from": player_id, "msg": data.get("msg")})

            elif msg.type == aiohttp.WSMsgType.ERROR:
                print(f"ws connection closed with exception {ws.exception()}")
    finally:
        room_manager.leave_room(player_id)
        print(f"Player disconnected: {player_id}")

    return ws

def create_app():
    app = web.Application()
    
    if not os.path.exists(STATIC_DIR):
        os.makedirs(STATIC_DIR)
        with open(os.path.join(STATIC_DIR, "index.html"), "w") as f:
            f.write("<h1>Gunjin Shogi Server Running</h1>")

    app.router.add_get('/', handle_index)
    app.router.add_get('/ws', websocket_handler)
    app.router.add_static('/static', STATIC_DIR)
    
    return app

if __name__ == '__main__':
    app = create_app()
    web.run_app(app, port=PORT)
