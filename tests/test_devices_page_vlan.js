const fs = require('fs');
const vm = require('vm');

const devicesPath =
    'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devices.volt';

const view = fs.readFileSync(devicesPath, 'utf8');

function check(condition, message) {
    if (!condition) {
        console.error('FAIL: ' + message);
        process.exit(1);
    }
}

// ---------------------------------------------------------------------------
// Checkbox-style VLAN multi-select
// ---------------------------------------------------------------------------

// The VLAN checklist must use native checkboxes wrapped in <label> elements so
// a single click reliably toggles one VLAN (no <a href="#"> navigation).
check(
    view.includes('class="vlan-cb"'),
    'VLAN selector must build native checkbox inputs'
);
check(
    view.includes('id="vlan-all"'),
    'VLAN selector must keep the All VLANs checkbox'
);
check(
    view.includes("$('<label>')"),
    'VLAN checkbox items must be wrapped in <label> elements'
);
check(
    !view.includes("attr('href','#')"),
    'VLAN checkbox items must not be wrapped in <a href="#"> anchors'
);
check(
    !view.includes('vlan-select-none'),
    'VLAN selector must no longer use the confusing Select none link'
);

// The dropdown must stay open while several VLANs are toggled.
check(
    view.includes("$('#vlan-checklist').on('click', function(e){ e.stopPropagation(); });"),
    'VLAN dropdown must keep itself open on checkbox clicks'
);

// ---------------------------------------------------------------------------
// Explicit Apply / Clear controls
// ---------------------------------------------------------------------------

check(view.includes('id="vlan-apply"'), 'VLAN Apply button missing');
check(view.includes('id="vlan-clear"'), 'VLAN Clear button missing');
check(view.includes("{{ lang._('Apply') }}"), 'Apply button must be localised');
check(view.includes("{{ lang._('Clear') }}"), 'Clear button must be localised');

check(
    view.includes("$('#vlan-apply').on('click', function(){ commitVlans(); });"),
    'Apply button must commit the pending VLAN selection'
);
check(
    view.includes("$('#vlan-clear').on('click', function(){"),
    'Clear button handler missing'
);

// ---------------------------------------------------------------------------
// One filter/render operation on Apply (never per checkbox click)
// ---------------------------------------------------------------------------

check(!view.includes('persistVlans'), 'per-checkbox auto-apply helper must be removed');

