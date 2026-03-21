/**
 * Neo-Hack: Gridlock v3.2 — Scenario Registry
 * Central registry for all playable scenarios.
 */

import { SCENARIO_CRIMSON_TIDE } from './crimson-tide.js';

export const SCENARIOS = {
  crimson_tide: SCENARIO_CRIMSON_TIDE,
};

/**
 * Get a scenario by ID. Returns null if not found.
 * @param {string} id
 */
export function getScenario(id) {
  return SCENARIOS[id] || null;
}

/**
 * List all available scenarios as { id, name, description }.
 */
export function listScenarios() {
  return Object.values(SCENARIOS).map(s => ({
    id: s.id,
    name: s.name,
    description: s.description,
    difficulty: s.difficulty,
    maxTurns: s.maxTurns,
  }));
}
