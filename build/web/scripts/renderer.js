/**
 * Neo-Hack: Gridlock — 3D Globe Renderer Engine
 */

import Globe from 'globe.gl';
import * as THREE from 'three';

export class GameRenderer {
  constructor(canvasContainerId) {
    this.containerId = canvasContainerId;
    this.globe = null;
    
    // Config
    this.colors = {
      player: '#00FF88', // green
      enemy: '#FF4444',  // red
      ally: '#4488FF',   // blue
      neutral: '#66AAAA', // cyan
      background: '#0A0E17',
      earthLines: '#1d2c4d',
      earthGlow: 'rgba(0, 255, 136, 0.2)' 
    };

    // Node lookup maps
    this.nodeMap = new Map();
  }

  async init() {
    const container = document.getElementById(this.containerId);
    if (!container) throw new Error(`Container #${this.containerId} not found`);

    if (this.globe) {
      // Already initialized, just clear data and return
      this.nodeMap.clear();
      this.globe.pointsData([]).arcsData([]).labelsData([]);
      return;
    }

    // Initialize Globe.gl with relaxed WebGL config for Chrome OS / headless fallback
    try {
        this.globe = Globe()(container)
          .globeImageUrl('//unpkg.com/three-globe/example/img/earth-water.png') // Fallback base texture (optional, can omit for pure wireframe)
          .backgroundColor('rgba(0,0,0,0)') // Transparent background to show our CSS space gradient
          .showAtmosphere(true)
          .atmosphereColor(this.colors.neutral)
          .atmosphereAltitude(0.15);
          
        sessionStorage.removeItem('webgl_reloaded'); // Clear flag on success
    } catch (e) {
        console.error('[CRITICAL] Failed to initialize WebGL context:', e);
        
        console.warn('[SYS] WebGL initialization failed. Falling back to 2D Degraded Mode.');
        this.fallbackMode = true;
        this.initFallbackCanvas(container);
        return;
    }

    // Load GeoJSON for landmasses
    try {
      const response = await fetch('/datasets/ne_110m_admin_0_countries.geojson');
      const countries = await response.json();
      
      this.globe
        .hexPolygonsData(countries.features)
        .hexPolygonResolution(1)
        .hexPolygonMargin(0.3)
        .hexPolygonColor(() => this.colors.earthLines);
        
    } catch (err) {
      console.error('[SYS] Failed to load GeoJSON map data:', err);
    }

    // Configure Camera & Controls
    this.setupCamera();

    // Event binding
    this.globe.onPointClick((point) => {
      window.dispatchEvent(new CustomEvent('nodeClicked', { detail: { nodeId: point.id } }));
    });

    console.log('[SYS] Globe.GL 3D Renderer Initialized');
  }

  setupCamera() {
    // Globe.gl automatically provides Three.js scene, camera, and renderer.
    // It also wires up OrbitControls.
    const controls = this.globe.controls();
    controls.enablePan = false;
    controls.minDistance = 120;
    controls.maxDistance = 600;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.5;
    
    // Stop rotating on interaction
    controls.addEventListener('start', () => {
      controls.autoRotate = false;
    });
    
    // Adjust default lighting
    const scene = this.globe.scene();
    scene.add(new THREE.AmbientLight(0x222222));
    const dLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dLight.position.set(-800, 2000, 400);
    scene.add(dLight);
    
    // Set initial position
    this.globe.pointOfView({ lat: 40, lng: -40, altitude: 2.5 });
  }

  // --- RENDERING API ---

  getColorForFaction(factionId) {
    const isColorblind = document.documentElement.getAttribute('data-colorblind') === 'true';
    switch(factionId) {
      case 1: return isColorblind ? '#3380FF' : this.colors.player; // Silicon Valley (Player default for now)
      case 2: return isColorblind ? '#FF8000' : this.colors.enemy;  // Iron Grid
      case 3: return isColorblind ? '#E6CC33' : '#FFCC00';          // Silk Road
      case 4: return isColorblind ? '#8800FF' : this.colors.ally;   // Euro Nexus
      case 5: return isColorblind ? '#00FF88' : '#8800FF';          // Pacific Vanguard
      default: return this.colors.neutral; 
    }
  }

