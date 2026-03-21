/**
 * Neo-Hack: Gridlock v3.2 — CLI Command Parser
 * Parses text commands mirroring all 15 GUI actions. Returns structured results.
 */

const COMMAND_DEFS = {
  // Attacker actions
  scan:        { action: 'SCAN_NETWORK',         requiresTarget: true,  aliases: ['s'],  role: 'attacker', description: 'Scan a host for vulnerabilities' },
  exploit:     { action: 'EXPLOIT_VULNERABILITY', requiresTarget: true,  aliases: ['e'],  role: 'attacker', description: 'Exploit a found vulnerability', flags: ['--vuln'] },
  phish:       { action: 'PHISHING',              requiresTarget: true,  aliases: ['ph'], role: 'attacker', description: 'Social engineering attack' },
  malware:     { action: 'INSTALL_MALWARE',       requiresTarget: true,  aliases: ['mw'], role: 'attacker', description: 'Install persistent malware' },
  elevate:     { action: 'ELEVATE_PRIVILEGES',    requiresTarget: true,  aliases: ['el'], role: 'attacker', description: 'Escalate to admin access' },
  move:        { action: 'LATERAL_MOVEMENT',      requiresTarget: true,  aliases: ['mv'], role: 'attacker', description: 'Move to adjacent segment' },
  exfiltrate:  { action: 'EXFILTRATE_DATA',       requiresTarget: true,  aliases: ['ex'], role: 'attacker', description: 'Steal data from compromised host' },
  clearlogs:   { action: 'CLEAR_LOGS',            requiresTarget: false, aliases: ['cl'], role: 'attacker', description: 'Remove evidence from logs' },

  // Defender actions
  monitor:     { action: 'MONITOR_LOGS',          requiresTarget: false, aliases: ['mon'],  role: 'defender', description: 'Check system logs for suspicious activity' },
  scanmal:     { action: 'SCAN_FOR_MALWARE',      requiresTarget: true,  aliases: ['sm'],   role: 'defender', description: 'Scan host for malware infections' },
  patch:       { action: 'APPLY_PATCH',           requiresTarget: true,  aliases: ['p'],    role: 'defender', description: 'Apply security patch to fix vulnerability' },
  isolate:     { action: 'ISOLATE_HOST',          requiresTarget: true,  aliases: ['iso'],  role: 'defender', description: 'Quarantine a host from network' },
  restore:     { action: 'RESTORE_BACKUP',        requiresTarget: true,  aliases: ['rb'],   role: 'defender', description: 'Restore system from clean backup' },
  firewall:    { action: 'FIREWALL_RULE',         requiresTarget: true,  aliases: ['fw'],   role: 'defender', description: 'Add firewall rule to block connections' },
  respond:     { action: 'INCIDENT_RESPONSE',     requiresTarget: true,  aliases: ['ir'],   role: 'defender', description: 'Active countermeasure against attack' },

  // Meta commands
  status:      { meta: true, description: 'Show network status summary' },
  endturn:     { meta: true, aliases: ['et', 'end'], description: 'End your turn' },
  help:        { meta: true, aliases: ['h', '?'], description: 'Show command help' },
  nodes:       { meta: true, aliases: ['ls', 'list'], description: 'List nodes by faction (my | enemies | all)' },
  clear:       { meta: true, description: 'Clear terminal output' },
};

// Build alias lookup
const ALIAS_MAP = {};
for (const [name, def] of Object.entries(COMMAND_DEFS)) {
  ALIAS_MAP[name] = name;
  if (def.aliases) {
    for (const alias of def.aliases) {
      ALIAS_MAP[alias] = name;
    }
  }
}

/**
 * Parse a raw command string into a structured result.
 * @param {string} input - Raw user input
 * @param {object} context - { role, selectedNodeId, nodes }
 * @returns {{ ok: boolean, command?: string, action?: string, target?: string|number, flags?: object, meta?: boolean, error?: string }}
 */
export function parseCommand(input, context = {}) {
  const trimmed = input.trim();
  if (!trimmed) return { ok: false, error: 'Empty command' };

  // Tokenize
  const tokens = trimmed.split(/\s+/);
  let cmdToken = tokens[0].toLowerCase().replace(/^\//, ''); // allow /scan or scan
  const rest = tokens.slice(1);

  // Resolve alias
  const cmdName = ALIAS_MAP[cmdToken];
  if (!cmdName) {
    return { ok: false, error: `Unknown command '${cmdToken}'. Type 'help' for available commands.` };
  }

  const def = COMMAND_DEFS[cmdName];

  // Meta commands
  if (def.meta) {
    return { ok: true, command: cmdName, meta: true, args: rest };
  }

  // Role check
  if (def.role && context.role && def.role !== context.role) {
    return { ok: false, error: `'${cmdName}' is a ${def.role} command. You are playing as ${context.role}.` };
  }

  // Parse flags (--key=value)
  const flags = {};
  const positional = [];
  for (const token of rest) {
    if (token.startsWith('--')) {
      const eqIdx = token.indexOf('=');
      if (eqIdx !== -1) {
        flags[token.substring(2, eqIdx)] = token.substring(eqIdx + 1);
      } else {
        flags[token.substring(2)] = true;
      }
    } else {
      positional.push(token);
    }
  }

  // Resolve target
  let target = null;
  if (def.requiresTarget) {
    if (positional.length > 0) {
      target = positional.join(' ');
    } else if (context.selectedNodeId != null) {
      target = context.selectedNodeId;
    } else {
      return { ok: false, error: `'${cmdName}' requires a target. Usage: ${cmdName} <target>` };
    }
  }

  // Resolve target to node ID if it's a name
  if (target != null && context.nodes) {
    const resolved = resolveNodeTarget(target, context.nodes);
    if (resolved === null) {
      return { ok: false, error: `Node '${target}' not found.` };
    }
    target = resolved;
  }

  return {
    ok: true,
    command: cmdName,
    action: def.action,
    target,
    flags,
    meta: false,
  };
}

/**
 * Resolve a target string to a node ID.
 * Accepts numeric IDs or case-insensitive name matching.
 */
export function resolveNodeTarget(target, nodes) {
  if (target == null) return null;

  // Numeric ID
  const numId = parseInt(target, 10);
  if (!isNaN(numId) && nodes.some(n => n.id === numId)) {
    return numId;
  }

  // Name match (case-insensitive)
  const lower = String(target).toLowerCase();
  const match = nodes.find(n => n.name && n.name.toLowerCase() === lower);
  if (match) return match.id;

  // Partial match
  const partial = nodes.find(n => n.name && n.name.toLowerCase().includes(lower));
  if (partial) return partial.id;

  return null;
}

/**
 * Get all command names available for a given role.
 */
export function getCommandsForRole(role) {
  const result = [];
  for (const [name, def] of Object.entries(COMMAND_DEFS)) {
    if (def.meta || !def.role || def.role === role) {
      result.push({ name, ...def });
    }
  }
  return result;
}

/**
 * Generate help text.
 */
export function getHelpText(role) {
  const lines = ['AVAILABLE COMMANDS:', ''];
  const cmds = getCommandsForRole(role);

  for (const cmd of cmds) {
    const aliases = cmd.aliases ? ` (${cmd.aliases.join(', ')})` : '';
    const target = cmd.requiresTarget ? ' <target>' : '';
    const flagStr = cmd.flags ? ` [${cmd.flags.join(' ')}]` : '';
    lines.push(`  ${cmd.name}${target}${flagStr}${aliases}`);
    lines.push(`    ${cmd.description}`);
  }

  return lines.join('\n');
}

export { COMMAND_DEFS, ALIAS_MAP };
