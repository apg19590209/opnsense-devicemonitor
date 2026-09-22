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

// Device Summary: IP Address leads the primary identity column, with
// Friendly Name grouped before Hostname/MAC/Vendor.
check(
    history.indexOf('id="summary-ip"') <
        history.indexOf('id="summary-friendly-name"'),
    'Device Summary must lead with IP Address before Friendly Name'
);

check(
    history.indexOf('id="summary-friendly-name"') <
        history.indexOf('id="summary-mac"'),
    'Device Summary Friendly Name must precede MAC Address'
);

// The old mutable Notes-count row is gone from the summary.
check(
    !history.includes('id="summary-note-count"'),
    'Device Summary must no longer expose a Notes count row'
);

// Lifecycle concept is explained in plain language.
check(
    history.includes('A lifecycle is one continuous period'),
    'Lifecycle explanation missing'
);

// Lifecycle History table leads with Lifecycle/Status, then IP Address
// before Friendly Name.
const thead = history.match(/<thead>([\s\S]*?)<\/thead>/);

check(
    thead && thead.length > 0,
    'Lifecycle History thead missing'
);

const head = thead[0];

check(
    head.indexOf("lang._('Lifecycle')") <
        head.indexOf("lang._('Status')"),
    'Lifecycle History column order: Lifecycle must precede Status'
);

check(
    head.indexOf("lang._('Status')") <
        head.indexOf("lang._('IP Address')"),
    'Lifecycle History column order: Status must precede IP Address'
);

check(
    head.indexOf("lang._('IP Address')") <
        head.indexOf("lang._('Friendly Name')"),
    'Lifecycle History column order: IP Address must precede Friendly Name'
);

// Notes panel is placed after Lifecycle History.
check(
    history.indexOf('id="lifecycle-history"') <
        history.indexOf('id="device-notes"'),
    'Notes panel must follow Lifecycle History'
);

// Returning-device resolution remains available.
check(
    history.includes('id="return-resolution-controls"'),
    'Returning-device resolution controls missing'
);

check(
    history.includes('id="btn-start-new-lifecycle"'),
    'Start New Lifecycle control missing'
);

check(
    history.includes('/api/devicemonitor/devices/relinklifecycle'),
    'Relink lifecycle action missing'
);

// Hostname source is surfaced in the summary.
check(
    history.includes('function hostnameSourceLabel'),
    'Hostname source label helper missing'
);

// Device Activity navigation remains intact.
check(
    history.includes('id="activity-timeline-link"'),
    'Device Activity navigation missing'
);

// Grouping summary remains, but no grouping management controls return.
[
    'id="physical-device-grouping"',
    'Open Profile',
    'Add to Profile'
].forEach(function(value) {
    check(
        history.includes(value),
        'Device Details grouping summary missing: ' + value
    );
});

[
    'createphysicaldevice',
    'linkphysicaldeviceidentity',
    'removephysicaldeviceidentity'
].forEach(function(value) {
    check(
        !history.includes(value),
        'Device Details must not restore grouping management: ' + value
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
            'FAIL: Device Details JavaScript syntax: ' + error.message
        );
        process.exit(1);
    }
});

console.log('DEVICE_DETAILS_SUMMARY_ORDER=PASS');
console.log('DEVICE_DETAILS_LIFECYCLE_EXPLANATION=PASS');
console.log('DEVICE_DETAILS_HISTORY_ORDER=PASS');
console.log('DEVICE_DETAILS_NOTES_POSITION=PASS');
console.log('DEVICE_DETAILS_RETURNING_CONTROLS=PASS');
console.log('DEVICE_DETAILS_JAVASCRIPT=PASS');
