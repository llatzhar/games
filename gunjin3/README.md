# Gunjin Shogi (Python + WebUI)

A web-based implementation of Gunjin Shogi (Military Chess) with a Python server and browser-based client.

## Overview

This project implements the rules defined in [RULES.md](RULES.md). The system consists of:
- **Server**: Python (FastAPI/aiohttp) handling game logic, room management, and WebSocket connections.
- **Client**: Web interface (HTML/JS) for gameplay, communicating via WebSocket.

## Architecture

- **Authoritative Server**: The server maintains the true state of the board, including hidden pieces.
- **Masked State**: Clients only receive information they are allowed to see. Opponent pieces are masked as "Unknown" until revealed by combat or specific rules.
- **Communication**: WebSocket for real-time events (moves, combat results, game state changes).

## Protocol Design (Draft)

### Messages (Client -> Server)
- `{"type": "JOIN", "room_id": "..."}`
- `{"type": "SETUP", "placement": [{"id": "marshal", "pos": [0, 4]}, ...]}`
- `{"type": "MOVE", "from": [x, y], "to": [x, y]}`
- `{"type": "SURRENDER"}`

### Messages (Server -> Client)
- `{"type": "WELCOME", "player_id": "...", "side": "FRONT/BACK"}`
- `{"type": "GAME_START"}`
- `{"type": "BOARD_UPDATE", "board": [[...], ...], "turn": "..."}` (Opponent pieces hidden)
- `{"type": "COMBAT_RESULT", "attacker": {...}, "defender": {...}, "result": "WIN/LOSS/DRAW"}`
- `{"type": "GAME_OVER", "winner": "..."}`

## TODO List

- [ ] **Documentation & Design**
    - [x] Initial README & Protocol Draft
    - [ ] Refine Protocol details (JSON schema)

- [ ] **Shared Rules Engine (Python)**
    - [ ] `Piece` class & Ranks
    - [ ] `Board` class (Grid, HQ, Rivers/Bridges)
    - [ ] `MoveValidator` (Movement rules, HQ entry)
    - [ ] `CombatEngine` (Resolution table, Flag logic)

- [ ] **Server Implementation**
    - [ ] Web Server Setup (FastAPI/aiohttp)
    - [ ] WebSocket Endpoint
    - [ ] Room/Match Manager
    - [ ] Game Loop & State Management

- [ ] **WebUI Implementation**
    - [ ] Basic HTML Layout
    - [ ] Board Rendering (Canvas/Grid)
    - [ ] Setup Phase (Drag & Drop)
    - [ ] Game Phase (Move interaction)
    - [ ] WebSocket Integration

- [ ] **Testing**
    - [ ] Unit tests for Rules
    - [ ] Integration tests for Game Flow
