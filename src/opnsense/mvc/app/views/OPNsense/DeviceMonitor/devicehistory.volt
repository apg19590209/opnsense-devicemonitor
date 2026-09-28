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
#service-alert-preferences td {
    vertical-align: middle !important;
}
#service-alert-preferences .bootstrap-select {
    vertical-align: middle;
}
#service-alert-preferences .bootstrap-select > .dropdown-toggle {
    display: flex;
    align-items: center;
    height: 30px;
}
.dm-info { border:0; background:transparent; color:#337ab7; padding:0 3px; cursor:pointer; }
</style>

<div class="content-box">
    <div class="content-box-main">

        <div style="padding:10px 10px 8px 10px;border-bottom:1px solid #333;margin-bottom:12px;">
            <a href="/ui/devicemonitor/index/devices"
               class="btn btn-default btn-sm pull-right"
               style="font-size:14px;font-weight:600;padding:6px 12px;">
                <i class="fa fa-arrow-left"></i>
                {{ devicemonitor_t('Back to Devices') }}
            </a>

            <a id="activity-timeline-link"
               href="/ui/devicemonitor/index/activitytimeline"
               class="btn btn-default btn-sm pull-right"
               style="font-size:14px;font-weight:600;padding:6px 12px;margin-right:6px;">
                <i class="fa fa-clock-o"></i>
                {{ devicemonitor_t('Device Activity') }}
            </a>
            <h1 style="margin:0;font-size:20px;">
                {{ devicemonitor_t('Network Identity Details') }}
            </h1>
        </div>

        <div class="panel panel-default">
            <div class="panel-heading">
                <strong>
                    <i class="fa fa-desktop"></i>
                    {{ devicemonitor_t('Network Identity Summary') }}
                </strong>
            </div>
            <div class="panel-body" style="padding-bottom:5px;">
                <div class="row">
                    <div class="col-md-6">
                        <table class="table table-condensed" style="margin-bottom:5px;">
                            <tbody>
                                <tr><th style="width:135px;">{{ devicemonitor_t('IP Address') }}</th><td id="summary-ip">&mdash;</td></tr>
                                <tr><th>{{ devicemonitor_t('Friendly Name') }}</th><td id="summary-friendly-name">&mdash;</td></tr>
                                <tr><th>{{ devicemonitor_t('Hostname') }}</th><td id="summary-hostname">&mdash;</td></tr>
                                <tr><th>{{ devicemonitor_t('MAC Address') }}</th><td id="summary-mac">&mdash;</td></tr>
                                <tr><th>{{ devicemonitor_t('Vendor') }}</th><td id="summary-vendor">&mdash;</td></tr>
                            </tbody>
                        </table>
                    </div>

                    <div class="col-md-6">
                        <table class="table table-condensed" style="margin-bottom:5px;">
                            <tbody>
                                <tr><th style="width:135px;">{{ devicemonitor_t('Status') }}</th><td id="summary-status">&mdash;</td></tr>
                                <tr><th>{{ devicemonitor_t('VLAN') }}</th><td id="summary-vlan">&mdash;</td></tr>
                                <tr><th>{{ devicemonitor_t('First Seen') }}</th><td id="summary-first-seen">&mdash;</td></tr>
                                <tr><th>{{ devicemonitor_t('Last Seen') }}</th><td id="summary-last-seen">&mdash;</td></tr>
                                <tr><th>{{ devicemonitor_t('Current Lifecycle') }}</th><td id="summary-lifecycle">&mdash;</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <div class="panel panel-default" id="device-service-alerts">
            <div class="panel-heading">
                <strong><i class="fa fa-bell-o"></i> {{ devicemonitor_t('Service Email Alerts') }}</strong>
                <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('About Service Email Alerts') }}"
                        data-content="{{ devicemonitor_t('Choose whether this network identity sends service email alerts. Use global setting preserves the Settings defaults. Email delivery must be enabled in Settings.') }}">
                    <i class="fa fa-info-circle" aria-hidden="true"></i>
                </button>
            </div>
            <div class="panel-body">
                <div id="service-alert-delivery" class="alert alert-warning"
                     role="status" style="display:none;padding:8px 12px;">
                    <i class="fa fa-exclamation-triangle" aria-hidden="true"></i>
                    <span id="service-alert-delivery-reason"></span>
                    <a id="service-alert-settings-link" class="btn btn-default btn-sm"
                       href="/ui/devicemonitor/index/settings#tab-email">
                        <i class="fa fa-envelope-o" aria-hidden="true"></i>
                        {{ devicemonitor_t('Go to Email Notifications') }}
                    </a>
                </div>
                <div class="table-responsive">
                    <table class="table table-condensed" id="service-alert-preferences">
                        <thead><tr>
                            <th>{{ devicemonitor_t('Service event') }}</th>
                            <th>{{ devicemonitor_t('Preference') }}</th>
                            <th>{{ devicemonitor_t('Effective') }}</th>
                        </tr></thead>
                        <tbody>
                            <tr data-alert-field="service_new">
                                <td>{{ devicemonitor_t('New service') }}</td>
                                <td><select class="selectpicker" data-style="btn-default btn-sm" data-width="190px" aria-label="{{ devicemonitor_t('New service email preference') }}">
                                    <option value="inherit">{{ devicemonitor_t('Use global setting') }}</option>
                                    <option value="on">{{ devicemonitor_t('On') }}</option>
                                    <option value="off">{{ devicemonitor_t('Off') }}</option>
                                </select></td>
                                <td class="alert-effective">&mdash;</td>
                            </tr>
                            <tr data-alert-field="service_unavailable">
                                <td>{{ devicemonitor_t('Service unavailable') }}</td>
                                <td><select class="selectpicker" data-style="btn-default btn-sm" data-width="190px" aria-label="{{ devicemonitor_t('Service unavailable email preference') }}">
                                    <option value="inherit">{{ devicemonitor_t('Use global setting') }}</option>
                                    <option value="on">{{ devicemonitor_t('On') }}</option>
                                    <option value="off">{{ devicemonitor_t('Off') }}</option>
                                </select></td>
                                <td class="alert-effective">&mdash;</td>
                            </tr>
                            <tr data-alert-field="service_recovered">
                                <td>{{ devicemonitor_t('Service recovered') }}</td>
                                <td><select class="selectpicker" data-style="btn-default btn-sm" data-width="190px" aria-label="{{ devicemonitor_t('Service recovered email preference') }}">
                                    <option value="inherit">{{ devicemonitor_t('Use global setting') }}</option>
                                    <option value="on">{{ devicemonitor_t('On') }}</option>
                                    <option value="off">{{ devicemonitor_t('Off') }}</option>
                                </select></td>
                                <td class="alert-effective">&mdash;</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <button type="button" id="save-service-alerts" class="btn btn-primary btn-sm" disabled>
                    {{ devicemonitor_t('Save alert preferences') }}
                </button>
            </div>
        </div>

        <div class="panel panel-default" id="physical-device-grouping">
            <div class="panel-heading">
                <strong>
                    <i class="fa fa-sitemap"></i>
                    {{ devicemonitor_t('Device Profile') }}
                </strong>
            </div>
            <div class="panel-body" id="physical-device-content">
                <div class="text-muted">
                    {{ devicemonitor_t('Loading device profile...') }}
                </div>
            </div>
        </div>

        <div class="panel panel-default" id="lifecycle-history">
            <div class="panel-heading">
                <strong>
                    <i class="fa fa-history"></i>
                    {{ devicemonitor_t('Lifecycle History') }}
                </strong>
                <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('About Lifecycle History') }}"
                        data-content="{{ devicemonitor_t('A lifecycle is one continuous period during which this MAC address is treated as the same known device. Earlier lifecycles are archived, not deleted, and remain available below.') }}">
                    <i class="fa fa-info-circle" aria-hidden="true"></i>
                </button>
                <span class="text-muted" style="margin-left:10px;">
                    {{ devicemonitor_t('MAC address') }}:
                    <span id="device-history-mac"></span>
                </span>
            </div>

            <div id="return-resolution-controls"
                 style="display:none;padding:10px 15px;border-bottom:1px solid #ddd;">
                <button id="btn-start-new-lifecycle"
                        type="button"
                        class="btn btn-sm btn-primary">
                    <i class="fa fa-plus-circle"></i>
                    {{ devicemonitor_t('Start New Lifecycle') }}
                </button>
                <span class="text-muted" style="margin-left:8px;">
                    {{ devicemonitor_t('Use this when the returning device should be treated as new.') }}
                </span>
            </div>

            <div class="table-responsive">
                <table class="table table-condensed table-hover table-striped"
                       id="grid-device-history">
                    <thead>
                        <tr>
                            <th>{{ devicemonitor_t('Lifecycle') }}</th>
                            <th>{{ devicemonitor_t('Status') }}</th>
                            <th>{{ devicemonitor_t('IP Address') }}</th>
                            <th>{{ devicemonitor_t('Friendly Name') }}</th>
                            <th>{{ devicemonitor_t('Hostname') }}</th>
                            <th>{{ devicemonitor_t('Vendor') }}</th>
                            <th>{{ devicemonitor_t('VLAN') }}</th>
                            <th>{{ devicemonitor_t('First Seen') }}</th>
                            <th>{{ devicemonitor_t('Last Seen') }}</th>
                            <th>{{ devicemonitor_t('Notes') }}</th>
                            <th class="text-center">{{ devicemonitor_t('Actions') }}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td colspan="11" class="text-muted">
                                {{ devicemonitor_t('Loading device history...') }}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <div class="panel panel-default" id="device-notes">
            <div class="panel-heading">
                <strong>
                    <i class="fa fa-comment-o"></i>
                    {{ devicemonitor_t('Notes') }}
                </strong>
                <span id="current-lifecycle-badge"
                      class="label label-success"
                      style="display:none;margin-left:8px;"></span>
            </div>

            <div class="panel-body">
                <div id="notes-no-active"
                     class="alert alert-info"
                     style="display:none;margin-bottom:10px;">
                    {{ devicemonitor_t('There is no active lifecycle. Resolve the returning device in Lifecycle History before adding notes.') }}
                </div>

                <div id="notes-editor" style="display:none;margin-bottom:15px;">
                    <label for="new-note-text">{{ devicemonitor_t('Add Note') }}</label>
                    <textarea id="new-note-text"
                              class="form-control"
                              rows="3"
                              style="width:100%;max-width:none;box-sizing:border-box;resize:vertical;"
                              placeholder="{{ devicemonitor_t('Enter a new note...') }}"></textarea>
                    <button id="btn-add-note"
                            type="button"
                            class="btn btn-xs btn-primary"
                            style="margin-top:8px;">
                        <i class="fa fa-plus"></i>
                        {{ devicemonitor_t('Add Note') }}
                    </button>
                </div>

                <div id="current-notes">
                    <div class="text-muted">{{ devicemonitor_t('Loading notes...') }}</div>
                </div>
            </div>
        </div>

    </div>
