<style>
.content-box .label {
    font-size: 12px;
}
</style>

<div class="content-box">
    <div class="content-box-main">

        <div style="padding:10px 10px 8px 10px;border-bottom:1px solid #333;margin-bottom:12px;">
            <a href="/ui/devicemonitor/index/devices"
               class="btn btn-default btn-sm pull-right"
               style="font-size:14px;font-weight:600;padding:6px 12px;">
                <i class="fa fa-arrow-left"></i>
                {{ lang._('Back to Devices') }}
            </a>

            <a id="activity-timeline-link"
               href="/ui/devicemonitor/index/activitytimeline"
               class="btn btn-default btn-sm pull-right"
               style="font-size:14px;font-weight:600;padding:6px 12px;margin-right:6px;">
                <i class="fa fa-clock-o"></i>
                {{ lang._('Activity Timeline') }}
            </a>
            <h1 style="margin:0;font-size:20px;">
                {{ lang._('Device Monitor') }}
                <span style="color:#555;margin:0 8px;">&ndash;</span>
                <span style="font-weight:normal;">{{ lang._('Device Details') }}</span>
            </h1>
        </div>

        <div class="panel panel-default">
            <div class="panel-heading">
                <strong>
                    <i class="fa fa-desktop"></i>
                    {{ lang._('Device Summary') }}
                </strong>
            </div>
            <div class="panel-body" style="padding-bottom:5px;">
                <div class="row">
                    <div class="col-md-6">
                        <table class="table table-condensed" style="margin-bottom:5px;">
                            <tbody>
                                <tr><th style="width:135px;">{{ lang._('Friendly Name') }}</th><td id="summary-friendly-name">&mdash;</td></tr>
                                <tr><th>{{ lang._('MAC Address') }}</th><td id="summary-mac">&mdash;</td></tr>
                                <tr><th>{{ lang._('IP Address') }}</th><td id="summary-ip">&mdash;</td></tr>
                                <tr><th>{{ lang._('Vendor') }}</th><td id="summary-vendor">&mdash;</td></tr>
                                <tr><th>{{ lang._('VLAN') }}</th><td id="summary-vlan">&mdash;</td></tr>
                                <tr><th>{{ lang._('Status') }}</th><td id="summary-status">&mdash;</td></tr>
                            </tbody>
                        </table>
                    </div>

                    <div class="col-md-6">
                        <table class="table table-condensed" style="margin-bottom:5px;">
                            <tbody>
                                <tr><th style="width:135px;">{{ lang._('Hostname') }}</th><td id="summary-hostname">&mdash;</td></tr>
                                <tr><th>{{ lang._('Current Lifecycle') }}</th><td id="summary-lifecycle">&mdash;</td></tr>
                                <tr><th>{{ lang._('First Seen') }}</th><td id="summary-first-seen">&mdash;</td></tr>
                                <tr><th>{{ lang._('Last Seen') }}</th><td id="summary-last-seen">&mdash;</td></tr>
                                <tr><th>{{ lang._('Notes') }}</th><td id="summary-note-count">0</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <div class="panel panel-default" id="physical-device-grouping">
            <div class="panel-heading">
                <strong>
                    <i class="fa fa-sitemap"></i>
                    {{ lang._('Physical Device / Related Identities') }}
                </strong>
            </div>
            <div class="panel-body" id="physical-device-content">
                <div class="text-muted">
                    {{ lang._('Loading physical-device grouping...') }}
                </div>
            </div>
        </div>

        <div class="panel panel-default" id="device-notes">
            <div class="panel-heading">
                <strong>
                    <i class="fa fa-comment-o"></i>
                    {{ lang._('Notes') }}
                </strong>
                <span id="current-lifecycle-badge"
                      class="label label-success"
                      style="display:none;margin-left:8px;"></span>
            </div>

            <div class="panel-body">
                <div id="notes-no-active"
                     class="alert alert-info"
                     style="display:none;margin-bottom:10px;">
                    {{ lang._('There is no active lifecycle. Resolve the returning device in Lifecycle History before adding notes.') }}
                </div>

                <div id="notes-editor" style="display:none;margin-bottom:15px;">
                    <label for="new-note-text">{{ lang._('Add Note') }}</label>
                    <textarea id="new-note-text"
                              class="form-control"
                              rows="3"
                              style="width:100%;max-width:none;box-sizing:border-box;resize:vertical;"
                              placeholder="{{ lang._('Enter a new note...') }}"></textarea>
                    <button id="btn-add-note"
                            type="button"
                            class="btn btn-sm btn-primary"
                            style="margin-top:8px;">
                        <i class="fa fa-plus"></i>
                        {{ lang._('Add Note') }}
                    </button>
                </div>

                <div id="current-notes">
                    <div class="text-muted">{{ lang._('Loading notes...') }}</div>
                </div>
            </div>
        </div>

        <div class="panel panel-default" id="lifecycle-history">
            <div class="panel-heading">
                <strong>
                    <i class="fa fa-history"></i>
                    {{ lang._('Lifecycle History') }}
                </strong>
                <span class="text-muted" style="margin-left:10px;">
                    {{ lang._('MAC address') }}:
                    <span id="device-history-mac"></span>
                </span>
            </div>

            <div id="return-resolution-controls"
                 style="display:none;padding:10px 15px;border-bottom:1px solid #ddd;">
                <button id="btn-start-new-lifecycle"
                        type="button"
                        class="btn btn-sm btn-primary">
                    <i class="fa fa-plus-circle"></i>
                    {{ lang._('Start New Lifecycle') }}
                </button>
                <span class="text-muted" style="margin-left:8px;">
                    {{ lang._('Use this when the returning device should be treated as new.') }}
                </span>
            </div>

            <div class="table-responsive">
                <table class="table table-condensed table-hover table-striped"
                       id="grid-device-history">
                    <thead>
                        <tr>
                            <th>{{ lang._('Lifecycle') }}</th>
                            <th>{{ lang._('Status') }}</th>
                            <th>{{ lang._('Friendly Name') }}</th>
                            <th>{{ lang._('Hostname') }}</th>
                            <th>{{ lang._('IP Address') }}</th>
                            <th>{{ lang._('Vendor') }}</th>
                            <th>{{ lang._('VLAN') }}</th>
                            <th>{{ lang._('First Seen') }}</th>
                            <th>{{ lang._('Last Seen') }}</th>
                            <th>{{ lang._('Notes') }}</th>
                            <th class="text-center">{{ lang._('Actions') }}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td colspan="11" class="text-muted">
                                {{ lang._('Loading device history...') }}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

    </div>
