<div class="content-box">
    <div class="content-box-main">

        <div style="padding:10px 10px 8px 10px;border-bottom:1px solid #333;margin-bottom:12px;">
            <h1 style="margin:0;font-size:20px;">
                {{ lang._('Device Monitor') }}
                <span style="color:#555;margin:0 8px;">–</span>
                <span style="font-weight:normal;">{{ lang._('Nmap Scan History') }}</span>
            </h1>
        </div>

        <div class="panel panel-default">
            <div class="panel-heading"
                 style="display:flex;align-items:center;justify-content:space-between;">

                <strong style="font-size:13px;">
                    <i class="fa fa-history"></i>
                    {{ lang._('Nmap Scan History') }}
                    <span id="scan-history-total"
                          class="badge"
                          style="margin-left:6px;">0</span>
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
                            class="btn btn-xs btn-default"
                            style="height:28px;min-width:28px;padding:0 8px;display:inline-flex;align-items:center;justify-content:center;vertical-align:middle;"
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
#grid-scan-history thead th {
    font-size: 12px;
    font-weight: 600;
    vertical-align: middle;
    white-space: nowrap;
    position: sticky;
    top: 0;
    z-index: 2;
    background: inherit;
}
</style>

<script>
$(document).ready(function() {

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

    $('#btn-history-refresh').on('click', function() {
        loadScanHistory();
    });

    $('#scan-history-limit').on('change', function() {
        loadScanHistory();
    });

    loadScanHistory();

    setInterval(function() {
        loadScanHistory();
    }, 30000);
});
</script>