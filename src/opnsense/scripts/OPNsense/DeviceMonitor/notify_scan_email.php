#!/usr/local/bin/php
<?php

require_once('/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/DeviceMonitor.php');

if ($argc < 2) {
    fwrite(STDERR, "Usage: notify_scan_email.php <json-file>\n");
    exit(1);
}

$jsonFile = $argv[1];

if (!is_file($jsonFile)) {
    fwrite(STDERR, "Scan result file not found\n");
    exit(1);
}

$data = json_decode(file_get_contents($jsonFile), true);

if (!is_array($data)) {
    fwrite(STDERR, "Invalid scan result JSON\n");
    exit(1);
}

$config = \OPNsense\DeviceMonitor\DeviceMonitor::getConfig();

if (($config['email_enabled'] ?? '0') !== '1' || empty($config['email_to'])) {
    exit(0);
}

$emailTo   = $config['email_to'];
$emailFrom = $config['email_from'] ?? 'devicemonitor@opnsense.local';

$e = static function ($value) {
    return htmlspecialchars((string)$value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
};

$ip        = $e($data['ip'] ?? '');
$mac       = $e($data['mac'] ?? '');
$hostname  = $e($data['hostname'] ?? 'Unknown');
$vendor    = $e($data['vendor'] ?? 'Unknown');
$vlan      = $e($data['vlan'] ?? '');
$firstSeen = $e($data['first_seen'] ?? '');
$scanTime  = $e($data['scan_time'] ?? date('Y-m-d H:i:s'));
$duration  = $e($data['duration'] ?? '');
$osHint    = $e($data['os_hint'] ?? 'Not identified');
$server    = $e(gethostname());

$rows = '';

foreach (($data['services'] ?? []) as $svc) {
    $port    = $e($svc['port'] ?? '');
    $proto   = $e($svc['protocol'] ?? '');
    $state   = $e($svc['state'] ?? '');
    $service = $e($svc['service'] ?? '');
    $version = $e($svc['version'] ?? '');

    $rows .= <<<HTML
<tr>
    <td style="padding:12px;border-bottom:1px solid #e9ecef;font-family:'Courier New',monospace;">{$port}</td>
    <td style="padding:12px;border-bottom:1px solid #e9ecef;">{$proto}</td>
    <td style="padding:12px;border-bottom:1px solid #e9ecef;">{$state}</td>
    <td style="padding:12px;border-bottom:1px solid #e9ecef;font-weight:600;">{$service}</td>
    <td style="padding:12px;border-bottom:1px solid #e9ecef;">{$version}</td>
</tr>
HTML;
}

if ($rows === '') {
    $rows = <<<HTML
<tr>
    <td colspan="5" style="padding:18px;border-bottom:1px solid #e9ecef;color:#6c757d;">
        No open ports detected in the top-100 TCP scan.
    </td>
</tr>
HTML;
}

$subject = "OPNsense: Targeted scan of new device {$ip}";

$html = <<<HTML
<!DOCTYPE html>
<html>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;background-color:#f5f7fa;margin:0;padding:20px;color:#2d3748;">
<div style="max-width:800px;margin:0 auto;background:white;border-radius:12px;box-shadow:0 4px 6px rgba(0,0,0,0.1);overflow:hidden;">

    <div style="background:linear-gradient(135deg,#f6821f 0%,#e65100 100%);color:white;padding:30px;text-align:center;">
        <div style="font-size:48px;margin-bottom:10px;">🔎</div>
        <h1 style="margin:0;font-size:28px;font-weight:600;">Device Security Scan</h1>
    </div>

    <div style="background:#fff3e0;border-left:4px solid #f6821f;padding:20px;margin:20px;border-radius:8px;">
        <strong style="color:#e65100;font-size:20px;">Targeted scan completed</strong><br>
        Only the newly detected host {$ip} was scanned.
    </div>

    <div style="padding:20px;">
        <h3 style="color:#2c3e50;">🖥️ Device</h3>

        <table style="width:100%;border-collapse:collapse;margin:20px 0;">
            <tr><td style="padding:8px;font-weight:600;color:#6c757d;">IP</td><td style="padding:8px;font-family:'Courier New',monospace;">{$ip}</td></tr>
            <tr><td style="padding:8px;font-weight:600;color:#6c757d;">MAC</td><td style="padding:8px;font-family:'Courier New',monospace;">{$mac}</td></tr>
            <tr><td style="padding:8px;font-weight:600;color:#6c757d;">Hostname</td><td style="padding:8px;">{$hostname}</td></tr>
            <tr><td style="padding:8px;font-weight:600;color:#6c757d;">Vendor</td><td style="padding:8px;">{$vendor}</td></tr>
            <tr><td style="padding:8px;font-weight:600;color:#6c757d;">VLAN</td><td style="padding:8px;">{$vlan}</td></tr>
            <tr><td style="padding:8px;font-weight:600;color:#6c757d;">First seen</td><td style="padding:8px;">{$firstSeen}</td></tr>
            <tr><td style="padding:8px;font-weight:600;color:#6c757d;">OS hint</td><td style="padding:8px;">{$osHint}</td></tr>
            <tr><td style="padding:8px;font-weight:600;color:#6c757d;">Scan duration</td><td style="padding:8px;">{$duration}</td></tr>
        </table>

        <h3 style="margin-top:30px;color:#2c3e50;">🔐 Detected Services</h3>

        <table style="width:100%;border-collapse:collapse;margin:20px 0;">
            <thead>
            <tr>
                <th style="background:#2c3e50;color:white;padding:12px;text-align:left;">Port</th>
                <th style="background:#2c3e50;color:white;padding:12px;text-align:left;">Protocol</th>
                <th style="background:#2c3e50;color:white;padding:12px;text-align:left;">State</th>
                <th style="background:#2c3e50;color:white;padding:12px;text-align:left;">Service</th>
                <th style="background:#2c3e50;color:white;padding:12px;text-align:left;">Version</th>
            </tr>
            </thead>
            <tbody>
                {$rows}
            </tbody>
        </table>
    </div>

    <div style="background:#f8f9fa;padding:20px;text-align:center;color:#6c757d;font-size:12px;border-top:1px solid #e9ecef;">
        <div>🛡️ <strong>OPNsense Device Monitor</strong></div>
        <div style="font-family:'Courier New',monospace;color:#495057;margin-top:5px;">
            Server: {$server} | Scan: {$scanTime}
        </div>
    </div>

</div>
</body>
</html>
HTML;

$emailMethod = strtolower($config['email_method'] ?? 'sendmail');

if ($emailMethod === 'smtp') {
    $helper = '/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/smtp_send.py';

    if (!is_file($helper)) {
        fwrite(STDERR, "Direct SMTP helper not found\n");
        exit(1);
    }

    $plain = html_entity_decode(strip_tags(
        str_replace(
            ['<br>', '<br/>', '<br />', '</p>', '</tr>'],
            ["\n", "\n", "\n", "\n", "\n"],
            $html
        )
    ), ENT_QUOTES | ENT_HTML5, 'UTF-8');

    $plain = preg_replace('/[ \t]+/', ' ', $plain);
    $plain = preg_replace('/\n{3,}/', "\n\n", $plain);
    $plain = trim($plain);

    $payload = json_encode([
        'subject' => $subject,
        'html' => $html,
        'text' => $plain,
    ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);

    if ($payload === false) {
        fwrite(STDERR, "Unable to encode SMTP payload\n");
        exit(1);
    }

    $proc = proc_open(
        '/usr/local/bin/python3 ' . escapeshellarg($helper),
        [
            0 => ['pipe', 'r'],
            1 => ['pipe', 'w'],
            2 => ['pipe', 'w'],
        ],
        $pipes
    );

    if (!is_resource($proc)) {
        fwrite(STDERR, "Unable to start Direct SMTP helper\n");
        exit(1);
    }

    fwrite($pipes[0], $payload);
    fclose($pipes[0]);

    $stdout = stream_get_contents($pipes[1]);
    $stderr = stream_get_contents($pipes[2]);

    fclose($pipes[1]);
    fclose($pipes[2]);

    $ret = proc_close($proc);
    $response = json_decode(trim($stdout), true);

    if (
        $ret !== 0 ||
        !is_array($response) ||
        ($response['result'] ?? '') !== 'sent'
    ) {
        $detail = is_array($response) ? ($response['message'] ?? '') : '';

        if ($detail === '') {
            $detail = trim($stderr) !== ''
                ? trim($stderr)
                : (trim($stdout) !== '' ? trim($stdout) : "exit code {$ret}");
        }

        fwrite(STDERR, "Direct SMTP error: {$detail}\n");
        exit(1);
    }

    exit(0);
}

/* Default transport: local sendmail. */
$message  = "From: {$emailFrom}\r\n";
$message .= "To: {$emailTo}\r\n";
$message .= "Subject: {$subject}\r\n";
$message .= "MIME-Version: 1.0\r\n";
$message .= "Content-Type: text/html; charset=UTF-8\r\n";
$message .= "\r\n{$html}";

$proc = proc_open('/usr/local/sbin/sendmail -t -i', [
    0 => ['pipe', 'r'],
    1 => ['pipe', 'w'],
    2 => ['pipe', 'w']
], $pipes);

if (!is_resource($proc)) {
    fwrite(STDERR, "Unable to start sendmail\n");
    exit(1);
}

fwrite($pipes[0], $message);
fclose($pipes[0]);

$stdout = stream_get_contents($pipes[1]);
$stderr = stream_get_contents($pipes[2]);

fclose($pipes[1]);
fclose($pipes[2]);

$ret = proc_close($proc);

if ($ret !== 0) {
    fwrite(STDERR, $stderr ?: "sendmail exit code {$ret}\n");
}

exit($ret);
