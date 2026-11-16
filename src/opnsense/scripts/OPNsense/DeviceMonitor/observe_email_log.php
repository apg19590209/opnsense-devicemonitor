<?php
/**
 * Bounded, out-of-band observation of queued Device Monitor mail.
 *
 * Runs from a scheduled action, never from the sending path. Only emails whose
 * transport identity was proven (our own Message-ID present in a queue file) move
 * beyond `queued`; disappearance from the queue is recorded as UNKNOWN because it
 * proves neither delivery nor failure.
 */
require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php');
require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/EmailTransport.php');

$log = \OPNsense\DeviceMonitor\EmailLog::instance();
$pending = $log->pendingForObservation(20);
$observed = 0;
foreach ($pending as $row) {
    try {
        \OPNsense\DeviceMonitor\EmailTransport::observe($row['event_id'], $log);
        $observed++;
    } catch (\Throwable $e) {
        /* observation is additive and must never fail the action */
    }
}
echo json_encode(['result' => 'ok', 'observed' => $observed, 'pending' => count($pending)]), PHP_EOL;
