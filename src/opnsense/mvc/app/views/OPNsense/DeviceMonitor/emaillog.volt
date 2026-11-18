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
                        <a href="#email-log-local" id="email-log-tab-local" role="tab" data-toggle="tab"
                           data-scope="local">{{ devicemonitor_t('Local') }}</a>
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
                        {# Describes the disabled remote action only; no global banner text. #}
                        <span class="sr-only" id="email-log-remote-note"></span>

                        <div class="row email-log-filters">
                            <div class="col-sm-3">
                                <input type="text" id="email-log-search" class="form-control input-sm"
                                       placeholder="{{ devicemonitor_t('Search subject or recipient') }}">
                            </div>
                            <div class="col-sm-2">
                                <select id="email-log-visibility" class="selectpicker"
                                            data-style="btn-default btn-sm" data-width="100%">
                                    <option value="active" selected>{{ devicemonitor_t('Active') }}</option>
                                    <option value="deleted">{{ devicemonitor_t('Deleted') }}</option>
                                    <option value="all">{{ devicemonitor_t('All entries') }}</option>
                                </select>
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
                            <div class="col-sm-2">
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
                        </div>
                        {# Actions sit in one wrapping toolbar so every control stays inside the
                           container; buttons wrap instead of overflowing. #}
                        <div class="email-log-toolbar" role="toolbar">
                            <button id="email-log-export" class="btn btn-default btn-sm">
                                <i class="fa fa-download"></i> {{ devicemonitor_t('Export CSV') }}
                            </button>
                            <button id="email-log-clear" type="button" class="btn btn-link btn-sm">
                                {{ devicemonitor_t('Clear filters') }}
                            </button>
                            <button id="email-log-delete-selected" type="button" class="btn btn-default btn-sm"
                                    disabled>{{ devicemonitor_t('Delete selected') }} (0)</button>
                            <button id="email-log-delete-all" type="button" class="btn btn-default btn-sm">
                                {{ devicemonitor_t('Delete all local entries') }}
                            </button>
                        </div>

                        {# One shared column layout for Local, Peer and All nodes: the same
                           colgroup and fixed layout keep boundaries identical across tabs,
                           refreshes and empty results. #}
                        <div class="table-responsive">
                        <table class="table table-condensed table-hover email-log-table" id="email-log-table">
                            <colgroup>
                                <col class="email-log-col-select"/>
                                <col class="email-log-col-time"/>
                                <col class="email-log-col-node"/>
                                <col class="email-log-col-type"/>
                                <col class="email-log-col-recipient"/>
                                <col class="email-log-col-subject"/>
                                <col class="email-log-col-status"/>
                                <col class="email-log-col-actions"/>
                            </colgroup>
                            <thead>
                            <tr>
                                <th class="email-log-select-head"><input type="checkbox" id="email-log-select-all"
                                        aria-label="{{ devicemonitor_t('Select all eligible entries on this page') }}"/></th>
                                {# Static translated label; individual values carry their own zone suffix. #}
                                <th id="email-log-time-heading">{{ devicemonitor_t('Time (local)') }}</th>
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
                        </div>
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
    /* Confirmation dialog: ~480px on desktop, never wider than the viewport. */
    #email-log-delete-modal .email-log-confirm-dialog {
        width: 480px;
        max-width: calc(100vw - 32px);
        margin: 60px auto 16px;
    }
    #email-log-delete-modal .modal-body p { line-height: 1.5; margin-bottom: 12px; }
    #email-log-delete-modal .modal-body { overflow-wrap: anywhere; }
    @media (max-width: 520px) {
        #email-log-delete-modal .email-log-confirm-dialog { margin: 16px auto; }
    }
    #email-log-local .email-log-filters { margin-bottom: 8px; }
    #email-log-local .email-log-toolbar {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 8px;
    }
    #email-log-local .email-log-toolbar .btn { margin: 0; }
    /* Shared Email Log column layout. Proportions follow the Local screenshot:
       time and status are compact, node and subject carry the extra width. */
    #email-log-table.email-log-table {
        table-layout: fixed;
        width: 100%;
        margin-bottom: 0;
    }
    /* The selection column is taken from the actions column only, so the other
     * proportions of the agreed layout are unchanged. */
    #email-log-table.email-log-table .email-log-col-select { width: 3%; }
    #email-log-table.email-log-table .email-log-col-time { width: 16%; }
    #email-log-table.email-log-table .email-log-col-node { width: 19%; }
    #email-log-table.email-log-table .email-log-col-type { width: 10%; }
    #email-log-table.email-log-table .email-log-col-recipient { width: 17%; }
    #email-log-table.email-log-table .email-log-col-subject { width: 22%; }
    #email-log-table.email-log-table .email-log-col-status { width: 10%; }
    #email-log-table.email-log-table .email-log-col-actions { width: 3%; }
    /* Values wrap rather than being clipped; fonts are unchanged. */
    #email-log-table.email-log-table td,
    #email-log-table.email-log-table th {
        overflow-wrap: anywhere;
        word-break: break-word;
        vertical-align: top;
    }
    /* Actions wrap inside their own column; nothing is hidden or shrunk. */
    #email-log-table.email-log-table td.email-log-actions .btn {
        margin: 0 0 2px 0;
        white-space: normal;
    }
    @media (max-width: 991px) {
        #email-log-table.email-log-table { min-width: 720px; }
    }
    /* Scoped to this dialog only. OPNsense main.css sets .modal-body padding:0,
     * so the padded body the design requires is supplied here. No fixed heights
     * on the content: the dialog itself is capped to the viewport below the fixed
     * navigation and only .modal-body scrolls, so header and footer stay put. */
    /* Core main.css gives .modal-dialog margin-top 62px while the fixed page head
     * (.page-head, 70px) sits above the overlay: the 1050 z-index loses to the
     * navbar's 1030 because document-order list items are painted before the
     * transformed .modal. Lift the overlay above the head and position the dialog
     * from the top of the remaining viewport. */
    #email-log-message-modal {
        z-index: 1200;
    }
    /* Dialog width: aim for 800px, never closer than 16px to the viewport edge. */
    #email-log-message-modal .modal-dialog {
        width: 800px;
        max-width: calc(100vw - 32px);
        margin: 86px auto 16px;
        max-height: calc(100vh - 102px);
    }
    #email-log-message-modal .modal-content {
        display: flex;
        flex-direction: column;
        max-height: calc(100vh - 102px);
    }
    #email-log-message-modal .modal-header,
    #email-log-message-modal .modal-footer {
        flex: none; /* header and footer keep their height; the body scrolls */
    }
    #email-log-message-modal .modal-body {
        flex: 1 1 auto;
        min-height: 0;
        overflow-y: auto;
    }
    #email-log-message-modal .modal-header {
        padding: 20px;
        /* Keep clear space between the subject and the close control. */
        position: relative;
        padding-right: 56px;
    }
    /* Float the close control so a long subject only wraps inside the remaining
     * width; matching header padding-right keeps the subject clear of it. */
    #email-log-message-modal .modal-header .close {
        float: right;
        margin: 0;
        line-height: 1;
    }
    #email-log-message-modal .modal-header .modal-title {
        word-break: break-word;
        overflow-wrap: anywhere;
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
        #email-log-message-modal .modal-dialog {
            margin: 70px auto 16px;
            max-height: calc(100vh - 86px);
        }
        #email-log-message-modal .modal-content {
            max-height: calc(100vh - 86px);
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
    /* Standard disclosure control: normal body text, a chevron that rotates when
     * expanded, and the framework focus ring on the native button. */
    #email-log-message-modal .email-log-dialog-disclosure {
        display: block;
        width: 100%;
        padding: 12px 0;
        border: 0;
        border-top: 1px solid #e5e5e5;
        background: transparent;
        color: inherit;
        font-size: inherit;
        line-height: inherit;
        text-align: left;
        cursor: pointer;
    }
    #email-log-message-modal .email-log-dialog-disclosure .glyphicon {
        margin-right: 6px;
        transition: transform 0.15s ease-in-out;
    }
    #email-log-message-modal .email-log-dialog-disclosure[aria-expanded="true"] .glyphicon {
        transform: rotate(90deg);
    }
    #email-log-message-modal .email-log-dialog-disclosure-count {
        color: #777;
    }
    #email-log-message-modal .email-log-dialog-no-delivery {
        padding-top: 12px;
        border-top: 1px solid #e5e5e5;
    }
    #email-log-message-modal .email-log-dialog-timeline-extra {
        margin-top: 12px;
    }
    /* Legacy rows: the delivery record is still readable when the body is not. */
    #email-log-message-modal .email-log-dialog-reading.is-unavailable {
        display: none;
    }
    #email-log-message-modal .email-log-dialog-timeline {
        margin-top: 4px;
    }
    #email-log-message-modal .email-log-dialog-timeline .text-muted,
    #email-log-message-modal .email-log-dialog-timeline .email-log-event-time {
        margin-bottom: 2px;
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
            {# panel-header styling only: the installed .panel-default > .panel-heading
               rule supplies the theme's subtle header background and its paired text
               colour in both the light and dark themes. Scoped padding stays below. #}
            <div class="modal-header panel-heading">
                <button type="button" class="close" data-dismiss="modal" aria-label="{{ lang.query('Close')|json_encode(15) }}">
                    <span aria-hidden="true">&times;</span>
                </button>
                {# The subject becomes the heading; the static label is only a fallback
                   that the script replaces before the dialog is shown. #}
                <h4 class="modal-title" id="email-log-message-title">{{ devicemonitor_t('Message') }}</h4>
            </div>
            <div class="modal-body email-log-dialog-body">
                <div class="alert alert-warning" id="email-log-message-error" style="display:none;" role="alert"></div>
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
                <div id="email-log-message-delivery">
                    {# Native button disclosure, as used on the Devices page: keyboard
                       activation comes from the button itself and aria-expanded carries
                       the state. The chevron points right when collapsed and the label
                       carries the recorded event count. #}
                    <button type="button" id="email-log-message-timeline-disclosure"
                            class="email-log-dialog-disclosure"
                            aria-expanded="false" aria-controls="email-log-message-timeline-panel">
                        <span class="glyphicon glyphicon-chevron-right" aria-hidden="true"></span>
                        <span id="email-log-message-timeline-label">{{ devicemonitor_t('Delivery details') }}</span>
                        <span id="email-log-message-timeline-count" class="email-log-dialog-disclosure-count"></span>
                    </button>
                    <div id="email-log-message-timeline-panel" class="email-log-dialog-timeline" hidden>
                        <div id="email-log-message-timeline"></div>
                        <div id="email-log-message-timeline-extra" class="email-log-dialog-timeline-extra"></div>
                    </div>
                </div>
                {# Without recorded events there is no expansion control at all. #}
                <div id="email-log-message-no-delivery" hidden>
                    <div class="email-log-dialog-no-delivery"><strong>{{ devicemonitor_t('Delivery details') }}</strong></div>
                    <div class="text-muted" id="email-log-message-no-delivery-text"></div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal">{{ devicemonitor_t('Close') }}</button>
            </div>
        </div>
    </div>
</div>

{# Standard OPNsense confirmation dialog (same structure as core modal confirmations). #}
<div class="modal fade" id="email-log-delete-modal" tabindex="-1" role="dialog"
     aria-labelledby="email-log-delete-title">
    <div class="modal-dialog email-log-confirm-dialog" role="document">
        <div class="modal-content">
            <div class="modal-header panel-heading">
                <button type="button" class="close" data-dismiss="modal"
                        aria-label="{{ lang.query('Close')|json_encode(15) }}">
                    <span aria-hidden="true">&times;</span>
                </button>
                <h4 class="modal-title" id="email-log-delete-title">{{ devicemonitor_t('Delete entry') }}</h4>
            </div>
            <div class="modal-body" style="padding:24px;">
                <p id="email-log-delete-text"></p>
                <div id="email-log-delete-all-extra" style="display:none;">
                    <label>
                        <input type="checkbox" id="email-log-delete-all-confirm"/>
                        {{ devicemonitor_t('I understand this removes every active local entry from view') }}
                    </label>
                </div>
            </div>
            <div class="modal-footer" style="padding:16px 24px;">
                <button type="button" class="btn btn-default" data-dismiss="modal">{{ devicemonitor_t('Cancel') }}</button>
                <button type="button" class="btn btn-danger" id="email-log-delete-confirm">{{ devicemonitor_t('Delete') }}</button>
            </div>
        </div>
    </div>
</div>

<script>
    function emailLogText() {
        return {
            relayAcceptedNotice: {{ lang.query('Relay acceptance is not proof that the message reached the recipient inbox.')|json_encode(15) }},
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
            viewFailed: {{ lang.query('Could not load this message')|json_encode(15) }},
            keepNotice: {{ lang.query('Entries are hidden and can be restored until the normal 30-day retention removes them. Actual emails and mail queues are unaffected.')|json_encode(15) }},
            deleteSelectedTitle: {{ lang.query('Delete selected entries')|json_encode(15) }},
            deleteAllTitle: {{ lang.query('Delete all local entries')|json_encode(15) }},
            deleteSelectedBody: {{ lang.query('Remove %count% selected local entr%plural% from the active log on %node%?')|json_encode(15) }},
            deleteAllBody: {{ lang.query('Remove every active local entry on %node% from the active log, including entries outside the current filters and page?')|json_encode(15) }},
            selectionRemote: {{ lang.query('Remote entries cannot be selected from this node.')|json_encode(15) }},            eventSingular: {{ lang.query('event')|json_encode(15) }},
            eventPlural: {{ lang.query('events')|json_encode(15) }},
            noDelivery: {{ lang.query('No delivery details recorded')|json_encode(15) }},
            peerPrefix: {{ lang.query('Peer')|json_encode(15) }},
            thisNode: {{ lang.query('This node')|json_encode(15) }},
            roleWhenSent: {{ lang.query('Role when sent')|json_encode(15) }},
            queueId: {{ lang.query('Queue ID')|json_encode(15) }},
            delete: {{ lang.query('Delete')|json_encode(15) }},
            restore: {{ lang.query('Restore')|json_encode(15) }},
            remoteLocked: {{ lang.query('This entry belongs to the configured peer; delete and restore are available only on the node that owns it.')|json_encode(15) }},
            confirmDelete: {{ lang.query('Remove this entry from the active log? Its message and delivery history will be retained under the existing retention policy.')|json_encode(15) }},
            confirmRestore: {{ lang.query('Return this entry to the active log?')|json_encode(15) }},
            deleteTitle: {{ lang.query('Delete entry')|json_encode(15) }},
            restoreTitle: {{ lang.query('Restore entry')|json_encode(15) }},
            changeFailed: {{ lang.query('The entry could not be changed')|json_encode(15) }},
            changed: {{ lang.query('Entry updated')|json_encode(15) }}
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
        /* Selected local event ids (value = owning node for the confirmation text). */
        var selected = {};
        /* "hostname — management IP" of this node, used to name it in confirmations. */
        var localNodeLabel = '';

        function syncSelection() {
            $('#email-log-remote-note').text(text.remoteLocked + ' ' + text.selectionRemote);
            var count = Object.keys(selected).length;
            $('#email-log-delete-selected')
                .prop('disabled', count === 0 || scope !== 'local')
                .text({{ lang.query('Delete selected')|json_encode(15) }} + ' (' + count + ')');
            var boxes = $('.email-log-select:not(:disabled)');
            var all = boxes.length > 0 && boxes.filter(':checked').length === boxes.length;
            $('#email-log-select-all').prop('checked', all).prop('indeterminate',
                !all && boxes.filter(':checked').length > 0);
            $('#email-log-delete-all').prop('disabled', scope !== 'local');
        }

        /* Any change of scope, filters or page drops the selection. */
        function clearSelection() {
            selected = {};
            syncSelection();
        }

        $('#email-log-select-all').on('change', function () {
            var on = $(this).prop('checked');
            $('.email-log-select:not(:disabled)').each(function () {
                $(this).prop('checked', on);
                var id = $(this).attr('data-event-id');
                if (on) { selected[id] = true; } else { delete selected[id]; }
            });
            syncSelection();
        });

        /* Plugin timestamp convention: stored UTC, rendered once in the browser's
         * own timezone with its DST rules and native abbreviation. When the browser
         * cannot format the value, ``localFallback`` (converted server-side with the
         * OPNsense-configured zone) is shown instead. Intl renders the fields and
         * the zone from the same instant, so midnight and DST boundaries are never
         * formatted from mixed calendars. */
        function formatTimestamp(utc, localFallback) {
            var value = String(utc || '').trim();
            if (value === '') { return '\u2014'; }
            var date = new Date(value.replace(' ', 'T') + 'Z');
            if (isNaN(date.getTime())) { return localFallback || value; }
            var parts = {};
            var opts = {
                year: 'numeric', month: '2-digit', day: '2-digit',
                hour: '2-digit', minute: '2-digit', second: '2-digit',
                hourCycle: 'h23', timeZoneName: 'short'
            };
            try {
                new Intl.DateTimeFormat(undefined, opts)
                    .formatToParts(date).forEach(function (part) { parts[part.type] = part.value; });
            } catch (e) {
                new Intl.DateTimeFormat('en-GB', opts)
                    .formatToParts(date).forEach(function (part) { parts[part.type] = part.value; });
            }
            return parts.year + '-' + parts.month + '-' + parts.day + ' ' +
                parts.hour + ':' + parts.minute + ':' + parts.second +
                (parts.timeZoneName ? ' ' + parts.timeZoneName : '');
        }
        /* Stored values are UTC; every view renders them in the browser's own
         * zone. The legend names that zone from the browser itself, so the
         * reader knows which clock the converted times are on. */
        /* Display-only: internal and API values stay unchanged. An accepted handoff
         * is relay acceptance, never proof of inbox receipt. */
        var statusNames = {
            accepted: {{ lang.query('Relay accepted')|json_encode(15) }},
            queued: {{ lang.query('Queued or deferred')|json_encode(15) }},
            deferred: {{ lang.query('Queued or deferred')|json_encode(15) }},
            submitted: {{ lang.query('Submitted')|json_encode(15) }},
            failed: {{ lang.query('Failed')|json_encode(15) }},
            unknown: {{ lang.query('Unknown')|json_encode(15) }}
        };
        function statusLabel(value) {
            var key = String(value || '').toLowerCase();
            return statusNames.hasOwnProperty(key) ? statusNames[key] : (value || '');
        }

        /* Remote rows are read-only from this node. The note follows the scope and
         * the visibility: Local + All entries can carry peer rows when a peer is
         * configured, so a disabled action there is never left unexplained. */
        function refreshRemoteNote() {
            /* The explanation lives on the disabled remote control (title and
             * aria-describedby), never as page-wide text. */
            $('#email-log-remote-note').text(text.remoteLocked);
        }

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
            /* All nodes always describes both halves: this node's records plus the
             * configured peer's. It never borrows the Peer-only wording. */
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
                    search: $('#email-log-search').val(),
                    visibility: $('#email-log-visibility').val()
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
                refreshRemoteNote();
                /* The banner always describes the scope that produced this response. */
                if (scope === 'local') {
                    $('#email-log-partial').hide();
                    $('#email-log-scope-note').text(text.localOnly);
                } else {
                    setScopeNote(data);
                }
                var allRows = data.rows || [];
                var rows = scope === 'peer' ? allRows.filter(function (r) { return r.scope === 'peer'; }) : allRows;
                var $body = $('#email-log-rows').empty();
                /* Header identity: "hostname — management IP — role", labelled so the
                 * local and remote nodes cannot be confused. */
                function nodeLabel(facts) {
                    if (!facts) { return ''; }
                    return facts.label || [facts.node_id, facts.node_ip, facts.role]
                        .filter(function (v) { return v; }).join(' \u2014 ');
                }
                var localFacts = data.local_node || data.node || null;
                localNodeLabel = nodeLabel(localFacts) || '';
                var header = text.thisNode + ': ' + localNodeLabel;
                if (scope !== 'local' && data.peer_node) {
                    header += ' | ' + text.peerPrefix + ': ' + nodeLabel(data.peer_node);
                }
                $('#email-log-node').text(header);
                if (data.logging_diagnostic) {
                    $('#email-log-diagnostic').show().text(data.logging_diagnostic);
                } else {
                    $('#email-log-diagnostic').hide();
                }
                selected = {};
                syncSelection();
                rows.forEach(function (row) {
                    var $tr = $('<tr>');
                    /* Only local records can be selected; remote rows are read-only
                     * here and say so on the control itself. */
                    var remoteRow = row.scope === 'peer';
                    var $select = $('<input type="checkbox"/>').addClass('email-log-select')
                        .attr('data-event-id', row.event_id)
                        .prop('disabled', remoteRow)
                        .on('change', function () {
                            if ($(this).prop('checked')) { selected[row.event_id] = row.node_ip || true; }
                            else { delete selected[row.event_id]; }
                            syncSelection();
                        });
                    if (remoteRow) {
                        $select.attr('title', text.remoteLocked).attr('aria-describedby', 'email-log-remote-note');
                    }
                    $tr.append($('<td>').addClass('email-log-select-cell').append($select));
                    $tr.append($('<td>').text(formatTimestamp(row.created_utc, row.created_local)));
                    /* Attribute the row to the node that produced it: both HA nodes share
                     * the hostname, so the origin IP is what distinguishes them. */
                    /* origin_ip identifies the node for correlation; node_role is the role
                     * recorded when the email was created and is never rewritten. */
                    var originIp = row.origin_ip || row.node_ip || '';
                    var nodeText = (row.scope === 'peer' ? (text.peerPrefix + ' ') : '') + originIp;
                    var sentRole = String(row.node_role || '').trim();
                    if (sentRole !== '' && sentRole.toLowerCase() !== 'unknown') {
                        nodeText += ' (' + sentRole + ')';
                    }
                    $tr.append($('<td>').text(nodeText.trim()));
                    $tr.append($('<td>').text(row.notification_type));
                    $tr.append($('<td>').text(row.recipient));
                    $tr.append($('<td>').text(row.subject));
                    $tr.append($('<td>').text(statusLabel(row.status)));
                    var $detail = $('<td>').addClass('email-log-actions');
                    /* The single row action. Metadata, message content and the full
                     * delivery timeline all open in the dialog. It is always offered,
                     * even for rows recorded before capture: the dialog then explains
                     * that the content is unavailable and still lists the delivery. */
                    $('<button>').addClass('btn btn-default btn-xs')
                        .attr('data-event-id', row.event_id)
                        .attr('aria-label', text.viewMessage)
                        .text(text.viewMessage)
                        .on('click', function () { openMessage(row.event_id, row.scope === 'peer'); })
                        .appendTo($detail);
                    /* Delete/Restore act on this node's database only. A remote row is
                     * shown with the action disabled and the reason attached, because no
                     * secure cross-node mutation capability is configured. */
                    var remote = row.scope === 'peer';
                    var deleted = (row.deleted_utc || '') !== '';
                    var $change = $('<button>').addClass('btn btn-default btn-xs')
                        .css('margin-left', '4px')
                        .attr('data-event-id', row.event_id)
                        .attr('data-action', deleted ? 'restore' : 'delete')
                        .prop('disabled', remote)
                        .text(deleted ? text.restore : text.delete)
                        .on('click', function () {
                            confirmVisibility(row.event_id, !deleted);
                        });
                    if (remote) {
                        /* A disabled control is not announced by assistive technology,
                         * so the explanation travels on the control and again in the
                         * dialog: the peer's log is read-only from this node. */
                        $change.attr('title', text.remoteLocked).attr('aria-describedby', 'email-log-remote-note');
                    }
                    $change.appendTo($detail);
                    $tr.append($detail);
                    $body.append($tr);
                });
                $('#email-log-empty').toggle(rows.length === 0);
                $('#email-log-prev').prop('disabled', page === 1);
                $('#email-log-next').prop('disabled', rows.length < perPage);
            });
        }

        /* Label and chevron follow aria-expanded, so the control's state, its
         * accessible state and its appearance can never disagree. */
        function setTimelineExpanded(expanded) {
            var on = !!expanded;
            $('#email-log-message-timeline-disclosure').attr('aria-expanded', on ? 'true' : 'false');
            $('#email-log-message-timeline-panel').prop('hidden', !on);
        }

        function setTimelineCount(count) {
            var label = count === 1 ? text.eventSingular : text.eventPlural;
            $('#email-log-message-timeline-count').text(
                count > 0 ? '(' + count + ' ' + label + ')' : ''
            );
        }

        $('#email-log-message-timeline-disclosure').on('click', function () {
            setTimelineExpanded($(this).attr('aria-expanded') !== 'true');
        });

        /* Retrieval errors are reported in the dialog itself with a retrievable
         * message. Opening it never sends or retries mail: every request below is
         * a read-only POST to a lookup action. */
        function showMessageError(reason) {
            $('#email-log-message-error').show().text(reason);
            $('#email-log-message-modal')
                .off('hidden.bs.modal.emailfocus')
                .one('hidden.bs.modal.emailfocus', restoreOpenerFocus)
                .modal('show');
        }

        var $openEventId = null;

        function restoreOpenerFocus() {
            var $opener = $('button[data-event-id]').filter(function () {
                return $(this).attr('data-event-id') === $openEventId;
            });
            if ($opener.length) { $opener.first().trigger('focus'); }
        }

        function openMessage(eventId, fromPeer) {
            $openEventId = eventId;
            $.ajax({
                url: fromPeer
                    ? '/api/devicemonitor/emaillog/peermessageview'
                    : '/api/devicemonitor/emaillog/message',
                type: 'POST',
                dataType: 'json',
                data: { event_id: eventId }
            }).fail(function (xhr) {
                // The failure belongs where the operator is looking: in the dialog.
                showMessageError((fromPeer ? text.viewFailed : text.loadFailed) +
                    ' (HTTP ' + (xhr && xhr.status ? xhr.status : '?') + ')');
            }).done(function (data) {
                if (!data || data.result !== 'ok' || !data.message) {
                    showMessageError((fromPeer ? text.viewFailed : text.loadFailed) +
                        (data && data.message ? ': ' + data.message : ''));
                    return;
                }
                var m = data.message;
                $('#email-log-message-error').hide().text('');
                $('#email-log-message-title').text(m.subject || text.unknown);
                var $meta = $('#email-log-message-meta').empty();
                /* The role recorded when the email was sent is shown only when one was
                 * actually captured; the node's current role is never substituted. */
                var sentRole = String(m.node_role || '').trim();
                var hasSentRole = sentRole !== '' && sentRole.toLowerCase() !== 'unknown';
                var metaPairs = [
                    ['Recipient', m.recipient],
                    ['Node', m.node_ip],
                    ['Time', formatTimestamp(m.created_utc, m.created_local)],
                    ['Type', m.notification_type],
                    ['Status', statusLabel(m.status)]
                ];
                if (hasSentRole) { metaPairs.push([text.roleWhenSent, sentRole]); }
                metaPairs.forEach(function (pair) {
                    $meta.append($('<dt>').text(pair[0])).append($('<dd>').text(pair[1] || ''));
                });
                // Body is plain text; .text() prevents any markup or remote load.
                // Legacy rows without captured content keep their delivery record:
                // only the empty reading area is hidden, behind the explanation.
                $('#email-log-message-body').text(m.content_available ? m.content : '');
                $('#email-log-message-unavailable').prop('hidden', !!m.content_available);
                $('#email-log-message-unavailable').text(text.unavailable);
                $('#email-log-message-truncated').prop('hidden', true);
                $('.email-log-dialog-reading').toggleClass('is-unavailable', !m.content_available);
                $('#email-log-message-truncated').toggle(!!m.content_truncated);
                var steps = m.timeline || [];
                var $timeline = $('#email-log-message-timeline').empty();
                steps.forEach(function (step) {
                    // One readable row per event, in the recorded (chronological) order:
                    // time, stage and status, then any diagnostic detail and source.
                    var $row = $('<div>').addClass('email-log-event');
                    $('<div>').addClass('email-log-event-time')
                        .text(formatTimestamp(step.occurred_utc, step.occurred_local)).appendTo($row);
                    $('<div>')
                        .append($('<strong>').text(statusLabel(step.stage)))
                        .append(document.createTextNode(' — '))
                        .append($('<span>').text(statusLabel(step.status)))
                        .appendTo($row);
                    if (step.detail) { $('<div>').addClass('email-log-event-detail').text(step.detail).appendTo($row); }
                    if (step.source) {
                        $('<div>').addClass('text-muted').text('[' + step.source + ']').appendTo($row);
                    }
                    $row.appendTo($timeline);
                });
                var $extra = $('#email-log-message-timeline-extra').empty();
                if (m.status === 'accepted') {
                    $extra.append($('<div>').addClass('text-muted').text(text.relayAcceptedNotice));
                }
                $extra.append($('<div>').text(text.queueId + ': ' + (m.queue_id || text.unknown)));
                // No recorded events: a plain statement instead of an expansion control.
                $('#email-log-message-delivery').prop('hidden', steps.length === 0);
                $('#email-log-message-no-delivery').prop('hidden', steps.length > 0);
                $('#email-log-message-no-delivery-text').text(text.noDelivery);
                setTimelineCount(steps.length);
                // Collapsed by default on every open, with an accurate state.
                setTimelineExpanded(false);
                // Return focus to the control that opened the dialog on close.
                $('#email-log-message-modal')
                    .off('hidden.bs.modal.emailfocus')
                    .one('hidden.bs.modal.emailfocus', restoreOpenerFocus)
                    .modal('show');
            });
        }

        /* The Local/Peer/All nodes tabs own the request scope: selecting one re-requests
         * with that scope so the tab, the banner and the returned origin always agree. */
        $('#email-log-tab-local, #email-log-tab-peer, #email-log-tab-all').on('shown.bs.tab', function () {
            var next = String($(this).attr('data-scope') || 'local');
            if (next === scope) { return; }
            scope = next;
            page = 1;
            clearSelection();
            load();
        });

        $('#email-log-type, #email-log-status, #email-log-visibility').on('change', function () { page = 1; clearSelection(); load(); });
        $('#email-log-search').on('input', function () { page = 1; clearSelection(); load(); });

        /* Clear filters resets search, type and status to their defaults, returns to
         * page one and refreshes once. The Local/Peer/All scope and the Active/
         * Deleted/All visibility choice are deliberately left as they are. */
        $('#email-log-clear').on('click', function () {
            $('#email-log-search').val('');
            $('#email-log-type').val('');
            $('#email-log-status').val('');
            $('#email-log-type, #email-log-status').selectpicker('refresh');
            page = 1;
            clearSelection();
            load();
        });

        var $pendingDelete = null;

        /* The standard confirmation step for every visibility change. Delete uses
         * the policy wording the operator approved; restore states plainly that the
         * entry returns to the active log. */
        function confirmVisibility(eventId, deleted) {
            $pendingDelete = { eventId: eventId, deleted: !!deleted };
            $('#email-log-delete-title').text(deleted ? text.deleteTitle : text.restoreTitle);
            $('#email-log-delete-text').text(deleted ? text.confirmDelete : text.confirmRestore);
            $('#email-log-delete-confirm')
                .toggleClass('btn-danger', deleted)
                .toggleClass('btn-primary', !deleted)
                .text(deleted ? text.delete : text.restore);
            $('#email-log-delete-modal')
                .one('hidden.bs.modal.emailfocus', function () {
                    var $opener = $('button[data-event-id]').filter(function () {
                        return $(this).attr('data-event-id') === eventId;
                    });
                    if ($opener.length) { $opener.first().trigger('focus'); }
                })
                .modal('show');
        }

        /* Both bulk actions use the same standard confirmation dialog. */
        function confirmBulk(mode) {
            var ids = Object.keys(selected);
            var node = localNodeLabel || 'this node';
            $pendingDelete = { mode: mode, ids: ids };
            var all = mode === 'all';
            var body = all
                ? text.deleteAllBody.replace('%node%', node)
                : text.deleteSelectedBody.replace('%count%', ids.length)
                    .replace('%plural%', ids.length === 1 ? 'y' : 'ies').replace('%node%', node);
            $('#email-log-delete-title').text(all ? text.deleteAllTitle : text.deleteSelectedTitle);
            $('#email-log-delete-text').text(body + ' ' + text.keepNotice);
            $('#email-log-delete-all-extra').toggle(all);
            $('#email-log-delete-all-confirm').prop('checked', false);
            $('#email-log-delete-confirm')
                .toggleClass('btn-danger', true).toggleClass('btn-primary', false)
                .prop('disabled', all)
                .text(text.delete);
            $('#email-log-delete-modal').modal('show');
        }

        $('#email-log-delete-all-confirm').on('change', function () {
            $('#email-log-delete-confirm').prop('disabled', !$(this).prop('checked'));
        });

        $('#email-log-delete-selected').on('click', function () {
            if (Object.keys(selected).length) { confirmBulk('selected'); }
        });
        $('#email-log-delete-all').on('click', function () { confirmBulk('all'); });

        $('#email-log-delete-confirm').on('click', function () {
            var pending = $pendingDelete;
            $pendingDelete = null;
            $('#email-log-delete-modal').modal('hide');
            if (!pending) { return; }
            if (pending.mode) {
                $.ajax({
                    url: pending.mode === 'all'
                        ? '/api/devicemonitor/emaillog/deleteall'
                        : '/api/devicemonitor/emaillog/bulkdelete',
                    type: 'POST',
                    dataType: 'json',
                    data: pending.mode === 'all'
                        ? { confirm: 'delete-all' }
                        : { 'event_ids[]': pending.ids }
                }).fail(function (xhr) {
                    $('#email-log-diagnostic').show().text(text.changeFailed +
                        ' (HTTP ' + (xhr && xhr.status ? xhr.status : '?') + ')');
                }).done(function (data) {
                    if (!data || data.result !== 'ok') {
                        $('#email-log-diagnostic').show().text(text.changeFailed +
                            (data && data.message ? ': ' + data.message : ''));
                        return;
                    }
                    $('#email-log-diagnostic').hide();
                    clearSelection();
                    load();
                });
                return;
            }
            changeVisibility(pending.eventId, pending.deleted);
        });

        /* Soft delete/restore only: the server changes the visibility marker and
         * leaves the body, event id, status and timeline intact. Postfix queues,
         * mailboxes and delivery behaviour are never touched. */
        function changeVisibility(eventId, deleted) {
            $.ajax({
                url: deleted
                    ? '/api/devicemonitor/emaillog/delete'
                    : '/api/devicemonitor/emaillog/restore',
                type: 'POST',
                dataType: 'json',
                data: { event_id: eventId }
            }).fail(function (xhr) {
                $('#email-log-diagnostic').show().text(text.changeFailed +
                    ' (HTTP ' + (xhr && xhr.status ? xhr.status : '?') + ')');
            }).done(function (data) {
                if (!data || data.result !== 'ok') {
                    $('#email-log-diagnostic').show().text(text.changeFailed +
                        (data && data.message ? ': ' + data.message : ''));
                    return;
                }
                $('#email-log-diagnostic').hide();
                load();
            });
        }
        $('#email-log-prev').on('click', function () { if (page > 1) { page--; clearSelection(); load(); } });
        $('#email-log-next').on('click', function () { page++; clearSelection(); load(); });
        $('#email-log-export').on('click', function () {
            $.ajax({
                url: '/api/devicemonitor/emaillog/exportcsv',
                type: 'POST',
                dataType: 'json',
                data: {
                    type: $('#email-log-type').val(),
                    status: $('#email-log-status').val(),
                    search: $('#email-log-search').val(),
                    visibility: $('#email-log-visibility').val()
                }
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
