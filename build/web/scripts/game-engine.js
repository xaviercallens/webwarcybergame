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

  async init(difficulty = 'INTERMEDIATE') {
    this.difficulty = difficulty;
    
    // Set AI aggression modifier
    switch(this.difficulty) {
        case 'BEGINNER': this.aiAggression = 0.05; break;
        case 'INTERMEDIATE': this.aiAggression = 0.1; break;
        case 'ADVANCED': this.aiAggression = 0.25; break;
        default: this.aiAggression = 0.1; break;
    }
    
    await this.renderer.init();
    
    // Generate initial map (Geographic coordinates)
    this.generateProceduralMap();
    this.renderer.renderNodes(this.nodes);
    this.renderer.renderConnections(this.connections, this.nodes);
    
    // Start loop
    this.isPlaying = true;
    this.stats = { startTime: performance.now(), nodesCaptured: 0, nodesLost: 0, attacksLaunched: 0 };
    
    // Prevent overlapping requestAnimationFrame leaps!
    if (this._animationFrameId) cancelAnimationFrame(this._animationFrameId);
    this._boundGameLoop = this.gameLoop.bind(this);
    this._animationFrameId = requestAnimationFrame(this._boundGameLoop);
    
    console.log(`[SYS] Global Engine started on ${this.difficulty} difficulty.`);
  }

  bindEvents() {
    window.addEventListener('nodeClicked', (e) => {
      this.handleNodeClick(e.detail.nodeId);
    });

    // Keyboard Shortcuts for Highlighting & Attacking
    window.addEventListener('keydown', (e) => {
        if (!this.isPlaying) return;
        const key = e.key.toLowerCase();
        let needsRender = false;

        // Auto-Attack (Spacebar)
        if (key === ' ') {
            e.preventDefault(); // Prevent page scrolling
            this.executeAutoAttack();
            return;
        }

        if (key === 'e' && !this.highlightEnemies) {
            this.highlightEnemies = true;
            needsRender = true;
        }
        if (key === 'a' && !this.highlightAttackable) {
            this.highlightAttackable = true;
            needsRender = true;
        }

        if (needsRender && this.renderer.globe) {
            this.renderer.renderNodes(this.nodes, this.highlightEnemies, this.highlightAttackable, this.connections);
        }
    });

    window.addEventListener('keyup', (e) => {
        if (!this.isPlaying) return;
        const key = e.key.toLowerCase();
        let needsRender = false;

        if (key === 'e' && this.highlightEnemies) {
            this.highlightEnemies = false;
            needsRender = true;
        }
        if (key === 'a' && this.highlightAttackable) {
            this.highlightAttackable = false;
            needsRender = true;
        }

        if (needsRender && this.renderer.globe) {
            this.renderer.renderNodes(this.nodes, this.highlightEnemies, this.highlightAttackable, this.connections);
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
        const lng = corePos.lng + Math.cos(jitterAngle) * jitterRadius * 2;
        
        // Guarantee conflict by placing PLAYER next to ENEMY and NEUTRAL
        let owner = 'NEUTRAL';
        if (i === 0) owner = 'PLAYER';
        else if (i === 1 || i === 4) owner = 'ENEMY';
        else if (i === 3) owner = 'ALLY';
        
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
        
        // Connect to previous sibling to form a solid inner ring
        if (i > 0) {
            this.connections.push({ source: id, target: id - 1 });
        }
    }
    // close inner ring
    this.connections.push({ source: innerNodeIds[0], target: innerNodeIds[innerCount - 1] });
    
    // 3. Global Outpost Ring (12 nodes)
    const outerRadiusDeg = 55;
    const outerCount = 12;
    const outerNodeIds = [];
    
    for (let i = 0; i < outerCount; i++) {
        const angle = (Math.PI * 2 * i) / outerCount;
        const ji = angle + (Math.random() - 0.5) * 0.2;
        const jr = outerRadiusDeg + (Math.random() - 0.5) * 10;
        
        const lat = corePos.lat + Math.sin(ji) * jr;
        const lng = corePos.lng + Math.cos(ji) * jr * 2.5;
        
        // Well-distributed layout
        let owner = 'NEUTRAL';
        let fw = 80;
      
        if (i === 0 || i === 1) {
            owner = 'PLAYER';
            if (this.difficulty === 'BEGINNER') fw = 150;
            if (this.difficulty === 'ADVANCED') fw = 60;
        }
        if (i === 6 || i === 7) {
            owner = 'ENEMY';
            if (this.difficulty === 'BEGINNER') fw = 40;
            if (this.difficulty === 'ADVANCED') fw = 120;
        }
      
        const id = currentId++;
        outerNodeIds.push(id);
      
        this.nodes.push({
            id,
            name: `EXT-${id.toString().padStart(2, '0')}`,
            owner,
            lat, lng,
            firewall: fw, maxFirewall: fw, power: 6
        });
        
        // Connect to closest inner node
        const closestInner = this.getClosestNodeGeo(lat, lng, innerNodeIds);
        this.connections.push({ source: id, target: closestInner });
        
        // Always connect outer nodes in a solid ring so no node is an island
        if (i > 0) {
            this.connections.push({ source: id, target: id - 1 });
        }
    }
    // Close outer ring
    this.connections.push({ source: outerNodeIds[0], target: outerNodeIds[outerCount - 1] });
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

  executeAutoAttack() {
      const playerNodes = this.nodes.filter(n => n.owner === 'PLAYER');
      if (playerNodes.length === 0) return;
      
      let source = null;
      let target = null;
      
      // If a player node is currently selected, prioritize attacking from it
      if (this.selectedNodeId) {
          const selected = playerNodes.find(n => n.id === this.selectedNodeId);
          if (selected) {
              target = this.findBestTargetForNode(selected);
              if (target) source = selected;
          }
      }
      
      // If no valid target found from selected node, search all player nodes globally
      if (!target) {
          for (const pNode of playerNodes) {
              target = this.findBestTargetForNode(pNode);
              if (target) {
                  source = pNode;
                  break;
              }
          }
      }
      
      if (source && target) {
          // Launch the attack
          this.initiateAttack(source.id, target.id);
          // Visually select the node that launched the attack
          this.selectedNodeId = source.id;
          window.dispatchEvent(new CustomEvent('nodeSelected', { detail: { node: source } }));
      } else {
          // If the player spams Spacebar but there is absolutely nothing to attack
          window.dispatchEvent(new CustomEvent('toast', { detail: { message: 'NO VALID TARGETS IN RANGE', type: 'info' } }));
      }
  }
  
  findBestTargetForNode(sourceNode) {
      // Find all adjacent node IDs based on the connections graph
      const adjacentLinks = this.connections.filter(c => c.source === sourceNode.id || c.target === sourceNode.id);
      const adjacentNodes = adjacentLinks.map(c => c.source === sourceNode.id ? c.target : c.source)
                                         .map(id => this.nodes.find(n => n.id === id));
                                         
      // Prefer ENEMY targets first
      const enemyTargets = adjacentNodes.filter(n => n && n.owner === 'ENEMY');
      if (enemyTargets.length > 0) return enemyTargets[Math.floor(Math.random() * enemyTargets.length)];
      
      // Fallback to capturing NEUTRAL or ALLY nodes
      const neutralTargets = adjacentNodes.filter(n => n && n.owner !== 'PLAYER');
      if (neutralTargets.length > 0) return neutralTargets[Math.floor(Math.random() * neutralTargets.length)];
      
      return null;
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
    
    this._animationFrameId = requestAnimationFrame(this._boundGameLoop);
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
        
        if (canAct && Math.random() < (this.promoMode ? 0.2 : this.aiAggression)) {
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
