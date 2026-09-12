<?php

function check($condition, $message)
{
    if (!$condition) {
        fwrite(STDERR, "FAIL: " . $message . "\n");
        exit(1);
    }
}

$modelPath = getenv('DM_MODEL_PATH');
$defaultsPath = getenv('DM_DEFAULTS_PATH');

check(
    $modelPath && is_file($modelPath),
    'DM_MODEL_PATH missing or invalid'
);
check(
    $defaultsPath && is_file($defaultsPath),
    'DM_DEFAULTS_PATH missing or invalid'
);

$pid = getmypid();

$tmpDefaults =
    sys_get_temp_dir() .
    '/dm-timeline-defaults-' .
    $pid .
    '.json';

$tmpModel =
    sys_get_temp_dir() .
    '/dm-timeline-model-' .
    $pid .
    '.php';

$dbFile =
    sys_get_temp_dir() .
    '/dm-timeline-' .
    $pid .
    '.db';

@unlink($tmpDefaults);
@unlink($tmpModel);
@unlink($dbFile);

$defaults = json_decode(
    file_get_contents($defaultsPath),
    true
);

check(
    is_array($defaults),
    'Unable to read defaults JSON'
);
check(
    isset($defaults['paths']) &&
    is_array($defaults['paths']),
    'Defaults paths missing'
);

$defaults['paths']['dbFile'] = $dbFile;

check(
    file_put_contents(
        $tmpDefaults,
        json_encode(
            $defaults,
            JSON_PRETTY_PRINT
        )
    ) !== false,
    'Unable to write temporary defaults'
);

$modelSource = file_get_contents($modelPath);

check(
    $modelSource !== false,
    'Unable to read model source'
);

$liveDefaults =
    '/usr/local/opnsense/mvc/app/models/' .
    'OPNsense/DeviceMonitor/defaults.json';

$modelSource = str_replace(
    $liveDefaults,
    $tmpDefaults,
    $modelSource,
    $replaceCount
);

check(
    $replaceCount > 0,
    'Model defaults path anchor not found'
);

check(
    file_put_contents(
        $tmpModel,
        $modelSource
    ) !== false,
    'Unable to write test model'
);

require_once $tmpModel;

$model =
    new \OPNsense\DeviceMonitor\DeviceMonitor();

$mac = 'aa:bb:cc:dd:ee:ff';

check(
    $model->getDeviceTimeline($mac, 50) === [],
    'Fresh timeline is not empty'
);

$db = new SQLite3(
    $dbFile,
    SQLITE3_OPEN_READWRITE
);
$db->busyTimeout(2000);

/*
 * These tables are owned/created by scan_network.py in production.
 * The PHP model deliberately reads them but does not create them, so this
 * isolated model regression supplies the minimum scanner-owned schema needed
 * by the timeline aggregation test.
 */
check(
    $db->exec(
        "CREATE TABLE IF NOT EXISTS device_services (" .
        "id INTEGER PRIMARY KEY AUTOINCREMENT, " .
        "mac TEXT, " .
        "ip TEXT NOT NULL, " .
        "interface TEXT NOT NULL DEFAULT '', " .
        "service_type TEXT NOT NULL, " .
        "port INTEGER NOT NULL, " .
        "protocol TEXT NOT NULL, " .
        "status TEXT NOT NULL DEFAULT 'available', " .
        "detection_method TEXT NOT NULL, " .
        "confidence TEXT NOT NULL, " .
        "product TEXT, " .
        "version TEXT, " .
        "first_detected DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, " .
        "last_verified DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, " .
        "UNIQUE(ip, service_type, port, protocol, " .
        "detection_method, interface)" .
        ")"
    ),
    'Unable to create service fixture table'
);

check(
    $db->exec(
        "CREATE TABLE IF NOT EXISTS device_identity_events (" .
        "id INTEGER PRIMARY KEY AUTOINCREMENT, " .
        "mac TEXT NOT NULL, " .
        "lifecycle_id INTEGER DEFAULT NULL, " .
        "event_type TEXT NOT NULL, " .
        "severity TEXT NOT NULL, " .
        "detected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, " .
        "ip TEXT, other_ip TEXT, other_mac TEXT, " .
        "interface TEXT, other_interface TEXT, " .
        "details TEXT, resolved_at DATETIME DEFAULT NULL" .
        ")"
    ),
    'Unable to create identity fixture table'
);

check(
    $db->exec(
        "CREATE TABLE IF NOT EXISTS nmap_scan_history (" .
        "id INTEGER PRIMARY KEY AUTOINCREMENT, " .
        "mac TEXT NOT NULL, " .
        "lifecycle_id INTEGER DEFAULT NULL, " .
        "ip TEXT, " .
        "scan_type TEXT NOT NULL, " .
        "started_at DATETIME NOT NULL, " .
        "finished_at DATETIME, " .
        "success INTEGER, " .
        "error TEXT, " .
        "os_hint TEXT, " .
        "open_port_count INTEGER" .
        ")"
    ),
    'Unable to create Nmap fixture table'
);

check(
    $db->exec(
        "INSERT INTO device_lifecycles " .
        "(id, mac, status, first_seen, last_seen, " .
        "archived_at, created_at) VALUES " .
        "(1, 'aa:bb:cc:dd:ee:ff', 'archived', " .
        "'2026-09-12 08:00:00', " .
        "'2026-09-12 10:20:00', " .
        "'2026-09-12 10:20:00', " .
        "'2026-09-12 08:00:00')"
    ),
    'Unable to seed lifecycle'
);

