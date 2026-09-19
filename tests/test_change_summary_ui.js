const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');

const view = fs.readFileSync(
    path.join(
        root,
        'src',
        'opnsense',
        'mvc',
        'app',
        'views',
        'OPNsense',
        'DeviceMonitor',
        'changesummary.volt'
    ),
    'utf8'
);

const controller = fs.readFileSync(
    path.join(
        root,
        'src',
        'opnsense',
        'mvc',
        'app',
        'controllers',
        'OPNsense',
        'DeviceMonitor',
        'IndexController.php'
    ),
    'utf8'
);

const menu = fs.readFileSync(
    path.join(
        root,
        'src',
        'opnsense',
        'mvc',
        'app',
        'models',
        'OPNsense',
        'DeviceMonitor',
        'Menu',
        'Menu.xml'
    ),
    'utf8'
);

function check(condition, message) {
    if (!condition) {
        console.error('FAIL: ' + message);
        process.exit(1);
    }
}

/* Route / view markers. */
check(
    controller.includes('public function changesummaryAction()'),
    'IndexController changesummaryAction missing'
);

check(
    controller.includes(
        "$this->view->pick('OPNsense/DeviceMonitor/changesummary')"
    ),
    'IndexController changesummary view pick missing'
);

check(
    menu.includes('/ui/devicemonitor/index/changesummary'),
    'Menu.xml Change Summary entry missing'
);

/* Time-window selectpicker. */
check(
    view.includes('id="change-summary-window"'),
    'Change Summary window select missing'
);

check(
    view.includes('class="selectpicker"') &&
    view.includes('data-style="btn-default btn-sm"'),
    'Change Summary controls are not selectpicker btn-sm'
);

[
    'value="since_last_review"',
    'value="24h"',
    'value="7d"',
    'value="30d"',
    'value="custom"'
].forEach(function(value) {
    check(
        view.includes(value),
        'Change Summary window option missing: ' + value
    );
});

/* Category selectpicker. */
check(
    view.includes('id="change-summary-category"'),
    'Change Summary category select missing'
);

[
    'value="all"',
    'value="device"',
    'value="lifecycle"',
    'value="identity"',
    'value="physical_device"',
    'value="user_history"',
    'value="infrastructure"'
].forEach(function(value) {
    check(
        view.includes(value),
        'Change Summary category option missing: ' + value
    );
});

/* Custom range controls. */
check(
    view.includes('id="change-summary-custom-range"') &&
    view.includes('id="change-summary-start"') &&
    view.includes('id="change-summary-end"'),
    'Change Summary custom-range controls missing'
);

/* Mark reviewed button and browser-local behaviour. */
check(
    view.includes('id="btn-mark-reviewed"'),
    'Mark reviewed button missing'
);

check(
    view.includes('devicemonitor.changeSummary.lastReviewed'),
    'lastReviewed localStorage key missing'
);

check(
    view.includes(
        'localStorage.setItem(LS_KEY, new Date().toISOString())'
    ),
    'Mark-reviewed does not write the browser-local marker'
);

/* API endpoint usage. */
check(
    view.includes("url: '/api/devicemonitor/devices/changesummary'"),
    'Change Summary API endpoint usage missing'
);

/* Summary counters. */
check(
    view.includes('id="change-summary-counters"') &&
    view.includes('id="change-summary-count-total"') &&
    view.includes('id="change-summary-count-new_devices"') &&
    view.includes('id="change-summary-count-returned_devices"') &&
    view.includes('id="change-summary-count-identity"') &&
    view.includes('id="change-summary-count-infrastructure"') &&
    view.includes('id="change-summary-count-lifecycle"'),
    'Change Summary counters missing'
);

/* Event table and empty state. */
check(
    view.includes('id="grid-change-summary"'),
    'Change Summary event table missing'
);

/* Row-number column and numbering semantics. */
check(
    view.includes('class="change-summary-row-number"') &&
    view.includes('>#</th>'),
    'Change Summary row-number (#) column missing'
);

check(
    view.includes('.text(total - offset - rowIndex)'),
    'Change Summary row-number formula missing (must be total - offset - rowIndex)'
);

check(
    view.includes(
        'renderTable(result.events || [], result.total || 0, result.offset || 0)'
    ),
    'Change Summary renderTable does not receive total/offset for numbering'
);

