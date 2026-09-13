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
    'Physical Device / Related Identities',
    '/api/devicemonitor/devices/physicaldevice',
    '/api/devicemonitor/devices/createphysicaldevice',
    '/api/devicemonitor/devices/linkphysicaldeviceidentity',
    '/api/devicemonitor/devices/removephysicaldeviceidentity',
    '/ui/devicemonitor/index/devicehistory?mac=',
    'Create Physical Device',
    'Link Identity',
    'Identity history will be preserved.'
].forEach(function(value) {
    check(
        history.includes(value),
        'Device Details physical-device UI missing: ' + value
    );
});

[
    'physical-device-link-guidance',
    'belongs to the same physical',
    'such as another network interface',
    'Do not link separate devices',
    'merely because they are the same type or vendor.'
].forEach(function(value) {
    check(
        history.includes(value),
        'Device Details physical-device SAME-DEVICE link guidance ' +
        'missing: ' + value
    );
});

check(
    history.includes(
        'Only continue if this MAC belongs to the same physical'
    ) &&
    history.includes(
        'hardware. Do not link separate devices merely because'
    ) &&
    history.includes('type, model or vendor.'),
    'Link confirmation does not explicitly require SAME physical hardware'
);

check(
    !history.includes('members.length > 1'),
    'UI must allow explicit removal of the sole physical-device identity'
);

check(
    history.includes('loadPhysicalDevice();'),
    'Physical-device grouping is not loaded on Device Details'
);

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
            'FAIL: Device Details physical-device JavaScript syntax: ' +
            error.message
        );
        process.exit(1);
    }
});

console.log('DEVICE_PHYSICAL_GROUP_UI_STRUCTURE=PASS');
console.log('DEVICE_PHYSICAL_GROUP_UI_JAVASCRIPT=PASS');