check(
    $db->exec(
        "INSERT INTO device_comments " .
        "(id, lifecycle_id, comment, created_at, " .
        "updated_at, deleted_at) VALUES " .
        "(1, 1, 'Updated note', " .
        "'2026-09-12 08:15:00', " .
        "'2026-09-12 08:45:00', " .
        "'2026-09-12 08:50:00')"
    ),
    'Unable to seed note'
);

check(
    $db->exec(
        "INSERT INTO device_comment_versions " .
        "(id, comment_id, lifecycle_id, comment, " .
        "action, created_at) VALUES " .
        "(1, 1, 1, 'Initial note', 'created', " .
        "'2026-09-12 08:15:00'), " .
        "(2, 1, 1, 'Updated note', 'edited', " .
        "'2026-09-12 08:45:00'), " .
        "(3, 1, 1, 'Updated note', 'deleted', " .
        "'2026-09-12 08:50:00')"
    ),
    'Unable to seed note versions'
);

check(
    $db->exec(
        "INSERT INTO device_services " .
        "(mac, ip, interface, service_type, port, " .
        "protocol, status, detection_method, confidence, " .
        "product, version, first_detected, last_verified) " .
        "VALUES (" .
        "'aa:bb:cc:dd:ee:ff', " .
        "'192.168.20.10', 'LAN', 'SSH', 22, 'tcp', " .
        "'available', 'ssh_banner', 'verified', " .
        "'OpenSSH', '9', " .
        "'2026-09-12 08:30:00', " .
        "'2026-09-12 08:30:00')"
    ),
    'Unable to seed service discovery'
);

check(
    $db->exec(
        "INSERT INTO device_activity_events " .
        "(mac, lifecycle_id, event_type, occurred_at, " .
        "old_value, new_value, details) VALUES " .
        "('aa:bb:cc:dd:ee:ff', 1, 'IP_CHANGED', " .
        "'2026-09-12 09:00:00', " .
        "'192.168.20.9', '192.168.20.10', NULL)"
    ),
    'Unable to seed activity event'
);

$identityColumns = [];

$result = $db->query(
    'PRAGMA table_info(device_identity_events)'
);

while (
    $result &&
    ($row = $result->fetchArray(SQLITE3_ASSOC))
) {
    $identityColumns[$row['name']] = true;
}

check(
    isset($identityColumns['lifecycle_id']),
    'Identity lifecycle_id column missing'
);

check(
    $db->exec(
        "INSERT INTO device_identity_events " .
        "(mac, lifecycle_id, event_type, severity, " .
        "detected_at, ip, other_ip, other_mac, " .
        "interface, other_interface, details, resolved_at) " .
        "VALUES (" .
        "'aa:bb:cc:dd:ee:ff', 1, " .
        "'IP_IDENTITY_CHANGED', 'high', " .
        "'2026-09-12 09:30:00', " .
        "'192.168.20.10', '192.168.20.11', " .
        "'11:22:33:44:55:66', 'LAN', 'LAN', " .
        "'identity test', " .
        "'2026-09-12 10:30:00')"
    ),
    'Unable to seed identity event'
);

$scanColumns = [];

$result = $db->query(
    'PRAGMA table_info(nmap_scan_history)'
);

while (
    $result &&
    ($row = $result->fetchArray(SQLITE3_ASSOC))
) {
    $scanColumns[$row['name']] = true;
}

check(
    isset($scanColumns['lifecycle_id']),
    'Nmap lifecycle_id column missing'
);

check(
    $db->exec(
        "INSERT INTO nmap_scan_history " .
        "(mac, lifecycle_id, ip, scan_type, " .
        "started_at, finished_at, success, error, " .
        "os_hint, open_port_count) VALUES (" .
        "'aa:bb:cc:dd:ee:ff', 1, " .
        "'192.168.20.10', 'manual', " .
        "'2026-09-12 10:00:00', " .
        "'2026-09-12 10:05:00', " .
        "1, NULL, 'Linux', 2)"
    ),
    'Unable to seed Nmap history'
);

$db->close();

$timeline =
    $model->getDeviceTimeline($mac, 50);

$types =
    array_column(
        $timeline,
        'event_type'
    );

$expected = [
    'IDENTITY_RESOLVED',
    'LIFECYCLE_ARCHIVED',
    'NMAP_SCAN_COMPLETED',
    'IP_IDENTITY_CHANGED',
    'IP_CHANGED',
    'NOTE_ARCHIVED',
    'NOTE_UPDATED',
    'SERVICE_DISCOVERED',
    'NOTE_CREATED',
    'LIFECYCLE_STARTED'
];

check(
    $types === $expected,
    'Timeline ordering or normalization is wrong'
);

check(
    count($timeline) === 10,
    'Timeline row count is wrong'
);

check(
    $timeline[0]['lifecycle_id'] === 1,
    'Identity resolution lifecycle missing'
);

check(
    $timeline[7]['lifecycle_id'] === null,
    'Service discovery falsely assigned lifecycle'
);

check(
    $timeline[4]['data']['old_value'] ===
        '192.168.20.9' &&
    $timeline[4]['data']['new_value'] ===
        '192.168.20.10',
    'Activity transition values missing'
);

$limited =
    $model->getDeviceTimeline($mac, 3);

check(
    count($limited) === 3,
    'Timeline limit not applied'
);

check(
    array_column(
        $limited,
        'event_type'
    ) === array_slice(
        $expected,
        0,
        3
    ),
    'Timeline limit returned wrong rows'
);

check(
    $model->getDeviceTimeline(
        '00:11:22:33:44:55',
        50
    ) === [],
    'Timeline leaked rows from another MAC'
);

@unlink($dbFile);
@unlink($tmpDefaults);
@unlink($tmpModel);

echo "DEVICE_TIMELINE_AGGREGATION=PASS\n";