check(
    view.includes('events.forEach(function(event, rowIndex)'),
    'Change Summary row renderer does not expose the current row index'
);

/* Numbering: newest displayed row is the total count, the oldest event in the
   filtered result set is #1, and pagination preserves that numbering. */
function changeSummaryRowNumber(total, offset, rowIndex) {
    return total - offset - rowIndex;
}

check(
    changeSummaryRowNumber(72, 0, 0) === 72 &&
    changeSummaryRowNumber(72, 0, 49) === 23,
    'Newest-first numbering is wrong for the first page'
);

check(
    changeSummaryRowNumber(72, 50, 0) === 22 &&
    changeSummaryRowNumber(72, 50, 21) === 1,
    'Pagination-aware numbering is wrong: oldest event must be #1'
);

/* Browser-local time display: the authoritative UTC value is rendered through
   native browser Date/Intl formatting in the user's local timezone. No
   timezone or abbreviation (UTC/AEST/AEDT) is hardcoded. */
check(
    view.includes('formatBrowserLocalTime(event.occurred_at_utc)'),
    'Change Summary does not render the authoritative occurred_at_utc value'
);

check(
    view.includes('new Date(') &&
    view.includes('Intl.DateTimeFormat'),
    'Change Summary does not use native browser Date/Intl formatting'
);

check(
    !view.includes('dash(event.occurred_at)'),
    'Change Summary still renders the server-local occurred_at field'
);

check(
    !view.includes('AEST') &&
    !view.includes('AEDT') &&
    !view.includes('Etc/UTC') &&
    !view.includes('Australia/Sydney'),
    'Change Summary hardcodes a timezone or abbreviation'
);

check(
    !view.includes("' UTC'") && !view.includes('" UTC"'),
    'Change Summary still hardcodes a UTC suffix in rendered row output'
);

/* Full sticky-stack mechanism: one unified opaque sticky controls wrapper
   (panel title + toolbar + custom-range + fallback notice + summary counters)
   with the table thead sticky immediately beneath it. The wrapping
   .table-responsive overflow must be overridden (it would otherwise create a
   scroll container that stops position:sticky from sticking to page scroll). */
check(
    view.includes('.table-responsive.change-summary-table-wrap') &&
    view.includes('overflow: visible'),
    'Change Summary table wrapper does not override .table-responsive overflow'
);

check(
    view.includes('id="change-summary-sticky-controls"'),
    'Change Summary unified sticky controls wrapper missing'
);

[
    'id="change-summary-title"',
    'id="change-summary-toolbar"',
    'id="change-summary-custom-range"',
    'id="change-summary-fallback"',
    'id="change-summary-counters"',
    'id="grid-change-summary"'
].forEach(function(marker) {
    check(
        view.includes(marker),
        'Change Summary layer missing: ' + marker
    );
});

check(
    view.includes('.change-summary-sticky-controls') &&
    view.includes('position: sticky'),
    'Change Summary unified wrapper is not sticky'
);

check(
    view.includes('#grid-change-summary thead th') &&
    view.includes('position: sticky'),
    'Change Summary sticky thead th CSS missing'
);

check(
    view.includes('function updateChangeSummaryStickyStack()'),
    'Change Summary updateChangeSummaryStickyStack() missing'
);

check(
    view.includes("$('header.page-content-head')"),
    'Change Summary stack does not reference header.page-content-head'
);

/* Geometry preservation: the page title bar's own rendered document top is
   measured once via getBoundingClientRect() and used as the baseline (rather
   than assuming it equals the fixed menu height), and the initial visual gap
   between page-content-head and the controls block is measured and preserved.
   Rendered (offsetHeight) heights replace margin-inclusive outerHeight(true)
   so no vertical jump occurs on sticky engage. */
check(
    view.includes('getBoundingClientRect()'),
    'Change Summary stack does not use getBoundingClientRect() for rendered geometry'
);

check(
    view.includes('pageHeadTop'),
    'Change Summary stack does not store the measured page-title-bar top'
);

check(
    view.includes('pageHeadRect.top + scrollTop'),
    'Change Summary stack does not measure the page-title-bar document top'
);

check(
    view.includes('controlsRect.top - pageHeadRect.bottom'),
    'Change Summary stack does not measure the initial visual gap'
);

