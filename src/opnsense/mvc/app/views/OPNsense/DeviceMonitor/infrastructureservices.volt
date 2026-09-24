<div class="content-box">
    <div class="content-box-main">

        <div id="infrastructure-sticky-controls" class="infrastructure-sticky-controls">
            <div class="infrastructure-header">
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
                    class="selectpicker"
                    data-style="btn-default btn-sm"
                    data-width="180px"
                >
                    <option value="">
                        {{ lang._('All Services') }}
                    </option>
                </select>

                <select
                    id="services-status-filter"
                    class="selectpicker"
                    data-style="btn-default btn-sm"
                    data-width="180px"
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

            <ul id="infrastructure-tabs"
                class="nav nav-tabs infrastructure-tabs"
                role="tablist">
                <li role="presentation" class="active">
                    <a href="#tab-infrastructure-recent-changes"
                       data-toggle="tab"
                       role="tab"
                       aria-controls="tab-infrastructure-recent-changes">
                        {{ lang._('Recent Service Changes') }}
                    </a>
                </li>
                <li role="presentation">
                    <a href="#tab-infrastructure-port-discovery"
                       data-toggle="tab" role="tab"
                       aria-controls="tab-infrastructure-port-discovery">
                        {{ lang._('Port Discovery') }}
                    </a>
                </li>
            </ul>
        </div>

        <div id="infrastructure-tab-content" class="tab-content infrastructure-tab-content">
            <div id="tab-infrastructure-recent-changes"
                 class="tab-pane fade in active"
                 role="tabpanel">
                <div class="panel panel-default infrastructure-recent-changes">
                    <div class="panel-heading">
                        <span class="text-muted">
                            {{ lang._('Latest verified or authoritative service changes') }}
                        </span>
                    </div>
                    <div id="infrastructure-recent-changes">
                        <div class="text-muted">
                            {{ lang._('Loading recent service changes') }}...
                        </div>
                    </div>
                </div>
            </div>
            <div id="tab-infrastructure-port-discovery"
                 class="tab-pane fade" role="tabpanel">
                <div class="panel panel-default infrastructure-recent-changes">
                    <div class="panel-heading">
                        {{ lang._('Port Discovery') }}
                    </div>
                    <div class="panel-body">
                        <p class="text-muted">
                            {{ lang._('Select one monitored device. A full TCP port scan is bounded to 120 seconds. Scheduled scans are opt-in and run at most once a week per selected device, one host at a time. UDP services such as WireGuard require separate authoritative evidence.') }}
                        </p>
                        <div class="form-inline">
                            <label for="port-discovery-device">
                                {{ lang._('Device') }}
                            </label>
                            <select id="port-discovery-device"
                                    class="form-control input-sm"
                                    style="max-width:360px"></select>
                            <button type="button" id="btn-port-discovery-run"
                                    class="btn btn-primary btn-sm">
                                {{ lang._('Run Now') }}
                            </button>
                            <label class="checkbox-inline">
                                <input type="checkbox" id="port-discovery-schedule">
                                {{ lang._('Scan weekly') }}
                            </label>
                            <button type="button" id="btn-port-discovery-refresh"
                                    class="btn btn-default btn-sm">
                                {{ lang._('Refresh') }}
                            </button>
                        </div>
                        <p id="port-discovery-status" class="text-muted"
                           role="status"></p>
                    </div>
                    <div class="table-responsive">
                        <table class="table table-striped table-condensed">
                            <thead><tr>
                                <th>{{ lang._('Device') }}</th>
                                <th>{{ lang._('Scan Time') }}</th>
                                <th>{{ lang._('Result') }}</th>
                                <th>{{ lang._('Open TCP Ports') }}</th>
                            </tr></thead>
                            <tbody id="port-discovery-results"></tbody>
                        </table>
                    </div>
                </div>
            </div>
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

.infrastructure-toolbar input {
    width: 230px;
}

