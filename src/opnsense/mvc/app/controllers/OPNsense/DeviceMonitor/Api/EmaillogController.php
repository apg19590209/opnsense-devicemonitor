<?php

namespace OPNsense\DeviceMonitor\Api;

use OPNsense\Base\ApiControllerBase;
use OPNsense\Core\Backend;

/**
 * Read-only access to the local Device Monitor email log.
 *
 * Local only. The response names this node explicitly so the UI never implies a
 * combined cluster view: peer aggregation is not implemented, and the UI must
 * not present empty Peer/All views as working.
 */
/* The OPNsense router derives the filename from ucwords() of the URI segment:
 * /api/devicemonitor/emaillog/... resolves to EmaillogController. The file and
 * class names therefore follow that convention exactly. */
class EmaillogController extends ApiControllerBase
{
    private function recorder()
    {
        require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php');
        require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/PluginTimestamps.php');
        return \OPNsense\DeviceMonitor\EmailLog::instance();
    }

    /**
     * Visibility selector shared by every read path. Anything other than the two
     * explicit values falls back to the active log, so a mistyped request can
     * never widen or hide more than the default view.
     */
    private function visibilityFilter()
    {
        $value = (string)$this->request->getPost('visibility', 'string', 'active');
        return in_array($value, ['active', 'deleted', 'all'], true) ? $value : 'active';
    }

    /**
     * Write gate for delete/restore. The framework base class already enforces
     * authentication, the page ACL (api/devicemonitor/*) and the per-request token
     * check on POST. On top of that, a user carrying user-config-readonly is
     * refused, so a read-only account or read-only API key can never change a log
     * entry.
     */
    private function requireWriteAccess()
    {
        try {
            $this->throwReadOnly();
        } catch (\Throwable $e) {
            return false;
        }
        return true;
    }

    private function nodeFacts()
    {
        require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php');
        require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/PluginTimestamps.php');
        $node = \OPNsense\DeviceMonitor\EmailLog::currentNode();
        return [
            'node_id' => $node['host'],
            'node_ip' => $node['ip'],
            'role' => (string)@shell_exec("ifconfig 2>/dev/null | grep -oE 'carp: [A-Z]+' | head -1 | awk '{print $2}'") ?: 'unknown',
        ];
    }

    /** POST /api/devicemonitor/emaillog/search */
    public function searchAction()
    {
        if (!$this->request->isPost()) {
            return ['result' => 'failed', 'message' => 'POST required'];
        }
        $page = max(1, (int)$this->request->getPost('page', 'int', 1));
        $perPage = max(10, min(200, (int)$this->request->getPost('per_page', 'int', 50)));
        $filters = [
            'type' => (string)$this->request->getPost('type', 'string', ''),
            'status' => (string)$this->request->getPost('status', 'string', ''),
            'search' => (string)$this->request->getPost('search', 'string', ''),
            'visibility' => $this->visibilityFilter(),
        ];
        $log = $this->recorder();
        $rows = $log->query($filters, $perPage, ($page - 1) * $perPage);

        // Values are returned raw: the view inserts them with text() so they are
        // escaped exactly once at render time. Encoding here would double-escape.
        $fields = ['event_id', 'created_utc', 'updated_utc', 'node_id', 'node_ip', 'node_role',
            'notification_type', 'recipient', 'subject', 'status', 'status_detail', 'transport',
            'queue_id', 'message_id', 'deleted_utc'];
        $safe = [];
        foreach ($rows as $row) {
            $clean = [];
            foreach ($fields as $field) {
                $clean[$field] = (string)($row[$field] ?? '');
            }
            $clean['scope'] = 'local';
            $timeline = [];
            foreach (($row['timeline'] ?? []) as $step) {
                $timeline[] = [
                    'occurred_utc' => (string)($step['occurred_utc'] ?? ''),
                    'stage' => (string)($step['stage'] ?? ''),
                    'status' => (string)($step['status'] ?? ''),
                    'detail' => (string)($step['detail'] ?? ''),
                    'evidence' => (string)($step['evidence'] ?? ''),
                    'source' => (string)($step['source'] ?? ''),
                ];
            }
            /* Fallback rendering only: the browser converts the UTC value with its
             * own DST rules; this uses the configured zone if it cannot. */
            foreach ($timeline as $i => $step) {
                $timeline[$i]['occurred_local'] = \OPNsense\DeviceMonitor\PluginTimestamps::toConfiguredZone($step['occurred_utc']);
            }
            $clean['created_local'] = \OPNsense\DeviceMonitor\PluginTimestamps::toConfiguredZone($clean['created_utc']);
            $clean['deleted_local'] = \OPNsense\DeviceMonitor\PluginTimestamps::toConfiguredZone($clean['deleted_utc']);
            $clean['timezone'] = \OPNsense\DeviceMonitor\PluginTimestamps::configuredZoneName();
            $clean['timeline'] = $timeline;
            $safe[] = $clean;
        }

        return [
            'result' => 'ok',
            'scope' => 'local',
            'node' => $this->nodeFacts(),
            'page' => $page,
            'per_page' => $perPage,
            'rows' => $safe,
            'logging_diagnostic' => $log->lastDiagnostic() === null
                ? null
                : htmlspecialchars($log->lastDiagnostic(), ENT_QUOTES, 'UTF-8'),
            'peer_status' => [
                'available' => false,
                'reason' => 'Peer aggregation is not implemented; no secure peer access is configured.',
            ],
        ];
    }

