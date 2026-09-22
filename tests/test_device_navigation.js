const fs = require('fs');

const ROOT = 'src/opnsense/mvc/app';

const menu = fs.readFileSync(
    ROOT + '/models/OPNsense/DeviceMonitor/Menu/Menu.xml',
    'utf8'
);
const devices = fs.readFileSync(
    ROOT + '/views/OPNsense/DeviceMonitor/devices.volt',
    'utf8'
);
const profiles = fs.readFileSync(
    ROOT + '/views/OPNsense/DeviceMonitor/physicaldevices.volt',
    'utf8'
);
const details = fs.readFileSync(
    ROOT + '/views/OPNsense/DeviceMonitor/devicehistory.volt',
    'utf8'
);
const summary = fs.readFileSync(
    ROOT + '/views/OPNsense/DeviceMonitor/changesummary.volt',
    'utf8'
);

function check(condition, message) {
    if (!condition) {
        console.error('FAIL: ' + message);
        process.exit(1);
    }
}

// Menu: exactly one Devices submenu entry, no separate Physical Devices entry.
check(
    (menu.match(/VisibleName="Devices"/g) || []).length === 1,
    'Menu must expose exactly one Devices submenu entry'
);
check(
    !menu.includes('Physical Devices') && !menu.includes('PhysicalDevices'),
    'Menu must not expose a separate Physical Devices entry'
);

const devicesLink = '/ui/devicemonitor/index/devices';
const profilesLink = '/ui/devicemonitor/index/physicaldevices';

function hasTabs(text) {
    return text.includes('Network Identities') &&
        text.includes('Device Profiles') &&
        text.includes(devicesLink) &&
        text.includes(profilesLink);
}

check(hasTabs(devices), 'Network Identities view must show both navigation tabs');
check(hasTabs(profiles), 'Device Profiles view must show both navigation tabs');

const activeMarker = 'role="presentation" class="active"';

check(
    devices.indexOf(activeMarker) < devices.indexOf(devicesLink) &&
        devices.indexOf(devicesLink) < devices.indexOf(profilesLink),
    'Network Identities view must mark the Network Identities tab active'
);

check(
    profiles.indexOf(devicesLink) < profiles.indexOf(activeMarker) &&
        profiles.indexOf(activeMarker) < profiles.indexOf(profilesLink),
    'Device Profiles view must mark the Device Profiles tab active'
);

check(
    devices.includes(
        'Automatically discovered network identities. Each row represents one MAC address.'
    ),
    'Network Identities explanatory text missing'
);
check(
    profiles.includes(
        'Real-world devices linked to one or more network identities, such as wired and Wi-Fi adapters.'
    ),
    'Device Profiles explanatory text missing'
);

// Compatibility: physicaldevices route/API identifiers must remain unchanged.
[
    '/ui/devicemonitor/index/physicaldevices',
    '/api/devicemonitor/devices/physicaldevices',
    'createphysicaldevice',
    'linkphysicaldeviceidentity',
    'removephysicaldeviceidentity',
    'physical_devices',
    'physical_device_id'
].forEach(function(value) {
    check(profiles.includes(value), 'physicaldevices identifier missing: ' + value);
});

// Compatibility: database table identifiers must remain unchanged (model).
const model = fs.readFileSync(
    ROOT + '/models/OPNsense/DeviceMonitor/DeviceMonitor.php',
    'utf8'
);
[
    'physical_devices',
    'physical_device_memberships'
].forEach(function(value) {
    check(model.includes(value), 'model database identifier missing: ' + value);
});

// The Device Profiles route must render the same standard page heading as the
// Network Identities view (Services: Device Monitor: Devices).
const controller = fs.readFileSync(
    ROOT + '/controllers/OPNsense/DeviceMonitor/IndexController.php',
    'utf8'
);
check(
    controller.includes('function physicaldevicesAction') &&
        controller.includes("gettext('Services')") &&
        controller.includes("gettext('Device Monitor')") &&
        controller.includes("gettext('Devices')"),
    'Device Profiles route must set the standard Devices page heading'
);

// Old affected user-facing terminology must be absent from active UI templates.
[
    ['devices', devices],
    ['profiles', profiles],
    ['details', details],
    ['summary', summary]
].forEach(function(pair) {
    ['Physical Device', 'Physical Devices', 'Device Group', 'Device Groups',
     'Create Device'].forEach(function(bad) {
        check(
            !pair[1].includes(bad),
            pair[0] + ' view must not contain old terminology: ' + bad
        );
    });
});

console.log('DEVICE_NAVIGATION_MENU=PASS');
console.log('DEVICE_NAVIGATION_TABS=PASS');
console.log('DEVICE_NAVIGATION_ACTIVE=PASS');
console.log('DEVICE_NAVIGATION_EXPLANATORY=PASS');
console.log('DEVICE_NAVIGATION_COMPAT=PASS');
console.log('DEVICE_NAVIGATION_TERMINOLOGY=PASS');
console.log('DEVICE_NAVIGATION_HEADING=PASS');
