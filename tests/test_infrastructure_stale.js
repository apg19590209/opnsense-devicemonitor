const {renderTranslations} = require('./render_translations');
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
const start = text.indexOf('    function recordedStatusLabel(status) {');
const end = text.indexOf('    function serviceChangeLabel(row) {', start);
const timeStart = text.indexOf('    function storedEventTimeText(row) {');
const timeEnd = text.indexOf('    function recentStoredMacText(row) {', timeStart);
const normalizeStart = text.indexOf('    function normalizeServices(rows) {');
const archiveStart = text.indexOf('    function serviceArchiveRequest(row) {');
const archiveEnd = text.indexOf('    function filteredRows() {', archiveStart);

if (
    start < 0 ||
    end < 0 ||
    timeStart < 0 ||
    timeEnd < 0 ||
    normalizeStart < 0 ||
    archiveStart < 0 ||
    archiveEnd < 0
) {
    throw new Error('Unable to extract Infrastructure Services presentation helpers');
}

if (text.includes('<time')) {
    throw new Error('Ambiguous stored timestamps must not receive a machine datetime attribute');
}
if (text.includes('Date.now()')) {
    throw new Error('Recorded status must not depend on browser-time freshness');
}
if (
    text.slice(start, end).includes('new Date') ||
    text.slice(timeStart, timeEnd).includes('new Date')
) {
    throw new Error('Service timeline timestamps must use server-side conversion');
}
if (text.includes('.html(') || text.includes('innerHTML')) {
    throw new Error('Dynamic service values must use text nodes');
}
if (!text.includes('dm-service-time-entry')) {
    throw new Error('Observation labels and values must use stackable entries');
}
if (!text.includes('border-right: 1px solid #e2e6ea')) {
    throw new Error('Recorded State and Evidence lack a desktop separator');
}
if (!text.includes('min-height: 32px')) {
    throw new Error('Narrow-width action controls lack a usable target height');
}
if (text.includes('text-overflow') || text.includes('letter-spacing:')) {
    throw new Error('Presentation must not truncate or manipulate letter spacing');
}
if (!text.includes("lang.query('Event Time')")) {
    throw new Error('Recent Service Changes must use the Event Time heading');
}

