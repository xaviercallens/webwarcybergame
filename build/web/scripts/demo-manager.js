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
  
  start(scenarioId = 'tutorial') {
    console.log(`[SYS] Starting Interactive Scenario: ${scenarioId}`);
    this.isActive = true;
    this.step = 0;
    this.currentScenario = scenarioId;
    
    // Force reset game to ensure a clean slate
    this.game.init();
    
    this.tutorialPanel.style.display = 'block';
    
    // Disable AI so the user doesn't get overwhelmed instantly during tutorials
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
    
    if (this.currentScenario === 'tutorial') {
        switch(this.step) {
          case 1:
            this.titleEl.innerText = '[ TUTORIAL : NAV ]';
            this.textEl.innerHTML = 'Welcome to Neo-Hack.<br/><br/>Use your <b>Mouse Scroll Wheel</b> to zoom in/out, and <b>Left-Click + Drag</b> to rotate the globe.<br/>Press NEXT when ready.';
            this.nextBtn.style.display = 'inline-block';
            this.nextBtn.innerText = 'NEXT >>';
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
    else if (this.currentScenario === 'bank_run') {
        this.nextBtn.style.display = 'inline-block';
        if (this.step === 1) {
            this.titleEl.innerText = '[ SCENARIO : BERYLIA BANK RUN ]';
            this.textEl.innerHTML = 'Your objective is to siphon CU from the Iron Grid financial core without triggering a massive kinetic escalation.<br/><br/>Click NEXT to review the plan.';
            this.nextBtn.innerText = 'NEXT >>';
        } else if (this.step === 2) {
            this.titleEl.innerText = '[ STEP 1 : SECURE FLANKS ]';
            this.textEl.innerHTML = 'Open the Diplomacy Modal from the Node UI or Terminal. Secure a Non-Aggression pact with the <b>Silk Road Coalition</b> before proceeding.';
        } else if (this.step === 3) {
            this.titleEl.innerText = '[ STEP 2 : STEALTH CONFIG ]';
            this.textEl.innerHTML = 'Hardware detection risk is high. Open the <b>SENTINEL LAB</b> (top right). Set your agent policy to <b>0.8 Stealth</b> and <b>0.2 Aggression</b>.';
        } else if (this.step === 4) {
            this.titleEl.innerText = '[ STEP 3 : TARGET ACQUISITION ]';
            this.textEl.innerHTML = 'Hold <b>[E]</b> to highlight enemy nodes. Use the Terminal <b>/scan</b> command to find poorly defended nodes.';
        } else if (this.step === 5) {
            this.titleEl.innerText = '[ STEP 4 : EXECUTE ]';
            this.textEl.innerHTML = 'Queue a Breach via Terminal <b>/breach</b> and wait for the Transition Phase. Good luck, Director.';
            this.nextBtn.innerText = 'END INSTRUCTIONS';
            this.game.disableAI = false; 
        } else {
            this.stop();
        }
    }
    else if (this.currentScenario === 'heist') {
        this.nextBtn.style.display = 'inline-block';
        if (this.step === 1) {
            this.titleEl.innerText = '[ SCENARIO : SILK ROAD HEIST ]';
            this.textEl.innerHTML = 'The Silk Road is poisoning our AI data grids. The Shadow Cartels are masking their movements with ransomware.<br/>We must retaliate.';
            this.nextBtn.innerText = 'NEXT >>';
        } else if (this.step === 2) {
            this.titleEl.innerText = '[ STEP 1 : BULWARK ]';
            this.textEl.innerHTML = 'Open Diplomacy. Draft an Accord with the <b>Sentinel Vanguard</b> (Ethical Hackers) to drastically boost your defensive firewalls.';
        } else if (this.step === 3) {
            this.titleEl.innerText = '[ STEP 2 : PROXY WAR ]';
            this.textEl.innerHTML = 'A direct attack is too risky. Contact the <b>Cyber Mercenaries</b> and lease their botnets for a +20% undocumented combat buff.';
        } else if (this.step === 4) {
            this.titleEl.innerText = '[ STEP 3 : COUNTER-BREACH ]';
            this.textEl.innerHTML = 'Click multiple Silk Road targets or use the Terminal to queue your strikes. The server will resolve all combat concurrently.';
            this.nextBtn.innerText = 'END INSTRUCTIONS';
            this.game.disableAI = false; 
        } else {
            this.stop();
        }
    }
    else if (this.currentScenario === 'blackout') {
        this.nextBtn.style.display = 'inline-block';
        if (this.step === 1) {
            this.titleEl.innerText = '[ SCENARIO : OPR BLACKOUT ]';
            this.textEl.innerHTML = '<b>TARGET RICH ENVIRONMENT</b><br/><br/>Every faction has declared war on you. You have massive Compute Output, but limited time.';
            this.nextBtn.innerText = 'NEXT >>';
        } else if (this.step === 2) {
            this.titleEl.innerText = '[ STEP 1 : THE SWARM ]';
            this.textEl.innerHTML = 'Use the Terminal to type <b>/status</b> and review your global penetration. You must capture 5 nodes in a single Epoch to survive.';
        } else if (this.step === 3) {
            this.titleEl.innerText = '[ STEP 2 : DEPLOYMENT ]';
            this.textEl.innerHTML = 'Hold <b>[A]</b> to highlight all valid Breach Vectors. You can queue multiple attacks across the globe simultaneously.';
            this.nextBtn.innerText = 'END INSTRUCTIONS';
            this.game.disableAI = false; 
        } else {
            this.stop();
        }
    }
  }

  checkEvent(type, e) {
    if (!this.isActive) return;
    
    // Auto-advancement rules only apply to the base tutorial scenario
    if (this.currentScenario !== 'tutorial') return;
    
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
