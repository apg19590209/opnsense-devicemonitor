<?php

$modelPath = getenv('DM_MODEL_PATH');
$defaultsPath = getenv('DM_DEFAULTS_PATH');

require_once $modelPath;

function check($ok, $message)
{
    if (!$ok) {
        throw new RuntimeException($message);
    }
}

function fresh_model($dbFile, $defaultsPath)
{
    $data = json_decode(file_get_contents($defaultsPath), true);
    $data['paths']['dbFile'] = $dbFile;

    $tmpDefaults = sys_get_temp_dir() . '/dm-change-summary-defaults.json';
    file_put_contents($tmpDefaults, json_encode($data));

    $r = new ReflectionClass(
        \OPNsense\DeviceMonitor\DeviceMonitor::class
    );

    $p = $r->getProperty('defaultsFile');
    $p->setAccessible(true);
    $p->setValue(null, $tmpDefaults);

    $p = $r->getProperty('data');
    $p->setAccessible(true);
    $p->setValue(null, null);

    @unlink($dbFile);

    $m = new \OPNsense\DeviceMonitor\DeviceMonitor();

    // Trigger getDb() so the model-owned tables exist.
    $m->getDeviceLifecycles('aa:bb:cc:dd:ee:00');

    check(file_exists($dbFile), 'Test DB not created');

    return $m;
}

function count_by_type($events, $type)
{
    $n = 0;

    foreach ($events as $event) {
        if ($event['event_type'] === $type) {
            $n++;
        }
    }

    return $n;
}

$dbFile = sys_get_temp_dir() . '/dm-change-summary.db';

$model = fresh_model($dbFile, $defaultsPath);
$db = new SQLite3($dbFile);

$db->exec(
    'CREATE TABLE device_identity_events (' .
    'id INTEGER PRIMARY KEY AUTOINCREMENT, ' .
    'mac TEXT NOT NULL, event_type TEXT NOT NULL, ' .
    'severity TEXT NOT NULL, ' .
    'detected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, ' .
    'ip TEXT, other_ip TEXT, other_mac TEXT, interface TEXT, ' .
    'other_interface TEXT, details TEXT, resolved_at DATETIME, ' .
    'lifecycle_id INTEGER DEFAULT NULL)'
);

$db->exec(
    'CREATE TABLE device_services (' .
    'id INTEGER PRIMARY KEY AUTOINCREMENT, mac TEXT, ip TEXT NOT NULL, ' .
    'interface TEXT NOT NULL DEFAULT \'\', service_type TEXT NOT NULL, ' .
    'port INTEGER NOT NULL, protocol TEXT NOT NULL, ' .
    'status TEXT NOT NULL DEFAULT \'available\', ' .
    'detection_method TEXT NOT NULL, confidence TEXT NOT NULL, ' .
    'product TEXT, version TEXT, ' .
    'first_detected DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, ' .
    'last_verified DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, ' .
    'UNIQUE(ip, service_type, port, protocol, detection_method, interface))'
);

$db->exec(
    "INSERT INTO devices (mac, ip, hostname, custom_hostname, first_seen) " .
    "VALUES ('aa:bb:cc:dd:ee:01', '192.0.2.10', 'laptop', NULL, '2026-09-14 08:00:00')"
);

$db->exec(
    "INSERT INTO devices (mac, ip, hostname, custom_hostname, first_seen) " .
    "VALUES ('aa:bb:cc:dd:ee:02', '192.0.2.20', '', 'Printer', '2026-09-15 08:00:00')"
);

$db->exec(
    "INSERT INTO device_lifecycles " .
    "(mac, status, first_seen, created_at, archived_at) VALUES " .
    "('aa:bb:cc:dd:ee:01', 'active', '2026-09-14 08:00:00', '2026-09-14 08:00:00', NULL)"
);

$db->exec(
    "INSERT INTO device_lifecycles " .
    "(mac, status, first_seen, created_at, archived_at) VALUES " .
    "('aa:bb:cc:dd:ee:02', 'archived', '2026-09-15 08:00:00', '2026-09-15 08:00:00', '2026-09-16 10:00:00')"
);

$db->exec(
    "INSERT INTO device_activity_events " .
    "(mac, lifecycle_id, event_type, occurred_at, old_value, new_value) VALUES " .
    "('aa:bb:cc:dd:ee:01', 1, 'IP_CHANGED', '2026-09-15 09:00:00', '192.0.2.10', '192.0.2.11')"
);

