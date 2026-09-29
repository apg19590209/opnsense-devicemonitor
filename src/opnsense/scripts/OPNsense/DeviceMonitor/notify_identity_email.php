<?php
/**
 * Identity-conflict webhook forwarder
 * Path: /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/notify_identity_email.php
 *
 * Reads one scan cycle's identity events from STDIN, builds the identity_conflict
 * payload frame and dispatches it through the shared NotificationHandler curl
 * engine using a direct payload override (the notification_pending queue is not
 * consulted).
 *
 * STDIN: {"events":[{"detected_at","event_type","severity","mac","other_mac",
 *                    "ip","other_ip","interface","other_interface","details"}, ...]}
 * STDOUT: the NotificationHandler result as JSON
 */

require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/NotificationHandler.php');

$raw = stream_get_contents(STDIN);
$payload = json_decode($raw, true);

if (!is_array($payload) || !isset($payload['events']) || !is_array($payload['events'])) {
    fwrite(STDERR, "Invalid identity webhook payload\n");
    exit(2);
}

$allowedTypes = [
    'IP_IDENTITY_CHANGED',
    'IPV6_IDENTITY_CHANGED',
];

$events = [];

foreach ($payload['events'] as $event) {
    if (!is_array($event)) {
        continue;
    }

    $type = (string)($event['event_type'] ?? '');
    $severity = strtolower((string)($event['severity'] ?? ''));

    if ($severity !== 'high' || !in_array($type, $allowedTypes, true)) {
        continue;
    }

    $events[] = $event;
}

if (empty($events)) {
    echo json_encode([
        'result' => 'skipped',
        'message' => 'No high-severity IP and MAC conflicts',
    ]) . PHP_EOL;
    exit(0);
}

$identityPayload = [
    'event' => 'identity_conflict',
    'hostname' => gethostname(),
    'timestamp' => date('Y-m-d H:i:s'),
    'severity' => 'high',
    'conflict_count' => count($events),
    'conflicts' => array_values($events),
];

$handler = new NotificationHandler();
$result = $handler->sendWebhook(false, null, $identityPayload);

echo json_encode($result) . PHP_EOL;

exit(($result['result'] ?? '') === 'failed' ? 1 : 0);
