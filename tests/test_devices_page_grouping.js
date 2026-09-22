const fs = require('fs');

const devicesPath =
    'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devices.volt';

const devices = fs.readFileSync(devicesPath, 'utf8');

function check(condition, message) {
    if (!condition) {
        console.error('FAIL: ' + message);
        process.exit(1);
    }
}

[
    "{{ lang._('Device Profile') }}",
    'function buildGroupingCell(row)',
    'buildGroupingCell(row)',
    'physical_device_id',
    'physical_device_name',
    'physical_device_member_count',
    'devices-grouping-badge',
    'devices-grouping-cell',
    '/ui/devicemonitor/index/physicaldevices?group=',
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
    !devices.includes('#physical-device-grouping'),
    'Grouping badge must no longer target the Device Details anchor'
);

check(
    !devices.includes('translations.grouped'),
    'Devices page grouping badge must not use a grouped fallback label'
);

check(
    devices.includes('if (!groupId || memberCount < 1)'),
    'Grouping badge has no invalid/missing group-id guard'
);

check(
    devices.includes("$('<span>').addClass('text-muted').text('\\u2014')"),
    'Ungrouped state must render a quiet non-link span'
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
