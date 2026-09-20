<div class="content-box">
    <div class="content-box-main">

        <div id="physical-devices-sticky-controls">
            <div class="physical-devices-header">
                <div class="physical-devices-stats">
                    <span>
                        {{ lang._('Devices') }}:
                        <strong id="stat-devices">&mdash;</strong>
                    </span>
                    <span>
                        {{ lang._('Current') }}:
                        <strong id="stat-current">&mdash;</strong>
                    </span>
                    <span>
                        {{ lang._('Archived') }}:
                        <strong id="stat-archived">&mdash;</strong>
                    </span>
                </div>
            </div>

            <div class="physical-devices-toolbar">
                <button id="btn-refresh"
                        type="button"
                        class="btn btn-default btn-sm"
                        title="{{ lang._('Refresh') }}">
                    <i class="fa fa-refresh"></i>
                </button>

                <button id="btn-create-toggle"
                        type="button"
                        class="btn btn-primary btn-sm">
                    <i class="fa fa-plus"></i>
                    {{ lang._('Create Device') }}
                </button>

                <select id="filter-state"
                        class="selectpicker"
                        data-style="btn-default btn-sm"
                        data-width="170px">
                    <option value="all">{{ lang._('All Devices') }}</option>
                    <option value="current">{{ lang._('Current Devices') }}</option>
                    <option value="archived">{{ lang._('Archived Devices') }}</option>
                </select>

                <input id="physical-devices-search"
                       type="text"
                       class="form-control input-sm"
                       placeholder="{{ lang._('Search by name or MAC') }}" />

                <span class="text-muted">
                    {{ lang._('Showing') }}
                    <strong id="stat-visible">0</strong>
                </span>
            </div>
        </div>

        <div id="create-form" class="panel panel-default" style="display:none;">
            <div class="panel-heading">
                <strong>
                    <i class="fa fa-plus-circle"></i>
                    {{ lang._('Create Device') }}
                </strong>
            </div>
            <div class="panel-body">
                <div class="form-inline">
                    <input id="create-name"
                           type="text"
                           class="form-control input-sm"
                           placeholder="{{ lang._('Device name') }}"
                           style="margin-right:6px;" />
                    <input id="create-mac"
                           type="text"
                           maxlength="17"
                           class="form-control input-sm"
                           placeholder="aa:bb:cc:dd:ee:ff"
                           style="margin-right:6px;" />
                    <button id="btn-create-submit"
                            type="button"
                            class="btn btn-xs btn-primary">
                        <i class="fa fa-plus"></i>
                        {{ lang._('Create') }}
                    </button>
                </div>
                <div class="text-muted" style="margin-top:8px;">
                    {{ lang._('Start with one MAC address from this device. It must belong to a currently online device. Adding identities is explicit and never merges or rewrites device, lifecycle or identity history.') }}
                </div>
            </div>
        </div>

        <div id="physical-devices-list">
            <div class="text-muted">{{ lang._('Loading devices...') }}</div>
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

.physical-devices-header {
    padding: 10px 10px 8px 10px;
    border-bottom: 1px solid #444;
    margin-bottom: 0;
}

.physical-devices-stats {
    display: flex;
    gap: 20px;
    align-items: center;
    font-size: 13px;
    color: #888;
}

.physical-devices-stats strong {
    font-size: 16px;
    margin-left: 4px;
    color: #ccc;
}

.physical-devices-toolbar {
    padding: 12px 4px 12px 4px;
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
}

.physical-device-panel {
    margin-top: 12px;
}

.physical-device-panel .panel-heading {
    cursor: pointer;
}

.member-section-title {
    font-weight: 600;
    margin: 12px 0 4px 0;
}
</style>

