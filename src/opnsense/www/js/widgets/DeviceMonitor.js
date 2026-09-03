export default class DeviceMonitor extends BaseWidget {
    constructor(config) {
        super(config);
        this.tickTimeout = 15;
    }

    getMarkup() {
        let t = this.translations;
        // Unique ID so the widget framework always finds the correct DOM element
        return $(`
            <table id="dm-widget-table" class="table table-condensed" style="margin-bottom:0;">
                <tbody>
                    <tr>
                        <td>${t.status || 'Status'}</td>
                        <td id="dm-status"><span class="text-muted">...</span></td>
                    </tr>
                    <tr>
                        <td>${t.total || 'Total Devices'}</td>
                        <td><strong id="dm-total">-</strong></td>
                    </tr>
                    <tr>
                        <td>${t.online || 'Online'}</td>
                        <td><strong id="dm-online" style="color:#4CAF50;font-weight:bold;">-</strong></td>
                    </tr>
                </tbody>
            </table>
        `);
    }

    async onWidgetTick() {
        try {
            const stats = await this.ajaxCall('/api/devicemonitor/devices/stats');
            if (stats) {
                // Search directly in the document, not through this.$container
                $('#dm-total').text(stats.total ?? '-');
                $('#dm-online').text(stats.online ?? '-');
            }
        } catch(e) {
            console.error("Error loading stats:", e);
        }

        try {
            const status = await this.ajaxCall('/api/devicemonitor/service/status');
            if (status && status.result) {
                const ok    = status.result === 'running';
                const label = ok ? 'label-success' : 'label-danger';
                const text  = ok
                    ? (this.translations.running  || 'Running')
                    : (this.translations.stopped  || 'Stopped');
                $('#dm-status').html(`<span class="label ${label}">${text}</span>`);
            }
        } catch(e) {
            console.error("Error loading status:", e);
        }
    }
}