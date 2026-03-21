/**
 * Unit tests for FogOfWar
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { FogOfWar } from '../scripts/fog-of-war.js';
import { events, Events } from '../scripts/game-events.js';

const MOCK_NODES = [
  { id: 1, name: 'gateway' },
  { id: 2, name: 'db-server' },
  { id: 3, name: 'web-app' },
  { id: 4, name: 'backup-srv' },
];

const MOCK_CONNECTIONS = [
  { source: 1, target: 2 },
  { source: 2, target: 3 },
  { source: 3, target: 4 },
];

describe('FogOfWar', () => {
  let fog;

  beforeEach(() => {
    events.clear();
    fog = new FogOfWar();
  });

  describe('attacker view', () => {
    beforeEach(() => {
      events.emit(Events.GAME_START, { role: 'attacker' });
      events.emit(Events.GAME_STATE, {
        role: 'attacker',
        nodes: MOCK_NODES,
        discoveredNodes: [1, 2],
        compromisedNodes: [1],
        detectedNodes: [],
      });
    });

    it('should mark discovered nodes as visible', () => {
      const visible = fog.getVisibleNodes();
      const node1 = visible.find(n => n.id === 1);
      const node2 = visible.find(n => n.id === 2);
      expect(node1.visible).toBe(true);
      expect(node2.visible).toBe(true);
    });

    it('should mark undiscovered nodes as dimmed/hidden', () => {
      const visible = fog.getVisibleNodes();
      const node3 = visible.find(n => n.id === 3);
      const node4 = visible.find(n => n.id === 4);
      expect(node3.visible).toBe(false);
      expect(node3.dimmed).toBe(true);
      expect(node3.statusOverlay).toBe('hidden');
      expect(node4.visible).toBe(false);
    });

    it('should mark compromised nodes correctly', () => {
      const visible = fog.getVisibleNodes();
      const node1 = visible.find(n => n.id === 1);
      expect(node1.statusOverlay).toBe('compromised');
    });

    it('should mark discovered (non-compromised) nodes as discovered', () => {
      const visible = fog.getVisibleNodes();
      const node2 = visible.find(n => n.id === 2);
      expect(node2.statusOverlay).toBe('discovered');
    });

    it('should filter connections by visibility', () => {
      const visConn = fog.getVisibleConnections(MOCK_CONNECTIONS);
      // Only connection 1→2 should be visible (both discovered/compromised)
      expect(visConn.length).toBe(1);
      expect(visConn[0].source).toBe(1);
      expect(visConn[0].target).toBe(2);
    });

    it('isNodeVisible should check discovery', () => {
      expect(fog.isNodeVisible(1)).toBe(true);
      expect(fog.isNodeVisible(2)).toBe(true);
      expect(fog.isNodeVisible(3)).toBe(false);
    });
  });

  describe('defender view', () => {
    beforeEach(() => {
      events.emit(Events.GAME_START, { role: 'defender' });
      events.emit(Events.GAME_STATE, {
        role: 'defender',
        nodes: MOCK_NODES,
        discoveredNodes: [],
        compromisedNodes: [2],
        detectedNodes: [2, 3],
      });
    });

    it('should show all nodes as visible', () => {
      const visible = fog.getVisibleNodes();
      visible.forEach(n => {
        expect(n.visible).toBe(true);
        expect(n.dimmed).toBe(false);
      });
    });

    it('should mark compromised + detected nodes', () => {
      const visible = fog.getVisibleNodes();
      const node2 = visible.find(n => n.id === 2);
      expect(node2.statusOverlay).toBe('compromised_detected');
    });

    it('should mark detected-only nodes as suspicious', () => {
      const visible = fog.getVisibleNodes();
      const node3 = visible.find(n => n.id === 3);
      expect(node3.statusOverlay).toBe('suspicious');
    });

    it('should mark clean nodes as secure', () => {
      const visible = fog.getVisibleNodes();
      const node1 = visible.find(n => n.id === 1);
      expect(node1.statusOverlay).toBe('secure');
    });

    it('should return all connections', () => {
      const visConn = fog.getVisibleConnections(MOCK_CONNECTIONS);
      expect(visConn.length).toBe(3);
    });

    it('isNodeVisible always true for defender', () => {
      expect(fog.isNodeVisible(1)).toBe(true);
      expect(fog.isNodeVisible(99)).toBe(true);
    });
  });

  describe('destroy', () => {
    it('should clear internal state', () => {
      events.emit(Events.GAME_START, { role: 'attacker' });
      events.emit(Events.GAME_STATE, {
        role: 'attacker',
        nodes: MOCK_NODES,
        discoveredNodes: [1],
        compromisedNodes: [],
        detectedNodes: [],
      });
      fog.destroy();
      const visible = fog.getVisibleNodes();
      expect(visible.length).toBe(0);
    });
  });
});
