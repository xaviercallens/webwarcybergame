/**
 * Neo-Hack: Gridlock v3.2 — Mission Briefing Overlay
 * Full-screen themed overlay showing scenario narrative, role, and objectives.
 */

import { events, Events } from '../game-events.js';

const SCENARIOS = {
  default: {
    title: 'OPERATION: FIREWALL',
    narrative: 'A critical banking infrastructure is under threat. Intelligence reports indicate a sophisticated APT group has infiltrated the perimeter network. Your mission parameters have been set.',
    attackerBrief: 'Compromise the core database server and exfiltrate customer financial records before the defender can detect and contain the breach.',
    defenderBrief: 'Detect the intrusion, identify compromised hosts, and contain the breach before sensitive data is exfiltrated.',
  },
  bank_run: {
    title: 'THE BERYLIA BANK RUN',
    narrative: 'Berylia National Bank\'s SWIFT infrastructure has been targeted by state-sponsored hackers. Millions are at stake. The clock is ticking.',
    attackerBrief: 'Infiltrate the SWIFT terminal network, install persistent backdoors, and initiate fraudulent transfers totaling $50M.',
    defenderBrief: 'Monitor the SWIFT network for anomalies, patch known vulnerabilities, and prevent unauthorized fund transfers.',
  },
  heist: {
    title: 'SILICON SILK ROAD HEIST',
    narrative: 'A dark web marketplace has amassed a cryptocurrency fortune. Both sides want control of the wallet infrastructure.',
    attackerBrief: 'Locate and compromise the cold wallet servers. Extract the private keys before network isolation kicks in.',
    defenderBrief: 'Protect the cold wallet infrastructure. Detect lateral movement and isolate compromised segments.',
  },
  blackout: {
    title: 'OPERATION BLACKOUT',
    narrative: 'Critical power grid SCADA systems are being targeted. A successful attack could plunge millions into darkness.',
    attackerBrief: 'Gain access to SCADA control systems and trigger a cascading grid failure across three sectors.',
    defenderBrief: 'Defend the SCADA network. Detect intrusions early and prevent any unauthorized commands to grid controllers.',
  },
};

export class Briefing {
  constructor() {
    this.el = document.createElement('div');
    this.el.id = 'briefing-overlay';
    this.el.className = 'briefing-overlay';
    this.el.style.display = 'none';
    document.body.appendChild(this.el);

    this._onContinue = null;
    this._skipPref = localStorage.getItem('nh_skip_briefing') === 'true';
  }

  /**
   * Show the briefing overlay.
   * @param {object} opts - { scenario, role, difficulty, objectives }
   * @returns {Promise} Resolves when user clicks Continue
   */
  show({ scenario = 'default', role, difficulty, objectives }) {
    if (this._skipPref) {
      return Promise.resolve();
    }

    const data = SCENARIOS[scenario] || SCENARIOS.default;
    const brief = role === 'attacker' ? data.attackerBrief : data.defenderBrief;
    const roleLabel = role === 'attacker' ? '🔴 ATTACKER' : '🔵 DEFENDER';
    const diffLabel = (difficulty || 'normal').toUpperCase();

    const objList = objectives || [];

    this.el.innerHTML = `
      <div class="briefing-overlay__content">
        <div class="briefing-overlay__header">
          <div class="briefing-overlay__classification">// CLASSIFIED — EYES ONLY //</div>
          <h1 class="briefing-overlay__title">${data.title}</h1>
        </div>

        <div class="briefing-overlay__body">
          <div class="briefing-overlay__narrative">
            <p>${data.narrative}</p>
          </div>

          <div class="briefing-overlay__assignment">
            <div class="briefing-overlay__role">
              <span class="briefing-overlay__label">ROLE ASSIGNMENT:</span>
              <span class="briefing-overlay__value ${role}">${roleLabel}</span>
            </div>
            <div class="briefing-overlay__difficulty">
              <span class="briefing-overlay__label">THREAT LEVEL:</span>
              <span class="briefing-overlay__value">${diffLabel}</span>
            </div>
          </div>

          <div class="briefing-overlay__mission">
            <h3>MISSION BRIEFING</h3>
            <p>${brief}</p>
          </div>

          ${objList.length > 0 ? `
          <div class="briefing-overlay__objectives">
            <h3>PRIMARY OBJECTIVES</h3>
            <ul>
              ${objList.map(o => `<li>▸ ${o.text || o}</li>`).join('')}
            </ul>
          </div>
          ` : ''}
        </div>

        <div class="briefing-overlay__footer">
          <label class="briefing-overlay__skip">
            <input type="checkbox" id="briefing-skip-check" ${this._skipPref ? 'checked' : ''}>
            <span>Don't show again</span>
          </label>
          <button class="btn btn-primary briefing-overlay__continue" id="btn-briefing-continue">
            COMMENCE OPERATION ▶
          </button>
        </div>
      </div>
    `;

    this.el.style.display = 'flex';

    return new Promise((resolve) => {
      const btn = this.el.querySelector('#btn-briefing-continue');
      const skipCheck = this.el.querySelector('#briefing-skip-check');

      const handleContinue = () => {
        if (skipCheck && skipCheck.checked) {
          localStorage.setItem('nh_skip_briefing', 'true');
          this._skipPref = true;
        }
        this.hide();
        resolve();
      };

      btn.addEventListener('click', handleContinue);

      // Also allow Enter, Space, or gamepad A
      const keyHandler = (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          document.removeEventListener('keydown', keyHandler);
          handleContinue();
        }
      };
      document.addEventListener('keydown', keyHandler);
    });
  }

  hide() {
    this.el.style.display = 'none';
  }

  destroy() {
    this.el.remove();
  }
}