<script>
$(document).ready(function() {
    var allDevices = [];
    var stateFilter = 'all';
    var searchText = '';
    var params = new URLSearchParams(window.location.search);
    var deviceParam = params.get('group') || '';
    var revealedDevice = false;

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

    function validMac(value) {
        return /^(?:[0-9a-f]{2}:){5}[0-9a-f]{2}$/.test(
            (value || '').trim().toLowerCase()
        );
    }

    function dash(value) {
        return value === null || value === undefined || value === ''
            ? '\u2014'
            : value;
    }

    function statusLabel(status) {
        return status === 'online' ? 'Online' : 'Offline';
    }

    function identityStatusLabel(isActive) {
        if (isActive === 1) {
            return 'Online';
        }
        if (isActive === 0) {
            return 'Offline';
        }
        return '\u2014';
    }

    function loadPhysicalDevices() {
        $('#physical-devices-list')
            .removeClass('text-danger')
            .empty()
            .append(
                $('<div>')
                    .addClass('text-muted')
                    .text('Loading devices...')
            );

        $.ajax({
            url: '/api/devicemonitor/devices/physicaldevices',
            type: 'GET',
            success: function(result) {
                if (!result || result.result !== 'ok') {
                    physicalDevicesError(
                        result && result.error
                            ? result.error
                            : 'Unable to load devices'
                    );
                    return;
                }

                allDevices = Array.isArray(result.physical_devices)
                    ? result.physical_devices
                    : [];

                updateStats();
                renderPhysicalDevices();
                revealDevice();
            },
            error: function() {
                physicalDevicesError('Unable to load devices');
            }
        });
    }

    function physicalDevicesError(message) {
        $('#physical-devices-list')
            .empty()
            .addClass('text-danger')
            .text(message);
    }

    function updateStats() {
        var current = 0;
        var archived = 0;

        allDevices.forEach(function(device) {
            if (device.archived_at) {
                archived++;
            } else {
                current++;
            }
        });

        $('#stat-devices').text(allDevices.length);
        $('#stat-current').text(current);
        $('#stat-archived').text(archived);
    }

    function deviceMacs(device) {
        var macs = [];

        (Array.isArray(device.members) ? device.members : []).forEach(
            function(member) {
                if (member && member.mac) {
                    macs.push(member.mac);
                }
            }
        );

        return macs.join(' ');
    }

    function deviceMatches(device) {
        if (stateFilter === 'current' && device.archived_at) {
            return false;
        }

        if (stateFilter === 'archived' && !device.archived_at) {
            return false;
        }

        if (searchText) {
            var hay = (
                (device.name || '') +
                ' ' +
                deviceMacs(device)
            ).toLowerCase();

            if (hay.indexOf(searchText) === -1) {
                return false;
            }
        }

        return true;
    }

    function renderPhysicalDevices() {
        var $list = $('#physical-devices-list').empty();
        var visible = 0;

        allDevices.forEach(function(device) {
            if (!deviceMatches(device)) {
                return;
            }

            visible++;
            $list.append(buildDevicePanel(device));
        });

        if (!visible) {
            $list.append(
                $('<div>')
                    .addClass('text-muted')
                    .text('No devices found.')
            );
        }

        $('#stat-visible').text(visible);
    }

    function revealDevice() {
        if (!deviceParam || revealedDevice) {
            return;
        }

        revealedDevice = true;

        var $target = $(
            '.physical-device-panel[data-device-id="' + deviceParam + '"]'
        );

        if (!$target.length) {
            return;
        }

        $target.find('.panel-body').show();
        $target.find('i.fa-chevron-right')
            .toggleClass('fa-chevron-right fa-chevron-down');
        $('html, body').animate({
            scrollTop: $target.offset().top - 20
        }, 300);
    }

    function buildDevicePanel(device) {
        var isArchived = !!device.archived_at;
        var members = Array.isArray(device.members) ? device.members : [];
        var current = members.filter(function(member) {
            return !member.removed_at;
        });
        var previous = members.filter(function(member) {
            return !!member.removed_at;
        });

        var $panel = $('<div>')
            .addClass('panel panel-default physical-device-panel')
            .attr('data-device-id', device.id);
        var $heading = $('<div>').addClass('panel-heading');
        var $body = $('<div>').addClass('panel-body').css('display', 'none');

        $heading.append(
            $('<i>').addClass('fa fa-server'),
            $('<span>').css('margin-left', '4px').text(device.name || '')
        );

        $('<span>')
            .addClass('label label-info')
            .css('margin-left', '8px')
            .text((device.current_identity_count || 0) + ' current')
            .appendTo($heading);

        var statusClass = device.status === 'online'
            ? 'label-success'
            : 'label-default';

        $('<span>')
            .addClass('label ' + statusClass)
            .css('margin-left', '8px')
            .text(statusLabel(device.status))
            .appendTo($heading);

        $('<span>')
            .addClass('text-muted')
            .css({'margin-left': '8px', 'font-size': '12px'})
            .text('Last Seen: ' + dash(device.last_seen))
            .appendTo($heading);

        if (isArchived) {
            $('<span>')
                .addClass('label label-default')
                .css('margin-left', '8px')
                .text('Archived')
                .appendTo($heading);
        }

        $('<i>')
            .addClass('fa fa-chevron-right pull-right')
            .css('margin-top', '4px')
            .appendTo($heading);

        $heading.on('click', function() {
            $body.toggle();
            $heading
                .find('i.fa-chevron-down, i.fa-chevron-right')
                .toggleClass('fa-chevron-down fa-chevron-right');
        });

        $body.append(buildDeviceSummary(device, isArchived));
        $body.append(buildCurrentIdentitiesSection(device, current, isArchived));

        if (previous.length) {
            $body.append(buildPreviousIdentitiesSection(previous));
        }

        if (!isArchived) {
            $body.append(buildAddIdentityForm(device));
        }

        $panel.append($heading, $body);
        return $panel;
    }

    function buildDeviceSummary(device, isArchived) {
        var $table = $('<table>')
            .addClass('table table-condensed')
            .css('margin-bottom', '8px');

        var $tbody = $('<tbody>');

        $tbody.append(
            $('<tr>').append(
                $('<th>').css('width', '170px').text('Device Name'),
                $('<td>').text(device.name || '\u2014')
            ),
            $('<tr>').append(
                $('<th>').text('Status'),
                $('<td>').text(statusLabel(device.status))
            ),
            $('<tr>').append(
                $('<th>').text('Current Identities'),
                $('<td>').text(device.current_identity_count || 0)
            ),
            $('<tr>').append(
                $('<th>').text('Previous Identities'),
                $('<td>').text(device.previous_identity_count || 0)
            ),
            $('<tr>').append(
                $('<th>').text('Created'),
                $('<td>').text(dash(device.created_at))
            )
        );

        if (isArchived) {
            $tbody.append(
                $('<tr>').append(
                    $('<th>').text('Archived'),
                    $('<td>').text(dash(device.archived_at))
                )
            );
        }

        $table.append($tbody);
        return $table;
    }

    function buildCurrentIdentitiesSection(device, current, isArchived) {
        var $section = $('<div>');

        $('<div>')
            .addClass('member-section-title text-muted')
            .text('Current Identities')
            .appendTo($section);

        var $table = $('<table>')
            .addClass('table table-condensed table-striped')
            .css('margin-bottom', '8px');

        $('<thead>')
            .append(
                $('<tr>').append(
                    $('<th>').text('IP Address'),
                    $('<th>').text('Friendly Name'),
                    $('<th>').text('Hostname'),
                    $('<th>').text('MAC Address'),
                    $('<th>').text('Status'),
                    $('<th>').text('Last Seen'),
                    $('<th>')
                        .addClass('text-center')
                        .css('width', '180px')
                        .text('Actions')
                )
            )
            .appendTo($table);

        var $tbody = $('<tbody>').appendTo($table);

        if (!current.length) {
            $('<tr>')
                .append(
                    $('<td>')
                        .attr('colspan', 7)
                        .addClass('text-muted')
                        .text('No current identities')
                )
                .appendTo($tbody);
        }

        current.forEach(function(member) {
            var $actions = $('<div>').addClass('btn-group');

            $('<a>')
                .attr({
                    href: '/ui/devicemonitor/index/devicehistory?mac=' +
                        encodeURIComponent(member.mac || ''),
                    title: 'Open Device Details'
                })
                .addClass('btn btn-xs btn-default')
                .html('<i class="fa fa-external-link"></i> View Device Details')
                .appendTo($actions);

            if (!isArchived) {
                $('<button>')
                    .attr({
                        type: 'button',
                        title: 'Unlink this identity from the device'
                    })
                    .addClass('btn btn-xs btn-danger')
                    .html('<i class="fa fa-unlink"></i> Unlink Identity')
                    .on('click', function() {
                        removePhysicalDeviceIdentity(
                            device.id,
                            device.name,
                            member.mac,
                            $(this)
                        );
                    })
                    .appendTo($actions);
            }

            $('<tr>')
                .append(
                    $('<td>').text(dash(member.ip)),
                    $('<td>').text(dash(member.friendly_name)),
                    $('<td>').text(dash(member.hostname)),
                    $('<td>').text(member.mac || '\u2014'),
                    $('<td>').text(identityStatusLabel(member.is_active)),
                    $('<td>').text(dash(member.last_seen)),
                    $('<td>').addClass('text-center').append($actions)
                )
                .appendTo($tbody);
        });

        $table.appendTo($section);
        return $section;
    }

    function buildPreviousIdentitiesSection(previous) {
        var $section = $('<div>');

        $('<div>')
            .addClass('member-section-title text-muted')
            .text('Previous Identities')
            .appendTo($section);

        var $table = $('<table>')
            .addClass('table table-condensed table-striped')
            .css('margin-bottom', '8px');

        $('<thead>')
            .append(
                $('<tr>').append(
                    $('<th>').text('MAC Address'),
                    $('<th>').text('Friendly Name'),
                    $('<th>').text('IP Address'),
                    $('<th>').text('Hostname'),
                    $('<th>').text('Linked'),
                    $('<th>').text('Removed'),
                    $('<th>')
                        .addClass('text-center')
                        .css('width', '80px')
                        .text('Actions')
                )
            )
            .appendTo($table);

        var $tbody = $('<tbody>').appendTo($table);

        previous.forEach(function(member) {
            var $actions = $('<div>').addClass('btn-group');

            $('<a>')
                .attr({
                    href: '/ui/devicemonitor/index/devicehistory?mac=' +
                        encodeURIComponent(member.mac || ''),
                    title: 'Open Device Details'
                })
                .addClass('btn btn-xs btn-default')
                .html('<i class="fa fa-external-link"></i> View Device Details')
                .appendTo($actions);

            $('<tr>')
                .append(
                    $('<td>').text(member.mac || '\u2014'),
                    $('<td>').text(dash(member.friendly_name)),
                    $('<td>').text(dash(member.ip)),
                    $('<td>').text(dash(member.hostname)),
                    $('<td>').text(dash(member.added_at)),
                    $('<td>').text(dash(member.removed_at)),
                    $('<td>').addClass('text-center').append($actions)
                )
                .appendTo($tbody);
        });

        $table.appendTo($section);
        return $section;
    }

    function buildAddIdentityForm(device) {
        var $form = $('<div>')
            .addClass('form-inline')
            .css('margin-top', '4px');

        var $macInput = $('<input>')
            .attr({
                type: 'text',
                maxlength: 17,
                placeholder: 'aa:bb:cc:dd:ee:ff'
            })
            .addClass('form-control input-sm')
            .css({
                width: '190px',
                'margin-right': '6px'
            });

        var $addButton = $('<button>')
            .attr('type', 'button')
            .addClass('btn btn-xs btn-primary')
            .html('<i class="fa fa-plus"></i> Add Identity')
            .on('click', function() {
                addPhysicalDeviceIdentity(
                    device.id,
                    device.name,
                    $macInput.val(),
                    $(this)
                );
            });

        $form.append($macInput, $addButton);
        return $form;
    }

    function createPhysicalDevice(name, mac, button) {
        name = (name || '').trim();
        mac = (mac || '').trim().toLowerCase();

        if (!name) {
            showError('Enter a device name');
            return;
        }

        if (!validMac(mac)) {
            showError('Enter a valid MAC address');
            return;
        }

        if (
            !confirm(
                'Create device "' + name + '" with MAC address ' + mac + '?'
            )
        ) {
            return;
        }

        button.prop('disabled', true);

        $.ajax({
            url: '/api/devicemonitor/devices/createphysicaldevice',
            type: 'POST',
            data: {name: name, mac: mac},
            success: function(result) {
                if (result && result.result === 'saved') {
                    showToast('Device created', 'success');
                    $('#create-form').hide();
                    $('#create-name').val('');
                    $('#create-mac').val('');
                    loadPhysicalDevices();
                    return;
                }

                button.prop('disabled', false);
                showError(
                    result && result.error
                        ? result.error
                        : 'Unable to create device'
                );
            },
            error: function(xhr) {
                button.prop('disabled', false);
                showError(
                    xhr.responseJSON && xhr.responseJSON.error
                        ? xhr.responseJSON.error
                        : 'Unable to create device'
                );
            }
        });
    }

    function addPhysicalDeviceIdentity(
        deviceId,
        deviceName,
        relatedMac,
        button
    ) {
        relatedMac = (relatedMac || '').trim().toLowerCase();

        if (!validMac(relatedMac)) {
            showError('Enter a valid MAC address');
            return;
        }

        if (
            !confirm(
                'Add ' +
                relatedMac +
                ' to device "' +
                deviceName +
                '"?\n\n' +
                'Only continue if this MAC belongs to the same physical ' +
                'hardware. Do not add separate devices merely because ' +
                'they are the same type, model or vendor.'
            )
        ) {
            return;
        }

        button.prop('disabled', true);

        $.ajax({
            url: '/api/devicemonitor/devices/linkphysicaldeviceidentity',
            type: 'POST',
            data: {
                physical_device_id: deviceId,
                mac: relatedMac
            },
            success: function(result) {
                if (result && result.result === 'saved') {
                    showToast('Identity added', 'success');
                    loadPhysicalDevices();
                    return;
                }

                button.prop('disabled', false);
                showError(
                    result && result.error
                        ? result.error
                        : 'Unable to add identity'
                );
            },
            error: function(xhr) {
                button.prop('disabled', false);
                showError(
                    xhr.responseJSON && xhr.responseJSON.error
                        ? xhr.responseJSON.error
                        : 'Unable to add identity'
                );
            }
        });
    }

    function removePhysicalDeviceIdentity(
        deviceId,
        deviceName,
        relatedMac,
        button
    ) {
        if (
            !confirm(
                'Unlink ' +
                relatedMac +
                ' from device "' +
                deviceName +
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
                physical_device_id: deviceId,
                mac: relatedMac
            },
            success: function(result) {
                if (result && result.result === 'removed') {
                    showToast('Identity unlinked', 'success');
                    loadPhysicalDevices();
                    return;
                }

                button.prop('disabled', false);
                showError(
                    result && result.error
                        ? result.error
                        : 'Unable to unlink identity'
                );
            },
            error: function(xhr) {
                button.prop('disabled', false);
                showError(
                    xhr.responseJSON && xhr.responseJSON.error
                        ? xhr.responseJSON.error
                        : 'Unable to unlink identity'
                );
            }
        });
    }

    $('#btn-refresh').on('click', loadPhysicalDevices);

    $('#btn-create-toggle').on('click', function() {
        $('#create-form').toggle();
    });

    $('#btn-create-submit').on('click', function() {
        createPhysicalDevice(
            $('#create-name').val(),
            $('#create-mac').val(),
            $(this)
        );
    });

    $('#filter-state').on('change', function() {
        stateFilter = $(this).val();
        renderPhysicalDevices();
    });

    $('#physical-devices-search').on('input', function() {
        searchText = $(this).val().trim().toLowerCase();
        renderPhysicalDevices();
    });

    loadPhysicalDevices();
});
</script>
