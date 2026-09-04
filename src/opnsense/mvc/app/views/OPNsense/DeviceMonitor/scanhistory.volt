<div class="content-box">
    <div class="content-box-main">

        <div style="padding:10px 10px 8px 10px;border-bottom:1px solid #333;margin-bottom:12px;">
            <h1 style="margin:0;font-size:20px;">
                {{ lang._('Device Monitor') }}
                <span style="color:#555;margin:0 8px;">&ndash;</span>
                <span style="font-weight:normal;">{{ lang._('Nmap Scan History') }}</span>
            </h1>
        </div>

        <div class="panel panel-default">
            <div class="panel-heading scan-history-heading">

                <strong style="font-size:13px;">
                    <i class="fa fa-history"></i>
                    {{ lang._('Nmap Scan History') }}
                    <span id="scan-history-total"
                          class="badge"
                          style="margin-left:6px;">0</span>
                </strong>

                <div class="scan-history-controls">
                    <label for="scan-history-limit"
                           style="margin:0;font-size:12px;font-weight:600;">
                        {{ lang._('Rows') }}
                    </label>

                    <select id="scan-history-limit"
                            class="form-control input-sm">
                        <option value="10" selected>10</option>
                        <option value="25">25</option>
                        <option value="50">50</option>
                        <option value="100">100</option>
                    </select>

                    <button id="btn-history-refresh"
                            class="btn btn-xs btn-default"
                            title="{{ lang._('Refresh scan history') }}">
                        <i class="fa fa-refresh"></i>
                    </button>
                </div>
            </div>

            <div id="scan-history-scroll"
                 class="table-responsive">
                <table class="table table-condensed table-hover table-striped"
                       id="grid-scan-history">
                    <thead>
                        <tr>
                            <th>{{ lang._('Started') }}</th>
                            <th>{{ lang._('MAC Address') }}</th>
                            <th>{{ lang._('IP Address') }}</th>
                            <th>{{ lang._('Type') }}</th>
                            <th>{{ lang._('Scan') }}</th>
                            <th>{{ lang._('Open Ports') }}</th>
                            <th>{{ lang._('Email') }}</th>
                            <th class="text-center">{{ lang._('Details') }}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td colspan="8" class="text-muted">
                                {{ lang._('Loading scan history...') }}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

    </div>
</div>

<style>
.scan-history-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.scan-history-controls {
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
}

#scan-history-limit {
    width: 70px;
    height: 28px;
    padding: 0 24px 0 8px;
    margin: 0;
}

#btn-history-refresh {
    height: 28px;
    min-width: 28px;
    padding: 0 8px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

#scan-history-scroll {
    max-height: 480px;
    overflow-y: auto;
}

#grid-scan-history {
    margin-bottom: 0;
}

#grid-scan-history thead th {
    font-size: 12px;
    font-weight: 600;
    vertical-align: middle;
    white-space: nowrap;
    position: sticky;
    top: 0;
    z-index: 2;
    background: inherit;
}

#grid-scan-history tbody td {
    vertical-align: middle;
}

.scan-history-port-summary {
    white-space: nowrap;
}

.scan-history-details td {
    padding: 0 !important;
    background: rgba(127, 127, 127, 0.06);
}

.scan-history-detail-box {
    padding: 12px 16px 14px 16px;
}

.scan-history-detail-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 8px 18px;
    margin-bottom: 12px;
}

.scan-history-detail-label {
    display: block;
    font-size: 11px;
    font-weight: 600;
    opacity: 0.75;
    margin-bottom: 2px;
}

.scan-history-detail-value {
    overflow-wrap: anywhere;
}

.scan-history-error {
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}

.scan-history-ports-table {
    margin-top: 8px;
    margin-bottom: 0;
}

.scan-history-ports-table th,
.scan-history-ports-table td {
    font-size: 12px;
}

.scan-history-details-button {
    min-width: 30px;
}

@media (max-width: 767px) {
    .scan-history-heading {
        align-items: flex-start;
        gap: 8px;
    }

    .scan-history-detail-grid {
        grid-template-columns: 1fr;
    }
}
</style>

