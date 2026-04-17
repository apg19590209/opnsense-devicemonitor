<div id="devicemonitor_widget">
    <table class="table table-striped table-condensed">
        <tbody>
            <tr>
                <td style="color:#aaa;">Status</td>
                <td><span id="dm_widget_status" class="label label-default">...</span></td>
            </tr>
            <tr>
                <td style="color:#aaa;">Total</td>
                <td><strong id="dm_widget_total">—</strong></td>
            </tr>
            <tr>
                <td style="color:#aaa;">Online</td>
                <td><strong id="dm_widget_online" style="color:#4CAF50;">—</strong></td>
            </tr>
        </tbody>
    </table>
</div>

<script>
function update_devicemonitor_widget() {
    ajaxGet('/api/devicemonitor/service/status', {}, function(data, status) {
        if (status === 'success') {
            var isRunning = data.result === 'running';
            $('#dm_widget_status')
                .removeClass('label-default label-success label-danger')
                .addClass(isRunning ? 'label-success' : 'label-danger')
                .text(isRunning ? 'Running (PID: '+data.pid+')' : 'Stopped');
        }
    });
    ajaxGet('/api/devicemonitor/devices/stats', {}, function(data, status) {
        if (status === 'success') {
            $('#dm_widget_total').text(data.total || 0);
            $('#dm_widget_online').text(data.online || 0);
        }
    });
}

$(document).ready(function() {
    update_devicemonitor_widget();
    setInterval(update_devicemonitor_widget, 10000);
});
</script>