<style>
    /* Email Log only: align the type/status dropdowns, the search field and the
     * Export button on one baseline. Bootstrap's small select renders text on the
     * box edge in some themes; an explicit height with vertical centring fixes the
     * default label ("All types") and selected values ("Failed") alike. The rules
     * are scoped to this page's controls and change no shared OPNsense style. */
    #email-log-search,
    #email-log-type,
    #email-log-status,
    #email-log-export {
        height: 30px;
        line-height: 1.42857143;
        padding-top: 5px;
        padding-bottom: 5px;
        box-sizing: border-box;
    }
    #email-log-type,
    #email-log-status {
        /* Native selects ignore line-height in some engines; align the text box. */
        padding-top: 0;
        padding-bottom: 0;
        vertical-align: middle;
    }
    #email-log-export {
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }
</style>

<div class="content-box">
    <div class="content-box-main">

        <div class="panel panel-default">
            <div class="panel-heading">
                <strong style="font-size:13px;">
                    <i class="fa fa-envelope"></i>
                    {{ devicemonitor_t('Email Log') }}
                </strong>
                <span id="email-log-node" class="text-muted" style="margin-left:8px;font-size:12px;"></span>
            </div>

            <div class="panel-body">
                <ul class="nav nav-tabs" role="tablist">
                    <li role="presentation" class="active">
                        <a href="#email-log-local" role="tab" data-toggle="tab">{{ devicemonitor_t('Local') }}</a>
                    </li>
                    <li role="presentation" class="disabled" title="{{ devicemonitor_t('Peer aggregation is not implemented yet') }}">
                        <a href="#email-log-peer" role="tab" aria-disabled="true">{{ devicemonitor_t('Peer') }}</a>
                    </li>
                    <li role="presentation" class="disabled" title="{{ devicemonitor_t('Peer aggregation is not implemented yet') }}">
                        <a href="#email-log-all" role="tab" aria-disabled="true">{{ devicemonitor_t('All nodes') }}</a>
                    </li>
                </ul>

                <div class="tab-content" style="padding-top:12px;">
                    <div role="tabpanel" class="tab-pane active" id="email-log-local">
                        <div class="alert alert-info" id="email-log-scope-note" style="font-size:12px;">
                            {{ devicemonitor_t('This view shows only the email log of the local node. Peer aggregation is not available in this release.') }}
                        </div>
                        <div class="alert alert-warning" id="email-log-diagnostic" style="display:none;font-size:12px;"></div>

                        <div class="row" style="margin-bottom:10px;">
                            <div class="col-sm-4">
                                <input type="text" id="email-log-search" class="form-control input-sm"
                                       placeholder="{{ devicemonitor_t('Search subject or recipient') }}">
                            </div>
                            <div class="col-sm-3">
                                <select id="email-log-type" class="form-control input-sm">
                                    <option value="">{{ devicemonitor_t('All types') }}</option>
                                    <option value="test">{{ devicemonitor_t('Test') }}</option>
                                    <option value="new_device">{{ devicemonitor_t('New device') }}</option>
                                    <option value="scan_result">{{ devicemonitor_t('Scan result') }}</option>
                                    <option value="failover">{{ devicemonitor_t('Failover') }}</option>
                                    <option value="service">{{ devicemonitor_t('Service alert') }}</option>
                                </select>
                            </div>
                            <div class="col-sm-3">
                                <select id="email-log-status" class="form-control input-sm">
                                    <option value="">{{ devicemonitor_t('All statuses') }}</option>
                                    <option value="submitted">{{ devicemonitor_t('Submitted') }}</option>
                                    <option value="queued">{{ devicemonitor_t('Queued or deferred') }}</option>
                                    <option value="accepted">{{ devicemonitor_t('Relay accepted') }}</option>
                                    <option value="failed">{{ devicemonitor_t('Failed') }}</option>
                                    <option value="unknown">{{ devicemonitor_t('Unknown') }}</option>
                                </select>
                            </div>
                            <div class="col-sm-2">
                                <button id="email-log-export" class="btn btn-default btn-sm">
                                    <i class="fa fa-download"></i> {{ devicemonitor_t('Export CSV') }}
                                </button>
                            </div>
                        </div>

                        <table class="table table-condensed table-hover" id="email-log-table">
                            <thead>
                            <tr>
                                <th>{{ devicemonitor_t('Time (UTC)') }}</th>
                                <th>{{ devicemonitor_t('Node') }}</th>
                                <th>{{ devicemonitor_t('Type') }}</th>
                                <th>{{ devicemonitor_t('Recipient') }}</th>
                                <th>{{ devicemonitor_t('Subject') }}</th>
                                <th>{{ devicemonitor_t('Status') }}</th>
                                <th></th>
                            </tr>
                            </thead>
                            <tbody id="email-log-rows"></tbody>
                        </table>
                        <p class="text-muted" id="email-log-empty" style="display:none;">
                            {{ devicemonitor_t('No email records in the retention window.') }}
                        </p>
                        <div class="clearfix">
                            <button id="email-log-prev" class="btn btn-default btn-xs pull-left">
                                {{ devicemonitor_t('Previous') }}
                            </button>
                            <button id="email-log-next" class="btn btn-default btn-xs pull-right">
                                {{ devicemonitor_t('Next') }}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    function emailLogText() {
        return {
            relayAcceptedNotice: {{ lang.query('Relay acceptance is not proof that the message reached the recipient inbox.')|json_encode(15) }},
            diagnostics: {{ lang.query('Timeline')|json_encode(15) }},
            role: {{ lang.query('Role')|json_encode(15) }},
            ip: {{ lang.query('Node address')|json_encode(15) }},
            unknown: {{ lang.query('Unknown')|json_encode(15) }},
            loadFailed: {{ lang.query('Could not load the email log')|json_encode(15) }}
        };
    }

    (function () {
        var page = 1;
        var perPage = 50;
        var text = emailLogText();

        function esc(value) {
            return $('<div>').text(value === undefined || value === null ? '' : value).html();
        }

        function load() {
            $.ajax({
                url: '/api/devicemonitor/emaillog/search',
                type: 'POST',
                dataType: 'json',
                data: {
                    page: page,
                    per_page: perPage,
                    type: $('#email-log-type').val(),
                    status: $('#email-log-status').val(),
                    search: $('#email-log-search').val()
                }
            }).fail(function (xhr) {
                // A failed request must be visible, never an empty table.
                $('#email-log-empty').hide();
                $('#email-log-diagnostic')
                    .show()
                    .text(text.loadFailed + ' (HTTP ' + (xhr && xhr.status ? xhr.status : '?') + ')');
            }).done(function (data) {
                if (!data || data.result !== 'ok') {
                    $('#email-log-empty').hide();
                    $('#email-log-diagnostic').show().text(text.loadFailed);
                    return;
                }
                var rows = data.rows || [];
                var $body = $('#email-log-rows').empty();
                $('#email-log-node').text((data.node.node_id || '') + ' ' + (data.node.node_ip || '') +
                    (data.node.role ? ' (' + data.node.role + ')' : ''));
                if (data.logging_diagnostic) {
                    $('#email-log-diagnostic').show().text(data.logging_diagnostic);
                } else {
                    $('#email-log-diagnostic').hide();
                }
                rows.forEach(function (row) {
                    var $tr = $('<tr>');
                    $tr.append($('<td>').text(row.created_utc));
                    $tr.append($('<td>').text(row.node_ip + ' ' + row.node_role));
                    $tr.append($('<td>').text(row.notification_type));
                    $tr.append($('<td>').text(row.recipient));
                    $tr.append($('<td>').text(row.subject));
                    $tr.append($('<td>').text(row.status));
                    var $detail = $('<td>');
                    $('<button>').addClass('btn btn-default btn-xs')
                        .text(text.diagnostics)
                        .on('click', function () { $(this).closest('tr').next().toggle(); })
                        .appendTo($detail);
                    $tr.append($detail);
                    $body.append($tr);
                    var $timeline = $('<tr>').hide();
                    var $cell = $('<td>').attr('colspan', 7).css('font-size', '12px');
                    var steps = row.timeline || [];
                    if (steps.length === 0) {
                        $cell.append($('<div>').addClass('text-muted').text(text.unknown));
                    }
                    steps.forEach(function (step) {
                        var $line = $('<div>');
                        $line.append($('<span>').css('font-family', 'monospace').text(step.occurred_utc + '  '));
                        $line.append($('<strong>').text(step.stage + ': '));
                        $line.append($('<span>').text(step.status));
                        if (step.detail) { $line.append(document.createTextNode(' — ' + step.detail)); }
                        if (step.source) {
                            $line.append($('<span>').addClass('text-muted').text(' [' + step.source + ']'));
                        }
                        $cell.append($line);
                    });
                    if (row.status === 'accepted') {
                        $cell.append($('<div>').addClass('text-muted').text(text.relayAcceptedNotice));
                    }
                    $cell.append($('<div>').text('Queue ID: ' + (row.queue_id || text.unknown)));
                    $timeline.append($cell);
                    $body.append($timeline);
                });
                $('#email-log-empty').toggle(rows.length === 0);
                $('#email-log-prev').prop('disabled', page === 1);
                $('#email-log-next').prop('disabled', rows.length < perPage);
            });
        }

        $('#email-log-type, #email-log-status').on('change', function () { page = 1; load(); });
        $('#email-log-search').on('input', function () { page = 1; load(); });
        $('#email-log-prev').on('click', function () { if (page > 1) { page--; load(); } });
        $('#email-log-next').on('click', function () { page++; load(); });
        $('#email-log-export').on('click', function () {
            $.ajax({
                url: '/api/devicemonitor/emaillog/exportcsv',
                type: 'POST',
                dataType: 'json'
            }).done(function (data) {
                if (data.result !== 'ok') { return; }
                var blob = new Blob([data.csv], { type: 'text/csv;charset=utf-8' });
                var link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = 'devicemonitor-email-log.csv';
                link.click();
                URL.revokeObjectURL(link.href);
            });
        });
        /* The layout installs its CSRF header hook inside $(document).ready
         * ($.ajaxSetup). Firing load() synchronously here would send the first
         * request before that hook exists, so the API answers 403. Defer to
         * ready so every request carries X-CSRFToken, like the other pages. */
        $(document).ready(function () {
            load();
        });
    })();
</script>
