<div class="content-box">
    <div class="content-box-main">

        {% if portDiscoveryPage %}
        <div id="port-discovery-page"></div>
        {% else %}
        <div id="infrastructure-sticky-controls" class="infrastructure-sticky-controls">
            <div class="infrastructure-header">
                <div class="infrastructure-stats">
                    <span>
                        {{ devicemonitor_t('Total') }}:
                        <strong id="services-total">0</strong>
                    </span>
                    <span>
                        {{ devicemonitor_t('Recorded Available') }}:
                        <strong id="services-available">0</strong>
                    </span>
                    <span>
                        {{ devicemonitor_t('Recorded Unavailable') }}:
                        <strong id="services-unavailable">0</strong>
                    </span>
                    <span>
                        {{ devicemonitor_t('Recorded Unknown') }}:
                        <strong id="services-unknown">0</strong>
                    </span>
                </div>
                <div class="text-muted">
                    {{ devicemonitor_t('Counts describe stored observations, not current health.') }}
                </div>
            </div>

            <div class="infrastructure-toolbar">
                <button
                    id="btn-services-refresh"
                    type="button"
                    class="btn btn-primary btn-sm"
                >
                    <i class="fa fa-refresh"></i>
                    {{ devicemonitor_t('Refresh View') }}
                </button>
                <button
                    id="btn-services-discover"
                    type="button"
                    class="btn btn-success btn-sm"
                >
                    <i class="fa fa-search"></i>
                    {{ devicemonitor_t('Discover Now') }}
                </button>

                <select
                    id="services-type-filter"
                    class="selectpicker"
                    data-style="btn-default btn-sm"
                    data-width="180px"
                >
                    <option value="">
                        {{ devicemonitor_t('All Services') }}
                    </option>
                </select>

                <select
                    id="services-status-filter"
                    class="selectpicker"
                    data-style="btn-default btn-sm"
                    data-width="180px"
                >
                    <option value="">
                        {{ devicemonitor_t('All Recorded States') }}
                    </option>
                    <option value="available">
                        {{ devicemonitor_t('Available') }}
                    </option>
                    <option value="unavailable">
                        {{ devicemonitor_t('Unavailable') }}
                    </option>
                    <option value="unknown">
                        {{ devicemonitor_t('Unknown') }}
                    </option>
                </select>

                <input
                    id="services-search"
                    type="text"
                    class="form-control input-sm"
                    placeholder="{{ devicemonitor_t('Search services') }}"
                />

                <span class="text-muted">
                    {{ devicemonitor_t('Showing') }}
                    <strong id="services-visible">0</strong>
                </span>
                <span class="dm-show-archived-toggle">
                    <input id="services-show-archived" type="checkbox">
                    <label for="services-show-archived">
                        {{ devicemonitor_t('Show archived') }}
                    </label>
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
                        {{ devicemonitor_t('Recent Service Changes') }}
                    </a>
                </li>
            </ul>
        </div>
        {% endif %}

        <div id="infrastructure-tab-content" class="tab-content infrastructure-tab-content">
            {% if not portDiscoveryPage %}
            <div id="tab-infrastructure-recent-changes"
                 class="tab-pane fade in active"
                 role="tabpanel">
                <div class="panel panel-default infrastructure-recent-changes">
                    <div class="panel-heading">
                        <span class="text-muted">
                            {{ devicemonitor_t('Latest verified or authoritative service changes') }}
                        </span>
                    </div>
                    <div id="infrastructure-recent-changes">
                        <div class="text-muted">
                            {{ devicemonitor_t('Loading recent service changes') }}...
                        </div>
                    </div>
                </div>
            </div>
            {% else %}
            <div id="tab-infrastructure-port-discovery"
                 class="tab-pane active" role="tabpanel">
                <div class="panel panel-default infrastructure-recent-changes">
                    <div class="panel-heading">
                        {{ devicemonitor_t('Port Discovery') }}
                        <button type="button" class="dm-info" aria-label="{{ devicemonitor_t('About Port Discovery') }}"
                                data-content="{{ devicemonitor_t('Use Run Now on a device row to scan TCP ports 1–65535, including standard and nonstandard ports. Open ports and identified services appear on the Scans tab. Select multiple devices for optional weekly scans, then save. Scans run one host at a time and stop after 120 seconds; incomplete scans are marked failed. UDP ports, including WireGuard, are not scanned.') }}">
                            <i class="fa fa-info-circle" aria-hidden="true"></i>
                        </button>
                    </div>
                    <div class="panel-body">
                        <p class="text-muted">{{ devicemonitor_t('TCP only · 120-second limit per host') }}</p>
                        <ul class="nav nav-tabs port-discovery-tabs" role="tablist">
                            <li role="presentation" class="active">
                                <a href="#tab-port-discovery-devices"
                                   data-toggle="tab" role="tab">
                                    {{ devicemonitor_t('Devices') }}
                                </a>
                            </li>
                            <li role="presentation">
                                <a href="#tab-port-discovery-scans"
                                   data-toggle="tab" role="tab">
                                    {{ devicemonitor_t('Scans') }}
                                </a>
                            </li>
                        </ul>
                        <div class="tab-content port-discovery-tab-content">
                            <div id="tab-port-discovery-devices"
                               class="tab-pane fade in active" role="tabpanel">
                            <div class="port-discovery-controls">
                                <input id="port-discovery-search" type="search"
                                       class="form-control input-sm"
                                       placeholder="{{ devicemonitor_t('Search devices') }}">
                                <select id="port-discovery-filter"
                                        class="selectpicker"
                                        data-style="btn-default btn-sm"
                                        data-width="180px">
                                    <option value="all">{{ devicemonitor_t('All devices') }}</option>
                                    <option value="weekly">{{ devicemonitor_t('Weekly enabled') }}</option>
                                    <option value="never">{{ devicemonitor_t('Never scanned') }}</option>
                                </select>
                                <button type="button" id="btn-port-discovery-save"
                                        class="btn btn-primary btn-sm" disabled>
                                    {{ devicemonitor_t('Save weekly selections') }}
                                </button>
                                <span id="port-discovery-schedule-status"
                                      class="text-muted" role="status"
                                      aria-live="polite"></span>
                            </div>
                            <p id="port-discovery-status" class="text-muted"
                               role="status"></p>
                            <div class="table-responsive port-discovery-device-scroll">
                                <table id="port-discovery-device-table"
                                       class="table table-striped table-condensed">
                                    <thead><tr>
                                        <th>{{ devicemonitor_t('Device') }}</th>
                                        <th>{{ devicemonitor_t('Last Scan') }}</th>
                                        <th>{{ devicemonitor_t('Status') }}</th>
                                        <th>{{ devicemonitor_t('Scan weekly') }}</th>
                                        <th>{{ devicemonitor_t('Action') }}</th>
                                    </tr></thead>
                                    <tbody id="port-discovery-devices"></tbody>
                                </table>
                            </div>
                            </div>
                            <div id="tab-port-discovery-scans"
                               class="tab-pane fade" role="tabpanel">
                            <div class="port-discovery-controls port-discovery-scan-filters">
                                <input id="port-scans-search" type="search"
                                       class="form-control input-sm"
                                       placeholder="{{ devicemonitor_t('Search IP, MAC or name') }}">
                                <input id="port-scans-port" type="text"
                                       class="form-control input-sm"
                                       placeholder="{{ devicemonitor_t('TCP ports, e.g. 22,443') }}">
                                <select id="port-scans-result"
                                        class="selectpicker"
                                        data-style="btn-default btn-sm"
                                        data-width="160px">
                                    <option value="all">{{ devicemonitor_t('All results') }}</option>
                                    <option value="complete">{{ devicemonitor_t('Complete') }}</option>
                                    <option value="failed">{{ devicemonitor_t('Failed') }}</option>
                                    <option value="running">{{ devicemonitor_t('Running') }}</option>
                                </select>
                                <span class="text-muted">
                                    {{ devicemonitor_t('Filtering the 50 most recent scans') }}
                                </span>
                            </div>
                            <div class="table-responsive">
                                <table class="table table-striped table-condensed">
                                    <thead><tr>
                                        <th>{{ devicemonitor_t('Device') }}</th>
                                        <th>{{ devicemonitor_t('Scan Time') }}</th>
                                        <th>{{ devicemonitor_t('Result') }}</th>
                                        <th>{{ devicemonitor_t('Open TCP Ports') }}</th>
                                    </tr></thead>
                                    <tbody id="port-discovery-results"></tbody>
                                </table>
                            </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}
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

