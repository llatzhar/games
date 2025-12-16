## Plan: Python Network Gunjin Shogi (WebUI)

Implement a Python client/server system for Gunjin Shogi per RULES.md. The server embeds a web server to host a WebUI. The system enforces authoritative rules (hidden state, complex movement, combat) and synchronizes state via WebSocket.

### Steps
1. **Documentation & Protocol Design**
    - Draft README.md with architecture, TODOs, and reference to RULES.md.
    - Design WebSocket protocol (JSON payloads):
        - `Lobby`: Join, Ready.
        - `Setup`: Submit initial board arrangement.
        - `Game`: Move request, Surrender.
        - `Events`: GameStart, BoardUpdate (masked), CombatResult (win/loss/draw info), GameOver.
    - **Crucial**: Define "Masked State" logic so clients never receive opponent piece types (except revealed ones if rules allow, though RULES.md suggests keeping them hidden).

2. **Shared Rules Engine (Core Logic)**
    - Implement `Board` class handling the specific geometry:
        - 2x (8x6) grids + "River/Bridge" connectivity.
        - **HQ Logic**: Handle "2-cell wide" HQ nodes.
    - Implement `Piece` definitions and ranks.
    - Implement `MoveValidator`:
        - Standard moves (1 step).
        - Special moves: Tank/Cavalry (jump bridges), Plane (fly), Engineer (free move).
        - **HQ Entry Restriction**: Only Major and above can enter Enemy HQ.
    - Implement `CombatEngine`:
        - Resolution table lookup.
        - **Flag (Gunki) Logic**: Calculate strength based on the piece *behind* the flag dynamically.

3. **Server Implementation (Python)**
    - Async server (e.g., FastAPI or aiohttp) serving static files and WebSocket endpoint.
    - **Room Manager**: Handle matchmaking and session state.
    - **Game Loop**:
        - Phase management: `Setup` -> `Play` -> `Finished`.
        - Process moves, execute combat, check Victory Conditions (HQ occupation, annihilation).
        - Broadcast masked updates to clients.

4. **WebUI Implementation (HTML/JS/CSS)**
    - **Tech**: Vanilla JS or lightweight framework (Alpine/Vue) + Canvas or DOM-based grid.
    - **Setup Phase UI**: Drag-and-drop interface for placing 23 pieces in the home territory.
    - **Game Phase UI**:
        - Render board (handling HQ visual merging).
        - Display own pieces (visible) and opponent pieces (hidden '?').
        - Visual feedback for moves and combat results.
    - **Network**: WebSocket client handling reconnects and state sync.

5. **Testing & Refinement**
    - Unit tests for `CombatEngine` (especially Flag and special pieces).
    - Unit tests for `MoveValidator` (especially Bridge/River crossing).
    - Integration test for a full game flow (Setup -> Move -> Win).
