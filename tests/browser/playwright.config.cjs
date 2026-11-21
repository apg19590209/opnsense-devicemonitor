const path = require('node:path');
const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: __dirname,
  testMatch: 'infrastructure-services.spec.js',
  timeout: 30000,
  expect: {
    timeout: 7000,
  },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: true,
  outputDir: path.join(__dirname, 'artifacts', 'test-output'),
  reporter: [
    ['list'],
    ['json', { outputFile: path.join(__dirname, 'artifacts', 'results.json') }],
    ['html', { outputFolder: path.join(__dirname, 'artifacts', 'html-report'), open: 'never' }],
  ],
  use: {
    browserName: 'firefox',
    headless: true,
    viewport: { width: 1200, height: 900 },
    ignoreHTTPSErrors: false,
    serviceWorkers: 'block',
    actionTimeout: 7000,
    navigationTimeout: 20000,
    screenshot: 'off',
    trace: 'off',
    video: 'off',
    launchOptions: {
      firefoxUserPrefs: {
        'security.enterprise_roots.enabled': true,
      },
    },
  },
});
