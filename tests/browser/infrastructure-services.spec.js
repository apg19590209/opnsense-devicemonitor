const fs = require('node:fs');
const path = require('node:path');
const { test, expect } = require('@playwright/test');

const TARGET_ORIGIN = 'https://192.168.20.23';
const SERVICE_PATH = '/ui/devicemonitor/index/infrastructureservices';
const SERVICES_API = '/api/devicemonitor/devices/services';
const PRIMARY_FIXTURE = require('./fixtures/infrastructure-services-primary.json');
const EDGE_FIXTURE = require('./fixtures/infrastructure-services-edge-cases.json');
const ARTIFACTS = path.join(__dirname, 'artifacts');
const SCREENSHOTS = path.join(ARTIFACTS, 'screenshots');
const guardStates = new WeakMap();

const LAYOUT_CASES = [
  { width: 360, sidebar: 'hidden' },
  { width: 768, sidebar: 'expanded' },
  { width: 1199, sidebar: 'expanded' },
  { width: 1199, sidebar: 'collapsed' },
  { width: 1200, sidebar: 'expanded' },
  { width: 1200, sidebar: 'collapsed' },
  { width: 1440, sidebar: 'expanded' },
  { width: 1440, sidebar: 'collapsed' },
];

function credentials() {
  const filename = process.env.DM_BROWSER_CREDENTIAL_FILE;
  if (!filename) {
    throw new Error('DM_BROWSER_CREDENTIAL_FILE is required');
  }
  const values = {};
  for (const line of fs.readFileSync(filename, 'utf8').split(/\r?\n/)) {
    const index = line.indexOf('=');
    if (index > 0) {
      values[line.slice(0, index)] = line.slice(index + 1);
    }
  }
  if (!values.user || !values.password) {
    throw new Error('browser credential file is incomplete');
  }
  return values;
}

function assertTarget() {
  const base = process.env.DM_BROWSER_BASE_URL;
  if (base !== TARGET_ORIGIN) {
    throw new Error('DM_BROWSER_BASE_URL must equal ' + TARGET_ORIGIN);
  }
}

async function installGuards(page, fixture) {
  assertTarget();
  const state = { unexpected: [] };
  guardStates.set(page, state);

  await page.route('**/*', async route => {
    const request = route.request();
    const url = new URL(request.url());
    const method = request.method().toUpperCase();

    if (url.origin !== TARGET_ORIGIN) {
      state.unexpected.push(method + ' ' + url.origin + url.pathname);
      await route.abort('blockedbyclient');
      return;
    }

    if (url.pathname.startsWith('/api/devicemonitor/')) {
      if (method === 'GET' && url.pathname === SERVICES_API) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(fixture),
        });
        return;
      }
      state.unexpected.push(method + ' ' + url.pathname);
      await route.abort('blockedbyclient');
      return;
    }

    const loginPost = method === 'POST' &&
      (url.pathname === '/' || url.pathname === '/index.php');
    if (method !== 'GET' && !loginPost) {
      state.unexpected.push(method + ' ' + url.pathname);
      await route.abort('blockedbyclient');
      return;
    }

    await route.continue();
  });

  page.on('websocket', socket => {
    state.unexpected.push('WEBSOCKET ' + socket.url());
    socket.close();
  });
  page.on('dialog', async dialog => {
    state.unexpected.push('DIALOG ' + dialog.type());
    await dialog.dismiss();
  });
}

async function openPage(page, fixture, width = 1200) {
  await installGuards(page, fixture);
  await page.setViewportSize({ width, height: 900 });
  await page.goto(TARGET_ORIGIN + '/', { waitUntil: 'domcontentloaded' });

  const username = page.locator('#usernamefld');
  if (await username.isVisible().catch(() => false)) {
    const auth = credentials();
    await username.fill(auth.user);
    await page.locator('#passwordfld').fill(auth.password);
    await page.locator('button[name="login"]').click();
    await expect(username).toHaveCount(0);
  }

  await page.goto(TARGET_ORIGIN + SERVICE_PATH, { waitUntil: 'domcontentloaded' });
  await expect(page.locator('#infrastructure-sticky-controls')).toBeVisible();
  await expect(page.locator('#services-type-filter')).toHaveCount(1);
  await expect(page.locator('#services-type-filter option[value="DNS"]')).toHaveCount(1);
}

