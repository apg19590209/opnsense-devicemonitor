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
                    <li role="presentation">
                        <a href="#email-log-table" id="email-log-tab-peer" role="tab" data-toggle="tab"
                           data-scope="peer">{{ devicemonitor_t('Peer') }}</a>
                    </li>
                    <li role="presentation">
                        <a href="#email-log-table" id="email-log-tab-all" role="tab" data-toggle="tab"
                           data-scope="all">{{ devicemonitor_t('All nodes') }}</a>
                    </li>
                </ul>

                <div class="tab-content" style="padding-top:12px;">
                    <div role="tabpanel" class="tab-pane active" id="email-log-local">
                        <div class="alert alert-info" id="email-log-scope-note" style="font-size:12px;"></div>
                        <div class="alert alert-warning" id="email-log-partial" style="display:none;font-size:12px;"></div>
                        <div class="alert alert-warning" id="email-log-diagnostic" style="display:none;font-size:12px;"></div>

                        <div class="row" style="margin-bottom:10px;">
                            <div class="col-sm-4">
                                <input type="text" id="email-log-search" class="form-control input-sm"
                                       placeholder="{{ devicemonitor_t('Search subject or recipient') }}">
                            </div>
                            <div class="col-sm-3">
                                <select id="email-log-type" class="selectpicker"
                                            data-style="btn-default btn-sm" data-width="100%">
                                    <option value="">{{ devicemonitor_t('All types') }}</option>
                                    <option value="test">{{ devicemonitor_t('Test') }}</option>
                                    <option value="new_device">{{ devicemonitor_t('New device') }}</option>
                                    <option value="scan_result">{{ devicemonitor_t('Scan result') }}</option>
                                    <option value="failover">{{ devicemonitor_t('Failover') }}</option>
                                    <option value="service">{{ devicemonitor_t('Service alert') }}</option>
                                </select>
                            </div>
                            <div class="col-sm-3">
                                <select id="email-log-status" class="selectpicker"
                                            data-style="btn-default btn-sm" data-width="100%">
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

<style>
    /* Scoped to this dialog only. OPNsense main.css sets .modal-body padding:0,
     * so the padded body the design requires is supplied here. No fixed heights
     * and no nested scrolling: core's .modal-body already scrolls. */
    /* Dialog width: aim for 800px, never closer than 16px to the viewport edge. */
    #email-log-message-modal .modal-dialog {
        width: 800px;
        max-width: calc(100vw - 32px);
        margin: 16px auto;
    }
    #email-log-message-modal .modal-header {
        padding: 20px;
        /* Keep clear space between the subject and the close control. */
        position: relative;
        padding-right: 56px;
    }
    #email-log-message-modal .modal-header .modal-title {
        word-break: break-word;
        margin: 0;
    }
    #email-log-message-modal .email-log-dialog-body {
        padding: 24px;
    }
    #email-log-message-modal .email-log-dialog-meta {
        margin-bottom: 24px;
        word-break: break-word;
    }
    #email-log-message-modal .email-log-dialog-meta dt {
        font-weight: 600;
        margin-bottom: 0;
        /* 16px gap between the label column and its value. */
        width: 140px;
    }
    #email-log-message-modal .email-log-dialog-meta dd {
        word-break: break-word;
        margin-bottom: 8px;
        margin-left: 156px; /* 140px label + 16px gap */
    }
    #email-log-message-modal .email-log-dialog-meta dd:last-child {
        margin-bottom: 0;
    }
    /* Narrow screens: stack each label above its value. */
    @media (max-width: 767px) {
        /* Bootstrap floats dl-horizontal labels; unset it so the label sits above
         * its value instead of beside it. */
        #email-log-message-modal .email-log-dialog-meta dt {
            float: none;
            width: auto;
            text-align: left;
            margin-bottom: 2px;
        }
        #email-log-message-modal .email-log-dialog-meta dd {
            margin-left: 0;
        }
        #email-log-message-modal .modal-header {
            padding-right: 56px;
        }
    }
    #email-log-message-modal .email-log-dialog-heading {
        margin: 0 0 12px;
    }
    #email-log-message-modal .email-log-dialog-reading {
        padding: 20px;
        border: 1px solid #ddd;
        border-radius: 3px;
        background: #fbfbfb;
        margin-bottom: 24px;
    }
    #email-log-message-modal .email-log-dialog-reading pre {
        margin: 0;
        padding: 0;
        border: 0;
        background: transparent;
        font-family: inherit;
        font-size: inherit;
        line-height: 1.5;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
        word-break: break-word;
        max-height: none;
        overflow: visible;
    }
    #email-log-message-modal .email-log-dialog-delivery {
        margin-top: 0;
    }
    #email-log-message-modal .email-log-dialog-delivery summary {
        cursor: pointer;
        margin-top: 0;
    }
    #email-log-message-modal .email-log-dialog-delivery summary h4 {
        display: inline;
        font-size: 14px;
        margin: 0;
    }
    #email-log-message-modal .modal-footer {
        padding: 16px 24px;
    }
    #email-log-message-modal #email-log-message-timeline .email-log-event {
        padding: 6px 0;
        border-bottom: 1px solid #eee;
        word-break: break-word;
    }
    #email-log-message-modal #email-log-message-timeline .email-log-event:last-child {
        border-bottom: 0;
    }
