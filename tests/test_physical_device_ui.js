const fs = require('fs');

const historyPath =
    'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devicehistory.volt';

const history = fs.readFileSync(historyPath, 'utf8');

function check(condition, message) {
    if (!condition) {
        console.error('FAIL: ' + message);
        process.exit(1);
    }
}

[
    'id="physical-device-grouping"',
    'id="physical-device-content"',
    'Physical Device',
    '/api/devicemonitor/devices/physicaldevice',
    'loadPhysicalDevice();',
    'renderPhysicalDeviceSummary',
    'View / Manage Physical Device',
    'Assign to Physical Device',
    '/ui/devicemonitor/index/physicaldevices',
    '?group=',
    'Identities',
    'memberCount'
].forEach(function(value) {
    check(
        history.includes(value),
        'Device Details physical-device summary missing: ' + value
    );
});

[
    'createphysicaldevice',
    'linkphysicaldeviceidentity',
    'removephysicaldeviceidentity',
    'Create Physical Device',
    'physical-device-select',
    'physical-device-controls',
    'physical-device-name',
    'btn-create-physical-device',
    'btn-link-current-identity',
    'related-identity-mac',
    'Link Identity',
    'Related identity removed',
    'renderPhysicalDeviceLinkForm',
    'renderPhysicalDeviceControls',
    'linkCurrentIdentityToPhysicalDevice'
].forEach(function(value) {
    check(
        !history.includes(value),
        'Device Details must not contain grouping management: ' + value
    );
});

check(
    !history.includes('function validMac'),
    'Obsolete Device Details physical-device helper not removed'
);

[
    'loadDeviceData',
    '/api/devicemonitor/devices/lifecycles',
    'renderSummary',
    'renderHistory',
    'renderNotes',
    'startnewlifecycle',
    'addcomment'
].forEach(function(value) {
    check(
        history.includes(value),
        'Device Details lifecycle/comments/history functionality missing: ' +
        value
    );
});

const scripts = history.match(/<script>([\s\S]*?)<\/script>/g);

check(
    scripts && scripts.length > 0,
    'Device Details JavaScript block missing'
);

scripts.forEach(function(block) {
    const javascript = block
        .replace(/^<script>/, '')
        .replace(/<\/script>$/, '');

    try {
        new Function(javascript);
    } catch (error) {
        console.error(
            'FAIL: Device Details physical-device summary JavaScript syntax: ' +
            error.message
        );
        process.exit(1);
    }
});

console.log('DEVICE_PHYSICAL_GROUP_UI_STRUCTURE=PASS');
console.log('DEVICE_PHYSICAL_GROUP_UI_JAVASCRIPT=PASS');
