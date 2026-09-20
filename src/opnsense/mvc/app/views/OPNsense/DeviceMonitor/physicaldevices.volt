<div class="content-box">
    <div class="content-box-main">

        <div id="physical-devices-sticky-controls">
            <div class="physical-devices-header">
                <div class="physical-devices-stats">
                    <span>
                        {{ lang._('Total Groups') }}:
                        <strong id="stat-groups">&mdash;</strong>
                    </span>
                    <span>
                        {{ lang._('Active Groups') }}:
                        <strong id="stat-active">&mdash;</strong>
                    </span>
                    <span>
                        {{ lang._('Archived Groups') }}:
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
                    {{ lang._('Create Physical Device') }}
                </button>

                <select id="filter-state"
                        class="selectpicker"
                        data-style="btn-default btn-sm"
                        data-width="160px">
                    <option value="all">{{ lang._('All Groups') }}</option>
                    <option value="active">{{ lang._('Active Only') }}</option>
                    <option value="archived">{{ lang._('Archived Only') }}</option>
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
                    {{ lang._('Create Physical Device') }}
                </strong>
            </div>
            <div class="panel-body">
                <div class="form-inline">
                    <input id="create-name"
                           type="text"
                           class="form-control input-sm"
                           placeholder="{{ lang._('Physical-device name') }}"
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
                    {{ lang._('The seed MAC must belong to a current, active device. Grouping is explicit and does not merge or rewrite device, lifecycle or identity history.') }}
                </div>
            </div>
        </div>

        <div id="physical-devices-list">
            <div class="text-muted">{{ lang._('Loading physical devices...') }}</div>
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
    var allGroups = [];
    var stateFilter = 'all';
    var searchText = '';

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

    function loadPhysicalDevices() {
        $('#physical-devices-list')
            .removeClass('text-danger')
            .empty()
            .append(
                $('<div>')
                    .addClass('text-muted')
                    .text('Loading physical devices...')
            );

        $.ajax({
            url: '/api/devicemonitor/devices/physicaldevices',
            type: 'GET',
            success: function(result) {
                if (!result || result.result !== 'ok') {
                    physicalDevicesError(
                        result && result.error
                            ? result.error
                            : 'Unable to load physical devices'
                    );
                    return;
                }

                allGroups = Array.isArray(result.physical_devices)
                    ? result.physical_devices
                    : [];

                updateStats();
                renderPhysicalDevices();
            },
            error: function() {
                physicalDevicesError('Unable to load physical devices');
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
        var active = 0;
        var archived = 0;

        allGroups.forEach(function(group) {
            if (group.archived_at) {
                archived++;
            } else {
                active++;
            }
        });

        $('#stat-groups').text(allGroups.length);
        $('#stat-active').text(active);
        $('#stat-archived').text(archived);
    }

    function groupMacs(group) {
        var macs = [];

        (Array.isArray(group.members) ? group.members : []).forEach(
            function(member) {
                if (member && member.mac) {
                    macs.push(member.mac);
                }
            }
        );

        return macs.join(' ');
    }

    function groupMatches(group) {
        if (stateFilter === 'active' && group.archived_at) {
            return false;
        }

        if (stateFilter === 'archived' && !group.archived_at) {
            return false;
        }

        if (searchText) {
            var hay = (
                (group.name || '') +
                ' ' +
                (group.id || '') +
                ' ' +
                groupMacs(group)
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

        allGroups.forEach(function(group) {
            if (!groupMatches(group)) {
                return;
            }

            visible++;
            $list.append(buildGroupPanel(group));
        });

        if (!visible) {
            $list.append(
                $('<div>')
                    .addClass('text-muted')
                    .text('No physical devices found.')
            );
        }

        $('#stat-visible').text(visible);
    }

    function buildGroupPanel(group) {
        var isArchived = !!group.archived_at;
        var members = Array.isArray(group.members) ? group.members : [];
        var activeMembers = members.filter(function(member) {
            return !member.removed_at;
        });
        var historicalMembers = members.filter(function(member) {
            return !!member.removed_at;
        });

        var $panel = $('<div>').addClass(
            'panel panel-default physical-device-panel'
        );
        var $heading = $('<div>').addClass('panel-heading');
        var $body = $('<div>').addClass('panel-body').css('display', 'none');

        $heading.append(
            $('<i>').addClass('fa fa-sitemap'),
            $('<span>').css('margin-left', '4px').text(group.name || '')
        );

        $('<span>')
            .addClass('label label-info')
            .css('margin-left', '8px')
            .text((group.active_member_count || 0) + ' active')
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

        $body.append(buildGroupSummary(group, isArchived));
        $body.append(buildActiveMembersTable(group, activeMembers, isArchived));

        if (historicalMembers.length) {
            $body.append(buildHistoricalMembersSection(historicalMembers));
        }

        if (!isArchived) {
            $body.append(buildLinkForm(group));
        }

        $panel.append($heading, $body);
        return $panel;
    }

    function buildGroupSummary(group, isArchived) {
        var $table = $('<table>')
            .addClass('table table-condensed')
            .css('margin-bottom', '8px');

        var $tbody = $('<tbody>');

        $tbody.append(
            $('<tr>').append(
                $('<th>').css('width', '130px').text('Group ID'),
                $('<td>').text(group.id || '\u2014')
            ),
            $('<tr>').append(
                $('<th>').text('Active identities'),
                $('<td>').text(group.active_member_count || 0)
            ),
            $('<tr>').append(
                $('<th>').text('Total identities'),
                $('<td>').text(group.total_member_count || 0)
            ),
            $('<tr>').append(
                $('<th>').text('Created'),
                $('<td>').text(dash(group.created_at))
            )
        );

        if (isArchived) {
            $tbody.append(
                $('<tr>').append(
                    $('<th>').text('Archived'),
                    $('<td>').text(dash(group.archived_at))
                )
            );
        } else {
            $tbody.append(
                $('<tr>').append(
                    $('<th>').text('Updated'),
                    $('<td>').text(dash(group.updated_at))
                )
            );
        }

        $table.append($tbody);
        return $table;
    }

    function buildActiveMembersTable(group, activeMembers, isArchived) {
        var $section = $('<div>');

        $('<div>')
            .addClass('member-section-title')
            .text('Active identities')
            .appendTo($section);

        var $table = $('<table>')
            .addClass('table table-condensed table-hover table-striped')
            .css('margin-bottom', '8px');

        $('<thead>')
            .append(
                $('<tr>').append(
                    $('<th>').text('MAC Address'),
                    $('<th>').text('Added'),
                    $('<th>')
                        .addClass('text-center')
                        .css('width', '180px')
                        .text('Actions')
                )
            )
            .appendTo($table);

        var $tbody = $('<tbody>').appendTo($table);

        if (!activeMembers.length) {
            $('<tr>')
                .append(
                    $('<td>')
                        .attr('colspan', 3)
                        .addClass('text-muted')
                        .text('No active identities')
                )
                .appendTo($tbody);
        }

        activeMembers.forEach(function(member) {
            var $actions = $('<div>').addClass('btn-group');

            $('<a>')
                .attr({
                    href: '/ui/devicemonitor/index/devicehistory?mac=' +
                        encodeURIComponent(member.mac || ''),
                    title: 'Open Device Details'
                })
                .addClass('btn btn-xs btn-default')
                .html('<i class="fa fa-external-link"></i> View')
                .appendTo($actions);

            if (!isArchived) {
                $('<button>')
                    .attr({
                        type: 'button',
                        title: 'Remove this identity from the physical device'
                    })
                    .addClass('btn btn-xs btn-danger')
                    .html('<i class="fa fa-unlink"></i> Remove')
                    .on('click', function() {
                        removePhysicalDeviceIdentity(
                            group.id,
                            group.name,
                            member.mac,
                            $(this)
                        );
                    })
                    .appendTo($actions);
            }

            $('<tr>')
                .append(
                    $('<td>').text(member.mac || '\u2014'),
                    $('<td>').text(dash(member.added_at)),
                    $('<td>').addClass('text-center').append($actions)
                )
                .appendTo($tbody);
        });

        $table.appendTo($section);
        return $section;
    }

    function buildHistoricalMembersSection(historicalMembers) {
        var $section = $('<div>');

        $('<div>')
            .addClass('member-section-title text-muted')
            .text('Historical identities')
            .appendTo($section);

        var $table = $('<table>')
            .addClass('table table-condensed table-striped')
            .css('margin-bottom', '8px');

        $('<thead>')
            .append(
                $('<tr>').append(
                    $('<th>').text('MAC Address'),
                    $('<th>').text('Added'),
                    $('<th>').text('Removed'),
                    $('<th>')
                        .addClass('text-center')
                        .css('width', '80px')
                        .text('Actions')
                )
            )
            .appendTo($table);

        var $tbody = $('<tbody>').appendTo($table);

        historicalMembers.forEach(function(member) {
            var $actions = $('<div>').addClass('btn-group');

            $('<a>')
                .attr({
                    href: '/ui/devicemonitor/index/devicehistory?mac=' +
                        encodeURIComponent(member.mac || ''),
                    title: 'Open Device Details'
                })
                .addClass('btn btn-xs btn-default')
                .html('<i class="fa fa-external-link"></i> View')
                .appendTo($actions);

            $('<tr>')
                .append(
                    $('<td>').text(member.mac || '\u2014'),
                    $('<td>').text(dash(member.added_at)),
                    $('<td>').text(dash(member.removed_at)),
                    $('<td>').addClass('text-center').append($actions)
                )
                .appendTo($tbody);
        });

        $table.appendTo($section);
        return $section;
    }

    function buildLinkForm(group) {
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

        var $linkButton = $('<button>')
            .attr('type', 'button')
            .addClass('btn btn-xs btn-primary')
            .html('<i class="fa fa-link"></i> Link Identity')
            .on('click', function() {
                linkPhysicalDeviceIdentity(
                    group.id,
                    group.name,
                    $macInput.val(),
                    $(this)
                );
            });

        $form.append($macInput, $linkButton);
        return $form;
    }

    function createPhysicalDevice(name, mac, button) {
        name = (name || '').trim();
        mac = (mac || '').trim().toLowerCase();

        if (!name) {
            showError('Enter a physical-device name');
            return;
        }

        if (!validMac(mac)) {
            showError('Enter a valid seed MAC address');
            return;
        }

        button.prop('disabled', true);

        $.ajax({
            url: '/api/devicemonitor/devices/createphysicaldevice',
            type: 'POST',
            data: {name: name, mac: mac},
            success: function(result) {
                if (result && result.result === 'saved') {
                    showToast('Physical device created', 'success');
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

        if (
            !confirm(
                'Link ' +
                relatedMac +
                ' to physical device "' +
                physicalDeviceName +
                '"?\n\n' +
                'Only continue if this MAC belongs to the same physical ' +
                'hardware. Do not link separate devices merely because ' +
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
                physical_device_id: physicalDeviceId,
                mac: relatedMac
            },
            success: function(result) {
                if (result && result.result === 'saved') {
                    showToast('Identity linked', 'success');
                    loadPhysicalDevices();
                    return;
                }

                button.prop('disabled', false);
                showError(
                    result && result.error
                        ? result.error
                        : 'Unable to link identity'
                );
            },
            error: function(xhr) {
                button.prop('disabled', false);
                showError(
                    xhr.responseJSON && xhr.responseJSON.error
                        ? xhr.responseJSON.error
                        : 'Unable to link identity'
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
                    showToast('Identity removed', 'success');
                    loadPhysicalDevices();
                    return;
                }

                button.prop('disabled', false);
                showError(
                    result && result.error
                        ? result.error
                        : 'Unable to remove identity'
                );
            },
            error: function(xhr) {
                button.prop('disabled', false);
                showError(
                    xhr.responseJSON && xhr.responseJSON.error
                        ? xhr.responseJSON.error
                        : 'Unable to remove identity'
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
