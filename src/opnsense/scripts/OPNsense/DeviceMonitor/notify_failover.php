<?php
/**
 * CARP failover notifier
 * Path: /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/notify_failover.php
 *
 * Reads one CARP role transition from STDIN and reports it on both configured
 * channels. The scan daemon calls this only when the persisted role changed and
 * the HA / CARP tab has "Notify when this node changes CARP role" enabled.
 *
 * STDIN: {"hostname","role","observing","reason","timestamp"}
 * STDOUT: the combined NotificationHandler result as JSON
 */

require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/NotificationHandler.php');

$raw = stream_get_contents(STDIN);
$payload = json_decode($raw, true);

if (!is_array($payload)) {
    fwrite(STDERR, "Invalid failover payload\n");
    exit(2);
}

$role = strtoupper(trim((string)($payload['role'] ?? '')));

if ($role === '') {
    $role = 'none';
}

$hostname = trim((string)($payload['hostname'] ?? ''));
if ($hostname === '') {
    $hostname = (string)gethostname();
}

$observing = !empty($payload['observing']);
$previous = strtoupper(trim((string)($payload['previous'] ?? '')));
$reason = trim((string)($payload['reason'] ?? ''));
$timestamp = trim((string)($payload['timestamp'] ?? ''));
if ($timestamp === '') {
    $timestamp = date('Y-m-d H:i:s');
}

$verb = ($role === 'BACKUP')
    ? 'This node is now on standby'
    : (($role === 'MASTER') ? 'This node is now the master' : 'This node reports no CARP role');

$subject = '[Device Monitor] ' . $hostname . ' CARP role: ' . $role;

if ($previous !== '' && $previous !== $role) {
    $subject = '[Device Monitor] ' . $hostname . ' CARP failover: ' . $previous . ' to ' . $role;
}

$body = '<p><strong>' . htmlspecialchars($verb, ENT_QUOTES, 'UTF-8') . '</strong></p>'
    . '<table cellpadding="4" style="border-collapse:collapse;">'
    . '<tr><td>Host</td><td>' . htmlspecialchars($hostname, ENT_QUOTES, 'UTF-8') . '</td></tr>'
    . '<tr><td>Role</td><td>' . htmlspecialchars($role, ENT_QUOTES, 'UTF-8') . '</td></tr>';

if ($previous !== '') {
    $body .= '<tr><td>Previous role</td><td>' . htmlspecialchars($previous, ENT_QUOTES, 'UTF-8') . '</td></tr>';
}

$body .= '<tr><td>Service observation</td><td>'
    . ($observing ? 'active' : 'suppressed' . ($reason !== '' ? ' (' . htmlspecialchars($reason, ENT_QUOTES, 'UTF-8') . ')' : ''))
    . '</td></tr>'
    . '<tr><td>Detected</td><td>' . htmlspecialchars($timestamp, ENT_QUOTES, 'UTF-8') . '</td></tr>'
    . '</table>';

$handler = new NotificationHandler();

/* sendCustomEmail and sendWebhook own the channel guards: a disabled or
 * unconfigured channel returns "skipped" and never reaches the network. */
$result = [
    'result' => 'ok',
    'email' => $handler->sendCustomEmail($subject, $body),
    'webhook' => $handler->sendWebhook(false, null, [
        'event' => 'carp_failover',
        'hostname' => $hostname,
        'timestamp' => $timestamp,
        'role' => $role,
        'severity' => 'high',
        'observing' => $observing,
        'reason' => $reason,
        'message' => $hostname . ': CARP role is now ' . $role,
    ]),
];

$failed = (
    (($result['email']['result'] ?? '') === 'failed')
    && (($result['webhook']['result'] ?? '') === 'failed')
);

if ($failed) {
    $result['result'] = 'failed';
}

/* A delivery failure is reported on STDOUT and through the exit code, so the
 * daemon can log it without re-parsing the individual channel results. */
echo json_encode($result) . PHP_EOL;

exit($failed ? 1 : 0);