const renderTableCalls = (view.match(/renderTable\(/g) || []).length;
check(
    renderTableCalls === 2,
    'renderTable must be defined once and called exactly once (from applyFilters), got ' +
        renderTableCalls
);
check(
    (view.match(/renderTable\(filtered\)/g) || []).length === 1,
    'renderTable must only be invoked from applyFilters with the filtered rows'
);

check(view.includes('function commitVlans()'), 'commitVlans helper missing');
check(
    view.includes('activeVlans = finalizeVlanSelection(readCheckedVlans(), allVlans);'),
    'Apply must finalise the checked VLANs into activeVlans'
);

check(
    view.includes("$('#vlan-clear').on('click', function(){") &&
        view.includes('activeVlans = [];'),
    'Clear must reset activeVlans to the unfiltered all-VLAN view'
);

// ---------------------------------------------------------------------------
// Selected VLAN state retained during table rendering
// ---------------------------------------------------------------------------

check(
    view.includes('activeVlans.indexOf(v) !== -1'),
    'Dropdown rebuild must retain the committed VLAN selection'
);
check(
    view.includes("localStorage.getItem('dm_vlan_filter')"),
    'VLAN selection must be restored from localStorage'
);

// ---------------------------------------------------------------------------
// No deliberate page movement during filtering
// ---------------------------------------------------------------------------

check(
    !view.includes('scrollIntoView'),
    'Filtering must never call scrollIntoView()'
);

const focusCalls = (view.match(/\.focus\(\)/g) || []).length;
check(
    focusCalls === 1,
    'Filtering must not focus any element (only the friendly-name editor may focus), got ' +
        focusCalls
);

check(
    view.includes('function captureScrollPosition()'),
    'captureScrollPosition helper missing'
);
check(
    view.includes('function restoreScrollPosition(pos)'),
    'restoreScrollPosition helper missing'
);
check(
    view.includes('window.scrollTo(pos.x, pos.y)'),
    'restoreScrollPosition must restore both axes with window.scrollTo'
);

// ---------------------------------------------------------------------------
// Sticky header / tab stacking and offsets
// ---------------------------------------------------------------------------

check(
    view.includes('var devicesStickyGeometry = null;'),
    'Sticky geometry cache missing'
);
check(
    view.includes('getBoundingClientRect'),
    'Sticky offsets must be derived from measured geometry'
);
check(
    view.includes('gap: summaryRect.top - pageHeadRect.bottom'),
    'Sticky stack must measure the natural gap to the summary (below the tabs)'
);
check(
    view.includes('top = devicesStickyGeometry.pageHeadTop + pageHeadHeight + devicesStickyGeometry.gap;'),
    'Sticky summary must be confined below the page title bar and tabs'
);
check(
    view.includes('#devices-sticky-summary') && view.includes('position: sticky'),
    'Summary must remain position: sticky'
);
check(
    view.includes('#devices-sticky-toolbar') && view.includes('position: sticky'),
    'Toolbar must remain position: sticky'
);
check(
    view.includes('#grid-devices thead th') && view.includes('position: sticky'),
    'Table header cells must remain position: sticky'
);

// ---------------------------------------------------------------------------
// Pure helper behaviour (no DOM required)
// ---------------------------------------------------------------------------

const scripts = view.match(/<script>([\s\S]*?)<\/script>/g);

check(scripts && scripts.length > 0, 'Devices page JavaScript block missing');

const javascript = scripts
    .map(function (block) {
        return block
            .replace(/^<script>/, '')
            .replace(/<\/script>$/, '')
            .replace(/\{\{[\s\S]*?\}\}/g, 'VOLT');
    })
    .join('\n');

try {
    new Function(javascript);
} catch (error) {
    console.error('FAIL: Devices page JavaScript syntax: ' + error.message);
    process.exit(1);
}

const sandbox = {
    $: function () {
        return { ready: function () {} };
    },
    document: {}
};
vm.runInNewContext(javascript, sandbox);

check(
    typeof sandbox.finalizeVlanSelection === 'function',
    'finalizeVlanSelection helper is not exposed'
);

function assertSame(actual, expected, label) {
    const actualJson = JSON.stringify(actual);
    const expectedJson = JSON.stringify(expected);
    check(
        actualJson === expectedJson,
        label + ': got ' + actualJson + ' expected ' + expectedJson
    );
}

assertSame(
    sandbox.finalizeVlanSelection(['VLAN50'], ['VLAN10', 'VLAN50', 'VLAN99']),
    ['VLAN50'],
    'one VLAN selected'
);
assertSame(
    sandbox.finalizeVlanSelection(['VLAN50', 'VLAN10'], ['VLAN10', 'VLAN50', 'VLAN99']),
    ['VLAN10', 'VLAN50'],
    'multiple VLANs selected'
);
assertSame(
    sandbox.finalizeVlanSelection(
        ['VLAN10', 'VLAN50', 'VLAN99'],
        ['VLAN10', 'VLAN50', 'VLAN99']
    ),
    [],
    'all VLANs selected'
);
assertSame(
    sandbox.finalizeVlanSelection([], ['VLAN10', 'VLAN50', 'VLAN99']),
    [],
    'no VLANs selected'
);
assertSame(
    sandbox.finalizeVlanSelection(['VLAN50', 'VLAN50'], ['VLAN50', 'VLAN99']),
    ['VLAN50'],
    'duplicate VLAN selection'
);

const rows = [
    { mac: 'm1', ip: '192.168.50.180', vlan: 'VLAN50', status: 'online' },
    { mac: 'm2', ip: '192.168.50.1', vlan: 'VLAN50', status: 'online' },
    { mac: 'm3', ip: '192.168.50.1', vlan: 'VLAN50', status: 'offline' },
    { mac: 'm4', ip: '192.168.20.1', vlan: 'RE0', status: 'online' },
    { mac: 'm5', ip: '192.168.20.2', vlan: 'RE0', status: 'offline' }
];

const vlanOnly = sandbox.applyDeviceFilters(rows, ['VLAN50'], '');
check(vlanOnly.length === 3, 'VLAN-only filter must keep 3 rows');
check(
    sandbox.summarizeDevices(vlanOnly).total === 3 &&
        sandbox.summarizeDevices(vlanOnly).online === 2,
    'VLAN-only summary counters must match filtered rows'
);

console.log('DEVICES_VLAN_CHECKBOX_TOGGLE=PASS');
console.log('DEVICES_VLAN_APPLY_CLEAR=PASS');
console.log('DEVICES_VLAN_SINGLE_RENDER=PASS');
console.log('DEVICES_VLAN_CLEAR_RESTORES_ALL=PASS');
console.log('DEVICES_VLAN_STATE_RETAINED=PASS');
console.log('DEVICES_VLAN_NO_SCROLL_MOVEMENT=PASS');
console.log('DEVICES_VLAN_STICKY_OFFSETS=PASS');
console.log('DEVICES_VLAN_SELECTION_HELPER=PASS');
console.log('DEVICES_VLAN_SUMMARY_COUNTERS=PASS');
console.log('DEVICES_VLAN_JAVASCRIPT=PASS');
