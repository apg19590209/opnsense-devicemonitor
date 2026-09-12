<?php

function check($condition, $message)
{
    if (!$condition) {
        fwrite(STDERR, "FAIL: {$message}\n");
        exit(1);
    }
}

$modelSourcePath = getenv('DM_MODEL_PATH');
$defaultsSourcePath = getenv('DM_DEFAULTS_PATH');

check(is_string($modelSourcePath) && is_file($modelSourcePath), 'DM_MODEL_PATH is required');
check(is_string($defaultsSourcePath) && is_file($defaultsSourcePath), 'DM_DEFAULTS_PATH is required');

$token = getmypid() . '-' . bin2hex(random_bytes(4));
$tmp = rtrim(sys_get_temp_dir(), DIRECTORY_SEPARATOR);
$dbPath = $tmp . DIRECTORY_SEPARATOR . "dm-timeline-history-{$token}.db";
$defaultsPath = $tmp . DIRECTORY_SEPARATOR . "dm-timeline-history-defaults-{$token}.json";
$modelPath = $tmp . DIRECTORY_SEPARATOR . "dm-timeline-history-model-{$token}.php";

$cleanup = function () use ($dbPath, $defaultsPath, $modelPath) {
    @unlink($dbPath);
    @unlink($defaultsPath);
    @unlink($modelPath);
};
register_shutdown_function($cleanup);

$defaults = json_decode(file_get_contents($defaultsSourcePath), true);
check(is_array($defaults), 'Unable to parse defaults.json');
if (!isset($defaults['paths']) || !is_array($defaults['paths'])) {
    $defaults['paths'] = [];
}
$defaults['paths']['dbFile'] = $dbPath;
check(
    file_put_contents(
        $defaultsPath,
        json_encode($defaults, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES)
    ) !== false,
    'Unable to create temporary defaults'
);

$db = new SQLite3($dbPath);
$db->busyTimeout(2000);
check(
    $db->exec(
        "CREATE TABLE devices (" .
        "mac TEXT PRIMARY KEY, ip TEXT, hostname TEXT, " .
        "hostname_source TEXT DEFAULT '', custom_hostname TEXT, " .
        "vendor TEXT, vlan TEXT, first_seen DATETIME, last_seen DATETIME, " .
        "is_active INTEGER DEFAULT 0, notification_pending INTEGER DEFAULT 0, " .
        "lifecycle_id INTEGER DEFAULT NULL, return_pending INTEGER DEFAULT 0)"
    ),
    'Unable to create devices fixture'
);
check(
    $db->exec(
        "CREATE TABLE device_identity_events (" .
        "id INTEGER PRIMARY KEY AUTOINCREMENT, mac TEXT NOT NULL, " .
        "lifecycle_id INTEGER DEFAULT NULL, event_type TEXT NOT NULL, " .
        "severity TEXT NOT NULL, detected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, " .
        "ip TEXT, other_ip TEXT, other_mac TEXT, interface TEXT, " .
        "other_interface TEXT, details TEXT, resolved_at DATETIME DEFAULT NULL)"
    ),
    'Unable to create identity-event fixture'
);
$db->close();

$modelSource = file_get_contents($modelSourcePath);
check($modelSource !== false, 'Unable to read staged model');
$liveDefaults = '/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json';
$count = 0;
$modelSource = str_replace($liveDefaults, $defaultsPath, $modelSource, $count);
check($count >= 1, 'Unable to redirect staged model defaults path');
check(file_put_contents($modelPath, $modelSource) !== false, 'Unable to create isolated model copy');
require_once $modelPath;

$model = new \OPNsense\DeviceMonitor\DeviceMonitor();
$model->getDeviceTimeline('ff:ff:ff:ff:ff:ff', 1);

$db = new SQLite3($dbPath);
$db->busyTimeout(2000);