.infrastructure-toolbar .dm-show-archived-toggle {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    max-width: 100%;
    margin: 0;
}

.infrastructure-toolbar .dm-show-archived-toggle > input[type="checkbox"] {
    position: static;
    float: none;
    flex: 0 0 auto;
    width: auto;
    min-width: 0;
    margin: 0;
}

.infrastructure-toolbar .dm-show-archived-toggle > label {
    min-width: 0;
    margin: 0;
    font-weight: normal;
    white-space: normal;
    overflow-wrap: break-word;
    cursor: pointer;
}

.port-discovery-controls {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
}

.port-discovery-tab-content {
    padding-top: 12px;
}

.port-discovery-controls .checkbox-inline {
    margin: 0;
}

.port-discovery-controls input[type="search"] {
    width: 230px;
}

.port-discovery-device-scroll {
    max-height: 65vh;
    overflow-y: auto;
}

#port-discovery-device-table {
    width: 100%;
    min-width: 850px;
    table-layout: fixed;
}

#port-discovery-device-table th:nth-child(1) { width: 38%; }
#port-discovery-device-table th:nth-child(2) { width: 24%; }
#port-discovery-device-table th:nth-child(3) { width: 17%; }
#port-discovery-device-table th:nth-child(4) { width: 9%; }
#port-discovery-device-table th:nth-child(5) { width: 12%; }

#port-discovery-device-table td {
    overflow-wrap: anywhere;
    vertical-align: middle;
}

.port-discovery-scan-filters {
    margin-bottom: 12px;
}

#port-scans-port {
    width: 190px;
}

.port-discovery-device-scroll thead th {
    position: sticky;
    top: 0;
    z-index: 2;
    background-color: #fff;
}

