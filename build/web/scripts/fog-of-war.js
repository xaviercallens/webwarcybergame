/**
 * Neo-Hack: Gridlock v3.2 — Fog of War Manager
 * Filters visible nodes based on player role and discovery state.
 * Attacker: only sees discovered nodes. Defender: sees all but only detected compromises.
 */

import { events, Events } from './game-events.js';

export class FogOfWar {
  constructor() {
    this._role = null;
    this._discoveredNodes = new Set();
    this._detectedNodes = new Set();
    this._compromisedNodes = new Set();
    this._allNodes = [];

    events.on(Events.GAME_STATE, (state) => this._onStateUpdate(state));
    events.on(Events.GAME_START, ({ role }) => { this._role = role; });
  }

  _onStateUpdate(state) {
    this._role = state.role || this._role;
    this._allNodes = state.nodes || [];
    this._discoveredNodes = new Set(state.discoveredNodes || []);
    this._detectedNodes = new Set(state.detectedNodes || []);
    this._compromisedNodes = new Set(state.compromisedNodes || []);
  }

  /**
   * Returns the filtered/annotated list of nodes the current player should see.
   * Each node gets additional properties: visible, dimmed, statusOverlay.
   */
  getVisibleNodes() {
    return this._allNodes.map(node => {
      const nodeId = node.id;

      if (this._role === 'attacker') {
        return this._getAttackerView(node, nodeId);
      } else {
        return this._getDefenderView(node, nodeId);
      }
    });
  }

  _getAttackerView(node, nodeId) {
    const discovered = this._discoveredNodes.has(nodeId);
    const compromised = this._compromisedNodes.has(nodeId);

    return {
      ...node,
      visible: discovered || compromised,
      dimmed: !discovered && !compromised,
      statusOverlay: compromised ? 'compromised' : (discovered ? 'discovered' : 'hidden'),
    };
  }

  _getDefenderView(node, nodeId) {
    const detected = this._detectedNodes.has(nodeId);
    const compromised = this._compromisedNodes.has(nodeId);

    let statusOverlay = 'secure';
    if (compromised && detected) {
      statusOverlay = 'compromised_detected';
    } else if (compromised && !detected) {
      statusOverlay = 'compromised_hidden'; // defender can't see this yet
    } else if (detected) {
      statusOverlay = 'suspicious';
    }

    return {
      ...node,
      visible: true,
      dimmed: false,
      statusOverlay,
    };
  }

  /**
   * Returns connections filtered by visibility.
   */
  getVisibleConnections(connections) {
    if (this._role === 'defender') return connections;

    const visibleIds = new Set();
    this._discoveredNodes.forEach(id => visibleIds.add(id));
    this._compromisedNodes.forEach(id => visibleIds.add(id));

    return connections.filter(c =>
      visibleIds.has(c.source) && visibleIds.has(c.target)
    );
  }

  /**
   * Check if a specific node is visible to the current player.
   */
  isNodeVisible(nodeId) {
    if (this._role === 'defender') return true;
    return this._discoveredNodes.has(nodeId) || this._compromisedNodes.has(nodeId);
  }

  destroy() {
    this._allNodes = [];
    this._discoveredNodes.clear();
    this._detectedNodes.clear();
    this._compromisedNodes.clear();
  }
}
