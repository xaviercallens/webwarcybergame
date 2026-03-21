/**
 * Neo-Hack: Gridlock v3.2 — Scenario: Operation Crimson Tide
 * Asymmetric 16-node financial sector network.
 * Attacker has tempo advantage; Defender has scaling and time advantage.
 */

export const SCENARIO_CRIMSON_TIDE = {
  id: 'crimson_tide',
  name: 'Operation Crimson Tide',
  description: 'Eastern European banking cluster under APT-41 assault. Asymmetric factions, no equilibrium.',
  maxTurns: 20,
  difficulty: 'advanced',

  factions: {
    attacker: {
      name: 'Scarlet Protocol',
      subtitle: 'APT-41 / State-Sponsored',
      apPerTurn: 3,
      exploitKits: 5,
      startingStealth: 100,
      startingVisibility: [1, 2], // DMZ-FW, VPN-GW
      winCondition: 'Exfiltrate data from CORE-DB (node 12)',
      scaling: null,
    },
    defender: {
      name: 'Iron Bastion',
      subtitle: 'National CERT',
      apPerTurn: 2,
      irBudget: 8,
      startingAlertLevel: 0,
      startingVisibility: 'all',
      winCondition: 'Survive 20 turns OR isolate attacker completely',
      scaling: {
        alertThreshold: 50,
        scaledAP: 3,
        irUnlockAlert: 80,
      },
    },
  },

  nodes: [
    { id: 1,  name: 'DMZ-FW',      type: 'firewall',  lat: 48.86, lng: 2.35,  tier: 'perimeter',  defenseLevel: 40 },
    { id: 2,  name: 'VPN-GW',      type: 'gateway',   lat: 48.87, lng: 2.38,  tier: 'perimeter',  defenseLevel: 45 },
    { id: 3,  name: 'WEB-01',      type: 'webserver',  lat: 48.84, lng: 2.30,  tier: 'dmz',        defenseLevel: 35 },
    { id: 4,  name: 'WEB-02',      type: 'webserver',  lat: 48.85, lng: 2.32,  tier: 'dmz',        defenseLevel: 35 },
    { id: 5,  name: 'MAIL-SRV',    type: 'mailserver', lat: 48.88, lng: 2.40,  tier: 'dmz',        defenseLevel: 30 },
    { id: 6,  name: 'APP-LB',      type: 'loadbalancer',lat: 48.83, lng: 2.31, tier: 'application', defenseLevel: 50 },
    { id: 7,  name: 'APP-01',      type: 'appserver',  lat: 48.82, lng: 2.28,  tier: 'application', defenseLevel: 45 },
    { id: 8,  name: 'APP-02',      type: 'appserver',  lat: 48.82, lng: 2.34,  tier: 'application', defenseLevel: 45 },
    { id: 9,  name: 'INT-FW',      type: 'firewall',  lat: 48.80, lng: 2.31,  tier: 'internal',    defenseLevel: 60 },
    { id: 10, name: 'LDAP-DC',     type: 'domainctrl', lat: 48.78, lng: 2.28,  tier: 'core',       defenseLevel: 55 },
    { id: 11, name: 'FILE-SRV',    type: 'fileserver', lat: 48.78, lng: 2.34,  tier: 'core',       defenseLevel: 50 },
    { id: 12, name: 'CORE-DB',     type: 'database',   lat: 48.76, lng: 2.31,  tier: 'core',       defenseLevel: 70, isTarget: true },
    { id: 13, name: 'BACKUP-SRV',  type: 'backup',    lat: 48.75, lng: 2.31,  tier: 'core',       defenseLevel: 40 },
    { id: 14, name: 'SIEM-MON',    type: 'monitoring', lat: 48.79, lng: 2.38,  tier: 'security',   defenseLevel: 65 },
    { id: 15, name: 'LOG-AGG',     type: 'logging',   lat: 48.79, lng: 2.42,  tier: 'security',   defenseLevel: 55 },
    { id: 16, name: 'HONEYPOT',    type: 'honeypot',  lat: 48.79, lng: 2.46,  tier: 'security',   defenseLevel: 20, isHoneypot: true },
  ],

  connections: [
    { source: 1, target: 3 },
    { source: 1, target: 4 },
    { source: 2, target: 5 },
    { source: 3, target: 6 },
    { source: 4, target: 6 },
    { source: 5, target: 6 },
    { source: 6, target: 7 },
    { source: 6, target: 8 },
    { source: 7, target: 9 },
    { source: 8, target: 9 },
    { source: 9, target: 10 },
    { source: 9, target: 11 },
    { source: 10, target: 12 },
    { source: 11, target: 12 },
    { source: 12, target: 13 },
    { source: 14, target: 15 },
    { source: 15, target: 16 },
    { source: 9, target: 14 },
  ],

  briefing: {
    attacker: {
      title: 'OPERATION CRIMSON TIDE',
      narrative: [
        'Intelligence confirms a critical financial database in the Eastern European banking cluster.',
        'Your mission: penetrate the 16-node network and exfiltrate transaction records from CORE-DB.',
        'You have 20 turns and 5 exploit kits. The defenders are slow to respond but scale quickly once alerted.',
        'Stay stealthy. Once your stealth drops below 50%, detection probability increases exponentially.',
        'The clock is ticking, operative.',
      ],
      objectives: [
        { id: 'obj_discover', text: 'Discover the path to CORE-DB', type: 'primary' },
        { id: 'obj_compromise', text: 'Compromise CORE-DB (node 12)', type: 'primary' },
        { id: 'obj_exfiltrate', text: 'Exfiltrate data from CORE-DB', type: 'primary' },
        { id: 'obj_stealth', text: 'Complete mission with stealth above 30%', type: 'bonus' },
        { id: 'obj_fast', text: 'Complete before turn 10', type: 'bonus' },
      ],
    },
    defender: {
      title: 'OPERATION IRON WALL',
      narrative: [
        'Threat intelligence indicates an imminent APT-41 operation targeting our banking infrastructure.',
        'Your mission: protect the CORE-DB at all costs. Detect, contain, and eradicate the threat.',
        'You start with 2 action points per turn, but your capability scales as alert level rises.',
        'At alert level 50%, you gain a third AP. At 80%, full Incident Response tools unlock.',
        'Time is on your side. Survive 20 turns and the attacker fails.',
      ],
      objectives: [
        { id: 'obj_survive', text: 'Survive 20 turns without data exfiltration', type: 'primary' },
        { id: 'obj_detect', text: 'Detect attacker presence in 3+ nodes', type: 'primary' },
        { id: 'obj_isolate', text: 'Isolate at least 2 compromised nodes', type: 'secondary' },
        { id: 'obj_clean', text: 'Restore all compromised nodes', type: 'bonus' },
        { id: 'obj_coredb', text: 'Keep CORE-DB uncompromised', type: 'bonus' },
      ],
    },
  },

  // Action success rate modifiers for this scenario
  actionModifiers: {
    SCAN_NETWORK:         { baseCost: 1, baseSuccessRate: 0.95, stealthCost: 3 },
    EXPLOIT_VULNERABILITY:{ baseCost: 1, baseSuccessRate: 0.65, stealthCost: 8, consumesExploitKit: true },
    PHISHING:             { baseCost: 1, baseSuccessRate: 0.55, stealthCost: 15, detectionChance: 0.40 },
    INSTALL_MALWARE:      { baseCost: 1, baseSuccessRate: 0.80, stealthCost: 10 },
    ELEVATE_PRIVILEGES:   { baseCost: 1, baseSuccessRate: 0.60, stealthCost: 12, detectionChance: 0.50 },
    LATERAL_MOVEMENT:     { baseCost: 1, baseSuccessRate: 0.85, stealthCost: 5 },
    EXFILTRATE_DATA:      { baseCost: 1, baseSuccessRate: 0.90, stealthCost: 20, detectionChance: 0.70 },
    CLEAR_LOGS:           { baseCost: 1, baseSuccessRate: 0.90, stealthRestore: 5 },
    MONITOR_LOGS:         { baseCost: 1, baseSuccessRate: 0.80, alertGain: 0 },
    SCAN_FOR_MALWARE:     { baseCost: 1, baseSuccessRate: 0.85, alertGain: 5 },
    APPLY_PATCH:          { baseCost: 1, baseSuccessRate: 0.95, alertGain: 0 },
    ISOLATE_HOST:         { baseCost: 1, baseSuccessRate: 1.00, alertGain: 0, consumesIR: true },
    RESTORE_BACKUP:       { baseCost: 1, baseSuccessRate: 0.90, alertGain: 0, consumesIR: true },
    FIREWALL_RULE:        { baseCost: 1, baseSuccessRate: 1.00, alertGain: 0, exploitReduction: 0.15 },
    INCIDENT_RESPONSE:    { baseCost: 1, baseSuccessRate: 0.75, alertGain: 0, requiresAlert: 80, consumesIR: true },
  },

  // Detection thresholds
  detection: {
    stealthDetectionCurve: [
      // [stealth%, detection probability per action]
      [100, 0.00],
      [80,  0.05],
      [60,  0.15],
      [40,  0.30],
      [20,  0.55],
      [0,   0.85],
    ],
    monitorDetectionBonus: 0.15, // bonus detection when defender monitors
    honeypotDetection: 1.0,      // instant detection if attacker touches honeypot
  },
};
