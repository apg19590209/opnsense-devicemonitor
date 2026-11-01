#!/usr/local/bin/php
<?php
/**
 * Identity-conflict email sender
 * Path: /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/notify_identity_mail.php
 *
 * Sends one batched identity-conflict email through the shared
 * NotificationHandler transport (sendmail or SMTP, whichever the email
 * settings select). The webhook leg keeps using notify_identity_email.php;
 * this file is the email leg, gated on the identity_email_enabled setting.
 *
 * STDIN: {"events":[{"detected_at","event_type","severity","mac","other_mac",
 *                    "ip","other_ip","interface","other_interface","details"}, ...]}
 * STDOUT: the NotificationHandler result as JSON
 */

require_once('/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/DeviceMonitor.php');
require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/NotificationHandler.php');

$raw = stream_get_contents(STDIN);
$payload = json_decode($raw, true);

if (!is_array($payload) || !isset($payload['events']) || !is_array($payload['events'])) {
    fwrite(STDERR, "Invalid identity email payload\n");
    exit(2);
}

$config = \OPNsense\DeviceMonitor\DeviceMonitor::getConfig();

if (($config['email_enabled'] ?? '0') !== '1' || empty($config['email_to'])) {
    exit(0);
}

if (($config['identity_email_enabled'] ?? '0') !== '1') {
    exit(0);
}

$allowedTypes = ['IP_IDENTITY_CHANGED', 'IPV6_IDENTITY_CHANGED'];

$e = static function ($value) {
    return htmlspecialchars((string)$value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
};

$rows = '';
$count = 0;
$firstIp = '';

foreach ($payload['events'] as $event) {
    if (!is_array($event)) {
        continue;
    }

    if (!in_array((string)($event['event_type'] ?? ''), $allowedTypes, true)) {
        continue;
    }

    $ip = (string)($event['ip'] ?? '');

    if ($firstIp === '') {
        $firstIp = $ip;
    }

    $rows .= sprintf(
        '<tr>'
        . '<td style="padding:10px;border-bottom:1px solid #e9ecef;font-family:\'Courier New\',monospace;">%s</td>'
        . '<td style="padding:10px;border-bottom:1px solid #e9ecef;">%s</td>'
        . '<td style="padding:10px;border-bottom:1px solid #e9ecef;font-family:\'Courier New\',monospace;">%s</td>'
        . '<td style="padding:10px;border-bottom:1px solid #e9ecef;font-family:\'Courier New\',monospace;">%s</td>'
        . '<td style="padding:10px;border-bottom:1px solid #e9ecef;">%s</td>'
        . '<td style="padding:10px;border-bottom:1px solid #e9ecef;">%s</td>'
        . '</tr>',
        $e($ip),
        $e($event['event_type'] ?? ''),
        $e($event['mac'] ?? ''),
        $e($event['other_mac'] ?? ''),
        $e($event['detected_at'] ?? ''),
        $e($event['interface'] ?? '')
    );

    $count++;
}

if ($count === 0) {
    exit(0);
}

$host = $e(gethostname());
$when = $e(date('Y-m-d H:i:s'));
$subject = sprintf(
    'Device Monitor: %d identity conflict%s on %s',
    $count,
    $count === 1 ? '' : 's',
    $firstIp !== '' ? $firstIp : $host
);

$html = <<<HTML
<div style="font-family:Arial,Helvetica,sans-serif;color:#212529;max-width:760px;">
  <h2 style="margin:0 0 6px;font-size:18px;">Identity conflict detected</h2>
  <p style="margin:0 0 12px;color:#6c757d;font-size:13px;">
    {$count} address conflict(s) reported by Device Monitor on <strong>{$host}</strong> at {$when}.
  </p>
  <table style="border-collapse:collapse;width:100%;font-size:13px;">
    <thead>
      <tr style="background:#f8f9fa;text-align:left;">
        <th style="padding:10px;border-bottom:2px solid #dee2e6;">Address</th>
        <th style="padding:10px;border-bottom:2px solid #dee2e6;">Event</th>
        <th style="padding:10px;border-bottom:2px solid #dee2e6;">MAC</th>
        <th style="padding:10px;border-bottom:2px solid #dee2e6;">Conflicting MAC</th>
        <th style="padding:10px;border-bottom:2px solid #dee2e6;">Detected</th>
        <th style="padding:10px;border-bottom:2px solid #dee2e6;">Interface</th>
      </tr>
    </thead>
    <tbody>
      {$rows}
    </tbody>
  </table>
</div>
HTML;

$handler = new \NotificationHandler();
$result = $handler->sendCustomEmail($subject, $html);

echo json_encode($result);
exit(0);
