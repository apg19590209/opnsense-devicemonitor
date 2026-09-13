const fs = require('fs');

const devicesPath =
    'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devices.volt';
const historyPath =
    'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devicehistory.volt';

const devices = fs.readFileSync(devicesPath, 'utf8');
const history = fs.readFileSync(historyPath, 'utf8');

function check(condition, message) {
    if (!condition) {
        console.error('FAIL: ' + message);
        process.exit(1);
    }
}

[
    "{{ lang._('Physical Device') }}",
    'function buildGroupingCell(row)',
    'buildGroupingCell(row)',
    'physical_device_id',
    'physical_device_name',
    'physical_device_member_count',
    'devices-grouping-badge',
    'devices-grouping-cell',
    '/ui/devicemonitor/index/devicehistory?mac=',
    '#physical-device-grouping',
    'translations.grouped',
    'translations.identity',
    'translations.identities',
    'memberCount === 1 ? translations.identity : translations.identities',
    "' \\u00b7 '"
].forEach(function(value) {
    check(
        devices.includes(value),
        'Devices page grouping indicator missing: ' + value
    );
});

check(
    devices.includes('\\u2014'),
    'Devices page grouping indicator has no quiet ungrouped state'
);

check(
    history.includes('id="physical-device-grouping"'),
    'Destination physical-device grouping section anchor is missing'
);

[
    'createphysicaldevice',
    'linkphysicaldeviceidentity',
    'removephysicaldeviceidentity'
].forEach(function(value) {
    check(
        !devices.includes(value),
        'Devices page must not duplicate grouping management controls: ' + value
    );
});

const scripts = devices.match(/<script>([\s\S]*?)<\/script>/g);

check(
    scripts && scripts.length > 0,
    'Devices page JavaScript block missing'
);

scripts.forEach(function(block) {
    const javascript = block
        .replace(/^<script>/, '')
        .replace(/<\/script>$/, '')
        // Volt substitutes lang._() placeholders before the browser parses
        // this block, so neutralise them before syntax checking the raw file.
        .replace(/\{\{[\s\S]*?\}\}/g, 'VOLT');

    try {
        new Function(javascript);
    } catch (error) {
        console.error(
            'FAIL: Devices page JavaScript syntax: ' + error.message
        );
        process.exit(1);
    }
});

console.log('DEVICES_PAGE_GROUPING_COLUMN=PASS');
console.log('DEVICES_PAGE_GROUPING_NAVIGATION=PASS');
console.log('DEVICES_PAGE_GROUPING_JAVASCRIPT=PASS');
