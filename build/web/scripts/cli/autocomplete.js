/**
 * Neo-Hack: Gridlock v3.2 — CLI Tab Completion & Command History
 * Provides tab-completion for commands, node names, and flag values.
 */

import { COMMAND_DEFS, ALIAS_MAP } from './command-parser.js';

export class AutoComplete {
  constructor() {
    this._history = [];
    this._historyIndex = -1;
    this._maxHistory = 50;
    this._nodes = [];
    this._role = null;
  }

  /** Update known nodes for target completion. */
  setNodes(nodes) {
    this._nodes = nodes || [];
  }

  /** Set current player role to filter commands. */
  setRole(role) {
    this._role = role;
  }

  /** Set the current player faction ID to precisely filter nodes. */
  setPlayerFaction(factionId) {
    this._playerFactionId = factionId;
  }

  /**
   * Get tab-completion results for current input.
   * @param {string} input - Current input string
   * @returns {{ completions: string[], replacement: string|null, isAmbiguous: boolean }}
   */
  complete(input) {
    const trimmed = input.trimStart();
    const spaceIdx = trimmed.indexOf(' ');

    if (spaceIdx === -1) {
      return this._completeCommand(trimmed);
    }

    const cmdToken = trimmed.substring(0, spaceIdx).toLowerCase().replace(/^\//, '');
    const partial = trimmed.substring(spaceIdx + 1).trimStart();
    
    const cmdName = ALIAS_MAP[cmdToken] || cmdToken;
    const def = COMMAND_DEFS[cmdName] || { name: cmdName };
    if (!def.name && COMMAND_DEFS[cmdName]) def.name = cmdName;
    
    return this._completeTarget(partial, trimmed, def);
  }

  _completeCommand(partial) {
    const lower = partial.toLowerCase().replace(/^\//, '');
    if (!lower) {
      // List all available commands
      const all = this._getAvailableCommands();
      return { completions: all, replacement: null, isAmbiguous: true };
    }

    const matches = this._getAvailableCommands().filter(c => c.startsWith(lower));

    if (matches.length === 0) {
      return { completions: [], replacement: null, isAmbiguous: false };
    }
    if (matches.length === 1) {
      return { completions: matches, replacement: '/' + matches[0] + ' ', isAmbiguous: false };
    }

    // Find common prefix
    const prefix = this._commonPrefix(matches);
    return {
      completions: matches,
      replacement: prefix.length > lower.length ? '/' + prefix : null,
      isAmbiguous: true,
    };
  }

  _completeTarget(partial, fullInput, cmdDef) {
    const lower = partial.toLowerCase();
    
    let candidates = this._nodes;
    if (cmdDef && cmdDef.action && this._playerFactionId) {
       if (['BREACH', 'EXPLOIT_VULNERABILITY', 'PHISHING', 'INSTALL_MALWARE', 'ELEVATE_PRIVILEGES', 'LATERAL_MOVEMENT', 'EXFILTRATE_DATA', 'SCAN_NETWORK'].includes(cmdDef.action)) {
           candidates = candidates.filter(n => n.faction_id !== this._playerFactionId);
       } else if (['DEFEND', 'APPLY_PATCH', 'RESTORE_BACKUP', 'ISOLATE_HOST', 'FIREWALL_RULE', 'INCIDENT_RESPONSE'].includes(cmdDef.action)) {
           candidates = candidates.filter(n => n.faction_id === this._playerFactionId);
       }
    }

    const nodeNames = candidates.filter(n => n.name).map(n => n.name);
    
    if (cmdDef && (cmdDef.name === 'nodes' || (cmdDef.aliases && cmdDef.aliases.includes('ls')))) {
       nodeNames.push('my', 'enemies', 'all');
    }

    const matches = nodeNames.filter(name => name.toLowerCase().startsWith(lower));

    if (matches.length === 0) {
      // Try partial match
      const fuzzy = nodeNames.filter(name => name.toLowerCase().includes(lower));
      return { completions: fuzzy.slice(0, 10), replacement: null, isAmbiguous: fuzzy.length > 1 };
    }

    if (matches.length === 1) {
      const prefix = fullInput.substring(0, fullInput.length - partial.length);
      return { completions: matches, replacement: prefix + matches[0], isAmbiguous: false };
    }

    const prefixMatch = this._commonPrefix(matches.map(m => m.toLowerCase()));
    let replacement = null;
    
    if (prefixMatch.length > lower.length) {
       const actualPrefix = matches[0].substring(0, prefixMatch.length);
       const base = fullInput.substring(0, fullInput.length - partial.length);
       replacement = base + actualPrefix;
    }

    return {
      completions: matches.slice(0, 10),
      replacement: replacement,
      isAmbiguous: true,
    };
  }

  _getAvailableCommands() {
    const cmds = [];
    for (const [name, def] of Object.entries(COMMAND_DEFS)) {
      if (def.meta || !def.role || def.role === this._role) {
        cmds.push(name);
      }
    }
    return cmds.sort();
  }

  _commonPrefix(strings) {
    if (strings.length === 0) return '';
    let prefix = strings[0];
    for (let i = 1; i < strings.length; i++) {
      while (!strings[i].startsWith(prefix)) {
        prefix = prefix.slice(0, -1);
        if (!prefix) return '';
      }
    }
    return prefix;
  }

  // --- Command History ---

  pushHistory(command) {
    if (!command || command === this._history[this._history.length - 1]) return;
    this._history.push(command);
    if (this._history.length > this._maxHistory) {
      this._history.shift();
    }
    this._historyIndex = -1;
  }

  /**
   * Navigate history. direction: -1 (older), +1 (newer)
   * @returns {string|null}
   */
  navigateHistory(direction) {
    if (this._history.length === 0) return null;

    if (direction === -1) {
      // Go older
      if (this._historyIndex === -1) {
        this._historyIndex = this._history.length - 1;
      } else if (this._historyIndex > 0) {
        this._historyIndex--;
      }
    } else {
      // Go newer
      if (this._historyIndex === -1) return null;
      this._historyIndex++;
      if (this._historyIndex >= this._history.length) {
        this._historyIndex = -1;
        return '';
      }
    }

    return this._history[this._historyIndex] ?? null;
  }

  resetHistoryIndex() {
    this._historyIndex = -1;
  }
}
