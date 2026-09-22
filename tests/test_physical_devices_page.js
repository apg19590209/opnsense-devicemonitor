const fs = require('fs');

const pagePath =
    'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/physicaldevices.volt';

const page = fs.readFileSync(pagePath, 'utf8');

function check(condition, message) {
    if (!condition) {
        console.error('FAIL: ' + message);
        process.exit(1);
    }
}

[
    'id="physical-devices-list"',
    'id="filter-state"',
    'id="physical-devices-search"',
    'id="create-form"',
    'id="btn-create-toggle"',
    'id="btn-create-submit"',
    'id="btn-refresh"',
    'id="stat-devices"',
    'id="stat-current"',
    'id="stat-archived"',
    'id="stat-visible"',
    'data-device-id',
    'URLSearchParams',
    'revealDevice();',
    'Create Profile',
    'Add Identity',
    'Unlink Identity',
    'View Device Details',
    'Profile name',
    'Profile Name',
    'Current Identities',
    'Previous Identities',
    'Current Profiles',
    'Archived Profiles',
    'All Profiles',
    "/api/devicemonitor/devices/physicaldevices",
    '/api/devicemonitor/devices/createphysicaldevice',
    '/api/devicemonitor/devices/linkphysicaldeviceidentity',
    '/api/devicemonitor/devices/removephysicaldeviceidentity',
    '/ui/devicemonitor/index/devicehistory?mac=',
    'loadPhysicalDevices();',
    'Identity history will be preserved.',
    'belongs to the same device profile',
    'archived_at',
    'current_identity_count',
    'previous_identity_count',
    "params.get('group')"
].forEach(function(value) {
    check(
        page.includes(value),
        'Physical Devices page missing: ' + value
    );
});

// The Device Profiles summary must use the "Profiles" label, not "Devices".
check(
    page.includes("{{ lang._('Profiles') }}:"),
    'Device Profiles summary must use the "Profiles" label'
);
check(
    !page.includes("{{ lang._('Devices') }}:"),
    'Device Profiles summary must not use the "Devices" label'
);

// User-facing implementation terminology must not remain.
[
    'Group ID',
    'Active identities',
    'Historical identities',
    'Link Identity',
    'Total Groups',
    'Active Groups',
    'All Groups',
    'seed MAC'
].forEach(function(value) {
    check(
        !page.includes(value),
        'Physical Devices page must not expose: ' + value
    );
});

const scripts = page.match(/<script>([\s\S]*?)<\/script>/g);

check(
    scripts && scripts.length > 0,
    'Physical Devices page JavaScript block missing'
);

scripts.forEach(function(block) {
    const javascript = block
        .replace(/^<script>/, '')
        .replace(/<\/script>$/, '');

    try {
        new Function(javascript);
    } catch (error) {
        console.error(
            'FAIL: Physical Devices page JavaScript syntax: ' +
            error.message
        );
        process.exit(1);
    }
});

console.log('PHYSICAL_DEVICES_PAGE_STRUCTURE=PASS');
console.log('PHYSICAL_DEVICES_PAGE_JAVASCRIPT=PASS');
