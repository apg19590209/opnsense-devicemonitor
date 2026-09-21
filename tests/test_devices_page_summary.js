const fs = require('fs');
const vm = require('vm');

const devicesPath =
    'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devices.volt';

const view = fs.readFileSync(devicesPath, 'utf8');

function check(condition, message) {
    if (!condition) {
        console.error('FAIL: ' + message);
        process.exit(1);
    }
}

// The Devices header must no longer source its counters from the unfiltered
// global stats endpoint.
check(
    !view.includes('/api/devicemonitor/devices/stats'),
    'Devices header must not call the unfiltered global stats endpoint'
);
check(
    !view.includes('function loadStats'),
    'Devices page must not keep the global loadStats() helper'
);

// The header counters must be derived from the filtered rows.
[
    'function applyDeviceFilters',
    'function summarizeDevices',
    'function updateSummary',
    'updateSummary(filtered);'
].forEach(function (value) {
    check(
        view.includes(value),
        'Devices summary wiring missing: ' + value
    );
});

// Extract the inline script block(s) and neutralise Volt placeholders before
// parsing/executing the JavaScript.
const scripts = view.match(/<script>([\s\S]*?)<\/script>/g);

check(scripts && scripts.length > 0, 'Devices page JavaScript block missing');

const javascript = scripts
    .map(function (block) {
        return block
            .replace(/^<script>/, '')
            .replace(/<\/script>$/, '')
            .replace(/\{\{[\s\S]*?\}\}/g, 'VOLT');
    })
    .join('\n');

// Syntax check (parse only, matching the existing UI test convention).
try {
    new Function(javascript);
} catch (error) {
    console.error('FAIL: Devices page JavaScript syntax: ' + error.message);
    process.exit(1);
}

// Execute the pure filter/summary helpers in an isolated context. The DOM
// bootstrap ($(document).ready) is stubbed out so only the pure functions run.
const sandbox = {
    $: function () {
        return { ready: function () {} };
    },
    document: {}
};
vm.runInNewContext(javascript, sandbox);

check(
    typeof sandbox.applyDeviceFilters === 'function',
    'applyDeviceFilters helper is not exposed'
);
check(
    typeof sandbox.summarizeDevices === 'function',
    'summarizeDevices helper is not exposed'
);

// Fixture mirroring the observed VLAN50 runtime defect (2 online, 1 offline)
// plus unrelated RE0 rows used to prove filter isolation.
const rows = [
    { mac: 'm1', ip: '192.168.50.180', vlan: 'VLAN50', status: 'online' },
    { mac: 'm2', ip: '192.168.50.1', vlan: 'VLAN50', status: 'online' },
    { mac: 'm3', ip: '192.168.50.1', vlan: 'VLAN50', status: 'offline' },
    { mac: 'm4', ip: '192.168.20.1', vlan: 'RE0', status: 'online' },
    { mac: 'm5', ip: '192.168.20.2', vlan: 'RE0', status: 'offline' }
];

function assertSummary(actual, total, online, label) {
    check(
        actual.total === total,
        label + ': total ' + actual.total + ' != ' + total
    );
    check(
        actual.online === online,
        label + ': online ' + actual.online + ' != ' + online
    );
}

// VLAN-only filtering.
const vlanOnly = sandbox.applyDeviceFilters(rows, ['VLAN50'], '');
check(vlanOnly.length === 3, 'VLAN-only filter must keep 3 rows');
assertSummary(sandbox.summarizeDevices(vlanOnly), 3, 2, 'VLAN-only');

// Status-only filtering.
const statusOnly = sandbox.applyDeviceFilters(rows, [], 'offline');
check(statusOnly.length === 2, 'status-only offline filter must keep 2 rows');
assertSummary(sandbox.summarizeDevices(statusOnly), 2, 0, 'status-only');

// Combined VLAN/status filtering.
const combined = sandbox.applyDeviceFilters(rows, ['VLAN50'], 'offline');
check(combined.length === 1, 'combined VLAN50+offline filter must keep 1 row');
assertSummary(sandbox.summarizeDevices(combined), 1, 0, 'combined');

// No filters.
const none = sandbox.applyDeviceFilters(rows, [], '');
check(none.length === 5, 'no filters must keep all 5 rows');
assertSummary(sandbox.summarizeDevices(none), 5, 3, 'no filters');

// Empty input must not throw and must report zero counters.
const empty = sandbox.applyDeviceFilters([], [], '');
check(empty.length === 0, 'empty rows must yield an empty filter result');
assertSummary(sandbox.summarizeDevices(empty), 0, 0, 'empty');

console.log('DEVICES_SUMMARY_VLAN_ONLY=PASS');
console.log('DEVICES_SUMMARY_STATUS_ONLY=PASS');
console.log('DEVICES_SUMMARY_COMBINED=PASS');
console.log('DEVICES_SUMMARY_NO_FILTERS=PASS');
console.log('DEVICES_SUMMARY_JAVASCRIPT=PASS');
