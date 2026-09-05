<?php

require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/NotificationHandler.php');

function identityHtml($value)
{
    return htmlspecialchars(
        (string)($value ?? ''),
        ENT_QUOTES | ENT_SUBSTITUTE,
        'UTF-8'
    );
}

function identityValue($value)
{
    $value = trim((string)($value ?? ''));
    return identityHtml($value !== '' ? $value : '-');
}
function identityEventTypeLabel($value)
{
    switch ((string)$value) {
        case 'IP_IDENTITY_CHANGED':
            return 'IPv4 address used by another device';
        case 'IPV6_IDENTITY_CHANGED':
            return 'IPv6 address used by another device';
        case 'MAC_MULTI_IP':
            return 'Device using multiple IPv4 addresses';
        case 'MAC_MULTI_INTERFACE':
            return 'Device seen on multiple interfaces';
        default:
            return (string)$value;
    }
}

$raw = stream_get_contents(STDIN);
$payload = json_decode($raw, true);

if (!is_array($payload) || !isset($payload['events']) || !is_array($payload['events'])) {
    fwrite(STDERR, "Invalid identity email payload\n");
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
        'message' => 'No high-severity IP & MAC conflicts',
    ]) . PHP_EOL;
    exit(0);
}

$count = count($events);
$conflictWord = $count === 1 ? 'conflict' : 'conflicts';
$subject = "OPNsense: IP & MAC conflict alert ({$count} {$conflictWord})";

$hostname = identityHtml(gethostname());
$generated = identityHtml(date('Y-m-d H:i:s'));

$eventHtml = '';

foreach ($events as $index => $event) {
    $number = $index + 1;

    $detected       = identityValue($event['detected_at'] ?? '');
    $severity       = strtoupper(identityValue($event['severity'] ?? ''));
    $type           = identityValue(identityEventTypeLabel($event['event_type'] ?? ''));
    $mac            = identityValue($event['mac'] ?? '');
    $otherMac       = identityValue($event['other_mac'] ?? '');
    $ip             = identityValue($event['ip'] ?? '');
    $otherIp        = identityValue($event['other_ip'] ?? '');
    $interface      = identityValue($event['interface'] ?? '');
    $otherInterface = identityValue($event['other_interface'] ?? '');

    $eventHtml .= <<<HTML
        <div style="margin:20px 0;border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
            <div style="background:#2c3e50;color:white;padding:12px 16px;font-weight:600;">
                IP &amp; MAC Conflict {$number}
            </div>

            <table style="width:100%;border-collapse:collapse;">
                <tr>
                    <td style="width:180px;padding:10px 14px;background:#f8f9fa;border-bottom:1px solid #e9ecef;font-weight:600;color:#6c757d;">Severity</td>
                    <td style="padding:10px 14px;border-bottom:1px solid #e9ecef;">
                        <span style="color:#b71c1c;font-weight:700;">{$severity}</span>
                    </td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;background:#f8f9fa;border-bottom:1px solid #e9ecef;font-weight:600;color:#6c757d;">Conflict Type</td>
                    <td style="padding:10px 14px;border-bottom:1px solid #e9ecef;font-family:monospace;">{$type}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;background:#f8f9fa;border-bottom:1px solid #e9ecef;font-weight:600;color:#6c757d;">Detected</td>
                    <td style="padding:10px 14px;border-bottom:1px solid #e9ecef;font-family:monospace;">{$detected}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;background:#f8f9fa;border-bottom:1px solid #e9ecef;font-weight:600;color:#6c757d;">MAC</td>
                    <td style="padding:10px 14px;border-bottom:1px solid #e9ecef;font-family:monospace;">{$mac}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;background:#f8f9fa;border-bottom:1px solid #e9ecef;font-weight:600;color:#6c757d;">Other MAC</td>
                    <td style="padding:10px 14px;border-bottom:1px solid #e9ecef;font-family:monospace;">{$otherMac}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;background:#f8f9fa;border-bottom:1px solid #e9ecef;font-weight:600;color:#6c757d;">IP Address</td>
                    <td style="padding:10px 14px;border-bottom:1px solid #e9ecef;font-family:monospace;">{$ip}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;background:#f8f9fa;border-bottom:1px solid #e9ecef;font-weight:600;color:#6c757d;">Other IP</td>
                    <td style="padding:10px 14px;border-bottom:1px solid #e9ecef;font-family:monospace;">{$otherIp}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;background:#f8f9fa;border-bottom:1px solid #e9ecef;font-weight:600;color:#6c757d;">Interface</td>
                    <td style="padding:10px 14px;border-bottom:1px solid #e9ecef;font-family:monospace;">{$interface}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;background:#f8f9fa;font-weight:600;color:#6c757d;">Other Interface</td>
                    <td style="padding:10px 14px;font-family:monospace;">{$otherInterface}</td>
                </tr>
            </table>
        </div>
HTML;
}

$html = <<<HTML
<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;background-color:#f5f7fa;margin:0;padding:20px;color:#2d3748;">

<div style="max-width:800px;margin:0 auto;background:white;border-radius:12px;box-shadow:0 4px 6px rgba(0,0,0,0.1);overflow:hidden;">

    <div style="background:linear-gradient(135deg,#f6821f 0%,#e65100 100%);color:white;padding:30px;text-align:center;">
        <div style="font-size:48px;margin-bottom:10px;">⚠️</div>
        <h1 style="margin:0;font-size:28px;font-weight:600;">Device Monitor Identity Alert</h1>
    </div>

    <div style="background:#fff3e0;border-left:4px solid #f6821f;padding:20px;margin:20px;border-radius:8px;">
        <strong style="color:#e65100;font-size:20px;">{$count} high-severity IP &amp; MAC {$conflictWord}</strong>
        detected
    </div>

    <div style="padding:0 20px 20px 20px;">

        <div style="background:#f8f9fa;border-radius:8px;padding:15px;margin-bottom:15px;">
            <span style="font-weight:600;color:#6c757d;">Server:</span>
            <span style="font-family:monospace;background:white;padding:5px 12px;border-radius:4px;border:1px solid #dee2e6;margin-left:10px;">{$hostname}</span>
        </div>

        <div style="background:#f8f9fa;border-radius:8px;padding:15px;margin-bottom:20px;">
            <span style="font-weight:600;color:#6c757d;">Email generated:</span>
            <span style="font-family:monospace;background:white;padding:5px 12px;border-radius:4px;border:1px solid #dee2e6;margin-left:10px;">{$generated}</span>
        </div>

        {$eventHtml}

        <div style="background:#fff8e1;border-left:4px solid #ffb300;padding:15px;margin-top:20px;border-radius:6px;">
            <strong>Observational alert only.</strong><br>
            Device Monitor did not block, delete, quarantine, or otherwise remediate any device.
        </div>

    </div>

    <div style="background:#f8f9fa;padding:20px;text-align:center;color:#6c757d;font-size:12px;border-top:1px solid #e9ecef;">
        <div>🛡️ <strong>OPNsense Device Monitor</strong></div>
        <div style="font-family:monospace;color:#495057;margin-top:5px;">
            Generated: {$generated}
        </div>
    </div>

</div>
</body>
</html>
HTML;

$handler = new NotificationHandler();
$result = $handler->sendCustomEmail($subject, $html);

echo json_encode($result) . PHP_EOL;

exit(($result['result'] ?? '') === 'failed' ? 1 : 0);