async function setSidebar(page, requested) {
  const navigation = page.locator('#navigation');
  if (requested === 'hidden') {
    await expect(navigation).toBeHidden();
    return;
  }

  const collapsed = await navigation.evaluate(node =>
    node.classList.contains('col-sidebar-left')
  );
  const wantCollapsed = requested === 'collapsed';
  if (collapsed !== wantCollapsed) {
    const toggle = page.locator('button.toggle-sidebar');
    if (!await toggle.isVisible().catch(() => false)) {
      throw new Error('sidebar cannot be ' + requested + ' at this viewport');
    }
    await toggle.click();
    await expect.poll(() => navigation.evaluate(node =>
      node.classList.contains('col-sidebar-left')
    )).toBe(wantCollapsed);
  }
}

async function setType(page, value) {
  await page.locator('#services-type-filter').evaluate((select, nextValue) => {
    select.value = nextValue;
    select.dispatchEvent(new Event('change', { bubbles: true }));
    if (window.jQuery && window.jQuery(select).hasClass('selectpicker')) {
      window.jQuery(select).selectpicker('refresh');
    }
  }, value);
}

async function waitForInventoryPane(page, paneId, expectedRowId = null) {
  const pane = page.locator('#' + paneId);
  await expect(page.locator(
    '#infrastructure-tabs li a[href="#' + paneId + '"]'
  )).toHaveCount(1);
  await expect(
    page.locator('#infrastructure-tabs li.active a[href="#' + paneId + '"]')
  ).toHaveCount(1);
  await expect(pane).toHaveCount(1);
  await expect(pane).toHaveClass(/\bactive\b/);
  await expect(pane).toHaveClass(/\bin\b/);
  await expect(pane).toBeVisible();
  await expect(
    page.locator('#infrastructure-tab-content > .tab-pane.active')
  ).toHaveAttribute('id', paneId);
  await expect(
    page.locator('#tab-infrastructure-recent-changes')
  ).not.toHaveClass(/\bactive\b/);

  if (expectedRowId !== null) {
    await expect(pane.locator('.infrastructure-service-table')).toBeVisible();
    await expect(
      pane.locator('tr.dm-service-row[data-service-id="' + expectedRowId + '"]')
    ).toBeVisible();
  }
  return pane;
}

async function selectDns(page, expectedRowId) {
  await setType(page, 'DNS');
  return waitForInventoryPane(
    page,
    'tab-services-dns-servers',
    expectedRowId
  );
}

async function capture(page, name) {
  fs.mkdirSync(SCREENSHOTS, { recursive: true });
  const accountLabel = page.locator('header.page-head .navbar-text');
  await page.screenshot({
    path: path.join(SCREENSHOTS, 'fixture-' + name + '.png'),
    fullPage: true,
    animations: 'disabled',
    mask: await accountLabel.count() ? [accountLabel] : [],
  });
}

async function inventoryGeometry(page, paneId = 'tab-services-dns-servers') {
  return page.locator('#' + paneId).evaluate(pane => {
    const table = pane ? pane.querySelector('.infrastructure-service-table') : null;
    const header = table ? table.querySelector('thead') : null;
    const row = table ? table.querySelector('tbody tr.dm-service-row') : null;
    const cells = row ? Array.from(row.children).filter(node => node.tagName === 'TD') : [];
    const labels = row ? Array.from(row.querySelectorAll('.dm-service-cell-label')) : [];
    const state = node => {
      if (!node) return null;
      const style = getComputedStyle(node);
      const rect = node.getBoundingClientRect();
      return {
        display: style.display,
        position: style.position,
        visible: style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0,
        width: rect.width,
        scrollWidth: node.scrollWidth,
        clientWidth: node.clientWidth,
      };
    };
    return {
      pageClientWidth: document.documentElement.clientWidth,
      pageScrollWidth: document.documentElement.scrollWidth,
      pane: state(pane),
      table: state(table),
      header: state(header),
      row: state(row),
      cells: cells.map(state),
      labels: labels.map(state),
    };
  });
}

