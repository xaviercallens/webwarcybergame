/**
 * Neo-Hack: Gridlock — 3D Geographic Game Engine
 * Handles State, Combat Logic, and Global Node Gen
 */

import { GameRenderer } from './renderer.js';
import { initUI } from './ui-manager.js';
import { audio } from './audio-manager.js';

export class GameEngine {
  constructor() {
    this.renderer = new GameRenderer('canvas-container');
    
    // Core state
    this.nodes = [];
    this.connections = [];
    this.attacks = [];
    this.selectedNodeId = null;
    
    // Game loop
    this.lastTick = 0;
    this.isPlaying = false;
    
    // Match Stats
    this.stats = {
      startTime: 0,
      nodesCaptured: 0,
      nodesLost: 0,
      attacksLaunched: 0
    };
    
    this.disableAI = false;
    this.promoMode = false;
    
    this.bindEvents();
  }

  async init() {
    await this.renderer.init();
    
    // Generate initial map (Geographic coordinates)
    this.generateProceduralMap();
    this.renderer.renderNodes(this.nodes);
    this.renderer.renderConnections(this.connections, this.nodes);
    
    // Start loop
    this.isPlaying = true;
    this.stats = { startTime: performance.now(), nodesCaptured: 0, nodesLost: 0, attacksLaunched: 0 };
    requestAnimationFrame(this.gameLoop.bind(this));
    
    console.log('[SYS] Global Game Engine started.');
  }

  bindEvents() {
    window.addEventListener('nodeClicked', (e) => {
      this.handleNodeClick(e.detail.nodeId);
    });
    
    window.addEventListener('viewChanged', (e) => {
      if (e.detail.view === 'game' && !this.renderer.globe) {
        this.init();
      }
    });
  }

  /**
   * Generates a global network of nodes
   * Core located in NA/EU with regional clusters
   */
  generateProceduralMap() {
    this.nodes = [];
    this.connections = [];
    
    const corePos = { lat: 48.8566, lng: 2.3522 }; // Paris pseudo-hub
    let currentId = 0;
    
    // 1. Center Hub
    this.nodes.push({
      id: currentId++,
      name: 'CORE-EU',
      owner: 'NEUTRAL',
      lat: corePos.lat,
      lng: corePos.lng,
      firewall: 150,
      maxFirewall: 150,
      power: 12
    });
    
    // 2. Trans-Atlantic / Eurasian Ring (6 nodes)
    const innerRadiusDeg = 25; // roughly 2500km
    const innerCount = 6;
    const innerNodeIds = [];
    
    for (let i = 0; i < innerCount; i++) {
      const angle = (Math.PI * 2 * i) / innerCount;
      const jitterAngle = angle + (Math.random() - 0.5) * 0.4;
      const jitterRadius = innerRadiusDeg + (Math.random() - 0.5) * 5;
      
      const lat = corePos.lat + Math.sin(jitterAngle) * jitterRadius;
      const lng = corePos.lng + Math.cos(jitterAngle) * jitterRadius * 2; // stretch longitude to account for mercator-ish spread
      
      let owner = 'NEUTRAL';
      if (i === 0) owner = 'PLAYER';
      else if (i === 3) owner = 'ENEMY';
      else if (i === 5) owner = 'ALLY';
      
      const id = currentId++;
      innerNodeIds.push(id);
      
      this.nodes.push({
        id,
        name: `SYS-${id.toString().padStart(2, '0')}`,
        owner,
        lat, lng,
        firewall: 100, maxFirewall: 100, power: 8
      });
      
      // Connect to hub
      this.connections.push({ source: id, target: 0 });
      
      // Connect to previous sibling in ring
      if (i > 0) {
        this.connections.push({ source: id, target: id - 1 });
      }
    }
    // close inner ring
    this.connections.push({ source: innerNodeIds[0], target: innerNodeIds[innerCount - 1] });
    
    // 3. Global Outpost Ring (12 nodes)
    const outerRadiusDeg = 55;
    const outerCount = 12;
    
    for (let i = 0; i < outerCount; i++) {
      const angle = (Math.PI * 2 * i) / outerCount;
      const ji = angle + (Math.random() - 0.5) * 0.2;
      const jr = outerRadiusDeg + (Math.random() - 0.5) * 10;
      
      const lat = corePos.lat + Math.sin(ji) * jr;
      const lng = corePos.lng + Math.cos(ji) * jr * 2.5;
      
      let owner = 'NEUTRAL';
      if (i === 0 || i === 1) owner = 'PLAYER';
      if (i === 6 || i === 7) owner = 'ENEMY';
      
      const id = currentId++;
      
      this.nodes.push({
        id,
        name: `EXT-${id.toString().padStart(2, '0')}`,
        owner,
        lat, lng,
        firewall: 80, maxFirewall: 80, power: 6
      });
      
      // Connect to closest inner node
      const closestInner = this.getClosestNodeGeo(lat, lng, innerNodeIds);
      this.connections.push({ source: id, target: closestInner });
      
      // Connect to previous sibling sometimes
      if (i > 0 && Math.random() > 0.3) {
        this.connections.push({ source: id, target: id - 1 });
      }
    }
  }