$db->exec(
    "INSERT INTO device_activity_events " .
    "(mac, lifecycle_id, event_type, occurred_at, old_value, new_value) VALUES " .
    "('aa:bb:cc:dd:ee:01', 1, 'SERVICE_AVAILABLE', '2026-09-15 10:00:00', 'unavailable', 'available')"
);

$db->exec(
    "INSERT INTO device_activity_events " .
    "(mac, lifecycle_id, event_type, occurred_at, old_value, new_value) VALUES " .
    "('aa:bb:cc:dd:ee:01', 1, 'LIFECYCLE_RELINKED', '2026-09-16 09:00:00', 'archived', 'active')"
);

$db->exec(
    "INSERT INTO device_identity_events " .
    "(mac, event_type, severity, detected_at, ip, resolved_at) VALUES " .
    "('aa:bb:cc:dd:ee:01', 'MAC_MULTI_IP', 'medium', '2026-09-15 11:00:00', '192.0.2.10', '2026-09-15 12:00:00')"
);

$db->exec(
    "INSERT INTO device_comment_versions " .
    "(comment_id, lifecycle_id, comment, action, created_at) VALUES " .
    "(1, 1, 'Test note', 'created', '2026-09-14 12:00:00')"
);

$db->exec(
    "INSERT INTO physical_devices (name, created_at, archived_at) VALUES " .
    "('Office Printer', '2026-09-16 08:00:00', NULL)"
);

$db->exec(
    "INSERT INTO physical_device_memberships " .
    "(physical_device_id, mac, added_at, removed_at) VALUES " .
    "(1, 'aa:bb:cc:dd:ee:02', '2026-09-16 08:00:00', NULL)"
);

$db->exec(
    "INSERT INTO device_services " .
    "(mac, ip, interface, service_type, port, protocol, status, " .
    "detection_method, confidence, first_detected, last_verified) VALUES " .
    "('aa:bb:cc:dd:ee:01', '192.0.2.10', 're0', 'SSH', 22, 'tcp', 'available', " .
    "'probe', 'high', '2026-09-14 10:00:00', '2026-09-14 10:00:00')"
);

$db->close();

$WINDOW_START = '2026-09-14 00:00:00';
$WINDOW_END = '2026-09-16 23:59:59';

/* Valid window filtering and summary counters. */
$result = $model->getChangeSummary($WINDOW_START, $WINDOW_END);

check(is_array($result), 'Change summary is not an array');
check($result['total'] === 14, 'Total event count is wrong');

check(
    $result['summary']['new_devices'] === 2,
    'New-device counter is wrong'
);

check(
    $result['summary']['returned_devices'] === 1,
    'Returned-device counter is wrong'
);

check(
    $result['summary']['lifecycle'] === 4,
    'Lifecycle counter is wrong'
);

check(
    $result['summary']['identity'] === 3,
    'Identity counter is wrong'
);

check(
    $result['summary']['physical_device'] === 2,
    'Physical-device counter is wrong'
);

check(
    $result['summary']['user_history'] === 1,
    'User-history counter is wrong'
);

check(
    $result['summary']['infrastructure'] === 2,
    'Infrastructure counter is wrong'
);

/* Supported event types are present. */
$expectedTypes = [
    'DEVICE_DISCOVERED' => 2,
    'LIFECYCLE_STARTED' => 2,
    'LIFECYCLE_ARCHIVED' => 1,
    'LIFECYCLE_RELINKED' => 1,
    'IP_CHANGED' => 1,
    'SERVICE_AVAILABLE' => 1,
    'SERVICE_DISCOVERED' => 1,
    'MAC_MULTI_IP' => 1,
    'IDENTITY_RESOLVED' => 1,
    'NOTE_CREATED' => 1,
    'PHYSICAL_DEVICE_CREATED' => 1,
    'PHYSICAL_DEVICE_IDENTITY_LINKED' => 1
];

foreach ($expectedTypes as $type => $count) {
    check(
        count_by_type($result['events'], $type) === $count,
        'Expected event type count is wrong for ' . $type
    );
}

/* No duplicate IDENTITY_RESOLVED (only one authoritative source). */
check(
    count_by_type($result['events'], 'IDENTITY_RESOLVED') === 1,
    'Identity resolution was duplicated'
);

/* Ordering is newest-first and deterministic. */
$events = $result['events'];
$sorted = true;

