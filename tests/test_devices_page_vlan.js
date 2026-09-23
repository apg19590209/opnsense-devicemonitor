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
check(!view.includes('id="vlan-clear"'), 'standalone VLAN Clear button must be removed');
check(
    view.includes("{{ lang._('Apply VLAN Filter') }}"),
    'Apply button must be localised as "Apply VLAN Filter"'
);
check(
    !view.includes("{{ lang._('Apply') }}"),
    'generic "Apply" must not be reused for the VLAN apply button'
);
check(
    view.includes("{{ lang._('Not applied') }}"),
    'pending "Not applied" indicator must be localised'
);
check(
    view.includes('id="vlan-not-applied"'),
    'pending "Not applied" indicator element missing'
);

check(
    view.includes("$('#vlan-apply').on('click', function(){ commitVlans(); });"),
    'Apply button must commit the pending VLAN selection'
);
check(
    !view.includes("$('#vlan-clear').on('click'"),
    'VLAN Clear handler must be removed'
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
    view.includes('resolveVlanDraft(readCheckedVlans(), allVlans)'),
    'Apply must resolve the checked VLANs through the draft helper'
);
check(
    view.includes('activeVlans = draft.filter'),
    'Apply must commit the resolved draft filter'
);

check(
    !view.includes("$('#vlan-clear').on('click'"),
    'no standalone VLAN Clear handler may remain'
);
check(
    view.includes('activeVlans = []'),
    'activeVlans must still be initialised to the unfiltered all-VLAN state'
);

// ---------------------------------------------------------------------------
// Selected VLAN state retained during table rendering
// ---------------------------------------------------------------------------

