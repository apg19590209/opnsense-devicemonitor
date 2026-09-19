<div class="content-box">
    <div class="content-box-main">

        <div id="change-summary-sticky-controls" class="change-summary-sticky-controls">
            <div id="change-summary-title"
                 class="change-summary-title"
                 style="padding:10px 10px 8px 10px;border-bottom:1px solid #333;margin-bottom:12px;">
            <h1 style="margin:0;font-size:20px;">
                {{ lang._('Device Monitor') }}
                <span style="color:#555;margin:0 8px;">&ndash;</span>
                <span style="font-weight:normal;">{{ lang._('Change Summary') }}</span>
            </h1>
        </div>

            <div class="panel panel-default change-summary-controls-panel">
            <div id="change-summary-toolbar" class="panel-heading change-summary-heading">
                <div class="change-summary-controls">
                    <label for="change-summary-window"
                           style="margin:0;font-size:12px;font-weight:600;">
                        {{ lang._('Period') }}
                    </label>

                    <select id="change-summary-window"
                            class="selectpicker"
                            data-style="btn-default btn-sm"
                            data-width="170px">
                        <option value="since_last_review">{{ lang._('Since last review') }}</option>
                        <option value="24h" selected>{{ lang._('Last 24 hours') }}</option>
                        <option value="7d">{{ lang._('Last 7 days') }}</option>
                        <option value="30d">{{ lang._('Last 30 days') }}</option>
                        <option value="custom">{{ lang._('Custom range') }}</option>
                    </select>

                    <label for="change-summary-category"
                           style="margin:0;font-size:12px;font-weight:600;margin-left:10px;">
                        {{ lang._('Category') }}
                    </label>

                    <select id="change-summary-category"
                            class="selectpicker"
                            data-style="btn-default btn-sm"
                            data-width="150px">
                        <option value="all" selected>{{ lang._('All categories') }}</option>
                        <option value="device">{{ lang._('Device') }}</option>
                        <option value="lifecycle">{{ lang._('Lifecycle') }}</option>
                        <option value="identity">{{ lang._('Identity') }}</option>
                        <option value="physical_device">{{ lang._('Physical Device') }}</option>
                        <option value="user_history">{{ lang._('Notes / History') }}</option>
                        <option value="infrastructure">{{ lang._('Infrastructure') }}</option>
                    </select>

                    <button id="btn-change-summary-refresh"
                            class="btn btn-default btn-sm"
                            title="{{ lang._('Refresh') }}">
                        <i class="fa fa-refresh"></i>
                    </button>

                    <button id="btn-mark-reviewed"
                            class="btn btn-default btn-sm"
                            title="{{ lang._('Mark reviewed now') }}">
                        <i class="fa fa-check"></i>
                        {{ lang._('Mark reviewed now') }}
                    </button>
                </div>
            </div>

            <div id="change-summary-custom-range"
                 class="change-summary-custom-range"
                 style="display:none;">
                <label for="change-summary-start"
                       style="margin:0;font-size:12px;font-weight:600;">
                    {{ lang._('Start') }} (UTC)
                </label>
                <input type="datetime-local"
                       id="change-summary-start"
                       class="form-control"
                       style="width:200px;display:inline-block;" />

                <label for="change-summary-end"
                       style="margin:0;font-size:12px;font-weight:600;margin-left:10px;">
                    {{ lang._('End') }} (UTC)
                </label>
                <input type="datetime-local"
                       id="change-summary-end"
                       class="form-control"
                       style="width:200px;display:inline-block;" />
            </div>

            <div id="change-summary-fallback"
                 class="change-summary-fallback"
                 style="display:none;">
                {{ lang._('No previous review marker; showing the last 24 hours.') }}
            </div>

            <div class="panel-body change-summary-counters" id="change-summary-counters">
                <span class="change-summary-counter" data-category="all">
                    <span class="change-summary-counter-label">{{ lang._('Total Changes') }}</span>
                    <span class="badge" id="change-summary-count-total">0</span>
                </span>
                <span class="change-summary-counter" data-category="device">
                    <span class="change-summary-counter-label">{{ lang._('New Devices') }}</span>
                    <span class="badge" id="change-summary-count-new_devices">0</span>
                </span>
                <span class="change-summary-counter" data-category="lifecycle">
                    <span class="change-summary-counter-label">{{ lang._('Returned Devices') }}</span>
                    <span class="badge" id="change-summary-count-returned_devices">0</span>
                </span>
                <span class="change-summary-counter" data-category="identity">
                    <span class="change-summary-counter-label">{{ lang._('Identity Changes') }}</span>
                    <span class="badge" id="change-summary-count-identity">0</span>
                </span>
                <span class="change-summary-counter" data-category="infrastructure">
                    <span class="change-summary-counter-label">{{ lang._('Infrastructure Changes') }}</span>
                    <span class="badge" id="change-summary-count-infrastructure">0</span>
                </span>
                <span class="change-summary-counter" data-category="lifecycle">
                    <span class="change-summary-counter-label">{{ lang._('Lifecycle Changes') }}</span>
                    <span class="badge" id="change-summary-count-lifecycle">0</span>
                </span>
            </div>
            </div>
        </div>

        <div class="panel panel-default change-summary-table-panel">
            <div class="table-responsive change-summary-table-wrap">
                <table class="table table-condensed table-hover table-striped"
                       id="grid-change-summary"
                       style="margin-bottom:0;">
                    <thead>
                        <tr>
                            <th class="change-summary-row-number" style="width:40px;">#</th>
                            <th style="width:170px;">{{ lang._('Time') }}</th>
                            <th style="width:120px;">{{ lang._('Category') }}</th>
                            <th>{{ lang._('Device / Subject') }}</th>
                            <th style="width:200px;">{{ lang._('Change') }}</th>
                            <th>{{ lang._('Previous') }}</th>
                            <th>{{ lang._('Current') }}</th>
                            <th style="width:130px;">{{ lang._('Action') }}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td colspan="8" class="text-muted">
                                {{ lang._('Loading changes...') }}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="change-summary-pagination" id="change-summary-pagination"
                 style="display:none;">
                <span id="change-summary-pagination-info"
                      class="text-muted"
                      style="font-size:12px;margin-right:10px;"></span>
                <button id="btn-change-summary-prev"
                        class="btn btn-default btn-xs">
                    {{ lang._('Previous') }}
                </button>
                <button id="btn-change-summary-next"
                        class="btn btn-default btn-xs">
                    {{ lang._('Next') }}
                </button>
            </div>
        </div>

    </div>
