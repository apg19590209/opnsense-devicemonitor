<div class="content-box">
    <div class="content-box-main">

        <!-- Header with version and statistics -->
        <div style="padding:10px 10px 8px 10px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;border-bottom:1px solid #333;margin-bottom:12px;">
            <h1 style="margin:0;font-size:20px;">
                {{ lang._('Device Monitor') }}
                <small id="plugin-version" style="font-size:13px;color:#888;margin-left:5px;"></small>
                <span style="color:#555;margin:0 8px;">–</span>
                <span style="font-weight:normal;">{{ lang._('Devices') }}</span>
            </h1>
            <div style="display:flex;gap:20px;align-items:center;">
                <span style="font-size:13px;color:#888;">
                    {{ lang._('Total Devices') }}:
                    <strong id="stat-total" style="color:#ccc;font-size:16px;margin-left:4px;">—</strong>
                </span>
                <span style="font-size:13px;color:#888;">
                    {{ lang._('Online') }}:
                    <strong id="stat-online" style="color:#4CAF50;font-size:16px;margin-left:4px;">—</strong>
                </span>
            </div>
        </div>

        <!-- Toolbar -->
        <div style="padding:0 4px 12px 4px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">

            <!-- Multi-select VLAN dropdown -->
            <div class="dropdown" id="vlan-filter-wrapper" style="display:inline-block;">
                <button type="button" class="btn btn-default dropdown-toggle"
                        id="vlan-dropdown-toggle" data-toggle="dropdown"
                        style="min-width:160px;text-align:left;">
                    <span id="vlan-filter-label">{{ lang._('All VLANs') }}</span>
                    <span class="caret" style="float:right;margin-top:7px;"></span>
                </button>
                <ul class="dropdown-menu" id="vlan-checklist"
                    style="min-width:240px;padding:4px 0;max-height:300px;overflow-y:auto;">
                </ul>
            </div>

            <!-- Status filtr -->
            <select id="filter-status" class="form-control" style="width:auto;min-width:130px;">
                <option value="">{{ lang._('All statuses') }}</option>
                <option value="online">🟢 Online</option>
                <option value="offline">⚫ Offline</option>
            </select>

            <button id="btn-refresh" class="btn btn-default" title="{{ lang._('Refresh') }}">
                <i class="fa fa-refresh"></i>
            </button>

            <button id="btn-scan-now" class="btn btn-default" title="{{ lang._('Run scan now') }}">
                <i class="fa fa-search"></i>
            </button>

            <button id="btn-export" class="btn btn-default" title="{{ lang._('Export to CSV') }}">
                <i class="fa fa-download"></i>
            </button>

            <div style="flex-grow:1;"></div>

            <button id="btn-clear" class="btn btn-danger">
                <i class="fa fa-trash"></i> {{ lang._('Clear Database') }}
            </button>
        </div>

        <!-- Tabulka -->
        <table class="table table-condensed table-hover table-striped" id="grid-devices" style="margin-top:0;border-top:2px solid #444;">
            <thead>
                <tr>
                    <th class="sortable" data-col="mac" style="cursor:pointer;white-space:nowrap;">{{ lang._('MAC Address') }} <i class="fa fa-sort"></i></th>
                    <th class="sortable" data-col="ip" style="cursor:pointer;white-space:nowrap;">{{ lang._('IP Address') }} <i class="fa fa-sort"></i></th>
                    <th class="sortable" data-col="hostname" style="cursor:pointer;white-space:nowrap;">{{ lang._('Hostname') }} <i class="fa fa-sort"></i></th>
                    <th class="sortable" data-col="vendor" style="cursor:pointer;white-space:nowrap;">{{ lang._('Vendor') }} <i class="fa fa-sort"></i></th>
                    <th class="sortable" data-col="vlan" style="cursor:pointer;white-space:nowrap;">{{ lang._('VLAN') }} <i class="fa fa-sort"></i></th>
                    <th class="sortable" data-col="status" style="cursor:pointer;white-space:nowrap;">{{ lang._('Status') }} <i class="fa fa-sort"></i></th>
                    <th class="sortable" data-col="nmap_scan_status" style="cursor:pointer;white-space:nowrap;">{{ lang._('Scan Status') }} <i class="fa fa-sort"></i></th>
                    <th class="sortable" data-col="last_seen" style="cursor:pointer;white-space:nowrap;">{{ lang._('Last Seen') }} <i class="fa fa-sort"></i></th>
                    <th style="white-space:nowrap;">{{ lang._('Actions') }}</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>

        <div class="panel panel-default" style="margin-top:20px;">
            <div class="panel-heading" style="display:flex;align-items:center;justify-content:space-between;">
                <strong style="font-size:13px;">
                    <i class="fa fa-history"></i>
                    {{ lang._('Nmap Scan History') }}
                    <span id="scan-history-total" class="badge" style="margin-left:6px;">0</span>
                </strong>

                <div style="display:flex;align-items:center;gap:8px;white-space:nowrap;">
                    <label for="scan-history-limit"
                           style="margin:0;display:inline-flex;align-items:center;height:28px;font-size:12px;font-weight:600;white-space:nowrap;">
                        {{ lang._('Rows') }}
                    </label>

                    <select id="scan-history-limit"
                            class="form-control input-sm"
                            style="width:70px;height:28px;padding:0 24px 0 8px;margin:0;display:inline-block;vertical-align:middle;line-height:26px;">
                        <option value="10" selected>10</option>
                        <option value="25">25</option>
                        <option value="50">50</option>
                        <option value="100">100</option>
                    </select>

                    <button id="btn-history-refresh"
                            class="btn btn-xs btn-default" style="height:28px;min-width:28px;padding:0 8px;display:inline-flex;align-items:center;justify-content:center;vertical-align:middle;"
                            title="{{ lang._('Refresh scan history') }}">
                        <i class="fa fa-refresh"></i>
                    </button>
                </div>
            </div>

            <div id="scan-history-scroll"
                 class="table-responsive"
                 style="max-height:360px;overflow-y:auto;">
                <table class="table table-condensed table-hover table-striped"
                       id="grid-scan-history"
                       style="margin-bottom:0;">
                    <thead>
                        <tr>
                            <th>{{ lang._('Started') }}</th>
                            <th>{{ lang._('MAC Address') }}</th>
                            <th>{{ lang._('IP Address') }}</th>
                            <th>{{ lang._('Type') }}</th>
                            <th>{{ lang._('Status') }}</th>
                            <th>{{ lang._('Finished') }}</th>
                            <th>{{ lang._('Error') }}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td colspan="7" class="text-muted">
                                {{ lang._('Loading scan history...') }}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>


