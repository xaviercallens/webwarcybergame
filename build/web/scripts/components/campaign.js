/**
 * Neo-Hack: Gridlock v4.1 — Campaign Component
 * Mission progression, launch, and reward tracking
 */

export class Campaign {
  constructor() {
    this.missions = [
      { id: 1, title: 'CORE SYSTEMS TUTORIAL', status: 'completed', rank: 'A', xp: 1500 },
      { id: 2, title: 'THE BERYLIA BANK RUN', status: 'active', xp: 4500 },
      { id: 3, title: 'SILICON SILK ROAD HEIST', status: 'locked', reqLevel: 5, xp: 6000 },
      { id: 4, title: 'OPERATION BLACKOUT', status: 'locked', reqLevel: 8, xp: 8500 },
      { id: 5, title: 'OPERATION CRIMSON TIDE', status: 'locked', reqLevel: 12, xp: 12000 },
    ];
    this.currentMission = 2;
    this._bindEvents();
  }

  _bindEvents() {
    // Campaign card click interactions
    document.querySelectorAll('.campaign__card').forEach((card, idx) => {
      card.addEventListener('click', () => {
        this._selectMission(idx + 1);
      });
    });
  }

  _selectMission(missionId) {
    const mission = this.missions.find(m => m.id === missionId);
    if (!mission || mission.status === 'locked') return;

    this.currentMission = missionId;
    document.querySelectorAll('.campaign__card').forEach((card, idx) => {
      card.style.outline = (idx + 1 === missionId) ? '2px solid var(--color-accent)' : 'none';
    });

    window.dispatchEvent(new CustomEvent('missionSelected', { detail: mission }));
  }

  launchMission() {
    const mission = this.missions.find(m => m.id === this.currentMission);
    if (!mission || mission.status === 'locked') return null;

    window.dispatchEvent(new CustomEvent('missionLaunched', { detail: mission }));
    return mission;
  }

  completeMission(missionId, rank) {
    const mission = this.missions.find(m => m.id === missionId);
    if (!mission) return;

    mission.status = 'completed';
    mission.rank = rank;

    // Unlock next mission
    const next = this.missions.find(m => m.id === missionId + 1);
    if (next) {
      next.status = 'active';
    }

    this._updateCards();
  }

  _updateCards() {
    const container = document.getElementById('campaign-cards');
    if (!container) return;

    container.querySelectorAll('.campaign__card').forEach((card, idx) => {
      const mission = this.missions[idx];
      if (!mission) return;

      card.className = `campaign__card ${mission.status}`;
      const statusEl = card.querySelector('.campaign__card-status');
      if (statusEl) {
        statusEl.className = `campaign__card-status ${mission.status}`;
        statusEl.textContent = mission.status === 'completed' ? 'COMPLETED' :
                               mission.status === 'active' ? 'ACTIVE' :
                               '🔒 LOCKED';
      }
    });
  }
}
