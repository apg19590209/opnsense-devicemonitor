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
class EmailLogController extends ApiControllerBase
{
    private function recorder()
    {
        require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php');
        return \OPNsense\DeviceMonitor\EmailLog::instance();
    }

    private function nodeFacts()
    {
        require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php');
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
        ];
        $log = $this->recorder();
        $rows = $log->query($filters, $perPage, ($page - 1) * $perPage);

        // Values are returned raw: the view inserts them with text() so they are
        // escaped exactly once at render time. Encoding here would double-escape.
        $fields = ['event_id', 'created_utc', 'updated_utc', 'node_id', 'node_ip', 'node_role',
            'notification_type', 'recipient', 'subject', 'status', 'status_detail', 'transport',
            'queue_id', 'message_id'];
        $safe = [];
        foreach ($rows as $row) {
            $clean = [];
            foreach ($fields as $field) {
                $clean[$field] = (string)($row[$field] ?? '');
            }
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

    /** POST /api/devicemonitor/emaillog/exportcsv */
    public function exportcsvAction()
    {
        if (!$this->request->isPost()) {
            return ['result' => 'failed', 'message' => 'POST required'];
        }
        $log = $this->recorder();
        $rows = $log->query([], 200, 0);
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
