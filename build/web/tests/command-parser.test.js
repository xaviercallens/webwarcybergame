/**
 * Unit tests for CLI Command Parser
 */
import { describe, it, expect } from 'vitest';
import { parseCommand, resolveNodeTarget, getCommandsForRole, getHelpText, COMMAND_DEFS, ALIAS_MAP } from '../scripts/cli/command-parser.js';

const MOCK_NODES = [
  { id: 1, name: 'web-server-01' },
  { id: 2, name: 'db-primary' },
  { id: 3, name: 'mail-gateway' },
  { id: 10, name: 'firewall-edge' },
];

describe('parseCommand', () => {
  it('should parse a simple command with target', () => {
    const result = parseCommand('scan web-server-01', { role: 'attacker', nodes: MOCK_NODES });
    expect(result.ok).toBe(true);
    expect(result.command).toBe('scan');
    expect(result.action).toBe('SCAN_NETWORK');
    expect(result.target).toBe(1);
    expect(result.meta).toBe(false);
  });

  it('should parse command with leading slash', () => {
    const result = parseCommand('/scan web-server-01', { role: 'attacker', nodes: MOCK_NODES });
    expect(result.ok).toBe(true);
    expect(result.command).toBe('scan');
  });

  it('should resolve alias', () => {
    const result = parseCommand('s web-server-01', { role: 'attacker', nodes: MOCK_NODES });
    expect(result.ok).toBe(true);
    expect(result.command).toBe('scan');
    expect(result.action).toBe('SCAN_NETWORK');
  });

  it('should parse numeric target', () => {
    const result = parseCommand('exploit 2', { role: 'attacker', nodes: MOCK_NODES });
    expect(result.ok).toBe(true);
    expect(result.target).toBe(2);
  });

  it('should use selectedNodeId when no target given', () => {
    const result = parseCommand('exploit', { role: 'attacker', selectedNodeId: 3, nodes: MOCK_NODES });
    expect(result.ok).toBe(true);
    expect(result.target).toBe(3);
  });

  it('should error when target required but not provided', () => {
    const result = parseCommand('exploit', { role: 'attacker', nodes: MOCK_NODES });
    expect(result.ok).toBe(false);
    expect(result.error).toContain('requires a target');
  });

  it('should error on unknown command', () => {
    const result = parseCommand('hacktheplanet', { role: 'attacker' });
    expect(result.ok).toBe(false);
    expect(result.error).toContain('Unknown command');
  });

  it('should error on empty input', () => {
    const result = parseCommand('', {});
    expect(result.ok).toBe(false);
    expect(result.error).toBe('Empty command');
  });

  it('should reject attacker commands for defender', () => {
    const result = parseCommand('exploit 1', { role: 'defender', nodes: MOCK_NODES });
    expect(result.ok).toBe(false);
    expect(result.error).toContain('attacker command');
  });

  it('should reject defender commands for attacker', () => {
    const result = parseCommand('patch 1', { role: 'attacker', nodes: MOCK_NODES });
    expect(result.ok).toBe(false);
    expect(result.error).toContain('defender command');
  });

  it('should parse meta commands', () => {
    const result = parseCommand('help', {});
    expect(result.ok).toBe(true);
    expect(result.meta).toBe(true);
    expect(result.command).toBe('help');
  });

  it('should parse endturn aliases', () => {
    expect(parseCommand('endturn', {}).command).toBe('endturn');
    expect(parseCommand('et', {}).command).toBe('endturn');
    expect(parseCommand('end', {}).command).toBe('endturn');
  });

  it('should parse flags', () => {
    const result = parseCommand('exploit web-server-01 --vuln=CVE-2024-1234', { role: 'attacker', nodes: MOCK_NODES });
    expect(result.ok).toBe(true);
    expect(result.flags.vuln).toBe('CVE-2024-1234');
  });

  it('should parse boolean flags', () => {
    const result = parseCommand('scan web-server-01 --verbose', { role: 'attacker', nodes: MOCK_NODES });
    expect(result.ok).toBe(true);
    expect(result.flags.verbose).toBe(true);
  });

  it('should parse commands without required target (clearlogs)', () => {
    const result = parseCommand('clearlogs', { role: 'attacker' });
    expect(result.ok).toBe(true);
    expect(result.target).toBeNull();
  });

  it('should error when node not found', () => {
    const result = parseCommand('scan nonexistent-host', { role: 'attacker', nodes: MOCK_NODES });
    expect(result.ok).toBe(false);
    expect(result.error).toContain('not found');
  });

  it('should handle partial node name match', () => {
    const result = parseCommand('scan firewall', { role: 'attacker', nodes: MOCK_NODES });
    expect(result.ok).toBe(true);
    expect(result.target).toBe(10);
  });

  it('should parse all defender commands', () => {
    const defCmds = ['monitor', 'scanmal 1', 'patch 1', 'isolate 1', 'restore 1', 'firewall 1', 'respond 1'];
    for (const cmd of defCmds) {
      const result = parseCommand(cmd, { role: 'defender', nodes: MOCK_NODES });
      expect(result.ok).toBe(true);
    }
  });
});