</div>

<script>
$(document).ready(function() {
    var params = new URLSearchParams(window.location.search);
    var mac = (params.get('mac') || '').trim().toLowerCase();
    var returnPending = false;
    var activeLifecycleId = 0;

    function dash(value) {
        return value === null || value === undefined || value === ''
            ? '\u2014'
            : value;
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
            $('#summary-note-count').text('0');
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
        $('#summary-hostname').text(dash(row.hostname));
        $('#summary-first-seen').text(dash(row.first_seen));
        $('#summary-last-seen').text(dash(row.last_seen));

        if (active) {
            $('#summary-lifecycle').text('#' + active.id + ' (active)');
            $('#summary-note-count').text(
                parseInt(active.comment_count, 10) || 0
            );
        } else if (returnPending) {
            $('#summary-lifecycle').text('Pending decision');
            $('#summary-note-count').text('0');
        } else {
            $('#summary-lifecycle').text(
                row.id
                    ? '#' + row.id + ' (' + dash(row.status) + ')'
                    : '\u2014'
            );
            $('#summary-note-count').text(
                parseInt(row.comment_count, 10) || 0
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
            'Edit note',
            comment.comment || ''
        );

        if (value === null) {
            return;
        }

        value = value.trim();

        if (!value) {
            showError('Note cannot be empty');
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
                    showToast('Note updated', 'success');
                    loadDeviceData();
                    return;
                }

                showError('Unable to update note');
            },
            error: function() {
                showError('Unable to update note');
            }
        });
    }

    function deleteNote(lifecycleId, comment, commentNumber) {
        if (!confirm('Archive Note #' + commentNumber + '?')) {
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
                    showToast('Note archived', 'success');
                    loadDeviceData();
                    return;
                }

                showError('Unable to archive note');
            },
            error: function() {
                showError('Unable to archive note');
            }
        });
    }

    function renderNotes($container, comments, lifecycleId, editable) {
        $container.removeClass('text-danger').empty();

        if (!Array.isArray(comments) || !comments.length) {
            $('<div>')
                .addClass('text-muted')
                .text('No notes')
                .appendTo($container);
            return;
        }

        comments.forEach(function(comment, index) {
            var commentNumber = comments.length - index;

            var $table = $('<table>')
                .addClass('table table-condensed table-bordered')
                .css('margin-bottom', '10px');

            var $titleCell = $('<th>')
                .text('Note #' + commentNumber);

            var $head = $('<thead>').append(
                $('<tr>')
                    .addClass('active')
                    .append(
                        $titleCell,
                        $('<th>')
                            .css('width', '90px')
                            .text('Action'),
                        $('<th>')
                            .css('width', '220px')
                            .text('Date / time')
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
                        .text('No active lifecycle notes')
                );
            return;
        }

        $container
            .removeClass('text-danger')
            .empty()
            .append(
                $('<div>')
                    .addClass('text-muted')
                    .text('Loading notes...')
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
                        .text('Unable to load notes');
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
                    .text('Unable to load notes');
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
                    .text('No lifecycle history recorded')
            ).appendTo($tbody);
            return;
        }

        rows.forEach(function(row) {
            var $actions = $('<span>');

            if (returnPending && row.status === 'archived') {
                $('<button>')
                    .attr({
                        type: 'button',
                        title: 'Relink returning device to this lifecycle'
                    })
                    .addClass('btn btn-xs btn-warning')
                    .html('<i class="fa fa-link"></i> Relink')
                    .on('click', function() {
                        if (
                            !confirm(
                                'Relink ' +
                                mac +
                                ' to lifecycle #' +
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
                    .text('View (' + commentCount + ')')
                    .appendTo($commentsCell);
            } else {
                $('<span>')
                    .addClass('text-muted')
                    .text('0')
                    .appendTo($commentsCell);
            }

            $('<tr>').append(
                $('<td>').text(dash(row.id)),
                $('<td>').append($status),
                $('<td>').text(dash(row.custom_hostname)),
                $('<td>').text(dash(row.hostname)),
                $('<td>').text(dash(row.ip)),
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

            $detailCell.text('Loading notes...');

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
                            .text('Unable to load notes');
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
                        .text('Unable to load notes');
                }
            });
        });

    $('#btn-add-note').on('click', function() {
        var $button = $(this);
        var value = $('#new-note-text').val().trim();

        if (!activeLifecycleId) {
            showError('No active lifecycle');
            return;
        }

        if (!value) {
            showError('Enter a note first');
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
                    showToast('Note added', 'success');
                    loadDeviceData();
                    return;
                }

                showError('Unable to add note');
            },
            error: function() {
                $button.prop('disabled', false);
                showError('Unable to add note');
            }
        });
    });

    $('#btn-start-new-lifecycle').on('click', function() {
        if (
            !confirm(
                'Start a new lifecycle for returning device ' +
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

    function validMac(value) {
        return /^(?:[0-9a-f]{2}:){5}[0-9a-f]{2}$/.test(
            (value || '').trim().toLowerCase()
        );
    }

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
                    .text('Loading physical-device grouping...')
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
                            : 'Unable to load physical-device grouping'
                    );
                    return;
                }

                renderPhysicalDevice(result.physical_device || null);
            },
            error: function() {
                physicalDeviceError(
                    'Unable to load physical-device grouping'
                );
            }
        });
    }

    function createPhysicalDevice(name, button) {
        name = (name || '').trim();

        if (!name) {
            showError('Enter a physical-device name');
            return;
        }

        if (
            !confirm(
                'Create physical device "' +
                name +
                '" for ' +
                mac +
                '?'
            )
        ) {
            return;
        }

        button.prop('disabled', true);

        $.ajax({
            url: '/api/devicemonitor/devices/createphysicaldevice',
            type: 'POST',
            data: {
                name: name,
                mac: mac
            },
            success: function(result) {
                if (result && result.result === 'saved') {
                    showToast('Physical device created', 'success');
                    loadPhysicalDevice();
                    return;
                }

                button.prop('disabled', false);
                showError(
                    result && result.error
                        ? result.error
                        : 'Unable to create physical device'
                );
            },
            error: function(xhr) {
                button.prop('disabled', false);
                showError(
                    xhr.responseJSON && xhr.responseJSON.error
                        ? xhr.responseJSON.error
                        : 'Unable to create physical device'
                );
            }
        });
    }

    function linkPhysicalDeviceIdentity(
        physicalDeviceId,
        physicalDeviceName,
        relatedMac,
        button
    ) {
        relatedMac = (relatedMac || '').trim().toLowerCase();

        if (!validMac(relatedMac)) {
            showError('Enter a valid MAC address');
            return;
        }

        if (relatedMac === mac) {
            showError('That MAC address is already this device');
            return;
        }

        if (
            !confirm(
                'Link ' +
                relatedMac +
                ' to physical device "' +
                physicalDeviceName +
                '"?'
            )
        ) {
            return;
        }

        button.prop('disabled', true);

        $.ajax({
            url: '/api/devicemonitor/devices/linkphysicaldeviceidentity',
            type: 'POST',
            data: {
                physical_device_id: physicalDeviceId,
                mac: relatedMac
            },
            success: function(result) {
                if (result && result.result === 'saved') {
                    showToast('Related identity linked', 'success');
                    loadPhysicalDevice();
                    return;
                }

                button.prop('disabled', false);
                showError(
                    result && result.error
                        ? result.error
                        : 'Unable to link related identity'
                );
            },
            error: function(xhr) {
                button.prop('disabled', false);
                showError(
                    xhr.responseJSON && xhr.responseJSON.error
                        ? xhr.responseJSON.error
                        : 'Unable to link related identity'
                );
            }
        });
    }

    function removePhysicalDeviceIdentity(
        physicalDeviceId,
        physicalDeviceName,
        relatedMac,
        button
    ) {
        if (
            !confirm(
                'Remove ' +
                relatedMac +
                ' from physical device "' +
                physicalDeviceName +
                '"? Identity history will be preserved.'
            )
        ) {
            return;
        }

        button.prop('disabled', true);

        $.ajax({
            url: '/api/devicemonitor/devices/removephysicaldeviceidentity',
            type: 'POST',
            data: {
                physical_device_id: physicalDeviceId,
                mac: relatedMac
            },
            success: function(result) {
                if (result && result.result === 'removed') {
                    showToast('Related identity removed', 'success');
                    loadPhysicalDevice();
                    return;
                }

                button.prop('disabled', false);
                showError(
                    result && result.error
                        ? result.error
                        : 'Unable to remove related identity'
                );
            },
            error: function(xhr) {
                button.prop('disabled', false);
                showError(
                    xhr.responseJSON && xhr.responseJSON.error
                        ? xhr.responseJSON.error
                        : 'Unable to remove related identity'
                );
            }
        });
    }

    function renderPhysicalDevice(physicalDevice) {
        var $container = $('#physical-device-content')
            .removeClass('text-danger')
            .empty();

        if (!physicalDevice) {
            $('<p>')
                .addClass('text-muted')
                .text(
                    'This MAC address is not linked to a user-confirmed ' +
                    'physical device.'
                )
                .appendTo($container);

            var $createForm = $('<div>')
                .addClass('form-inline');

            var $name = $('<input>')
                .attr({
                    id: 'physical-device-name',
                    type: 'text',
                    placeholder: 'Physical-device name'
                })
                .addClass('form-control input-sm')
                .css({
                    width: '280px',
                    'margin-right': '6px'
                });

            var $createButton = $('<button>')
                .attr({
                    id: 'btn-create-physical-device',
                    type: 'button'
                })
                .addClass('btn btn-sm btn-primary')
                .html(
                    '<i class="fa fa-plus-circle"></i> Create Physical Device'
                )
                .on('click', function() {
                    createPhysicalDevice($name.val(), $(this));
                });

            $createForm
                .append($name, $createButton)
                .appendTo($container);

            $('<div>')
                .addClass('text-muted')
                .css('margin-top', '8px')
                .text(
                    'Grouping is explicit and does not merge or rewrite ' +
                    'device, lifecycle or identity history.'
                )
                .appendTo($container);

            return;
        }

        var physicalDeviceId =
            parseInt(physicalDevice.id, 10) || 0;
        var physicalDeviceName =
            physicalDevice.name || ('Physical device #' + physicalDeviceId);
        var members = Array.isArray(physicalDevice.members)
            ? physicalDevice.members
            : [];

        var $summary = $('<table>')
            .addClass('table table-condensed')
            .css('margin-bottom', '12px');

        $('<tbody>')
            .append(
                $('<tr>').append(
                    $('<th>')
                        .css('width', '160px')
                        .text('Physical Device'),
                    $('<td>').text(physicalDeviceName)
                ),
                $('<tr>').append(
                    $('<th>').text('Group ID'),
                    $('<td>').text(physicalDeviceId || '\u2014')
                )
            )
            .appendTo($summary);

        $summary.appendTo($container);

        var $table = $('<table>')
            .addClass('table table-condensed table-hover table-striped')
            .attr('id', 'grid-related-identities')
            .css('margin-bottom', '12px');

        $('<thead>')
            .append(
                $('<tr>').append(
                    $('<th>').text('MAC Address'),
                    $('<th>').text('Relationship'),
                    $('<th>')
                        .addClass('text-center')
                        .css('width', '180px')
                        .text('Actions')
                )
            )
            .appendTo($table);

        var $tbody = $('<tbody>').appendTo($table);

        if (!members.length) {
            $('<tr>')
                .append(
                    $('<td>')
                        .attr('colspan', 3)
                        .addClass('text-muted')
                        .text('No active identities')
                )
                .appendTo($tbody);
        }

        members.forEach(function(member) {
            var memberMac = (member.mac || '').trim().toLowerCase();
            var isCurrent = memberMac === mac;
            var $actions = $('<div>').addClass('btn-group btn-group-xs');

            if (isCurrent) {
                $('<span>')
                    .addClass('label label-success')
                    .text('Current')
                    .appendTo($actions);
            } else {
                $('<a>')
                    .attr({
                        href:
                            '/ui/devicemonitor/index/devicehistory?mac=' +
                            encodeURIComponent(memberMac),
                        title: 'Open Device Details'
                    })
                    .addClass('btn btn-default')
                    .html('<i class="fa fa-external-link"></i> View')
                    .appendTo($actions);
            }

            $('<button>')
                .attr({
                    type: 'button',
                    title: 'Remove this identity from the physical device'
                })
                .addClass('btn btn-danger')
                .html('<i class="fa fa-unlink"></i> Remove')
                .on('click', function() {
                    removePhysicalDeviceIdentity(
                        physicalDeviceId,
                        physicalDeviceName,
                        memberMac,
                        $(this)
                    );
                })
                .appendTo($actions);

            $('<tr>')
                .append(
                    $('<td>').text(memberMac || '\u2014'),
                    $('<td>').text(
                        isCurrent ? 'Current identity' : 'Related identity'
                    ),
                    $('<td>')
                        .addClass('text-center')
                        .append($actions)
                )
                .appendTo($tbody);
        });

        $table.appendTo($container);

        var $linkForm = $('<div>')
            .addClass('form-inline');

        var $macInput = $('<input>')
            .attr({
                id: 'related-identity-mac',
                type: 'text',
                maxlength: 17,
                placeholder: 'aa:bb:cc:dd:ee:ff'
            })
            .addClass('form-control input-sm')
            .css({
                width: '190px',
                'margin-right': '6px'
            });

        var $linkButton = $('<button>')
            .attr({
                id: 'btn-link-physical-identity',
                type: 'button'
            })
            .addClass('btn btn-sm btn-primary')
            .html('<i class="fa fa-link"></i> Link Identity')
            .on('click', function() {
                linkPhysicalDeviceIdentity(
                    physicalDeviceId,
                    physicalDeviceName,
                    $macInput.val(),
                    $(this)
                );
            });

        $linkForm
            .append($macInput, $linkButton)
            .appendTo($container);

        $('<div>')
            .addClass('text-muted')
            .css('margin-top', '8px')
            .text(
                'Removing a relationship preserves its membership history.'
            )
            .appendTo($container);
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
