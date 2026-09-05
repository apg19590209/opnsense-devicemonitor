<div class="content-box">
    <div class="content-box-main">

        <div class="infrastructure-header">
            <h1>
                {{ lang._('Device Monitor') }}
                <span class="infrastructure-divider">&ndash;</span>
                <span class="infrastructure-title">
                    {{ lang._('Infrastructure Services') }}
                </span>
            </h1>

            <div class="infrastructure-stats">
                <span>
                    {{ lang._('Total') }}:
                    <strong id="services-total">0</strong>
                </span>
                <span>
                    {{ lang._('Available') }}:
                    <strong id="services-available">0</strong>
                </span>
                <span>
                    {{ lang._('Unavailable') }}:
                    <strong id="services-unavailable">0</strong>
                </span>
            </div>
        </div>

        <div class="infrastructure-toolbar">
            <button
                id="btn-services-refresh"
                type="button"
                class="btn btn-primary btn-sm"
            >
                <i class="fa fa-refresh"></i>
                {{ lang._('Refresh View') }}
            </button>

            <select
                id="services-type-filter"
                class="form-control input-sm"
            >
                <option value="">
                    {{ lang._('All Services') }}
                </option>
            </select>

            <select
                id="services-status-filter"
                class="form-control input-sm"
            >
                <option value="">
                    {{ lang._('All Statuses') }}
                </option>
                <option value="available">
                    {{ lang._('Available') }}
                </option>
                <option value="unavailable">
                    {{ lang._('Unavailable') }}
                </option>
            </select>

            <input
                id="services-search"
                type="text"
                class="form-control input-sm"
                placeholder="{{ lang._('Search services') }}"
            />

            <span class="text-muted">
                {{ lang._('Showing') }}
                <strong id="services-visible">0</strong>
            </span>
        </div>

        <div id="infrastructure-service-groups">
            <div class="text-muted">
                {{ lang._('Loading infrastructure services') }}...
            </div>
        </div>

    </div>
</div>

<style>
.infrastructure-header {
    padding: 10px 10px 8px 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
    border-bottom: 1px solid #444;
    margin-bottom: 12px;
}

.infrastructure-header h1 {
    margin: 0;
    font-size: 20px;
}

.infrastructure-divider {
    color: #777;
    margin: 0 8px;
}

.infrastructure-title {
    font-weight: normal;
}

.infrastructure-stats {
    display: flex;
    gap: 20px;
    align-items: center;
    font-size: 13px;
}

.infrastructure-stats strong {
    font-size: 16px;
    margin-left: 4px;
}

.infrastructure-toolbar {
    padding: 0 4px 12px 4px;
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
}

.infrastructure-toolbar select.form-control {
    width: 180px;
    height: 30px;
    min-width: 180px;
    padding: 4px 8px;
    line-height: 20px;
    vertical-align: middle;
}

.infrastructure-toolbar input {
    width: 230px;
}

.infrastructure-service-group {
    margin-bottom: 16px;
}

.infrastructure-service-group .panel-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.infrastructure-service-table {
    margin-bottom: 0;
}

.infrastructure-service-table td,
.infrastructure-service-table th {
    vertical-align: middle !important;
}

.infrastructure-service-product {
    white-space: normal;
    min-width: 120px;
}
</style>