async function toolbarGeometry(page) {
  return page.evaluate(() => {
    const showing = document.querySelector('#services-visible');
    const toggle = document.querySelector('.infrastructure-toolbar .dm-show-archived-toggle');
    const checkbox = document.querySelector('#services-show-archived');
    const label = document.querySelector('label[for="services-show-archived"]');
    const showingRect = showing ? showing.getBoundingClientRect() : null;
    const toggleRect = toggle ? toggle.getBoundingClientRect() : null;
    const checkboxRect = checkbox ? checkbox.getBoundingClientRect() : null;
    const labelRect = label ? label.getBoundingClientRect() : null;
    const style = toggle ? getComputedStyle(toggle) : null;
    const sameLine = (first, second) => Boolean(first && second) &&
      Math.max(first.top, second.top) < Math.min(first.bottom, second.bottom);
    return {
      computedColumnGapPx: style ? parseFloat(style.columnGap) : null,
      checkboxLabelEdgePx: checkboxRect && labelRect
        ? labelRect.left - checkboxRect.right
        : null,
      checkboxLabelCenterDeltaY: checkboxRect && labelRect
        ? ((checkboxRect.top + checkboxRect.bottom) -
          (labelRect.top + labelRect.bottom)) / 2
        : null,
      countToggleSameLine: sameLine(showingRect, toggleRect),
      countToggleEdgePx: showingRect && toggleRect
        ? toggleRect.left - showingRect.right
        : null,
    };
  });
}

function expectLayout(geometry, stacked) {
  expect(geometry.pageScrollWidth).toBeLessThanOrEqual(geometry.pageClientWidth + 1);
  expect(geometry.pane).not.toBeNull();
  expect(geometry.pane.scrollWidth).toBeLessThanOrEqual(geometry.pane.clientWidth + 1);
  expect(geometry.table).not.toBeNull();
  expect(geometry.table.width).toBeGreaterThan(0);
  expect(geometry.cells).toHaveLength(6);
  expect(geometry.labels).toHaveLength(6);
  expect(geometry.cells.every(cell => cell.visible)).toBe(true);
  expect(geometry.cells.every(cell =>
    cell.scrollWidth <= cell.clientWidth + 1
  )).toBe(true);

  if (stacked) {
    expect(geometry.table.display).toBe('block');
    expect(geometry.header.display).toBe('none');
    expect(geometry.row.display).toBe('block');
    expect(geometry.cells.every(cell => cell.display === 'block')).toBe(true);
    expect(geometry.labels.every(label => label.display === 'block' && label.visible)).toBe(true);
  } else {
    expect(geometry.table.display).toBe('table');
    expect(geometry.header.display).toBe('table-header-group');
    expect(geometry.row.display).toBe('table-row');
    expect(geometry.cells.every(cell => cell.display === 'table-cell')).toBe(true);
    expect(geometry.labels.every(label => label.display === 'none')).toBe(true);
  }
}

test.describe.configure({ mode: 'serial' });

test.afterEach(async ({ page }) => {
  const state = guardStates.get(page);
  if (state) {
    expect(state.unexpected, 'unexpected network, dialog or websocket activity').toEqual([]);
  }
});

