<div class="content-box">
    <div class="content-box-main">

        <!-- Device navigation tabs -->
        <ul class="nav nav-tabs" role="tablist" style="margin:10px 0 0 0;">
            <li role="presentation">
                <a href="/ui/devicemonitor/index/devices">
                    <i class="fa fa-list"></i> {{ lang._('Network Identities') }}
                </a>
            </li>
            <li role="presentation" class="active dm-tab-with-info">
                <a href="/ui/devicemonitor/index/physicaldevices">
                    <i class="fa fa-sitemap"></i> {{ lang._('Device Profiles') }}
                </a>
                <button type="button" class="dm-info" aria-label="{{ lang._('About Device Profiles') }}"
                        data-content="{{ lang._('Real-world devices linked to one or more network identities, such as wired and Wi-Fi adapters.') }}">
                    <i class="fa fa-info-circle" aria-hidden="true"></i>
                </button>
            </li>
        </ul>

        <div id="physical-devices-sticky-controls">
            <div class="physical-devices-header">
                <div class="physical-devices-stats">
                    <span>
                        {{ lang._('Profiles') }}:
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
                    {{ lang._('Create Profile') }}
                </button>

                <select id="filter-state"
                        class="selectpicker"
                        data-style="btn-default btn-sm"
                        data-width="170px">
                    <option value="all">{{ lang._('All Profiles') }}</option>
                    <option value="current">{{ lang._('Current Profiles') }}</option>
                    <option value="archived">{{ lang._('Archived Profiles') }}</option>
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
                    {{ lang._('Create Profile') }}
                </strong>
                <button type="button" class="dm-info" aria-label="{{ lang._('About Creating Profiles') }}"
                        data-content="{{ lang._('Start with one MAC address for this profile. It must belong to a currently online network identity. Adding identities is explicit and never merges or rewrites device, lifecycle or identity history.') }}">
                    <i class="fa fa-info-circle" aria-hidden="true"></i>
                </button>
            </div>
            <div class="panel-body">
                <div class="form-inline">
                    <input id="create-name"
                           type="text"
                           class="form-control input-sm"
                           placeholder="{{ lang._('Profile name') }}"
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
.dm-info { border:0; background:transparent; color:#337ab7; padding:0 3px; cursor:pointer; }
.dm-tab-with-info { position:relative; }
.dm-tab-with-info > a { padding-right:30px !important; }
.dm-tab-with-info > .dm-info {
    position:absolute; right:8px; top:50%; transform:translateY(-50%);
    z-index:2; line-height:1;
}
</style>

<script>
$(document).ready(function() {
    $('.dm-info').popover({container:'body', placement:'auto bottom', trigger:'focus'});
    $('.dm-info').on('keydown', function(event) {
        if (event.key === 'Escape') { $(this).popover('hide').trigger('blur'); }
    });
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
                    .text({{ lang.query('Loading devices...')|json_encode(15) }})
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
                    .text({{ lang.query('No devices found.')|json_encode(15) }})
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
            .text(({{ lang.query('Last Seen')|json_encode(15) }} + ": ") + dash(device.last_seen))
            .appendTo($heading);

        if (isArchived) {
            $('<span>')
                .addClass('label label-default')
                .css('margin-left', '8px')
                .text({{ lang.query('Archived')|json_encode(15) }})
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
        var $section = $('<div>');

        $('<div>')
            .addClass('member-section-title text-muted')
            .text({{ lang.query('Profile Summary')|json_encode(15) }})
            .appendTo($section);

        var $table = $('<table>')
            .addClass('table table-condensed')
            .css('margin-bottom', '8px');

        var $tbody = $('<tbody>');

        $tbody.append(
            $('<tr>').append(
                $('<th>').css('width', '170px').text({{ lang.query('Profile Name')|json_encode(15) }}),
                $('<td>').text(device.name || '\u2014')
            ),
            $('<tr>').append(
                $('<th>').text({{ lang.query('Status')|json_encode(15) }}),
                $('<td>').text(statusLabel(device.status))
            ),
            $('<tr>').append(
                $('<th>').text({{ lang.query('Current Identities')|json_encode(15) }}),
                $('<td>').text(device.current_identity_count || 0)
            ),
            $('<tr>').append(
                $('<th>').text({{ lang.query('Previous Identities')|json_encode(15) }}),
                $('<td>').text(device.previous_identity_count || 0)
            ),
            $('<tr>').append(
                $('<th>').text({{ lang.query('Created')|json_encode(15) }}),
                $('<td>').text(dash(device.created_at))
            )
        );

        if (isArchived) {
            $tbody.append(
                $('<tr>').append(
                    $('<th>').text({{ lang.query('Archived')|json_encode(15) }}),
                    $('<td>').text(dash(device.archived_at))
                )
            );
        }

        $table.append($tbody);
        $section.append($table);
        return $section;
    }

    function buildCurrentIdentitiesSection(device, current, isArchived) {
        var $section = $('<div>');

        $('<div>')
            .addClass('member-section-title text-muted')
            .text({{ lang.query('Current Identities')|json_encode(15) }})
            .appendTo($section);

        var $table = $('<table>')
            .addClass('table table-condensed table-striped')
            .css('margin-bottom', '8px');

        $('<thead>')
            .append(
                $('<tr>').append(
                    $('<th>').text({{ lang.query('IP Address')|json_encode(15) }}),
                    $('<th>').text({{ lang.query('Friendly Name')|json_encode(15) }}),
                    $('<th>').text({{ lang.query('Hostname')|json_encode(15) }}),
                    $('<th>').text({{ lang.query('MAC Address')|json_encode(15) }}),
                    $('<th>').text({{ lang.query('Status')|json_encode(15) }}),
                    $('<th>').text({{ lang.query('Last Seen')|json_encode(15) }}),
                    $('<th>')
                        .addClass('text-center')
                        .css('width', '180px')
                        .text({{ lang.query('Actions')|json_encode(15) }})
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
                        .text({{ lang.query('No current identities')|json_encode(15) }})
                )
                .appendTo($tbody);
        }

        current.forEach(function(member) {
            var $actions = $('<div>').addClass('btn-group');

            $('<a>')
                .attr({
                    href: '/ui/devicemonitor/index/devicehistory?mac=' +
                        encodeURIComponent(member.mac || ''),
                    title: {{ lang.query('Open Network Identity Details')|json_encode(15) }}
                })
                .addClass('btn btn-xs btn-default')
                .html(("<i class='fa fa-external-link'></i> " + {{ lang.query('View Network Identity Details')|json_encode(15) }}))
                .appendTo($actions);

            if (!isArchived) {
                $('<button>')
                    .attr({
                        type: 'button',
                        title: {{ lang.query('Unlink this identity from the profile')|json_encode(15) }}
                    })
                    .addClass('btn btn-xs btn-danger')
                    .html(('<i class="fa fa-unlink"></i> ' + {{ lang.query('Unlink Identity')|json_encode(15) }}))
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
            .text({{ lang.query('Previous Identities')|json_encode(15) }})
            .appendTo($section);

        var $table = $('<table>')
            .addClass('table table-condensed table-striped')
            .css('margin-bottom', '8px');

        $('<thead>')
            .append(
                $('<tr>').append(
                    $('<th>').text({{ lang.query('MAC Address')|json_encode(15) }}),
                    $('<th>').text({{ lang.query('Friendly Name')|json_encode(15) }}),
                    $('<th>').text({{ lang.query('IP Address')|json_encode(15) }}),
                    $('<th>').text({{ lang.query('Hostname')|json_encode(15) }}),
                    $('<th>').text({{ lang.query('Linked')|json_encode(15) }}),
                    $('<th>').text({{ lang.query('Removed')|json_encode(15) }}),
                    $('<th>')
                        .addClass('text-center')
                        .css('width', '80px')
                        .text({{ lang.query('Actions')|json_encode(15) }})
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
                    title: {{ lang.query('Open Network Identity Details')|json_encode(15) }}
                })
                .addClass('btn btn-xs btn-default')
                .html(("<i class='fa fa-external-link'></i> " + {{ lang.query('View Network Identity Details')|json_encode(15) }}))
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
            .html(('<i class="fa fa-plus"></i> ' + {{ lang.query('Add Identity')|json_encode(15) }}))
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
            showError({{ lang.query('Enter a profile name')|json_encode(15) }});
            return;
        }

        if (!validMac(mac)) {
            showError({{ lang.query('Enter a valid MAC address')|json_encode(15) }});
            return;
        }

        if (
            !confirm(
                ({{ lang.query('Create profile')|json_encode(15) }} + " ") + '"' + name + '"' + (" " + {{ lang.query('with MAC address')|json_encode(15) }} + " ") + mac + '?'
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
                    showToast({{ lang.query('Profile created')|json_encode(15) }}, 'success');
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
                        : 'Unable to create profile'
                );
            },
            error: function(xhr) {
                button.prop('disabled', false);
                showError(
                    xhr.responseJSON && xhr.responseJSON.error
                        ? xhr.responseJSON.error
                        : 'Unable to create profile'
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
            showError({{ lang.query('Enter a valid MAC address')|json_encode(15) }});
            return;
        }

        if (
            !confirm(
                ({{ lang.query('Add')|json_encode(15) }} + " ") +
                relatedMac +
                (" " + {{ lang.query('to profile')|json_encode(15) }} + " ") + '"' +
                deviceName +
                '"?\n\n' +
                ({{ lang.query('Only continue if this MAC belongs to the same device profile.')|json_encode(15) }} + " ") +
                ({{ lang.query('Do not add separate devices merely because')|json_encode(15) }} + " ") +
                {{ lang.query('they are the same type, model or vendor.')|json_encode(15) }}
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
                    showToast({{ lang.query('Identity added')|json_encode(15) }}, 'success');
                    loadPhysicalDevices();
                    return;
                }

                button.prop('disabled', false);
                showError(
                    result && result.error
                        ? result.error
                        : {{ lang.query('Unable to add identity')|json_encode(15) }}
                );
            },
            error: function(xhr) {
                button.prop('disabled', false);
                showError(
                    xhr.responseJSON && xhr.responseJSON.error
                        ? xhr.responseJSON.error
                        : {{ lang.query('Unable to add identity')|json_encode(15) }}
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
                ({{ lang.query('Unlink')|json_encode(15) }} + " ") +
                relatedMac +
                (" " + {{ lang.query('from profile')|json_encode(15) }} + " ") + '"' +
                deviceName +
                '"? ' + {{ lang.query('Identity history will be preserved.')|json_encode(15) }}
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
                    showToast({{ lang.query('Identity unlinked')|json_encode(15) }}, 'success');
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
