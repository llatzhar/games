# Gunjin Shogi (Python + WebUI)

A web-based implementation of Gunjin Shogi (Military Chess) with a Python server and browser-based client.

## Overview

This project implements the rules defined in [RULES.md](RULES.md). The system consists of:
- **Server**: Python (aiohttp) handling game logic, room management, and WebSocket connections.
- **Client**: Web interface (HTML/JS) for gameplay, communicating via WebSocket.

## Architecture

- **Authoritative Server**: The server maintains the true state of the board, including hidden pieces.
- **Masked State**: Clients only receive information they are allowed to see. Opponent pieces are masked as "Unknown" until revealed by combat or specific rules.
- **Communication**: WebSocket for real-time events (moves, combat results, game state changes).

## Protocol Design (Draft)

### Messages (Client -> Server)
- `{"type": "CREATE_ROOM"}`
- `{"type": "JOIN_ROOM", "room_id": "..."}`
- `{"type": "READY"}`
- `{"type": "SETUP", "placement": [{"rank": "MARSHAL", "pos": [0, 4]}, ...]}`
- `{"type": "MOVE", "from": [r, c], "to": [r, c]}`
- `{"type": "SURRENDER"}`

### Messages (Server -> Client)
- `{"type": "WELCOME", "player_id": "..."}`
- `{"type": "ROOM_JOINED", "room_id": "...", "role": "HOST/GUEST"}`
- `{"type": "GAME_START", "side": "FRONT/BACK", "opponent": "..."}`
- `{"type": "BOARD_UPDATE", "board": [[...], ...], "turn": "..."}` (Opponent pieces hidden)
- `{"type": "COMBAT_RESULT", "attacker": {...}, "defender": {...}, "result": "WIN/LOSS/DRAW"}`
- `{"type": "GAME_OVER", "winner": "..."}`

## Current Status

- **Server**: Fully functional WebSocket server with Room Management.
- **Game Logic**:
    - Complete Gunjin Shogi rules implemented (6x8 board).
    - Special unit rules (Spy, Mine, Tank, Engineer, Plane) implemented.
    - Win conditions (HQ occupation, Annihilation) implemented.
- **WebUI**: 
    - Lobby system.
    - Interactive board with Drag & Drop.
    - "Auto Setup" feature for quick testing.
    - **Board Rotation**: The board automatically rotates 180 degrees for the "BACK" player so their pieces are always at the bottom.
    - **Privacy**: Combat results are masked so players only see their own piece and the result (Win/Loss/Draw), preserving the "fog of war".

## TODO List

- [x] **Documentation & Design**
    - [x] Initial README & Protocol Draft
    - [x] Plan Document (`planGunjin3.prompt.md`)
- [x] **Core Implementation**
    - [x] Server Skeleton (aiohttp)
    - [x] Game Engine (Board, Pieces, Rules)
    - [x] Client Skeleton (HTML/JS)
- [x] **Game Features**
    - [x] Setup Phase (Placement validation)
    - [x] Main Game Loop (Turn-based movement)
    - [x] Combat Logic (Rank comparison, Special rules)
    - [x] Win/Loss Detection
- [x] **UI/UX Improvements**
    - [x] Board Rotation for 2nd Player
    - [x] Combat Result Alerts (Masked)
    - [x] Visual Polish (CSS, Assets)

- [ ] **Shared Rules Engine (Python)**
    - [x] `Piece` class & Ranks
    - [x] `Board` class (Dimensions fixed, HQ logic basic)
    - [ ] `MoveValidator` (Special moves: Tank, Plane, Engineer; River crossing)
    - [ ] `CombatEngine` (Complete resolution table, Flag logic)

- [ ] **Server Implementation**
    - [x] Web Server Setup (aiohttp)
    - [x] WebSocket Endpoint
    - [x] Room/Match Manager
    - [ ] Game Loop & State Management (Setup -> Play -> End)

- [ ] **WebUI Implementation**
    - [x] Lobby UI
    - [ ] Setup Phase (Drag & Drop)
    - [ ] Game Board Rendering (Canvas/DOM)
    - [ ] Move Interaction & Visual Feedback
    - [ ] Basic HTML Layout
    - [ ] Board Rendering (Canvas/Grid)
    - [ ] Setup Phase (Drag & Drop)
    - [ ] Game Phase (Move interaction)
    - [ ] WebSocket Integration

- [ ] **Testing**
    - [ ] Unit tests for Rules
    - [ ] Integration tests for Game Flow
