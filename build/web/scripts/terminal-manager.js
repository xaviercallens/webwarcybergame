import { api } from './api-client.js';

export class TerminalManager {
  constructor(gameEngine) {
    this.gameEngine = gameEngine;
    this.panel = document.getElementById('terminal-panel');
    this.input = document.getElementById('terminal-input');
    this.output = document.getElementById('terminal-output');
    this.isOpen = false;

    this.bindEvents();
  }

  bindEvents() {
    window.addEventListener('keydown', (e) => {
      if (window.AppState && window.AppState.currentView !== 'game') return;
      
      // Don't toggle if user is typing in any input or textarea
      const tag = document.activeElement ? document.activeElement.tagName : '';
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;
      
      if (e.key === '`' || e.key === '~' || (e.key.toLowerCase() === 'c' && !this.isOpen)) {
        e.preventDefault();
        this.toggle();
      }
      // Allow Escape to close the terminal
      if (e.key === 'Escape' && this.isOpen) {
        e.preventDefault();
        this.toggle();
      }
    });

    if (this.input) {
      this.input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          const cmd = this.input.value.trim();
          if (cmd) {
            this.print(`> ${cmd}`, 'var(--color-text-muted)');
            this.processCommand(cmd);
            this.input.value = '';
          }
        }
      });
    }
  }

  toggle() {
    this.isOpen = !this.isOpen;
    if (this.panel) {
      if (this.isOpen) {
        this.panel.style.display = 'flex';
        setTimeout(() => this.input && this.input.focus(), 50);
      } else {
        this.panel.style.display = 'none';
        this.input && this.input.blur();
      }
    }
  }

  print(text, color = 'var(--color-player)') {
    if (!this.output) return;
    const line = document.createElement('div');
    line.style.color = color;
    line.style.marginTop = '0.25rem';
    line.innerText = text;
    this.output.appendChild(line);
    // Auto-scroll
    this.output.scrollTop = this.output.scrollHeight;
  }

  resolveNode(input) {
    // Try numeric ID first
    const numId = parseInt(input);
    if (!isNaN(numId)) {
      return this.gameEngine.nodes.find(n => n.id === numId) || null;
    }
    // Try node name (case-insensitive)
    const nameLower = input.toLowerCase();
    return this.gameEngine.nodes.find(n => n.name && n.name.toLowerCase() === nameLower) || null;
  }

  async processCommand(commandStr) {
    const parts = commandStr.trim().split(/\s+/);
    if (parts.length === 0 || !parts[0]) return;
    const cmd = parts[0].toLowerCase();
    const args = parts.slice(1);

    if (cmd === '/help') {
      this.print('AVAILABLE COMMANDS:', '#fff');
      this.print('  /scan [node_name or id]   - Reveal node stats');
      this.print('  /breach [node_name or id] - Launch attack on enemy node (Costs CU)');
      this.print('  /defend [node_name or id] - Reinforce owned node (Costs CU)');
      this.print('  /diplomacy                - Open the Secure Diplomatic Channel');
      this.print('  /status                   - Show global faction stats');
      this.print('  /epoch                    - Show current epoch info');
      this.print('  /clear                    - Clear terminal output');
      return;
    }

    if (cmd === '/diplomacy' || cmd === '/dip') {
       const modal = document.getElementById('modal-diplomacy');
       if (modal) {
           modal.style.display = 'flex';
           modal.classList.add('active');
           this.print('[*] SECURE DIPLOMATIC CHANNEL OPENED.', 'var(--color-accent)');
       } else {
           this.print('ERR: DIPLOMATIC MODULE OFFLINE.', 'var(--color-enemy)');
       }
       return;
    }

    if (cmd === '/clear') {
      if (this.output) {
        this.output.innerHTML = '';
        this.print('Neo-Hack OS v2.0.1 - Terminal Access Granted. Type /help for commands.', 'var(--color-accent)');
      }
      return;
    }

    if (cmd === '/epoch') {
      if (!this.gameEngine.currentEpoch) {
         this.print('ERR: Epoch engine offline or desynced.', 'var(--color-enemy)');
         return;
      }
      const epoch = this.gameEngine.currentEpoch;
      this.print(`EPOCH ${epoch.number} - PHASE: ${epoch.phase}`);
      this.print(`Transition expected at: ${epoch.ended_at} UTC`, 'var(--color-text-muted)');
      return;
    }

    if (cmd === '/status') {
      const nodes = this.gameEngine.nodes;
      let counts = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
      nodes.forEach(n => {
        if (counts[n.faction_id] !== undefined) counts[n.faction_id]++;
      });
      const total = nodes.length;
      if (total === 0) {
          this.print('ERR: World state uninitialized.', 'var(--color-enemy)');
          return;
      }
      this.print('GLOBAL INFLUENCE STATUS:', '#fff');
      this.print(`  Silicon Valley (Player): ${counts[1]} nodes (${Math.round(counts[1]/total*100)}%)`, 'var(--color-player)');
      this.print(`  Iron Grid:               ${counts[2]} nodes (${Math.round(counts[2]/total*100)}%)`, 'var(--color-enemy)');
      this.print(`  Silk Road Coalition:     ${counts[3]} nodes (${Math.round(counts[3]/total*100)}%)`, '#FFCC00');
      this.print(`  Euro Nexus:              ${counts[4]} nodes (${Math.round(counts[4]/total*100)}%)`, 'var(--color-ally)');
      this.print(`  Pacific Vanguard:        ${counts[5]} nodes (${Math.round(counts[5]/total*100)}%)`, '#00FF88');
      return;
    }

    if (cmd === '/scan') {
      if (!args[0]) {
          this.print('ERR: Missing target. Usage: /scan [node_name or id]', 'var(--color-enemy)');
          return;
      }
      const node = this.resolveNode(args.join(' '));
      if (!node) {
          this.print(`ERR: Node '${args.join(' ')}' not found. Use /status to see nodes.`, 'var(--color-warning)');
          return;
      }
      this.print(`SCAN RESULTS FOR: ${node.name} [ID: ${node.id}]`, '#fff');
      this.print(`  Owner Faction ID: ${node.faction_id}`);
      this.print(`  Node Class:       ${node.node_class}`);
      this.print(`  Firewall:         ${node.firewall}`);
      this.print(`  Power Output:     ${node.power} TB/s`);
      return;
    }

    if (cmd === '/breach') {
       if (!args[0]) {
           this.print('ERR: Missing target. Usage: /breach [node_name or id]', 'var(--color-enemy)');
           return;
       }
       if (this.gameEngine.currentEpoch && this.gameEngine.currentEpoch.phase !== 'PLANNING') {
           this.print('ERR: ACTIONS ONLY PERMITTED IN PLANNING PHASE', 'var(--color-enemy)');
           return;
       }
       const node = this.resolveNode(args.join(' '));
       if (!node) {
           this.print(`ERR: Node '${args.join(' ')}' not found.`, 'var(--color-warning)');
           return;
       }
       const cu = 25;
       try {
           const res = await api.submitAction(node.id, 'BREACH', cu);
           this.print(`[+] BREACH payload queued against ${node.name} [${node.id}]. Committing ${cu} CU.`, 'var(--color-player)');
       } catch (e) {
           this.print(`ERR: Failed to queue BREACH. ${e.message}`, 'var(--color-enemy)');
       }
       return;
    }

    if (cmd === '/defend') {
       if (!args[0]) {
           this.print('ERR: Missing target. Usage: /defend [node_name or id]', 'var(--color-enemy)');
           return;
       }
       if (this.gameEngine.currentEpoch && this.gameEngine.currentEpoch.phase !== 'PLANNING') {
           this.print('ERR: ACTIONS ONLY PERMITTED IN PLANNING PHASE', 'var(--color-enemy)');
           return;
       }
       const node = this.resolveNode(args.join(' '));
       if (!node) {
           this.print(`ERR: Node '${args.join(' ')}' not found.`, 'var(--color-warning)');
           return;
       }
       const cu = 25;
       try {
           const res = await api.submitAction(node.id, 'DEFEND', cu);
           this.print(`[+] DEFEND protocol queued for ${node.name} [${node.id}]. Committing ${cu} CU.`, 'var(--color-player)');
       } catch (e) {
           this.print(`ERR: Failed to queue DEFEND. ${e.message}`, 'var(--color-enemy)');
       }
       return;
    }

    this.print(`ERR: Unknown command '${cmd}'. Type /help.`, 'var(--color-enemy)');
  }
}