$friendlyMac = 'aa:bb:cc:dd:ee:01';
check(
    $db->exec(
        "INSERT INTO device_lifecycles " .
        "(id, mac, status, custom_hostname, hostname, hostname_source, ip, vendor, vlan, first_seen, last_seen) " .
        "VALUES (10, '{$friendlyMac}', 'active', 'Old name', 'host-one', 'hostwatch', " .
        "'192.168.20.10', 'Vendor', 'LAN', '2026-09-12 08:00:00', '2026-09-12 08:10:00')"
    ),
    'Unable to seed active lifecycle'
);
check(
    $db->exec(
        "INSERT INTO devices " .
        "(mac, ip, hostname, hostname_source, custom_hostname, vendor, vlan, first_seen, last_seen, is_active, lifecycle_id, return_pending) " .
        "VALUES ('{$friendlyMac}', '192.168.20.10', 'host-one', 'hostwatch', 'Old name', " .
        "'Vendor', 'LAN', '2026-09-12 08:00:00', '2026-09-12 08:10:00', 1, 10, 0)"
    ),
    'Unable to seed friendly-name device'
);

$relinkMac = 'aa:bb:cc:dd:ee:02';
check(
    $db->exec(
        "INSERT INTO device_lifecycles " .
        "(id, mac, status, custom_hostname, hostname, hostname_source, ip, vendor, vlan, first_seen, last_seen, archived_at) " .
        "VALUES (20, '{$relinkMac}', 'archived', 'Saved relink name', 'host-two', 'kea', " .
        "'192.168.20.20', 'Vendor', 'LAN', '2026-09-01 08:00:00', '2026-09-01 09:00:00', '2026-09-01 10:00:00')"
    ),
    'Unable to seed archived lifecycle'
);
check(
    $db->exec(
        "INSERT INTO devices " .
        "(mac, ip, hostname, hostname_source, custom_hostname, vendor, vlan, first_seen, last_seen, is_active, lifecycle_id, return_pending) " .
        "VALUES ('{$relinkMac}', '192.168.20.21', 'host-two-return', 'kea', NULL, " .
        "'Vendor', 'LAN', '2026-09-12 09:00:00', '2026-09-12 09:01:00', 1, NULL, 1)"
    ),
    'Unable to seed returning device'
);

$identityMac = 'aa:bb:cc:dd:ee:03';
check(
    $db->exec(
        "INSERT INTO device_identity_events " .
        "(id, mac, lifecycle_id, event_type, severity, detected_at, ip, details, resolved_at) " .
        "VALUES (30, '{$identityMac}', 30, 'IP_IDENTITY_CHANGED', 'warning', " .
        "'2026-09-12 07:00:00', '192.168.20.30', 'fixture', '2026-09-12 07:30:00')"
    ),
    'Unable to seed resolved identity event'
);
$db->close();

check($model->updateHostname($friendlyMac, 'New name'), 'Unable to update friendly name');
$db = new SQLite3($dbPath);
check($db->querySingle("SELECT custom_hostname FROM devices WHERE mac = '{$friendlyMac}'") === 'New name', 'Device friendly name not updated');
check($db->querySingle("SELECT custom_hostname FROM device_lifecycles WHERE id = 10") === 'New name', 'Lifecycle friendly name not synchronized');
$nameEvent = $db->querySingle(
    "SELECT old_value, new_value, lifecycle_id FROM device_activity_events " .
    "WHERE mac = '{$friendlyMac}' AND event_type = 'FRIENDLY_NAME_CHANGED'",
    true
);
check(
    $nameEvent && $nameEvent['old_value'] === 'Old name' &&
    $nameEvent['new_value'] === 'New name' && (int)$nameEvent['lifecycle_id'] === 10,
    'Friendly-name history is incorrect'
);
$db->close();

check($model->updateHostname($friendlyMac, 'New name'), 'Repeated identical friendly name should succeed');
$db = new SQLite3($dbPath);
$nameCount = (int)$db->querySingle(
    "SELECT COUNT(*) FROM device_activity_events WHERE mac = '{$friendlyMac}' " .
    "AND event_type = 'FRIENDLY_NAME_CHANGED'"
);
$db->close();
check($nameCount === 1, 'Repeated identical friendly name created duplicate history');

