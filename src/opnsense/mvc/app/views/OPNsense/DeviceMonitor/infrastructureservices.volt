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
                <span>
                    {{ lang._('Stale') }}:
                    <strong id="services-stale">0</strong>
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
            <button
                id="btn-services-discover"
                type="button"
                class="btn btn-success btn-sm"
            >
                <i class="fa fa-search"></i>
                {{ lang._('Discover Now') }}
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
                <option value="stale">
                    {{ lang._('Stale') }}
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
    width: 100%;
    table-layout: fixed;
    margin-bottom: 0;
}

/* Keep identical column widths across every service group */
.infrastructure-service-table th:nth-child(1),
.infrastructure-service-table td:nth-child(1) {
    width: 13%;
    white-space: nowrap;
}

.infrastructure-service-table th:nth-child(2),
.infrastructure-service-table td:nth-child(2) {
    width: 13%;
}

.infrastructure-service-table th:nth-child(3),
.infrastructure-service-table td:nth-child(3) {
    width: 8%;
}

.infrastructure-service-table th:nth-child(4),
.infrastructure-service-table td:nth-child(4) {
    width: 10%;
}

.infrastructure-service-table th:nth-child(5),
.infrastructure-service-table td:nth-child(5) {
    width: 11%;
}

.infrastructure-service-table th:nth-child(6),
.infrastructure-service-table td:nth-child(6) {
    width: 12%;
}

.infrastructure-service-table th:nth-child(7),
.infrastructure-service-table td:nth-child(7) {
    width: 9%;
}

.infrastructure-service-table th:nth-child(8),
.infrastructure-service-table td:nth-child(8) {
    width: 13%;
}

.infrastructure-service-table th:nth-child(9),
.infrastructure-service-table td:nth-child(9) {
    width: 11%;
}

.infrastructure-service-table th,
.infrastructure-service-table td {
    overflow-wrap: anywhere;
}

.infrastructure-service-table th:nth-child(3),
.infrastructure-service-table td:nth-child(3),
.infrastructure-service-table th:nth-child(4),
.infrastructure-service-table td:nth-child(4),
.infrastructure-service-table th:nth-child(7),
.infrastructure-service-table td:nth-child(7),
.infrastructure-service-table th:nth-child(9),
.infrastructure-service-table td:nth-child(9) {
    white-space: nowrap;
}

.infrastructure-service-table td,
.infrastructure-service-table th {
    vertical-align: middle !important;
}

.infrastructure-service-product {
    white-space: normal;
    min-width: 120px;
}

