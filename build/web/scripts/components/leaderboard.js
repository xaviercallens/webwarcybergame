/**
 * Neo-Hack: Gridlock v4.1 — Leaderboard Hub Component
 * Interactive leaderboard with search, tab switching, and real-time updates
 */

export class LeaderboardHub {
  constructor() {
    this.currentTab = 'rankings';
    this.searchQuery = '';
    this._bindEvents();
  }

  _bindEvents() {
    const searchInput = document.getElementById('lb-search');
    const tabRankings = document.getElementById('tab-rankings');
    const tabHof = document.getElementById('tab-hof');
    const refreshBtn = document.getElementById('btn-lb-refresh');

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.searchQuery = e.target.value.toUpperCase();
        this._filterTable();
      });
    }

    if (tabRankings) {
      tabRankings.addEventListener('click', () => this._switchTab('rankings'));
    }
    if (tabHof) {
      tabHof.addEventListener('click', () => this._switchTab('hof'));
    }
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => this._refresh());
    }
  }

  _switchTab(tab) {
    this.currentTab = tab;
    document.querySelectorAll('.leaderboard-hub__tab').forEach(t => t.classList.remove('active'));
    if (tab === 'rankings') {
      document.getElementById('tab-rankings')?.classList.add('active');
    } else {
      document.getElementById('tab-hof')?.classList.add('active');
    }
  }

  _filterTable() {
    const tbody = document.getElementById('lb-tbody');
    if (!tbody) return;
    const rows = tbody.querySelectorAll('tr');
    rows.forEach(row => {
      const text = row.textContent.toUpperCase();
      row.style.display = text.includes(this.searchQuery) ? '' : 'none';
    });
  }

  _refresh() {
    const btn = document.getElementById('btn-lb-refresh');
    if (btn) {
      btn.textContent = '↻ REFRESHING...';
      btn.disabled = true;
      setTimeout(() => {
        btn.textContent = '↻ REFRESH DATA';
        btn.disabled = false;
      }, 1500);
    }
  }
}
