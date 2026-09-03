#!/usr/local/bin/php
<?php

// Include shared handler
require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/NotificationHandler.php');

// Zavolej funkci
$handler = new NotificationHandler(); // No namespace means the global namespace
$handler->fLog("Preparing to send email", 'EMAIL');
$result = $handler->sendEmail(false);  // false = REAL mode

// Log the result
//$handler->fLog("Result: " . json_encode($result), "EMAIL-SCRIPT");
$logMessage = "Email notification result: " . ($result['result'] === 'sent' ? "SUCCESS" : "FAILED");
if ($result['result'] !== 'sent') {
    $logMessage .= " | Reason: " . ($result['message'] ?? 'Unknown error');
}
$handler->fLog($logMessage, "NOTIFY_EMAIL.php");

// CLI script must use echo and exit
echo json_encode($result);
exit($result['result'] === 'sent' ? 0 : 1);