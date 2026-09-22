<div class="content-box">
    <div class="content-box-main">

        <!-- Device navigation tabs -->
        <ul class="nav nav-tabs" role="tablist" style="margin:10px 0 0 0;">
            <li role="presentation" class="active">
                <a href="/ui/devicemonitor/index/devices">
                    <i class="fa fa-list"></i> {{ lang._('Network Identities') }}
                </a>
            </li>
            <li role="presentation">
                <a href="/ui/devicemonitor/index/physicaldevices">
                    <i class="fa fa-sitemap"></i> {{ lang._('Device Profiles') }}
                </a>
            </li>
        </ul>
        <p class="text-muted" style="margin:8px 0 0 0;">
            {{ lang._('Automatically discovered network identities. Each row represents one MAC address.') }}
        </p>

        <!-- Sticky region: summary counters + VLAN/status toolbar remain pinned
             while device rows scroll; the column headings stick directly below. -->
        <div id="devices-sticky-header">

            <!-- Header with statistics -->
            <div id="devices-sticky-summary" class="devices-header">
                <div class="devices-stats">
                    <span>
                        {{ lang._('Total Devices') }}:
                        <strong id="stat-total">—</strong>
                    </span>
                    <span>
                        {{ lang._('Online') }}:
                        <strong id="stat-online">—</strong>
                    </span>
                </div>
            </div>

            <!-- Toolbar -->
            <div id="devices-sticky-toolbar" class="devices-toolbar">

                <!-- Multi-select VLAN dropdown -->
                <div class="dropdown" id="vlan-filter-wrapper">
                    <button type="button" class="btn btn-default btn-sm dropdown-toggle"
                            id="vlan-dropdown-toggle" data-toggle="dropdown">
                        <span id="vlan-filter-label">{{ lang._('All VLANs') }}</span>
                        <span class="caret"></span>
                    </button>
                    <ul class="dropdown-menu" id="vlan-checklist">
                    </ul>
                </div>

                <!-- Explicit apply/clear controls for the VLAN multi-select -->
                <button type="button" id="vlan-apply" class="btn btn-default btn-sm">{{ lang._('Apply') }}</button>
                <button type="button" id="vlan-clear" class="btn btn-default btn-sm">{{ lang._('Clear') }}</button>

                <!-- Status filtr -->
                <select id="filter-status"
                        class="selectpicker"
                        data-style="btn-default btn-sm"
                        data-width="130px">
                    <option value="">{{ lang._('All statuses') }}</option>
                    <option value="online">🟢 Online</option>
                    <option value="offline">⚫ Offline</option>
                </select>

                <button id="btn-refresh" class="btn btn-default btn-sm" title="{{ lang._('Refresh') }}">
                    <i class="fa fa-refresh"></i>
                </button>

                <button id="btn-scan-now" class="btn btn-default btn-sm" title="{{ lang._('Run scan now') }}">
                    <i class="fa fa-search"></i>
                </button>

                <button id="btn-export" class="btn btn-default btn-sm" title="{{ lang._('Export to CSV') }}">
                    <i class="fa fa-download"></i>
                </button>

                <div class="devices-toolbar-spacer"></div>

                <button id="btn-clear" class="btn btn-danger btn-sm">
                    <i class="fa fa-trash"></i> {{ lang._('Clear Database') }}
                </button>
            </div>

        </div>

        <!-- Tabulka -->
        <table class="table table-condensed table-hover table-striped devices-table" id="grid-devices">
            <thead>
                <tr>
                    <th class="sortable devices-table-header" data-col="ip">{{ lang._('IP Address') }} <i class="fa fa-sort"></i></th>
                    <th class="sortable devices-table-header" data-col="custom_hostname">{{ lang._('Friendly Name') }} <i class="fa fa-sort"></i></th>
                    <th class="sortable devices-table-header" data-col="hostname">{{ lang._('Hostname') }} <i class="fa fa-sort"></i></th>
                    <th class="sortable devices-table-header" data-col="mac">{{ lang._('MAC Address') }} <i class="fa fa-sort"></i></th>
                    <th class="sortable devices-table-header" data-col="vendor">{{ lang._('Vendor') }} <i class="fa fa-sort"></i></th>                    <th class="devices-table-header">{{ lang._('Services') }}</th>

                    <th class="sortable devices-table-header" data-col="vlan">{{ lang._('VLAN') }} <i class="fa fa-sort"></i></th>
                    <th class="sortable devices-table-header" data-col="status">{{ lang._('Status') }} <i class="fa fa-sort"></i></th>
                    <th class="devices-table-header">{{ lang._('Device Profile') }}</th>
                    <th class="sortable devices-table-header" data-col="nmap_scan_status">{{ lang._('Scan Status') }} <i class="fa fa-sort"></i></th>
                    <th class="devices-table-header">{{ lang._('First Seen') }}</th>
                    <th class="sortable devices-table-header" data-col="last_seen">{{ lang._('Last Seen') }} <i class="fa fa-sort"></i></th>
                    <th class="devices-table-header">{{ lang._('Actions') }}</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>

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