.infrastructure-recent-changes {
    margin: 0 4px 16px 4px;
}

.infrastructure-recent-changes .panel-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
}

.infrastructure-recent-table {
    width: 100%;
    table-layout: fixed;
    margin-bottom: 0;
}

.infrastructure-recent-table th,
.infrastructure-recent-table td {
    overflow-wrap: anywhere;
    vertical-align: middle !important;
}

.infrastructure-recent-table th:nth-child(1),
.infrastructure-recent-table td:nth-child(1) {
    width: 17%;
    white-space: nowrap;
}

.infrastructure-recent-table th:nth-child(2),
.infrastructure-recent-table td:nth-child(2) {
    width: 17%;
}

.infrastructure-recent-table th:nth-child(3),
.infrastructure-recent-table td:nth-child(3) {
    width: 13%;
}

.infrastructure-recent-table th:nth-child(4),
.infrastructure-recent-table td:nth-child(4) {
    width: 16%;
}

.infrastructure-recent-table th:nth-child(5),
.infrastructure-recent-table td:nth-child(5) {
    width: 15%;
}

.infrastructure-recent-table th:nth-child(6),
.infrastructure-recent-table td:nth-child(6) {
    width: 15%;
}

.infrastructure-recent-table th:nth-child(7),
.infrastructure-recent-table td:nth-child(7) {
    width: 7%;
    text-align: center;
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
}

/* Tabbed Infrastructure Services layout. */
.infrastructure-tabs {
    padding: 0 4px;
    margin-bottom: 0;
}

.infrastructure-tabs > li > a {
    padding: 8px 14px;
}

.infrastructure-tabs .badge {
    margin-left: 6px;
    background-color: #555;
    font-weight: 600;
}

.infrastructure-tab-content {
    padding: 12px 4px 0 4px;
}

/* Sticky stack: OPNsense page title bar, then the unified controls block
   (header + toolbar + tab strip), then the active table column headers.
   Mirrors the proven Change Summary sticky-header implementation. */
.infrastructure-sticky-controls {
    position: sticky;
    z-index: 20;
}

.infrastructure-sticky-controls::before {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    bottom: 100%;
    height: var(--infrastructure-sticky-gap, 0px);
    background: inherit;
    pointer-events: none;
}

header.page-content-head {
    position: sticky;
    z-index: 30;
}