<script>
$(document).ready(function() {

    function dash(value) {
        return value === null ||
               value === undefined ||
               value === ''
            ? '\u2014'
            : value;
    }

    function yesNo(value) {
        if (value === 1 || value === '1') {
            return 'Yes';
        }

        if (value === 0 || value === '0') {
            return 'No';
        }

        return '\u2014';
    }

    function scanStatus(row) {
        if (row.success === 1 || row.success === '1') {
            return $('<span>')
                .css({
                    'color': '#4CAF50',
                    'font-weight': 'bold',
                    'white-space': 'nowrap'
                })
                .append(
                    $('<i>').addClass('fa fa-check-circle'),
                    document.createTextNode(' ' + historyText.success)
                );
        }

        if (row.success === 0 || row.success === '0') {
            return $('<span>')
                .css({
                    'color': '#d9534f',
                    'font-weight': 'bold',
                    'white-space': 'nowrap'
                })
                .append(
                    $('<i>').addClass('fa fa-exclamation-circle'),
                    document.createTextNode(' ' + historyText.failed)
                );
        }

        return $('<span>')
            .css({
                'color': '#f0ad4e',
                'font-weight': 'bold',
                'white-space': 'nowrap'
            })
            .append(
                $('<i>').addClass('fa fa-minus-circle'),
                document.createTextNode(' ' + historyText.incomplete)
            );
    }

    var historyText = {
        emailSent: "{{ lang._('Email sent') }}",
        emailFailed: "{{ lang._('Email failed') }}",
        sent: "{{ lang._('Sent') }}",
        failed: "{{ lang._('Failed') }}",
        success: "{{ lang._('Success') }}",
        incomplete: "{{ lang._('Incomplete') }}",
        none: "{{ lang._('None') }}",
        manual: "{{ lang._('Manual') }}",
        automatic: "{{ lang._('Automatic') }}",
        port: "{{ lang._('Port') }}",
        protocol: "{{ lang._('Protocol') }}",
        service: "{{ lang._('Service') }}",
        product: "{{ lang._('Product') }}",
        version: "{{ lang._('Version') }}",
        extraInfo: "{{ lang._('Extra info') }}",
        noOpenPorts: "{{ lang._('No open ports recorded') }}",
        enabled: "{{ lang._('Enabled') }}",
        disabled: "{{ lang._('Disabled') }}",
        finished: "{{ lang._('Finished') }}",
        topPorts: "{{ lang._('Top ports') }}",
        timing: "{{ lang._('Timing') }}",
        hostTimeout: "{{ lang._('Host timeout') }}",
        versionDetection: "{{ lang._('Version detection') }}",
        nmapVersion: "{{ lang._('Nmap version') }}",
        nmapElapsed: "{{ lang._('Nmap elapsed') }}",
        osHint: "{{ lang._('OS hint') }}",
        openPorts: "{{ lang._('Open ports') }}",
        emailSentLabel: "{{ lang._('Email sent') }}",
        scanError: "{{ lang._('Scan error') }}",
        emailError: "{{ lang._('Email error') }}",
        openPortDetails: "{{ lang._('Open port details') }}",
        noHistory: "{{ lang._('No targeted Nmap scan history recorded') }}",
        showDetails: "{{ lang._('Show scan details') }}",
        hideDetails: "{{ lang._('Hide scan details') }}",

    };

    function emailStatus(row) {
        if (row.email_sent === 1 || row.email_sent === '1') {
            return $('<span>')
                .addClass('text-success')
                .attr('title', historyText.emailSent)
                .append(
                    $('<i>').addClass('fa fa-envelope'),
                    document.createTextNode(' ' + historyText.sent)
                );
        }

        if (row.email_sent === 0 || row.email_sent === '0') {
            return $('<span>')
                .addClass('text-danger')
                .attr('title', row.email_error || historyText.emailFailed)
                .append(
                    $('<i>').addClass('fa fa-exclamation-triangle'),
                    document.createTextNode(' ' + historyText.failed)
                );
        }

        return $('<span>')
            .addClass('text-muted')
            .text('\u2014');
    }

    function typeLabel(row) {
        if (row.scan_type === 'manual') {
            return $('<span>')
                .addClass('label label-info')
                .text(historyText.manual);
        }

        return $('<span>')
            .addClass('label label-default')
            .text(historyText.automatic);
    }

    function portSummary(row) {
        var ports = Array.isArray(row.ports) ? row.ports : [];

        if (ports.length) {
            var labels = ports.slice(0, 5).map(function(port) {
                var suffix = port.protocol
                    ? '/' + port.protocol
                    : '';

                return String(port.port) + suffix;
            });

            if (ports.length > 5) {
                labels.push('+' + (ports.length - 5));
            }

            return $('<span>')
                .addClass('scan-history-port-summary')
                .attr(
                    'title',
                    ports.map(function(port) {
                        return [
                            port.port,
                            port.protocol || '',
                            port.service || ''
                        ].filter(Boolean).join('/');
                    }).join(', ')
                )
                .text(labels.join(', '));
        }

        if (row.open_port_count === 0 ||
            row.open_port_count === '0') {
            return $('<span>')
                .addClass('text-muted')
                .text(historyText.none);
        }

        if (row.open_port_count !== null &&
            row.open_port_count !== undefined) {
            return $('<span>')
                .text(String(row.open_port_count));
        }

        return $('<span>')
            .addClass('text-muted')
            .text('\u2014');
    }

    function detailItem(label, value) {
        return $('<div>').append(
            $('<span>')
                .addClass('scan-history-detail-label')
                .text(label),
            $('<span>')
                .addClass('scan-history-detail-value')
                .text(dash(value))
        );
    }

    function buildPortsTable(ports) {
        var $table = $('<table>')
            .addClass(
                'table table-condensed table-bordered ' +
                'scan-history-ports-table'
            );

        var $head = $('<thead>').append(
            $('<tr>').append(
                $('<th>').text(historyText.port),
                $('<th>').text(historyText.protocol),
                $('<th>').text(historyText.service),
                $('<th>').text(historyText.product),
                $('<th>').text(historyText.version),
                $('<th>').text(historyText.extraInfo)
            )
        );

        var $body = $('<tbody>');

        if (!ports.length) {
            $body.append(
                $('<tr>').append(
                    $('<td>')
                        .attr('colspan', 6)
                        .addClass('text-muted')
                        .text(historyText.noOpenPorts)
                )
            );
        } else {
            ports.forEach(function(port) {
                $body.append(
                    $('<tr>').append(
                        $('<td>').text(dash(port.port)),
                        $('<td>').text(dash(port.protocol)),
                        $('<td>').text(dash(port.service)),
                        $('<td>').text(dash(port.product)),
                        $('<td>').text(dash(port.version)),
                        $('<td>').text(dash(port.extra_info))
                    )
                );
            });
        }

        return $table.append($head, $body);
    }

    function buildDetailRow(row, detailId) {
        var ports = Array.isArray(row.ports) ? row.ports : [];

        var versionDetection;

        if (row.version_detection === 1 ||
            row.version_detection === '1') {
            versionDetection = historyText.enabled;
        } else if (
            row.version_detection === 0 ||
            row.version_detection === '0'
        ) {
            versionDetection = historyText.disabled;
        } else {
            versionDetection = '\u2014';
        }

        var elapsed = row.nmap_elapsed !== null &&
                      row.nmap_elapsed !== undefined
            ? row.nmap_elapsed + ' s'
            : '\u2014';

        var $grid = $('<div>')
            .addClass('scan-history-detail-grid')
            .append(
                detailItem(historyText.finished, row.finished_at),
                detailItem(historyText.topPorts, row.top_ports),
                detailItem(
                    historyText.timing,
                    row.timing !== null &&
                    row.timing !== undefined
                        ? 'T' + row.timing
                        : null
                ),
                detailItem(
                    historyText.hostTimeout,
                    row.host_timeout !== null &&
                    row.host_timeout !== undefined
                        ? row.host_timeout + ' s'
                        : null
                ),
                detailItem(
                    historyText.versionDetection,
                    versionDetection
                ),
                detailItem(
                    historyText.nmapVersion,
                    row.nmap_version
                ),
                detailItem(
                    historyText.nmapElapsed,
                    elapsed
                ),
                detailItem(
                    historyText.osHint,
                    row.os_hint
                ),
                detailItem(
                    historyText.openPorts,
                    row.open_port_count
                ),
                detailItem(
                    historyText.emailSentLabel,
                    yesNo(row.email_sent)
                )
            );

        var $box = $('<div>')
            .addClass('scan-history-detail-box')
            .append($grid);

        if (row.error) {
            $box.append(
                $('<div>')
                    .css('margin-bottom', '10px')
                    .append(
                        $('<span>')
                            .addClass('scan-history-detail-label')
                            .text(historyText.scanError),
                        $('<div>')
                            .addClass(
                                'scan-history-error text-danger'
                            )
                            .text(row.error)
                    )
            );
        }

        if (row.email_error) {
            $box.append(
                $('<div>')
                    .css('margin-bottom', '10px')
                    .append(
                        $('<span>')
                            .addClass('scan-history-detail-label')
                            .text(historyText.emailError),
                        $('<div>')
                            .addClass(
                                'scan-history-error text-danger'
                            )
                            .text(row.email_error)
                    )
            );
        }

        $box.append(
            $('<span>')
                .addClass('scan-history-detail-label')
                .text(historyText.openPortDetails),
            buildPortsTable(ports)
        );

        return $('<tr>')
            .attr('id', detailId)
            .addClass('scan-history-details')
            .hide()
            .append(
                $('<td>')
                    .attr('colspan', 8)
                    .append($box)
            );
    }

    function renderScanHistory(rows) {
        var $tbody = $('#grid-scan-history tbody').empty();

        if (!rows.length) {
            $('<tr>').append(
                $('<td>')
                    .attr('colspan', 8)
                    .addClass('text-muted')
                    .text(historyText.noHistory)
            ).appendTo($tbody);

            return;
        }

        rows.forEach(function(row) {
            var detailId = 'scan-history-detail-' + row.id;

            var $button = $('<button>')
                .attr({
                    'type': 'button',
                    'title': historyText.showDetails,
                    'aria-expanded': 'false'
                })
                .addClass(
                    'btn btn-xs btn-default ' +
                    'scan-history-details-button'
                )
                .append(
                    $('<i>').addClass('fa fa-chevron-down')
                );

            $button.on('click', function() {
                var $detail = $('#' + detailId);
                var visible = $detail.is(':visible');

                $detail.toggle(!visible);

                $(this)
                    .attr(
                        'aria-expanded',
                        visible ? 'false' : 'true'
                    )
                    .attr(
                        'title',
                        visible
                            ? historyText.showDetails
                            : historyText.hideDetails
                    )
                    .find('i')
                    .toggleClass(
                        'fa-chevron-down',
                        visible
                    )
                    .toggleClass(
                        'fa-chevron-up',
                        !visible
                    );
            });

            $('<tr>')
                .append(
                    $('<td>').text(dash(row.started_at)),
                    $('<td>').text(dash(row.mac)),
                    $('<td>').text(dash(row.ip)),
                    $('<td>').append(typeLabel(row)),
                    $('<td>').append(scanStatus(row)),
                    $('<td>').append(portSummary(row)),
                    $('<td>').append(emailStatus(row)),
                    $('<td>')
                        .addClass('text-center')
                        .append($button)
                )
                .appendTo($tbody);

            buildDetailRow(row, detailId)
                .appendTo($tbody);
        });
    }

    function showLoadError() {
        $('#scan-history-total').text('?');

        $('#grid-scan-history tbody')
            .empty()
            .append(
                $('<tr>').append(
                    $('<td>')
                        .attr('colspan', 8)
                        .addClass('text-danger')
                        .text(
                            'Unable to load Nmap scan history'
                        )
                )
            );
    }

    function loadScanHistory() {
        var limit =
            parseInt(
                $('#scan-history-limit').val(),
                10
            ) || 10;

        $.ajax({
            url: '/api/devicemonitor/devices/scanhistory',
            type: 'GET',
            data: {
                limit: limit
            },

            success: function(data) {
                if (data && data.error) {
                    showLoadError();
                    return;
                }

                $('#scan-history-total')
                    .text(
                        data &&
                        data.total !== undefined
                            ? data.total
                            : 0
                    );

                renderScanHistory(
                    data && Array.isArray(data.rows)
                        ? data.rows
                        : []
                );
            },

            error: function() {
                showLoadError();
            }
        });
    }

    $('#btn-history-refresh').on(
        'click',
        function() {
            loadScanHistory();
        }
    );

    $('#scan-history-limit').on(
        'change',
        function() {
            loadScanHistory();
        }
    );

    loadScanHistory();

    setInterval(
        function() {
            loadScanHistory();
        },
        30000
    );
});
</script>