.devices-header {
    padding: 10px 10px 8px 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
    border-bottom: 1px solid #444;
    margin-bottom: 0;
}
.devices-header h1 {
    margin: 0;
    font-size: 20px;
}
.devices-header small {
    font-size: 13px;
    color: #888;
    margin-left: 5px;
}
.devices-divider {
    color: #777;
    margin: 0 8px;
}
.devices-title {
    font-weight: normal;
}
.devices-stats {
    display: flex;
    gap: 20px;
    align-items: center;
    font-size: 13px;
    color: #888;
}
.devices-stats strong {
    font-size: 16px;
    margin-left: 4px;
    color: #ccc;
}
#stat-online {
    color: #4CAF50;
}

.devices-toolbar {
    padding: 0 4px 12px 4px;
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
}
.devices-table {
    margin-top: 0;
    border-top: 2px solid #444;
}
.devices-table-header {
    cursor: default;
    white-space: nowrap;
}
.devices-table-header.sortable {
    cursor: pointer;
}
.devices-grouping-cell {
    white-space: nowrap;
    max-width: 220px;
}
.devices-grouping-badge {
    display: inline-block;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    vertical-align: middle;
    white-space: nowrap;
}
.devices-toolbar-spacer {
    flex-grow: 1;
}
#vlan-dropdown-toggle {
    min-width: 160px;
    text-align: left;
}
#vlan-dropdown-toggle .caret {
    float: right;
    margin-top: 7px;
}
#vlan-checklist {
    min-width: 240px;
    padding: 4px 0;
    max-height: 300px;
    overflow-y: auto;
}

#grid-devices thead th {
    font-size: 12px;
    font-weight: 600;
    vertical-align: middle;
    white-space: nowrap;
    position: sticky;
    top: var(--devices-sticky-thead-top);
    z-index: 10;
}

/* Single sticky block (summary counters + VLAN/status toolbar). Its top offset
   and opaque background are assigned by syncDevicesStickyHeader() so it sits
   flush beneath the OPNsense fixed top navbar and never covers the page title,
   tabs or explanatory text. No scroll-snap, pseudo-element shield or cached
   one-shot geometry is used. */
#devices-sticky-header {
    position: sticky;
    top: var(--devices-sticky-top);
    z-index: 20;
}
#devices-sticky-toolbar {
    padding: 12px 4px 12px 4px;
    margin: 0;
    border-bottom: 1px solid #333;
}
main.page-content > .row {
    height: auto;
    min-height: 100%;
}
</style>

<script>
    // Pure filter/summary helpers live at script scope so the Devices page
    // header counters and the rendered table share one source of truth and
    // can be unit-tested without a DOM.
    function applyDeviceFilters(rows, activeVlans, activeStatus) {
        var vlans = activeVlans || [];
        var status = activeStatus || '';

        if (!rows || !rows.length) {
            return [];
        }

        return rows.filter(function (r) {
            var vlanOk = !vlans.length || vlans.indexOf(r.vlan) !== -1;
            var statusOk = !status || r.status === status;
            return vlanOk && statusOk;
        });
    }

    function summarizeDevices(rows) {
        var total = 0;
        var online = 0;

        (rows || []).forEach(function (r) {
            total += 1;
            if (r.status === 'online') {
                online += 1;
            }
        });

        return { total: total, online: online };
    }

    // Resolve a set of checked VLANs into the active VLAN filter array.
    // Selecting no VLANs, or every known VLAN, means "no VLAN filter"
    // (an empty array), matching the existing All VLANs behaviour.
    function finalizeVlanSelection(selectedVlans, allVlans) {
        var selected = selectedVlans || [];
        var all = allVlans || [];
        var uniq = [];
        selected.forEach(function (v) {
            if (uniq.indexOf(v) === -1) {
                uniq.push(v);
            }
        });
        if (!uniq.length) {
            return [];
        }
        if (all.length && uniq.length === all.length) {
            return [];
        }
        return uniq.sort();
    }

