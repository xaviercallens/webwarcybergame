/**
 * Unit tests for CLI AutoComplete
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { AutoComplete } from '../scripts/cli/autocomplete.js';

const MOCK_NODES = [
  { id: 1, name: 'web-server-01' },
  { id: 2, name: 'web-server-02' },
  { id: 3, name: 'db-primary' },
  { id: 4, name: 'mail-gateway' },
];

describe('AutoComplete', () => {
  let ac;

  beforeEach(() => {
    ac = new AutoComplete();
    ac.setNodes(MOCK_NODES);
    ac.setRole('attacker');
  });

  describe('command completion', () => {
    it('should complete partial command', () => {
      const result = ac.complete('sc');
      expect(result.completions).toContain('scan');
      expect(result.replacement).toBe('scan ');
    });

    it('should return all commands on empty input', () => {
      const result = ac.complete('');
      expect(result.completions.length).toBeGreaterThan(5);
      expect(result.isAmbiguous).toBe(true);
    });

    it('should return exact match for unique prefix', () => {
      const result = ac.complete('exp');
      expect(result.completions).toEqual(['exploit']);
      expect(result.replacement).toBe('exploit ');
      expect(result.isAmbiguous).toBe(false);
    });

    it('should handle ambiguous command prefix', () => {
      // 'e' matches exploit, elevate, exfiltrate, endturn
      const result = ac.complete('e');
      expect(result.completions.length).toBeGreaterThan(1);
      expect(result.isAmbiguous).toBe(true);
    });

    it('should return empty for no-match prefix', () => {
      const result = ac.complete('zzz');
      expect(result.completions).toEqual([]);
      expect(result.replacement).toBeNull();
    });

    it('should filter by role (defender cannot see scan)', () => {
      ac.setRole('defender');
      const result = ac.complete('sca');
      expect(result.completions).toContain('scanmal');
      expect(result.completions).not.toContain('scan');
    });
  });

  describe('target completion', () => {
    it('should complete node names after command', () => {
      const result = ac.complete('scan web');
      expect(result.completions).toContain('web-server-01');
      expect(result.completions).toContain('web-server-02');
    });

    it('should complete unique node name', () => {
      const result = ac.complete('scan db');
      expect(result.completions).toEqual(['db-primary']);
    });

    it('should handle no matching nodes', () => {
      const result = ac.complete('scan zzz');
      expect(result.completions).toEqual([]);
    });

    it('should complete partial match', () => {
      const result = ac.complete('scan mail');
      expect(result.completions).toContain('mail-gateway');
    });
  });

  describe('command history', () => {
    it('should push and navigate history', () => {
      ac.pushHistory('scan web-server-01');
      ac.pushHistory('exploit db-primary');
      ac.pushHistory('status');

      expect(ac.navigateHistory(-1)).toBe('status');
      expect(ac.navigateHistory(-1)).toBe('exploit db-primary');
      expect(ac.navigateHistory(-1)).toBe('scan web-server-01');
      // At oldest, stay there
      expect(ac.navigateHistory(-1)).toBe('scan web-server-01');
    });

    it('should navigate forward in history', () => {
      ac.pushHistory('cmd1');
      ac.pushHistory('cmd2');
      ac.pushHistory('cmd3');

      ac.navigateHistory(-1); // cmd3
      ac.navigateHistory(-1); // cmd2
      expect(ac.navigateHistory(1)).toBe('cmd3');
      // Past newest returns empty string
      expect(ac.navigateHistory(1)).toBe('');
    });

    it('should not push duplicates', () => {
      ac.pushHistory('scan host');
      ac.pushHistory('scan host');
      expect(ac.navigateHistory(-1)).toBe('scan host');
      // Going back further should return null (no more history)
      expect(ac.navigateHistory(-1)).toBe('scan host');
    });

    it('should return null on empty history', () => {
      expect(ac.navigateHistory(-1)).toBeNull();
      expect(ac.navigateHistory(1)).toBeNull();
    });

    it('should respect max history size', () => {
      for (let i = 0; i < 60; i++) {
        ac.pushHistory(`cmd-${i}`);
      }
      // Navigate all the way back
      let oldest = null;
      for (let i = 0; i < 60; i++) {
        const val = ac.navigateHistory(-1);
        if (val !== null) oldest = val;
      }
      // Should have kept only 50
      expect(oldest).toBe('cmd-10');
    });

    it('resetHistoryIndex should reset navigation position', () => {
      ac.pushHistory('a');
      ac.pushHistory('b');
      ac.navigateHistory(-1); // b
      ac.resetHistoryIndex();
      expect(ac.navigateHistory(-1)).toBe('b');
    });
  });
});