<script>
$(document).ready(function() {
    var allServices = [];

    function dash(value) {
        if (value === undefined || value === null || value === '') {
            return '\u2014';
        }

        return value;
    }

    function groupTitle(type) {
        var names = {
            DHCP: 'DHCP Servers',
            DNS: 'DNS Servers',
            NTP: 'NTP Servers',
            SSH: 'SSH Servers',
            WEB_ADMIN: 'Web / Admin Interfaces',
            SMB: 'File / NAS Services',
            NFS: 'File / NAS Services',
            RDP: 'Remote Access',
            VNC: 'Remote Access',
            WINRM: 'Remote Access',
            LDAP: 'Directory / Authentication',
            LDAPS: 'Directory / Authentication',
            KERBEROS: 'Directory / Authentication'
        };

        return names[type] || (type + ' Services');
    }

    function statusBadge(status) {
        var available = status === 'available';

        return $('<span>')
            .addClass(
                'label ' +
                (available ? 'label-success' : 'label-danger')
            )
            .text(
                available
                    ? 'Available'
                    : 'Unavailable'
            );
    }

    function productText(row) {
        var parts = [];

        if (row.product) {
            parts.push(row.product);
        }

        if (row.version) {
            parts.push(row.version);
        }

        return parts.length ? parts.join(' ') : '\u2014';
    }

    function locationText(row) {
        var values = [];

        if (row.interface) {
            values.push(row.interface);
        }

        if (row.vlan && values.indexOf(row.vlan) === -1) {
            values.push(row.vlan);
        }

        return values.length ? values.join(' / ') : '\u2014';
    }

    function searchText(row) {
        return [
            row.service_type,
            row.ip,
            row.mac,
            row.hostname,
            row.vendor,
            row.interface,
            row.vlan,
            row.status,
            row.detection_method,
            row.confidence,
            row.product,
            row.version,
            row.port,
            row.protocol
        ].join(' ').toLowerCase();
    }

    function filteredRows() {
        var type = $('#services-type-filter').val();
        var status = $('#services-status-filter').val();
        var search = ($('#services-search').val() || '')
            .toLowerCase()
            .trim();

        return allServices.filter(function(row) {
            if (
                type &&
                (row.service_type || '').toUpperCase() !== type
            ) {
                return false;
            }

            if (status && row.status !== status) {
                return false;
            }

            if (search && searchText(row).indexOf(search) === -1) {
                return false;
            }

            return true;
        });
    }

    function renderServices() {
        var rows = filteredRows();
        var groups = {};
        var $root = $('#infrastructure-service-groups').empty();

        $('#services-visible').text(rows.length);

        if (!rows.length) {
            $('<div>')
                .addClass('alert alert-info')
                .text('No infrastructure services match the current filter.')
                .appendTo($root);

            return;
        }

        rows.forEach(function(row) {
            var type = (row.service_type || 'OTHER')
                .toUpperCase();

            if (!groups[type]) {
                groups[type] = [];
            }

            groups[type].push(row);
        });

        var preferredOrder = [
            'DHCP',
            'DNS',
            'NTP',
            'SSH',
            'WEB_ADMIN',
            'SMB',
            'NFS',
            'RDP',
            'VNC',
            'WINRM',
            'LDAP',
            'LDAPS',
            'KERBEROS'
        ];

        var types = Object.keys(groups);

        types.sort(function(a, b) {
            var ai = preferredOrder.indexOf(a);
            var bi = preferredOrder.indexOf(b);

            if (ai === -1) {
                ai = 999;
            }

            if (bi === -1) {
                bi = 999;
            }

            if (ai !== bi) {
                return ai - bi;
            }

            return a.localeCompare(b);
        });

        types.forEach(function(type) {
            var groupRows = groups[type];

            var $panel = $('<div>')
                .addClass(
                    'panel panel-default infrastructure-service-group'
                );

            $('<div>')
                .addClass('panel-heading')
                .append(
                    $('<strong>').text(groupTitle(type)),
                    $('<span>')
                        .addClass('badge')
                        .text(groupRows.length)
                )
                .appendTo($panel);

            var $table = $('<table>')
                .addClass(
                    'table table-condensed table-hover ' +
                    'infrastructure-service-table'
                );

            $('<thead>')
                .append(
                    $('<tr>').append(
                        $('<th>').text('IP Address'),
                        $('<th>').text('Hostname'),
                        $('<th>').text('Status'),
                        $('<th>').text('Port / Protocol'),
                        $('<th>').text('Interface / VLAN'),
                        $('<th>').text('Detection'),
                        $('<th>').text('Confidence'),
                        $('<th>').text('Product / Version'),
                        $('<th>').text('Last Verified')
                    )
                )
                .appendTo($table);

            var $body = $('<tbody>');

            groupRows.forEach(function(row) {
                var endpoint =
                    dash(row.port) +
                    ' / ' +
                    (row.protocol || '').toUpperCase();

                var $hostname = $('<td>');

                $('<div>')
                    .text(dash(row.hostname))
                    .appendTo($hostname);

                if (row.vendor) {
                    $('<small>')
                        .addClass('text-muted')
                        .text(row.vendor)
                        .appendTo($hostname);
                }

                $('<tr>')
                    .append(
                        $('<td>').text(dash(row.ip)),
                        $hostname,
                        $('<td>').append(
                            statusBadge(row.status)
                        ),
                        $('<td>').text(endpoint),
                        $('<td>').text(locationText(row)),
                        $('<td>').text(
                            dash(row.detection_method)
                        ),
                        $('<td>').text(
                            dash(row.confidence)
                        ),
                        $('<td>')
                            .addClass(
                                'infrastructure-service-product'
                            )
                            .text(productText(row)),
                        $('<td>').text(
                            dash(row.last_verified)
                        )
                    )
                    .appendTo($body);
            });

            $body.appendTo($table);
            $table.appendTo($panel);
            $panel.appendTo($root);
        });
    }

    function populateTypes(types) {
        var current = $('#services-type-filter').val();
        var $select = $('#services-type-filter');

        $select.find('option:not(:first)').remove();

        (types || []).forEach(function(type) {
            $('<option>')
                .attr('value', type)
                .text(groupTitle(type))
                .appendTo($select);
        });

        if (current) {
            $select.val(current);
        }
    }

    function loadServices() {
        $('#btn-services-refresh')
            .prop('disabled', true)
            .find('i')
            .addClass('fa-spin');

        $.ajax({
            url: '/api/devicemonitor/devices/services',
            type: 'GET',

            success: function(data) {
                allServices =
                    data && Array.isArray(data.rows)
                        ? data.rows
                        : [];

                $('#services-total').text(
                    data && data.total !== undefined
                        ? data.total
                        : 0
                );

                $('#services-available').text(
                    data && data.available !== undefined
                        ? data.available
                        : 0
                );

                $('#services-unavailable').text(
                    data && data.unavailable !== undefined
                        ? data.unavailable
                        : 0
                );

                populateTypes(
                    data && Array.isArray(data.types)
                        ? data.types
                        : []
                );

                renderServices();
            },

            error: function() {
                $('#infrastructure-service-groups')
                    .empty()
                    .append(
                        $('<div>')
                            .addClass('alert alert-danger')
                            .text(
                                'Unable to load infrastructure services.'
                            )
                    );
            },

            complete: function() {
                $('#btn-services-refresh')
                    .prop('disabled', false)
                    .find('i')
                    .removeClass('fa-spin');
            }
        });
    }

    $('#btn-services-refresh').on('click', loadServices);

    $('#services-type-filter, #services-status-filter')
        .on('change', renderServices);

    $('#services-search').on('input', renderServices);

    loadServices();
});
</script>
