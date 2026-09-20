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

    $tmpDefaults =
        sys_get_temp_dir() . '/dm-physical-devices-overview-defaults.json';
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

    // Trigger getDb() so the physical-device tables exist.
    $m->getActivePhysicalDevices();

    check(file_exists($dbFile), 'Test DB not created');

    return $m;
}

$dbFile = sys_get_temp_dir() . '/dm-physical-devices-overview.db';

$model = fresh_model($dbFile, $defaultsPath);
$db = new SQLite3($dbFile);

$db->exec(
    "INSERT INTO physical_devices (id, name, created_at, updated_at, archived_at) " .
    "VALUES " .
    "(1, 'Active Group', '2026-09-01 08:00:00', '2026-09-02 08:00:00', NULL), " .
    "(2, 'Archived Group', '2026-09-03 08:00:00', '2026-09-04 08:00:00', '2026-09-05 08:00:00')"
);

$db->exec(
    "INSERT INTO physical_device_memberships " .
    "(physical_device_id, mac, added_at, removed_at) VALUES " .
    "(1, 'aa:bb:cc:dd:ee:01', '2026-09-01 08:00:00', NULL), " .
    "(1, 'aa:bb:cc:dd:ee:02', '2026-09-01 09:00:00', NULL), " .
    "(1, 'aa:bb:cc:dd:ee:03', '2026-09-01 10:00:00', '2026-09-02 10:00:00'), " .
    "(2, 'aa:bb:cc:dd:ee:04', '2026-09-03 08:00:00', '2026-09-05 08:00:00')"
);

// Identity enrichment comes from the existing devices table (read-only).
$db->exec(
    "INSERT INTO devices " .
    "(mac, ip, hostname, hostname_source, custom_hostname, is_active, last_seen) " .
    "VALUES " .
    "('aa:bb:cc:dd:ee:01', '192.168.20.10', 'laptop', 'kea', 'Alice Laptop', 1, '2026-09-10 12:00:00'), " .
    "('aa:bb:cc:dd:ee:02', '192.168.20.11', 'phone', 'hostwatch', NULL, 0, '2026-09-11 12:00:00'), " .
    "('aa:bb:cc:dd:ee:03', '192.168.20.12', 'old-phone', 'kea', NULL, 0, '2026-09-01 11:00:00'), " .
    "('aa:bb:cc:dd:ee:04', '192.168.20.13', 'printer', 'hostwatch', NULL, 0, '2026-09-04 09:00:00')"
);

$db->close();

$overview = $model->getPhysicalDevicesOverview();

check(
    is_array($overview) && count($overview) === 2,
    'Overview did not return both active and archived groups'
);

$active = $overview[0];
$archived = $overview[1];

check(
    $active['id'] === 1 &&
    $active['name'] === 'Active Group' &&
    $active['archived_at'] === null,
    'Active group was not returned first with the expected fields'
);

check(
    $archived['id'] === 2 &&
    $archived['name'] === 'Archived Group' &&
    $archived['archived_at'] !== null,
    'Archived group was not returned with a populated archived_at'
);

check(
    $active['active_member_count'] === 2,
    'Active group active_member_count is wrong'
);

check(
    $active['total_member_count'] === 3,
    'Active group total_member_count did not include removed memberships'
);

check(
    $archived['active_member_count'] === 0 &&
    $archived['total_member_count'] === 1,
    'Archived group member counts are wrong'
);

check(
    is_array($active['members']) && count($active['members']) === 3,
    'Active group did not return all members'
);

check(
    $active['members'][0]['removed_at'] === null &&
    $active['members'][1]['removed_at'] === null,
    'Active memberships were not returned with removed_at null first'
);

check(
    $active['members'][2]['mac'] === 'aa:bb:cc:dd:ee:03' &&
    $active['members'][2]['removed_at'] !== null,
    'Historical membership was not returned with a populated removed_at'
);

check(
    is_array($archived['members']) &&
    count($archived['members']) === 1 &&
    $archived['members'][0]['mac'] === 'aa:bb:cc:dd:ee:04' &&
    $archived['members'][0]['removed_at'] !== null,
    'Archived group history was not readable'
);

check(
    $archived['members'][0]['added_at'] === '2026-09-03 08:00:00',
    'Archived group membership added_at was not preserved'
);

/* Read-model enrichment: identity fields are surfaced alongside membership. */
check(
    $active['members'][0]['friendly_name'] === 'Alice Laptop' &&
    $active['members'][0]['ip'] === '192.168.20.10' &&
    $active['members'][0]['hostname'] === 'laptop' &&
    $active['members'][0]['hostname_source'] === 'kea' &&
    $active['members'][0]['is_active'] === 1 &&
    $active['members'][0]['last_seen'] === '2026-09-10 12:00:00',
    'Current identity enrichment fields are missing or wrong'
);

check(
    $active['members'][1]['friendly_name'] === null &&
    $active['members'][1]['is_active'] === 0,
    'Current identity without a friendly name was not enriched cleanly'
);

/* Derived device-level counts, online/offline status and Last Seen. */
check(
    $active['current_identity_count'] === 2 &&
    $active['previous_identity_count'] === 1,
    'Derived current/previous identity counts are wrong'
);

check(
    $active['status'] === 'online',
    'Device with an online current identity must derive status online'
);

check(
    $active['last_seen'] === '2026-09-11 12:00:00',
    'Derived device Last Seen must be the max across current identities'
);

check(
    $archived['current_identity_count'] === 0 &&
    $archived['previous_identity_count'] === 1 &&
    $archived['status'] === 'offline' &&
    $archived['last_seen'] === null,
    'Archived device derived fields are wrong'
);

/* Existing listphysicaldevices contract still excludes archived groups. */
$activeGroups = $model->getActivePhysicalDevices();

check(
    is_array($activeGroups) && count($activeGroups) === 1,
    'getActivePhysicalDevices still returns archived groups'
);

check(
    $activeGroups[0]['id'] === 1 &&
    $activeGroups[0]['name'] === 'Active Group' &&
    $activeGroups[0]['member_count'] === 2,
    'getActivePhysicalDevices active group contract changed'
);

echo "DEVICE_PHYSICAL_DEVICES_OVERVIEW=PASS\n";