for ($i = 1; $i < count($events); $i++) {
    if (
        strcmp(
            $events[$i - 1]['occurred_at_utc'],
            $events[$i]['occurred_at_utc']
        ) < 0
    ) {
        $sorted = false;
        break;
    }
}

check($sorted, 'Events are not ordered newest-first');

/* Normalized event shape. */
$first = $events[0];

foreach (
    [
        'id',
        'category',
        'event_type',
        'occurred_at',
        'occurred_at_utc',
        'severity',
        'subject',
        'mac',
        'previous',
        'current',
        'detail',
        'action'
    ] as $key
) {
    check(
        array_key_exists($key, $first),
        'Event missing normalized key ' . $key
    );
}

/* Display timestamp is formatted in OPNsense local time while the raw UTC
   value is preserved separately for sorting/filtering. */
check(
    preg_match(
        '/^\d{2}\.\d{2}\.\d{4} - \d{2}:\d{2}:\d{2} [A-Z]+$/',
        $first['occurred_at']
    ) === 1,
    'occurred_at is not in local d.m.Y - H:i:s T display format'
);

check(
    preg_match(
        '/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/',
        $first['occurred_at_utc']
    ) === 1,
    'occurred_at_utc is not the raw UTC sortable format'
);

/* Category filtering. */
$identity = $model->getChangeSummary(
    $WINDOW_START,
    $WINDOW_END,
    'identity'
);

check(
    $identity['total'] === 3 &&
    $identity['summary']['identity'] === 3,
    'Identity category filter is wrong'
);

foreach ($identity['events'] as $event) {
    check(
        $event['category'] === 'identity',
        'Category filter leaked a non-identity event'
    );
}

/* Time-window filtering bounds. */
$narrow = $model->getChangeSummary(
    '2026-09-15 00:00:00',
    '2026-09-15 23:59:59'
);

check(
    $narrow['total'] === 6,
    'Narrow time window returned the wrong count'
);

/* Limit and offset. */
$page = $model->getChangeSummary($WINDOW_START, $WINDOW_END, 'all', 5, 0);
check(count($page['events']) === 5, 'Limit was not applied');
check($page['total'] === 14, 'Limit changed total');

$page2 = $model->getChangeSummary($WINDOW_START, $WINDOW_END, 'all', 5, 5);
check(count($page2['events']) === 5, 'Offset page size is wrong');

/* Empty result window. */
$empty = $model->getChangeSummary('2026-09-20 00:00:00', '2026-09-21 00:00:00');
check(
    $empty['total'] === 0 &&
    $empty['summary']['total'] === 0 &&
    count($empty['events']) === 0,
    'Empty window did not return an empty result'
);

/* Validation: invalid start. */
$threw = false;

try {
    $model->getChangeSummary('not-a-date', $WINDOW_END);
} catch (\InvalidArgumentException $e) {
    $threw = true;
}

check($threw, 'Invalid start was not rejected');

/* Validation: invalid end. */
$threw = false;

try {
    $model->getChangeSummary($WINDOW_START, 'not-a-date');
} catch (\InvalidArgumentException $e) {
    $threw = true;
}

check($threw, 'Invalid end was not rejected');

/* Validation: start after end. */
$threw = false;

try {
    $model->getChangeSummary($WINDOW_END, $WINDOW_START);
} catch (\InvalidArgumentException $e) {
    $threw = true;
}

check($threw, 'Start-after-end was not rejected');

/* Validation: excessive range (over 90 days). */
$threw = false;

try {
    $model->getChangeSummary('2026-01-01 00:00:00', '2026-06-01 00:00:00');
} catch (\InvalidArgumentException $e) {
    $threw = true;
}

check($threw, 'Over-90-day range was not rejected');

/* Validation: unknown category. */
$threw = false;

try {
    $model->getChangeSummary($WINDOW_START, $WINDOW_END, 'bogus');
} catch (\InvalidArgumentException $e) {
    $threw = true;
}

check($threw, 'Unknown category was not rejected');

/* Unsupported event classes are not fabricated. */
check(
    count_by_type($result['events'], 'VENDOR_CHANGED') === 0 &&
    count_by_type($result['events'], 'NMAP_SCAN_COMPLETED') === 0 &&
    count_by_type($result['events'], 'NMAP_SCAN_FAILED') === 0,
    'Unsupported event classes were fabricated'
);

echo "DEVICE_CHANGE_SUMMARY_MODEL=PASS\n";
