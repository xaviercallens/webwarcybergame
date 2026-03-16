/**
 * Neo-Hack: Gridlock — Network API Client
 * Handles communication with the FastAPI backend
 */

export class ApiClient {
  constructor() {
    if (window.location.hostname === 'frontend') {
        this.baseUrl = 'http://backend:8000/api';
    } else {
        this.baseUrl = window.location.hostname === 'localhost' 
            ? 'http://localhost:8000/api' 
            : '/api'; // production
    }
        
    this.token = localStorage.getItem('nh_token') || null;
  }

  getHeaders() {
    const headers = {
      'Content-Type': 'application/json'
    };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async health() {
    try {
      const res = await fetch(`${this.baseUrl}/health`);
      return await res.json();
    } catch(e) {
      console.error('[API] Health check failed:', e);
      return { status: 'offline' };
    }
  }

  async login(username, password) {
    try {
      const res = await fetch(`${this.baseUrl}/auth/login`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ username, password })
      });
      
      if (!res.ok) throw new Error('Login failed');
      const data = await res.json();
      
      this.token = data.access_token;
      localStorage.setItem('nh_token', this.token);
      return data;
      
    } catch(e) {
      console.error('[API] Login Error:', e);
      throw e;
    }
  }

  async register(username, password) {
    try {
      const res = await fetch(`${this.baseUrl}/auth/register`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ username, password })
      });
      
      if (!res.ok) throw new Error('Registration failed');
      const data = await res.json();
      
      this.token = data.access_token;
      localStorage.setItem('nh_token', this.token);
      return data;
      
    } catch(e) {
      console.error('[API] Register Error:', e);
      throw e;
    }
  }

  async getProfile() {
    try {
      const res = await fetch(`${this.baseUrl}/players/me`, {
        headers: this.getHeaders()
      });
      if (!res.ok) return null;
      return await res.json();
    } catch(e) {
      return null;
    }
  }

  async getLeaderboard(limit = 10) {
    try {
      const res = await fetch(`${this.baseUrl}/leaderboard?limit=${limit}`);
      if (!res.ok) throw new Error('Failed to fetch leaderboard');
      return await res.json();
    } catch(e) {
      console.error('[API] Leaderboard Error:', e);
      return [];
    }
  }

  async postGameOverStats(stats) {
    // stats = { won: boolean, time_seconds: int, nodes_captured: int, nodes_lost: int, attacks: int }
    try {
      const res = await fetch(`${this.baseUrl}/players/me/game-over`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(stats)
      });
      if (!res.ok) throw new Error('Failed to post game stats');
      return await res.json();
    } catch(e) {
      console.error('[API] Game Over Stats Error:', e);
      return null;
    }
  }
  async getWorldState() {
    try {
      const res = await fetch(`${this.baseUrl}/world/state`, {
        headers: this.getHeaders()
      });
      if (!res.ok) throw new Error('Failed to fetch world state');
      const data = await res.json();
      return data.nodes || Object.values(data) || [];
    } catch(e) {
      console.error('[API] World State Error:', e);
      return [];
    }
  }

  async getCurrentEpoch() {
    try {
      const res = await fetch(`${this.baseUrl}/epoch/current`, {
        headers: this.getHeaders()
      });
      if (!res.ok) throw new Error('Failed to fetch current epoch');
      return await res.json();
    } catch(e) {
      console.error('[API] Current Epoch Error:', e);
      return null;
    }
  }

  async submitAction(targetId, actionType, cuCommitted) {
    try {
      const res = await fetch(`${this.baseUrl}/epoch/action`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({
           target_node_id: targetId,
           action_type: actionType,
           cu_committed: cuCommitted
        })
      });
      if (!res.ok) {
         const errorData = await res.json();
         throw new Error(errorData.detail || 'Action failed');
      }
      return await res.json();
    } catch(e) {
      console.error('[API] Action Submit Error:', e);
      throw e;
    }
  }

  async getFactionInfo(factionId) {
    try {
      const res = await fetch(`${this.baseUrl}/faction/${factionId}`, {
        headers: this.getHeaders()
      });
      if (!res.ok) throw new Error('Failed to fetch faction info');
      return await res.json();
    } catch(e) {
      console.error('[API] Faction Info Error:', e);
      return null;
    }
  }

  // --- SPRINT 3: DIPLOMACY & NEWS API ---
  
  async sendDiplomacyChat(factionId, message) {
    try {
      const res = await fetch(`${this.baseUrl}/diplomacy/chat`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({
          faction_id: parseInt(factionId),
          message: message
        })
      });
      if (!res.ok) throw new Error('Failed to send diplomacy chat');
      return await res.json();
    } catch(e) {
      console.error('[API] Diplomacy Chat Error:', e);
      return { reply: "[CONNECTION FAILED: AMBASSADOR UNAVAILABLE]" };
    }
  }

  async proposeTreaty(targetFactionId, type, proposalText) {
    try {
      const res = await fetch(`${this.baseUrl}/diplomacy/propose`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({
          target_faction_id: parseInt(targetFactionId),
          type: type, // CEASEFIRE, ALLIANCE, TRADE
          proposal_text: proposalText
        })
      });
      if (!res.ok) throw new Error('Failed to propose treaty');
      return await res.json();
    } catch(e) {
      console.error('[API] Treaty Propose Error:', e);
      return { status: 'error', message: "Transmission failed." };
    }
  }

  async getAccords() {
    try {
      const res = await fetch(`${this.baseUrl}/diplomacy/accords`, {
        headers: this.getHeaders()
      });
      if (!res.ok) throw new Error('Failed to fetch accords');
      return await res.json();
    } catch(e) {
      console.error('[API] Fetch Accords Error:', e);
      return [];
    }
  }

  async getLatestNews(limit = 5) {
    try {
      const res = await fetch(`${this.baseUrl}/news/latest?limit=${limit}`, {
        headers: this.getHeaders()
      });
      if (!res.ok) throw new Error('Failed to fetch latest news');
      return await res.json();
    } catch(e) {
      console.error('[API] Fetch News Error:', e);
      return [];
    }
  }

  // --- SPRINT 4: SENTINEL API ---

  async getSentinels() {
    try {
      const res = await fetch(`${this.baseUrl}/sentinels`, { headers: this.getHeaders() });
      if (!res.ok) throw new Error('Failed to fetch sentinels');
      return await res.json();
    } catch(e) {
      console.error('[API] Get Sentinels Error:', e);
      return { sentinels: [] };
    }
  }

  async createSentinel(name) {
    try {
      const res = await fetch(`${this.baseUrl}/sentinels/create`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ name })
      });
      if (!res.ok) {
         const d = await res.json();
         throw new Error(d.detail || 'Failed to create sentinel');
      }
      return await res.json();
    } catch(e) {
      console.error('[API] Create Sentinel Error:', e);
      throw e;
    }
  }

  async updateSentinelPolicy(id, weights) {
    try {
      const res = await fetch(`${this.baseUrl}/sentinels/${id}/policy`, {
        method: 'PATCH',
        headers: this.getHeaders(),
        body: JSON.stringify(weights)
      });
      if (!res.ok) throw new Error('Policy update failed');
      return await res.json();
    } catch(e) {
      console.error('[API] Update Sentinel Policy Error:', e);
      throw e;
    }
  }

  async toggleSentinel(id) {
    try {
      const res = await fetch(`${this.baseUrl}/sentinels/${id}/toggle`, {
        method: 'POST',
        headers: this.getHeaders()
      });
      if (!res.ok) throw new Error('Toggle failed');
      return await res.json();
    } catch(e) {
      console.error('[API] Toggle Sentinel Error:', e);
      throw e;
    }
  }

  async getSentinelLogs(id) {
    try {
      const res = await fetch(`${this.baseUrl}/sentinels/${id}/logs`, { headers: this.getHeaders() });
      if (!res.ok) throw new Error('Logs fetch failed');
      return await res.json();
    } catch(e) {
      console.error('[API] Get Logs Error:', e);
      return { logs: [] };
    }
  }

  // --- SPRINT 5: WEBSOCKETS & NOTIFICATIONS ---

  connectWebSocket() {
    if (this.ws) {
        this.ws.close();
    }
    const token = localStorage.getItem('token');
    if (!token) return;

    // Convert http:// to ws://
    const wsUrl = this.baseUrl.replace(/^http/, 'ws').replace('/api', '') + `/ws/game?token=${token}`;
    
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
        console.log('[WS] Connected to Game State Stream');
    };

    this.ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            // Dispatch a global event that ui-manager can listen to
            const wsEvent = new CustomEvent('wsMessage', { detail: data });
            window.dispatchEvent(wsEvent);
        } catch (e) {
            console.error('[WS] Error parsing message:', e);
        }
    };

    this.ws.onclose = () => {
        console.log('[WS] Disconnected. Reconnecting in 3s...');
        setTimeout(() => this.connectWebSocket(), 3000);
    };

    this.ws.onerror = (err) => {
        console.error('[WS] Connection Error', err);
    };
  }

  async getNotifications() {
      try {
          const res = await fetch(`${this.baseUrl}/notifications`, { headers: this.getHeaders() });
          if (!res.ok) throw new Error('Fetch notifications failed');
          return await res.json();
      } catch(e) {
          console.error('[API] Get Notifications error:', e);
          return { notifications: [] };
      }
  }

  async markNotificationsRead() {
      try {
          await fetch(`${this.baseUrl}/notifications/read`, { method: 'POST', headers: this.getHeaders() });
      } catch(e) {
          console.error('[API] Mark Notifications Read error:', e);
      }
  }

}

// Export singleton instance
export const api = new ApiClient();