</div>

<style>
.content-box .label {
    font-size: 13px;
    line-height: 1.5;
    padding: 1px 5px;
    border: 1px solid transparent;
    border-radius: 3px;
    vertical-align: middle;
    display: inline-block;
}

.change-summary-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.change-summary-controls {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
}

.change-summary-custom-range {
    padding: 8px 15px;
    border-bottom: 1px solid #333;
}

.change-summary-fallback {
    padding: 8px 15px;
    background-color: #2a2a2a;
    color: #f0ad4e;
    font-size: 12px;
    border-bottom: 1px solid #333;
}

.change-summary-counters {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px 18px;
    padding: 10px 15px;
    border-bottom: 1px solid #333;
}

.change-summary-counter {
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 12px;
    color: #888;
}

.change-summary-counter .badge {
    font-size: 12px;
}

.change-summary-counter.active .change-summary-counter-label {
    color: #ccc;
    font-weight: 600;
}

.change-summary-pagination {
    padding: 8px 15px;
    border-top: 1px solid #333;
    text-align: right;
}

#grid-change-summary td {
    vertical-align: middle;
}

/* Row-number column: narrow, right-aligned, visually de-emphasised. */
#grid-change-summary .change-summary-row-number {
    text-align: right;
    color: #777;
    white-space: nowrap;
}

/* The default .table-responsive overflow makes it a scroll container, which
   prevents position:sticky from sticking against page scroll. Override it for
   this page only; the table columns wrap so no horizontal scroll is needed. */
.table-responsive.change-summary-table-wrap {
    overflow: visible;
}

/* Unified opaque sticky controls block (panel title + toolbar + custom-range +
   fallback notice + summary counters). Its top and opaque background are
   assigned by updateChangeSummaryStickyStack(). */
.change-summary-sticky-controls {
    position: sticky;
    z-index: 20;
}

/* Opaque gap cover: a page-scoped ::before pseudo-element extends upward from
   the sticky controls block by exactly the measured gap to
   header.page-content-head, so scrolling event rows cannot show through the
   intentional visual spacing. It is absolutely positioned (out of flow, so no
   layout-height change), inherits the controls block's opaque background, and
   is click-transparent. */
.change-summary-sticky-controls::before {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    bottom: 100%;
    height: var(--change-summary-sticky-gap, 0px);
    background: inherit;
    pointer-events: none;
}

