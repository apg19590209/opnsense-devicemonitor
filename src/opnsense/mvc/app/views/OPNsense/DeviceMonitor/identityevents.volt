<div class="content-box">
    <div class="content-box-main">

        <div style="padding:10px 10px 8px 10px;border-bottom:1px solid #333;margin-bottom:12px;">
            <h1 style="margin:0;font-size:20px;">
                {{ lang._('Device Monitor') }}
                <span style="color:#555;margin:0 8px;">&ndash;</span>
                <span style="font-weight:normal;">{{ lang._('Identity Events') }}</span>
            </h1>
        </div>

        <div class="panel panel-default">
            <div class="panel-heading identity-events-heading">
                <strong style="font-size:13px;">
                    <i class="fa fa-exclamation-triangle"></i>
                    {{ lang._('Identity Events') }}
                    <span id="identity-events-total"
                          class="badge"
                          style="margin-left:6px;">0</span>
                </strong>

                <div class="identity-events-controls">
                    <label for="identity-events-limit"
                           style="margin:0;font-size:12px;font-weight:600;">
                        {{ lang._('Rows') }}
                    </label>

                    <select id="identity-events-limit"
                            class="form-control input-sm">
                        <option value="10" selected>10</option>
                        <option value="25">25</option>
                        <option value="50">50</option>
                        <option value="100">100</option>
                    </select>

                    <button id="btn-identity-refresh"
                            class="btn btn-xs btn-default"
                            title="{{ lang._('Refresh identity events') }}">
                        <i class="fa fa-refresh"></i>
                    </button>
                </div>
            </div>

            <div id="identity-events-scroll"
                 class="table-responsive">
                <table class="table table-condensed table-hover table-striped"
                       id="grid-identity-events">
                    <thead>
                        <tr>
                            <th>{{ lang._('Detected') }}</th>
                            <th>{{ lang._('Severity') }}</th>
                            <th>{{ lang._('Event Type') }}</th>
                            <th>{{ lang._('MAC Address') }}</th>
                            <th>{{ lang._('IP Address') }}</th>
                            <th>{{ lang._('Other MAC') }}</th>
                            <th>{{ lang._('Other IP') }}</th>
                            <th>{{ lang._('Interface') }}</th>
                            <th class="text-center">{{ lang._('Details') }}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td colspan="9" class="text-muted">
                                {{ lang._('Loading identity events...') }}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

    </div>
</div>

<style>
.identity-events-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.identity-events-controls {
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
}

#identity-events-limit {
    width: 70px;
    height: 28px;
    padding: 0 24px 0 8px;
    margin: 0;
}

#btn-identity-refresh {
    height: 28px;
    min-width: 28px;
    padding: 0 8px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

#identity-events-scroll {
    max-height: 520px;
    overflow-y: auto;
}

#grid-identity-events {
    margin-bottom: 0;
}

#grid-identity-events thead th {
    font-size: 12px;
    font-weight: 600;
    vertical-align: middle;
    white-space: nowrap;
    position: sticky;
    top: 0;
    z-index: 2;
    background: inherit;
}

#grid-identity-events tbody td {
    vertical-align: middle;
}

.identity-event-details td {
    padding: 0 !important;
    background: rgba(127, 127, 127, 0.06);
}

.identity-event-detail-box {
    padding: 12px 16px 14px 16px;
}

.identity-event-detail-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 8px 18px;
    margin-bottom: 12px;
}

.identity-event-detail-label {
    display: block;
    font-size: 11px;
    font-weight: 600;
    opacity: 0.75;
    margin-bottom: 2px;
}

.identity-event-details-content {
    margin: 0;
    padding: 10px;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    max-height: 300px;
    overflow-y: auto;
}

.identity-event-details-button {
    min-width: 30px;
}

.identity-event-state-button {
    min-width: 30px;
    margin-left: 4px;
}

@media (max-width: 767px) {
    .identity-events-heading {
        align-items: flex-start;
        gap: 8px;
    }

    .identity-event-detail-grid {
        grid-template-columns: 1fr;
    }
}
</style>