const helpers = renderTranslations(
    text.slice(start, end) +
    '\n' +
    text.slice(timeStart, timeEnd) +
    '\n' +
    text.slice(normalizeStart, archiveStart) +
    '\n' +
    text.slice(archiveStart, archiveEnd)
);
const assertions = `
function check(name, actual, expected) {
    if (actual !== expected) {
        throw new Error(
            name + '=FAIL actual=' + JSON.stringify(actual) +
            ' expected=' + JSON.stringify(expected)
        );
    }
    console.log(name + '=PASS');
}

check(
    'RECORDED_STATUS_AVAILABLE',
    recordedStatusLabel('available'),
    'Available'
);
check(
    'RECORDED_STATUS_UNAVAILABLE',
    recordedStatusLabel('unavailable'),
    'Unavailable'
);
check(
    'RECORDED_STATUS_UNKNOWN',
    recordedStatusLabel('unknown'),
    'Unknown'
);
check(
    'RECORDED_STATUS_MISSING',
    recordedStatusLabel(''),
    'Recorded state not available'
);

check(
    'EVIDENCE_AUTHORITATIVE_CONFIDENCE_PRECEDENCE',
    serviceEvidenceKind({
        evidence_kind: 'probe',
        confidence: 'authoritative',
        detection_method: 'runtime_probe'
    }),
    'authoritative'
);
check(
    'EVIDENCE_AUTHORITATIVE_DETECTION_PRECEDENCE',
    serviceEvidenceKind({
        evidence_kind: 'probe',
        confidence: 'verified',
        detection_method: 'authoritative_runtime'
    }),
    'authoritative'
);
check(
    'EVIDENCE_UNKNOWN_NEUTRAL',
    evidenceLabel({
        evidence_kind: 'unknown',
        confidence: '',
        detection_method: ''
    }),
    'Evidence source not classified'
);

check(
    'PROBE_OBSERVATION_LABELS',
    JSON.stringify(observationValues({
        evidence_kind: 'probe',
        last_verified: '2026-11-19 23:10:02',
        last_checked: '2026-11-20 00:10:02'
    })),
    JSON.stringify([
        ['Last successful probe', '2026-11-19 23:10:02', true],
        ['Last probe attempt', '2026-11-20 00:10:02', true]
    ])
);
check(
    'AUTHORITATIVE_OBSERVATION_LABELS',
    JSON.stringify(observationValues({
        evidence_kind: 'authoritative',
        last_verified: '2026-11-19 23:10:02',
        last_checked: '2026-11-20 00:10:02'
    })),
    JSON.stringify([
        ['Evidence recorded', '2026-11-19 23:10:02', true],
        ['Evidence refreshed', '2026-11-20 00:10:02', true]
    ])
);
check(
    'MIXED_OBSERVATION_PROVENANCE',
    JSON.stringify(observationValues({
        evidence_kind: 'probe',
        first_detected: '2026-11-19 22:00:00',
        first_detected_display: '2026-11-19 22:00:00',
        first_detected_timestamp_domain: 'unknown',
        last_verified: '2026-11-19 23:10:02',
        last_verified_display: '20.11.2026 - 10:10:02 AEDT',
        last_verified_timestamp_domain: 'utc',
        last_checked: '2026-11-20 00:10:02',
        last_checked_display: '20.11.2026 - 11:10:02 AEDT',
        last_checked_timestamp_domain: 'utc',
        timestamp_timezone: 'Australia/Sydney'
    })),
    JSON.stringify([
        ['Last successful probe', '20.11.2026 - 10:10:02 AEDT', false],
        ['Last probe attempt', '20.11.2026 - 11:10:02 AEDT', false]
    ])
);
check(
    'MISSING_OBSERVATION_NOTE',
    JSON.stringify(observationValues({
        evidence_kind: 'probe',
        last_verified: '',
        last_checked: ''
    })),
    JSON.stringify([
        ['Last successful probe', '—', false],
        ['Last probe attempt', '—', false]
    ])
);

check(
    'ENDPOINT_FORMAT',
    endpointText({ip: '192.168.50.20', port: 53, protocol: 'udp'}),
    '192.168.50.20:53/UDP'
);
check('ENDPOINT_MISSING', endpointText({}), 'Endpoint not recorded');
check('INTERFACE_MISSING', locationText({}), 'Interface not recorded');

check('INVENTORY_EMPTY', inventoryCountText({}), 'No stored inventory matches');
check(
    'INVENTORY_COUNTS',
    inventoryCountText({
        inventory_matches: {
            by_mac: [{mac: 'AA'}],
            by_ip: [{mac: 'BB'}, {mac: 'CC'}]
        }
    }),
    '2 matching endpoint IP; 1 matching stored MAC'
);
check(
    'INVENTORY_ORDER_PRESERVED',
    inventoryCollection({
        inventory_matches: {
            by_ip: [{mac: 'BB'}, {mac: 'CC'}]
        }
    }, 'by_ip').map(function(match) { return match.mac; }).join(','),
    'BB,CC'
);
check(
    'HOSTILE_INVENTORY_TEXT_PRESERVED_AS_TEXT',
    inventoryMatchText({
        mac: 'aa:bb:cc:dd:ee:21',
        ip: '192.168.50.20',
        monitored_interface_label: '<script>alert(1)</script>',
        hostname: 'A&B'
    }, 'ip'),
    'Matching endpoint IP: aa:bb:cc:dd:ee:21 @ 192.168.50.20 Monitored interface label: <script>alert(1)</script> A&B'
);
check(
    'AMBIGUOUS_EVENT_TIME_PRESERVED',
    storedEventTimeText({
        occurred_at_stored: '2026-11-16 21:52:36',
        occurred_at_display: '2026-11-16 21:52:36',
        timestamp_domain: 'unknown'
    }),
    '2026-11-16 21:52:36'
);
check(
    'TIMEZONE_UNKNOWN_LABEL',
    timezoneUnknownLabel(),
    'Timezone unknown'
);
check(
    'TIMEZONE_TABLE_EXPLANATION_WITH_ZONE',
    timezoneTableText([
        {timestamp_timezone: 'Australia/Sydney'}
    ]),
    'Unknown timezone values remain exactly as stored because UTC provenance is unavailable. Displayed in Australia/Sydney.'
);
check(
    'TIMEZONE_TABLE_EXPLANATION_WITHOUT_ROWS',
    timezoneTableText([]),
    'Unknown timezone values remain exactly as stored because UTC provenance is unavailable.'
);

const first = {id: 41, archived: 0};
const second = {id: 42, archived: 1};
const normalized = normalizeServices([
    {id: 41, service_type: 'dns'},
    {id: 42, service_type: 'dns'}
]);
check(
    'LEFT_SERVICE_ROWS_PRESERVED',
    normalized.map(function(row) { return row.id; }).join(','),
    '41,42'
);
check(
    'ACTION_TARGET_FIRST',
    JSON.stringify(serviceArchiveRequest(first)),
    JSON.stringify({id: 41, archive: '1'})
);
check(
    'ACTION_TARGET_SECOND',
    JSON.stringify(serviceArchiveRequest(second)),
    JSON.stringify({id: 42, archive: '0'})
);
check(
    'ACTION_TARGETS_DISTINCT',
    serviceArchiveRequest(first).id !== serviceArchiveRequest(second).id,
    true
);

console.log('INFRASTRUCTURE_PRESENTATION_HELPERS=PASS');
`;

vm.runInNewContext(
    helpers + assertions,
    {
        console: console,
        dash: function(value) {
            return value === undefined || value === null || value === ''
                ? '\u2014'
                : value;
        },
        $: (function() {
            const stub = function() {
                throw new Error('DOM should not be used by presentation helper tests');
            };
            stub.extend = function(target, source) {
                return Object.assign({}, target, source);
            };
            return stub;
        })()
    }
);
