/**
 * Neo-Hack: Gridlock v5.0 — Subscription Management Component
 * Handles pricing display, checkout flow, and subscription management.
 */
export class SubscriptionManager {
  constructor() {
    this.plans = [];
    this.currentTier = 'FREE';
  }

  async init() {
    await this.loadPlans();
    await this.loadStatus();
    this.bindEvents();
  }

  async loadPlans() {
    try {
      const res = await fetch('/api/subscription/plans');
      const data = await res.json();
      this.plans = data.plans || [];
      this.renderPlans();
    } catch (e) {
      console.error('[SUB] Failed to load plans:', e);
    }
  }

  async loadStatus() {
    const token = localStorage.getItem('token');
    if (!token) return;
    try {
      const res = await fetch('/api/subscription/status', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      this.currentTier = data.tier || 'FREE';
      this.updateCurrentBadge(data.tier_name, data.subscription);
    } catch (e) {
      console.error('[SUB] Failed to load status:', e);
    }
  }

  renderPlans() {
    const container = document.getElementById('sub-plans-grid');
    if (!container) return;

    const tierIcons = { FREE: '◈', CYBER_PASS: '⚡', DEV_API: '⟁', ENTERPRISE: '🏢' };
    const tierColors = { FREE: 'var(--color-text-muted)', CYBER_PASS: 'var(--color-accent)', DEV_API: 'var(--color-amber)', ENTERPRISE: 'var(--color-stable)' };

    container.innerHTML = this.plans.map(p => `
      <div class="sub-card ${p.tier === this.currentTier ? 'sub-card--active' : ''}" data-tier="${p.tier}" style="border-top-color:${tierColors[p.tier] || 'var(--color-accent)'}">
        <div class="sub-card__icon" style="color:${tierColors[p.tier]}">${tierIcons[p.tier] || '◈'}</div>
        <div class="sub-card__tier">${p.tier}</div>
        <div class="sub-card__name">${p.name}</div>
        <div class="sub-card__price">${p.price}<span class="sub-card__interval">/${p.interval}</span></div>
        <ul class="sub-card__features">${(p.features || []).map(f => `<li>▸ ${f}</li>`).join('')}</ul>
        ${p.tier === this.currentTier
          ? '<button class="sub-card__btn sub-card__btn--current" disabled>CURRENT_PLAN ✓</button>'
          : p.tier === 'FREE'
            ? ''
            : `<button class="sub-card__btn" data-checkout-tier="${p.tier}">UPGRADE →</button>`
        }
      </div>
    `).join('');
  }

  updateCurrentBadge(tierName, subscription) {
    const badge = document.getElementById('sub-current-badge');
    if (badge) {
      badge.innerHTML = `<span style="color:var(--color-accent);">●</span> ${tierName || 'Operative (Free)'}`;
    }
    const statusEl = document.getElementById('sub-status-detail');
    if (statusEl && subscription) {
      const end = subscription.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString() : '—';
      statusEl.innerHTML = `STATUS: <span style="color:var(--color-stable);">${subscription.status}</span> | RENEWS: ${end}`;
    }
  }

  bindEvents() {
    document.querySelectorAll('[data-checkout-tier]').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const tier = e.target.dataset.checkoutTier;
        await this.checkout(tier);
      });
    });

    const cancelBtn = document.getElementById('btn-cancel-sub');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => this.cancelSubscription());
    }

    const portalBtn = document.getElementById('btn-manage-billing');
    if (portalBtn) {
      portalBtn.addEventListener('click', () => this.openPortal());
    }
  }

  async checkout(tier) {
    const token = localStorage.getItem('token');
    if (!token) { alert('Please log in first.'); return; }
    try {
      const res = await fetch('/api/subscription/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ tier })
      });
      const data = await res.json();
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        alert('Checkout error: ' + (data.detail || 'Unknown'));
      }
    } catch (e) {
      console.error('[SUB] Checkout failed:', e);
    }
  }

  async cancelSubscription() {
    if (!confirm('Cancel your subscription? You will retain access until the end of your billing period.')) return;
    const token = localStorage.getItem('token');
    try {
      const res = await fetch('/api/subscription/cancel', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      alert(data.status === 'cancelled' ? 'Subscription cancelled.' : 'Error: ' + (data.detail || 'Unknown'));
      await this.loadStatus();
    } catch (e) {
      console.error('[SUB] Cancel failed:', e);
    }
  }

  async openPortal() {
    const token = localStorage.getItem('token');
    try {
      const res = await fetch('/api/subscription/portal', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.portal_url) {
        window.open(data.portal_url, '_blank');
      }
    } catch (e) {
      console.error('[SUB] Portal failed:', e);
    }
  }
}
