import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { api } from '../scripts/api-client.js';

describe('ApiClient', () => {
  beforeEach(() => {
    // Reset fetch mock and local storage before each test
    global.fetch = vi.fn();
    Storage.prototype.getItem = vi.fn(() => null);
    Storage.prototype.setItem = vi.fn();
    // Reset api base URL logic since node env might be different
    api.baseUrl = 'http://localhost:8000/api';
    api.token = null;
    vi.stubGlobal('location', { hostname: 'localhost' });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it('should initialize with correct default values (localhost)', async () => {
    vi.resetModules();
    vi.stubGlobal('location', { hostname: 'localhost' });
    const { api: localApi } = await import('../scripts/api-client.js');
    expect(localApi.baseUrl).toBe('http://localhost:8000/api');
  });

  it('should initialize with correct default values (frontend module)', async () => {
    vi.resetModules();
    vi.stubGlobal('location', { hostname: 'frontend' });
    const { api: frontendApi } = await import('../scripts/api-client.js');
    expect(frontendApi.baseUrl).toBe('http://backend:8000/api');
  });
  
  it('should initialize with correct default values (prod)', async () => {
    vi.resetModules();
    vi.stubGlobal('location', { hostname: 'production.com' });
    const { api: prodApi } = await import('../scripts/api-client.js');
    expect(prodApi.baseUrl).toBe('/api');
  });

  it('health() should return data on success', async () => {
    const mockReponse = { status: 'healthy' };
    global.fetch.mockResolvedValueOnce({
      json: async () => mockReponse
    });
    const result = await api.health();
    expect(result).toEqual(mockReponse);
  });

  it('health() should return offline on error', async () => {
    global.fetch.mockRejectedValueOnce(new Error('Network error'));
    const result = await api.health();
    expect(result).toEqual({ status: 'offline' });
  });

  it('login() should store token and return data on success', async () => {
    const mockResponse = { access_token: 'fake-token' };
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    });
    const result = await api.login('user1', 'pass1');
    expect(result).toEqual(mockResponse);
    expect(api.token).toBe('fake-token');
    expect(localStorage.setItem).toHaveBeenCalledWith('nh_token', 'fake-token');
  });

  it('login() should throw error on failure', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false });
    await expect(api.login('user1', 'badpass')).rejects.toThrow('Login failed');
  });

  it('register() should store token and return data on success', async () => {
    const mockResponse = { access_token: 'fake-token' };
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    });
    const result = await api.register('user1', 'pass1');
    expect(result).toEqual(mockResponse);
    expect(api.token).toBe('fake-token');
    expect(localStorage.setItem).toHaveBeenCalledWith('nh_token', 'fake-token');
  });

  it('register() should throw error on failure', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false });
    await expect(api.register('user1', 'badpass')).rejects.toThrow('Registration failed');
  });

  it('getProfile() should return profile on success', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ player: '1' }) });
    expect(await api.getProfile()).toEqual({ player: '1' });
  });

  it('getProfile() should return null on failure', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false });
    expect(await api.getProfile()).toBeNull();
    global.fetch.mockRejectedValueOnce(new Error('error'));
    expect(await api.getProfile()).toBeNull();
  });

  it('getLeaderboard() should return array on success', async () => {
    const mockResponse = [{ username: 'player1', score: 100 }];
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => mockResponse });
    const result = await api.getLeaderboard(5);
    expect(result).toEqual(mockResponse);
  });

  it('getLeaderboard() should return empty array on failure', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false });
    expect(await api.getLeaderboard()).toEqual([]);
  });

  it('getHeaders() should include Authorization if token exists', () => {
    api.token = 'test-token';
    const headers = api.getHeaders();
    expect(headers['Authorization']).toBe('Bearer test-token');
  });
  
  it('postGameOverStats() works', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ res: 'success' }) });
    expect(await api.postGameOverStats({ won: true })).toEqual({ res: 'success' });
  });

  it('postGameOverStats() failure fallback', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false });
    expect(await api.postGameOverStats({})).toBeNull();
  });

  it('getWorldState() works with generic data', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ some: 'data' }) });
    expect(await api.getWorldState()).toEqual(['data']);
  });

  it('getWorldState() works with nodes array', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ nodes: ['item'] }) });
    expect(await api.getWorldState()).toEqual(['item']);
  });

  it('getWorldState() failure fallback', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false });
    expect(await api.getWorldState()).toEqual([]);
  });

  it('getCurrentEpoch() works', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ epoch: 1 }) });
    expect(await api.getCurrentEpoch()).toEqual({ epoch: 1 });
  });

  it('getCurrentEpoch() failure', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false });
    expect(await api.getCurrentEpoch()).toBeNull();
  });

  it('submitAction() works', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ success: true }) });
    expect(await api.submitAction('a1', 'attack', 10)).toEqual({ success: true });
  });

  it('submitAction() throws with detailed detail message', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false, json: async () => ({ detail: 'Custom error' }) });
    await expect(api.submitAction('a1', 'attack', 10)).rejects.toThrow('Custom error');
  });

  it('getFactionInfo() works', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1 }) });
    expect(await api.getFactionInfo(1)).toEqual({ id: 1 });
  });

  it('getFactionInfo() failure', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false });
    expect(await api.getFactionInfo(1)).toBeNull();
  });

  it('sendDiplomacyChat() works', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ reply: 'yes' }) });
    expect(await api.sendDiplomacyChat(1, 'hi')).toEqual({ reply: 'yes' });
  });

  it('sendDiplomacyChat() failure', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false });
    expect(await api.sendDiplomacyChat(1, 'hi')).toEqual({ reply: "[CONNECTION FAILED: AMBASSADOR UNAVAILABLE]" });
  });

  it('proposeTreaty() works', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'accepted' }) });
    expect(await api.proposeTreaty(1, 'ALLIANCE', 'join us')).toEqual({ status: 'accepted' });
  });

  it('proposeTreaty() failure', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false });
    expect(await api.proposeTreaty(1, 'ALLIANCE', 'join us')).toEqual({ status: 'error', message: "Transmission failed." });
  });

  it('getAccords() works', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ([]) });
    expect(await api.getAccords()).toEqual([]);
  });

  it('getAccords() failure', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false });
    expect(await api.getAccords()).toEqual([]);
  });

  it('getLatestNews() works', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ([]) });
    expect(await api.getLatestNews()).toEqual([]);
  });

  it('getLatestNews() failure', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false });
    expect(await api.getLatestNews()).toEqual([]);
  });

  // Sentinels

  it('getSentinels() works', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ sentinels: [] }) });
    expect(await api.getSentinels()).toEqual({ sentinels: [] });
  });

  it('getSentinels() failure', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false });
    expect(await api.getSentinels()).toEqual({ sentinels: [] });
  });

  it('createSentinel() works', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1 }) });
    expect(await api.createSentinel('bot')).toEqual({ id: 1 });
  });

  it('createSentinel() failure', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false, json: async () => ({ detail: 'Custom detail' }) });
    await expect(api.createSentinel('bot')).rejects.toThrow('Custom detail');
  });

  it('updateSentinelPolicy() works', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ id: 1 }) });
    expect(await api.updateSentinelPolicy(1, {})).toEqual({ id: 1 });
  });

  it('updateSentinelPolicy() failure', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false });
    await expect(api.updateSentinelPolicy(1, {})).rejects.toThrow('Policy update failed');
  });

  it('toggleSentinel() works', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'on' }) });
    expect(await api.toggleSentinel(1)).toEqual({ status: 'on' });
  });

  it('toggleSentinel() failure', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false });
    await expect(api.toggleSentinel(1)).rejects.toThrow('Toggle failed');
  });

  it('getSentinelLogs() works', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ logs: [] }) });
    expect(await api.getSentinelLogs(1)).toEqual({ logs: [] });
  });

  it('getSentinelLogs() failure', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false });
    expect(await api.getSentinelLogs(1)).toEqual({ logs: [] });
  });

  // Notifications
  
  it('getNotifications() works', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({ notifications: [] }) });
    expect(await api.getNotifications()).toEqual({ notifications: [] });
  });

  it('getNotifications() failure', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false });
    expect(await api.getNotifications()).toEqual({ notifications: [] });
  });

  it('markNotificationsRead() works without throws', async () => {
    global.fetch.mockResolvedValueOnce({ ok: true });
    await expect(api.markNotificationsRead()).resolves.toBeUndefined();
  });

  it('markNotificationsRead() catches exceptions', async () => {
    global.fetch.mockRejectedValueOnce(new Error('fail'));
    await expect(api.markNotificationsRead()).resolves.toBeUndefined();
  });

  // Websockets

  it('connectWebSocket() creates a WS connection', () => {
    Storage.prototype.getItem = vi.fn(() => 'test-token');
    
    // Polyfill WebSocket
    class MockWebSocket {
        constructor(url) {
            this.url = url;
            this.onopen = null;
            this.onmessage = null;
            this.onclose = null;
            this.onerror = null;
            this.close = vi.fn();
            setTimeout(() => {
                if(this.onopen) this.onopen();
            }, 0);
        }
    }
    const realWS = global.WebSocket;
    global.WebSocket = MockWebSocket;

    // First connect
    api.connectWebSocket();
    expect(api.ws).toBeDefined();
    expect(api.ws.url).toContain('ws://');
    expect(api.ws.url).toContain('test-token');

    // Make sure closing and errors don't crash the loop
    if(api.ws.onmessage) api.ws.onmessage({ data: '{"hello": 1}' });
    if(api.ws.onerror) api.ws.onerror(new Error('ws error'));
    
    // Second connect closes first
    api.connectWebSocket();
    
    global.WebSocket = realWS;
  });

  it('connectWebSocket() no-op if no token', () => {
    api.ws = null;
    api.connectWebSocket(); // uses getItem mocked to null by default
    expect(api.ws).toBeNull();
  });

  it('connectWebSocket() retries on close', () => {
      vi.useFakeTimers();
      Storage.prototype.getItem = vi.fn(() => 'test-token');
      class MockWebSocket { close(){} }
      global.WebSocket = MockWebSocket;

      api.connectWebSocket();
      expect(api.ws.onclose).toBeDefined();
      
      const connectSpy = vi.spyOn(api, 'connectWebSocket');
      api.ws.onclose();
      
      vi.runAllTimers();
      expect(connectSpy).toHaveBeenCalled();
      
      vi.useRealTimers();
  });

});