  // Very basic equirectangular distance approximation for quick lookup
  getClosestNodeGeo(lat, lng, candidateIds) {
    let closestId = candidateIds[0];
    let minD = Infinity;
    
    candidateIds.forEach(id => {
      const n = this.nodes.find(node => node.id === id);
      const dLat = n.lat - lat; 
      const dLng = (n.lng - lng) * Math.cos(lat * Math.PI / 180); // adjust for latitude convergence
      const d = dLat * dLat + dLng * dLng;
      
      if (d < minD) {
        minD = d;
        closestId = id;
      }
    });
    return closestId;
  }

  handleNodeClick(nodeId) {
    const targetNode = this.nodes.find(n => n.id === nodeId);
    if (!targetNode) return;
    
    // If we already have a player node selected, check for attack
    if (this.selectedNodeId !== null) {
      const sourceNode = this.nodes.find(n => n.id === this.selectedNodeId);
      
      if (sourceNode && sourceNode.owner === 'PLAYER' && sourceNode.id !== targetNode.id) {
        // Is it adjacent?
        const isAdjacent = this.connections.some(c => 
          (c.source === sourceNode.id && c.target === targetNode.id) ||
          (c.target === sourceNode.id && c.source === targetNode.id)
        );
        
        if (isAdjacent && targetNode.owner !== 'PLAYER') {
          this.initiateAttack(sourceNode.id, targetNode.id);
          this.selectedNodeId = null; // deselect after attacking
          return;
        }
      }
    }
    
    // Default selection
    if (targetNode.owner === 'PLAYER') {
      console.log('[COM] Player node targeted:', targetNode.name);
      this.selectedNodeId = targetNode.id;
      
      // Notify UI
      window.dispatchEvent(new CustomEvent('nodeSelected', { detail: { node: targetNode } }));
    } else {
      this.selectedNodeId = null; // deselect if clicking non-player without attack intent
      window.dispatchEvent(new CustomEvent('nodeSelected', { detail: { node: null } }));
    }
  }

  initiateAttack(sourceId, targetId) {
    console.log(`[ATK] Attack launched: ${sourceId} -> ${targetId}`);
    
    // Check if attack already exists
    if (!this.attacks.some(a => a.source === sourceId && a.target === targetId)) {
      this.attacks.push({ source: sourceId, target: targetId, power: 10 });
      const source = this.nodes.find(n => n.id === sourceId);
      if (source && source.owner === 'PLAYER') {
        this.stats.attacksLaunched++;
        audio.playAttack();
        window.dispatchEvent(new CustomEvent('attackLaunched'));
      }
    }
  }