check(
    view.includes('.offsetHeight'),
    'Change Summary stack does not use rendered offsetHeight'
);

check(
    !view.includes('outerHeight(true)'),
    'Change Summary stack still uses margin-inclusive outerHeight(true)'
);

check(
    view.includes("$(window).on('resize', updateChangeSummaryStickyStack)"),
    'Change Summary stack does not recalculate on window resize'
);

check(
    view.includes('updateChangeSummaryStickyStack();'),
    'Change Summary stack is not invoked to recalculate on layout changes'
);

check(
    view.includes('opaqueBackground'),
    'Change Summary stack opaque-background helper missing'
);

/* Opaque gap cover between header.page-content-head and the sticky controls
   block: the measured initial gap is re-exposed as a CSS custom property and a
   page-scoped ::before pseudo-element extends upward by exactly that gap. The
   cover must be opaque (inheriting the controls block background),
   non-layout-changing (absolutely positioned), and click-transparent. */
check(
    view.includes('--change-summary-sticky-gap'),
    'Change Summary gap cover does not expose --change-summary-sticky-gap'
);

check(
    view.includes('.change-summary-sticky-controls::before'),
    'Change Summary gap cover ::before pseudo-element missing'
);

check(
    view.includes('bottom: 100%'),
    'Change Summary gap cover does not extend upward from the controls block'
);

check(
    view.includes('var(--change-summary-sticky-gap'),
    'Change Summary gap cover does not size itself with the measured gap'
);

check(
    view.includes('background: inherit'),
    'Change Summary gap cover does not inherit the opaque controls background'
);

check(
    view.includes('pointer-events: none'),
    'Change Summary gap cover is not click-transparent'
);

check(
    view.includes('position: absolute'),
    'Change Summary gap cover is not absolutely positioned (would affect layout)'
);

/* Existing sticky geometry and offsets must remain untouched. */
check(
    view.includes("$controls.css('top', controlsTop + 'px')"),
    'Change Summary controls sticky top assignment changed'
);

check(
    view.includes("pageHead.css('top', pageHeadTop + 'px')"),
    'Change Summary page-title-bar sticky top assignment changed'
);

check(
    view.includes("thead.css('top', tableHeaderTop + 'px')"),
    'Change Summary table-header sticky top assignment changed'
);

/* header.page-content-head keeps its opaque background while sticky. */
check(
    view.includes("pageHead.css('background-color', opaqueBackground(pageHead))"),
    'Change Summary page-title-bar opaque sticky background missing'
);

/* No obsolete per-layer sticky mechanism remains. */
check(
    !view.includes('updateChangeSummaryStickyHeader') &&
    !view.includes("{ $el: $('#change-summary-title')"),
    'Change Summary obsolete per-layer sticky mechanism remains'
);

check(
    view.includes("'No meaningful Device Monitor changes were '") &&
    view.includes("'recorded in this period.'"),
    'Change Summary empty-state message missing'
);

/* Pagination. */
check(
    view.includes('id="btn-change-summary-prev"') &&
    view.includes('id="btn-change-summary-next"') &&
    view.includes('id="change-summary-pagination"'),
    'Change Summary pagination controls missing'
);

/* btn-xs row actions. */
check(
    view.includes("addClass('btn btn-default btn-xs')"),
    'Change Summary row actions are not btn-xs'
);

/* Mark-reviewed fallback message. */
check(
    view.includes('No previous review marker'),
    'Since-last-review fallback message missing'
);

/* JavaScript syntax check. */
const scripts = view.match(/<script>([\s\S]*?)<\/script>/g);

check(
    scripts && scripts.length > 0,
    'Change Summary JavaScript block missing'
);

scripts.forEach(function(block) {
    const javascript = block
        .replace(/^<script>/, '')
        .replace(/<\/script>$/, '')
        .replace(/\{\{[\s\S]*?\}\}/g, 'VOLT');

    try {
        new Function(javascript);
    } catch (error) {
        console.error(
            'FAIL: Change Summary JavaScript syntax: ' + error.message
        );
        process.exit(1);
    }
});

console.log('DEVICE_CHANGE_SUMMARY_UI_STRUCTURE=PASS');
console.log('DEVICE_CHANGE_SUMMARY_UI_JAVASCRIPT=PASS');
