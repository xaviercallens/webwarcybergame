/**
 * Playwright config for demo video recording.
 * Records WebM video at 1280x720, 30s timeout per action.
 * 
 * Usage: npx playwright test --config=playwright.demo.config.js
 */
import { defineConfig } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const recordingsDir = path.resolve(__dirname, '..', '..', 'specs', 'demo_recordings');

export default defineConfig({
  testDir: './e2e',
  testMatch: 'demo-recording.spec.js',
  timeout: 720_000,  // 12 minutes max (10 min demo + buffer)
  retries: 0,
  workers: 1,        // Single worker for sequential recording

  use: {
    baseURL: 'http://localhost:5173',
    headless: true,    // Headless for CI; video still records
    viewport: { width: 1280, height: 720 },
    video: {
      mode: 'on',
      size: { width: 1280, height: 720 },
    },
    screenshot: 'on',
    trace: 'on',
    launchOptions: {
      slowMo: 100,  // Slight slowdown for visual clarity
    },
  },

  outputDir: recordingsDir,

  reporter: [
    ['list'],
  ],

  webServer: {
    command: 'npm run dev',
    port: 5173,
    reuseExistingServer: true,
    timeout: 15000,
  },
});