  renderNodes(nodes, highlightEnemies = false, highlightAttackable = false, connections = []) {
    if (this.fallbackMode) {
      this.renderFallback(nodes, connections);
      return;
    }
    if (!this.globe) return;
    
    this.nodeMap.clear();
    nodes.forEach(n => this.nodeMap.set(n.id, n));

    const pointsData = nodes.map(node => {
      let size = node.faction_id === 1 ? 0.3 : 0.15; // Player nodes slightly larger
      let color = this.getColorForFaction(node.faction_id);
      
      // Override for Highlights
      if (highlightEnemies && node.faction_id !== 1 && node.faction_id !== null) {
          size = 0.8;
          color = '#ffffff'; // Flash white
      }
      if (highlightAttackable && node.faction_id === 1) {
          // Check if this player node has an adjacent non-player node
          const adjacentLinks = connections.filter(c => c.source === node.id || c.target === node.id);
          const hasTarget = adjacentLinks.some(c => {
             const tId = c.source === node.id ? c.target : c.source;
             const tNode = this.nodeMap.get(tId);
             return tNode && tNode.faction_id !== 1;
          });
          
          if (hasTarget) {
              size = 1.0;
              color = '#00FF88'; // Flash bright green
          }
      }

      // Accessibility Shapes
      let shapePrefix = '[■]'; // Neutral default
      if (node.faction_id === 1) shapePrefix = '[●]';
      else if (node.faction_id !== null) shapePrefix = '[▲]';

      return {
        id: node.id,
        lat: node.lat,
        lng: node.lng,
        size: size,
        color: color,
        name: `${shapePrefix} ${node.name}`
      };
    });

    this.globe
      .pointsData(pointsData)
      .pointAltitude('size')
      .pointColor('color')
      .pointRadius(0.5)
      .pointResolution(16);
      
    // Custom label text for nodes
    this.globe
      .labelsData(pointsData)
      .labelLat('lat')
      .labelLng('lng')
      .labelText('name')
      .labelSize(1.5)
      .labelDotRadius(0)
      .labelColor('color')
      .labelResolution(1)
      .labelAltitude(d => d.size + 0.05);
  }

  renderConnections(connections, nodes) {
    if (this.fallbackMode) return; // Handled concurrently in renderFallback
    if (!this.globe) return;
    const arcsData = connections.map(conn => {
      const source = this.nodeMap.get(conn.source);
      const target = this.nodeMap.get(conn.target);
      if (!source || !target) return null;
      
      const isCrossFaction = source.faction_id !== target.faction_id;
      const color = isCrossFaction ? this.colors.neutral : this.getColorForFaction(source.faction_id);
      
      return {
        startLat: source.lat,
        startLng: source.lng,
        endLat: target.lat,
        endLng: target.lng,
        color: color
      };
    }).filter(Boolean);

    this.globe
      .arcsData(arcsData)
      .arcColor('color')
      .arcDashLength(0.4)
      .arcDashGap(0.2)
      .arcDashInitialGap(() => Math.random())
      .arcDashAnimateTime(2000)
      .arcStroke(0.5);
  }

  // --- FALLBACK 2D RENDERING ---

  initFallbackCanvas(container) {
    this.canvas = document.createElement('canvas');
    this.canvas.width = container.clientWidth || 800;
    this.canvas.height = container.clientHeight || 600;
    this.canvas.style.width = '100%';
    this.canvas.style.height = '100%';
    container.innerHTML = '';
    container.appendChild(this.canvas);
    this.ctx = this.canvas.getContext('2d');
    
    // Store calculated 2D coordinates for hit detection
    this.mappedNodes = [];

    this.drawFallbackText('DEGRADED MODE - SYSTEM ONLINE');
    
    window.addEventListener('resize', () => {
        if (!this.canvas || !container) return;
        this.canvas.width = container.clientWidth;
        this.canvas.height = container.clientHeight;
        if (this.lastNodes) {
          this.renderFallback(this.lastNodes, this.lastConnections);
        } else {
          this.drawFallbackText('DEGRADED MODE - SYSTEM ONLINE');
        }
    });

    // Real node interaction for the 2D map fallback
    this.canvas.addEventListener('click', (e) => {
        if (!this.mappedNodes || this.mappedNodes.length === 0) return;
        
        const rect = this.canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        // Find the closest node within a hit radius
        const HIT_RADIUS = 15;
        let closestNode = null;
        let minDistance = Infinity;

        for (const mn of this.mappedNodes) {
            const dx = mn.x - mouseX;
            const dy = mn.y - mouseY;
            const dist = Math.sqrt(dx * dx + dy * dy);
            
            if (dist < minDistance && dist <= HIT_RADIUS) {
                minDistance = dist;
                closestNode = mn.node;
            }
        }

        if (closestNode) {
            window.dispatchEvent(new CustomEvent('nodeClicked', { detail: { nodeId: closestNode.id } }));
        }
    });
  }

