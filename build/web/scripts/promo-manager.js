export class PromoManager {
  constructor(gameEngine) {
    this.game = gameEngine;
    this.isActive = false;
    this.overlay = null;
  }

  start() {
    console.log('[SYS] Initiating Cyber War Promo Simulation');
    
    // Safety Guard: Cannot run 3D promo without WebGL Globe
    if (!this.game.renderer || !this.game.renderer.globe) {
        console.error('[FATAL] Promo Simulation Aborted: WebGL Context is missing. The 3D Engine failed to start.');
        window.dispatchEvent(new CustomEvent('toast', { detail: { message: 'SIMULATION ABORTED: Hardware Acceleration Required', type: 'error' } }));
        return false;
    }

    this.isActive = true;
    
    // Switch Views
    document.querySelectorAll('.view').forEach(el => el.classList.remove('active'));
    document.getElementById('view-game').classList.add('active');
    
    // Reset Engine
    this.game.disableAI = true;
    this.game.nodes = [];
    this.game.connections = [];
    this.game.attacks = [];
    
    // Hide standard HUD completely
    const hud = document.getElementById('hud-layer');
    if (hud) hud.style.display = 'none';
    
    // Inject Cinematic Overlay
    this.createCinematicOverlay();
    
    // Generate specialized 5-team Global Map
    this.buildGlobalMap();
    
    // Configure Camera for cinematic spinning with resilient polling
    let hookAttempts = 0;
    const attemptCameraHook = () => {
        try {
            if (this.game.renderer.globe) {
                const controls = this.game.renderer.globe.controls();
                if (controls) {
                    controls.autoRotate = true;
                    controls.autoRotateSpeed = 1.2;
                    // Slow dramatic zoom in
                    this.game.renderer.globe.pointOfView({ altitude: 1.2 }, 15000);
                    return; // Success, stop polling
                }
            }
        } catch(e) { /* ignore null pointer */ }
        
        hookAttempts++;
        if (hookAttempts < 120) { // Try for approx 2 seconds
            requestAnimationFrame(attemptCameraHook);
        } else {
            console.warn("[SYS] Promo camera automation skipped (globe not ready within 2s timeout).");
        }
    };
    attemptCameraHook();
    
    // Start autonomous warfare
    this.game.promoMode = true;
    this.game.disableAI = false;
    
    this.playSequence();
  }

  createCinematicOverlay() {
    if (this.overlay) this.overlay.remove();
    
    this.overlay = document.createElement('div');
    this.overlay.className = 'promo-overlay';
    this.overlay.style.position = 'absolute';
    this.overlay.style.top = '50%';
    this.overlay.style.left = '50%';
    this.overlay.style.transform = 'translate(-50%, -50%)';
    this.overlay.style.zIndex = '200';
    this.overlay.style.textAlign = 'center';
    this.overlay.style.color = 'var(--color-accent)';
    this.overlay.style.fontFamily = 'var(--font-display)';
    this.overlay.style.fontSize = '3rem';
    this.overlay.style.textShadow = '0 0 20px var(--color-accent)';
    this.overlay.style.opacity = '0';
    this.overlay.style.transition = 'opacity 2s ease-in-out';
    this.overlay.style.pointerEvents = 'none';
    this.overlay.style.whiteSpace = 'nowrap';
    
    document.getElementById('view-game').appendChild(this.overlay);
    
    // Also inject a small "REC" indicator in top right
    const rec = document.createElement('div');
    rec.innerHTML = '<span style="color:red; animation: blink 1s infinite;">●</span> REC';
    rec.style.position = 'absolute';
    rec.style.top = '2rem';
    rec.style.right = '2rem';
    rec.style.color = '#fff';
    rec.style.fontFamily = 'var(--font-mono)';
    rec.style.fontSize = '1.2rem';
    rec.style.zIndex = '200';
    rec.id = 'promo-rec-icon';
    document.getElementById('view-game').appendChild(rec);
  }

  playSequence() {
    const texts = [
      "GLOBAL CYBER WARGAME",
      "OPERATION: GRIDLOCK",
      "USA vs CHINA vs EUROPE",
      "TOTAL DOMINANCE",
      ""
    ];
    
    let step = 0;
    const loop = setInterval(() => {
      if (!this.isActive) {
        clearInterval(loop);
        return;
      }
      
      this.overlay.style.opacity = '0';
      
      setTimeout(() => {
        if (!this.isActive) return;
        if (step >= texts.length) {
            // Re-loop texts for a continuously running sim
            step = 0;
        }
        this.overlay.innerText = texts[step];
        if (texts[step] !== "") {
            this.overlay.style.opacity = '1';
        }
        step++;
      }, 2000);
      
    }, 8000);
  }

  buildGlobalMap() {
    const regions = [
      { owner: 'USA', bases: [{lat: 38, lng: -97}, {lat: 34, lng: -118}, {lat: 40, lng: -74}, {lat: 30, lng: -90}, {lat: 47, lng: -122}] },
      { owner: 'CHINA', bases: [{lat: 35, lng: 105}, {lat: 39, lng: 116}, {lat: 31, lng: 121}, {lat: 22, lng: 114}, {lat: 30, lng: 104}] },
      { owner: 'EUROPE', bases: [{lat: 51, lng: 10}, {lat: 48, lng: 2}, {lat: 52, lng: -0.1}, {lat: 41, lng: 12}, {lat: 52, lng: 13}] },
      { owner: 'RUSSIA', bases: [{lat: 60, lng: 90}, {lat: 55, lng: 37}, {lat: 59, lng: 30}, {lat: 55, lng: 82}, {lat: 43, lng: 131}] },
      { owner: 'APAC', bases: [{lat: -25, lng: 133}, {lat: 35, lng: 139}, {lat: 1.3, lng: 103}, {lat: 14, lng: 121}, {lat: -33, lng: 151}] }
    ];

    let idCounter = 1;
    const factions = [];

    // Create 5 Hub nodes for each faction
    regions.forEach(r => {
      r.bases.forEach((pos, i) => {
        const node = {
          id: `NODE-${idCounter++}`,
          name: `${r.owner}-${i+1}`,
          lat: pos.lat + (Math.random() * 4 - 2),
          lng: pos.lng + (Math.random() * 4 - 2),
          owner: r.owner,
          maxFirewall: 150,
          firewall: 150,
          power: 12 + Math.floor(Math.random() * 8) // Aggressive power
        };
        this.game.nodes.push(node);
        factions.push(node);
      });
    });

    // Create scattered neutral nodes across the globe
    for (let i = 0; i < 40; i++) {
        this.game.nodes.push({
          id: `NODE-${idCounter++}`,
          name: `N-NET-${i}`,
          lat: (Math.random() - 0.5) * 140, // Avoid extreme poles
          lng: (Math.random() - 0.5) * 360,
          owner: 'NEUTRAL',
          maxFirewall: 60,
          firewall: 60,
          power: 5
        });
    }

    // Connect nodes geographically
    // Connect each node to 3-5 of its closest neighbors
    this.game.nodes.forEach(source => {
      // Calculate distances to all other nodes
      const distances = this.game.nodes
        .filter(n => n.id !== source.id)
        .map(n => ({ target: n, dist: Math.pow(source.lat - n.lat, 2) + Math.pow(source.lng - n.lng, 2) }))
        .sort((a, b) => a.dist - b.dist);
        
      // Connect to closest 4
      for(let i = 0; i < 4; i++) {
        const target = distances[i].target;
        // Avoid duplicate paths
        const exists = this.game.connections.find(c => 
          (c.source === source.id && c.target === target.id) ||
          (c.source === target.id && c.target === source.id)
        );
        if (!exists) {
            this.game.connections.push({ source: source.id, target: target.id });
        }
      }
    });

    // Cross-continental long haul links to spark global wars
    for(let i=0; i<15; i++) {
        const n1 = factions[Math.floor(Math.random() * factions.length)];
        const n2 = factions[Math.floor(Math.random() * factions.length)];
        if (n1.owner !== n2.owner) {
             this.game.connections.push({ source: n1.id, target: n2.id });
        }
    }

    this.game.renderer.renderNodes(this.game.nodes);
    this.game.renderer.renderConnections(this.game.connections, this.game.nodes);
  }

  stop() {
    this.isActive = false;
    this.game.promoMode = false;
    if (this.overlay) this.overlay.remove();
    const rec = document.getElementById('promo-rec-icon');
    if (rec) rec.remove();
    const hud = document.getElementById('hud-layer');
    if (hud) hud.style.display = 'block';
  }
}