describe('resolveNodeTarget', () => {
  it('should resolve numeric id', () => {
    expect(resolveNodeTarget('2', MOCK_NODES)).toBe(2);
  });

  it('should resolve exact name (case-insensitive)', () => {
    expect(resolveNodeTarget('DB-PRIMARY', MOCK_NODES)).toBe(2);
  });

  it('should resolve partial name', () => {
    expect(resolveNodeTarget('mail', MOCK_NODES)).toBe(3);
  });

  it('should return null for unresolvable', () => {
    expect(resolveNodeTarget('zzzzz', MOCK_NODES)).toBeNull();
  });

  it('should return null for null input', () => {
    expect(resolveNodeTarget(null, MOCK_NODES)).toBeNull();
  });
});

describe('getCommandsForRole', () => {
  it('should return attacker commands + meta', () => {
    const cmds = getCommandsForRole('attacker');
    const names = cmds.map(c => c.name);
    expect(names).toContain('scan');
    expect(names).toContain('exploit');
    expect(names).toContain('help');
    expect(names).toContain('endturn');
    expect(names).not.toContain('patch');
    expect(names).not.toContain('isolate');
  });

  it('should return defender commands + meta', () => {
    const cmds = getCommandsForRole('defender');
    const names = cmds.map(c => c.name);
    expect(names).toContain('patch');
    expect(names).toContain('isolate');
    expect(names).toContain('help');
    expect(names).not.toContain('scan');
    expect(names).not.toContain('exploit');
  });
});

describe('getHelpText', () => {
  it('should produce non-empty help for attacker', () => {
    const text = getHelpText('attacker');
    expect(text).toContain('AVAILABLE COMMANDS');
    expect(text).toContain('scan');
    expect(text).toContain('exploit');
  });

  it('should produce non-empty help for defender', () => {
    const text = getHelpText('defender');
    expect(text).toContain('AVAILABLE COMMANDS');
    expect(text).toContain('patch');
  });
});

describe('ALIAS_MAP', () => {
  it('should map all aliases correctly', () => {
    expect(ALIAS_MAP['s']).toBe('scan');
    expect(ALIAS_MAP['e']).toBe('exploit');
    expect(ALIAS_MAP['p']).toBe('patch');
    expect(ALIAS_MAP['et']).toBe('endturn');
    expect(ALIAS_MAP['h']).toBe('help');
    expect(ALIAS_MAP['?']).toBe('help');
  });
});

describe('COMMAND_DEFS', () => {
  it('should have 15 game actions + 4 meta', () => {
    const gameActions = Object.values(COMMAND_DEFS).filter(d => d.action);
    const metaActions = Object.values(COMMAND_DEFS).filter(d => d.meta);
    expect(gameActions.length).toBe(15);
    expect(metaActions.length).toBe(4);
  });
});