  drawFallbackText(text) {
      if (!this.ctx) return;
      this.ctx.fillStyle = this.colors.background || '#0a0e17'; 
      this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
      
      this.ctx.fillStyle = this.colors.player || '#00ff88';
      this.ctx.font = '24px monospace';
      this.ctx.textAlign = 'center';
      this.ctx.textBaseline = 'middle';
      this.ctx.fillText(text, this.canvas.width / 2, this.canvas.height / 2);
  }

  renderFallback(nodes, connections) {
      this.lastNodes = nodes;
      this.lastConnections = connections;
      if (!this.ctx || !this.canvas) return;
      
      this.ctx.fillStyle = this.colors.background || '#0a0e17';
      this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
      
      const width = this.canvas.width;
      const height = this.canvas.height;
      const hw = width / 2;
      const hh = height / 2;
      
      // Draw Statistics in the top-left corner
      this.ctx.fillStyle = this.colors.ally || '#4488ff';
      this.ctx.textAlign = 'left';
      this.ctx.textBaseline = 'top';
      this.ctx.font = '20px monospace';
      this.ctx.fillText('DEGRADED MODE: 2D MAP', 20, 20);
      
      const counts = {};
      nodes.forEach(n => {
          counts[n.faction_id] = (counts[n.faction_id] || 0) + 1;
      });
      
      let y = 60;
      this.ctx.font = '16px monospace';
      for (const [faction, count] of Object.entries(counts)) {
         this.ctx.fillStyle = this.getColorForFaction(faction === 'null' ? null : parseInt(faction));
         let fName = faction === '1' ? 'Player' : faction === 'null' ? 'Neutral' : 'Enemy ' + faction;
         this.ctx.fillText(`${fName} Nodes: ${count}`, 20, y);
         y += 25;
      }
      this.ctx.fillStyle = '#ffff00';
      this.ctx.fillText(`Connections: ${connections ? connections.length : 0}`, 20, y + 10);
      
      // Setup Earth projection space
      const earthRadius = Math.min(width, height) * 0.4;
      const cx = hw + 100; // Shift earth a bit to the right
      const cy = hh;
      
      // Draw Earth Circle
      this.ctx.strokeStyle = this.colors.earthLines || '#1d2c4d';
      this.ctx.lineWidth = 2;
      this.ctx.beginPath();
      this.ctx.arc(cx, cy, earthRadius, 0, 2 * Math.PI);
      this.ctx.stroke();
      
      // Simple pulsing glow
      const time = Date.now() * 0.002;
      const pulse = (Math.sin(time) + 1) / 2;
      this.ctx.fillStyle = `rgba(68, 136, 255, ${0.05 + pulse * 0.05})`;
      this.ctx.fill();

      // Convert Lat/Lng to X/Y using simple equirectangular projection onto the circle area
      // lat: -90 to +90, lng: -180 to +180
      this.mappedNodes = nodes.map(node => {
         // Normalize lat/lng to -1 to +1 range
         const nx = node.lng / 180;
         // Invert lat so southern hemisphere is +y
         const ny = -node.lat / 90; 
         
         return {
            node: node,
            x: cx + (nx * earthRadius * 0.9), // 0.9 padding
            y: cy + (ny * earthRadius * 0.9)
         }
      });

      // Draw Connections First
      if (connections && connections.length > 0) {
          const mapDict = Object.fromEntries(this.mappedNodes.map(mn => [mn.node.id, mn]));
          this.ctx.lineWidth = 1;
          
          connections.forEach(conn => {
              const src = mapDict[conn.source];
              const tgt = mapDict[conn.target];
              if (src && tgt) {
                  const isCross = src.node.faction_id !== tgt.node.faction_id;
                  this.ctx.strokeStyle = isCross ? this.colors.neutral : this.getColorForFaction(src.node.faction_id);
                  this.ctx.globalAlpha = 0.5;
                  
                  this.ctx.beginPath();
                  this.ctx.moveTo(src.x, src.y);
                  this.ctx.lineTo(tgt.x, tgt.y);
                  this.ctx.stroke();
              }
          });
          this.ctx.globalAlpha = 1.0;
      }
      
      // Draw Nodes
      this.mappedNodes.forEach(mn => {
          this.ctx.fillStyle = this.getColorForFaction(mn.node.faction_id);
          const size = mn.node.faction_id === 1 ? 6 : 4;
          
          this.ctx.beginPath();
          this.ctx.arc(mn.x, mn.y, size, 0, 2 * Math.PI);
          this.ctx.fill();
      });
  }
}
