const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.resolve(__dirname, '..');

const view = path.join(
    root,
    'src',
    'opnsense',
    'mvc',
    'app',
    'views',
    'OPNsense',
    'DeviceMonitor',
    'infrastructureservices.volt'
);

const text = fs.readFileSync(view, 'utf8');

const start = text.indexOf(
    '    function verifiedTime(value) {'
);

const end = text.indexOf(
    '    function consolidateServices(rows) {',
    start
);

if (start < 0 || end < 0) {
    throw new Error(
        'Unable to extract Infrastructure Services lifecycle functions'
    );
}

const functions = text.slice(start, end);

const assertions = `

function check(name, actual, expected) {
    if (actual !== expected) {
        throw new Error(
            name +
            '=FAIL actual=' +
            actual +
            ' expected=' +
            expected
        );
    }

    console.log(name + '=PASS');
}

const fixedNow = Date.parse(
    '2026-09-06T10:00:00'
);

Date.now = function() {
    return fixedNow;
};

check(
    'STALE_RECENT_AVAILABLE',
    effectiveStatus({
        status: 'available',
        last_verified: '2026-09-06 09:59:59'
    }),
    'available'
);

check(
    'STALE_EXACT_TWO_HOURS',
    effectiveStatus({
        status: 'available',
        last_verified: '2026-09-06 08:00:00'
    }),
    'available'
);

check(
    'STALE_OVER_TWO_HOURS',
    effectiveStatus({
        status: 'available',
        last_verified: '2026-09-06 07:59:59'
    }),
    'stale'
);

check(
    'STALE_MISSING_TIMESTAMP',
    effectiveStatus({
        status: 'available',
        last_verified: ''
    }),
    'stale'
);

check(
    'STALE_INVALID_TIMESTAMP',
    effectiveStatus({
        status: 'available',
        last_verified: 'not-a-date'
    }),
    'stale'
);

check(
    'UNAVAILABLE_PRECEDENCE',
    effectiveStatus({
        status: 'unavailable',
        last_verified: '2000-01-01 00:00:00'
    }),
    'unavailable'
);

console.log(
    'PHASE3_STALE_UI_LIFECYCLE=PASS'
);
`;

vm.runInNewContext(
    functions + assertions,
    {
        console: console
    }
);