</div>

<script>
$(document).ready(function() {
    $('.dm-info').popover({container:'body', placement:'auto right', trigger:'focus'});
    $('.dm-info').on('keydown', function(event) {
        if (event.key === 'Escape') { $(this).popover('hide').trigger('blur'); }
    });
    var params = new URLSearchParams(window.location.search);
    var mac = (params.get('mac') || '').trim().toLowerCase();
    $('#service-alert-settings-link').attr('href',
        '/ui/devicemonitor/index/settings?return=' +
        encodeURIComponent(window.location.pathname + window.location.search) +
        '#tab-email');
    function showServiceAlertToast(message, success) {
        var $toast = $('<div>').attr({role: 'status', 'aria-live': 'polite'})
            .css({position: 'fixed', top: '20px', right: '20px',
                'background-color': success ? '#4CAF50' : '#f44336',
                color: 'white', padding: '15px 20px', 'border-radius': '4px',
                'box-shadow': '0 4px 8px rgba(0,0,0,.3)', 'z-index': 9999,
                'min-width': '280px', display: 'none'});
        $('<i>').addClass('fa ' + (success ? 'fa-check-circle' : 'fa-exclamation-circle'))
            .appendTo($toast);
        $toast.append(document.createTextNode(' ' + message)).appendTo('body')
            .fadeIn(300);
        setTimeout(function() {
            $toast.fadeOut(300, function() { $toast.remove(); });
        }, 3000);
    }

    function renderServiceAlertPreferences(response) {
        $('#service-alert-preferences tbody tr').each(function() {
            var field = $(this).attr('data-alert-field');
            $(this).find('select').val(response.preferences[field])
                .selectpicker('refresh');
            $(this).find('.alert-effective').text(
                response.effective[field]
                    ? {{ lang.query('Enabled')|json_encode(15) }}
                    : {{ lang.query('Disabled')|json_encode(15) }}
            );
        });
        $('#save-service-alerts').prop('disabled', false);
        var deliveryMessages = {
            email_disabled: {{ lang.query('These preferences are saved, but this network identity’s service alert emails will not be sent because global email notifications are turned off.')|json_encode(15) }},
            monitoring_disabled: {{ lang.query('These preferences are saved, but this network identity’s service alert emails will not be sent because monitoring is turned off.')|json_encode(15) }},
            recipient_missing: {{ lang.query('These preferences are saved, but this network identity’s service alert emails will not be sent because no email recipient is configured in Settings.')|json_encode(15) }}
        };
        $('#service-alert-delivery-reason').text(
            deliveryMessages[response.email_unavailable_reason] ||
            {{ lang.query('These preferences are saved, but service alert email delivery is unavailable.')|json_encode(15) }}
        );
        $('#service-alert-delivery').toggle(!response.email_available);
    }

    function loadServiceAlertPreferences() {
        $.getJSON('/api/devicemonitor/devices/alertpreferences', {mac: mac})
            .done(function(response) {
                if (response && response.result === 'ok') {
                    renderServiceAlertPreferences(response);
                } else {
                    showServiceAlertToast({{ lang.query('Unable to load alert preferences')|json_encode(15) }}, false);
                }
            }).fail(function() {
                showServiceAlertToast({{ lang.query('Unable to load alert preferences')|json_encode(15) }}, false);
            });
    }

    $('#save-service-alerts').on('click', function() {
        var $button = $(this);
        var originalLabel = $button.html();
        $button.prop('disabled', true).html(
            ("<i class='fa fa-spinner fa-spin'></i> " + {{ lang.query('Saving...')|json_encode(15) }})
        );
        var values = {mac: mac};
        $('#service-alert-preferences tbody tr').each(function() {
            values[$(this).attr('data-alert-field')] = $(this).find('select').val();
        });
        $.post('/api/devicemonitor/devices/savealertpreferences', values)
            .done(function(response) {
                if (response && response.result === 'saved') {
                    renderServiceAlertPreferences(response);
                    showServiceAlertToast({{ lang.query('Alert preferences saved')|json_encode(15) }}, true);
                } else {
                    showServiceAlertToast(
                        response && response.error
                            ? response.error
                            : {{ lang.query('Unable to save alert preferences')|json_encode(15) }},
                        false
                    );
                }
            }).fail(function() {
                showServiceAlertToast({{ lang.query('Unable to save alert preferences')|json_encode(15) }}, false);
            }).always(function() {
                $button.prop('disabled', false).html(originalLabel);
            });
    });

    if (mac) {
        loadServiceAlertPreferences();
    }
    var returnPending = false;
    var activeLifecycleId = 0;

    function dash(value) {
        return value === null || value === undefined || value === ''
            ? '\u2014'
            : value;
    }

    function hostnameSourceLabel(source) {
        var labels = {
            adguard: 'AdGuard DNS rewrite',
            dnsmasq: 'Dnsmasq',
            kea: 'Kea DHCP',
            isc: 'ISC DHCP',
            unbound: 'Unbound',
            pihole: 'Pi-hole',
            hostwatch: 'Hostwatch'
        };

        return labels[source] || source || '';
    }

    function showToast(msg, type) {
        var bg = type === 'success'
            ? '#4CAF50'
            : (type === 'error' ? '#f44336' : '#2196F3');
        var ic = type === 'success'
            ? 'fa-check-circle'
            : (type === 'error'
                ? 'fa-exclamation-circle'
                : 'fa-info-circle');

        var $t = $('<div>').css({
            position: 'fixed',
            top: '20px',
            right: '20px',
            'background-color': bg,
            color: 'white',
            padding: '15px 20px',
            'border-radius': '4px',
            'box-shadow': '0 4px 8px rgba(0,0,0,.3)',
            'z-index': 9999,
            'min-width': '280px',
            display: 'none'
        }).html('<i class="fa ' + ic + '"></i> ' + msg);

        $('body').append($t);
        $t.fadeIn(300);

        setTimeout(function() {
            $t.fadeOut(300, function() {
                $t.remove();
            });
        }, 3000);
    }

    function showError(message) {
        showToast(message, 'error');
    }

    function resolveLifecycle(url, data, button, successMessage) {
        button.prop('disabled', true);

        $.ajax({
            url: url,
            type: 'POST',
            data: data,
            success: function(result) {
                if (result && result.result === 'saved') {
                    showToast(successMessage, 'success');
                    window.location.reload();
                    return;
                }

                button.prop('disabled', false);
                showError(
                    result && result.error
                        ? result.error
                        : 'Unable to resolve returning device'
                );
            },
            error: function(xhr) {
                button.prop('disabled', false);
                var message = 'Unable to resolve returning device';

                if (xhr.responseJSON && xhr.responseJSON.error) {
                    message = xhr.responseJSON.error;
                }

                showError(message);
            }
        });
    }

    function findActiveLifecycle(rows) {
        var active = null;

        rows.some(function(row) {
            if (row.status === 'active') {
                active = row;
                return true;
            }
            return false;
        });

        return active;
    }

    function renderSummary(rows, deviceState) {
        var active = findActiveLifecycle(rows);
        var row = active || (rows.length ? rows[0] : null);

        activeLifecycleId = active
            ? (parseInt(active.id, 10) || 0)
            : 0;

        $('#summary-mac').text(mac || '\u2014');

        var $status = $('#summary-status').empty();
        var hasDeviceStatus = deviceState &&
            deviceState.is_active !== undefined &&
            deviceState.is_active !== null;

        if (hasDeviceStatus) {
            var online = (
                deviceState.is_active === 1 ||
                deviceState.is_active === '1'
            );

            $('<span>')
                .addClass(
                    'label ' +
                    (online ? 'label-success' : 'label-default')
                )
                .text(online ? 'ONLINE' : 'OFFLINE')
                .appendTo($status);
        } else {
            $status.text('\u2014');
        }

        if (!row) {
            $('#summary-friendly-name,#summary-ip,#summary-vendor,#summary-vlan,#summary-hostname,#summary-first-seen,#summary-last-seen,#summary-lifecycle')
                .text('\u2014');
            $('#current-lifecycle-badge').hide().text('');
            $('#notes-editor').hide();
            $('#notes-no-active').show();
            return;
        }

        $('#summary-friendly-name').text(
            dash(row.custom_hostname || row.hostname)
        );
        $('#summary-ip').text(dash(row.ip));
        $('#summary-vendor').text(dash(row.vendor));
        $('#summary-vlan').text(dash(row.vlan));

        $('#summary-hostname').empty().text(dash(row.hostname));
        var hostnameSource = (row.hostname_source || '').toString().trim();
        if (hostnameSource) {
            $('<div>')
                .addClass('text-muted')
                .css('font-size', '11px')
                .text(hostnameSourceLabel(hostnameSource))
                .appendTo($('#summary-hostname'));
        }

        $('#summary-first-seen').text(dash(row.first_seen));
        $('#summary-last-seen').text(dash(row.last_seen));

        if (active) {
            $('#summary-lifecycle').text('#' + active.id + ' (active)');
        } else if (returnPending) {
            $('#summary-lifecycle').text({{ lang.query('Pending decision')|json_encode(15) }});
        } else {
            $('#summary-lifecycle').text(
                row.id
                    ? '#' + row.id + ' (' + dash(row.status) + ')'
                    : '\u2014'
            );
        }

        $('#current-lifecycle-badge')
            .toggle(!!activeLifecycleId)
            .text(
                activeLifecycleId
                    ? 'Active Lifecycle #' + activeLifecycleId
                    : ''
            );

        $('#notes-editor').toggle(!!activeLifecycleId);
        $('#notes-no-active').toggle(!activeLifecycleId);
    }

    function addNoteEvent($body, label, timestamp, text, labelClass) {
        var $event = $('<span>')
            .addClass('label ' + labelClass)
            .text(label);

        $('<tr>').append(
            $('<td>')
                .css({
                    'white-space': 'pre-wrap',
                    'overflow-wrap': 'anywhere'
                })
                .text(text || '\u2014'),
            $('<td>').append($event),
            $('<td>').text(timestamp || '\u2014')
        ).prependTo($body);
    }

    function updateNote(lifecycleId, comment) {
        var value = window.prompt(
            {{ lang.query('Edit note')|json_encode(15) }},
            comment.comment || ''
        );

        if (value === null) {
            return;
        }

        value = value.trim();

        if (!value) {
            showError({{ lang.query('Note cannot be empty')|json_encode(15) }});
            return;
        }

        $.ajax({
            url: '/api/devicemonitor/devices/updatecomment',
            type: 'POST',
            data: {
                lifecycle_id: lifecycleId,
                id: comment.id,
                comment: value
            },
            success: function(response) {
                if (response && response.result === 'saved') {
                    showToast({{ lang.query('Note updated')|json_encode(15) }}, 'success');
                    loadDeviceData();
                    return;
                }

                showError({{ lang.query('Unable to update note')|json_encode(15) }});
            },
            error: function() {
                showError({{ lang.query('Unable to update note')|json_encode(15) }});
            }
        });
    }

    function deleteNote(lifecycleId, comment, commentNumber) {
        if (!confirm({{ lang.query('Archive Note #')|json_encode(15) }} + commentNumber + '?')) {
            return;
        }

        $.ajax({
            url: '/api/devicemonitor/devices/deletecomment',
            type: 'POST',
            data: {
                lifecycle_id: lifecycleId,
                id: comment.id
            },
            success: function(response) {
                if (response && response.result === 'deleted') {
                    showToast({{ lang.query('Note archived')|json_encode(15) }}, 'success');
                    loadDeviceData();
                    return;
                }

                showError({{ lang.query('Unable to archive note')|json_encode(15) }});
            },
            error: function() {
                showError({{ lang.query('Unable to archive note')|json_encode(15) }});
            }
        });
    }

    function renderNotes($container, comments, lifecycleId, editable) {
        $container.removeClass('text-danger').empty();

        if (!Array.isArray(comments) || !comments.length) {
            $('<div>')
                .addClass('text-muted')
                .text({{ lang.query('No notes')|json_encode(15) }})
                .appendTo($container);
            return;
        }

        comments.forEach(function(comment, index) {
            var commentNumber = comments.length - index;

            var $table = $('<table>')
                .addClass('table table-condensed table-bordered')
                .css('margin-bottom', '10px');

            var $titleCell = $('<th>')
                .text({{ lang.query('Note #')|json_encode(15) }} + commentNumber);

            var $head = $('<thead>').append(
                $('<tr>')
                    .addClass('active')
                    .append(
                        $titleCell,
                        $('<th>')
                            .css('width', '90px')
                            .text({{ lang.query('Action')|json_encode(15) }}),
                        $('<th>')
                            .css('width', '220px')
                            .text({{ lang.query('Date / time')|json_encode(15) }})
                    )
            );

            var $body = $('<tbody>');
            var versions = Array.isArray(comment.versions)
                ? comment.versions
                : [];
            var createdText = '';
            var editedCount = 0;

            versions.forEach(function(version) {
                var action =
                    (version.action || '').toLowerCase();

                if (action === 'created' && !createdText) {
                    createdText = version.comment || '';
                }
            });

            if (!createdText) {
                if (
                    !comment.updated_at ||
                    comment.updated_at === comment.created_at
                ) {
                    createdText = comment.comment || '';
                }
            }

            addNoteEvent(
                $body,
                'Created',
                comment.created_at,
                createdText,
                'label-success'
            );

            versions.forEach(function(version) {
                var action =
                    (version.action || '').toLowerCase();

                if (action === 'edited') {
                    editedCount += 1;
                    addNoteEvent(
                        $body,
                        'Edited',
                        version.created_at,
                        version.comment || '',
                        'label-info'
                    );
                }
            });

            if (
                editedCount === 0 &&
                comment.updated_at &&
                comment.updated_at !== comment.created_at
            ) {
                addNoteEvent(
                    $body,
                    'Edited',
                    comment.updated_at,
                    comment.comment || '',
                    'label-info'
                );
            }

            if (comment.deleted_at) {
                addNoteEvent(
                    $body,
                    'Archived',
                    comment.deleted_at,
                    '',
                    'label-danger'
                );
            }

            if (editable && !comment.deleted_at) {
                var $currentCell = $body
                    .children('tr')
                    .first()
                    .children('td')
                    .first();

                var currentText = $currentCell.text();

                var $noteLine = $('<div>').css({
                    display: 'flex',
                    'align-items': 'center',
                    'justify-content': 'space-between'
                });

                var $noteText = $('<span>')
                    .css({
                        'white-space': 'pre-wrap',
                        'overflow-wrap': 'anywhere',
                        'min-width': 0,
                        flex: '1 1 auto'
                    })
                    .text(currentText);

                var $controls = $('<span>').css({
                    'white-space': 'nowrap',
                    'margin-left': '12px',
                    flex: '0 0 auto'
                });

                $('<button>')
                    .attr('type', 'button')
                    .addClass('btn btn-xs btn-default')
                    .css({
                        'margin-right': '4px',
                        width: '72px'
                    })
                    .html('<i class="fa fa-pencil"></i> Edit')
                    .on('click', function() {
                        updateNote(lifecycleId, comment);
                    })
                    .appendTo($controls);

                $('<button>')
                    .attr('type', 'button')
                    .addClass('btn btn-xs btn-default')
                    .css('width', '72px')
                    .html('<i class="fa fa-archive"></i> Archive')
                    .on('click', function() {
                        deleteNote(
                            lifecycleId,
                            comment,
                            commentNumber
                        );
                    })
                    .appendTo($controls);

                $noteLine.append($noteText, $controls);
                $currentCell.empty().append($noteLine);
            }

            $table.append($head, $body);
            $table.appendTo($container);
        });
    }

    function loadCurrentNotes() {
        var $container = $('#current-notes');

        if (!activeLifecycleId) {
            $container
                .removeClass('text-danger')
                .empty()
                .append(
                    $('<div>')
                        .addClass('text-muted')
                        .text({{ lang.query('No active lifecycle notes')|json_encode(15) }})
                );
            return;
        }

        $container
            .removeClass('text-danger')
            .empty()
            .append(
                $('<div>')
                    .addClass('text-muted')
                    .text({{ lang.query('Loading notes...')|json_encode(15) }})
            );

        $.ajax({
            url: '/api/devicemonitor/devices/comments',
            type: 'GET',
            data: { lifecycle_id: activeLifecycleId },
            success: function(result) {
                if (
                    !result ||
                    result.result !== 'ok' ||
                    !Array.isArray(result.comments)
                ) {
                    $container
                        .empty()
                        .addClass('text-danger')
                        .text({{ lang.query('Unable to load notes')|json_encode(15) }});
                    return;
                }

                renderNotes(
                    $container,
                    result.comments,
                    activeLifecycleId,
                    true
                );
            },
            error: function() {
                $container
                    .empty()
                    .addClass('text-danger')
                    .text({{ lang.query('Unable to load notes')|json_encode(15) }});
            }
        });
    }

    function renderHistory(rows) {
        var $tbody = $('#grid-device-history tbody').empty();

        if (!rows.length) {
            $('<tr>').append(
                $('<td>')
                    .attr('colspan', 11)
                    .addClass('text-muted')
                    .text({{ lang.query('No lifecycle history recorded')|json_encode(15) }})
            ).appendTo($tbody);
            return;
        }

        rows.forEach(function(row) {
            var $actions = $('<span>');

            if (returnPending && row.status === 'archived') {
                $('<button>')
                    .attr({
                        type: 'button',
                        title: {{ lang.query('Relink returning device to this lifecycle')|json_encode(15) }}
                    })
                    .addClass('btn btn-xs btn-warning')
                    .html(('<i class="fa fa-link"></i> ' + {{ lang.query('Relink')|json_encode(15) }}))
                    .on('click', function() {
                        if (
                            !confirm(
                                ({{ lang.query('Relink')|json_encode(15) }} + " ") +
                                mac +
                                (" " + {{ lang.query('to lifecycle #')|json_encode(15) }}) +
                                row.id +
                                '?'
                            )
                        ) {
                            return;
                        }

                        resolveLifecycle(
                            '/api/devicemonitor/devices/relinklifecycle',
                            {
                                mac: mac,
                                lifecycle_id: row.id
                            },
                            $(this),
                            'Device relinked to previous lifecycle'
                        );
                    })
                    .appendTo($actions);
            }

            var $status = $('<span>')
                .addClass(
                    row.status === 'active'
                        ? 'label label-success'
                        : 'label label-default'
                )
                .text(dash(row.status));

            var commentCount =
                parseInt(row.comment_count, 10) || 0;
            var $commentsCell = $('<td>');

            if (row.status === 'active') {
                $('<span>')
                    .text(commentCount)
                    .appendTo($commentsCell);
            } else if (commentCount > 0) {
                $('<button>')
                    .attr({
                        type: 'button',
                        'data-lifecycle-id': row.id
                    })
                    .addClass(
                        'btn btn-xs btn-default command-history-comments'
                    )
                    .text({{ lang.query('View (')|json_encode(15) }} + commentCount + ')')
                    .appendTo($commentsCell);
            } else {
                $('<span>')
                    .addClass('text-muted')
                    .text('0')
                    .appendTo($commentsCell);
            }

            $('<tr>').append(
                $('<td>').text('#' + row.id),
                $('<td>').append($status),
                $('<td>').text(dash(row.ip)),
                $('<td>').text(dash(row.custom_hostname)),
                $('<td>').text(dash(row.hostname)),
                $('<td>').text(dash(row.vendor)),
                $('<td>').text(dash(row.vlan)),
                $('<td>').text(dash(row.first_seen)),
                $('<td>').text(dash(row.last_seen)),
                $commentsCell,
                $('<td>')
                    .addClass('text-center')
                    .append($actions)
            ).appendTo($tbody);
        });
    }

    $('#grid-device-history')
        .off('click', '.command-history-comments')
        .on('click', '.command-history-comments', function() {
            var $button = $(this);
            var lifecycleId =
                parseInt($button.data('lifecycle-id'), 10) || 0;
            var $row = $button.closest('tr');
            var $existing =
                $row.next('.lifecycle-comments-row');

            if ($existing.length) {
                $existing.remove();
                return;
            }

            var $detailRow = $('<tr>')
                .addClass('lifecycle-comments-row');

            var $detailCell = $('<td>')
                .attr('colspan', 11)
                .css('padding', '10px 20px');

            $detailRow.append($detailCell);
            $row.after($detailRow);

            $detailCell.text({{ lang.query('Loading notes...')|json_encode(15) }});

            $.ajax({
                url: '/api/devicemonitor/devices/comments',
                type: 'GET',
                data: { lifecycle_id: lifecycleId },
                success: function(result) {
                    if (
                        !result ||
                        result.result !== 'ok' ||
                        !Array.isArray(result.comments)
                    ) {
                        $detailCell
                            .empty()
                            .addClass('text-danger')
                            .text({{ lang.query('Unable to load notes')|json_encode(15) }});
                        return;
                    }

                    renderNotes(
                        $detailCell,
                        result.comments,
                        lifecycleId,
                        false
                    );
                },
                error: function() {
                    $detailCell
                        .empty()
                        .addClass('text-danger')
                        .text({{ lang.query('Unable to load notes')|json_encode(15) }});
                }
            });
        });

    $('#btn-add-note').on('click', function() {
        var $button = $(this);
        var value = $('#new-note-text').val().trim();

        if (!activeLifecycleId) {
            showError({{ lang.query('No active lifecycle')|json_encode(15) }});
            return;
        }

        if (!value) {
            showError({{ lang.query('Enter a note first')|json_encode(15) }});
            return;
        }

        $button.prop('disabled', true);

        $.ajax({
            url: '/api/devicemonitor/devices/addcomment',
            type: 'POST',
            data: {
                lifecycle_id: activeLifecycleId,
                comment: value
            },
            success: function(response) {
                $button.prop('disabled', false);

                if (response && response.result === 'saved') {
                    $('#new-note-text').val('');
                    showToast({{ lang.query('Note added')|json_encode(15) }}, 'success');
                    loadDeviceData();
                    return;
                }

                showError({{ lang.query('Unable to add note')|json_encode(15) }});
            },
            error: function() {
                $button.prop('disabled', false);
                showError({{ lang.query('Unable to add note')|json_encode(15) }});
            }
        });
    });

    $('#btn-start-new-lifecycle').on('click', function() {
        if (
            !confirm(
                ({{ lang.query('Start a new lifecycle for returning device')|json_encode(15) }} + " ") +
                mac +
                '?'
            )
        ) {
            return;
        }

        resolveLifecycle(
            '/api/devicemonitor/devices/startnewlifecycle',
            {mac: mac},
            $(this),
            'New device lifecycle started'
        );
    });

    function physicalDeviceError(message) {
        $('#physical-device-content')
            .empty()
            .addClass('text-danger')
            .text(message);
    }

    function loadPhysicalDevice() {
        $('#physical-device-content')
            .removeClass('text-danger')
            .empty()
            .append(
                $('<div>')
                    .addClass('text-muted')
                    .text({{ lang.query('Loading device profile...')|json_encode(15) }})
            );

        $.ajax({
            url: '/api/devicemonitor/devices/physicaldevice',
            type: 'GET',
            data: {mac: mac},
            success: function(result) {
                if (!result || result.result !== 'ok') {
                    physicalDeviceError(
                        result && result.error
                            ? result.error
                            : 'Unable to load device profile'
                    );
                    return;
                }

                renderPhysicalDeviceSummary(result.physical_device || null);
            },
            error: function() {
                physicalDeviceError('Unable to load device profile');
            }
        });
    }

    function renderPhysicalDeviceSummary(physicalDevice) {
        var $container = $('#physical-device-content')
            .removeClass('text-danger')
            .empty();

        var physicalDeviceId = physicalDevice
            ? (parseInt(physicalDevice.id, 10) || 0)
            : 0;
        var physicalDeviceName = physicalDevice
            ? (physicalDevice.name || ('Device profile #' + physicalDeviceId))
            : '';
        var members = physicalDevice && Array.isArray(physicalDevice.members)
            ? physicalDevice.members
            : [];
        var memberCount = members.length;

        var $table = $('<table>')
            .addClass('table table-condensed')
            .css('margin-bottom', '12px');

        var $tbody = $('<tbody>');

        $tbody.append(
            $('<tr>').append(
                $('<th>').css('width', '160px').text({{ lang.query('Device')|json_encode(15) }}),
                $('<td>').text(physicalDeviceName || '\u2014')
            )
        );

        if (physicalDevice) {
            $tbody.append(
                $('<tr>').append(
                    $('<th>').text({{ lang.query('Identities')|json_encode(15) }}),
                    $('<td>').text(memberCount + ' current')
                )
            );
        }

        $table.append($tbody).appendTo($container);

        var $actions = $('<div>');

        if (physicalDevice) {
            $('<a>')
                .attr({
                    href: '/ui/devicemonitor/index/physicaldevices?group=' +
                        encodeURIComponent(physicalDeviceId),
                    title: {{ lang.query('Open this profile')|json_encode(15) }}
                })
                .addClass('btn btn-xs btn-primary')
                .html(
                    '<i class="fa fa-sitemap"></i> ' +
                    {{ lang.query('Open Profile')|json_encode(15) }}
                )
                .appendTo($actions);
        } else {
            $('<a>')
                .attr({
                    href: '/ui/devicemonitor/index/physicaldevices',
                    title: {{ lang.query('Add this network identity to a device profile')|json_encode(15) }}
                })
                .addClass('btn btn-xs btn-primary')
                .html(
                    '<i class="fa fa-sitemap"></i> ' +
                    {{ lang.query('Add to Profile')|json_encode(15) }}
                )
                .appendTo($actions);
        }

        $actions.appendTo($container);
    }

    function showLoadError(message) {
        $('#grid-device-history tbody')
            .empty()
            .append(
                $('<tr>').append(
                    $('<td>')
                        .attr('colspan', 11)
                        .addClass('text-danger')
                        .text(message)
                )
            );

        $('#current-notes')
            .empty()
            .addClass('text-danger')
            .text(message);
    }

    function loadDeviceData() {
        $.ajax({
            url: '/api/devicemonitor/devices/lifecycles',
            type: 'GET',
            data: {mac: mac},
            success: function(data) {
                if (!data || data.result !== 'ok') {
                    showLoadError(
                        data && data.error
                            ? data.error
                            : 'Unable to load device details'
                    );
                    return;
                }

                returnPending = !!(
                    data.device_state &&
                    (
                        data.device_state.return_pending === 1 ||
                        data.device_state.return_pending === '1'
                    )
                );

                $('#return-resolution-controls')
                    .toggle(returnPending);

                var rows = Array.isArray(data.lifecycles)
                    ? data.lifecycles
                    : [];

                renderSummary(rows, data.device_state || null);
                renderHistory(rows);
                loadCurrentNotes();
            },
            error: function() {
                showLoadError('Unable to load device details');
            }
        });
    }

    $('#device-history-mac').text(mac || '\u2014');

    $('#activity-timeline-link').attr(
        'href',
        '/ui/devicemonitor/index/activitytimeline?mac=' +
            encodeURIComponent(mac)
    );

    if (!mac) {
        showLoadError('MAC address required');
        return;
    }

    loadDeviceData();
    loadPhysicalDevice();
});
</script>
