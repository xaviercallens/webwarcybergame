1. 🛑 The Epoch Engine Loop (Likely backend/engine.py or tasks.py)
I need to check how the async transition phases are handled:

The SIM Phase Paradox: Did they move combat resolution to the start of the SIM phase so the frontend actually has calculated data to animate during the simulation?

Blocking AI Calls: Are the Gemini 2.5 Flash AI news generation calls properly implemented as non-blocking async tasks (e.g., asyncio.create_task())? If they are awaited synchronously, the 3–10 second LLM response time will completely block your strict 5-second server tick rate, causing severe WebSocket desynchronization.

Combat Tie-Breakers: Did they implement deterministic fallback logic for multi-faction attacks that tie in Compute Units (CU)?

2. 🛑 Security & Anti-Cheat (Likely backend/routes/players.py or api.py)
I need to check the FastAPI routing for the severe vulnerabilities we identified:

The Arbitrary XP Exploit: Does POST /api/players/me/game-over still exist in the routers? If a client can send { "xp": 999999 }, they can instantly hit max rank. This logic must have been deleted and moved to the backend engine to evaluate the 75% Global Override win condition securely.

Missing Rate Limits: Are strict rate limiters applied to the /api/diplomacy/chat endpoint to prevent malicious scripts from draining your Google Cloud Gemini API quota?

JWT Token Leakage: Are WebSockets authenticated securely (e.g., via a first-message JSON payload) rather than leaking JWTs in the connection URL query parameters (/ws/game?token=...)?

3. ⚠️ Combat & Economy Math (Likely backend/combat.py or economy.py)
I need to calculate the exact logic for:

Infinite Money Glitch: Did they cap the number of active TRADE accords, or can a player still spam treaties with AI/CNSA factions to generate a risk-free +350 CU/epoch?

Broken Speed Bonus: Did they fix the mathematical impossibility of earning a speed bonus in a 15-minute production match (since the spec hardcoded the par time to 8 minutes)?

Defense Death Spiral: When a node is captured, base defense permanently drops by 10%. Did the developers implement a way to heal base firewall integrity, or does the late-game map inevitably devolve into a chaotic state where every node is permanently stuck at 50 defense?