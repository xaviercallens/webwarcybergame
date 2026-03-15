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
}

// Export singleton instance
export const api = new ApiClient();
