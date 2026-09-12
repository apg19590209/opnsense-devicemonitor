<?php

require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/NotificationHandler.php');

function serviceAlertHtml($value)
{
    return htmlspecialchars(
        (string)($value ?? ''),
        ENT_QUOTES | ENT_SUBSTITUTE,
        'UTF-8'
    );
}

function serviceAlertValue($value)
{
    $value = trim((string)($value ?? ''));
    return serviceAlertHtml($value !== '' ? $value : '-');
}

function serviceAlertTypeLabel($value)
{
    switch ((string)$value) {
        case 'SERVICE_DISCOVERED':
            return 'New verified service';
        case 'SERVICE_UNAVAILABLE':
            return 'Established service unavailable';
        case 'SERVICE_AVAILABLE':
            return 'Unavailable service recovered';
        default:
            return (string)$value;
    }
}

$raw = stream_get_contents(STDIN);
$payload = json_decode($raw, true);

if (!is_array($payload) || !isset($payload['events']) || !is_array($payload['events'])) {
    fwrite(STDERR, "Invalid service alert email payload\n");
    exit(2);
}

$allowedTypes = [
    'SERVICE_DISCOVERED',
    'SERVICE_UNAVAILABLE',
    'SERVICE_AVAILABLE',
];

$events = [];

foreach ($payload['events'] as $event) {
    if (!is_array($event)) {
        continue;
    }

    $type = (string)($event['event_type'] ?? '');
    $eligible = (bool)($event['alert_eligible'] ?? false);

    if (!$eligible || !in_array($type, $allowedTypes, true)) {
        continue;
    }

    $events[] = $event;
}

if (empty($events)) {
    echo json_encode([
        'result' => 'skipped',
        'message' => 'No eligible infrastructure service alerts',
    ]) . PHP_EOL;
    exit(0);
}

$count = count($events);
$eventWord = $count === 1 ? 'event' : 'events';
$subject = "OPNsense: Infrastructure service alert ({$count} {$eventWord})";

$hostname = serviceAlertHtml(gethostname());
$generated = serviceAlertHtml(date('Y-m-d H:i:s'));

$eventHtml = '';

foreach ($events as $index => $event) {
    $number = $index + 1;

    $type            = serviceAlertValue(serviceAlertTypeLabel($event['event_type'] ?? ''));
    $occurredAt      = serviceAlertValue($event['occurred_at'] ?? '');
    $serviceType     = serviceAlertValue($event['service_type'] ?? '');
    $mac             = serviceAlertValue($event['mac'] ?? '');
    $ip              = serviceAlertValue($event['ip'] ?? '');
    $port            = serviceAlertValue($event['port'] ?? '');
    $protocol        = serviceAlertValue($event['protocol'] ?? '');
    $interface       = serviceAlertValue($event['interface'] ?? '');
    $detectionMethod = serviceAlertValue($event['detection_method'] ?? '');
    $confidence      = serviceAlertValue($event['confidence'] ?? '');
    $product         = serviceAlertValue($event['product'] ?? '');
    $version         = serviceAlertValue($event['version'] ?? '');
    $oldValue        = serviceAlertValue($event['old_value'] ?? '');
    $newValue        = serviceAlertValue($event['new_value'] ?? '');

    $eventHtml .= <<<HTML
        <div style="margin:20px 0;border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
            <div style="background:#2c3e50;color:white;padding:12px 16px;font-weight:600;">
                Infrastructure Service Event {$number}
            </div>

            <table style="width:100%;border-collapse:collapse;">
                <tr>
                    <td style="width:190px;padding:10px 14px;background:#f8f9fa;border-bottom:1px solid #e9ecef;font-weight:600;color:#6c757d;">Change</td>
                    <td style="padding:10px 14px;border-bottom:1px solid #e9ecef;">{$type}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;background:#f8f9fa;border-bottom:1px solid #e9ecef;font-weight:600;color:#6c757d;">Occurred</td>
                    <td style="padding:10px 14px;border-bottom:1px solid #e9ecef;font-family:monospace;">{$occurredAt}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;background:#f8f9fa;border-bottom:1px solid #e9ecef;font-weight:600;color:#6c757d;">Service</td>
                    <td style="padding:10px 14px;border-bottom:1px solid #e9ecef;font-family:monospace;">{$serviceType}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;background:#f8f9fa;border-bottom:1px solid #e9ecef;font-weight:600;color:#6c757d;">MAC</td>
                    <td style="padding:10px 14px;border-bottom:1px solid #e9ecef;font-family:monospace;">{$mac}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;background:#f8f9fa;border-bottom:1px solid #e9ecef;font-weight:600;color:#6c757d;">Endpoint</td>
                    <td style="padding:10px 14px;border-bottom:1px solid #e9ecef;font-family:monospace;">{$ip}:{$port}/{$protocol}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;background:#f8f9fa;border-bottom:1px solid #e9ecef;font-weight:600;color:#6c757d;">Interface</td>
                    <td style="padding:10px 14px;border-bottom:1px solid #e9ecef;font-family:monospace;">{$interface}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;background:#f8f9fa;border-bottom:1px solid #e9ecef;font-weight:600;color:#6c757d;">Detection</td>
                    <td style="padding:10px 14px;border-bottom:1px solid #e9ecef;font-family:monospace;">{$detectionMethod}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;background:#f8f9fa;border-bottom:1px solid #e9ecef;font-weight:600;color:#6c757d;">Confidence</td>
                    <td style="padding:10px 14px;border-bottom:1px solid #e9ecef;font-family:monospace;">{$confidence}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;background:#f8f9fa;border-bottom:1px solid #e9ecef;font-weight:600;color:#6c757d;">Product</td>
                    <td style="padding:10px 14px;border-bottom:1px solid #e9ecef;font-family:monospace;">{$product}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;background:#f8f9fa;border-bottom:1px solid #e9ecef;font-weight:600;color:#6c757d;">Version</td>
                    <td style="padding:10px 14px;border-bottom:1px solid #e9ecef;font-family:monospace;">{$version}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;background:#f8f9fa;border-bottom:1px solid #e9ecef;font-weight:600;color:#6c757d;">Previous state</td>
                    <td style="padding:10px 14px;border-bottom:1px solid #e9ecef;font-family:monospace;">{$oldValue}</td>
                </tr>
                <tr>
                    <td style="padding:10px 14px;background:#f8f9fa;font-weight:600;color:#6c757d;">Current state</td>
                    <td style="padding:10px 14px;font-family:monospace;">{$newValue}</td>
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
        <h1 style="margin:0;font-size:28px;font-weight:600;">Device Monitor Infrastructure Service Alert</h1>
    </div>

    <div style="background:#fff3e0;border-left:4px solid #f6821f;padding:20px;margin:20px;border-radius:8px;">
        <strong style="color:#e65100;font-size:20px;">{$count} infrastructure service {$eventWord}</strong>
        require attention
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
            Device Monitor did not restart, block, reconfigure, or otherwise remediate any service or device.
        </div>

    </div>

    <div style="background:#f8f9fa;padding:20px;text-align:center;color:#6c757d;font-size:12px;border-top:1px solid #e9ecef;">
        <div><strong>OPNsense Device Monitor</strong></div>
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