.infrastructure-tab-content thead th {
    position: sticky;
    z-index: 10;
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

    function serviceChangeLabel(row) {
        var type = String(row.event_type || '');

        if (type === 'SERVICE_DISCOVERED') {
            return 'New verified service';
        }

        if (type === 'SERVICE_UNAVAILABLE') {
            return 'Service unavailable';
        }

        if (type === 'SERVICE_AVAILABLE') {
            return 'Service recovered';
        }

        if (type === 'SERVICE_CHANGED') {
            return 'Service changed';
        }

        return type || '\u2014';
    }

    function serviceChangeDetail(row) {
        var oldValue = String(row.old_value || '');
        var newValue = String(row.new_value || '');

        if (oldValue && newValue && oldValue !== newValue) {
            return oldValue + ' \u2192 ' + newValue;
        }

        return '';
    }

    function recentDeviceText(row) {
        return row.custom_hostname ||
            row.hostname ||
            row.mac ||
            '\u2014';
    }

    function recentEndpointText(row) {
        var endpoint = String(row.ip || '');

        if (row.port) {
            endpoint += ':' + row.port;
        }

        if (row.protocol) {
            endpoint += '/' + String(row.protocol).toUpperCase();
        }

        return endpoint || '\u2014';
    }

    function recentEvidenceText(row) {
        var parts = [];

        if (row.detection_method) {
            parts.push(row.detection_method);
        }

        if (row.confidence) {
            parts.push(row.confidence);
        }

        return parts.length ? parts.join(' / ') : '\u2014';
    }

    function renderRecentServiceChanges(rows) {
        var $root = $('#infrastructure-recent-changes').empty();
        var changes = Array.isArray(rows) ? rows : [];

        if (!changes.length) {
            $('<div>')
                .addClass('text-muted')
                .css('padding', '10px')
                .text('No verified infrastructure service changes recorded yet.')
                .appendTo($root);
            return;
        }

        var $table = $('<table>')
            .addClass(
                'table table-condensed table-hover infrastructure-recent-table'
            );

        $('<thead>')
            .append(
                $('<tr>').append(
                    $('<th>').text('Date / Time'),
                    $('<th>').text('Change'),
                    $('<th>').text('Service'),
                    $('<th>').text('Device'),
                    $('<th>').text('Endpoint'),
                    $('<th>').text('Evidence'),
                    $('<th>').text('History')
                )
            )
            .appendTo($table);

        var $body = $('<tbody>');

        changes.forEach(function(row) {
            var $change = $('<td>');
            var detail = serviceChangeDetail(row);

            $('<div>')
                .text(serviceChangeLabel(row))
                .appendTo($change);

            if (detail) {
                $('<small>')
                    .addClass('text-muted')
                    .css('display', 'block')
                    .text(detail)
                    .appendTo($change);
            }

            var $history = $('<td>');

            if (row.mac) {
                $('<a>')
                    .addClass('btn btn-default btn-xs')
                    .attr(
                        'href',
                        '/ui/devicemonitor/index/activitytimeline?mac=' +
                            encodeURIComponent(row.mac)
                    )
                    .attr('title', 'Open device activity')
                    .append(
                        $('<i>').addClass('fa fa-history')
                    )
                    .appendTo($history);
            } else {
                $history.text('\u2014');
            }

            $('<tr>')
                .append(
                    $('<td>').text(dash(row.occurred_at)),
                    $change,
                    $('<td>').text(
                        groupTitle(
                            String(row.service_type || 'OTHER').toUpperCase()
                        )
                    ),
                    $('<td>').text(recentDeviceText(row)),
                    $('<td>').text(recentEndpointText(row)),
                    $('<td>').text(recentEvidenceText(row)),
                    $history
                )
                .appendTo($body);
        });

        $body.appendTo($table);
        $table.appendTo($root);
    }

    function searchText(row) {
        return [
            row.service_type,
            row.ip,
            row.mac,
            row.custom_hostname,
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

    var categoryOrder = [
        'DHCP Servers',
        'DNS Servers',
        'NTP Servers',
        'SSH Servers',
        'Web / Admin Services',
        'File / NAS Services',
        'Remote Access',
        'Directory / Authentication',
        'SNMP / Management',
        'VPN Endpoints'
    ];

    var servicePaneIds = {};

    function categoryForType(type) {
        return groupTitle(type);
    }

    function categoryRank(category) {
        var index = categoryOrder.indexOf(category);

        return index === -1 ? 999 : index;
    }

    function typeRank(type) {
        var index = preferredOrder.indexOf(type);

        return index === -1 ? 999 : index;
    }

    function ipCompare(a, b) {
        var aa = (a || '').split('.').map(Number);
        var bb = (b || '').split('.').map(Number);

        for (var i = 0; i < 4; i++) {
            var av = aa[i] || 0;
            var bv = bb[i] || 0;

            if (av !== bv) {
                return av - bv;
            }
        }

        return 0;
    }

    function categorySlug(name) {
        return 'tab-services-' +
            String(name)
                .toLowerCase()
                .replace(/[^a-z0-9]+/g, '-')
                .replace(/^-+|-+$/g, '');
    }

    function renderTabs() {
        var categories = {};

        allServices.forEach(function(row) {
            var category = categoryForType(
                String(row.service_type || 'OTHER').toUpperCase()
            );

            if (!categories[category]) {
                categories[category] = 0;
            }

            categories[category] += 1;
        });

        var names = Object.keys(categories);

        names.sort(function(a, b) {
            var ai = categoryRank(a);
            var bi = categoryRank(b);

            if (ai !== bi) {
                return ai - bi;
            }

            return a.localeCompare(b);
        });

        servicePaneIds = {};

        var $tabs = $('#infrastructure-tabs');
        var $content = $('#infrastructure-tab-content');

        var activeHref = '';
        var $active = $('#infrastructure-tabs li.active > a');

        if ($active.length) {
            activeHref = $active.attr('href');
        }

        $tabs.find('[data-service-tab]').remove();
        $content.find('[data-service-pane]').remove();

        names.forEach(function(name) {
            var paneId = categorySlug(name);

            servicePaneIds[name] = paneId;

            $('<li>')
                .attr('role', 'presentation')
                .attr('data-service-tab', '1')
                .append(
                    $('<a>')
                        .attr('href', '#' + paneId)
                        .attr('data-toggle', 'tab')
                        .attr('role', 'tab')
                        .attr('aria-controls', paneId)
                        .append(document.createTextNode(' ' + name + ' '))
                        .append(
                            $('<span>')
                                .addClass('badge')
                                .text(categories[name])
                        )
                )
                .appendTo($tabs);

            $('<div>')
                .addClass('tab-pane fade')
                .attr('role', 'tabpanel')
                .attr('id', paneId)
                .attr('data-service-pane', '1')
                .appendTo($content);
        });

        if (
            activeHref &&
            activeHref !== '#tab-infrastructure-recent-changes'
        ) {
            var $restore = $(
                '#infrastructure-tabs a[href="' + activeHref + '"]'
            );

            if ($restore.length) {
                $restore.tab('show');
            }
        }
    }

    function renderServices() {
        var rows = filteredRows();

        $('#services-visible').text(rows.length);

        var grouped = {};

        rows.forEach(function(row) {
            var category = categoryForType(
                String(row.service_type || 'OTHER').toUpperCase()
            );

            if (!grouped[category]) {
                grouped[category] = [];
            }

            grouped[category].push(row);
        });

        Object.keys(servicePaneIds).forEach(function(name) {
            var categoryRows = grouped[name] || [];

            categoryRows.sort(function(a, b) {
                var at = typeRank(
                    String(a.service_type || '').toUpperCase()
                );
                var bt = typeRank(
                    String(b.service_type || '').toUpperCase()
                );

                if (at !== bt) {
                    return at - bt;
                }

                return ipCompare(a.ip, b.ip);
            });

            var $badge = $(
                '#infrastructure-tabs a[aria-controls="' +
                servicePaneIds[name] + '"] .badge'
            );

            if ($badge.length) {
                $badge.text(categoryRows.length);
            }

            renderServiceTable(
                $('#' + servicePaneIds[name]),
                categoryRows
            );
        });
    }
    function renderServiceTable($pane, rows) {
        $pane.empty();

        if (!rows.length) {
            $('<div>')
                .addClass('alert alert-info')
                .text('No infrastructure services match the current filter.')
                .appendTo($pane);

            return;
        }

        var $panel = $('<div>')
            .addClass(
                'panel panel-default infrastructure-service-group'
            )
            .appendTo($pane);

        var $table = $('<table>')
            .addClass(
                'table table-condensed table-hover ' +
                'infrastructure-service-table'
            )
            .appendTo($panel);

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

        rows.forEach(function(row) {
            var endpoint =
                dash(row.port) +
                ' / ' +
                (row.protocol || '').toUpperCase();

            var $hostname = $('<td>');
            var friendly = row.custom_hostname || '';

            if (friendly) {
                var $friendly = $('<div>');
                $('<i>')
                    .addClass('fa fa-tag')
                    .attr('title', 'Friendly name')
                    .appendTo($friendly);
                $friendly.append(document.createTextNode(' ' + friendly));
                $friendly.appendTo($hostname);

                $('<small>')
                    .addClass('text-muted')
                    .css('display', 'block')
                    .text(dash(row.hostname))
                    .appendTo($hostname);
            } else {
                $('<div>')
                    .text(dash(row.hostname))
                    .appendTo($hostname);
            }

            if (row.vendor) {
                $('<small>')
                    .addClass('text-muted')
                    .css('display', 'block')
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

        if ($select.hasClass('selectpicker')) {
            $select.selectpicker('refresh');
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

                renderRecentServiceChanges(
                    data && Array.isArray(data.recent_changes)
                        ? data.recent_changes
                        : []
                );

                renderTabs();
                renderServices();
                updateInfrastructureStickyStack();
            },

            error: function() {
                $('#infrastructure-recent-changes')
                    .empty()
                    .append(
                        $('<div>')
                            .addClass('alert alert-danger')
                            .text(
                                'Unable to load recent service changes.'
                            )
                    );

                $('#infrastructure-tab-content')
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

    var portDiscoveryDevices = {};
    function loadPortDiscovery() {
        $.getJSON('/api/devicemonitor/devices/portdiscovery')
            .done(function(data) {
                var selected = $('#port-discovery-device').val();
                var $select = $('#port-discovery-device').empty();
                portDiscoveryDevices = {};
                (data.devices || []).slice().sort(function(a, b) {
                    return ipCompare(a.ip, b.ip) ||
                        String(a.mac).localeCompare(String(b.mac));
                }).forEach(function(device) {
                    portDiscoveryDevices[device.mac] = device;
                    $('<option>').val(device.mac)
                        .text((device.custom_hostname ||
                               device.hostname || device.ip) +
                              ' (' + device.ip + ', ' + device.mac + ')')
                        .appendTo($select);
                });
                if (selected && portDiscoveryDevices[selected]) {
                    $select.val(selected);
                }
                $select.trigger('change');
                var $body = $('#port-discovery-results').empty();
                (data.results || []).forEach(function(row) {
                    var detail = (row.ports || []).map(function(port) {
                        var name = [port.service, port.product,
                                    port.version].filter(Boolean).join(' ');
                        return port.port + '/' + port.protocol +
                            (name ? ' (' + name + ')' : ' (unknown)');
                    }).join(', ');
                    $('<tr>')
                        .append($('<td>').text(row.ip + ' (' + row.mac + ')'))
                        .append($('<td>').text(row.finished_at ||
                                                 row.started_at))
                        .append($('<td>').text(
                            row.success === null
                                ? 'Running'
                                : row.success == 1 ? 'Complete' :
                                  row.error || 'Failed'))
                        .append($('<td>').text(detail || '—'))
                        .appendTo($body);
                });
                if (data.error) {
                    $('#port-discovery-status').text(data.error);
                } else if (!data.devices || !data.devices.length) {
                    $('#port-discovery-status')
                        .text('No devices on the selected monitored interfaces.');
                } else {
                    $('#port-discovery-status').text('');
                }
            })
            .fail(function() {
                $('#port-discovery-status')
                    .text('Unable to load port discovery.');
            });
    }
    $('#port-discovery-device').on('change', function() {
        var device = portDiscoveryDevices[$(this).val()];
        $('#port-discovery-schedule')
            .prop('checked', !!(device && device.enabled))
            .prop('disabled', !device);
        $('#btn-port-discovery-run').prop('disabled', !device);
    });
    $('#btn-port-discovery-refresh').on('click', loadPortDiscovery);
    $('#port-discovery-schedule').on('change', function() {
        var mac = $('#port-discovery-device').val();
        var enabled = $(this).prop('checked') ? '1' : '0';
        if (!mac) return;
        $.post('/api/devicemonitor/devices/portdiscoverytarget',
               {mac: mac, enabled: enabled})
            .done(function(data) {
                $('#port-discovery-status')
                    .text(data.message || data.error || data.result);
                loadPortDiscovery();
            })
            .fail(function() {
                $('#port-discovery-status').text('Unable to save schedule.');
                loadPortDiscovery();
            });
    });
    $('#btn-port-discovery-run').on('click', function() {
        var mac = $('#port-discovery-device').val();
        if (!mac) return;
        var $button = $(this).prop('disabled', true);
        $('#port-discovery-status').text('Scanning selected device...');
        $.ajax({
            url: '/api/devicemonitor/devices/runportdiscovery',
            type: 'POST', data: {mac: mac}, timeout: 135000
        }).done(function(data) {
            $('#port-discovery-status')
                .text(data.message || data.error || data.result);
        }).fail(function() {
            $('#port-discovery-status').text('Port discovery request failed.');
        }).always(function() {
            $button.prop('disabled', false);
            loadPortDiscovery();
        });
    });

    var infrastructureStickyGeometry = null;

    function opaqueBackground($el) {
        var node = $el;
        var bg = node.css('background-color');

        while (
            node.length &&
            (!bg || bg === 'transparent' || bg === 'rgba(0, 0, 0, 0)')
        ) {
            node = node.parent();
            bg = node.css('background-color');
        }

        return bg || '#101218';
    }

    function applyInfrastructureTableHeaderSticky(headerTop) {
        var $active = $(
            '.infrastructure-tab-content .tab-pane.active'
        );
        var $table = $active.find('table').first();
        var thead = $table.find('thead th');

        if (!thead.length) {
            return;
        }

        var theadBg = opaqueBackground(thead);

        thead.css('top', headerTop + 'px');
        thead.css('background-color', theadBg);
        $table.find('thead').css('background-color', theadBg);
    }

    function updateInfrastructureStickyStack() {
        var pageHead = $('header.page-content-head');
        var $controls = $('#infrastructure-sticky-controls');

        if (
            infrastructureStickyGeometry === null &&
            pageHead.length &&
            $controls.length
        ) {
            var pageHeadRect = pageHead[0].getBoundingClientRect();
            var controlsRect = $controls[0].getBoundingClientRect();
            var scrollTop =
                (document.scrollingElement || document.documentElement)
                    .scrollTop;

            infrastructureStickyGeometry = {
                pageHeadTop: pageHeadRect.top + scrollTop,
                gap: controlsRect.top - pageHeadRect.bottom
            };
        }

        if (infrastructureStickyGeometry === null) {
            return;
        }

        var pageHeadTop = infrastructureStickyGeometry.pageHeadTop;
        var initialGap = infrastructureStickyGeometry.gap;
        var pageHeadHeight = pageHead.length
            ? pageHead[0].offsetHeight
            : 0;

        if (pageHead.length) {
            pageHead.css('top', pageHeadTop + 'px');
            pageHead.css('background-color', opaqueBackground(pageHead));
        }

        if ($controls.length) {
            var controlsTop = pageHeadTop + pageHeadHeight + initialGap;

            $controls.css('top', controlsTop + 'px');
            $controls.css('background-color', opaqueBackground($controls));

            $controls[0].style.setProperty(
                '--infrastructure-sticky-gap',
                initialGap + 'px'
            );

            var controlsHeight =
                $controls[0].getBoundingClientRect().height;

            applyInfrastructureTableHeaderSticky(
                controlsTop + controlsHeight
            );
        }
    }

    $(document).on('shown.bs.tab', 'a[data-toggle="tab"]', function() {
        var discovery = $(this).attr('href') ===
            '#tab-infrastructure-port-discovery';
        $('.infrastructure-toolbar, .infrastructure-stats')
            .toggle(!discovery);
        updateInfrastructureStickyStack();
    });

    $(window).on('resize', updateInfrastructureStickyStack);

    loadServices();
    loadPortDiscovery();
});
</script>
