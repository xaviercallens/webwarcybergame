/**
 * MissionPanel component for Neo-Hack v3.1.
 * Displays attacker and defender objectives with completion tracking.
 * Blueprint Alignment: Day 4, Section 2 (User Experience)
 */

export class MissionPanel {
  constructor(container) {
    this.container = container;
    this.el = document.createElement('div');
    this.el.id = 'mission-panel';
    this.el.className = 'mission-panel';
    this.container.appendChild(this.el);
    this._visible = false;
  }

  render(scenario) {
    const attackerGoals = scenario.attackerGoals || [
      { id: 'compromise', text: 'Compromise target nodes', completed: false },
      { id: 'exfiltrate', text: 'Exfiltrate sensitive data', completed: false },
      { id: 'stealth', text: 'Stay below alert threshold', completed: true },
    ];

    const defenderGoals = scenario.defenderGoals || [
      { id: 'detect', text: 'Detect all compromised nodes', completed: false },
      { id: 'contain', text: 'Contain the breach', completed: false },
      { id: 'survive', text: 'Survive until reinforcements', completed: true },
    ];

    this.el.innerHTML = `
      <div class="mission-panel__header">
        <span class="mission-panel__title">MISSION OBJECTIVES</span>
        <button class="mission-panel__toggle" id="btn-mission-toggle">\u2715</button>
      </div>

      <div class="mission-panel__section mission-panel__section--attacker">
        <h4 class="mission-panel__role-header mission-panel__role-header--attacker">
          \u{1F534} ATTACKER
        </h4>
        <ul class="mission-panel__list">
          ${attackerGoals.map(g => this._renderObjective(g)).join('')}
        </ul>
      </div>

      <div class="mission-panel__section mission-panel__section--defender">
        <h4 class="mission-panel__role-header mission-panel__role-header--defender">
          \u{1F535} DEFENDER
        </h4>
        <ul class="mission-panel__list">
          ${defenderGoals.map(g => this._renderObjective(g)).join('')}
        </ul>
      </div>
    `;

    this.el.querySelector('#btn-mission-toggle').addEventListener('click', () => {
      this.toggle();
    });
  }

  _renderObjective(goal) {
    const icon = goal.completed ? '\u2705' : '\u2B1C';
    const cls = goal.completed ? 'mission-panel__objective--done' : '';
    return `<li class="mission-panel__objective ${cls}">${icon} ${goal.text}</li>`;
  }

  toggle() {
    this._visible = !this._visible;
    this.el.style.display = this._visible ? 'block' : 'none';
  }

  show() {
    this._visible = true;
    this.el.style.display = 'block';
  }

  hide() {
    this._visible = false;
    this.el.style.display = 'none';
  }

  destroy() {
    this.el.remove();
  }
}
