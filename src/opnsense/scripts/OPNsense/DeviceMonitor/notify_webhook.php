#!/usr/local/bin/php
<?php

// Include shared handler
require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/NotificationHandler.php');

// Zavolej funkci
$handler = new NotificationHandler(); // No namespace means the global namespace
$handler->fLog("Preparing to send webhook", 'WEBHOOK');
$result = $handler->sendWebhook(false);  // false = REAL mode

// Log the result
//$handler->fLog("Result: " . json_encode($result), "WEBHOOK-SCRIPT");
$logMessage = "Webhook notification result: " . ($result['result'] === 'sent' ? "SUCCESS" : "FAILED");
if ($result['result'] !== 'sent') {
    $logMessage .= " | Reason: " . ($result['message'] ?? 'Unknown error');
}
$handler->fLog($logMessage, "NOTIFY_WEBHOOK.php");

// CLI script must use echo and exit
echo json_encode($result);
exit($result['result'] === 'sent' ? 0 : 1);

