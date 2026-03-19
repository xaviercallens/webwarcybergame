# 🌐 Neo-Hack: Gridlock

[![Play Now](https://img.shields.io/badge/PLAY_LIVE-Online_Playground-brightgreen?style=for-the-badge&logo=github)](https://xaviercallens.github.io/webwarcybergame/)

> **Global Cyber Warfare Simulation in full 3D.**

🔥 **[Watch the Global Simulation Trailer](docs/neo_hack_promo_trailer.mp4)** 🔥

<video src="https://github.com/xaviercallens/webwarcybergame/raw/main/docs/neo_hack_promo_trailer.mp4" width="100%" controls autoplay loop muted playsinline></video>

**Neo-Hack: Gridlock** is an immersive, browser-based cyber warfare strategy game played out on a visually stunning 3D globe. Take command of regional nodes, bypass enemy firewalls, and launch coordinated hacking payloads to achieve Total Dominance against rival factions.

## 🌟 What's New in Release 2.1

- 🌍 **WebGL Fallback Support**: Enjoy the game smoothly even on browsers without hardware acceleration.
- ⚙️ **Customizable Node Counts**: Tailor your match length by choosing between 10 to 100 global nodes.
- 🤝 **Diplomacy Enhancements**: Improved faction interaction with a revamped diplomacy modal.
- 📊 **Real-Time HUD**: Comprehensive Epoch Phase tracking (Planning, Simulation, Transition).
- 🛡️ **Unmatched Stability**: Over 360 passing tests ensuring 90%+ coverage across backend and frontend engines.

## 📸 Core Intel

<div align="center">
  <img src="docs/shot_01_main_menu.png" width="32%" alt="Main Menu">
  <img src="docs/shot_02_gameplay.png" width="32%" alt="Tactical Tutorial">
  <img src="docs/shot_03_combat_action.png" width="32%" alt="Live Gameplay">
</div>

## ✨ Features

- **Interactive 3D Globe**: Built on `Three.js` and `Globe.gl`, interact with a beautiful, fully rotatable, and zoomable globe tracking real-time attack arcs and cyber node rendering.
- **Dynamic Combat System**: Engage in tactical node-based combat. Drain target firewalls using adjacent captured network hubs.
- **Automated Faction AI**: Play against autonomous AI factions competing for global control.
- **Stunning Cyberpunk Aesthetics**: A cohesive hacker-themed UI with CRT scanlines, glitch effects, neon palettes, and atmospheric sound design.
- **Smart Launch System**: A lightning-fast `./launch_local.sh` tool with Vite caching, automated Selenium E2E health checks, and automatic browser deployment.

## 🚀 Quick Start (Local Development)

Getting the global cyber battlefield running locally is designed to be seamless.

### Prerequisites
- Node.js (v20+ recommended)
- Python (3.11+ recommended)

### Installation & Launch

1. Clone the repository.
2. Run the smart launch script:
   ```bash
   chmod +x launch_local.sh
   ./launch_local.sh
   ```

The script features a smart deployment pipeline that will automatically:
- Install frontend dependencies and build the Vite production bundle (caches aggressively to save time).
- Spin up the FastAPI backend on port `8000`.
- Run headless automated Selenium End-to-End tests to verify WebGL stability and dataset integrity.
- Open your default browser to `http://localhost:8000`.

*To force a fresh frontend build without using the cache, run `./launch_local.sh --build`.*

## 🛠️ Technology Stack

- **Frontend Engine**: `Vite`, `Three.js`, `Globe.gl`
- **Backend Architecture**: `FastAPI`, `Uvicorn`, `Python`
- **Testing Integrity**: `Selenium` (End-to-End headless Chrome UI verification)
- **Styling**: Modular CSS design system with CSS Variables

## 🎮 How to Play

1. **Observe**: Your claimed network nodes are designated **GREEN**. Hostile targets are **RED**. Neutral systems are **CYAN**.
2. **Select**: Click your `GREEN` node to access its root terminal.
3. **Attack**: Click an adjacent `RED` or `CYAN` node to launch an encrypted attack payload across the network.
4. **Capture**: Watch the firewall integrity drop. When it reaches 0, the node is successfully routed to your control.
5. **Dominate**: Capture 75% of the globe to achieve Total Dominance!

## 🎨 Cyberpunk Visual Assets

The project utilizes a custom neon-cyberpunk visual design language for its nodes and effects. 

<div align="center">
  <img src="assets/images/server_node_player.png" width="18%" alt="Player Node">
  <img src="assets/images/server_node_enemy.png" width="18%" alt="Enemy Node">
  <img src="assets/images/server_node_ally.png" width="18%" alt="Ally Node">
  <img src="assets/images/defense_shield.png" width="18%" alt="Firewall Shield">
  <img src="assets/images/attack_pulse.png" width="18%" alt="Attack Pulse">
</div>

## 🤝 Contributing
Contributions, tactical suggestions, and feature requests are welcome! Feel free to open an issue or submit a Pull Request.

## 📜 License
This project is distributed under the MIT License.