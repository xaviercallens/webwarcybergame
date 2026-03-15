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
        
        // If Vite HMR has exhausted WebGL contexts (16 limit block), self-heal by forcing a hard page reload.
        if (e.message && e.message.toLowerCase().includes('webgl')) {
            if (!sessionStorage.getItem('webgl_reloaded')) {
                console.warn('[SYS] Triggering automatic GC reload to flush orphaned WebGL contexts...');
                sessionStorage.setItem('webgl_reloaded', 'true');
                window.location.reload();
                return;
            } else {
                // If it already reloaded once, the browser is permanently unable to render WebGL.
                const errDiv = document.createElement('div');
                errDiv.style.cssText = 'position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); color:var(--color-enemy); background:rgba(0,0,0,0.9); padding:2rem; border:2px solid var(--color-enemy); z-index:99999; font-family:var(--font-mono); text-align:center;';
                errDiv.innerHTML = '<h2>CRITICAL ERROR</h2><p>Your browser or OS does not support WebGL 3D Hardware Acceleration.</p><button onclick="window.location.reload()" style="margin-top:1rem; padding:0.5rem 1rem; cursor:pointer;">RETRY</button>';
                document.body.appendChild(errDiv);
                return;
            }
        }
        throw e;
    }

    // Load GeoJSON for landmasses
    try {
      const response = await fetch('/datasets/ne_110m_admin_0_countries.geojson');
      const countries = await response.json();
      
      this.globe
        .hexPolygonsData(countries.features)
        .hexPolygonResolution(3)
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
      .pointResolution(32);
      
    // Custom label text for nodes
    this.globe
      .labelsData(pointsData)
      .labelLat('lat')
      .labelLng('lng')
      .labelText('name')
      .labelSize(1.5)
      .labelDotRadius(0)
      .labelColor('color')
      .labelResolution(2)
      .labelAltitude(d => d.size + 0.05);
  }

  renderConnections(connections, nodes) {
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
}
