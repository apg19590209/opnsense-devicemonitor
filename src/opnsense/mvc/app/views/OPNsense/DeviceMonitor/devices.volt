<div class="content-box">
    <div class="content-box-main">

        <!-- Header with version and statistics -->
        <div id="devices-sticky-summary" class="devices-header">
            <h1>
                {{ lang._('Device Monitor') }}
                <small id="plugin-version"></small>
                <span class="devices-divider">&ndash;</span>
                <span class="devices-title">{{ lang._('Devices') }}</span>
            </h1>
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

            <!-- Status filtr -->
            <select id="filter-status" class="form-control input-sm">
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

        <!-- Tabulka -->
        <table class="table table-condensed table-hover table-striped devices-table" id="grid-devices">
            <thead>
                <tr>
                    <th class="sortable devices-table-header" data-col="mac">{{ lang._('MAC Address') }} <i class="fa fa-sort"></i></th>
                    <th class="sortable devices-table-header" data-col="ip">{{ lang._('IP Address') }} <i class="fa fa-sort"></i></th>
                    <th class="sortable devices-table-header" data-col="custom_hostname">{{ lang._('Friendly Name') }} <i class="fa fa-sort"></i></th>
                    <th class="sortable devices-table-header" data-col="hostname">{{ lang._('Hostname') }} <i class="fa fa-sort"></i></th>
                    <th class="sortable devices-table-header" data-col="vendor">{{ lang._('Vendor') }} <i class="fa fa-sort"></i></th>                    <th class="devices-table-header">{{ lang._('Services') }}</th>

                    <th class="sortable devices-table-header" data-col="vlan">{{ lang._('VLAN') }} <i class="fa fa-sort"></i></th>
                    <th class="sortable devices-table-header" data-col="status">{{ lang._('Status') }} <i class="fa fa-sort"></i></th>
                    <th class="devices-table-header">{{ lang._('Physical Device') }}</th>
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
    font-size: 12px;
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
.devices-toolbar .form-control {
    width: auto;
    min-width: 130px;
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
    top: 100px;
    z-index: 10;
}
#grid-devices tbody tr {
    scroll-snap-align: start;
}
#devices-sticky-summary {
    position: sticky;
    z-index: 30;
}
#devices-sticky-summary::before,
#devices-sticky-summary::after {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    background-color: inherit;
    pointer-events: none;
}
#devices-sticky-summary::before {
    top: -15px;
    height: 15px;
}
#devices-sticky-summary::after {
    bottom: -12px;
    height: 12px;
}
#devices-sticky-toolbar {
    position: sticky;
    top: 50px;
    z-index: 20;
    padding: 12px 4px 12px 4px;
    margin: 0;
    border-bottom: 1px solid #333;
}
main.page-content > .row {
    height: auto;
    min-height: 100%;
}
header.page-content-head {
    position: sticky;
    top: 0;
    z-index: 30;
}
</style>