</style>

{# Standard OPNsense dialog: same structure as core DialogAlias (Firewall/alias.volt). #}
<div class="modal fade" id="email-log-message-modal" tabindex="-1" role="dialog"
     aria-labelledby="email-log-message-title">
    <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <button type="button" class="close" data-dismiss="modal" aria-label="{{ lang.query('Close')|json_encode(15) }}">
                    <span aria-hidden="true">&times;</span>
                </button>
                {# The subject becomes the heading; the static label is only a fallback
                   that the script replaces before the dialog is shown. #}
                <h4 class="modal-title" id="email-log-message-title">{{ devicemonitor_t('Message') }}</h4>
            </div>
            <div class="modal-body email-log-dialog-body">
                <dl class="dl-horizontal email-log-dialog-meta" id="email-log-message-meta"></dl>
                <div class="alert alert-warning" id="email-log-message-unavailable" style="display:none;">
                    {{ devicemonitor_t('Message content unavailable') }}
                </div>
                <div class="alert alert-warning" id="email-log-message-truncated" style="display:none;">
                    {{ devicemonitor_t('Message content truncated for display') }}
                </div>
                <hr/>
                <h4 class="email-log-dialog-heading">{{ devicemonitor_t('Message content') }}</h4>
                {# Plain text only: .text() fills this, so no markup or remote content executes. #}
                <div class="email-log-dialog-reading">
                    <pre id="email-log-message-body"></pre>
                </div>
                <details id="email-log-message-timeline-disclosure" class="email-log-dialog-delivery">
                    <summary><h4>{{ devicemonitor_t('Delivery details') }}</h4></summary>
                    <div id="email-log-message-timeline"></div>
                </details>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal">{{ devicemonitor_t('Close') }}</button>
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
            loadFailed: {{ lang.query('Could not load the email log')|json_encode(15) }},
            viewMessage: {{ lang.query('View message')|json_encode(15) }},
            unavailable: {{ lang.query('Message content unavailable')|json_encode(15) }},
            truncated: {{ lang.query('Message content truncated for display')|json_encode(15) }},
            localOnly: {{ lang.query('This view shows only the email log of the local node.')|json_encode(15) }},
            peerNotConfigured: {{ lang.query('Peer is not configured. Add secure peer settings to enable combined views.')|json_encode(15) }},
            peerUnavailable: {{ lang.query('The peer could not be read. Only local records are shown.')|json_encode(15) }},
            peerOnly: {{ lang.query('Showing records from the configured peer.')|json_encode(15) }},
            allNodes: {{ lang.query('Showing records from this node and the configured peer.')|json_encode(15) }},
            partialData: {{ lang.query('Incomplete data:')|json_encode(15) }},
            viewFailed: {{ lang.query('Could not load this message')|json_encode(15) }}
        };
    }

    (function () {
        var page = 1;
        var perPage = 50;
        var text = emailLogText();

        function esc(value) {
            return $('<div>').text(value === undefined || value === null ? '' : value).html();
        }

        var scope = 'local';

        function setScopeNote(data) {
            var $note = $('#email-log-scope-note');
            var $partial = $('#email-log-partial').hide();
            if (scope === 'local') {
                $note.text(text.localOnly);
                return;
            }
            if (scope === 'peer') {
                if (data.peer_enabled === false) {
                    $note.text(text.peerNotConfigured);
                } else if (data.peer && data.peer.status === 'unavailable') {
                    $note.text(text.peerUnavailable);
                    $partial.show().text(data.peer.reason || text.peerUnavailable);
                } else {
                    $note.text(text.peerOnly);
                }
                return;
            }
            // All nodes: the local half is always shown, the peer half may be missing.
            $note.text(text.allNodes);
            if (data.partial) {
                $partial.show().text(text.partialData + ' ' + (data.peer && data.peer.reason ? data.peer.reason : ''));
            }
        }

        function load() {
            var url = scope === 'local'
                ? '/api/devicemonitor/emaillog/search'
                : '/api/devicemonitor/emaillog/combined';
            $.ajax({
                url: url,
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
                if (scope !== 'local') {
                    setScopeNote(data);
                } else {
                    $('#email-log-partial').hide();
                    $('#email-log-scope-note').text(text.localOnly);
                }
                var allRows = data.rows || [];
                var rows = allRows.filter(function (r) {
                    if (scope === 'peer') { return r.scope === 'peer'; }
                    return true;
                });
                var $body = $('#email-log-rows').empty();
                if (scope === 'local' && data.node) {
                    $('#email-log-node').text((data.node.node_id || '') + ' ' + (data.node.node_ip || '') +
                        (data.node.role ? ' (' + data.node.role + ')' : ''));
                } else {
                    $('#email-log-node').text(data.local_node ? (data.local_node.node_id || '') : '');
                }
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
                    /* Always offered, even for rows recorded before capture: the modal
                     * then explains that the content is unavailable rather than the
                     * action disappearing without explanation. */
                    $('<button>').addClass('btn btn-default btn-xs')
                        .css('margin-left', '4px')
                        .attr('data-event-id', row.event_id)
                        .attr('aria-label', text.viewMessage)
                        .text(text.viewMessage)
                        .on('click', function () { openMessage(row.event_id); })
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

        function openMessage(eventId, fromPeer) {
            $.ajax({
                url: fromPeer
                    ? '/api/devicemonitor/emaillog/peermessageview'
                    : '/api/devicemonitor/emaillog/message',
                type: 'POST',
                dataType: 'json',
                data: { event_id: eventId }
            }).fail(function (xhr) {
                $('#email-log-diagnostic').show()
                    .text(text.loadFailed + ' (HTTP ' + (xhr && xhr.status ? xhr.status : '?') + ')');
            }).done(function (data) {
                if (!data || data.result !== 'ok' || !data.message) {
                    $('#email-log-diagnostic').show().text(fromPeer ? text.viewFailed : text.loadFailed);
                    return;
                }
                var m = data.message;
                $('#email-log-message-title').text(m.subject || text.unknown);
                var $meta = $('#email-log-message-meta').empty();
                [['Recipient', m.recipient],
                 ['Node', m.node_ip + (m.node_role ? ' (' + m.node_role + ')' : '')],
                 ['Time (UTC)', m.created_utc],
                 ['Type', m.notification_type],
                 ['Status', m.status]].forEach(function (pair) {
                    $meta.append($('<dt>').text(pair[0])).append($('<dd>').text(pair[1] || ''));
                });
                // Body is plain text; .text() prevents any markup or remote load.
                $('#email-log-message-body').text(m.content_available ? m.content : '');
                $('#email-log-message-unavailable').toggle(!m.content_available);
                $('#email-log-message-unavailable').text(text.unavailable);
                $('#email-log-message-truncated').toggle(!!m.content_truncated);
                var $timeline = $('#email-log-message-timeline').empty();
                (m.timeline || []).forEach(function (step) {
                    // One readable row per event: time, stage, status, then any detail.
                    var $row = $('<div>').addClass('email-log-event');
                    $('<div>').text(step.occurred_utc).appendTo($row);
                    $('<div>')
                        .append($('<strong>').text(step.stage))
                        .append(document.createTextNode(' — '))
                        .append($('<span>').text(step.status))
                        .appendTo($row);
                    if (step.detail) { $('<div>').text(step.detail).appendTo($row); }
                    if (step.source) {
                        $('<div>').addClass('text-muted').text('[' + step.source + ']').appendTo($row);
                    }
                    $row.appendTo($timeline);
                });
                // Collapsed by default; only expand when there is something to show.
                $('#email-log-message-timeline-disclosure').prop('open', false);
                // Return focus to the control that opened the dialog on close.
                $('#email-log-message-modal')
                    .off('hidden.bs.modal.emailfocus')
                    .one('hidden.bs.modal.emailfocus', function () {
                        var $opener = $('button[data-event-id]').filter(function () {
                            return $(this).attr('data-event-id') === eventId;
                        });
                        if ($opener.length) { $opener.first().trigger('focus'); }
                    })
                    .modal('show');
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
            /* bootstrap-select auto-initialises every .selectpicker on window
             * load, so no explicit init here: doing so would double-initialise.
             * The options never change, so no per-request refresh is needed
             * either; only the initial request waits for the ready handler. */
            load();
        });
    })();
</script>