  gameLoop(time) {
    if (!this.isPlaying) return;
    const delta = time - this.lastTick;
    
    if (delta > 1000) { // 1 tick per second for logic
      this.lastTick = time;
      this.tick();
    }
    
    requestAnimationFrame(this.gameLoop.bind(this));
  }

  tick() {
    // 1. Process Attacks & Damage
    for (let i = this.attacks.length - 1; i >= 0; i--) {
      const atk = this.attacks[i];
      const source = this.nodes.find(n => n.id === atk.source);
      const target = this.nodes.find(n => n.id === atk.target);
      
      // Cancel attack if source lost or target is same owner
      if (!source || !target || source.owner === target.owner) {
        this.attacks.splice(i, 1);
        continue;
      }
      
      // Apply damage
      target.firewall -= source.power;
      
      // Capture
      if (target.firewall <= 0) {
        if (source.owner === 'PLAYER') this.stats.nodesCaptured++;
        if (target.owner === 'PLAYER') this.stats.nodesLost++;
        
        target.owner = source.owner;
        target.firewall = target.maxFirewall * 0.25; // 25% health on capture
        this.attacks.splice(i, 1);
        console.log(`[SYS] Node ${target.name} captured by ${source.owner}!`);
        
        const msg = `[+] ROOT ACCESS GRANTED: ${target.name}`;
         window.dispatchEvent(new CustomEvent('toast', { detail: { message: msg, type: source.owner === 'PLAYER' ? 'capture' : 'lost' } }));
      }
    }

    // 2. Firewall regen
    this.nodes.forEach(n => {
      // Don't regen if under attack
      const isUnderAttack = this.attacks.some(a => a.target === n.id);
      if (!isUnderAttack && n.firewall < n.maxFirewall) {
        n.firewall = Math.min(n.maxFirewall, n.firewall + 2);
      }
    });
    
    // 3. Simple AI (Enemies attack adjacent non-enemy nodes)
    if (!this.disableAI) {
      this.nodes.forEach(node => {
        // In normal mode, only ENEMY acts. In promo mode, EVERYONE acts autonomously!
        const canAct = this.promoMode ? (node.owner !== 'NEUTRAL') : (node.owner === 'ENEMY');
        
        if (canAct && Math.random() < (this.promoMode ? 0.2 : 0.1)) { // Faster attacks in promo mode
          const adjacentLinks = this.connections.filter(c => c.source === node.id || c.target === node.id);
          const adjacentTargets = adjacentLinks.map(c => c.source === node.id ? c.target : c.source)
                                               .map(id => this.nodes.find(n => n.id === id))
                                               .filter(n => n && n.owner !== node.owner); // Attack anyone not on your team
                                               
          if (adjacentTargets.length > 0) {
            const target = adjacentTargets[Math.floor(Math.random() * adjacentTargets.length)];
            this.initiateAttack(node.id, target.id);
          }
        }
      });
    }
    
    // Re-render points colors 
    if (this.renderer.globe) {
      this.renderer.renderNodes(this.nodes);
      
      // Render active attacks as arcs over the globe
      this.renderer.renderConnections(this.attacks, this.nodes);
    }
    
    // Trigger UI updates for HUD
    window.dispatchEvent(new CustomEvent('gameStateUpdate', { detail: { nodes: this.nodes } }));
    
    // Check win/loss condition
    if (this.nodes.length > 0) {
      const pCount = this.nodes.filter(n => n.owner === 'PLAYER').length;
      if (pCount === 0 || pCount / this.nodes.length >= 0.75) {
        this.isPlaying = false;
        const isWin = pCount > 0;
        const timeSeconds = Math.floor((performance.now() - this.stats.startTime) / 1000);
        
        window.dispatchEvent(new CustomEvent('gameOver', { 
          detail: { 
            isWin,
            stats: {
                won: isWin,
                time_seconds: timeSeconds,
                nodes_captured: this.stats.nodesCaptured,
                nodes_lost: this.stats.nodesLost,
                attacks: this.stats.attacksLaunched
            }
          } 
        }));
      }
    }
  }
}