for (const scenario of LAYOUT_CASES) {
  test('layout ' + scenario.width + ' sidebar ' + scenario.sidebar, async ({ page }) => {
    await openPage(page, PRIMARY_FIXTURE, scenario.width);
    await setSidebar(page, scenario.sidebar);
    const dnsPane = await selectDns(page, 1);
    await expect(page.locator('#services-visible')).toHaveText('7');
    await expect(dnsPane.locator('tr.dm-service-row[data-service-id="1"]'))
      .toContainText('192.168.50.10:53/UDP');
    await expect(dnsPane.locator('tr.dm-service-row[data-service-id="1"]'))
      .toContainText('2026-11-20 21:00:00 AEDT');

    const geometry = await inventoryGeometry(page);
    expectLayout(geometry, scenario.width <= 1199);
    const toolbar = await toolbarGeometry(page);
    expect(toolbar.computedColumnGapPx).toBe(8);
    expect(toolbar.checkboxLabelEdgePx).toBeCloseTo(8, 1);
    expect(toolbar.checkboxLabelCenterDeltaY).toBeCloseTo(0, 1);
    await capture(page, 'layout-' + scenario.width + '-' + scenario.sidebar);
  });
}

test('toolbar count and complete toggle separate by 24px on one line', async ({ page }) => {
  await openPage(page, PRIMARY_FIXTURE, 1199);
  await setSidebar(page, 'collapsed');
  await selectDns(page, 1);

  const toolbar = await toolbarGeometry(page);
  expect(toolbar.computedColumnGapPx).toBe(8);
  expect(toolbar.checkboxLabelEdgePx).toBeCloseTo(8, 1);
  expect(toolbar.checkboxLabelCenterDeltaY).toBeCloseTo(0, 1);
  expect(toolbar.countToggleSameLine).toBe(true);
  expect(toolbar.countToggleEdgePx).toBeCloseTo(24, 1);
  await capture(page, 'toolbar-spacing-1199');
});

test('DNS filters preserve no-match state when type is cleared', async ({ page }) => {
  await openPage(page, PRIMARY_FIXTURE, 1199);
  await setSidebar(page, 'collapsed');
  const dnsPane = await selectDns(page, 1);

  const options = await page.locator('#services-type-filter option').allTextContents();
  for (const label of ['DNS', 'SMB', 'NFS', 'RDP', 'VNC']) {
    expect(options).toContain(label);
  }

  await page.locator('#services-search').fill('no-such-service');
  await expect(page.locator('#services-visible')).toHaveText('0');
  await expect(dnsPane).toContainText('No services match the selected filters');

  await setType(page, '');
  const clearedPane = await waitForInventoryPane(
    page,
    'tab-services-dns-servers'
  );
  await expect(page.locator('#services-search')).toHaveValue('no-such-service');
  await expect(page.locator('#services-visible')).toHaveText('0');
  await expect(clearedPane).toContainText('No services match the selected filters');
  await capture(page, 'filters-clear-type-preserves-no-match');
});

test('Show archived includes and excludes the fixture row by label and keyboard', async ({ page }) => {
  await openPage(page, PRIMARY_FIXTURE, 1199);
  await setSidebar(page, 'collapsed');
  await selectDns(page, 1);

  const checkbox = page.locator('#services-show-archived');
  const label = page.locator('label[for="services-show-archived"]');

  await expect(checkbox).not.toBeChecked();
  await expect(page.locator('#services-visible')).toHaveText('7');
  await label.click();
  const checkedPane = await waitForInventoryPane(
    page,
    'tab-services-dns-servers'
  );
  await expect(checkbox).toBeChecked();
  await expect(page.locator('#services-visible')).toHaveText('8');
  await expect(
    checkedPane.locator('tr.dm-service-row[data-service-id="8"]')
  ).toBeVisible();

  await label.click();
  const uncheckedPane = await waitForInventoryPane(
    page,
    'tab-services-dns-servers'
  );
  await expect(checkbox).not.toBeChecked();
  await expect(page.locator('#services-visible')).toHaveText('7');
  await expect(
    uncheckedPane.locator('tr.dm-service-row[data-service-id="8"]')
  ).toHaveCount(0);

  await page.locator('#services-search').focus();
  for (let count = 0; count < 10; count += 1) {
    if (await checkbox.evaluate(node => document.activeElement === node)) break;
    await page.keyboard.press('Tab');
  }
  await expect(checkbox).toBeFocused();
  await page.keyboard.press('Space');
  const keyboardCheckedPane = await waitForInventoryPane(
    page,
    'tab-services-dns-servers'
  );
  await expect(checkbox).toBeChecked();
  await expect(page.locator('#services-visible')).toHaveText('8');
  await expect(
    keyboardCheckedPane.locator('tr.dm-service-row[data-service-id="8"]')
  ).toBeVisible();
  await capture(page, 'show-archived-keyboard-checked');
});

