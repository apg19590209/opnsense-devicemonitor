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
const serviceTypeStart = text.indexOf('    function serviceTypeLabel(type) {');
const groupEnd = text.indexOf('    function recordedStatusLabel(status) {', serviceTypeStart);
const filterStart = text.indexOf('    function filterServices(rows, filters) {');
const filterEnd = text.indexOf('    var preferredOrder = [', filterStart);
const categoryStart = filterEnd;
const categoryEnd = text.indexOf('    function categoryRank(category) {', categoryStart);
const applyStart = text.indexOf('    function applyInventoryFilters(refreshTabs) {');
const applyEnd = text.indexOf('    function renderTabs() {', applyStart);

if (
    start < 0 ||
    end < 0 ||
    timeStart < 0 ||
    timeEnd < 0 ||
    normalizeStart < 0 ||
    archiveStart < 0 ||
    archiveEnd < 0 ||
    serviceTypeStart < 0 ||
    groupEnd < 0 ||
    filterStart < 0 ||
    filterEnd < 0 ||
    categoryStart < 0 ||
    categoryEnd < 0 ||
    applyStart < 0 ||
    applyEnd < 0
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
const serviceStackStart = text.indexOf('@media (max-width: 1199px) {');
const serviceStackEnd = text.indexOf(
    '\n}\n\n/* Tabbed Infrastructure Services layout.',
    serviceStackStart
);
if (serviceStackStart < 0 || serviceStackEnd < 0) {
    throw new Error('Service table stacked breakpoint is missing');
}
const serviceStack = text.slice(serviceStackStart, serviceStackEnd + 2);
const desktopDivider = text.indexOf('border-right: 1px solid #e2e6ea');
if (desktopDivider < 0 || desktopDivider > serviceStackStart) {
    throw new Error('Recorded State and Evidence lack a desktop separator');
}
if (
    !serviceStack.includes(
        '.infrastructure-service-table td {\n' +
        '        display: block;\n' +
        '        width: 100% !important;'
    ) ||
    !serviceStack.includes(
        '.infrastructure-service-table thead {\n' +
        '        display: none;'
    ) ||
    !serviceStack.includes(
        '.dm-service-cell-label {\n' +
        '        display: block;'
    ) ||
    !serviceStack.includes(
        '.dm-service-details-grid {\n' +
        '        grid-template-columns: 1fr;'
    ) ||
    !serviceStack.includes(
        '.dm-service-row > td:nth-child(2) {\n' +
        '        padding-right: 0 !important;\n' +
        '        border-right: 0 !important;'
    )
) {
    throw new Error('Service table stacked row presentation is incomplete');
}
if (!serviceStack.includes('min-height: 32px;')) {
    throw new Error('Narrow-width action controls lack a usable target height');
}
if (
    !text.includes(".addClass('dm-service-time-entry')") ||
    !text.includes('timezoneUnknownBadge()') ||
    !text.includes('.text(inventoryCountText(row))')
) {
    throw new Error('Stacked rows lost timestamp provenance or inventory values');
}
if (text.includes('text-overflow') || text.includes('letter-spacing:')) {
    throw new Error('Presentation must not truncate or manipulate letter spacing');
}
const detailsControls = text.indexOf(".attr('aria-controls', detailsId)");
const detailsButtonStart = text.lastIndexOf(
    "$('<button type=\"button\">')",
    detailsControls
);
const detailsButtonEnd = text.indexOf(
    '.appendTo($attribution);',
    detailsControls
);
const detailsButton = text.slice(detailsButtonStart, detailsButtonEnd);
if (
    detailsControls < 0 ||
    detailsButtonStart < 0 ||
    detailsButtonEnd < 0 ||
    !detailsButton.includes(".attr('aria-expanded', 'false')") ||
    !detailsButton.includes(".text({{ lang.query('Details')|json_encode(15) }})") ||
    !text.includes(
        "$attribution.find('button').on('click', function() {"
    ) ||
    !text.includes("$detailsRow.toggle(!expanded);")
) {
    throw new Error('Keyboard-operable Details disclosure was removed');
}
if (
    !text.includes(".attr('data-service-id', row.id)") ||
    !text.includes("actionLabel + ': ' +") ||
    !text.includes('serviceArchiveRequest(row)')
) {
    throw new Error('Exact-row action wiring was removed');
}
if (!text.includes("lang.query('Event Time')")) {
    throw new Error('Recent Service Changes must use the Event Time heading');
}
if (!text.includes("devicemonitor_t('All Service Types')")) {
    throw new Error('All Service Types label is missing');
}
if (
    !text.includes(
        "devicemonitor_t('These filters apply to service inventory, not Recent Service Changes.')"
    )
) {
    throw new Error('Service inventory filter scope is not stated');
}
if (!text.includes(".text(serviceTypeLabel(type))")) {
    throw new Error('Type filter does not show exact service types');
}
if (!text.includes("lang.query('No services match the selected filters')")) {
    throw new Error('Explicit no-match inventory state is missing');
}
if (!text.includes("lang.query('Service Inventory')")) {
    throw new Error('Stable inventory fallback label is missing');
}
if (!text.includes('class="dm-show-archived-toggle"')) {
    throw new Error('Show archived must use the scoped inline control');
}
if (!text.includes('<input id="services-show-archived" type="checkbox">')) {
    throw new Error('Show archived checkbox ID changed');
}
if (!text.includes('<label for="services-show-archived">')) {
    throw new Error('Show archived label is not explicitly associated');
}
if (
    /<label[^>]*class=["'][^"']*checkbox-inline[^"']*["'][^>]*>\s*<input[^>]+id=["']services-show-archived/.test(text)
) {
    throw new Error('Show archived must not use inherited checkbox-inline positioning');
}
const showArchivedRule = text.match(
    /\.infrastructure-toolbar \.dm-show-archived-toggle \{([\s\S]*?)\}/
);
if (
    !showArchivedRule ||
    !showArchivedRule[1].includes('display: inline-flex;') ||
    !showArchivedRule[1].includes('align-items: center;') ||
    !showArchivedRule[1].includes('gap: 8px;') ||
    !showArchivedRule[1].includes('flex-wrap: nowrap;') ||
    !showArchivedRule[1].includes('margin: 0;') ||
    !showArchivedRule[1].includes('margin-left: 16px;') ||
    !text.includes('flex: 0 0 auto;') ||
    !text.includes('width: auto;') ||
    !text.includes('min-width: 0;')
) {
    throw new Error('Show archived control lacks scoped alignment and spacing');
}
if (!text.includes('@media (max-width: 991px), (max-height: 640px)')) {
    throw new Error('Compact sticky breakpoint is missing');
}
if (
    !text.includes('.infrastructure-sticky-controls {\n        position: static;') ||
    !text.includes('.infrastructure-sticky-controls::before {\n        display: none;') ||
    !text.includes('.infrastructure-tab-content thead th {\n        position: static !important;')
) {
    throw new Error('Compact mode does not fully disable the sticky stack');
}
if (
    !text.includes('.infrastructure-sticky-controls {\n    position: sticky;') ||
    !text.includes('.infrastructure-tab-content thead th {\n    position: sticky;')
) {
    throw new Error('Desktop sticky behaviour was removed');
}
if (
    /\.css\(\s*['"]position['"]|\.style\.position\s*=/.test(text)
) {
    throw new Error('Runtime JavaScript must not re-enable sticky positioning');
}
if (
    text.includes('body {') ||
    text.includes('.page-head {') ||
    text.includes('.page-foot {') ||
    text.includes('.page-side {')
) {
    throw new Error('Infrastructure Services must not override global layout');
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
        last_verified_display: '2026-11-20 10:10:02 AEDT',
        last_verified_timestamp_domain: 'utc',
        last_checked: '2026-11-20 00:10:02',
        last_checked_display: '2026-11-20 11:10:02 AEDT',
        last_checked_timestamp_domain: 'utc',
        timestamp_timezone: 'Australia/Sydney'
    })),
    JSON.stringify([
        ['Last successful probe', '2026-11-20 10:10:02 AEDT', false],
        ['Last probe attempt', '2026-11-20 11:10:02 AEDT', false]
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

const filterSource =
    text.slice(serviceTypeStart, groupEnd) +
    '\n' +
    text.slice(filterStart, filterEnd) +
    '\n' +
    text.slice(categoryStart, categoryEnd);
const filterContext = {
    console: console,
    inventoryFallbackCategory: 'Service Inventory',
    searchText: function(row) {
        return [
            row.service_type,
            row.ip,
            row.hostname,
            row.mac
        ].join(' ').toLowerCase();
    },
    $: function() {
        throw new Error('DOM should not be used by pure filter tests');
    }
};
vm.runInNewContext(
    filterSource +
    '\nthis.filterServices = filterServices;' +
    '\nthis.groupServicesByCategory = groupServicesByCategory;' +
    '\nthis.resolveInventoryCategory = resolveInventoryCategory;' +
    '\nthis.serviceTypeLabel = serviceTypeLabel;' +
    '\nthis.categoryForType = categoryForType;',
    filterContext
);

function filterCheck(name, actual, expected) {
    if (actual !== expected) {
        throw new Error(
            name + '=FAIL actual=' + JSON.stringify(actual) +
            ' expected=' + JSON.stringify(expected)
        );
    }

    console.log(name + '=PASS');
}

const filterFixture = [
    {id: 1, service_type: 'DNS', status: 'available', archived: 0, ip: '192.0.2.1'},
    {id: 2, service_type: 'DNS', status: 'unavailable', archived: 0, ip: '192.0.2.2'},
    {id: 3, service_type: 'VPN', status: 'available', archived: 0, ip: '192.0.2.3'},
    {id: 4, service_type: 'SSH', status: 'unknown', archived: 0, ip: '192.0.2.4'},
    {id: 5, service_type: 'SMB', status: 'available', archived: 0, ip: '192.0.2.5'},
    {id: 6, service_type: 'NFS', status: 'available', archived: 0, ip: '192.0.2.6'},
    {id: 7, service_type: 'RDP', status: 'available', archived: 0, ip: '192.0.2.7'},
    {id: 8, service_type: 'DNS', status: 'available', archived: 1, ip: '192.0.2.8'}
];
const baseFilters = {
    type: '',
    status: '',
    search: '',
    includeArchived: false
};
function filteredIds(overrides) {
    return filterContext.filterServices(
        filterFixture,
        Object.assign({}, baseFilters, overrides)
    ).map(function(row) { return row.id; }).join(',');
}

filterCheck('FILTER_ALL_ACTIVE', filteredIds({}), '1,2,3,4,5,6,7');
filterCheck('FILTER_DNS', filteredIds({type: 'DNS'}), '1,2');
filterCheck('FILTER_DNS_ARCHIVED', filteredIds({type: 'DNS', includeArchived: true}), '1,2,8');
filterCheck('FILTER_STATUS_AVAILABLE', filteredIds({status: 'available'}), '1,3,5,6,7');
filterCheck('FILTER_SEARCH_SSH', filteredIds({search: 'ssh'}), '4');
filterCheck(
    'FILTER_CLEAR_TYPE_PRESERVES_STATUS',
    filteredIds({type: '', status: 'available'}),
    '1,3,5,6,7'
);
filterCheck('FILTER_EXACT_SMB', filteredIds({type: 'SMB'}), '5');
filterCheck('FILTER_EXACT_NFS', filteredIds({type: 'NFS'}), '6');
filterCheck('FILTER_EXACT_RDP', filteredIds({type: 'RDP'}), '7');
filterCheck('TYPE_LABEL_SMB', filterContext.serviceTypeLabel('SMB'), 'SMB');
filterCheck('TYPE_LABEL_NFS', filterContext.serviceTypeLabel('NFS'), 'NFS');
filterCheck('TYPE_LABEL_RDP', filterContext.serviceTypeLabel('RDP'), 'RDP');

const duplicateGroups = filterContext.groupServicesByCategory(
    filterFixture.filter(function(row) {
        return row.service_type === 'SMB' || row.service_type === 'NFS';
    })
);
filterCheck(
    'DUPLICATE_GROUP_TITLE_DISTINCT_TYPES',
    duplicateGroups['File / NAS Services'].map(function(row) {
        return row.service_type;
    }).join(','),
    'SMB,NFS'
);

filterCheck(
    'TYPE_SELECTS_EMPTY_CATEGORY',
    filterContext.resolveInventoryCategory(
        'DNS',
        'Recent Service Changes',
        {},
        ['DNS Servers', 'File / NAS Services']
    ),
    'DNS Servers'
);
filterCheck(
    'STATUS_RETAINS_ACTIVE_CATEGORY',
    filterContext.resolveInventoryCategory(
        '',
        'DNS Servers',
        {'DNS Servers': [{id: 1}]},
        ['DNS Servers', 'File / NAS Services']
    ),
    'DNS Servers'
);
filterCheck(
    'STATUS_CHOOSES_MATCHING_CATEGORY',
    filterContext.resolveInventoryCategory(
        '',
        'DNS Servers',
        {'VPN Endpoints': [{id: 3}]},
        ['DNS Servers', 'VPN Endpoints']
    ),
    'VPN Endpoints'
);
filterCheck(
    'NO_MATCH_RETAINS_STABLE_CATEGORY',
    filterContext.resolveInventoryCategory(
        '',
        'DNS Servers',
        {},
        ['DNS Servers', 'VPN Endpoints']
    ),
    'DNS Servers'
);
filterCheck(
    'NO_CATEGORY_USES_STABLE_FALLBACK',
    filterContext.resolveInventoryCategory('', '', {}, []),
    'Service Inventory'
);

const applyCalls = [];
const applyContext = {
    servicePaneIds: {'DNS Servers': 'tab-services-dns-servers'},
    activeInventoryCategory: function() {
        applyCalls.push('active');
        return '';
    },
    renderTabs: function() {
        applyCalls.push('tabs');
    },
    renderServices: function() {
        applyCalls.push('render');
        return [{id: 1}];
    },
    selectedServiceType: function() {
        return 'DNS';
    },
    groupServicesByCategory: function() {
        applyCalls.push('group');
        return {'DNS Servers': [{id: 1}]};
    },
    resolveInventoryCategory: function() {
        applyCalls.push('resolve');
        return 'DNS Servers';
    },
    activateInventoryCategory: function(name) {
        applyCalls.push('activate:' + name);
    }
};
vm.runInNewContext(
    text.slice(applyStart, applyEnd) +
    '\nthis.applyInventoryFilters = applyInventoryFilters;',
    applyContext
);
filterCheck(
    'APPLY_TYPE_REFRESHES_TABS_AND_RENDERS',
    applyContext.applyInventoryFilters(true),
    'DNS Servers'
);
filterCheck(
    'APPLY_TYPE_CALL_ORDER',
    applyCalls.join(','),
    'active,tabs,render,group,resolve,activate:DNS Servers'
);

applyCalls.length = 0;
applyContext.applyInventoryFilters(false);
filterCheck(
    'APPLY_STATUS_SEARCH_RETAINS_TAB_SET',
    applyCalls.join(','),
    'active,render,group,resolve,activate:DNS Servers'
);

const handlerStart = text.indexOf("    $('#services-type-filter').on('change'");
const handlerEnd = text.indexOf(
    '    var portDiscoveryDevices = {};',
    handlerStart
);
const handlerBlock = text.slice(handlerStart, handlerEnd);
if (
    handlerStart < 0 ||
    handlerEnd < 0 ||
    !handlerBlock.includes('applyInventoryFilters(true);') ||
    !handlerBlock.includes('applyInventoryFilters(false);') ||
    (handlerBlock.match(/applyInventoryFilters\(/g) || []).length !== 4 ||
    handlerBlock.includes('renderRecentServiceChanges(')
) {
    throw new Error('Inventory filter handlers are not wired to inventory navigation');
}
console.log('INFRASTRUCTURE_FILTER_SCOPE=PASS');