    /**
     * POST /api/devicemonitor/emaillog/message
     *
     * One message with its body, for the detail view. The body is returned as
     * plain text; the client renders it as text and never as HTML. Rows created
     * before content capture report content_available=false so the UI can say
     * "Message content unavailable" instead of reconstructing anything.
     */
    public function messageAction()
    {
        if (!$this->request->isPost()) {
            return ['result' => 'failed', 'message' => 'POST required'];
        }
        $eventId = (string)$this->request->getPost('event_id', 'string', '');
        if ($eventId === '' || !preg_match('/^[0-9a-f]{32}$/', $eventId)) {
            return ['result' => 'failed', 'message' => 'Invalid message reference'];
        }
        $log = $this->recorder();
        $row = $log->messageDetail($eventId);
        if ($row === null) {
            return ['result' => 'failed', 'message' => 'Message not found in the retention window'];
        }
        $hasContent = !empty($row['content_text']);
        $timeline = [];
        foreach (($row['timeline'] ?? []) as $step) {
            $timeline[] = [
                'occurred_utc' => (string)($step['occurred_utc'] ?? ''),
                'stage' => (string)($step['stage'] ?? ''),
                'status' => (string)($step['status'] ?? ''),
                'detail' => (string)($step['detail'] ?? ''),
                'evidence' => (string)($step['evidence'] ?? ''),
                'source' => (string)($step['source'] ?? ''),
            ];
        }
        /* The framework HTML-escapes array responses unless they are marked safe,
         * which turned "&" into "&amp;" and "&amp;" into "&amp;amp;" inside the
         * JSON. The body is plain text and the client renders it with .text(), so
         * it must be delivered raw: exactly one escaping step, at render time. */
        $this->response->setContentType('application/json', 'UTF-8');
        $this->response->setContent([
            'result' => 'ok',
            'scope' => 'local',
            'message' => [
                'event_id' => (string)$row['event_id'],
                'created_utc' => (string)$row['created_utc'],
                'node_ip' => (string)$row['node_ip'],
                'node_role' => (string)$row['node_role'],
                'notification_type' => (string)$row['notification_type'],
                'recipient' => (string)$row['recipient'],
                'subject' => (string)$row['subject'],
                'status' => (string)$row['status'],
                'status_detail' => (string)$row['status_detail'],
                'queue_id' => (string)$row['queue_id'],
                'content_available' => $hasContent,
                'content_format' => $hasContent ? (string)($row['content_format'] ?? '') : '',
                'content_truncated' => $hasContent && !empty($row['content_truncated']),
                'content' => $hasContent ? (string)$row['content_text'] : '',
                'created_local' => \OPNsense\DeviceMonitor\PluginTimestamps::toConfiguredZone((string)$row['created_utc']),
                'deleted_local' => \OPNsense\DeviceMonitor\PluginTimestamps::toConfiguredZone((string)($row['deleted_utc'] ?? '')),
                'timezone' => \OPNsense\DeviceMonitor\PluginTimestamps::configuredZoneName(),
                'timeline' => $timeline,
            ],
        ], true);
        return;
    }

