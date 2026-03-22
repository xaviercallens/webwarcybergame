/**
 * Neo-Hack: Gridlock v4.1 — Mesh Hub Component
 * Canvas-based network topology renderer with interactive nodes
 */

export class MeshHub {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.nodes = [];
    this.edges = [];
    this.hoveredNode = null;
    this.selectedNode = null;
    this.animFrame = null;
    this.time = 0;
    this.packetParticles = [];

    // Color constants matching tokens.css
    this.COLORS = {
      bg: '#0a0e17',
      accent: '#00FFDD',
      accentDim: 'rgba(0, 255, 221, 0.15)',
      scarlet: '#FF0055',
      amber: '#FFCC00',
      stable: '#00FF88',
      textMuted: '#667788',
      edgeLine: 'rgba(0, 255, 221, 0.12)',
      edgeActive: 'rgba(0, 255, 221, 0.35)',
      ghostNode: 'rgba(0, 255, 221, 0.2)',
      warningNode: 'rgba(255, 204, 0, 0.6)',
      criticalNode: 'rgba(255, 0, 85, 0.6)',
    };

    this._initNodes();
    this._initEdges();
    this._initPackets();
    this._bindEvents();
    this._resize();
    window.addEventListener('resize', () => this._resize());
  }

  _initNodes() {
    // Generate mesh topology nodes based on Stitch design
    const nodeData = [
      { id: 'ROOT_CORE', x: 0.5, y: 0.55, type: 'core', icon: '✦', status: 'stable' },
      { id: 'NODE_SEC_A', x: 0.65, y: 0.7, type: 'server', icon: '⊞', status: 'stable' },
      { id: 'NODE_PR_01', x: 0.42, y: 0.3, type: 'workstation', icon: '⊡', status: 'stable' },
      { id: 'NODE_GW_02', x: 0.25, y: 0.2, type: 'gateway', icon: '◆', status: 'stable' },
      { id: 'ALERT_H_04', x: 0.6, y: 0.32, type: 'workstation', icon: '▣', status: 'warning' },
      { id: 'SYS_INT_DET', x: 0.75, y: 0.4, type: 'alert', icon: '⚠', status: 'warning' },
      { id: 'UPLINK_EST', x: 0.82, y: 0.25, type: 'uplink', icon: '●', status: 'stable' },
      { id: 'ENC_L3_FAIL', x: 0.82, y: 0.3, type: 'alert', icon: '●', status: 'critical' },
      { id: 'NODE_GHOST_1', x: 0.35, y: 0.48, type: 'ghost', icon: '⊡', status: 'ghost' },
      { id: 'NODE_GHOST_2', x: 0.78, y: 0.58, type: 'ghost', icon: '⊡', status: 'ghost' },
      { id: 'NODE_GHOST_3', x: 0.2, y: 0.65, type: 'ghost', icon: '⊡', status: 'ghost' },
      { id: 'NODE_GHOST_4', x: 0.55, y: 0.15, type: 'ghost', icon: '⊡', status: 'ghost' },
      { id: 'CORE_VALVE', x: 0.52, y: 0.45, type: 'core', icon: '✶', status: 'stable' },
      { id: 'SCAN_DEPTH', x: 0.38, y: 0.72, type: 'scanner', icon: '◎', status: 'stable' },
    ];

    this.nodes = nodeData.map(n => ({
      ...n,
      screenX: 0,
      screenY: 0,
      radius: n.type === 'core' ? 22 : n.type === 'ghost' ? 14 : 16,
      pulsePhase: Math.random() * Math.PI * 2,
    }));
  }

  _initEdges() {
    // Define mesh connections (redundant pathing)
    const connections = [
      ['ROOT_CORE', 'NODE_SEC_A'],
      ['ROOT_CORE', 'CORE_VALVE'],
      ['ROOT_CORE', 'NODE_PR_01'],
      ['CORE_VALVE', 'NODE_PR_01'],
      ['CORE_VALVE', 'ALERT_H_04'],
      ['NODE_PR_01', 'NODE_GW_02'],
      ['NODE_PR_01', 'ALERT_H_04'],
      ['ALERT_H_04', 'SYS_INT_DET'],
      ['SYS_INT_DET', 'UPLINK_EST'],
      ['SYS_INT_DET', 'ENC_L3_FAIL'],
      ['NODE_SEC_A', 'SCAN_DEPTH'],
      ['NODE_GHOST_1', 'CORE_VALVE'],
      ['NODE_GHOST_2', 'NODE_SEC_A'],
      ['NODE_GHOST_3', 'SCAN_DEPTH'],
      ['NODE_GHOST_4', 'NODE_GW_02'],
      ['NODE_GW_02', 'UPLINK_EST'],
      ['ROOT_CORE', 'NODE_GHOST_2'],
    ];

    this.edges = connections.map(([fromId, toId]) => ({
      from: this.nodes.find(n => n.id === fromId),
      to: this.nodes.find(n => n.id === toId),
      isGhost: fromId.includes('GHOST') || toId.includes('GHOST'),
    })).filter(e => e.from && e.to);
  }

  _initPackets() {
    // Create animated packets flowing along edges
    this.packetParticles = this.edges
      .filter(e => !e.isGhost)
      .slice(0, 8)
      .map((edge, i) => ({
        edge,
        progress: Math.random(),
        speed: 0.003 + Math.random() * 0.004,
        size: 2 + Math.random() * 2,
      }));
  }

  _bindEvents() {
    this.canvas.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      this.hoveredNode = null;
      for (const node of this.nodes) {
        const dx = mx - node.screenX;
        const dy = my - node.screenY;
        if (dx * dx + dy * dy < (node.radius + 8) * (node.radius + 8)) {
          this.hoveredNode = node;
          this.canvas.style.cursor = 'pointer';
          break;
        }
      }
      if (!this.hoveredNode) this.canvas.style.cursor = 'default';
    });

    this.canvas.addEventListener('click', () => {
      if (this.hoveredNode) {
        this.selectedNode = this.hoveredNode;
        window.dispatchEvent(new CustomEvent('meshNodeSelected', { detail: { node: this.selectedNode } }));
      }
    });
  }

  _resize() {
    const parent = this.canvas.parentElement;
    if (!parent) return;
    this.canvas.width = parent.clientWidth;
    this.canvas.height = parent.clientHeight;
    // Update screen positions
    this.nodes.forEach(n => {
      n.screenX = n.x * this.canvas.width;
      n.screenY = n.y * this.canvas.height;
    });
  }

  start() {
    const render = () => {
      this.time += 0.016;
      this._draw();
      this.animFrame = requestAnimationFrame(render);
    };
    render();
  }

  stop() {
    if (this.animFrame) cancelAnimationFrame(this.animFrame);
  }

  _draw() {
    const { ctx, canvas } = this;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Background grid
    this._drawGrid();

    // Draw edges
    this.edges.forEach(e => this._drawEdge(e));

    // Draw packet particles
    this._drawPackets();

    // Draw nodes (ghosts first, then normal)
    const ghosts = this.nodes.filter(n => n.status === 'ghost');
    const normals = this.nodes.filter(n => n.status !== 'ghost');
    ghosts.forEach(n => this._drawNode(n));
    normals.forEach(n => this._drawNode(n));

    // Draw labels for hovered/selected
    if (this.hoveredNode) this._drawLabel(this.hoveredNode);
    if (this.selectedNode && this.selectedNode !== this.hoveredNode) {
      this._drawLabel(this.selectedNode);
    }
  }

  _drawGrid() {
    const { ctx, canvas } = this;
    ctx.strokeStyle = 'rgba(0, 255, 221, 0.03)';
    ctx.lineWidth = 0.5;
    const spacing = 40;
    for (let x = 0; x < canvas.width; x += spacing) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += spacing) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }
  }

  _drawEdge(edge) {
    const { ctx } = this;
    const { from, to, isGhost } = edge;

    ctx.beginPath();
    ctx.moveTo(from.screenX, from.screenY);
    ctx.lineTo(to.screenX, to.screenY);

    if (isGhost) {
      ctx.strokeStyle = 'rgba(0, 255, 221, 0.06)';
      ctx.setLineDash([6, 8]);
      ctx.lineWidth = 1;
    } else {
      ctx.strokeStyle = this.COLORS.edgeLine;
      ctx.setLineDash([]);
      ctx.lineWidth = 1;
    }
    ctx.stroke();
    ctx.setLineDash([]);

    // Small dots at midpoint
    if (!isGhost) {
      const mx = (from.screenX + to.screenX) / 2;
      const my = (from.screenY + to.screenY) / 2;
      ctx.fillStyle = this.COLORS.accentDim;
      ctx.beginPath();
      ctx.arc(mx, my, 2, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  _drawPackets() {
    const { ctx } = this;
    this.packetParticles.forEach(p => {
      p.progress += p.speed;
      if (p.progress > 1) p.progress = 0;

      const { from, to } = p.edge;
      const px = from.screenX + (to.screenX - from.screenX) * p.progress;
      const py = from.screenY + (to.screenY - from.screenY) * p.progress;

      ctx.fillStyle = this.COLORS.accent;
      ctx.shadowColor = this.COLORS.accent;
      ctx.shadowBlur = 6;
      ctx.beginPath();
      ctx.arc(px, py, p.size, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
    });
  }

  _drawNode(node) {
    const { ctx, time } = this;
    const { screenX: x, screenY: y, radius, status, type, icon } = node;
    const isHovered = node === this.hoveredNode;
    const isSelected = node === this.selectedNode;
    const pulse = Math.sin(time * 2 + node.pulsePhase) * 0.5 + 0.5;

    // Node background
    ctx.save();
    if (status === 'ghost') {
      ctx.globalAlpha = 0.25 + pulse * 0.15;
      ctx.strokeStyle = this.COLORS.accent;
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      ctx.strokeRect(x - radius, y - radius, radius * 2, radius * 2);
      ctx.setLineDash([]);
    } else {
      let borderColor = this.COLORS.accent;
      let bgColor = 'rgba(10, 14, 23, 0.9)';

      if (status === 'warning') {
        borderColor = this.COLORS.amber;
        bgColor = 'rgba(255, 204, 0, 0.08)';
      } else if (status === 'critical') {
        borderColor = this.COLORS.scarlet;
        bgColor = 'rgba(255, 0, 85, 0.08)';
      }

      if (type === 'core') {
        // Core nodes are larger with glow
        ctx.shadowColor = borderColor;
        ctx.shadowBlur = isHovered ? 20 : 10;
      }

      ctx.fillStyle = bgColor;
      ctx.strokeStyle = borderColor;
      ctx.lineWidth = isHovered || isSelected ? 2 : 1;
      ctx.fillRect(x - radius, y - radius, radius * 2, radius * 2);
      ctx.strokeRect(x - radius, y - radius, radius * 2, radius * 2);
      ctx.shadowBlur = 0;

      // Corner brackets for selected
      if (isSelected) {
        const br = 6;
        ctx.strokeStyle = this.COLORS.accent;
        ctx.lineWidth = 2;
        // Top-left
        ctx.beginPath();
        ctx.moveTo(x - radius - 4, y - radius + br);
        ctx.lineTo(x - radius - 4, y - radius - 4);
        ctx.lineTo(x - radius + br, y - radius - 4);
        ctx.stroke();
        // Bottom-right
        ctx.beginPath();
        ctx.moveTo(x + radius + 4, y + radius - br);
        ctx.lineTo(x + radius + 4, y + radius + 4);
        ctx.lineTo(x + radius - br, y + radius + 4);
        ctx.stroke();
      }
    }

    // Node icon
    ctx.fillStyle = status === 'ghost' ? this.COLORS.accentDim :
                    status === 'warning' ? this.COLORS.amber :
                    status === 'critical' ? this.COLORS.scarlet :
                    this.COLORS.accent;
    ctx.font = `${radius * 0.9}px "Share Tech Mono", monospace`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(icon, x, y);
    ctx.restore();
  }

  _drawLabel(node) {
    const { ctx } = this;
    const { screenX: x, screenY: y, id, status, radius } = node;

    const labelY = y - radius - 12;
    const text = id;

    ctx.font = '11px "Share Tech Mono", monospace';
    const metrics = ctx.measureText(text);
    const padding = 6;
    const labelW = metrics.width + padding * 2;

    // Background
    ctx.fillStyle = 'rgba(10, 14, 23, 0.9)';
    ctx.fillRect(x - labelW / 2, labelY - 8, labelW, 16);

    // Border
    ctx.strokeStyle = status === 'warning' ? this.COLORS.amber :
                      status === 'critical' ? this.COLORS.scarlet :
                      this.COLORS.accent;
    ctx.lineWidth = 1;
    ctx.strokeRect(x - labelW / 2, labelY - 8, labelW, 16);

    // Text
    ctx.fillStyle = ctx.strokeStyle;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, x, labelY);
  }
}