.port-discovery-row-status {
    white-space: normal;
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

.infrastructure-service-table th:nth-child(1),
.infrastructure-service-table td:nth-child(1) {
    width: 23%;
}

.infrastructure-service-table th:nth-child(2),
.infrastructure-service-table td:nth-child(2) {
    width: 11%;
    padding-right: 14px;
    border-right: 1px solid #e2e6ea;
}

.infrastructure-service-table th:nth-child(3),
.infrastructure-service-table td:nth-child(3) {
    width: 17%;
    padding-left: 14px;
}

.infrastructure-service-table th:nth-child(4),
.infrastructure-service-table td:nth-child(4) {
    width: 23%;
}

.infrastructure-service-table th:nth-child(5),
.infrastructure-service-table td:nth-child(5) {
    width: 17%;
}

.infrastructure-service-table th:nth-child(6),
.infrastructure-service-table td:nth-child(6) {
    width: 9%;
    text-align: center;
}

.infrastructure-service-table th,
.infrastructure-service-table td {
    overflow-wrap: break-word;
    word-break: normal;
}

.infrastructure-service-table td,
.infrastructure-service-table th {
    vertical-align: top !important;
}

.dm-service-code,
.dm-service-mac {
    font-family: monospace;
    overflow-wrap: normal;
    word-break: normal;
    white-space: nowrap;
}

.dm-service-sub {
    display: block;
    margin-top: 3px;
    color: #666;
}

.dm-service-times {
    display: flex;
    flex-direction: column;
    gap: 8px;
    min-width: 0;
    font-variant-numeric: tabular-nums;
}

.dm-service-time-entry {
    min-width: 0;
}

.dm-service-time-entry dt {
    margin: 0;
    font-weight: 600;
}

.dm-service-time-entry dd {
    margin: 2px 0 0;
    font-family: monospace;
    line-height: 1.35;
    overflow-wrap: normal;
    word-break: normal;
    white-space: normal;
}

.dm-service-timezone-note {
    margin: 0 0 10px;
    color: #666;
}

.dm-timezone-unknown {
    display: inline-block;
    max-width: 100%;
    margin-top: 4px;
    color: #4f5d6b;
    background: #f4f6f8;
    border: 1px solid #cbd2d8;
    white-space: normal;
}

.dm-service-attribution {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
}

.dm-recorded-state {
    color: #4f5d6b;
    background: #fff;
    border: 1px solid #aeb9c4;
}

.dm-service-details-row > td {
    padding: 0 !important;
    background: #f7f9fb;
}

.dm-service-details {
    padding: 14px 18px;
    border-top: 1px solid #d9e1e8;
}

.dm-service-details-grid {
    display: grid;
    grid-template-columns: minmax(180px, 0.8fr) minmax(260px, 1.5fr);
    gap: 18px;
}

.dm-service-details h4 {
    margin: 0 0 6px 0;
    font-size: inherit;
    font-weight: 600;
}

.dm-service-match-list {
    padding-left: 18px;
    margin: 0;
}

.dm-service-match-list li + li {
    margin-top: 5px;
}

.dm-service-note {
    margin: 10px 0 0 0;
    color: #666;
}

.dm-service-cell-label {
    display: none;
}

@media (max-width: 991px) {
    .infrastructure-service-table,
    .infrastructure-service-table tbody,
    .infrastructure-service-table tr,
    .infrastructure-service-table td {
        display: block;
        width: 100% !important;
    }

    .infrastructure-service-table thead {
        display: none;
    }

    .dm-service-row {
        padding: 10px 12px;
        border-top: 1px solid #ddd;
    }

    .dm-service-row > td {
        padding: 6px 0 !important;
        border: 0 !important;
    }

    .dm-service-row > td + td {
        border-top: 1px solid #edf0f2 !important;
    }

    .dm-service-row > td:nth-child(2) {
        padding-right: 0 !important;
        border-right: 0 !important;
    }

    .dm-service-row > td:nth-child(3) {
        padding-left: 0 !important;
    }

    .dm-service-row .btn-xs {
        min-height: 32px;
        padding: 6px 10px;
    }

    .dm-service-cell-label {
        display: block;
        margin-bottom: 3px;
        font-weight: 600;
    }

    .dm-service-details-row > td {
        padding: 0 !important;
    }

    .dm-service-details-grid {
        grid-template-columns: 1fr;
    }
}

/* Tabbed Infrastructure Services layout. */
.infrastructure-tabs {
    padding: 0 4px;
    margin-bottom: 0;
    border-bottom: 0;
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
    padding: 0 4px;
}

.infrastructure-tab-content > .tab-pane > .panel {
    border-top: 0;
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

@media (max-width: 991px), (max-height: 640px) {
    .infrastructure-sticky-controls {
        position: static;
    }

    .infrastructure-sticky-controls::before {
        display: none;
    }

    .infrastructure-tab-content thead th {
        position: static !important;
    }
}

@media (max-width: 1100px) {
    #infrastructure-recent-changes {
        overflow: auto;
        max-height: min(65vh, 620px);
    }

    .infrastructure-recent-table {
        min-width: 1050px;
    }

    .infrastructure-recent-table thead th {
        position: sticky;
        top: 0 !important;
        z-index: 3;
        background: #fff;
    }
}
.dm-info { border:0; background:transparent; color:#337ab7; padding:0 3px; cursor:pointer; }
</style>

<script>
$(document).ready(function() {
    $('.dm-info').popover({container:'body', placement:'auto bottom', trigger:'focus'});
    $('.dm-info').on('keydown', function(event) {
        if (event.key === 'Escape') { $(this).popover('hide').trigger('blur'); }
    });
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
    function recordedStatusLabel(status) {
        if (status === 'available') {
            return {{ lang.query('Available')|json_encode(15) }};
        }

        if (status === 'unavailable') {
            return {{ lang.query('Unavailable')|json_encode(15) }};
        }

        if (status === 'unknown') {
            return {{ lang.query('Unknown')|json_encode(15) }};
        }

        return {{ lang.query('Recorded state not available')|json_encode(15) }};
    }

    function statusBadge(status) {
        return $('<span>')
            .addClass('label label-default dm-recorded-state')
            .text(recordedStatusLabel(status));
    }

    function serviceEvidenceKind(row) {
        var kind = String(row.evidence_kind || '').toLowerCase();
        var confidence = String(row.confidence || '').toLowerCase();
        var method = String(row.detection_method || '').toLowerCase();

        if (
            kind === 'authoritative' ||
            confidence === 'authoritative' ||
            method.indexOf('authoritative') !== -1
        ) {
            return 'authoritative';
        }

        if (kind === 'probe' || confidence === 'verified') {
            return 'probe';
        }

        if (
            kind === 'discovery' ||
            confidence === 'discovered' ||
            method === 'nmap_service'
        ) {
            return 'discovery';
        }

        return 'unknown';
    }

    function evidenceLabel(row) {
        var kind = serviceEvidenceKind(row);

        if (kind === 'authoritative') {
            return {{ lang.query('Authoritative/configuration record')|json_encode(15) }};
        }

        if (kind === 'probe') {
            return {{ lang.query('Reachability probe')|json_encode(15) }};
        }

        if (kind === 'discovery') {
            return {{ lang.query('Discovery evidence')|json_encode(15) }};
        }

        return {{ lang.query('Evidence source not classified')|json_encode(15) }};
    }

    function confidenceText(row) {
        var confidence = String(row.confidence || '').trim();
        var label = {{ lang.query('Recorded evidence confidence')|json_encode(15) }};

        if (!confidence) {
            return label + ': ' +
                {{ lang.query('Not recorded')|json_encode(15) }};
        }

        if (confidence.toLowerCase() === 'authoritative') {
            confidence = {{ lang.query('Authoritative')|json_encode(15) }};
        } else if (confidence.toLowerCase() === 'verified') {
            confidence = {{ lang.query('Verified')|json_encode(15) }};
        } else if (confidence.toLowerCase() === 'discovered') {
            confidence = {{ lang.query('Discovered')|json_encode(15) }};
        }

        return label + ': ' + confidence;
    }

    function productText(row) {
        var parts = [];

        if (row.product) {
            parts.push(row.product);
        }

        if (row.version) {
            parts.push(row.version);
        }

        return parts.length
            ? parts.join(' ')
            : {{ lang.query('Not recorded')|json_encode(15) }};
    }

    function locationText(row) {
        var location = String(row.interface || '').trim();

        return location
            ? location
            : {{ lang.query('Interface not recorded')|json_encode(15) }};
    }

    function endpointText(row) {
        var ip = String(row.ip || '').trim();
        var port = String(row.port || '').trim();
        var protocol = String(row.protocol || '').trim().toUpperCase();

        if (!ip) {
            return {{ lang.query('Endpoint not recorded')|json_encode(15) }};
        }

        if (port && protocol) {
            return ip + ':' + port + '/' + protocol;
        }

        if (port) {
            return ip + ':' + port;
        }

        return ip;
    }

    function serviceTypeText(row) {
        var type = String(row.service_type || '').trim().toUpperCase();
        return type || {{ lang.query('Service type not recorded')|json_encode(15) }};
    }

    function observationTimestampText(row, field) {
        return row[field + '_display'] || row[field];
    }

    function observationTimestampIsUnknown(row, field) {
        return !!String(row[field] || '').trim() &&
            String(row[field + '_timestamp_domain'] || 'unknown') !== 'utc';
    }

    function observationValues(row) {
        var kind = serviceEvidenceKind(row);

        if (kind === 'probe') {
            return [
                [
                    {{ lang.query('Last successful probe')|json_encode(15) }},
                    dash(observationTimestampText(row, 'last_verified')),
                    observationTimestampIsUnknown(row, 'last_verified')
                ],
                [
                    {{ lang.query('Last probe attempt')|json_encode(15) }},
                    dash(observationTimestampText(row, 'last_checked')),
                    observationTimestampIsUnknown(row, 'last_checked')
                ]
            ];
        }

        return [
            [
                {{ lang.query('Evidence recorded')|json_encode(15) }},
                dash(observationTimestampText(row, 'last_verified')),
                observationTimestampIsUnknown(row, 'last_verified')
            ],
            [
                {{ lang.query('Evidence refreshed')|json_encode(15) }},
                dash(observationTimestampText(row, 'last_checked')),
                observationTimestampIsUnknown(row, 'last_checked')
            ]
        ];
    }

    function inventoryCollection(row, key) {
        var matches = row && row.inventory_matches;
        return matches && Array.isArray(matches[key]) ? matches[key] : [];
    }

    function inventoryCountText(row) {
        var byMac = inventoryCollection(row, 'by_mac').length;
        var byIp = inventoryCollection(row, 'by_ip').length;

        if (!byMac && !byIp) {
            return {{ lang.query('No stored inventory matches')|json_encode(15) }};
        }

        var parts = [];
        if (byIp) {
            parts.push(
                byIp + ' ' +
                {{ lang.query('matching endpoint IP')|json_encode(15) }}
            );
        }
        if (byMac) {
            parts.push(
                byMac + ' ' +
                {{ lang.query('matching stored MAC')|json_encode(15) }}
            );
        }

        return parts.join('; ');
    }

    function inventoryMatchText(match, source) {
        var parts = [];
        var mac = String(match.mac || '').trim();
        var ip = String(match.ip || '').trim();
        var name = String(
            match.custom_hostname || match.hostname || ''
        ).trim();
        var interfaceLabel = String(
            match.monitored_interface_label || match.vlan || ''
        ).trim();

        if (source === 'mac') {
            parts.push(
                {{ lang.query('Matching stored MAC')|json_encode(15) }} + ':'
            );
        } else {
            parts.push(
                {{ lang.query('Matching endpoint IP')|json_encode(15) }} + ':'
            );
        }

        if (mac) {
            parts.push(mac);
        }
        if (ip) {
            parts.push('@ ' + ip);
        }
        if (interfaceLabel) {
            parts.push(
                {{ lang.query('Monitored interface label')|json_encode(15) }} +
                ': ' + interfaceLabel
            );
        }
        if (name) {
            parts.push(name);
        }

        return parts.join(' ');
    }

    function serviceChangeLabel(row) {
        var type = String(row.event_type || '');

        if (type === 'SERVICE_DISCOVERED') {
            return {{ lang.query('New verified service')|json_encode(15) }};
        }

        if (type === 'SERVICE_UNAVAILABLE') {
            return {{ lang.query('Service unavailable')|json_encode(15) }};
        }

        if (type === 'SERVICE_AVAILABLE') {
            return {{ lang.query('Service recovered')|json_encode(15) }};
        }

        if (type === 'SERVICE_CHANGED') {
            return {{ lang.query('Service changed')|json_encode(15) }};
        }

        return type || {{ lang.query('Not recorded')|json_encode(15) }};
    }

    function serviceChangeDetail(row) {
        var oldValue = String(row.old_value || '');
        var newValue = String(row.new_value || '');

        if (oldValue && newValue && oldValue !== newValue) {
            return oldValue + ' \u2192 ' + newValue;
        }

        return '';
    }

    function storedEventTimeText(row) {
        return row.occurred_at_display ||
            row.occurred_at_stored ||
            row.occurred_at;
    }

    function timezoneUnknownLabel() {
        return {{ lang.query('Timezone unknown')|json_encode(15) }};
    }

    function timezoneTableText(rows) {
        var text =
            {{ lang.query('Unknown timezone values remain exactly as stored because UTC provenance is unavailable.')|json_encode(15) }};
        var zone = '';

        (Array.isArray(rows) ? rows : []).some(function(row) {
            zone = String(
                row.timestamp_timezone || row.timezone || ''
            ).trim();
            return zone !== '';
        });

        if (zone) {
            text += ' ' +
                {{ lang.query('Displayed in')|json_encode(15) }} +
                ' ' + zone + '.';
        }

        return text;
    }

    function timezoneTableNote(rows) {
        return $('<p>')
            .addClass('dm-service-timezone-note')
            .text(timezoneTableText(rows));
    }

    function timezoneUnknownBadge() {
        return $('<span>')
            .addClass('label label-default dm-timezone-unknown')
            .text(timezoneUnknownLabel());
    }

    function recentStoredMacText(row) {
        return String(row.mac || '').trim() ||
            {{ lang.query('No stored MAC attribution')|json_encode(15) }};
    }

    function recentEndpointText(row) {
        var endpoint = String(row.ip || '');

        if (row.port) {
            endpoint += ':' + row.port;
        }

        if (row.protocol) {
            endpoint += '/' + String(row.protocol).toUpperCase();
        }

        if (row.interface) {
            endpoint += ' \u00b7 ' + row.interface;
        }

        return endpoint ||
            {{ lang.query('Endpoint not recorded')|json_encode(15) }};
    }

    function recentInventoryText(row) {
        return inventoryCountText(row);
    }

    function renderRecentServiceChanges(rows) {
        var $root = $('#infrastructure-recent-changes').empty();
        var changes = Array.isArray(rows) ? rows : [];

        if (!changes.length) {
            $('<div>')
                .addClass('text-muted')
                .css('padding', '10px')
                .text({{ lang.query('No verified infrastructure service changes recorded yet.')|json_encode(15) }})
                .appendTo($root);
            return;
        }

        timezoneTableNote(changes).appendTo($root);

        var $table = $('<table>')
            .addClass(
                'table table-condensed table-hover infrastructure-recent-table'
            )
            .attr(
                'aria-label',
                {{ lang.query('Recent service changes')|json_encode(15) }}
            );

        $('<thead>')
            .append(
                $('<tr>').append(
                    $('<th>')
                        .attr('scope', 'col')
                        .text({{ lang.query('Event Time')|json_encode(15) }}),
                    $('<th>')
                        .attr('scope', 'col')
                        .text({{ lang.query('Change')|json_encode(15) }}),
                    $('<th>')
                        .attr('scope', 'col')
                        .text({{ lang.query('Service')|json_encode(15) }}),
                    $('<th>')
                        .attr('scope', 'col')
                        .text({{ lang.query('Stored MAC attribution')|json_encode(15) }}),
                    $('<th>')
                        .attr('scope', 'col')
                        .text({{ lang.query('Endpoint')|json_encode(15) }}),
                    $('<th>')
                        .attr('scope', 'col')
                        .text({{ lang.query('Stored inventory matches at page load')|json_encode(15) }}),
                    $('<th>')
                        .attr('scope', 'col')
                        .text({{ lang.query('History')|json_encode(15) }})
                )
            )
            .appendTo($table);

        var $body = $('<tbody>');

        changes.forEach(function(row) {
            var $change = $('<td>');
            var $time = $('<td>');
            var detail = serviceChangeDetail(row);

            $('<div>')
                .text(dash(storedEventTimeText(row)))
                .appendTo($time);
            if (String(row.timestamp_domain || 'unknown') !== 'utc') {
                timezoneUnknownBadge().appendTo($time);
            }

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
                    .attr(
                        'title',
                        {{ lang.query('Open device activity')|json_encode(15) }}
                    )
                    .attr(
                        'aria-label',
                        {{ lang.query('Open device activity')|json_encode(15) }}
                    )
                    .append(
                        $('<i>').addClass('fa fa-history')
                    )
                    .appendTo($history);
            } else {
                $history.text(
                    {{ lang.query('Not recorded')|json_encode(15) }}
                );
            }

            $('<tr>')
                .append(
                    $time,
                    $change,
                    $('<td>').text(
                        groupTitle(
                            String(row.service_type || 'OTHER').toUpperCase()
                        )
                    ),
                    $('<td>').text(recentStoredMacText(row)),
                    $('<td>').text(recentEndpointText(row)),
                    $('<td>').text(recentInventoryText(row)),
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
            row.status,
            row.detection_method,
            row.confidence,
            row.product,
            row.version,
            row.port,
            row.protocol,
            inventoryCollection(row, 'by_mac').map(function(match) {
                return [
                    match.mac,
                    match.ip,
                    match.hostname,
                    match.custom_hostname,
                    match.vendor,
                    match.vlan
                ].join(' ');
            }).join(' '),
            inventoryCollection(row, 'by_ip').map(function(match) {
                return [
                    match.mac,
                    match.ip,
                    match.hostname,
                    match.custom_hostname,
                    match.vendor,
                    match.vlan
                ].join(' ');
            }).join(' ')
        ].join(' ').toLowerCase();
    }

    function normalizeServices(rows) {
        return (rows || []).map(function(row) {
            var normalized = $.extend({}, row);
            normalized.service_type =
                (row.service_type || '').toUpperCase();
            return normalized;
        });
    }

    function serviceArchiveRequest(row) {
        return {
            id: row.id,
            archive: row.archived ? '0' : '1'
        };
    }

    function filteredRows() {
        var type = $('#services-type-filter').val();
        var status = $('#services-status-filter').val();
        var search = ($('#services-search').val() || '')
            .toLowerCase()
            .trim();

        return allServices.filter(function(row) {
            if (row.archived && !$('#services-show-archived').prop('checked')) {
                return false;
            }
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

        allServices.filter(function(row) {
            return !row.archived ||
                $('#services-show-archived').prop('checked');
        }).forEach(function(row) {
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
    function appendLabeledCell($row, label, $content) {
        var $cell = $('<td>').append(
            $('<span>')
                .addClass('dm-service-cell-label')
                .text(label)
        );

        $content.appendTo($cell);
        $cell.appendTo($row);
        return $cell;
    }

    function serviceDetailsId(row) {
        return 'infrastructure-service-details-' + String(row.id);
    }

    function buildServiceDetails(row) {
        var $details = $('<div>')
            .addClass('dm-service-details')
            .attr('id', serviceDetailsId(row));
        var $grid = $('<div>')
            .addClass('dm-service-details-grid')
            .appendTo($details);

        var $attribution = $('<section>').appendTo($grid);
        $('<h4>')
            .text({{ lang.query('Stored MAC attribution')|json_encode(15) }})
            .appendTo($attribution);
        $('<div>')
            .addClass('dm-service-mac')
            .text(
                String(row.mac || '').trim() ||
                {{ lang.query('No stored MAC attribution')|json_encode(15) }}
            )
            .appendTo($attribution);
        $('<p>')
            .addClass('dm-service-note')
            .text(
                {{ lang.query('Used for alert correlation; not proof of endpoint ownership.')|json_encode(15) }}
            )
            .appendTo($attribution);

        $('<h4>')
            .text({{ lang.query('Product / Version')|json_encode(15) }})
            .appendTo($attribution);
        $('<div>')
            .text(productText(row))
            .appendTo($attribution);

        var $matches = $('<section>').appendTo($grid);
        $('<h4>')
            .text(
                {{ lang.query('Stored inventory matches at page load')|json_encode(15) }}
            )
            .appendTo($matches);

        var $list = $('<ul>')
            .addClass('dm-service-match-list')
            .appendTo($matches);
        var byMac = inventoryCollection(row, 'by_mac');
        var byIp = inventoryCollection(row, 'by_ip');

        byMac.forEach(function(match) {
            $('<li>')
                .text(inventoryMatchText(match, 'mac'))
                .appendTo($list);
        });
        byIp.forEach(function(match) {
            $('<li>')
                .text(inventoryMatchText(match, 'ip'))
                .appendTo($list);
        });

        if (!byMac.length && !byIp.length) {
            $('<li>')
                .text(
                    {{ lang.query('No stored inventory matches')|json_encode(15) }}
                )
                .appendTo($list);
        }

        $('<p>')
            .addClass('dm-service-note')
            .text(
                {{ lang.query('These matches come from stored device inventory. They do not identify which device answered the service probe. They are page-load lookups, not historical ownership evidence.')|json_encode(15) }}
            )
            .appendTo($matches);

        return $details;
    }

    function renderServiceTable($pane, rows) {
        $pane.empty();

        if (!rows.length) {
            $('<div>')
                .addClass('alert alert-info')
                .text({{ lang.query('No infrastructure services match the current filter.')|json_encode(15) }})
                .appendTo($pane);

            return;
        }

        timezoneTableNote(rows).appendTo($pane);

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
            .attr(
                'aria-label',
                {{ lang.query('Infrastructure services')|json_encode(15) }}
            )
            .appendTo($panel);

        $('<thead>')
            .append(
                $('<tr>').append(
                    $('<th>')
                        .attr('scope', 'col')
                        .text({{ lang.query('Endpoint')|json_encode(15) }}),
                    $('<th>')
                        .attr('scope', 'col')
                        .text({{ lang.query('Recorded State')|json_encode(15) }}),
                    $('<th>')
                        .attr('scope', 'col')
                        .text({{ lang.query('Evidence')|json_encode(15) }}),
                    $('<th>')
                        .attr('scope', 'col')
                        .text({{ lang.query('Observation times')|json_encode(15) }}),
                    $('<th>')
                        .attr('scope', 'col')
                        .text({{ lang.query('Stored MAC / Inventory')|json_encode(15) }}),
                    $('<th>')
                        .attr('scope', 'col')
                        .text({{ lang.query('Action')|json_encode(15) }})
                )
            )
            .appendTo($table);

        var $body = $('<tbody>');

        rows.forEach(function(row) {
            var detailsId = serviceDetailsId(row);
            var $row = $('<tr>')
                .addClass('dm-service-row')
                .attr('data-service-id', row.id)
                .appendTo($body);

            var $endpoint = $('<div>');
            $('<strong>')
                .text(serviceTypeText(row))
                .appendTo($endpoint);
            $('<div>')
                .addClass('dm-service-code dm-service-sub')
                .text(endpointText(row))
                .appendTo($endpoint);
            $('<div>')
                .addClass('dm-service-sub')
                .text(
                    {{ lang.query('Interface')|json_encode(15) }} +
                    ': ' + locationText(row)
                )
                .appendTo($endpoint);
            appendLabeledCell(
                $row,
                {{ lang.query('Endpoint')|json_encode(15) }},
                $endpoint
            );

            var $status = $('<div>').append(statusBadge(row.status));
            appendLabeledCell(
                $row,
                {{ lang.query('Recorded State')|json_encode(15) }},
                $status
            );

            var $evidence = $('<div>');
            $('<div>').text(evidenceLabel(row)).appendTo($evidence);
            $('<div>')
                .addClass('dm-service-sub')
                .text(confidenceText(row))
                .appendTo($evidence);
            appendLabeledCell(
                $row,
                {{ lang.query('Evidence')|json_encode(15) }},
                $evidence
            );

            var $times = $('<dl>').addClass('dm-service-times');
            observationValues(row).forEach(function(entry) {
                var $entry = $('<div>')
                    .addClass('dm-service-time-entry');
                $('<dt>').text(entry[0]).appendTo($entry);
                var $value = $('<dd>').text(entry[1]);

                if (entry[2]) {
                    timezoneUnknownBadge()
                        .appendTo($value);
                }

                $value.appendTo($entry);
                $entry.appendTo($times);
            });
            appendLabeledCell(
                $row,
                {{ lang.query('Observation times')|json_encode(15) }},
                $times
            );

            var $attribution = $('<div>')
                .addClass('dm-service-attribution');
            $('<div>')
                .addClass('dm-service-mac')
                .text(
                    String(row.mac || '').trim() ||
                    {{ lang.query('No stored MAC attribution')|json_encode(15) }}
                )
                .appendTo($attribution);
            $('<div>')
                .addClass('dm-service-sub')
                .text(inventoryCountText(row))
                .appendTo($attribution);
            $('<button type="button">')
                .addClass('btn btn-default btn-xs')
                .attr('aria-expanded', 'false')
                .attr('aria-controls', detailsId)
                .attr(
                    'aria-label',
                    {{ lang.query('Details')|json_encode(15) }} + ': ' +
                    serviceTypeText(row) + ' ' + endpointText(row)
                )
                .text({{ lang.query('Details')|json_encode(15) }})
                .appendTo($attribution);
            appendLabeledCell(
                $row,
                {{ lang.query('Stored MAC / Inventory')|json_encode(15) }},
                $attribution
            );

            var actionLabel = row.archived
                ? {{ lang.query('Restore')|json_encode(15) }}
                : {{ lang.query('Archive')|json_encode(15) }};
            var $action = $('<button type="button">')
                .addClass('btn btn-default btn-xs')
                .text(actionLabel)
                .attr(
                    'aria-label',
                    actionLabel + ': ' +
                    serviceTypeText(row) + ' ' + endpointText(row)
                )
                .on('click', function() {
                    var $button = $(this).prop('disabled', true);
                    $.post(
                        '/api/devicemonitor/devices/archiveservice',
                        serviceArchiveRequest(row)
                    ).done(function(data) {
                        if (data && data.result === 'ok') {
                            loadServices();
                        } else {
                            alert(data && data.error ||
                                  {{ lang.query('Unable to save service.')|json_encode(15) }});
                            $button.prop('disabled', false);
                        }
                    }).fail(function() {
                        alert({{ lang.query('Unable to save service.')|json_encode(15) }});
                        $button.prop('disabled', false);
                    });
                });
            appendLabeledCell(
                $row,
                {{ lang.query('Action')|json_encode(15) }},
                $action
            );

            var $details = buildServiceDetails(row);
            var $detailsRow = $('<tr>')
                .addClass('dm-service-details-row')
                .attr('data-service-details-for', row.id)
                .hide()
                .append($('<td>').attr('colspan', '6').append($details))
                .appendTo($body);

            $attribution.find('button').on('click', function() {
                var $button = $(this);
                var expanded = $button.attr('aria-expanded') === 'true';
                $button.attr('aria-expanded', expanded ? 'false' : 'true');
                $button.text(
                    expanded
                        ? {{ lang.query('Details')|json_encode(15) }}
                        : {{ lang.query('Hide details')|json_encode(15) }}
                );
                $button.attr(
                    'aria-label',
                    (expanded
                        ? {{ lang.query('Details')|json_encode(15) }}
                        : {{ lang.query('Hide details')|json_encode(15) }}) +
                        ': ' + serviceTypeText(row) + ' ' + endpointText(row)
                );
                $detailsRow.toggle(!expanded);
            });
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
                allServices = normalizeServices(
                    data && Array.isArray(data.rows)
                        ? data.rows
                        : []
                );

                var available = 0;
                var unavailable = 0;
                var unknown = 0;

                allServices.forEach(function(row) {
                    if (row.archived) return;
                    var status = row.status;

                    if (status === 'available') {
                        available++;
                    } else if (status === 'unavailable') {
                        unavailable++;
                    } else if (status === 'unknown') {
                        unknown++;
                    }
                });

                $('#services-total').text(allServices.filter(function(row) {
                    return !row.archived;
                }).length);
                $('#services-available').text(available);
                $('#services-unavailable').text(unavailable);
                $('#services-unknown').text(unknown);

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
                                {{ lang.query('Unable to load recent service changes.')|json_encode(15) }}
                            )
                    );

                $('#infrastructure-tab-content')
                    .append(
                        $('<div>')
                            .addClass('alert alert-danger')
                            .text(
                                {{ lang.query('Unable to load infrastructure services.')|json_encode(15) }}
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
                            : {{ lang.query('Infrastructure discovery failed.')|json_encode(15) }}
                    );
                    return;
                }

                loadServices();
            },

            error: function() {
                alert({{ lang.query('Infrastructure discovery failed.')|json_encode(15) }});
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

    $('#services-show-archived').on('change', function() {
        renderTabs();
        renderServices();
    });

    $('#services-search').on('input', renderServices);

    var portDiscoveryDevices = {};
    var portDiscoveryPending = {};
    var portDiscoveryBusy = false;
    var portDiscoveryLastScan = {};
    var portDiscoveryResults = [];
    var portDiscoveryRunningMac = null;
    var portDiscoveryScanStatus = {};
    var portDiscoveryStatusTimers = {};
    var portDiscoveryScheduleTimer = null;

    function setPortDiscoveryRowStatus(mac, message, temporary) {
        clearTimeout(portDiscoveryStatusTimers[mac]);
        portDiscoveryScanStatus[mac] = message;
        renderPortDiscoveryDevices();
        if (temporary) {
            portDiscoveryStatusTimers[mac] = setTimeout(function() {
                delete portDiscoveryScanStatus[mac];
                delete portDiscoveryStatusTimers[mac];
                renderPortDiscoveryDevices();
            }, 20000);
        }
    }

    function setPortDiscoveryScheduleStatus(message, temporary) {
        clearTimeout(portDiscoveryScheduleTimer);
        $('#port-discovery-schedule-status').text(message);
        if (temporary) {
            portDiscoveryScheduleTimer = setTimeout(function() {
                $('#port-discovery-schedule-status').text('');
                portDiscoveryScheduleTimer = null;
            }, 20000);
        }
    }

    // Port discovery timestamps are stored as UTC without a suffix. Render
    // them in the browser's local timezone and show its abbreviation.
    function portDiscoveryLocalTime(value) {
        if (!value) return '—';
        var date = new Date(String(value).trim().replace(' ', 'T') + 'Z');
        if (isNaN(date.getTime())) return value;
        var pad = function(n) { return ('0' + n).slice(-2); };
        var zone = new Intl.DateTimeFormat(undefined, {
            timeZoneName: 'short'
        }).formatToParts(date).filter(function(part) {
            return part.type === 'timeZoneName';
        }).map(function(part) { return part.value; })[0] || '';
        return date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' +
            pad(date.getDate()) + ' ' + pad(date.getHours()) + ':' +
            pad(date.getMinutes()) + ':' + pad(date.getSeconds()) +
            (zone ? ' ' + zone : '');
    }

    function renderPortDiscoveryDevices() {
        var search = ($('#port-discovery-search').val() || '')
            .toLowerCase().trim();
        var filter = $('#port-discovery-filter').val();
        var $body = $('#port-discovery-devices').empty();
        var changed = 0;
        Object.keys(portDiscoveryDevices).sort(function(a, b) {
            return ipCompare(portDiscoveryDevices[a].ip,
                             portDiscoveryDevices[b].ip) ||
                a.localeCompare(b);
        }).forEach(function(mac) {
            var device = portDiscoveryDevices[mac];
            var enabled = Object.prototype.hasOwnProperty.call(
                portDiscoveryPending, mac)
                ? portDiscoveryPending[mac] : !!device.enabled;
            var last = portDiscoveryLastScan[mac];
            if (enabled !== !!device.enabled) changed++;
            var name = device.custom_hostname || device.hostname ||
                device.ip;
            var label = name === device.ip
                ? device.ip + ' (' + mac + ')'
                : name + ' (' + device.ip + ', ' + mac + ')';
            if ((search && label.toLowerCase().indexOf(search) === -1) ||
                (filter === 'weekly' && !enabled) ||
                (filter === 'never' && last)) return;
            var $check = $('<input type="checkbox">')
                .prop('checked', enabled)
                .prop('disabled', portDiscoveryBusy)
                .attr('aria-label', 'Scan weekly: ' + label)
                .on('change', function() {
                    portDiscoveryPending[mac] = this.checked;
                    setPortDiscoveryScheduleStatus('', false);
                    renderPortDiscoveryDevices();
                });
            var $button = $('<button type="button">')
                .addClass('btn btn-primary btn-sm')
                .text({{ lang.query('Run Now')|json_encode(15) }})
                .prop('disabled', portDiscoveryBusy ||
                                  !!portDiscoveryRunningMac)
                .on('click', function() {
                    runPortDiscovery(mac);
                });
            var lastStatus = last
                ? (last.success === null ? 'Running' :
                   last.success == 1 ? 'Complete' :
                   last.error || 'Failed')
                : {{ lang.query('Not scanned')|json_encode(15) }};
            var $status = $('<td>')
                .addClass('port-discovery-row-status')
                .attr('role', 'status')
                .attr('aria-live', 'polite')
                .text(portDiscoveryScanStatus[mac] || lastStatus);
            $('<tr>')
                .append($('<td>').text(label))
                .append($('<td>').text(last
                    ? portDiscoveryLocalTime(last.finished_at ||
                                              last.started_at)
                    : '—'))
                .append($status)
                .append($('<td>').append($check))
                .append($('<td>').append($button))
                .appendTo($body);
        });
        $('#btn-port-discovery-save')
            .prop('disabled', portDiscoveryBusy || !changed)
            .text('Save weekly selections' + (changed ? ' (' + changed + ')' : ''));
    }

    function renderPortDiscoveryResults() {
        var search = ($('#port-scans-search').val() || '')
            .toLowerCase().trim();
        var portText = ($('#port-scans-port').val() || '').trim();
        var ports = portText.split(',').map(function(value) {
            return Number(value.trim());
        });
        var validPorts = !portText ||
            (/^\d{1,5}(\s*,\s*\d{1,5})*$/.test(portText) &&
             ports.every(function(value) {
                 return value >= 1 && value <= 65535;
             }));
        var result = $('#port-scans-result').val();
        var $body = $('#port-discovery-results').empty();
        portDiscoveryResults.filter(function(row) {
            var device = portDiscoveryDevices[row.mac] || {};
            if (search && [row.ip, row.mac, device.hostname,
                           device.custom_hostname].join(' ')
                .toLowerCase().indexOf(search) === -1) return false;
            if (!validPorts) return false;
            if (portText && !(row.ports || []).some(function(item) {
                return ports.indexOf(Number(item.port)) !== -1;
            })) return false;
            if (result === 'complete' && row.success != 1) return false;
            if (result === 'failed' && row.success != 0) return false;
            if (result === 'running' && row.success !== null) return false;
            return true;
        }).forEach(function(row) {
            var detail = (row.ports || []).map(function(item) {
                var name = [item.service, item.product,
                            item.version].filter(Boolean).join(' ');
                return item.port + '/' + item.protocol +
                    (name ? ' (' + name + ')' : ' (unknown)');
            }).join(', ');
            $('<tr>')
                .append($('<td>').text(row.ip + ' (' + row.mac + ')'))
                .append($('<td>').text(portDiscoveryLocalTime(
                    row.finished_at || row.started_at)))
                .append($('<td>').text(row.success === null
                    ? 'Running' : row.success == 1
                      ? 'Complete' : row.error || 'Failed'))
                .append($('<td>').text(detail || '—'))
                .appendTo($body);
        });
        if (!$body.children().length) {
            $('<tr>').append($('<td colspan="4">')
                .addClass('text-muted')
                .text({{ lang.query('No scans match the current filters.')|json_encode(15) }}))
                .appendTo($body);
        }
    }

    function loadPortDiscovery(scheduleMessage) {
        $.getJSON('/api/devicemonitor/devices/portdiscovery')
            .done(function(data) {
                portDiscoveryDevices = {};
                (data.devices || []).forEach(function(device) {
                    portDiscoveryDevices[device.mac] = device;
                });
                portDiscoveryLastScan = data.last_results || {};
                renderPortDiscoveryDevices();
                if (scheduleMessage) {
                    setPortDiscoveryScheduleStatus(scheduleMessage, true);
                }
                portDiscoveryResults = data.results || [];
                renderPortDiscoveryResults();
                if (data.error) {
                    $('#port-discovery-status').text(data.error);
                } else if (!data.devices || !data.devices.length) {
                    $('#port-discovery-status')
                        .text({{ lang.query('No devices on the selected monitored interfaces.')|json_encode(15) }});
                } else {
                    $('#port-discovery-status').text('');
                }
            })
            .fail(function() {
                $('#port-discovery-status')
                    .text({{ lang.query('Unable to load port discovery.')|json_encode(15) }});
            });
    }
    $('#port-discovery-search').on('input', renderPortDiscoveryDevices);
    $('#port-discovery-filter').on('change', renderPortDiscoveryDevices);
    $('#port-scans-search, #port-scans-port')
        .on('input', renderPortDiscoveryResults);
    $('#port-scans-result').on('change', renderPortDiscoveryResults);
    $('#btn-port-discovery-save').on('click', function() {
        var changes = Object.keys(portDiscoveryPending).filter(function(mac) {
            return portDiscoveryDevices[mac] &&
                portDiscoveryPending[mac] !==
                    !!portDiscoveryDevices[mac].enabled;
        });
        var saved = 0;
        portDiscoveryBusy = true;
        renderPortDiscoveryDevices();
        function next() {
            if (!changes.length) {
                portDiscoveryBusy = false;
                loadPortDiscovery(saved + ' weekly selection(s) saved.');
                return;
            }
            var mac = changes.shift();
            $.post('/api/devicemonitor/devices/portdiscoverytarget', {
                mac: mac,
                enabled: portDiscoveryPending[mac] ? '1' : '0'
            }).done(function(data) {
                if (!data || data.result !== 'ok') {
                    failed(data && data.error);
                    return;
                }
                portDiscoveryDevices[mac].enabled =
                    portDiscoveryPending[mac] ? 1 : 0;
                delete portDiscoveryPending[mac];
                saved++;
                next();
            }).fail(function() { failed(); });
        }
        function failed(reason) {
            portDiscoveryBusy = false;
            renderPortDiscoveryDevices();
            setPortDiscoveryScheduleStatus(
                saved + ' saved; remaining selections were not saved. ' +
                (reason || 'Unable to save schedule.'), false);
        }
        next();
    });
    function runPortDiscovery(mac) {
        if (portDiscoveryBusy || portDiscoveryRunningMac) return;
        portDiscoveryRunningMac = mac;
        setPortDiscoveryRowStatus(mac, 'Scanning…', false);
        $.ajax({
            url: '/api/devicemonitor/devices/runportdiscovery',
            type: 'POST', data: {mac: mac}, timeout: 135000
        }).done(function(data) {
            setPortDiscoveryRowStatus(mac, data && data.result === 'ok'
                ? {{ lang.query('Scan complete')|json_encode(15) }}
                : (data && data.error || {{ lang.query('Scan failed')|json_encode(15) }}), true);
        }).fail(function() {
            setPortDiscoveryRowStatus(mac, {{ lang.query('Scan request failed')|json_encode(15) }}, true);
        }).always(function() {
            portDiscoveryRunningMac = null;
            renderPortDiscoveryDevices();
            loadPortDiscovery();
        });
    }

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
            '.infrastructure-tab-content > .tab-pane.active'
        );
        var $table = $active.find('table:visible').first();
        var thead = $table.find('thead th');

        if (!thead.length) {
            return;
        }

        var theadBg = opaqueBackground(thead);

        thead.css('top', $table.is('#port-discovery-device-table')
            ? '0px' : headerTop + 'px');
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
        updateInfrastructureStickyStack();
    });

    $(window).on('resize', updateInfrastructureStickyStack);

    if ($('#port-discovery-page').length) {
        loadPortDiscovery();
    } else {
        loadServices();
    }
});
</script>