    /**
     * POST /api/devicemonitor/emaillog/peerpage
     *
     * Read-only page of this node's log, offered to an authenticated peer. It
     * returns the same bounded row shape as the local search, without bodies, so a
     * peer can aggregate without pulling content it does not need.
     */
    /** Peer settings from config.json, with secrets kept server-side. */
    private function peerSettings()
    {
        $model = new \OPNsense\DeviceMonitor\DeviceMonitor();
        $config = $model->getConfig();
        return [
            'enabled' => (string)($config['email_log_peer_enabled'] ?? '0') === '1',
            'url' => (string)($config['email_log_peer_url'] ?? ''),
            'api_key' => (string)($config['email_log_peer_api_key'] ?? ''),
            'api_secret' => (string)($config['email_log_peer_api_secret'] ?? ''),
            'ca_pem' => (string)($config['email_log_peer_ca_pem'] ?? ''),
            'timeout' => (int)($config['email_log_peer_timeout'] ?? 8),
        ];
    }

    /**
     * POST /api/devicemonitor/emaillog/combined
     *
     * Local rows plus, when securely configured, the peer's rows for the same
     * filters. Sorting and pagination apply to the combined set. A peer failure
     * yields partial=true with the reason; the local half is always returned.
     */
    public function combinedAction()
    {
        if (!$this->request->isPost()) {
            return ['result' => 'failed', 'message' => 'POST required'];
        }
        require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/EmailLogAggregate.php');
        require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/PeerClient.php');
        $page = max(1, (int)$this->request->getPost('page', 'int', 1));
        $perPage = max(10, min(200, (int)$this->request->getPost('per_page', 'int', 50)));
        $filters = [
            'type' => (string)$this->request->getPost('type', 'string', ''),
            'status' => (string)$this->request->getPost('status', 'string', ''),
            'search' => (string)$this->request->getPost('search', 'string', ''),
            'visibility' => $this->visibilityFilter(),
        ];
        $log = $this->recorder();
        $localRows = $log->query($filters, \OPNsense\DeviceMonitor\EmailLogAggregate::MAX_PAGE, 0);

        $localFacts = $this->nodeFacts();
        $localTag = \OPNsense\DeviceMonitor\EmailLogAggregate::nodeTag(
            ['host' => $localFacts['node_id'], 'ip' => $localFacts['node_ip'], 'role' => $localFacts['role']],
            'local'
        );

        $settings = $this->peerSettings();
        $peer = null;
        $peerTag = ['scope' => 'peer', 'node_id' => '', 'node_ip' => '', 'role' => ''];
        if ($settings['enabled']) {
            $errors = \OPNsense\DeviceMonitor\PeerClient::validate($settings);
            if (!empty($errors)) {
                $peer = ['available' => false, 'reason' => implode(' ', $errors)];
            } else {
                $client = new \OPNsense\DeviceMonitor\PeerClient($settings);
                $peer = $client->search($filters, \OPNsense\DeviceMonitor\EmailLogAggregate::MAX_PAGE, 0);
            }
        }

        foreach ($localRows as &$localRow) {
            $localRow['scope'] = 'local';
        }
        unset($localRow);
        $combined = \OPNsense\DeviceMonitor\EmailLogAggregate::combine(
            $localRows, $peer, $localTag, $peerTag, $perPage, ($page - 1) * $perPage
        );

        $this->response->setContentType('application/json', 'UTF-8');
        $this->response->setContent([
            'result' => 'ok',
            'page' => $page,
            'per_page' => $perPage,
            'rows' => $combined['rows'],
            'total' => $combined['total'],
            'partial' => $combined['partial'],
            'peer' => $combined['peer'],
            'peer_enabled' => $settings['enabled'],
            'local_node' => $localTag,
        ], true);
        return;
    }

