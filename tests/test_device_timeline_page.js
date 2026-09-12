const fs = require('fs');

const historyPath =
    'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devicehistory.volt';

const timelinePath =
    'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/activitytimeline.volt';

const controllerPath =
    'src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/IndexController.php';

const history = fs.readFileSync(historyPath, 'utf8');
const timeline = fs.readFileSync(timelinePath, 'utf8');
const controller = fs.readFileSync(controllerPath, 'utf8');

function check(condition, message) {
    if (!condition) {
        console.error('FAIL: ' + message);
        process.exit(1);
    }
}

check(
    history.includes('id="activity-timeline-link"'),
    'Device Details timeline link missing'
);

check(
    history.includes('/ui/devicemonitor/index/activitytimeline?mac='),
    'Device Details timeline link does not preserve MAC'
);

check(
    controller.includes('public function activitytimelineAction()'),
    'Activity Timeline controller action missing'
);

check(
    controller.includes(
        "$this->view->pick('OPNsense/DeviceMonitor/activitytimeline')"
    ),
    'Activity Timeline view mapping missing'
);

check(
    timeline.includes('id="back-device-details"'),
    'Back to Device Details link missing'
);

check(
    timeline.includes('id="grid-device-timeline"'),
    'Timeline grid missing'
);

check(
    timeline.includes(
        "url: '/api/devicemonitor/devices/timeline'"
    ),
    'Timeline API call missing'
);

[
    'IP_CHANGED',
    'HOSTNAME_CHANGED',
    'HOSTNAME_SOURCE_CHANGED',
    'INTERFACE_CHANGED',
    'SERVICE_DISCOVERED',
    'SERVICE_AVAILABLE',
    'SERVICE_UNAVAILABLE',
    'SERVICE_CHANGED',
    'IP_IDENTITY_CHANGED',
    'IPV6_IDENTITY_CHANGED',
    'MAC_MULTI_IP',
    'MAC_MULTI_INTERFACE',
    'IDENTITY_RESOLVED',
    'NMAP_SCAN_COMPLETED',
    'NMAP_SCAN_FAILED',
    'NOTE_CREATED',
    'NOTE_UPDATED',
    'NOTE_ARCHIVED',
    'LIFECYCLE_STARTED',
    'LIFECYCLE_ARCHIVED'
].forEach(function(type) {
    check(
        timeline.includes(type),
        'Missing timeline activity label: ' + type
    );
});

const scripts = timeline.match(/<script>([\s\S]*?)<\/script>/g);

check(
    scripts && scripts.length > 0,
    'Timeline JavaScript block missing'
);

scripts.forEach(function(block) {
    const javascript = block
        .replace(/^<script>/, '')
        .replace(/<\/script>$/, '');

    try {
        new Function(javascript);
    } catch (error) {
        console.error(
            'FAIL: Activity Timeline JavaScript syntax: ' +
            error.message
        );
        process.exit(1);
    }
});

console.log('DEVICE_TIMELINE_PAGE_STRUCTURE=PASS');
console.log('DEVICE_TIMELINE_PAGE_JAVASCRIPT=PASS');
