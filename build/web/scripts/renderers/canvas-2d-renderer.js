/**
 * 2D Canvas Fallback Renderer for Neo-Hack: Gridlock
 * Used when WebGL is unavailable (e.g., in headless/sandboxed environments)
 * Renders nodes as circles, connections as lines, with status colors
 */

export class Canvas2DRenderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.gameState = null;
    this.selectedNodeId = null;
    this.hoveredNodeId = null;
    this.nodePositions = new Map();
    this.animationFrameId = null;
    
    // Layout
    this.padding = 40;
    this.nodeRadius = 20;
    this.centerX = canvas.width / 2;
    this.centerY = canvas.height / 2;
    
    // Colors
    this.colors = {
      background: '#0a0e27',
      connection: '#2a4a6a',
      nodeDefender: '#4a6a9a',
      nodeAttacker: '#d94a4a',
      nodeCompromised: '#ff6b6b',
      nodeSelected: '#ffd700',
      nodeHovered: '#ffff00',
      text: '#00ff88',
      textDark: '#001a00',
    };
    
    this.setupEventListeners();
  }
  
  setupEventListeners() {
    this.canvas.addEventListener('click', (e) => this.handleClick(e));
    this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
    this.canvas.addEventListener('mouseleave', () => {
      this.hoveredNodeId = null;
    });
  }
  
  handleClick(e) {
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    for (const [nodeId, pos] of this.nodePositions) {
      const dist = Math.hypot(x - pos.x, y - pos.y);
      if (dist <= this.nodeRadius + 5) {
        this.selectedNodeId = nodeId;
        // Dispatch custom event for node selection
        this.canvas.dispatchEvent(new CustomEvent('nodeSelected', { detail: { nodeId } }));
        break;
      }
    }
  }
  
  handleMouseMove(e) {
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    this.hoveredNodeId = null;
    for (const [nodeId, pos] of this.nodePositions) {
      const dist = Math.hypot(x - pos.x, y - pos.y);
      if (dist <= this.nodeRadius + 5) {
        this.hoveredNodeId = nodeId;
        this.canvas.style.cursor = 'pointer';
        return;
      }
    }
    this.canvas.style.cursor = 'default';
  }
  
  update(gameState) {
    this.gameState = gameState;
    this.render();
  }
  
  render() {
    if (!this.gameState) return;
    
    // Clear canvas
    this.ctx.fillStyle = this.colors.background;
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    
    // Draw connections first (so they appear behind nodes)
    this.drawConnections();
    
    // Draw nodes
    this.drawNodes();
    
    // Draw HUD
    this.drawHUD();
  }
  
  drawConnections() {
    const nodes = this.gameState.nodes || [];
    const connections = this.gameState.connections || [];
    
    // Calculate node positions in a circle
    this.nodePositions.clear();
    const numNodes = nodes.length;
    const radius = Math.min(this.canvas.width, this.canvas.height) / 2 - this.padding - this.nodeRadius;
    
    nodes.forEach((node, idx) => {
      const angle = (idx / numNodes) * Math.PI * 2 - Math.PI / 2;
      const x = this.centerX + Math.cos(angle) * radius;
      const y = this.centerY + Math.sin(angle) * radius;
      this.nodePositions.set(node.id, { x, y });
    });
    
    // Draw connections
    this.ctx.strokeStyle = this.colors.connection;
    this.ctx.lineWidth = 2;
    
    connections.forEach(conn => {
      const from = this.nodePositions.get(conn.source);
      const to = this.nodePositions.get(conn.target);
      
      if (from && to) {
        this.ctx.beginPath();
        this.ctx.moveTo(from.x, from.y);
        this.ctx.lineTo(to.x, to.y);
        this.ctx.stroke();
      }
    });
  }
  
  drawNodes() {
    const nodes = this.gameState.nodes || [];
    const compromisedNodes = this.gameState.compromised_nodes || [];
    
    nodes.forEach(node => {
      const pos = this.nodePositions.get(node.id);
      if (!pos) return;
      
      // Determine node color
      let fillColor = this.colors.nodeDefender;
      if (compromisedNodes.includes(node.id)) {
        fillColor = this.colors.nodeCompromised;
      } else if (node.owned_by === 'attacker') {
        fillColor = this.colors.nodeAttacker;
      }
      
      // Draw node circle
      this.ctx.fillStyle = fillColor;
      this.ctx.beginPath();
      this.ctx.arc(pos.x, pos.y, this.nodeRadius, 0, Math.PI * 2);
      this.ctx.fill();
      
      // Draw border if selected or hovered
      if (node.id === this.selectedNodeId) {
        this.ctx.strokeStyle = this.colors.nodeSelected;
        this.ctx.lineWidth = 3;
      } else if (node.id === this.hoveredNodeId) {
        this.ctx.strokeStyle = this.colors.nodeHovered;
        this.ctx.lineWidth = 2;
      } else {
        this.ctx.strokeStyle = '#ffffff';
        this.ctx.lineWidth = 1;
      }
      this.ctx.beginPath();
      this.ctx.arc(pos.x, pos.y, this.nodeRadius, 0, Math.PI * 2);
      this.ctx.stroke();
      
      // Draw node ID
      this.ctx.fillStyle = this.colors.text;
      this.ctx.font = 'bold 12px monospace';
      this.ctx.textAlign = 'center';
      this.ctx.textBaseline = 'middle';
      this.ctx.fillText(node.id, pos.x, pos.y);
    });
  }
  
  drawHUD() {
    const gs = this.gameState;
    
    // Draw turn info (top-left)
    this.ctx.fillStyle = this.colors.text;
    this.ctx.font = '14px monospace';
    this.ctx.textAlign = 'left';
    this.ctx.textBaseline = 'top';
    
    const hudLines = [
      `Turn: ${gs.current_turn}/${gs.max_turns}`,
      `Player: ${gs.current_player === 'attacker' ? 'ATTACKER' : 'DEFENDER'}`,
      `AP: ${gs.action_points_remaining}`,
      `Alert: ${gs.alert_level}/100`,
      `Stealth: ${gs.stealth_level}%`,
    ];
    
    hudLines.forEach((line, idx) => {
      this.ctx.fillText(line, 10, 10 + idx * 20);
    });
    
    // Draw legend (bottom-left)
    const legendY = this.canvas.height - 100;
    this.ctx.font = '12px monospace';
    
    const legend = [
      { color: this.colors.nodeDefender, label: 'Defender' },
      { color: this.colors.nodeAttacker, label: 'Attacker' },
      { color: this.colors.nodeCompromised, label: 'Compromised' },
    ];
    
    legend.forEach((item, idx) => {
      this.ctx.fillStyle = item.color;
      this.ctx.fillRect(10, legendY + idx * 20, 12, 12);
      this.ctx.fillStyle = this.colors.text;
      this.ctx.fillText(item.label, 28, legendY + idx * 20 + 2);
    });
    
    // Draw status (bottom-right)
    this.ctx.textAlign = 'right';
    const statusLines = [
      `Compromised: ${gs.compromised_nodes?.length || 0}`,
      `Discovered: ${gs.discovered_nodes?.length || 0}`,
      `Detected: ${gs.detected_nodes?.length || 0}`,
    ];
    
    statusLines.forEach((line, idx) => {
      this.ctx.fillStyle = this.colors.text;
      this.ctx.fillText(line, this.canvas.width - 10, 10 + idx * 20);
    });
  }
  
  selectNode(nodeId) {
    this.selectedNodeId = nodeId;
    this.render();
  }
  
  deselectNode() {
    this.selectedNodeId = null;
    this.render();
  }
  
  dispose() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
  }
}