    /** POST /api/devicemonitor/emaillog/peerpage
     *
     * Read-only page of this node's log, offered to an authenticated peer.
     */
    public function peerpageAction()
    {
        if (!$this->request->isPost()) {
            return ['result' => 'failed', 'message' => 'POST required'];
        }
        $page = max(1, (int)$this->request->getPost('page', 'int', 1));
        $perPage = max(10, min(200, (int)$this->request->getPost('per_page', 'int', 50)));
        $filters = [
            'type' => (string)$this->request->getPost('type', 'string', ''),
            'status' => (string)$this->request->getPost('status', 'string', ''),
            'search' => (string)$this->request->getPost('search', 'string', ''),
            'visibility' => $this->visibilityFilter(),
        ];
        $log = $this->recorder();
        $rows = $log->query($filters, $perPage, ($page - 1) * $perPage);
        $fields = ['event_id', 'created_utc', 'updated_utc', 'node_id', 'node_ip', 'node_role',
            'notification_type', 'recipient', 'subject', 'status', 'status_detail', 'queue_id',
            'deleted_utc', 'has_content'];
        $safe = [];
        foreach ($rows as $row) {
            $clean = [];
            foreach ($fields as $field) {
                $clean[$field] = $row[$field] ?? '';
            }
            $safe[] = $clean;
        }
        $this->response->setContentType('application/json', 'UTF-8');
        $this->response->setContent([
            'result' => 'ok',
            'node' => $this->nodeFacts(),
            'rows' => $safe,
            'scope' => 'local',
        ], true);
        return;
    }

    /** POST /api/devicemonitor/emaillog/peermessage */
    public function peermessageAction()
    {
        if (!$this->request->isPost()) {
            return ['result' => 'failed', 'message' => 'POST required'];
        }
        $eventId = (string)$this->request->getPost('event_id', 'string', '');
        if ($eventId === '' || !preg_match('/^[0-9a-f]{32}$/', $eventId)) {
            return ['result' => 'failed', 'message' => 'Invalid message reference'];
        }
        $log = $this->recorder();
        $row = $log->messageDetail($eventId);
        if ($row === null) {
            return ['result' => 'failed', 'message' => 'Message not found in the retention window'];
        }
        $hasContent = !empty($row['content_text']);
        $timeline = [];
        foreach (($row['timeline'] ?? []) as $step) {
            $timeline[] = [
                'occurred_utc' => (string)($step['occurred_utc'] ?? ''),
                'stage' => (string)($step['stage'] ?? ''),
                'status' => (string)($step['status'] ?? ''),
                'detail' => (string)($step['detail'] ?? ''),
                'source' => (string)($step['source'] ?? ''),
            ];
        }
        $this->response->setContentType('application/json', 'UTF-8');
        $this->response->setContent([
            'result' => 'ok',
            'scope' => 'local',
            'message' => [
                'event_id' => (string)$row['event_id'],
                'created_utc' => (string)$row['created_utc'],
                'node_id' => (string)$row['node_id'],
                'node_ip' => (string)$row['node_ip'],
                'node_role' => (string)$row['node_role'],
                'notification_type' => (string)$row['notification_type'],
                'recipient' => (string)$row['recipient'],
                'subject' => (string)$row['subject'],
                'status' => (string)$row['status'],
                'status_detail' => (string)$row['status_detail'],
                'content_available' => $hasContent,
                'content' => $hasContent ? (string)$row['content_text'] : '',
                'content_truncated' => $hasContent && !empty($row['content_truncated']),
                'created_local' => \OPNsense\DeviceMonitor\PluginTimestamps::toConfiguredZone((string)$row['created_utc']),
                'deleted_local' => \OPNsense\DeviceMonitor\PluginTimestamps::toConfiguredZone((string)($row['deleted_utc'] ?? '')),
                'timezone' => \OPNsense\DeviceMonitor\PluginTimestamps::configuredZoneName(),
                'timeline' => $timeline,
            ],
        ], true);
        return;
    }