<style>
#grid-devices thead th,
#grid-scan-history thead th {
    font-size: 12px;
    font-weight: 600;
    vertical-align: middle;
    white-space: nowrap;
}

#grid-scan-history thead th {
    position: sticky;
    top: 0;
    z-index: 2;
    background: inherit;
}
</style>

<script>
$(document).ready(function() {

    var translations = {
        deleted:        '{{ lang._('Device deleted') }}',
        delete_error:   '{{ lang._('Error deleting device') }}',
        db_cleared:     '{{ lang._('Database cleared') }}',
        db_clear_error: '{{ lang._('Error clearing database') }}',
        hostname_saved: '{{ lang._('Hostname saved') }}',
        hostname_error: '{{ lang._('Error saving hostname') }}',
        confirm_delete: '{{ lang._('Delete device') }}',
        confirm_clear:  '{{ lang._('Really delete all devices from database?') }}',
        all_vlans:      '{{ lang._('All VLANs') }}'
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

    // Render table
    function renderTable(rows) {
        var $tbody = $('#grid-devices tbody').empty();
        rows.forEach(function(row) {
            var statusHtml = row.status==='online'
                ? '<span style="color:#4CAF50;font-weight:bold;white-space:nowrap;"><i class="fa fa-circle"></i> ONLINE</span>'
                : '<span style="color:#666;font-weight:bold;white-space:nowrap;"><i class="fa fa-circle-o"></i> OFFLINE</span>';

            var hn = row.hostname || '';
            var hostnameHtml = '<span class="hostname-display" data-mac="'+row.mac+'" title="Click to edit"'
                +' style="cursor:pointer;border-bottom:1px dashed #666;">'
                +(hn||'<em style="color:#555;">\u2014</em>')+'</span>';

            var ipHtml = row.ip
                ? '<a href="http://'+row.ip+'" target="_blank" style="color:#5bc0de;">'+row.ip+'</a>'
                : '';

            var vlanLabel = row.vlan||'';
            if (row.vlan && vlanNames[row.vlan]) vlanLabel += ' \u2013 '+vlanNames[row.vlan];

            $('<tr>').append(
                $('<td>').text(row.mac||''),
                $('<td>').html(ipHtml),
                $('<td>').html(hostnameHtml),
                $('<td>').text(row.vendor||''),
                $('<td>').text(vlanLabel),
                $('<td>').html(statusHtml),
                buildScanStatusCell(row),
                $('<td>').text(row.last_seen||''),
                $('<td>').html('<button class="btn btn-xs btn-warning command-check" data-row-mac="'+row.mac+'" data-row-ip="'+row.ip+'" title="Check online" style="margin-right:2px;"><i class="fa fa-plug"></i></button>' +
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

    function renderScanHistory(rows) {
        var $tbody = $('#grid-scan-history tbody').empty();

        if (!rows.length) {
            $('<tr>').append(
                $('<td>')
                    .attr('colspan', 7)
                    .addClass('text-muted')
                    .text('No targeted Nmap scan history recorded')
            ).appendTo($tbody);
            return;
        }

        rows.forEach(function(row) {
            var statusHtml;

            if (row.success === 1 || row.success === '1') {
                statusHtml =
                    '<span style="color:#4CAF50;font-weight:bold;white-space:nowrap;">' +
                    '<i class="fa fa-check-circle"></i> Success</span>';
            } else if (row.success === 0 || row.success === '0') {
                statusHtml =
                    '<span style="color:#d9534f;font-weight:bold;white-space:nowrap;">' +
                    '<i class="fa fa-exclamation-circle"></i> Failed</span>';
            } else {
                statusHtml =
                    '<span style="color:#f0ad4e;font-weight:bold;white-space:nowrap;">' +
                    '<i class="fa fa-minus-circle"></i> Incomplete</span>';
            }

            var typeHtml = row.scan_type === 'manual'
                ? '<span class="label label-info">Manual</span>'
                : '<span class="label label-default">Automatic</span>';

            var errorText = row.error || '';

            $('<tr>').append(
                $('<td>').text(row.started_at || ''),
                $('<td>').text(row.mac || ''),
                $('<td>').text(row.ip || ''),
                $('<td>').html(typeHtml),
                $('<td>').html(statusHtml),
                $('<td>').text(row.finished_at || '\u2014'),
                $('<td>')
                    .text(errorText || '\u2014')
                    .attr('title', errorText)
                    .css({
                        'max-width': '320px',
                        'white-space': 'nowrap',
                        'overflow': 'hidden',
                        'text-overflow': 'ellipsis'
                    })
            ).appendTo($tbody);
        });
    }


    function loadScanHistory() {
        var limit = parseInt($('#scan-history-limit').val(), 10) || 10;

        $.ajax({
            url: '/api/devicemonitor/devices/scanhistory',
            type: 'GET',
            data: { limit: limit },
            success: function(data) {
                $('#scan-history-total').text(data.total || 0);
                renderScanHistory(data.rows || []);
            },
            error: function() {
                $('#scan-history-total').text('?');

                $('#grid-scan-history tbody').empty().append(
                    $('<tr>').append(
                        $('<td>')
                            .attr('colspan', 7)
                            .addClass('text-danger')
                            .text('Unable to load Nmap scan history')
                    )
                );
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

    // Inline editace hostname
    $(document).on('click','.hostname-display',function(){
        var $span=$(this);
        if ($span.find('input').length) return;
        var mac=$span.data('mac');
        var cur=$span.text().trim();
        if (cur==='\u2014') cur='';
        var $inp=$('<input type="text" class="form-control input-sm">').val(cur).css({width:'150px',display:'inline-block'});
        $span.html($inp);
        $inp.focus().select();
        function save(){
            $.ajax({url:'/api/devicemonitor/devices/updatehostname',type:'POST',
                data:{mac:mac,hostname:$inp.val().trim()},
                success:function(r){
                    showToast(r.result==='saved'?translations.hostname_saved:translations.hostname_error,
                              r.result==='saved'?'success':'error');
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

    $('#btn-refresh').on('click',function(){ loadDevices(); loadStats(); loadScanHistory(); });

    $('#btn-history-refresh').on('click', function() {
        loadScanHistory();
    });

    $('#scan-history-limit').on('change', function() {
        loadScanHistory();
    });

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
        var cols = ['mac', 'ip', 'hostname', 'vendor', 'vlan', 'status', 'last_seen'];
        var headers = ['MAC Address', 'IP Address', 'Hostname', 'Vendor', 'VLAN', 'Status', 'Last Seen'];

        var csv = headers.join(';') + '\n';
        filtered.forEach(function(row) {
            var line = cols.map(function(c) {
                var val = (row[c] || '').toString();
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

    // Initialize by loading interface labels before devices
    $.ajax({url:'/api/devicemonitor/config/getinterfaces',type:'GET',
        success:function(data){ vlanNames=data||{}; loadDevices(); },
        error:function(){ loadDevices(); }
    });
    loadStats();
    loadScanHistory();

    setInterval(function(){
        loadDevices();
        loadStats();
        loadScanHistory();
    },30000);
});
</script>
