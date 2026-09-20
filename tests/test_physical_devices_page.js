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
    'id="stat-groups"',
    'id="stat-active"',
    'id="stat-archived"',
    'id="stat-visible"',
    'Create Physical Device',
    'Link Identity',
    'Historical identities',
    'Active identities',
    'Physical-device name',
    '/api/devicemonitor/devices/physicaldevices',
    '/api/devicemonitor/devices/createphysicaldevice',
    '/api/devicemonitor/devices/linkphysicaldeviceidentity',
    '/api/devicemonitor/devices/removephysicaldeviceidentity',
    '/ui/devicemonitor/index/devicehistory?mac=',
    'loadPhysicalDevices();',
    'Identity history will be preserved.',
    'belongs to the same physical',
    'archived_at',
    'active_member_count',
    'total_member_count'
].forEach(function(value) {
    check(
        page.includes(value),
        'Physical Devices page missing: ' + value
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
