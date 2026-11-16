<?php
/**
 * Retention for the Device Monitor email log.
 *
 * Removes only records older than the 30-day window in the dedicated log
 * database. It never touches notification history, scan history, device
 * records or Postfix queues.
 */
require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php');

$log = \OPNsense\DeviceMonitor\EmailLog::instance();
$removed = $log->prune(\OPNsense\DeviceMonitor\EmailLog::RETENTION_DAYS);
$diag = $log->lastDiagnostic();
echo json_encode([
    'result' => $diag === null ? 'ok' : 'failed',
    'removed' => $removed,
    'retention_days' => \OPNsense\DeviceMonitor\EmailLog::RETENTION_DAYS,
    'message' => $diag,
]), PHP_EOL;
