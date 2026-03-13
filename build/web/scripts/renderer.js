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

    // Initialize Globe.gl with relaxed WebGL config for Chrome OS / headless fallback
    this.globe = Globe({ rendererConfig: { antialias: true, alpha: true, powerPreference: 'default', failIfMajorPerformanceCaveat: false } })(container)
      .globeImageUrl('//unpkg.com/three-globe/example/img/earth-water.png') // Fallback base texture (optional, can omit for pure wireframe)
      .backgroundColor('rgba(0,0,0,0)') // Transparent background to show our CSS space gradient
      .showAtmosphere(true)
      .atmosphereColor(this.colors.neutral)
      .atmosphereAltitude(0.15);

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

  getColorForFaction(faction) {
    const isColorblind = document.documentElement.getAttribute('data-colorblind') === 'true';
    switch(faction) {
      case 'PLAYER': return isColorblind ? '#3380FF' : this.colors.player;
      case 'ENEMY': return isColorblind ? '#FF8000' : this.colors.enemy;
      case 'ALLY': return isColorblind ? '#E6CC33' : this.colors.ally;
      
      // Promo Factions
      case 'USA': return '#4488FF';    // Tech Blue
      case 'CHINA': return '#FF1111';  // Security Red
      case 'EUROPE': return '#FFCC00'; // Grid Gold
      case 'RUSSIA': return '#8800FF'; // Rogue Purple
      case 'APAC': return '#00FF88';   // Bio Green
      
      default: return this.colors.neutral; 
    }
  }

  renderNodes(nodes) {
    this.nodeMap.clear();
    nodes.forEach(n => this.nodeMap.set(n.id, n));

    const pointsData = nodes.map(node => ({
      id: node.id,
      lat: node.lat,
      lng: node.lng,
      size: node.owner === 'PLAYER' || node.owner === 'ENEMY' ? 0.3 : 0.15,
      color: this.getColorForFaction(node.owner),
      name: node.name
    }));

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
    const arcsData = connections.map(conn => {
      const source = this.nodeMap.get(conn.source);
      const target = this.nodeMap.get(conn.target);
      if (!source || !target) return null;
      
      const isCrossFaction = source.owner !== target.owner;
      const color = isCrossFaction ? this.colors.neutral : this.getColorForFaction(source.owner);
      
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