echo "DEVICE_TIMELINE_FRIENDLY_NAME_HISTORY=PASS\n";

check($model->relinkLifecycle($relinkMac, 20), 'Unable to relink archived lifecycle');
$db = new SQLite3($dbPath);
check(
    $db->querySingle("SELECT status || '|' || COALESCE(archived_at, '') FROM device_lifecycles WHERE id = 20") === 'active|',
    'Relinked lifecycle state is incorrect'
);
$archiveEvent = $db->querySingle(
    "SELECT occurred_at, old_value, new_value FROM device_activity_events " .
    "WHERE mac = '{$relinkMac}' AND lifecycle_id = 20 AND event_type = 'LIFECYCLE_ARCHIVED' " .
    "ORDER BY id DESC LIMIT 1",
    true
);
check(
    $archiveEvent && $archiveEvent['occurred_at'] === '2026-09-01 10:00:00' &&
    $archiveEvent['old_value'] === 'active' && $archiveEvent['new_value'] === 'archived',
    'Archived lifecycle timestamp was not preserved'
);
$relinkEvent = $db->querySingle(
    "SELECT old_value, new_value FROM device_activity_events " .
    "WHERE mac = '{$relinkMac}' AND lifecycle_id = 20 AND event_type = 'LIFECYCLE_RELINKED' " .
    "ORDER BY id DESC LIMIT 1",
    true
);
check(
    $relinkEvent && $relinkEvent['old_value'] === 'archived' && $relinkEvent['new_value'] === 'active',
    'Lifecycle relink history is incorrect'
);
$db->close();

echo "DEVICE_TIMELINE_RELINK_HISTORY=PASS\n";

check($model->setIdentityEventResolved(30, false), 'Unable to reopen identity event');
$db = new SQLite3($dbPath);
check($db->querySingle("SELECT resolved_at FROM device_identity_events WHERE id = 30") === null, 'Identity event was not reopened');
$preservedResolution = $db->querySingle(
    "SELECT occurred_at, old_value, new_value FROM device_activity_events " .
    "WHERE mac = '{$identityMac}' AND lifecycle_id = 30 AND event_type = 'IDENTITY_RESOLVED' " .
    "ORDER BY id DESC LIMIT 1",
    true
);
check(
    $preservedResolution && $preservedResolution['occurred_at'] === '2026-09-12 07:30:00' &&
    $preservedResolution['old_value'] === 'unresolved' && $preservedResolution['new_value'] === 'resolved',
    'Identity resolution timestamp was not preserved'
);
$reopen = $db->querySingle(
    "SELECT old_value, new_value FROM device_activity_events " .
    "WHERE mac = '{$identityMac}' AND lifecycle_id = 30 AND event_type = 'IDENTITY_REOPENED' " .
    "ORDER BY id DESC LIMIT 1",
    true
);
check(
    $reopen && $reopen['old_value'] === 'resolved' && $reopen['new_value'] === 'unresolved',
    'Identity reopen history is incorrect'
);
$identityCount = (int)$db->querySingle("SELECT COUNT(*) FROM device_activity_events WHERE mac = '{$identityMac}'");
$db->close();

check($model->setIdentityEventResolved(30, false), 'Repeated identity reopen should succeed');
$db = new SQLite3($dbPath);
$repeatCount = (int)$db->querySingle("SELECT COUNT(*) FROM device_activity_events WHERE mac = '{$identityMac}'");
$db->close();
check($repeatCount === $identityCount, 'Repeated identity reopen created duplicate history');

check($model->setIdentityEventResolved(30, true), 'Unable to resolve reopened identity event');
$db = new SQLite3($dbPath);
$newResolvedAt = $db->querySingle("SELECT resolved_at FROM device_identity_events WHERE id = 30");
$db->close();
check(is_string($newResolvedAt) && trim($newResolvedAt) !== '', 'Identity event did not resolve again');

echo "DEVICE_TIMELINE_IDENTITY_REOPEN_HISTORY=PASS\n";
echo "DEVICE_TIMELINE_HISTORY_PRESERVATION=PASS\n";
$cleanup();
