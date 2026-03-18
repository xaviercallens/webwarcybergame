/**
 * Neo-Hack: Gridlock — 3D Geographic Game Engine
 * Handles State, Combat Logic, and Global Node Gen
 */

import { GameRenderer } from './renderer.js';
import { initUI } from './ui-manager.js';
import { audio } from './audio-manager.js';

import { api } from './api-client.js';

export class GameEngine {
  constructor() {
    this.renderer = new GameRenderer('canvas-container');
    
    // Core state
    this.nodes = [];
    this.connections = [];
    this.attacks = [];
    this.selectedNodeId = null;
    this.currentEpoch = null;
    
    // Game loop
    this.lastTick = 0;
    this.lastApiPoll = 0;
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
    
    await this.renderer.init();
    
    // Fetch initial map from API
    await this.fetchWorldState();
    
    this.renderer.renderNodes(this.nodes);
    this.renderer.renderConnections(this.connections, this.nodes);
    
    // Start loop
    this.isPlaying = true;
    this.stats = { startTime: performance.now(), nodesCaptured: 0, nodesLost: 0, attacksLaunched: 0 };
    
    // Prevent overlapping requestAnimationFrame leaps!
    if (this._animationFrameId) cancelAnimationFrame(this._animationFrameId);
    this._boundGameLoop = this.gameLoop.bind(this);
    this._animationFrameId = requestAnimationFrame(this._boundGameLoop);
    
    console.log(`[SYS] Global Engine synced with Server.`);
  }

  bindEvents() {
    window.addEventListener('nodeClicked', (e) => {
      this.handleNodeClick(e.detail.nodeId);
    });

    // Keyboard Shortcuts for Highlighting & Attacking
    window.addEventListener('keydown', (e) => {
        if (!this.isPlaying) return;
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        if (!e.key) return;
        const key = e.key.toLowerCase();
        let needsRender = false;

        if (key === ' ') {
            e.preventDefault();
            this.isPlaying = !this.isPlaying;
            if (this.isPlaying) {
                this.lastApiPoll = performance.now();
                this._boundGameLoop = this.gameLoop.bind(this);
                this._animationFrameId = requestAnimationFrame(this._boundGameLoop);
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: '[SYS] TIME RESUMED', type: 'info' } }));
            } else {
                window.dispatchEvent(new CustomEvent('toast', { detail: { message: '[SYS] TIME PAUSED', type: 'warning' } }));
            }
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
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        if (!e.key) return;
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

  async fetchWorldState() {
      try {
          // Fetch parallel
          const [stateNodes, currentEpoch] = await Promise.all([
              api.getWorldState(),
              api.getCurrentEpoch()
          ]);
          
          this.currentEpoch = currentEpoch;
          
          if (stateNodes && stateNodes.length > 0) {
              this.nodes = stateNodes.map(n => ({
                  id: n.id,
                  name: n.name,
                  lat: parseFloat(n.lat),
                  lng: parseFloat(n.lng),
                  faction_id: n.faction_id,
                  firewall: n.defense_level,
                  maxFirewall: n.defense_level,
                  power: n.compute_output,
                  node_class: n.node_class
              }));
              
              // Basic structural generation for visual arcs since backend currently doesn't store hard edges
              this.generateVisualConnections();
              
              window.dispatchEvent(new CustomEvent('gameStateUpdate', { 
                  detail: { nodes: this.nodes, epoch: this.currentEpoch } 
              }));
          }
      } catch (e) {
          console.error('[Engine] Failed to sync with server:', e);
      }
  }

  generateVisualConnections() {
      this.connections = [];
      // Simply connect each node to its nearest 2 neighbors to create a web
      this.nodes.forEach(node => {
          let distances = [];
          this.nodes.forEach(target => {
              if (node.id === target.id) return;
              const dLat = target.lat - node.lat;
              const dLng = (target.lng - node.lng) * Math.cos(node.lat * Math.PI / 180);
              const d2 = dLat * dLat + dLng * dLng;
              distances.push({ id: target.id, dist: d2 });
          });
          distances.sort((a,b) => a.dist - b.dist);
          // Connect to top 2
          for(let i=0; i<Math.min(2, distances.length); i++) {
              // Ensure uniqueness
              const exists = this.connections.some(c => 
                  (c.source === node.id && c.target === distances[i].id) ||
                  (c.target === node.id && c.source === distances[i].id)
              );
              if (!exists) {
                  this.connections.push({ source: node.id, target: distances[i].id });
              }
          }
      });
  }

  // Generation logic removed in favor of Server-Side State

  handleNodeClick(nodeId) {
    const targetNode = this.nodes.find(n => n.id === nodeId);
    if (!targetNode) return;
    
    // Always select the node and show its info panel
    this.selectedNodeId = targetNode.id;
    window.dispatchEvent(new CustomEvent('nodeSelected', { detail: { node: targetNode } }));
  }

  async submitPlayerAction(actionType, cuTarget) {
      if (!this.selectedNodeId) return;
      
      if (!this.currentEpoch || this.currentEpoch.phase !== 'PLANNING') {
          window.dispatchEvent(new CustomEvent('toast', { detail: { message: 'ACTIONS ONLY PERMITTED IN PLANNING PHASE', type: 'error' } }));
          return;
      }
      
      try {
          const res = await api.submitAction(this.selectedNodeId, actionType, parseInt(cuTarget));
          window.dispatchEvent(new CustomEvent('toast', { detail: { message: `[${actionType}] CMD ACCEPTED. QUEUED FOR EPOCH TRANSITION.`, type: 'capture' } }));
          
          audio.playAttack();
          this.stats.attacksLaunched++;
          
          // Optionally add visual arc showing pending
          // ...
          
      } catch (e) {
          window.dispatchEvent(new CustomEvent('toast', { detail: { message: 'ERR: ' + e.message, type: 'error' } }));
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
    
    // Poll API state every 5 seconds
    if (time - this.lastApiPoll > 5000) {
        this.lastApiPoll = time;
        this.fetchWorldState();
    }
    
    if (delta > 1000) { // 1 tick per second for local rendering logic
      this.lastTick = time;
      this.tick();
    }
    
    this._animationFrameId = requestAnimationFrame(this._boundGameLoop);
  }

  tick() {
    // Re-render points colors 
    if (this.renderer.globe) {
      this.renderer.renderNodes(this.nodes);
    }
  }
}