<script>
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
        grouped:        '{{ lang._('Grouped') }}',
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

    // Verze + statistiky
    $.getJSON('/api/devicemonitor/config/getversion', function(d) {
        $('#plugin-version').text('v'+(d.version||'?'));
    });

    function loadStats() {
        $.ajax({url:'/api/devicemonitor/devices/stats',type:'GET',success:function(d){
            $('#stat-total').text(d.total||0);
            $('#stat-online').text(d.online||0);
        }});
    }

    // VLAN multi-select dropdown
    function buildVlanDropdown(vlans) {
        var $list = $('#vlan-checklist').empty();
        if (!vlans.length) return;
        var allSel = (activeVlans.length === 0);

        $list.append($('<li>').append(
            $('<a>').attr('href','#').css({padding:'5px 14px',display:'flex',alignItems:'center',justifyContent:'space-between'}).append(
                $('<label>').css({margin:0,cursor:'pointer',display:'flex',alignItems:'center',gap:'6px'}).append(
                    $('<input type="checkbox" id="vlan-all">').prop('checked', allSel),
                    $('<span>').css({'font-style':'italic'}).text(translations.all_vlans)
                ),
                $('<a>').attr('href','#').addClass('vlan-select-none')
                    .css({fontSize:'11px',color:'#aaa',marginLeft:'12px',whiteSpace:'nowrap'})
                    .text('Select none')
                    .on('click', function(e){
                        e.preventDefault();
                        e.stopPropagation();
                        // Reset means all individual VLANs unchecked and All VLANs selected
                        $('#vlan-checklist .vlan-cb').prop('checked', false);
                        $('#vlan-all').prop('checked', true);
                        activeVlans = [];
                        try { localStorage.setItem('dm_vlan_filter', JSON.stringify([])); } catch(e2) {}
                        updateVlanLabel();
                        applyFilters();
                    })
            )
        ));

        $list.append($('<li class="divider" style="margin:4px 0;">'));

        vlans.sort().forEach(function(v) {
            var n = vlanNames[v];
            var label = (n && n !== v) ? (v+' \u2013 '+n) : v;
            var chk = allSel || (activeVlans.indexOf(v) !== -1);
            $list.append($('<li>').append(
                $('<a>').attr('href','#').css({padding:'4px 14px',display:'block'}).append(
                    $('<input type="checkbox" class="vlan-cb">').val(v).prop('checked', chk),
                    $('<span>').css('margin-left','8px').text(label)
                )
            ));
        });
        updateVlanLabel();
    }

    // Keep dropdown open when clicking a checkbox
    $('#vlan-checklist').on('click', function(e){ e.stopPropagation(); });

    $(document).on('change','#vlan-all',function(){
        $('#vlan-checklist .vlan-cb').prop('checked',$(this).prop('checked'));
        persistVlans();
    });
    $(document).on('change','#vlan-checklist .vlan-cb',function(){
        var total=$('#vlan-checklist .vlan-cb').length;
        var checked=$('#vlan-checklist .vlan-cb:checked').length;
        $('#vlan-all').prop('checked', total===checked);
        persistVlans();
    });

    function persistVlans() {
        var sel = [];
        var total = $('#vlan-checklist .vlan-cb').length;
        $('#vlan-checklist .vlan-cb:checked').each(function(){ sel.push($(this).val()); });

        if (sel.length === total || sel.length === 0) {
            // All selected or none selected means no filter
            activeVlans = [];
            $('#vlan-all').prop('checked', true);
        } else {
            activeVlans = sel;
            $('#vlan-all').prop('checked', false);
        }
        try { localStorage.setItem('dm_vlan_filter', JSON.stringify(activeVlans)); } catch(e) {}
        updateVlanLabel();
        applyFilters();
    }

    function updateVlanLabel() {
        if (!activeVlans.length) {
            $('#vlan-filter-label').text(translations.all_vlans);
        } else if (activeVlans.length===1) {
            var n=vlanNames[activeVlans[0]];
            $('#vlan-filter-label').text(activeVlans[0]+(n?' \u2013 '+n:''));
        } else {
            $('#vlan-filter-label').text(activeVlans.length+' VLANs');
        }
    }

    // Filtering
    function applyFilters() {
        if (!allRows || !allRows.length) return;
        var filtered = allRows.filter(function(r){
            var vo = !activeVlans.length || activeVlans.indexOf(r.vlan) !== -1;
            var so = !activeStatus || r.status === activeStatus;
            return vo && so;
        });
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

        renderTable(filtered);
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

        var label = groupName !== '' ? groupName : translations.grouped;
        label += ' \u00b7 ' + memberCount + ' ' +
            (memberCount === 1 ? translations.identity : translations.identities);

        return $cell.append(
            $('<a>')
                .addClass('label label-info devices-grouping-badge')
                .attr({
                    href: '/ui/devicemonitor/index/devicehistory?mac=' +
                        encodeURIComponent(row.mac || '') +
                        '#physical-device-grouping',
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
                $('<td>').text(row.mac||''),
                $('<td>').html(ipHtml),
                $friendlyCell,
                $hostnameCell,
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
                    loadDevices(); loadStats();
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

    $('#btn-refresh').on('click',function(){ loadDevices(); loadStats(); });


    $('#btn-scan-now').on('click', function() {
        var $btn = $(this);
        $btn.prop('disabled', true).html('<i class="fa fa-spinner fa-spin"></i>');
        $.ajax({ url: '/api/devicemonitor/service/scan', type: 'POST',
            success: function() {
                setTimeout(function() {
                    loadDevices(); loadStats();
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
                loadDevices(); loadStats();
            }
        });
    });

    // Keep toolbar and table header sticky while the device list scrolls.
    function updateStickyOffsets() {
        var shellHead = $('header.page-head');
        var pageHead = $('header.page-content-head');
        var contentMain = $('section.page-content-main');
        var summary = $('#devices-sticky-summary');
        var toolbar = $('#devices-sticky-toolbar');
        var thead = $('#grid-devices thead th');

        var top = shellHead.length ? shellHead.outerHeight() : 62;

        if (pageHead.length) {
            pageHead.css('top', top + 'px');
            top += pageHead.outerHeight();
        }

        if (contentMain.length) {
            top += parseInt(contentMain.css('padding-top'), 10) || 0;
            var bg = contentMain.css('background-color');
            summary.css('background-color', bg);
            toolbar.css('background-color', bg);
            thead.css('background-color', bg);
            $('#grid-devices thead').css('background-color', bg);
            var shield = '0 0 0 2px ' + bg;
            summary.css('box-shadow', shield);
            toolbar.css('box-shadow', shield);
            thead.css('box-shadow', shield);
        }

        if (summary.length) {
            summary.css('top', top + 'px');
            top += summary.outerHeight(true);
        }

        if (toolbar.length) {
            toolbar.css('top', top + 'px');
            top += toolbar.outerHeight(true);
        }

        thead.css('top', top + 'px');
        var scrollRoot = document.scrollingElement || document.documentElement;
        $(scrollRoot).css('scroll-snap-type', 'y proximity');
        $(scrollRoot).css('scroll-padding-top', (top + thead.first().outerHeight()) + 'px');
    }
    $(window).on('resize', updateStickyOffsets);
    setTimeout(updateStickyOffsets, 100);

    // Initialise by loading interface labels before devices

    $.ajax({url:'/api/devicemonitor/config/getinterfaces',type:'GET',
        success:function(data){ vlanNames=data||{}; loadDevices(); },
        error:function(){ loadDevices(); }
    });
    loadStats();
    setInterval(function(){ loadDevices(); loadStats(); },30000);
});
</script>
