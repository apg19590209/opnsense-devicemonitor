<style>
.content-box .label {
    font-size: 12px;
}
</style>

<div class="content-box">
    <div class="content-box-main">

        <div style="padding:10px 10px 8px 10px;border-bottom:1px solid #333;margin-bottom:12px;">
            <a id="back-device-details"
               href="/ui/devicemonitor/index/devicehistory"
               class="btn btn-default btn-sm pull-right"
               style="font-size:14px;font-weight:600;padding:6px 12px;">
                <i class="fa fa-arrow-left"></i>
                {{ lang._('Back to Device Details') }}
            </a>

            <h1 style="margin:0;font-size:20px;">
                {{ lang._('Device Monitor') }}
                <span style="color:#555;margin:0 8px;">&ndash;</span>
                <span style="font-weight:normal;">
                    {{ lang._('Activity Timeline') }}
                </span>
            </h1>
        </div>

        <div class="panel panel-default">
            <div class="panel-heading">
                <strong>
                    <i class="fa fa-clock-o"></i>
                    {{ lang._('Activity Timeline') }}
                </strong>
                <span class="text-muted" style="margin-left:10px;">
                    {{ lang._('MAC address') }}:
                    <span id="timeline-mac">&mdash;</span>
                </span>
            </div>

            <div class="table-responsive">
                <table class="table table-condensed table-hover table-striped"
                       id="grid-device-timeline"
                       style="margin-bottom:0;">
                    <thead>
                        <tr>
                            <th style="width:190px;">
                                {{ lang._('Date / time') }}
                            </th>
                            <th style="width:220px;">
                                {{ lang._('Activity') }}
                            </th>
                            <th>{{ lang._('Details') }}</th>
                            <th style="width:100px;">
                                {{ lang._('Lifecycle') }}
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td colspan="4" class="text-muted">
                                {{ lang._('Loading activity...') }}
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

    function dash(value) {
        return value === null || value === undefined || value === ''
            ? '\u2014'
            : value;
    }

    function activityLabel(type) {
        var labels = {
            LIFECYCLE_STARTED: 'Lifecycle started',
            LIFECYCLE_ARCHIVED: 'Lifecycle archived',
            NOTE_CREATED: 'Note created',
            NOTE_UPDATED: 'Note edited',
            NOTE_ARCHIVED: 'Note archived',
            IP_CHANGED: 'IP address changed',
            HOSTNAME_CHANGED: 'Hostname changed',
            HOSTNAME_SOURCE_CHANGED: 'Hostname source changed',
            INTERFACE_CHANGED: 'Interface / VLAN changed',
            SERVICE_DISCOVERED: 'Service discovered',
            SERVICE_AVAILABLE: 'Service available',
            SERVICE_UNAVAILABLE: 'Service unavailable',
            SERVICE_CHANGED: 'Service changed',
            IP_IDENTITY_CHANGED: 'IPv4 address used by another device',
            IPV6_IDENTITY_CHANGED: 'IPv6 address used by another device',
            MAC_MULTI_IP: 'Device using multiple IPv4 addresses',
            MAC_MULTI_INTERFACE: 'Device seen on multiple interfaces',
            IDENTITY_RESOLVED: 'Identity issue resolved',
            NMAP_SCAN_COMPLETED: 'Targeted scan completed',
            NMAP_SCAN_FAILED: 'Targeted scan failed'
        };

        if (labels[type]) {
            return labels[type];
        }

        return (type || 'Activity')
            .toLowerCase()
            .replace(/_/g, ' ')
            .replace(/\b\w/g, function(letter) {
                return letter.toUpperCase();
            });
    }

    function activityClass(type) {
        if (
            type === 'LIFECYCLE_STARTED' ||
            type === 'SERVICE_AVAILABLE' ||
            type === 'IDENTITY_RESOLVED' ||
            type === 'NMAP_SCAN_COMPLETED'
        ) {
            return 'label-success';
        }

        if (
            type === 'SERVICE_UNAVAILABLE' ||
            type === 'LIFECYCLE_ARCHIVED' ||
            type === 'NOTE_ARCHIVED'
        ) {
            return 'label-warning';
        }

        if (
            type === 'NMAP_SCAN_FAILED' ||
            type === 'IP_IDENTITY_CHANGED' ||
            type === 'IPV6_IDENTITY_CHANGED' ||
            type === 'MAC_MULTI_IP' ||
            type === 'MAC_MULTI_INTERFACE'
        ) {
            return 'label-danger';
        }

        return 'label-info';
    }

    function transitionText(data) {
        var hasOld =
            data.old_value !== null &&
            data.old_value !== undefined;

        var hasNew =
            data.new_value !== null &&
            data.new_value !== undefined;

        var oldValue =
            hasOld && String(data.old_value) !== ''
                ? String(data.old_value)
                : '\u2014';

        var newValue =
            hasNew && String(data.new_value) !== ''
                ? String(data.new_value)
                : '\u2014';

        if (hasOld && hasNew) {
            return oldValue + ' \u2192 ' + newValue;
        }

        if (hasNew) {
            return newValue;
        }

        if (hasOld) {
            return oldValue;
        }

        return '';
    }

    function serviceTransitionDetails(data) {
        var parts = String(data.details || '').split('|');
        var result = [];

        if (parts[0]) {
            result.push(parts[0]);
        }

        if (parts[1]) {
            var endpoint = parts[1];

            if (parts[2] && parts[2] !== '0') {
                endpoint += ':' + parts[2];
            }

            if (parts[3]) {
                endpoint += '/' + parts[3];
            }

            result.push(endpoint);
        }

        if (parts[4]) {
            result.push(parts[4]);
        }

        if (parts[5]) {
            result.push(parts[5]);
        }

        var transition = transitionText(data);

        if (transition) {
            result.push(transition);
        }

        return result.join(' \u00b7 ');
    }

    function activityDetails(row) {
        var data = row && row.data ? row.data : {};
        var details = [];

        if (row.source === 'note') {
            return dash(data.comment);
        }

        if (
            row.source === 'activity' &&
            String(row.event_type || '').indexOf('SERVICE_') === 0
        ) {
            return serviceTransitionDetails(data) || '\u2014';
        }

        if (row.source === 'activity') {
            return transitionText(data) || dash(data.details);
        }

        if (row.source === 'lifecycle') {
            return row.lifecycle_id
                ? 'Lifecycle #' + row.lifecycle_id
                : '\u2014';
        }

        if (row.source === 'service') {
            if (data.service_type) {
                details.push(data.service_type);
            }

            if (data.ip) {
                var endpoint = data.ip;

                if (data.port) {
                    endpoint += ':' + data.port;
                }

                if (data.protocol) {
                    endpoint += '/' + data.protocol;
                }

                details.push(endpoint);
            }

            if (data.interface) {
                details.push(data.interface);
            }

            if (data.detection_method) {
                details.push(data.detection_method);
            }

            return details.length
                ? details.join(' \u00b7 ')
                : '\u2014';
        }

        if (row.source === 'scan') {
            if (data.scan_type) {
                details.push(data.scan_type);
            }

            if (data.ip) {
                details.push(data.ip);
            }

            if (
                data.open_port_count !== null &&
                data.open_port_count !== undefined
            ) {
                details.push('Open ports: ' + data.open_port_count);
            }

            if (data.os_hint) {
                details.push('OS: ' + data.os_hint);
            }

            if (data.error) {
                details.push(data.error);
            }

            return details.length
                ? details.join(' \u00b7 ')
                : '\u2014';
        }

        if (row.source === 'identity') {
            if (data.ip) {
                details.push('IP: ' + data.ip);
            }

            if (data.other_ip) {
                details.push('Other IP: ' + data.other_ip);
            }

            if (data.other_mac) {
                details.push('Other MAC: ' + data.other_mac);
            }

            if (data.interface) {
                details.push('Interface: ' + data.interface);
            }

            if (
                data.other_interface &&
                data.other_interface !== data.interface
            ) {
                details.push(
                    'Other interface: ' + data.other_interface
                );
            }

            return details.length
                ? details.join(' \u00b7 ')
                : dash(data.details);
        }

        return dash(data.details);
    }

    function renderTimeline(rows) {
        var $tbody = $('#grid-device-timeline tbody').empty();

        if (!Array.isArray(rows) || !rows.length) {
            $('<tr>').append(
                $('<td>')
                    .attr('colspan', 4)
                    .addClass('text-muted')
                    .text('No activity recorded')
            ).appendTo($tbody);
            return;
        }

        rows.forEach(function(row) {
            var $label = $('<span>')
                .addClass(
                    'label ' +
                    activityClass(row.event_type || '')
                )
                .text(activityLabel(row.event_type));

            $('<tr>').append(
                $('<td>')
                    .css('white-space', 'nowrap')
                    .text(dash(row.occurred_at)),
                $('<td>').append($label),
                $('<td>')
                    .css({
                        'white-space': 'pre-wrap',
                        'overflow-wrap': 'anywhere'
                    })
                    .text(activityDetails(row)),
                $('<td>').text(
                    row.lifecycle_id
                        ? '#' + row.lifecycle_id
                        : '\u2014'
                )
            ).appendTo($tbody);
        });
    }

    function showLoadError(message) {
        $('#grid-device-timeline tbody')
            .empty()
            .append(
                $('<tr>').append(
                    $('<td>')
                        .attr('colspan', 4)
                        .addClass('text-danger')
                        .text(message)
                )
            );
    }

    $('#timeline-mac').text(mac || '\u2014');

    $('#back-device-details').attr(
        'href',
        '/ui/devicemonitor/index/devicehistory?mac=' +
            encodeURIComponent(mac)
    );

    if (!mac) {
        showLoadError('MAC address required');
        return;
    }

    $.ajax({
        url: '/api/devicemonitor/devices/timeline',
        type: 'GET',
        data: {
            mac: mac,
            limit: 200
        },
        success: function(result) {
            if (
                !result ||
                result.result !== 'ok' ||
                !Array.isArray(result.rows)
            ) {
                showLoadError('Unable to load activity');
                return;
            }

            renderTimeline(result.rows);
        },
        error: function() {
            showLoadError('Unable to load activity');
        }
    });
});
</script>