check(
    view.includes('effectiveCheckedVlans(pendingVlans, activeVlans, vlans)'),
    'Dropdown rebuild must preserve the pending selection via effectiveCheckedVlans'
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
// Natural DOM order plus a stable sticky summary/toolbar/headings region
// ---------------------------------------------------------------------------

// Document order must be tabs -> summary -> toolbar -> table (thead -> tbody).
const tabsIdx = view.indexOf('nav-tabs');
const summaryIdx = view.indexOf('id="devices-sticky-summary"');
const toolbarIdx = view.indexOf('id="devices-sticky-toolbar"');
const tableIdx = view.indexOf('id="grid-devices"');
const theadIdx = view.indexOf('<thead>');
const tbodyIdx = view.indexOf('<tbody>');

check(
    tabsIdx !== -1 && summaryIdx !== -1 && toolbarIdx !== -1 && tableIdx !== -1,
    'tabs/summary/toolbar/table must all be present'
);
check(tabsIdx < summaryIdx, 'tabs must precede the summary');
check(summaryIdx < toolbarIdx, 'summary must precede the toolbar');
check(toolbarIdx < tableIdx, 'toolbar must precede the table');
check(
    theadIdx !== -1 && tbodyIdx !== -1 && theadIdx < tbodyIdx,
    'thead must precede tbody'
);

// The complete persistent header (page title + tabs + explanatory text +
// counters + toolbar) and the column headings must stick beneath the fixed
// navigation. Offsets are recalculated from live measurements (load, resize,
// genuine toolbar-height change) via CSS custom properties, while the fragile
// scroll-snap, pseudo-element shield and cached one-shot geometry designs
// remain absent.
check(
    view.includes('id="devices-sticky-header"'),
    'sticky summary/toolbar wrapper missing'
);
check(
    view.includes('#devices-sticky-header {') && view.includes('position: sticky'),
    'sticky wrapper must use position: sticky'
);
check(
    view.includes('#grid-devices thead th {') && view.includes('position: sticky'),
    'sticky column headings must use position: sticky'
);
check(
    view.includes('top: var(--devices-sticky-thead-top)') &&
        !view.includes('calc(var(--devices-sticky-thead-top) - 1px)'),
    'sticky column headings must stick flush beneath the toolbar (no -1px overlap)'
);
check(
    view.includes('--devices-sticky-top') &&
        view.includes('--devices-sticky-thead-top'),
    'sticky offsets must use CSS custom properties'
);
check(
    view.includes('function syncDevicesStickyHeader'),
    'sticky offset recalculation helper missing'
);
check(
    view.includes('ResizeObserver'),
    'sticky offsets must recalculate on genuine toolbar-height change'
);
check(
    view.includes('border-collapse: separate') &&
        view.includes('border-spacing: 0'),
    'sticky heading band must use the separated border model so rows cannot bleed through'
);
check(
    view.includes('#grid-devices > tbody > tr:first-child > td') &&
        view.includes('border-top: 0'),
    'first body row border must be suppressed to keep a single heading separator'
);
check(
    view.includes("$thead.css('background-color', theadBg)") &&
        view.includes("$('#grid-devices thead').css('background-color', theadBg)"),
    'sticky heading cells and thead must receive an opaque background'
);
check(
    view.includes('header.page-content-head {') && view.includes('position: sticky'),
    'OPNsense page title must join the persistent header'
);
check(
    view.includes('--devices-title-top') &&
        view.includes('--devices-sticky-top') &&
        view.includes('--devices-sticky-thead-top'),
    'three sticky offsets must be expressed as CSS custom properties'
);
check(
    !view.includes('table-layout: fixed') && !view.includes('<colgroup>'),
    'defective fixed-percentage table layout must be removed'
);
check(
    view.includes('devices-col-secondary') &&
        view.includes('display: none') &&
        view.includes('devices-hide-1') &&
        view.includes('devices-col-sec-1') &&
        view.includes('devices-col-sec-5'),
    'progressive responsive column hiding must exist'
);
check(
    !view.includes('max-width: 1199px'),
    'viewport-based responsive breakpoint must be removed'
);
check(
    view.includes('function syncResponsiveColumns'),
    'responsive column sync helper missing'
);
check(
    view.includes("new ResizeObserver(syncResponsiveColumns)"),
    'responsive columns must observe the table width'
);
check(
    !view.includes('margin:10px 0 0 0') &&
        view.includes('.page-content-main') &&
        view.includes('padding-top: 0'),
    'redundant title-to-tabs gap must be removed'
);
check(
    !view.includes('<h1'),
    'view must not duplicate the OPNsense page title'
);
check(
    view.indexOf('id="devices-sticky-header"') < view.indexOf('nav nav-tabs') &&
        view.indexOf('nav nav-tabs') < view.indexOf('id="devices-sticky-summary"'),
    'tabs must sit inside the persistent header wrapper before the counters'
);
check(!view.includes('scroll-snap-align'), 'no scroll-snap-align may remain');
check(!view.includes('scroll-snap-type'), 'no scroll-snap-type may remain');
check(!view.includes('scroll-padding-top'), 'no scroll-padding-top may remain');
check(!view.includes('devicesStickyGeometry'), 'cached one-shot sticky geometry must be absent');
check(!view.includes('updateStickyOffsets'), 'fragile updateStickyOffsets must remain absent');
check(
    view.includes('getBoundingClientRect().height'),
    'sticky offsets must use fractional getBoundingClientRect().height'
);
check(!view.includes('.offsetHeight'), 'sticky offsets must not use integer .offsetHeight');
check(!view.includes('::before'), 'sticky shield pseudo-elements must remain absent');

// ---------------------------------------------------------------------------
// VLAN count-state: button reflects pending checkbox selection
// ---------------------------------------------------------------------------

check(
    view.includes("$('#vlan-checklist .vlan-cb:checked').length"),
    'VLAN label must read the pending checked count'
);
check(
    view.includes('checked === total'),
    'all-checked selection must display the All VLANs label'
);
check(
    view.includes('checked === 0') && view.includes('translations.select_vlan'),
    'zero-checked selection must display the Select a VLAN label'
);
check(view.includes("'1 VLAN'"), 'One selected checkbox must display "1 VLAN"');
check(
    view.includes("checked + ' VLANs'"),
    'Multiple selected checkboxes must display the checked count'
);
// updateVlanLabel is called from build + both checkbox change handlers +
// commitVlans (4 call sites), so checkbox changes update the label
// immediately without filtering.
const labelCallSites = view.split('updateVlanLabel();').length - 1;
check(
    labelCallSites === 4,
    'updateVlanLabel must be called from build + change handlers + apply, got ' +
        labelCallSites
);

// ---------------------------------------------------------------------------
// Apply button reflects pending-vs-applied state
// ---------------------------------------------------------------------------

check(
    view.includes('function syncVlanApplyButton'),
    'VLAN apply button sync helper missing'
);
check(
    view.includes("$btn.prop('disabled', same)"),
    'Apply button must be disabled while pending equals applied'
);
check(
    view.includes("$btn.removeClass('btn-primary').addClass('btn-default')") &&
        view.includes("$btn.removeClass('btn-default').addClass('btn-primary')"),
    'Apply button must switch between muted and OPNsense orange styles'
);
check(
    view.includes("$('#vlan-not-applied').toggle(!same)"),
    'Not applied indicator must track the pending/applied state'
);

// ---------------------------------------------------------------------------
// Empty VLAN selection is an incomplete draft, not the all-VLAN view
// ---------------------------------------------------------------------------

check(
    view.includes('function resolveVlanDraft'),
    'resolveVlanDraft draft-resolution helper missing'
);
check(
    view.includes("$('#vlan-filter-label').text(translations.select_vlan)"),
    'empty selection must set the dropdown label to "Select a VLAN"'
);
check(
    view.includes("$btn.prop('disabled', true)") &&
        view.includes("$('#vlan-not-applied').hide()"),
    'empty draft must disable Apply and hide the pending hint'
);

// ---------------------------------------------------------------------------
// Pending VLAN selection survives a dropdown rebuild / data refresh
// ---------------------------------------------------------------------------

check(
    view.includes('var pendingVlans = null'),
    'pending VLAN selection must be tracked in a variable'
);
check(
    view.includes('pendingVlans = readCheckedVlans()'),
    'checkbox changes must capture the pending VLAN selection'
);
check(
    view.includes('pendingVlans = null;'),
    'commit must clear the pending selection after applying'
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
check(
    typeof sandbox.resolveVlanDraft === 'function',
    'resolveVlanDraft helper is not exposed'
);
check(
    typeof sandbox.effectiveCheckedVlans === 'function',
    'effectiveCheckedVlans helper is not exposed'
);
check(
    typeof sandbox.computeStickyOffsets === 'function',
    'computeStickyOffsets helper is not exposed'
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

// resolveVlanDraft distinguishes an empty draft from the all-VLAN choice.
assertSame(
    sandbox.resolveVlanDraft([], ['VLAN10', 'VLAN50', 'VLAN99']),
    { valid: false, filter: [] },
    'zero checked VLANs is an incomplete draft'
);
assertSame(
    sandbox.resolveVlanDraft(['VLAN50'], ['VLAN10', 'VLAN50', 'VLAN99']),
    { valid: true, filter: ['VLAN50'] },
    'one checked VLAN is a valid draft filter'
);
assertSame(
    sandbox.resolveVlanDraft(
        ['VLAN10', 'VLAN50', 'VLAN99'],
        ['VLAN10', 'VLAN50', 'VLAN99']
    ),
    { valid: true, filter: [] },
    'all checked VLANs is the unfiltered all-VLAN draft'
);

// effectiveCheckedVlans preserves a pending selection across a rebuild.
assertSame(
    sandbox.effectiveCheckedVlans(['RE0'], [], ['RE0', 'VLAN50', 'VTNET0', 'VTNET1']),
    ['RE0'],
    'pending subset survives a dropdown rebuild'
);
assertSame(
    sandbox.effectiveCheckedVlans(null, [], ['RE0', 'VLAN50']),
    ['RE0', 'VLAN50'],
    'no pending + applied all shows every VLAN'
);
assertSame(
    sandbox.effectiveCheckedVlans(null, ['RE0'], ['RE0', 'VLAN50']),
    ['RE0'],
    'no pending + applied subset shows the applied subset'
);
assertSame(
    sandbox.effectiveCheckedVlans([], ['RE0'], ['RE0', 'VLAN50']),
    [],
    'pending empty draft survives a dropdown rebuild'
);

// computeStickyOffsets preserves fractional heights so the heading band stays
// flush with the sticky header bottom.
assertSame(
    sandbox.computeStickyOffsets(62.5, 48.25, 177.75),
    { titleTop: 62.5, stickyTop: 110.75, theadTop: 288.5 },
    'fractional heights produce a fractional sticky heading top'
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
console.log('DEVICES_VLAN_LAYOUT_ORDER=PASS');
console.log('DEVICES_VLAN_STICKY_REGION=PASS');
console.log('DEVICES_VLAN_COUNT_STATE=PASS');
console.log('DEVICES_VLAN_APPLY_BUTTON=PASS');
console.log('DEVICES_VLAN_SELECTION_HELPER=PASS');
console.log('DEVICES_VLAN_SUMMARY_COUNTERS=PASS');
console.log('DEVICES_VLAN_EMPTY_DRAFT=PASS');
console.log('DEVICES_VLAN_SEAM_FLUSH=PASS');
console.log('DEVICES_VLAN_PENDING_REBUILD=PASS');
console.log('DEVICES_VLAN_FRACTIONAL_STICKY=PASS');
console.log('DEVICES_VLAN_JAVASCRIPT=PASS');