/* Last Verified timestamp wrapping */
.infrastructure-service-table th:nth-child(9),
.infrastructure-service-table td:nth-child(9) {
    white-space: normal;
    overflow-wrap: normal;
    word-break: normal;
    font-variant-numeric: tabular-nums;
    font-size: 12px;
}</style>

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
            WEB_ADMIN: 'Web / Admin Services',
            SMB: 'File / NAS Services',
            NFS: 'File / NAS Services',
            RDP: 'Remote Access',
            VNC: 'Remote Access',
            WINRM: 'Remote Access',
            LDAP: 'Directory / Authentication',
            LDAPS: 'Directory / Authentication',
            KERBEROS: 'Directory / Authentication',
            SNMP: 'SNMP / Management',
            VPN: 'VPN Endpoints'
        };

        return names[type] || (type + ' Services');
    }
    function statusBadge(status) {
        var className = 'label-default';
        var label = status || 'Unknown';

        if (status === 'available') {
            className = 'label-success';
            label = 'Available';
        } else if (status === 'unavailable') {
            className = 'label-danger';
            label = 'Unavailable';
        } else if (status === 'stale') {
            className = 'label-warning';
            label = 'Stale';
        }

        return $('<span>')
            .addClass('label ' + className)
            .text(label);
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
            row.display_status || row.status,
            row.detection_method,
            row.confidence,
            row.product,
            row.version,
            row.port,
            row.protocol
        ].join(' ').toLowerCase();
    }
    function verifiedTime(value) {
        if (!value) {
            return 0;
        }

        var parsed = Date.parse(
            value.replace(' ', 'T')
        );

        return isNaN(parsed) ? 0 : parsed;
    }

    function confidenceRank(value) {
        var ranks = {
            authoritative: 3,
            verified: 2,
            discovered: 1
        };

        return ranks[value] || 0;
    }

    function effectiveStatus(row) {
        if (row.status !== 'available') {
            return row.status;
        }

        var verified = verifiedTime(row.last_verified);

        if (!verified) {
            return 'stale';
        }

        /* Two missed hourly discovery windows = stale. */
        if (
            Date.now() - verified >
            2 * 60 * 60 * 1000
        ) {
            return 'stale';
        }

        return 'available';
    }

    function consolidateServices(rows) {
        var grouped = {};

        (rows || []).forEach(function(row) {
            var type =
                (row.service_type || '').toUpperCase();

            var key = [
                type,
                row.ip || '',
                row.port || '',
                (row.protocol || '').toLowerCase()
            ].join('|');

            var method = row.detection_method || '';

            if (!grouped[key]) {
                grouped[key] = $.extend({}, row);
                grouped[key].service_type = type;
                grouped[key].evidence = [];

                if (method) {
                    grouped[key].evidence.push(method);
                }

                return;
            }

            var current = grouped[key];

            if (
                method &&
                current.evidence.indexOf(method) === -1
            ) {
                current.evidence.push(method);
            }

            if (
                confidenceRank(row.confidence) >
                confidenceRank(current.confidence)
            ) {
                current.confidence = row.confidence;

                if (row.product) {
                    current.product = row.product;
                }

                if (row.version) {
                    current.version = row.version;
                }
            }

            if (
                verifiedTime(row.last_verified) >
                verifiedTime(current.last_verified)
            ) {
                current.last_verified = row.last_verified;
            }

            if (row.status === 'available') {
                current.status = 'available';
            }

            [
                'hostname',
                'vendor',
                'mac',
                'interface',
                'vlan',
                'product',
                'version'
            ].forEach(function(field) {
                if (!current[field] && row[field]) {
                    current[field] = row[field];
                }
            });
        });

        return Object.keys(grouped).map(function(key) {
            var row = grouped[key];

            row.evidence.sort();
            row.display_status = effectiveStatus(row);

            return row;
        });
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

            if (status && (row.display_status || row.status) !== status) {
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
            'KERBEROS',
            'SNMP',
            'VPN'
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
                            statusBadge(row.display_status || row.status)
                        ),
                        $('<td>').text(endpoint),
                        $('<td>').text(locationText(row)),
                        $('<td>').text(
                            row.evidence && row.evidence.length
                                ? row.evidence.join(' + ')
                                : dash(row.detection_method)
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
                allServices = consolidateServices(
                    data && Array.isArray(data.rows)
                        ? data.rows
                        : []
                );

                var available = 0;
                var unavailable = 0;
                var stale = 0;

                allServices.forEach(function(row) {
                    var status =
                        row.display_status || row.status;

                    if (status === 'available') {
                        available++;
                    } else if (status === 'unavailable') {
                        unavailable++;
                    } else if (status === 'stale') {
                        stale++;
                    }
                });

                $('#services-total').text(allServices.length);
                $('#services-available').text(available);
                $('#services-unavailable').text(unavailable);
                $('#services-stale').text(stale);

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
    $('#btn-services-discover').on('click', function() {
        var $button = $(this);

        $button
            .prop('disabled', true)
            .find('i')
            .removeClass('fa-search')
            .addClass('fa-refresh fa-spin');

        $.ajax({
            url: '/api/devicemonitor/devices/discoverservices',
            type: 'POST',

            success: function(data) {
                if (!data || data.result !== 'ok') {
                    alert(
                        data && data.error
                            ? data.error
                            : 'Infrastructure discovery failed.'
                    );
                    return;
                }

                loadServices();
            },

            error: function() {
                alert('Infrastructure discovery failed.');
            },

            complete: function() {
                $button
                    .prop('disabled', false)
                    .find('i')
                    .removeClass('fa-refresh fa-spin')
                    .addClass('fa-search');
            }
        });
    });

    $('#services-type-filter, #services-status-filter')
        .on('change', renderServices);

    $('#services-search').on('input', renderServices);

    loadServices();
});
</script>
