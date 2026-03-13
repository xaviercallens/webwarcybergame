import { audio } from './audio-manager.js';

export class DemoManager {
  constructor(gameEngine) {
    this.game = gameEngine;
    this.step = 0;
    this.isActive = false;
    this.tutorialPanel = document.getElementById('tutorial-panel');
    this.titleEl = document.getElementById('tut-title');
    this.textEl = document.getElementById('tut-text');
    this.nextBtn = document.getElementById('btn-tut-next');
    
    if (this.nextBtn) {
        this.nextBtn.addEventListener('click', () => {
            if (this.step === 6) {
                this.stop();
            } else {
                this.nextStep();
            }
        });
    }
    
    // Bind game events to auto-advance tutorial if needed
    window.addEventListener('nodeSelected', (e) => this.checkEvent('select', e));
    window.addEventListener('attackLaunched', (e) => this.checkEvent('attack', e));
    window.addEventListener('toast', (e) => this.checkEvent('toast', e));
  }
  
  start() {
    console.log('[SYS] Starting Interactive Demo Sequence');
    this.isActive = true;
    this.step = 0;
    
    // Force reset game to ensure a clean slate
    this.game.init();
    
    this.tutorialPanel.style.display = 'block';
    
    // Disable AI so the user doesn't get overwhelmed instantly during the tutorial
    this.game.disableAI = true; 
    
    this.nextStep();
  }
  
  stop() {
    this.isActive = false;
    if (this.tutorialPanel) this.tutorialPanel.style.display = 'none';
    this.game.disableAI = false;
  }
  
  nextStep() {
    this.step++;
    audio.playSelect();
    
    if (!this.titleEl || !this.textEl) return;
    
    switch(this.step) {
      case 1:
        this.titleEl.innerText = '[ TUTORIAL : NAV ]';
        this.textEl.innerHTML = 'Welcome to Neo-Hack.<br/><br/>Use your <b>Mouse Scroll Wheel</b> to zoom in/out, and <b>Left-Click + Drag</b> to rotate the globe.<br/>Press NEXT when ready.';
        this.nextBtn.style.display = 'inline-block';
        break;
      case 2:
        this.titleEl.innerText = '[ TUTORIAL : FACTIONS ]';
        this.textEl.innerHTML = 'Review the Network.<br/><br/><span style="color:var(--color-player)">GREEN</span> nodes belong to you.<br/><span style="color:var(--color-enemy)">RED</span> nodes are hostile targets.<br/><span style="color:var(--color-neutral)">CYAN</span> nodes are neutral buffers.';
        break;
      case 3:
        this.titleEl.innerText = '[ TUTORIAL : SELECT ]';
        this.textEl.innerHTML = '<b>TARGET ACQUISITION</b><br/><br/>Click on your <span style="color:var(--color-player)">GREEN</span> node to access its root terminal.';
        this.nextBtn.style.display = 'none'; // Must actually click it to advance
        break;
      case 4:
        this.titleEl.innerText = '[ TUTORIAL : COMBAT ]';
        this.textEl.innerHTML = '<b>INITIATE HACK</b><br/><br/>Click on an adjacent <span style="color:var(--color-enemy)">RED</span> or <span style="color:var(--color-neutral)">CYAN</span> node to launch an attack payload across the network.';
        this.nextBtn.style.display = 'none'; // Must attack
        break;
      case 5:
        this.titleEl.innerText = '[ TUTORIAL : FIREWALL ]';
        this.textEl.innerHTML = '<b>BYPASS IN PROGRESS</b><br/><br/>Watch the attack arc! The target firewall is draining. When it hits 0, you capture the node.';
        this.nextBtn.style.display = 'none'; // Wait for capture toast
        break;
      case 6:
        this.titleEl.innerText = '[ TUTORIAL : DOMINANCE ]';
        this.textEl.innerHTML = '<b>EXCELLENT WORK</b><br/><br/>Capture 75% of the globe to achieve Total Dominance. Be careful, the AI will now counter-attack!';
        this.nextBtn.innerText = 'END TUTORIAL';
        this.nextBtn.style.display = 'inline-block';
        this.game.disableAI = false; // Re-enable AI
        break;
      default:
        this.stop();
        break;
    }
  }

  checkEvent(type, e) {
    if (!this.isActive) return;
    
    if (type === 'select' && this.step === 3) {
      if (e.detail.node && e.detail.node.owner === 'PLAYER') {
        this.nextStep();
      }
    }
    
    if (type === 'attack' && this.step === 4) {
      this.nextStep();
    }
    
    if (type === 'toast' && this.step === 5) {
      if (e.detail.type === 'capture') {
        this.nextStep();
      }
    }
  }
}