<script>
$(document).ready(function() {

    var identityText = {
        noEvents: "{{ lang._('No identity events recorded') }}",
        loadError: "{{ lang._('Unable to load identity events') }}",
        showDetails: "{{ lang._('Show event details') }}",
        hideDetails: "{{ lang._('Hide event details') }}",
        otherInterface: "{{ lang._('Other interface') }}",
        resolvedAt: "{{ lang._('Resolved at') }}",
        details: "{{ lang._('Details') }}",
        resolve: "{{ lang._('Resolve event') }}",
        reopen: "{{ lang._('Reopen event') }}",
        updateFailed: "{{ lang._('Unable to update identity event') }}"
    };

    function dash(value) {
        return value === null ||
               value === undefined ||
               value === ''
            ? '\u2014'
            : value;
    }

    function severityLabel(value) {
        var severity = (value || '').toString().toLowerCase();
        var cssClass = 'label-default';

        if (severity === 'high' || severity === 'critical') {
            cssClass = 'label-danger';
        } else if (severity === 'medium') {
            cssClass = 'label-warning';
        } else if (severity === 'low') {
            cssClass = 'label-info';
        }

        return $('<span>')
            .addClass('label ' + cssClass)
            .text(dash(value));
    }

    function formatDetails(value) {
        if (value === null || value === undefined || value === '') {
            return '\u2014';
        }

        var text = String(value);

        try {
            return JSON.stringify(JSON.parse(text), null, 2);
        } catch (e) {
            return text;
        }
    }

    function detailItem(label, value) {
        return $('<div>').append(
            $('<span>')
                .addClass('identity-event-detail-label')
                .text(label),
            $('<span>')
                .text(dash(value))
        );
    }

    function buildDetailRow(row, detailId) {
        var $grid = $('<div>')
            .addClass('identity-event-detail-grid')
            .append(
                detailItem(
                    identityText.otherInterface,
                    row.other_interface
                ),
                detailItem(
                    identityText.resolvedAt,
                    row.resolved_at
                )
            );

        var $details = $('<pre>')
            .addClass('identity-event-details-content')
            .text(formatDetails(row.details));

        var $box = $('<div>')
            .addClass('identity-event-detail-box')
            .append(
                $grid,
                $('<span>')
                    .addClass('identity-event-detail-label')
                    .text(identityText.details),
                $details
            );

        return $('<tr>')
            .attr('id', detailId)
            .addClass('identity-event-details')
            .hide()
            .append(
                $('<td>')
                    .attr('colspan', 9)
                    .append($box)
            );
    }

    function setIdentityEventResolved(row, resolved, $button) {
        $button.prop('disabled', true);

        $.ajax({
            url: '/api/devicemonitor/devices/identityeventstatus',
            type: 'POST',
            data: {
                id: row.id,
                resolved: resolved ? 1 : 0
            },

            success: function(data) {
                if (data && data.result === 'saved') {
                    loadIdentityEvents();
                    return;
                }

                alert(identityText.updateFailed);
            },

            error: function() {
                alert(identityText.updateFailed);
            },

            complete: function() {
                $button.prop('disabled', false);
            }
        });
    }
    function renderIdentityEvents(rows) {
        var $tbody = $('#grid-identity-events tbody').empty();

        if (!rows.length) {
            $('<tr>')
                .append(
                    $('<td>')
                        .attr('colspan', 9)
                        .addClass('text-muted')
                        .text(identityText.noEvents)
                )
                .appendTo($tbody);

            return;
        }

        rows.forEach(function(row) {
            var detailId = 'identity-event-detail-' + row.id;

            var $button = $('<button>')
                .attr({
                    type: 'button',
                    title: identityText.showDetails,
                    'aria-expanded': 'false'
                })
                .addClass(
                    'btn btn-xs btn-default ' +
                    'identity-event-details-button'
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
                            ? identityText.showDetails
                            : identityText.hideDetails
                    )
                    .find('i')
                    .toggleClass('fa-chevron-down', visible)
                    .toggleClass('fa-chevron-up', !visible);
            });

            var isResolved =
                row.resolved_at !== null &&
                row.resolved_at !== undefined &&
                row.resolved_at !== '';

            var $stateButton = $('<button>')
                .attr({
                    type: 'button',
                    title: isResolved
                        ? identityText.reopen
                        : identityText.resolve
                })
                .addClass(
                    'btn btn-xs ' +
                    (isResolved ? 'btn-warning' : 'btn-success') +
                    ' identity-event-state-button'
                )
                .append(
                    $('<i>').addClass(
                        isResolved ? 'fa fa-undo' : 'fa fa-check'
                    )
                );

            $stateButton.on('click', function() {
                setIdentityEventResolved(
                    row,
                    !isResolved,
                    $(this)
                );
            });
            $('<tr>')
                .append(
                    $('<td>').text(dash(row.detected_at)),
                    $('<td>').append(severityLabel(row.severity)),
                    $('<td>').text(dash(row.event_type)),
                    $('<td>').text(dash(row.mac)),
                    $('<td>').text(dash(row.ip)),
                    $('<td>').text(dash(row.other_mac)),
                    $('<td>').text(dash(row.other_ip)),
                    $('<td>').text(dash(row.interface)),
                    $('<td>')
                        .addClass('text-center')
                        .append($button, $stateButton)
                )
                .appendTo($tbody);

            buildDetailRow(row, detailId)
                .appendTo($tbody);
        });
    }

    function showLoadError() {
        $('#identity-events-total').text('?');

        $('#grid-identity-events tbody')
            .empty()
            .append(
                $('<tr>').append(
                    $('<td>')
                        .attr('colspan', 9)
                        .addClass('text-danger')
                        .text(identityText.loadError)
                )
            );
    }

    function loadIdentityEvents() {
        var limit =
            parseInt(
                $('#identity-events-limit').val(),
                10
            ) || 10;

        $.ajax({
            url: '/api/devicemonitor/devices/identityevents',
            type: 'GET',
            data: {
                limit: limit
            },

            success: function(data) {
                $('#identity-events-total')
                    .text(
                        data &&
                        data.total !== undefined
                            ? data.total
                            : 0
                    );

                renderIdentityEvents(
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

    $('#btn-identity-refresh').on(
        'click',
        function() {
            loadIdentityEvents();
        }
    );

    $('#identity-events-limit').on(
        'change',
        function() {
            loadIdentityEvents();
        }
    );

    loadIdentityEvents();

    setInterval(
        function() {
            loadIdentityEvents();
        },
        30000
    );
});
</script>