test('Details is pointer and keyboard operable and shared-IP inventory is complete', async ({ page }) => {
  await openPage(page, PRIMARY_FIXTURE, 1200);
  await setSidebar(page, 'expanded');
  const dnsPane = await selectDns(page, 7);

  const row = dnsPane.locator('tr.dm-service-row[data-service-id="7"]');
  const detailsButton = row.locator('button[aria-controls]');
  const details = dnsPane.locator('tr.dm-service-details-row[data-service-details-for="7"]');
  await expect(row).toContainText('192.168.50.1:53/UDP');
  await expect(row.locator('button[aria-label^="Archive:"]')).toBeVisible();
  await detailsButton.click();
  await expect(detailsButton).toHaveAttribute('aria-expanded', 'true');
  await expect(details).toBeVisible();
  await expect(details).toContainText('Matching stored MAC: 18:60:24:6a:64:8c');
  await expect(details).toContainText('Matching endpoint IP: 18:60:24:6a:64:8c');
  await expect(details).toContainText('Matching endpoint IP: f0:42:1c:f6:d2:18');
  expect(await details.getByText('VLAN50', { exact: false }).count()).toBeGreaterThanOrEqual(3);
  await expect(details).toContainText('Stored MAC attribution');
  await expect(details).toContainText('page-load lookups');
  await capture(page, 'details-shared-ip-expanded');

  await detailsButton.focus();
  await page.keyboard.press('Space');
  await expect(detailsButton).toHaveAttribute('aria-expanded', 'false');
  await page.keyboard.press('Enter');
  await expect(detailsButton).toHaveAttribute('aria-expanded', 'true');
});

test('malformed fixture and zero-category activation remain explicit', async ({ page }) => {
  await openPage(page, EDGE_FIXTURE, 1199);
  await setSidebar(page, 'collapsed');
  const dnsPane = await selectDns(page, 101);

  const malformed = dnsPane.locator('tr.dm-service-row[data-service-id="101"]');
  const timeEntries = malformed.locator('.dm-service-time-entry');
  const lastSuccessfulProbe = timeEntries.filter({
    hasText: 'Last successful probe'
  });
  const lastProbeAttempt = timeEntries.filter({
    hasText: 'Last probe attempt'
  });
  await expect(timeEntries).toHaveCount(2);
  await expect(malformed).not.toContainText('not-a-timestamp');
  await expect(lastSuccessfulProbe.locator('dt')).toHaveText(
    'Last successful probe'
  );
  await expect(lastSuccessfulProbe.locator('dd')).toContainText(
    'legacy-verified'
  );
  await expect(
    lastSuccessfulProbe.locator('dd > .dm-timezone-unknown')
  ).toHaveCount(1);
  await expect(
    lastSuccessfulProbe.locator('dd > .dm-timezone-unknown')
  ).toHaveText('Timezone unknown');
  await expect(lastProbeAttempt.locator('dt')).toHaveText(
    'Last probe attempt'
  );
  await expect(lastProbeAttempt.locator('dd')).toContainText(
    'legacy-checked'
  );
  await expect(
    lastProbeAttempt.locator('dd > .dm-timezone-unknown')
  ).toHaveCount(1);
  await expect(
    lastProbeAttempt.locator('dd > .dm-timezone-unknown')
  ).toHaveText('Timezone unknown');

  await setType(page, 'RDP');
  const remotePane = await waitForInventoryPane(page, 'tab-services-remote-access');
  await expect(
    page.locator('#infrastructure-tabs li.active a[aria-controls="tab-services-remote-access"]')
  ).toHaveCount(1);
  await expect(page.locator('#services-visible')).toHaveText('0');
  await expect(remotePane).toContainText('No services match the selected filters');
  await capture(page, 'fixture-malformed-and-zero-category');
});