$(document).ready(function() {

    var translations = {
        deleted:        '{{ lang._('Device deleted') }}',
        delete_error:   '{{ lang._('Error deleting device') }}',
        db_cleared:     '{{ lang._('Database cleared') }}',
        db_clear_error: '{{ lang._('Error clearing database') }}',
        hostname_saved: '{{ lang._('Friendly name saved') }}',
        hostname_cleared: '{{ lang._('Friendly name cleared') }}',
        hostname_error: '{{ lang._('Error saving friendly name') }}',
        confirm_delete: '{{ lang._('Delete device') }}',
        confirm_clear:  '{{ lang._('Really delete all devices from database?') }}',
        all_vlans:      '{{ lang._('All VLANs') }}',
        identity:       '{{ lang._('identity') }}',
        identities:     '{{ lang._('identities') }}'
    };

    var allRows = [], activeVlans = [], activeStatus = '', vlanNames = {};
    var sortCol = 'last_seen', sortDir = 'desc';

    // Restore saved VLAN filter
    try { activeVlans = JSON.parse(localStorage.getItem('dm_vlan_filter') || '[]'); } catch(e) {}

    // Toast
    function showToast(msg, type) {
        var bg = type==='success'?'#4CAF50':(type==='error'?'#f44336':'#2196F3');
        var ic = type==='success'?'fa-check-circle':(type==='error'?'fa-exclamation-circle':'fa-info-circle');
        var $t = $('<div>').css({position:'fixed',top:'20px',right:'20px','background-color':bg,color:'white',
            padding:'15px 20px','border-radius':'4px','box-shadow':'0 4px 8px rgba(0,0,0,.3)',
            'z-index':9999,'min-width':'280px',display:'none'})
            .html('<i class="fa '+ic+'"></i> '+msg);
        $('body').append($t); $t.fadeIn(300);
        setTimeout(function(){ $t.fadeOut(300,function(){ $t.remove(); }); },3000);
    }

    function updateSummary(rows) {
        var summary = summarizeDevices(rows);
        $('#stat-total').text(summary.total);
        $('#stat-online').text(summary.online);
    }

    // VLAN multi-select dropdown (pending selection; Apply commits it)
    function buildVlanDropdown(vlans) {
        var $list = $('#vlan-checklist').empty();
        if (!vlans.length) return;
        var allSel = (activeVlans.length === 0);

        $list.append($('<li>').append(
            $('<label>').css({margin:0,cursor:'pointer',display:'flex',alignItems:'center',gap:'6px',padding:'5px 14px'}).append(
                $('<input type="checkbox" id="vlan-all">').prop('checked', allSel),
                $('<span>').css({'font-style':'italic'}).text(translations.all_vlans)
            )
        ));

        $list.append($('<li class="divider" style="margin:4px 0;">'));

        vlans.sort().forEach(function(v) {
            var n = vlanNames[v];
            var label = (n && n !== v) ? (v+' \u2013 '+n) : v;
            var chk = allSel || (activeVlans.indexOf(v) !== -1);
            $list.append($('<li>').append(
                $('<label>').css({margin:0,cursor:'pointer',display:'flex',alignItems:'center',gap:'6px',padding:'4px 14px'}).append(
                    $('<input type="checkbox" class="vlan-cb">').val(v).prop('checked', chk),
                    $('<span>').css('margin-left','8px').text(label)
                )
            ));
        });
        updateVlanLabel();
    }

    // Keep the dropdown open while checkboxes are toggled.
    $('#vlan-checklist').on('click', function(e){ e.stopPropagation(); });

    // Toggling a checkbox only updates the pending visual state; the table is
    // not filtered or re-rendered until Apply/Clear.
    $(document).on('change','#vlan-all',function(){
        $('#vlan-checklist .vlan-cb').prop('checked',$(this).prop('checked'));
        updateVlanLabel();
    });
    $(document).on('change','#vlan-checklist .vlan-cb',function(){
        var total=$('#vlan-checklist .vlan-cb').length;
        var checked=$('#vlan-checklist .vlan-cb:checked').length;
        $('#vlan-all').prop('checked', total===checked);
        updateVlanLabel();
    });

    function readCheckedVlans() {
        var sel = [];
        $('#vlan-checklist .vlan-cb:checked').each(function(){ sel.push($(this).val()); });
        return sel;
    }

    function commitVlans() {
        var allVlans = [];
        $('#vlan-checklist .vlan-cb').each(function(){ allVlans.push($(this).val()); });
        activeVlans = finalizeVlanSelection(readCheckedVlans(), allVlans);
        try { localStorage.setItem('dm_vlan_filter', JSON.stringify(activeVlans)); } catch(e) {}
        updateVlanLabel();
        applyFilters();
    }

    $('#vlan-apply').on('click', function(){ commitVlans(); });

    $('#vlan-clear').on('click', function(){
        $('#vlan-checklist .vlan-cb').prop('checked', true);
        $('#vlan-all').prop('checked', true);
        activeVlans = [];
        try { localStorage.setItem('dm_vlan_filter', JSON.stringify([])); } catch(e) {}
        updateVlanLabel();
        applyFilters();
    });

    // The button reflects the pending checkbox selection immediately: it shows
    // the number of checked VLANs, or "All VLANs" when nothing is restricted
    // (no VLANs or every VLAN checked). It never reads the applied state.
    function updateVlanLabel() {
        var total = $('#vlan-checklist .vlan-cb').length;
        var checked = $('#vlan-checklist .vlan-cb:checked').length;
        if (checked === 0 || checked === total) {
            $('#vlan-filter-label').text(translations.all_vlans);
        } else if (checked === 1) {
            $('#vlan-filter-label').text('1 VLAN');
        } else {
            $('#vlan-filter-label').text(checked + ' VLANs');
        }
    }

    // Preserve the user's vertical and horizontal scroll position across a
    // table re-render so filtering never visibly jumps or scrolls the page.
    function captureScrollPosition() {
        var root = document.scrollingElement || document.documentElement;
        var x = (window.pageXOffset !== undefined) ? window.pageXOffset : (root ? root.scrollLeft : 0);
        var y = (window.pageYOffset !== undefined) ? window.pageYOffset : (root ? root.scrollTop : 0);
        return { x: x, y: y };
    }

    function restoreScrollPosition(pos) {
        if (!pos) return;
        window.scrollTo(pos.x, pos.y);
    }

    // Filtering
    function applyFilters() {
        var filtered = applyDeviceFilters(allRows, activeVlans, activeStatus);
        // Sorting
        filtered.sort(function(a, b) {
            var va = a[sortCol] || '';
            var vb = b[sortCol] || '';

            // Numeric sorting for IP addresses
            if (sortCol === 'ip') {
                var ia = va.split('.').map(Number);
                var ib = vb.split('.').map(Number);
                for (var i = 0; i < 4; i++) {
                    if ((ia[i]||0) !== (ib[i]||0)) {
                        var cmp = (ia[i]||0) < (ib[i]||0) ? -1 : 1;
                        return sortDir === 'asc' ? cmp : -cmp;
                    }
                }
                return 0;
            }

            // Numeric sorting for MAC addresses in hexadecimal
            if (sortCol === 'mac') {
                var ma = va.replace(/:/g,'').toLowerCase();
                var mb = vb.replace(/:/g,'').toLowerCase();
                var cmp = ma < mb ? -1 : ma > mb ? 1 : 0;
                return sortDir === 'asc' ? cmp : -cmp;
            }

            // Text sorting for remaining fields
            va = va.toString().toLowerCase();
            vb = vb.toString().toLowerCase();
            if (va === vb) return 0;
            var cmp = va < vb ? -1 : 1;
            return sortDir === 'asc' ? cmp : -cmp;
        });

        var scroll = captureScrollPosition();
        renderTable(filtered);
        restoreScrollPosition(scroll);
        updateSummary(filtered);
        // Update sort-arrow icons
        $('th.sortable .fa').removeClass('fa-sort-asc fa-sort-desc').addClass('fa-sort');
        $('th.sortable[data-col="'+sortCol+'"] .fa')
            .removeClass('fa-sort')
            .addClass(sortDir === 'asc' ? 'fa-sort-asc' : 'fa-sort-desc');
    }

    function buildScanStatusCell(row) {
        var $cell = $('<td>');
        var state = row.nmap_scan_status || '';
        var attempts = parseInt(row.nmap_scan_attempts || 0, 10);

        if (!state) {
            return $cell.html('<span style="color:#777;">&mdash;</span>');
        }

        if (row.nmap_last_error) {
            $cell.attr('title', row.nmap_last_error);
        }

        if (state === 'pending') {
            return $cell.html('<span style="color:#5bc0de;font-weight:bold;white-space:nowrap;"><i class="fa fa-clock-o"></i> Pending</span>');
        }

        if (state === 'retrying') {
            $cell.append(
                $('<div>').css({
                    'color': '#f0ad4e',
                    'font-weight': 'bold',
                    'white-space': 'nowrap'
                }).text('Retry ' + attempts + '/5')
            );

            if (row.nmap_next_attempt) {
                $cell.append(
                    $('<small>').addClass('text-muted').css({
                        'display': 'block',
                        'white-space': 'nowrap'
                    }).text('Next: ' + row.nmap_next_attempt)
                );
            }

            return $cell;
        }

        if (state === 'failed') {
            return $cell.html('<span style="color:#d9534f;font-weight:bold;white-space:nowrap;"><i class="fa fa-exclamation-triangle"></i> Failed ' + attempts + '/5</span>');
        }

        return $cell;
    }

    function buildGroupingCell(row) {
        var $cell = $('<td>').addClass('devices-grouping-cell');
        var groupName = (row.physical_device_name || '').toString().trim();
        var memberCount = parseInt(row.physical_device_member_count || 0, 10);
        var groupId = row.physical_device_id;

        if (!groupId || memberCount < 1) {
            return $cell.append(
                $('<span>').addClass('text-muted').text('\u2014')
            );
        }

        var label = groupName;
        label += ' \u00b7 ' + memberCount + ' ' +
            (memberCount === 1 ? translations.identity : translations.identities);

        return $cell.append(
            $('<a>')
                .addClass('label label-info devices-grouping-badge')
                .attr({
                    href: '/ui/devicemonitor/index/physicaldevices?group=' +
                        encodeURIComponent(groupId),
                    title: label
                })
                .text(label)
        );
    }

    function buildServicesCell(row) {
        var $cell = $('<td>').css('white-space', 'nowrap');
        var services = Array.isArray(row.services) ? row.services : [];

        if (!services.length) {
            return $cell.append(
                $('<span>')
                    .addClass('text-muted')
                    .text('\u2014')
            );
        }

        var seen = {};

        services.forEach(function(service) {
            var type = (service.service_type || '')
                .toString()
                .toUpperCase();

            if (!type || seen[type]) {
                return;
            }

            seen[type] = true;

            var confidence = (service.confidence || '').toString();
            var method = (service.detection_method || '').toString();
            var endpoint =
                (service.protocol || '').toString().toUpperCase() +
                '/' +
                (service.port || '');

            var title = type;

            if (endpoint !== '/') {
                title += ' - ' + endpoint;
            }

            if (confidence) {
                title += ' - ' + confidence;
            }

            if (method) {
                title += ' (' + method + ')';
            }

            var labelClass = 'label-default';

            if (type === 'DNS') {
                labelClass = 'label-info';
            } else if (type === 'DHCP') {
                labelClass = 'label-warning';
            }

            $('<span>')
                .addClass('label ' + labelClass)
                .attr('title', title)
                .css({
                    'display': 'inline-block',
                    'margin-right': '4px'
                })
                .text(type)
                .appendTo($cell);
        });

        return $cell;
    }
    function hostnameSourceLabel(source) {
        var labels = {
            adguard: '{{ lang._('AdGuard DNS rewrite') }}',
            dnsmasq: '{{ lang._('Dnsmasq') }}',
            kea: '{{ lang._('Kea DHCP') }}',
            isc: '{{ lang._('ISC DHCP') }}',
            hostwatch: '{{ lang._('Hostwatch') }}'
        };
        return labels[source] || source || '';
    }

    // Render table
    function renderTable(rows) {
        var $tbody = $('#grid-devices tbody').empty();
        rows.forEach(function(row) {
            var statusHtml;
            if (row.return_pending === 1 || row.return_pending === '1') {
                statusHtml = '<span style="color:#f0ad4e;font-weight:bold;white-space:nowrap;"><i class="fa fa-history"></i> RETURNING</span>';
            } else {
                statusHtml = row.status==='online'
                    ? '<span style="color:#4CAF50;font-weight:bold;white-space:nowrap;"><i class="fa fa-circle"></i> ONLINE</span>'
                    : '<span style="color:#666;font-weight:bold;white-space:nowrap;"><i class="fa fa-circle-o"></i> OFFLINE</span>';
            }

            var hn = row.hostname || '';
            var hostnameSource = hostnameSourceLabel(row.hostname_source || '');
            var friendly = row.custom_hostname || '';
            var friendlyDecoder = document.createElement('textarea');
            friendlyDecoder.innerHTML = friendly;
            friendly = friendlyDecoder.value;

            var $friendlyCell = $('<td>');
            var $friendlyDisplay = $('<span>')
                .addClass('friendly-name-display')
                .attr('data-mac', row.mac || '')
                .attr('data-friendly', friendly)
                .attr('title', 'Click to edit friendly name')
                .css({
                    cursor: 'pointer',
                    'border-bottom': '1px dashed #666'
                });

            if (friendly) {
                $('<i>')
                    .addClass('fa fa-tag')
                    .attr('title', 'Friendly name')
                    .appendTo($friendlyDisplay);
                $friendlyDisplay.append(document.createTextNode(' ' + friendly));
            } else {
                $('<em>')
                    .css('color', '#555')
                    .text('\u2014')
                    .appendTo($friendlyDisplay);
            }

            $friendlyDisplay.appendTo($friendlyCell);

            var $hostnameCell = $('<td>');
            if (hn) {
                $('<span>')
                    .text(hn)
                    .appendTo($hostnameCell);

                if (hostnameSource) {
                    $('<small>')
                        .css({
                            display: 'block',
                            color: '#777',
                            'margin-top': '2px'
                        })
                        .text(hostnameSource)
                        .appendTo($hostnameCell);
                }
            } else {
                $('<em>')
                    .css('color', '#555')
                    .text('\u2014')
                    .appendTo($hostnameCell);
            }

            var ipHtml = row.ip
                ? '<a href="http://'+row.ip+'" target="_blank" style="color:#5bc0de;">'+row.ip+'</a>'
                : '';

            var vlanLabel = row.vlan||'';
            if (row.vlan && vlanNames[row.vlan]) vlanLabel += ' \u2013 '+vlanNames[row.vlan];

            $('<tr>').append(
                $('<td>').html(ipHtml),
                $friendlyCell,
                $hostnameCell,
                $('<td>').text(row.mac||''),
                $('<td>').text(row.vendor||''),
                buildServicesCell(row),
                $('<td>').text(vlanLabel),
                $('<td>').html(statusHtml),
                buildGroupingCell(row),
                buildScanStatusCell(row),
                $('<td>').text(row.first_seen||''),
                $('<td>').text(row.last_seen||''),
                $('<td>').html(
                (row.return_pending === 1 || row.return_pending === '1'
                    ? '<a class="btn btn-xs btn-primary" href="/ui/devicemonitor/index/devicehistory?mac='+encodeURIComponent(row.mac||'')+'#lifecycle-history" title="Resolve returning device / lifecycle history" style="margin-right:2px;"><i class="fa fa-history"></i> History</a>'
                    : '<a class="btn btn-xs btn-default" href="/ui/devicemonitor/index/devicehistory?mac='+encodeURIComponent(row.mac||'')+'" title="Device details and notes" style="margin-right:2px;"><i class="fa fa-comment-o"></i></a>') +
                '<button class="btn btn-xs btn-warning command-check" data-row-mac="'+row.mac+'" data-row-ip="'+row.ip+'" title="Check online" style="margin-right:2px;"><i class="fa fa-plug"></i></button>' +
                '<button class="btn btn-xs btn-info command-nmap" data-row-mac="'+row.mac+'" title="Run targeted Nmap scan" style="margin-right:2px;"><i class="fa fa-search"></i></button>' +
                '<button class="btn btn-xs btn-danger command-delete" data-row-mac="'+row.mac+'"><i class="fa fa-trash"></i></button>')
            ).appendTo($tbody);
        });
        bindButtons();
    }

    // Load data
    function loadDevices() {
        $.ajax({url:'/api/devicemonitor/devices/search',type:'POST',
            data:{rowCount:-1,current:1,searchPhrase:''},
            success:function(data){
                allRows = data.rows||[];
                var vlans={};
                allRows.forEach(function(r){ if(r.vlan) vlans[r.vlan]=1; });
                buildVlanDropdown(Object.keys(vlans));
                applyFilters();
            }
        });
    }

    function bindButtons() {
        $('.command-delete').off('click').on('click',function(){
            var mac=$(this).data('row-mac');
            if (!confirm(translations.confirm_delete+' '+mac+'?')) return;
            $.ajax({url:'/api/devicemonitor/devices/delete',type:'POST',data:{mac:mac},
                success:function(r){
                    showToast(r.result==='deleted'?translations.deleted:translations.delete_error,
                              r.result==='deleted'?'success':'error');
                    loadDevices();
                }
            });
        });

        $('.command-nmap').off('click').on('click', function() {
            var mac = $(this).data('row-mac');
            var $btn = $(this);

            $btn.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i>');

            $.ajax({
                url: '/api/devicemonitor/devices/nmapscan',
                type: 'POST',
                data: { mac: mac },
                success: function(r) {
                    $btn.prop('disabled', false).html('<i class="fa fa-search"></i>');

                    if (r.result === 'scanned') {
                        showToast(r.message || 'Targeted Nmap scan completed', 'success');
                    } else {
                        showToast(r.error || 'Targeted Nmap scan failed', 'error');
                    }
                },
                error: function(xhr) {
                    $btn.prop('disabled', false).html('<i class="fa fa-search"></i>');

                    var message = 'Targeted Nmap scan failed';
                    if (xhr.responseJSON && xhr.responseJSON.error) {
                        message = xhr.responseJSON.error;
                    }

                    showToast(message, 'error');
                }
            });
        });


        $('.command-check').off('click').on('click', function() {
            var mac = $(this).data('row-mac');
            var ip  = $(this).data('row-ip');
            var $btn = $(this);

            if (!ip) {
                showToast('No IP address for this device', 'error');
                return;
            }

            $btn.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i>');

            $.ajax({
                url: '/api/devicemonitor/devices/pingdevice',
                type: 'POST',
                data: { mac: mac, ip: ip },
                success: function(r) {
                    $btn.prop('disabled', false).html('<i class="fa fa-plug"></i>');
                    if (r.result === 'online') {
                        showToast(ip + ' ONLINE', 'success');
                    } else if (r.result === 'offline') {
                        showToast(ip + ' OFFLINE', 'error');
                    }
                    loadDevices();
                },
                error: function() {
                    $btn.prop('disabled', false).html('<i class="fa fa-plug"></i>');
                    showToast('Ping failed', 'error');
                }
            });
        });
    }

    // Inline edit friendly name
    $(document).on('click','.friendly-name-display',function(){
        var $span=$(this);
        if ($span.find('input').length) return;
        var mac=$span.data('mac');
        var cur=$span.attr('data-friendly') || '';
        var $inp=$('<input type="text" class="form-control input-sm">').val(cur).css({width:'150px',display:'inline-block'});
        $span.html($inp);
        $inp.focus().select();
        function save(){
            var value=$inp.val().trim();
            $.ajax({url:'/api/devicemonitor/devices/updatehostname',type:'POST',
                data:{mac:mac,hostname:value},
                success:function(r){
                    var message = r.result==='saved'
                        ? (value ? translations.hostname_saved : translations.hostname_cleared)
                        : translations.hostname_error;
                    showToast(message, r.result==='saved'?'success':'error');
                    loadDevices();
                }
            });
        }
        $inp.on('keydown',function(e){
            if(e.key==='Enter') save();
            if(e.key==='Escape') loadDevices();
        }).on('blur',function(){ setTimeout(save,150); });
    });

    // Column sorting
    $(document).on('click', 'th.sortable', function() {
        var col = $(this).data('col');
        if (sortCol === col) {
            sortDir = sortDir === 'asc' ? 'desc' : 'asc';
        } else {
            sortCol = col;
            sortDir = 'asc';
        }
        applyFilters();
    });
    
    // Toolbar
    $('#filter-status').on('change',function(){ activeStatus=$(this).val(); applyFilters(); });

    $('#btn-refresh').on('click',function(){ loadDevices(); });


    $('#btn-scan-now').on('click', function() {
        var $btn = $(this);
        $btn.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i>');
        $.ajax({ url: '/api/devicemonitor/service/scan', type: 'POST',
            success: function() {
                setTimeout(function() {
                    loadDevices();
                    $btn.prop('disabled', false).html('<i class="fa fa-search"></i>');
                }, 3000);
            },
            error: function() {
                $btn.prop('disabled', false).html('<i class="fa fa-search"></i>');
            }
        });
    });

    // CSV export respects the current filter
    $('#btn-export').on('click', function() {
        // Use the currently displayed filtered data
        var filtered = allRows.filter(function(r) {
            var vo = !activeVlans.length || activeVlans.indexOf(r.vlan) !== -1;
            var so = !activeStatus || r.status === activeStatus;
            return vo && so;
        });

        if (!filtered.length) {
            showToast('No data to export', 'error');
            return;
        }

        // Headers
        var cols = ['mac', 'ip', 'custom_hostname', 'hostname', 'hostname_source', 'vendor', 'vlan', 'status', 'first_seen', 'last_seen'];
        var headers = ['MAC Address', 'IP Address', 'Friendly Name', 'Hostname', 'Hostname Source', 'Vendor', 'VLAN', 'Status', 'First Seen', 'Last Seen'];

        var csv = headers.join(';') + '\n';
        filtered.forEach(function(row) {
            var line = cols.map(function(c) {
                var val = (row[c] || '').toString();
                if (c === 'hostname_source') {
                    val = hostnameSourceLabel(row.hostname_source || '');
                }
                // Add the VLAN description
                if (c === 'vlan' && row.vlan && vlanNames[row.vlan]) {
                    val = row.vlan + ' - ' + vlanNames[row.vlan];
                }
                // Escape semicolons and quotation marks
                val = val.replace(/"/g, '""');
                if (val.indexOf(';') !== -1 || val.indexOf('"') !== -1) {
                    val = '"' + val + '"';
                }
                return val;
            }).join(';');
            csv += line + '\n';
        });

        // Add BOM for correct display in Excel
        var bom = '\uFEFF';
        var blob = new Blob([bom + csv], { type: 'text/csv;charset=utf-8;' });
        var url  = URL.createObjectURL(blob);

        // Create a filename containing the date and active filter
        var date    = new Date().toISOString().slice(0,10);
        var vlanPart = activeVlans.length === 1 ? '_' + activeVlans[0] : (activeVlans.length > 1 ? '_multi' : '_all');
        var filename = 'device_monitor_' + date + vlanPart + '.csv';

        var $a = $('<a>').attr({href: url, download: filename}).css('display','none');
        $('body').append($a);
        $a[0].click();
        $a.remove();
        URL.revokeObjectURL(url);

        showToast('Exported ' + filtered.length + ' devices', 'success');
    });

    $('#btn-clear').on('click',function(){
        if (!confirm(translations.confirm_clear)) return;
        $.ajax({url:'/api/devicemonitor/devices/clear',type:'POST',
            success:function(r){
                showToast(r.result==='cleared'?translations.db_cleared:translations.db_clear_error,
                          r.result==='cleared'?'success':'error');
                loadDevices();
            }
        });
    });

    // Stable sticky header: pin the summary + toolbar block and the column
    // headings beneath the OPNsense fixed top navbar. Offsets are derived from
    // live measurements of the fixed navbar and the sticky block, and are
    // refreshed on load, resize and genuine toolbar-height changes. No
    // scroll-snap, pseudo-element shield or cached one-shot geometry is used,
    // and measuring never triggers a table render.
    function opaqueDevicesBackground($el) {
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

    function syncDevicesStickyHeader() {
        var header = document.getElementById('devices-sticky-header');
        if (!header) {
            return;
        }

        var pageHead = document.querySelector('.page-head');
        var navbarHeight = pageHead ? pageHead.offsetHeight : 62;
        var headerHeight = header.offsetHeight;

        document.documentElement.style.setProperty(
            '--devices-sticky-top',
            navbarHeight + 'px'
        );
        document.documentElement.style.setProperty(
            '--devices-sticky-thead-top',
            (navbarHeight + headerHeight) + 'px'
        );

        var $header = $(header);
        $header.css('background-color', opaqueDevicesBackground($header));

        var $thead = $('#grid-devices thead th');
        var theadBg = opaqueDevicesBackground($thead);
        $thead.css('background-color', theadBg);
        $('#grid-devices thead').css('background-color', theadBg);
    }

    $(window).on('resize', syncDevicesStickyHeader);
    syncDevicesStickyHeader();

    if (window.ResizeObserver) {
        var dmStickyHeaderEl = document.getElementById('devices-sticky-header');
        if (dmStickyHeaderEl) {
            new ResizeObserver(syncDevicesStickyHeader).observe(
                dmStickyHeaderEl
            );
        }
    }

    // Initialise by loading interface labels before devices

    $.ajax({url:'/api/devicemonitor/config/getinterfaces',type:'GET',
        success:function(data){ vlanNames=data||{}; loadDevices(); },
        error:function(){ loadDevices(); }
    });
    setInterval(function(){ loadDevices(); },30000);
});
</script>