    /** POST /api/devicemonitor/emaillog/peermessageview - fetch from the peer on demand. */
    public function peermessageviewAction()
    {
        if (!$this->request->isPost()) {
            return ['result' => 'failed', 'message' => 'POST required'];
        }
        require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/PeerClient.php');
        $settings = $this->peerSettings();
        if (!$settings['enabled']) {
            return ['result' => 'failed', 'message' => 'Peer is not enabled.'];
        }
        $errors = \OPNsense\DeviceMonitor\PeerClient::validate($settings);
        if (!empty($errors)) {
            return ['result' => 'failed', 'message' => implode(' ', $errors)];
        }
        $eventId = (string)$this->request->getPost('event_id', 'string', '');
        $client = new \OPNsense\DeviceMonitor\PeerClient($settings);
        $result = $client->message($eventId);
        if (!$result['available']) {
            return ['result' => 'failed', 'message' => $result['reason']];
        }
        $this->response->setContentType('application/json', 'UTF-8');
        $this->response->setContent([
            'result' => 'ok',
            'scope' => 'peer',
            'message' => $result['message'],
        ], true);
        return;
    }

    /**
     * POST /api/devicemonitor/emaillog/delete
     *
     * Soft deletion of one local entry: only the visibility marker is set; the
     * captured body, event id, transport status and timeline events are left in
     * place, and the 30-day retention policy is unchanged. Remote (peer) rows are
     * never mutated here: this node cannot write another node's database and no
     * secure cross-node mutation capability exists.
     */
    public function deleteAction()
    {
        return $this->setVisibilityAction(true);
    }

    /** POST /api/devicemonitor/emaillog/restore */
    public function restoreAction()
    {
        return $this->setVisibilityAction(false);
    }

    private function setVisibilityAction($deleted)
    {
        if (!$this->request->isPost()) {
            return ['result' => 'failed', 'message' => 'POST required'];
        }
        if (!$this->requireWriteAccess()) {
            $this->response->setStatusCode(403, 'Forbidden');
            return ['result' => 'forbidden', 'message' => 'Write access is required to change the email log.'];
        }
        $eventId = (string)$this->request->getPost('event_id', 'string', '');
        if ($eventId === '' || !preg_match('/^[0-9a-f]{32}$/', $eventId)) {
            return ['result' => 'failed', 'message' => 'Invalid message reference'];
        }
        $log = $this->recorder();
        $result = $deleted ? $log->markDeleted($eventId) : $log->restore($eventId);
        if ($result !== true) {
            return ['result' => 'failed', 'message' => $log->lastDiagnostic() ?: 'No change'];
        }
        return ['result' => 'ok', 'deleted' => (bool)$deleted, 'event_id' => $eventId];
    }

    /** POST /api/devicemonitor/emaillog/exportcsv */
    public function exportcsvAction()
    {
        if (!$this->request->isPost()) {
            return ['result' => 'failed', 'message' => 'POST required'];
        }
        $log = $this->recorder();
        /* Same filters and visibility as the list: Active exports the active log,
         * Deleted the deleted set and All both. */
        $rows = $log->exportRows([
            'type' => (string)$this->request->getPost('type', 'string', ''),
            'status' => (string)$this->request->getPost('status', 'string', ''),
            'search' => (string)$this->request->getPost('search', 'string', ''),
            'visibility' => $this->visibilityFilter(),
        ], 200);
        $header = ['created_utc', 'node_ip', 'node_role', 'notification_type', 'recipient', 'subject', 'status', 'status_detail', 'queue_id'];
        $lines = [implode(',', $header)];
        // Neutralise spreadsheet formula injection: a leading = + - @ (or tab/CR) is
        // prefixed with a single quote so the cell is treated as text.
        $csv = function ($v) {
            $value = (string)$v;
            if ($value !== '' && strpos("=+-@\t\r", $value[0]) !== false) {
                $value = "'" . $value;
            }
            return '"' . str_replace('"', '""', $value) . '"';
        };
        foreach ($rows as $row) {
            $lines[] = implode(',', [
                $csv($row['created_utc']), $csv($row['node_ip']), $csv($row['node_role']),
                $csv($row['notification_type']), $csv($row['recipient']), $csv($row['subject']),
                $csv($row['status']), $csv($row['status_detail']), $csv($row['queue_id']),
            ]);
        }
        return ['result' => 'ok', 'scope' => 'local', 'csv' => implode("\n", $lines)];
    }
}
