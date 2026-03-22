/**
 * Neo-Hack: Gridlock v4.1 — k6 Load Test
 * Simulates 100 concurrent users hitting key API endpoints.
 *
 * Usage:
 *   k6 run -e BASE_URL="https://neohack-staging-xxx.run.app" tests/k6_load_test.js
 *
 * Install k6: https://k6.io/docs/get-started/installation/
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const leaderboardDuration = new Trend('leaderboard_duration');
const worldStateDuration = new Trend('world_state_duration');

export const options = {
  stages: [
    { duration: '15s', target: 25 },   // Warm up
    { duration: '30s', target: 50 },   // Ramp to 50
    { duration: '60s', target: 100 },  // Sustain 100 users
    { duration: '30s', target: 50 },   // Step down
    { duration: '15s', target: 0 },    // Cool down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],   // 95th percentile < 500ms
    http_req_failed: ['rate<0.01'],     // < 1% request failure
    errors: ['rate<0.02'],              // < 2% custom errors
  },
};

const BASE = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  group('Health Check', () => {
    const res = http.get(`${BASE}/api/health`);
    const success = check(res, {
      'health returns 200': (r) => r.status === 200,
      'health returns healthy': (r) => r.json().status === 'healthy',
    });
    errorRate.add(!success);
  });

  group('Leaderboard', () => {
    const res = http.get(`${BASE}/api/leaderboard?limit=20`);
    leaderboardDuration.add(res.timings.duration);
    const success = check(res, {
      'leaderboard 200': (r) => r.status === 200,
      'leaderboard has rankings': (r) => r.json().rankings !== undefined,
    });
    errorRate.add(!success);
  });

  group('World State', () => {
    const res = http.get(`${BASE}/api/world/state`);
    worldStateDuration.add(res.timings.duration);
    const success = check(res, {
      'world state 200': (r) => r.status === 200,
      'world state has nodes': (r) => r.json().nodes !== undefined,
    });
    errorRate.add(!success);
  });

  group('Leaderboard Search', () => {
    const res = http.get(`${BASE}/api/leaderboard/search?q=TEST&limit=10`);
    const success = check(res, {
      'search 200': (r) => r.status === 200,
    });
    errorRate.add(!success);
  });

  group('Current Epoch', () => {
    const res = http.get(`${BASE}/api/epoch/current`);
    // May 404 if no active epoch, that's acceptable
    check(res, {
      'epoch responds': (r) => r.status === 200 || r.status === 404,
    });
  });

  sleep(Math.random() * 2 + 0.5);  // 0.5-2.5s think time
}