.change-summary-controls-panel {
    margin-bottom: 12px;
}

/* OPNsense page title bar stays sticky above the controls block. */
header.page-content-head {
    position: sticky;
    z-index: 30;
}

/* The table header cells stick immediately beneath the controls block. */
#grid-change-summary thead th {
    position: sticky;
    z-index: 10;
}

.change-summary-subject {
    overflow-wrap: anywhere;
}

.change-summary-subject .mac {
    display: block;
    color: #777;
    font-size: 11px;
}

.change-summary-value {
    overflow-wrap: anywhere;
}
</style>

<script>
$(document).ready(function() {
    var LS_KEY = 'devicemonitor.changeSummary.lastReviewed';
    var state = {
        window: '24h',
        category: 'all',
        offset: 0,
        limit: 50
    };

    function dash(value) {
        return value === null || value === undefined || value === ''
            ? '\u2014'
            : value;
    }

    function pad2(value) {
        return (value < 10 ? '0' : '') + value;
    }

    // Render the authoritative UTC timestamp ("YYYY-MM-DD HH:MM:SS") in the
    // user's browser-local timezone using native Date/Intl formatting. The
    // timezone and its DST rules come from the browser, so no timezone or
    // abbreviation is hardcoded. Output stays compact: DD.MM.YYYY - HH:MM:SS TZ.
    function formatBrowserLocalTime(utc) {
        if (utc === null || utc === undefined || utc === '') {
            return '\u2014';
        }

        // Normalize the space-separated UTC value into an unambiguous ISO-8601
        // UTC instant. A bare "YYYY-MM-DD HH:MM:SS" can be mis-parsed as local
        // time by some engines.
        var iso = String(utc).trim().replace(' ', 'T') + 'Z';
        var date = new Date(iso);

        if (isNaN(date.getTime())) {
            return dash(utc);
        }

        // Browser-local calendar/time fields (native DST rules).
        var day = pad2(date.getDate());
        var month = pad2(date.getMonth() + 1);
        var year = date.getFullYear();
        var hour = pad2(date.getHours());
        var minute = pad2(date.getMinutes());
        var second = pad2(date.getSeconds());

        // Browser-local timezone indicator (abbreviation or offset), chosen
        // natively by the browser rather than hardcoded here.
        var zone = '';
        try {
            var zoneParts = new Intl.DateTimeFormat(undefined, {
                timeZoneName: 'short'
            }).formatToParts(date);

            for (var i = 0; i < zoneParts.length; i++) {
                if (zoneParts[i].type === 'timeZoneName') {
                    zone = zoneParts[i].value;
                    break;
                }
            }
        } catch (e) {
            zone = '';
        }

        return (
            day + '.' + month + '.' + year + ' - ' +
            hour + ':' + minute + ':' + second +
            (zone ? ' ' + zone : '')
        );
    }

    function activityLabel(type) {
        var labels = {
            DEVICE_DISCOVERED: 'New device discovered',
            LIFECYCLE_STARTED: 'Lifecycle started',
            LIFECYCLE_ARCHIVED: 'Lifecycle archived',
            LIFECYCLE_RELINKED: 'Returning device relinked',
            FRIENDLY_NAME_CHANGED: 'Friendly name changed',
            NOTE_CREATED: 'Note created',
            NOTE_UPDATED: 'Note edited',
            NOTE_ARCHIVED: 'Note archived',
            NOTE_CHANGED: 'Note changed',
            IP_CHANGED: 'IP address changed',
            HOSTNAME_CHANGED: 'Hostname changed',
            HOSTNAME_SOURCE_CHANGED: 'Hostname source changed',
            INTERFACE_CHANGED: 'Interface / VLAN changed',
            SERVICE_DISCOVERED: 'Service discovered',
            SERVICE_AVAILABLE: 'Service available',
            SERVICE_UNAVAILABLE: 'Service unavailable',
            SERVICE_CHANGED: 'Service changed',
            IP_IDENTITY_CHANGED: 'IPv4 address used by another device',
            IPV6_IDENTITY_CHANGED: 'IPv6 address used by another device',
            MAC_MULTI_IP: 'Device using multiple IPv4 addresses',
            MAC_MULTI_INTERFACE: 'Device seen on multiple interfaces',
            IDENTITY_RESOLVED: 'Identity issue resolved',
            IDENTITY_REOPENED: 'Identity issue reopened',
            PHYSICAL_DEVICE_CREATED: 'Physical device group created',
            PHYSICAL_DEVICE_ARCHIVED: 'Physical device group archived',
            PHYSICAL_DEVICE_IDENTITY_LINKED: 'Identity linked',
            PHYSICAL_DEVICE_IDENTITY_REMOVED: 'Identity removed'
        };

        if (labels[type]) {
            return labels[type];
        }

        return (type || 'Change')
            .toLowerCase()
            .replace(/_/g, ' ')
            .replace(/\b\w/g, function(letter) {
                return letter.toUpperCase();
            });
    }

    function activityClass(type) {
        if (
            type === 'DEVICE_DISCOVERED' ||
            type === 'LIFECYCLE_STARTED' ||
            type === 'LIFECYCLE_RELINKED' ||
            type === 'SERVICE_AVAILABLE' ||
            type === 'SERVICE_DISCOVERED' ||
            type === 'IDENTITY_RESOLVED' ||
            type === 'NOTE_CREATED' ||
            type === 'PHYSICAL_DEVICE_CREATED' ||
            type === 'PHYSICAL_DEVICE_IDENTITY_LINKED'
        ) {
            return 'label-success';
        }

        if (
            type === 'SERVICE_UNAVAILABLE' ||
            type === 'SERVICE_CHANGED' ||
            type === 'LIFECYCLE_ARCHIVED' ||
            type === 'IDENTITY_REOPENED' ||
            type === 'NOTE_ARCHIVED' ||
            type === 'PHYSICAL_DEVICE_ARCHIVED' ||
            type === 'PHYSICAL_DEVICE_IDENTITY_REMOVED'
        ) {
            return 'label-warning';
        }

        if (
            type === 'IP_IDENTITY_CHANGED' ||
            type === 'IPV6_IDENTITY_CHANGED' ||
            type === 'MAC_MULTI_IP' ||
            type === 'MAC_MULTI_INTERFACE'
        ) {
            return 'label-danger';
        }

        return 'label-info';
    }

    function categoryLabel(category) {
        var labels = {
            device: 'Device',
            lifecycle: 'Lifecycle',
            identity: 'Identity',
            physical_device: 'Physical Device',
            user_history: 'Notes / History',
            infrastructure: 'Infrastructure'
        };

        return labels[category] || category;
    }

    function actionLabel(type) {
        if (type === 'infrastructure') {
            return 'View Infrastructure';
        }

        if (type === 'identity') {
            return 'View Conflict';
        }

        return 'View Device';
    }

    function computeRange() {
        var end = new Date();
        var start;
        var startParam;
        var endParam;
        var fallback = false;

        if (state.window === 'since_last_review') {
            var marker = localStorage.getItem(LS_KEY);

            if (marker) {
                var parsed = new Date(marker);

                if (!isNaN(parsed.getTime())) {
                    start = parsed;

                    var min = new Date(
                        end.getTime() - 90 * 24 * 3600 * 1000
                    );

                    if (start < min) {
                        start = min;
                    }
                }
            }

            if (!start) {
                fallback = true;
                start = new Date(end.getTime() - 24 * 3600 * 1000);
            }

            startParam = start.toISOString();
            endParam = end.toISOString();
        } else if (state.window === '7d') {
            start = new Date(end.getTime() - 7 * 24 * 3600 * 1000);
            startParam = start.toISOString();
            endParam = end.toISOString();
        } else if (state.window === '30d') {
            start = new Date(end.getTime() - 30 * 24 * 3600 * 1000);
            startParam = start.toISOString();
            endParam = end.toISOString();
        } else if (state.window === 'custom') {
            var sv = $('#change-summary-start').val();
            var ev = $('#change-summary-end').val();

            if (sv && ev) {
                startParam = sv;
                endParam = ev;
            } else {
                start = new Date(end.getTime() - 24 * 3600 * 1000);
                startParam = start.toISOString();
                endParam = end.toISOString();
            }
        } else {
            start = new Date(end.getTime() - 24 * 3600 * 1000);
            startParam = start.toISOString();
            endParam = end.toISOString();
        }

        return {
            startParam: startParam,
            endParam: endParam,
            fallback: fallback
        };
    }

    function showToast(message) {
        if (typeof $.fn.notify !== 'undefined') {
            $.notify(message, { type: 'success' });
            return;
        }

        if (typeof window.bootbox !== 'undefined') {
            window.bootbox.alert(message);
        }
    }

    function showLoadError(message) {
        $('#grid-change-summary tbody')
            .empty()
            .append(
                $('<tr>').append(
                    $('<td>')
                        .attr('colspan', 8)
                        .addClass('text-danger')
                        .text(message)
                )
            );
    }

    function renderSummary(summary) {
        $('#change-summary-count-total').text(summary.total || 0);
        $('#change-summary-count-new_devices').text(summary.new_devices || 0);
        $('#change-summary-count-returned_devices').text(
            summary.returned_devices || 0
        );
        $('#change-summary-count-identity').text(summary.identity || 0);
        $('#change-summary-count-infrastructure').text(
            summary.infrastructure || 0
        );
        $('#change-summary-count-lifecycle').text(summary.lifecycle || 0);

        $('.change-summary-counter').each(function() {
            $(this).toggleClass(
                'active',
                $(this).data('category') === state.category
            );
        });
    }

    function loadChanges() {
        var range = computeRange();

        $('#change-summary-fallback').toggle(range.fallback);
        updateChangeSummaryStickyStack();

        $.ajax({
            url: '/api/devicemonitor/devices/changesummary',
            type: 'GET',
            data: {
                start: range.startParam,
                end: range.endParam,
                category: state.category,
                limit: state.limit,
                offset: state.offset
            },
            dataType: 'json',
            success: function(result) {
                if (!result || result.result !== 'ok') {
                    showLoadError(
                        (result && result.error) ||
                        'Unable to load changes'
                    );
                    return;
                }

                renderSummary(result.summary || {});
                renderTable(result.events || [], result.total || 0, result.offset || 0);
                renderPagination(
                    result.total || 0,
                    result.offset || 0,
                    result.limit || state.limit
                );
            },
            error: function() {
                showLoadError('Unable to load changes');
            }
        });
    }

    function renderTable(events, total, offset) {
        var $tbody = $('#grid-change-summary tbody').empty();

        if (!Array.isArray(events) || events.length === 0) {
            $('<tr>').append(
                $('<td>')
                    .attr('colspan', 8)
                    .addClass('text-muted')
                    .text(
                        'No meaningful Device Monitor changes were ' +
                        'recorded in this period.'
                    )
            ).appendTo($tbody);
            return;
        }

        events.forEach(function(event, rowIndex) {
            var $label = $('<span>')
                .addClass('label ' + activityClass(event.event_type || ''))
                .text(activityLabel(event.event_type));

            var $subject = $('<div>')
                .addClass('change-summary-subject')
                .append($('<span>').text(dash(event.subject)));

            if (event.mac) {
                $subject.append(
                    $('<span>').addClass('mac').text(event.mac)
                );
            }

            var $actionCell = $('<td>');

            if (event.action && event.action.target) {
                $('<a>')
                    .attr('href', event.action.target)
                    .addClass('btn btn-default btn-xs')
                    .text(actionLabel(event.action.type))
                    .appendTo($actionCell);
            } else {
                $actionCell.text('\u2014');
            }

            $('<tr>').append(
                $('<td>')
                    .addClass('change-summary-row-number')
                    .text(total - offset - rowIndex),
                $('<td>')
                    .css('white-space', 'nowrap')
                    .text(formatBrowserLocalTime(event.occurred_at_utc)),
                $('<td>').text(categoryLabel(event.category)),
                $('<td>').append($subject),
                $('<td>').append($label),
                $('<td>')
                    .addClass('change-summary-value')
                    .text(dash(event.previous)),
                $('<td>')
                    .addClass('change-summary-value')
                    .text(dash(event.current)),
                $actionCell
            ).appendTo($tbody);
        });
    }

    function renderPagination(total, offset, limit) {
        var $pagination = $('#change-summary-pagination');

        if (total <= 0) {
            $pagination.hide();
            return;
        }

        var from = offset + 1;
        var to = Math.min(offset + limit, total);

        $('#change-summary-pagination-info').text(
            'Showing ' + from + '\u2013' + to + ' of ' + total
        );

        $('#btn-change-summary-prev').prop('disabled', offset <= 0);
        $('#btn-change-summary-next').prop('disabled', to >= total);

        $pagination.show();
    }

    function updateCustomRangeVisibility() {
        $('#change-summary-custom-range').toggle(
            state.window === 'custom'
        );
        updateChangeSummaryStickyStack();
    }

    $('#change-summary-window').on('change', function() {
        state.window = $(this).val() || '24h';
        state.offset = 0;
        updateCustomRangeVisibility();
        loadChanges();
    });

    $('#change-summary-category').on('change', function() {
        state.category = $(this).val() || 'all';
        state.offset = 0;
        loadChanges();
    });

    $('#change-summary-start, #change-summary-end').on('change', function() {
        state.offset = 0;
        loadChanges();
    });

    $('#btn-change-summary-refresh').on('click', function() {
        loadChanges();
    });

    $('#btn-mark-reviewed').on('click', function() {
        localStorage.setItem(LS_KEY, new Date().toISOString());
        showToast('Marked as reviewed');

        if (state.window === 'since_last_review') {
            state.offset = 0;
            loadChanges();
        }
    });

    $('#btn-change-summary-prev').on('click', function() {
        if (state.offset > 0) {
            state.offset = Math.max(0, state.offset - state.limit);
            loadChanges();
        }
    });

    $('#btn-change-summary-next').on('click', function() {
        state.offset += state.limit;
        loadChanges();
    });

    $('.change-summary-counter').on('click', function() {
        state.category = $(this).data('category') || 'all';
        state.offset = 0;

        $('#change-summary-category').val(state.category);
        $('#change-summary-category').selectpicker('refresh');

        loadChanges();
    });

    // Records the page title bar's normal-flow document position and the visual
    // gap to the controls block, measured once before sticky offsets shift.
    var changeSummaryStickyGeometry = null;

    // Keep the page title bar, one unified opaque controls block and the
    // table column header sticky while the event rows scroll underneath.
    // position:sticky only sticks against the document once the wrapping
    // .table-responsive overflow is removed (see the style block above).
    function updateChangeSummaryStickyStack() {
        var pageHead = $('header.page-content-head');
        var $controls = $('#change-summary-sticky-controls');
        var $table = $('#grid-change-summary');

        function opaqueBackground($el) {
            var node = $el;
            var bg = node.css('background-color');

            while (
                node.length &&
                (!bg || bg === 'transparent' || bg === 'rgba(0, 0, 0, 0)')
            ) {
                node = node.parent();
                bg = node.css('background-color');
            }

            return bg || '#101218';
        }

        // Measure the normal-flow geometry once before sticky scrolling shifts
        // positions. The page title bar's own rendered top is used as the
        // baseline (rather than assuming it equals the fixed menu height), so
        // no small vertical jump occurs when sticky engages.
        if (
            changeSummaryStickyGeometry === null &&
            pageHead.length &&
            $controls.length
        ) {
            var pageHeadRect = pageHead[0].getBoundingClientRect();
            var controlsRect = $controls[0].getBoundingClientRect();
            var scrollTop =
                (document.scrollingElement || document.documentElement)
                    .scrollTop;

            changeSummaryStickyGeometry = {
                pageHeadTop: pageHeadRect.top + scrollTop,
                gap: controlsRect.top - pageHeadRect.bottom
            };
        }

        if (changeSummaryStickyGeometry === null) {
            return;
        }

        var pageHeadTop = changeSummaryStickyGeometry.pageHeadTop;
        var initialGap = changeSummaryStickyGeometry.gap;

        // Rendered layout height of the page title bar, unaffected by sticky.
        var pageHeadHeight = pageHead.length
            ? pageHead[0].offsetHeight
            : 0;

        // OPNsense page title bar.
        if (pageHead.length) {
            pageHead.css('top', pageHeadTop + 'px');
            pageHead.css('background-color', opaqueBackground(pageHead));
        }

        // Unified sticky controls block (title + toolbar + custom-range +
        // fallback notice + summary counters).
        if ($controls.length) {
            var controlsTop = pageHeadTop + pageHeadHeight + initialGap;

            $controls.css('top', controlsTop + 'px');
            $controls.css('background-color', opaqueBackground($controls));

            // Expose the measured gap to the CSS gap cover so it extends upward
            // by exactly the same distance (no layout or sticky-top change).
            $controls[0].style.setProperty(
                '--change-summary-sticky-gap',
                initialGap + 'px'
            );

            // Table column header sits immediately beneath the controls block.
            var controlsHeight = $controls[0].getBoundingClientRect().height;
            var tableHeaderTop = controlsTop + controlsHeight;

            var thead = $table.find('thead th');
            var theadBg = opaqueBackground(thead);

            thead.css('top', tableHeaderTop + 'px');
            thead.css('background-color', theadBg);
            $table.find('thead').css('background-color', theadBg);
        }
    }

    $(window).on('resize', updateChangeSummaryStickyStack);
    updateChangeSummaryStickyStack();

    updateCustomRangeVisibility();
    loadChanges();
});
</script>
