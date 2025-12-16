## Plan: Python Network Gunjin Shogi

Implement a Python client/server system for Gunjin Shogi per RULES.md, defining a clear protocol, shared rules engine, and match flow. Create and maintain README.md with architecture, message formats, and TODOs. Build a server that embeds a web server and hosts the WebUI, handling room/match orchestration and authoritative state; clients connect via browser using WebSocket/HTTP. Include tests for rules and protocol.

### Steps
1. Draft README.md sections (scope, architecture, protocol outline, TODO list) referencing RULES.md.
2. Design message protocol (lobby, matchmaking, moves, combat resolution) and document in README.md.
3. Implement shared rules engine (board, pieces, move validation, combat resolution) guided by RULES.md.
4. Build server app (matchmaking, game loop, rule enforcement, persistence stubs) using async IO; document endpoints/messages in README.md.
5. Build WebUI served from the server (HTML/JS/CSS) that talks over WebSocket/HTTP for lobby, in-game board rendering, and commands; add minimal static asset pipeline.
6. Add automated tests for rules engine, protocol handling, and API contracts; update README.md TODOs/status as coverage grows.

### Further Considerations
1. WebUI approach: single-page app served by embedded web server; minimal JS bundle; consider htmx/Alpine or lightweight React depending on scope.
