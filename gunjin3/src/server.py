import asyncio
import json
import os
import uuid
from typing import Dict, Set, Optional, List
from aiohttp import web
import aiohttp
from enum import Enum

from game.board import Board, ROWS, COLS
from game.piece import Piece, Rank, Side
from game.engine import MoveValidator, CombatEngine

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
        self.player_sides: Dict[str, Side] = {} # player_id -> Side
        self.game_started = False
        
        # Game State
        self.board = Board()
        self.validator = MoveValidator(self.board)
        self.combat_engine = CombatEngine()
        self.turn = Side.FRONT
        self.setup_complete: Dict[Side, bool] = {Side.FRONT: False, Side.BACK: False}
        self.winner: Optional[Side] = None

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
        if player_id in self.player_sides:
            del self.player_sides[player_id]
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
            
    def get_masked_board(self, viewer_side: Side) -> List[List[dict]]:
        # Return board representation for viewer
        # Own pieces: Full info
        # Enemy pieces: Hidden unless revealed
        grid_data = []
        for r in range(ROWS):
            row_data = []
            for c in range(COLS):
                p = self.board.get_piece(r, c)
                if p is None:
                    row_data.append(None)
                else:
                    try:
                        if p.side == viewer_side or p.is_revealed:
                            row_data.append({"rank": p.rank.name, "side": p.side.name, "revealed": p.is_revealed})
                        else:
                            row_data.append({"rank": "UNKNOWN", "side": p.side.name, "revealed": False})
                    except Exception as e:
                        print(f"Error processing piece at {r},{c}: {e}")
                        row_data.append(None)
            grid_data.append(row_data)
        return grid_data

    async def send_board_update(self):
        print(f"Sending board update. Players in sides: {[repr(k) for k in self.player_sides.keys()]}")
        print(f"Players in ws dict: {[repr(k) for k in self.players.keys()]}")
        for pid, side in self.player_sides.items():
            if pid in self.players:
                ws = self.players[pid]
                print(f"Found WS for {repr(pid)}: {type(ws)}")
                try:
                    board_data = self.get_masked_board(side)
                    print(f"Sending to {pid} ({side}): {len(board_data)} rows")
                    await ws.send_json({
                        "type": "BOARD_UPDATE",
                        "board": board_data,
                        "turn": self.turn.name
                    })
                except Exception as e:
                    print(f"Error sending board update to {pid}: {e}")
            else:
                print(f"WS key not found for {repr(pid)}")

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
                            # Assign sides
                            players = list(room.players.keys())
                            p1 = players[0]
                            p2 = players[1]
                            
                            room.player_sides[p1] = Side.FRONT
                            room.player_sides[p2] = Side.BACK
                            
                            await room.players[p1].send_json({"type": "GAME_START", "side": "FRONT", "opponent": p2})
                            await room.players[p2].send_json({"type": "GAME_START", "side": "BACK", "opponent": p1})

                elif msg_type == "SETUP":
                    room = room_manager.get_room(player_id)
                    if room and room.game_started:
                        side = room.player_sides.get(player_id)
                        placement = data.get("placement") # List of {"rank": "...", "pos": [r, c]}
                        
                        # Validate and Place
                        # TODO: Strict validation of piece counts and territory
                        placed_count = 0
                        for p_data in placement:
                            rank_str = p_data["rank"]
                            r, c = p_data["pos"]
                            try:
                                rank = Rank[rank_str]
                                piece = Piece(rank, side)
                                room.board.place_piece(piece, r, c)
                                placed_count += 1
                            except Exception as e:
                                print(f"Setup error for {rank_str} at {r},{c}: {e}")
                        
                        print(f"Player {player_id} ({side}) placed {placed_count} pieces.")
                        room.setup_complete[side] = True
                        
                        if all(room.setup_complete.values()):
                            # Both setup done, start play
                            print("All players setup complete. Starting game.")
                            await room.broadcast({"type": "PLAY_START"})
                            print("Broadcast PLAY_START done. Sending board update...")
                            await room.send_board_update()
                            print("Board update sent.")
                        else:
                            print(f"Waiting for other player setup. Status: {room.setup_complete}")

                elif msg_type == "MOVE":
                    room = room_manager.get_room(player_id)
                    if room and room.game_started and all(room.setup_complete.values()):
                        side = room.player_sides.get(player_id)
                        if room.turn != side:
                            await ws.send_json({"type": "ERROR", "msg": "Not your turn"})
                            continue
                            
                        from_pos = tuple(data.get("from"))
                        to_pos = tuple(data.get("to"))
                        
                        piece = room.board.get_piece(*from_pos)
                        if not piece or piece.side != side:
                            await ws.send_json({"type": "ERROR", "msg": "Invalid piece"})
                            continue
                            
                        if room.validator.is_valid_move(piece, from_pos, to_pos):
                            target = room.board.get_piece(*to_pos)
                            combat_result = None
                            
                            if target:
                                # Combat
                                result = room.combat_engine.resolve_combat(piece, target, from_pos, to_pos, room.board)
                                # 1: Attacker wins, -1: Defender wins, 0: Draw
                                
                                attacker_info = {"rank": piece.rank.name, "side": piece.side.name}
                                defender_info = {"rank": target.rank.name, "side": target.side.name}
                                
                                if result == 1:
                                    room.board.remove_piece(*to_pos) # Remove defender
                                    room.board.move_piece(from_pos, to_pos) # Move attacker
                                    combat_res_str = "WIN"
                                elif result == -1:
                                    room.board.remove_piece(*from_pos) # Remove attacker
                                    combat_res_str = "LOSS"
                                else:
                                    room.board.remove_piece(*from_pos)
                                    room.board.remove_piece(*to_pos)
                                    combat_res_str = "DRAW"
                                
                                # Broadcast combat result with masked info
                                # Attacker sees: Own rank, Result. (Defender rank hidden unless revealed?)
                                # Defender sees: Own rank, Result. (Attacker rank hidden unless revealed?)
                                # RULES: "自分の駒の種類と勝敗結果のみ表示" -> "Only display own piece type and win/loss result"
                                # This implies you don't see WHAT you fought, only if you won/lost.
                                
                                for pid, p_side in room.player_sides.items():
                                    if pid in room.players:
                                        p_ws = room.players[pid]
                                        
                                        msg = None
                                        # Determine what this player sees
                                        if p_side == piece.side: # Attacker
                                            msg = {
                                                "type": "COMBAT_RESULT",
                                                "my_piece": {"rank": piece.rank.name},
                                                "result": combat_res_str
                                            }
                                        elif p_side == target.side: # Defender
                                            def_res = "LOSS" if combat_res_str == "WIN" else ("WIN" if combat_res_str == "LOSS" else "DRAW")
                                            msg = {
                                                "type": "COMBAT_RESULT",
                                                "my_piece": {"rank": target.rank.name},
                                                "result": def_res
                                            }
                                        
                                        if msg:
                                            print(f"Sending COMBAT_RESULT to {pid} ({p_side}): {msg}")
                                            await p_ws.send_json(msg)
                                    else:
                                        print(f"WS key {repr(pid)} NOT found in room.players during combat broadcast. Keys: {[repr(k) for k in room.players.keys()]}")
                                
                                # Check Victory (HQ Occupation or Annihilation)
                                # HQ Check
                                if room.board.is_hq(*to_pos):
                                    hq_owner = room.board.get_hq_owner(*to_pos)
                                    if hq_owner and hq_owner != side:
                                        # Occupied Enemy HQ
                                        room.winner = side
                                        await room.broadcast({"type": "GAME_OVER", "winner": side.name})
                            else:
                                # Simple Move
                                room.board.move_piece(from_pos, to_pos)
                                
                                # Check HQ Entry (if empty)
                                if room.board.is_hq(*to_pos):
                                    hq_owner = room.board.get_hq_owner(*to_pos)
                                    if hq_owner and hq_owner != side:
                                        room.winner = side
                                        await room.broadcast({"type": "GAME_OVER", "winner": side.name})

                            # Switch Turn
                            room.turn = Side.BACK if room.turn == Side.FRONT else Side.FRONT
                            await room.send_board_update()
                        else:
                            await ws.send_json({"type": "ERROR", "msg": "Invalid move"})

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
