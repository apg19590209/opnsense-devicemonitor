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

    $tmpDefaults = sys_get_temp_dir() . '/dm-lifecycle-defaults.json';
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
    $m->startNewLifecycle('00:00:00:00:00:00');

    check(file_exists($dbFile), 'Test DB not created');
    return $m;
}

$dbFile = sys_get_temp_dir() . '/dm-lifecycle-actions.db';

/* Start New Lifecycle */
$model = fresh_model($dbFile, $defaultsPath);
$db = new SQLite3($dbFile);

$db->exec(
    "INSERT INTO device_lifecycles " .
    "(mac,status,custom_hostname,first_seen,last_seen,archived_at) VALUES " .
    "('aa:bb:cc:dd:ee:01','archived','Old Friendly'," .
    "'2026-01-01 10:00:00','2026-06-01 10:00:00','2026-06-01 10:05:00')"
);

$db->exec(
    "INSERT INTO device_comments (lifecycle_id,comment) " .
    "VALUES (1,'Old lifecycle comment')"
);

$db->exec(
    "INSERT INTO devices " .
    "(mac,ip,hostname,first_seen,last_seen,is_active,lifecycle_id,return_pending) " .
    "VALUES ('aa:bb:cc:dd:ee:01','192.0.2.20','return-host'," .
    "'2026-09-11 08:00:00','2026-09-11 08:00:00',1,NULL,1)"
);

$db->exec(
    "INSERT INTO deleted_devices (mac,last_seen) " .
    "VALUES ('aa:bb:cc:dd:ee:01','2026-06-01 10:00:00')"
);

$db->close();

$state = $model->getDeviceLifecycleState('aa:bb:cc:dd:ee:01');
check(
    is_array($state) &&
    $state['lifecycle_id'] === null &&
    $state['return_pending'] === 1,
    'Pending lifecycle state is wrong'
);

$newId = $model->startNewLifecycle('aa:bb:cc:dd:ee:01');
check($newId === 2, 'New lifecycle was not created as lifecycle 2');

$db = new SQLite3($dbFile);

check(
    $db->querySingle(
        "SELECT status FROM device_lifecycles WHERE id=1"
    ) === 'archived',
    'Old lifecycle was changed'
);

check(
    $db->querySingle(
        "SELECT first_seen FROM device_lifecycles WHERE id=2"
    ) === '2026-09-11 08:00:00',
    'New lifecycle first_seen is wrong'
);

check(
    $db->querySingle(
        "SELECT lifecycle_id || ':' || return_pending FROM devices " .
        "WHERE mac='aa:bb:cc:dd:ee:01'"
    ) === '2:0',
    'Device not attached to new lifecycle'
);

check(
    (int)$db->querySingle("SELECT COUNT(*) FROM deleted_devices") === 0,
    'Tombstone not removed'
);

check(
    (int)$db->querySingle(
        "SELECT COUNT(*) FROM device_comments WHERE lifecycle_id=1"
    ) === 1,
    'Old comment not preserved'
);

$db->close();

$state = $model->getDeviceLifecycleState('aa:bb:cc:dd:ee:01');
check(
    is_array($state) &&
    $state['lifecycle_id'] === 2 &&
    $state['return_pending'] === 0,
    'Resolved lifecycle state is wrong'
);

echo "DEVICE_START_NEW_LIFECYCLE=PASS\n";

/* Relink Previous Lifecycle */
$model = fresh_model($dbFile, $defaultsPath);
$db = new SQLite3($dbFile);

$db->exec(
    "INSERT INTO device_lifecycles " .
    "(mac,status,custom_hostname,first_seen,last_seen,archived_at) VALUES " .
    "('aa:bb:cc:dd:ee:02','archived','Saved Friendly'," .
    "'2026-02-01 09:00:00','2026-07-01 09:00:00','2026-07-01 09:05:00')"
);

$db->exec(
    "INSERT INTO device_comments (lifecycle_id,comment) " .
    "VALUES (1,'Preserved relink comment')"
);

$db->exec(
    "INSERT INTO devices " .
    "(mac,ip,hostname,custom_hostname,first_seen,last_seen,is_active," .
    "lifecycle_id,return_pending) VALUES " .
    "('aa:bb:cc:dd:ee:02','192.0.2.22','return-host',NULL," .
    "'2026-09-11 08:30:00','2026-09-11 08:30:00',1,NULL,1)"
);

$db->exec(
    "INSERT INTO deleted_devices (mac,last_seen) " .
    "VALUES ('aa:bb:cc:dd:ee:02','2026-07-01 09:00:00')"
);

$db->close();

check(
    $model->relinkLifecycle('aa:bb:cc:dd:ee:02', 1) === true,
    'Relink failed'
);

$db = new SQLite3($dbFile);

check(
    $db->querySingle(
        "SELECT status FROM device_lifecycles WHERE id=1"
    ) === 'active',
    'Relink did not reactivate lifecycle'
);

check(
    $db->querySingle(
        "SELECT first_seen FROM device_lifecycles WHERE id=1"
    ) === '2026-02-01 09:00:00',
    'Relink changed original first_seen'
);

check(
    $db->querySingle(
        "SELECT last_seen FROM device_lifecycles WHERE id=1"
    ) === '2026-09-11 08:30:00',
    'Relink did not update last_seen'
);

check(
    $db->querySingle(
        "SELECT custom_hostname FROM devices " .
        "WHERE mac='aa:bb:cc:dd:ee:02'"
    ) === 'Saved Friendly',
    'Relink did not restore Friendly Name'
);

check(
    $db->querySingle(
        "SELECT lifecycle_id || ':' || return_pending FROM devices " .
        "WHERE mac='aa:bb:cc:dd:ee:02'"
    ) === '1:0',
    'Relink did not attach device correctly'
);

check(
    (int)$db->querySingle("SELECT COUNT(*) FROM deleted_devices") === 0,
    'Relink tombstone not removed'
);

check(
    (int)$db->querySingle(
        "SELECT COUNT(*) FROM device_comments WHERE lifecycle_id=1"
    ) === 1,
    'Relink comment not preserved'
);

$db->close();
echo "DEVICE_RELINK_LIFECYCLE=PASS\n";

/* Wrong-MAC protection */
$model = fresh_model($dbFile, $defaultsPath);
$db = new SQLite3($dbFile);

$db->exec(
    "INSERT INTO device_lifecycles " .
    "(mac,status,custom_hostname,first_seen,last_seen,archived_at) VALUES " .
    "('aa:bb:cc:dd:ee:03','archived','Wrong Device'," .
    "'2026-03-01 09:00:00','2026-07-01 09:00:00','2026-07-01 09:05:00')"
);

$db->exec(
    "INSERT INTO devices " .
    "(mac,first_seen,last_seen,lifecycle_id,return_pending) VALUES " .
    "('aa:bb:cc:dd:ee:04','2026-09-11 08:40:00'," .
    "'2026-09-11 08:40:00',NULL,1)"
);

$db->exec(
    "INSERT INTO deleted_devices (mac,last_seen) " .
    "VALUES ('aa:bb:cc:dd:ee:04','2026-07-01 09:00:00')"
);

$db->close();

check(
    $model->relinkLifecycle('aa:bb:cc:dd:ee:04', 1) === false,
    'Wrong-MAC lifecycle relink was accepted'
);

$db = new SQLite3($dbFile);

check(
    $db->querySingle(
        "SELECT status FROM device_lifecycles WHERE id=1"
    ) === 'archived',
    'Wrong-MAC failure changed archived lifecycle'
);

check(
    $db->querySingle(
        "SELECT return_pending FROM devices " .
        "WHERE mac='aa:bb:cc:dd:ee:04'"
    ) == 1,
    'Wrong-MAC failure cleared pending state'
);

check(
    (int)$db->querySingle(
        "SELECT COUNT(*) FROM deleted_devices " .
        "WHERE mac='aa:bb:cc:dd:ee:04'"
    ) === 1,
    'Wrong-MAC failure removed tombstone'
);

$db->close();
@unlink($dbFile);

echo "DEVICE_RELINK_WRONG_MAC_REJECTED=PASS\n";

/* Non-pending device protection */
$model = fresh_model($dbFile, $defaultsPath);
$db = new SQLite3($dbFile);

$db->exec(
    "INSERT INTO device_lifecycles " .
    "(mac,status,first_seen,last_seen,archived_at) VALUES " .
    "('aa:bb:cc:dd:ee:05','archived'," .
    "'2026-04-01 09:00:00','2026-07-01 09:00:00','2026-07-01 09:05:00')"
);

$db->exec(
    "INSERT INTO devices " .
    "(mac,first_seen,last_seen,lifecycle_id,return_pending) VALUES " .
    "('aa:bb:cc:dd:ee:05','2026-09-11 09:00:00'," .
    "'2026-09-11 09:00:00',NULL,0)"
);

$db->close();

check(
    $model->startNewLifecycle('aa:bb:cc:dd:ee:05') === false,
    'Start New accepted a non-pending device'
);

check(
    $model->relinkLifecycle('aa:bb:cc:dd:ee:05', 1) === false,
    'Relink accepted a non-pending device'
);

echo "DEVICE_NON_PENDING_ACTIONS_REJECTED=PASS\n";



/* Existing active lifecycle protection */
$model = fresh_model($dbFile, $defaultsPath);
$db = new SQLite3($dbFile);

$db->exec(
    "INSERT INTO device_lifecycles " .
    "(mac,status,first_seen,last_seen) VALUES " .
    "('aa:bb:cc:dd:ee:06','active'," .
    "'2026-05-01 09:00:00','2026-08-01 09:00:00')"
);

$db->exec(
    "INSERT INTO device_lifecycles " .
    "(mac,status,first_seen,last_seen,archived_at) VALUES " .
    "('aa:bb:cc:dd:ee:06','archived'," .
    "'2026-01-01 09:00:00','2026-04-01 09:00:00','2026-04-01 09:05:00')"
);

$db->exec(
    "INSERT INTO devices " .
    "(mac,first_seen,last_seen,lifecycle_id,return_pending) VALUES " .
    "('aa:bb:cc:dd:ee:06','2026-09-11 09:10:00'," .
    "'2026-09-11 09:10:00',NULL,1)"
);

$db->exec(
    "INSERT INTO deleted_devices (mac,last_seen) " .
    "VALUES ('aa:bb:cc:dd:ee:06','2026-08-01 09:00:00')"
);

$db->close();

check(
    $model->startNewLifecycle('aa:bb:cc:dd:ee:06') === false,
    'Start New accepted an existing active lifecycle'
);

check(
    $model->relinkLifecycle('aa:bb:cc:dd:ee:06', 2) === false,
    'Relink accepted an existing active lifecycle'
);

echo "DEVICE_ACTIVE_LIFECYCLE_CONFLICT_REJECTED=PASS\n";


/* Lifecycle comment safety */
$model = fresh_model($dbFile, $defaultsPath);
$db = new SQLite3($dbFile);

$db->exec(
    "INSERT INTO device_lifecycles " .
    "(mac,status,first_seen,last_seen,archived_at) VALUES " .
    "('aa:bb:cc:dd:ee:07','archived'," .
    "'2026-01-01 09:00:00','2026-02-01 09:00:00','2026-02-01 09:05:00')"
);

$db->exec(
    "INSERT INTO device_comments (lifecycle_id,comment) " .
    "VALUES (1,'Archived comment')"
);

$db->close();

$comments = $model->getLifecycleComments(1);
check(
    count($comments) === 1 &&
    $comments[0]['comment'] === 'Archived comment',
    'Archived lifecycle comments are not readable'
);

check(
    $model->addLifecycleComment(1, 'Should fail') === 0,
    'Added comment to archived lifecycle'
);

check(
    $model->updateLifecycleComment(1, 1, 'Should fail') === false,
    'Updated comment on archived lifecycle'
);

check(
    $model->deleteLifecycleComment(1, 1) === false,
    'Deleted comment from archived lifecycle'
);

echo "DEVICE_ARCHIVED_LIFECYCLE_COMMENTS_READ_ONLY=PASS\n";

/* Active lifecycle comment history */
$model = fresh_model($dbFile, $defaultsPath);
$db = new SQLite3($dbFile);

$db->exec(
    "INSERT INTO device_lifecycles " .
    "(mac,status,first_seen,last_seen) VALUES " .
    "('aa:bb:cc:dd:ee:08','active'," .
    "'2026-09-11 09:30:00','2026-09-11 09:30:00')"
);

$db->close();

$firstId = $model->addLifecycleComment(1, 'First active comment');
$secondId = $model->addLifecycleComment(1, 'Second active comment');

check(
    $firstId === 1 && $secondId === 2,
    'Failed to add independent active lifecycle comments'
);

check(
    $model->updateLifecycleComment(
        1,
        $firstId,
        'First active comment - edited'
    ) === true,
    'Failed to edit first active lifecycle comment'
);

check(
    $model->deleteLifecycleComment(1, $firstId) === true,
    'Failed to delete first active lifecycle comment'
);

$comments = $model->getLifecycleComments(1);
check(count($comments) === 2, 'Deleted comment disappeared from history');

$lifecycles = $model->getDeviceLifecycles('aa:bb:cc:dd:ee:08');
check(
    count($lifecycles) === 1 &&
    (int)$lifecycles[0]['comment_count'] === 2,
    'Lifecycle history count omitted deleted comment'
);

$byId = [];
foreach ($comments as $comment) {
    $byId[(int)$comment['id']] = $comment;
}

check(
    isset($byId[$firstId]) &&
    $byId[$firstId]['comment'] === 'First active comment - edited' &&
    !empty($byId[$firstId]['deleted_at']),
    'Deleted comment current state was not retained'
);

check(
    isset($byId[$secondId]) &&
    $byId[$secondId]['comment'] === 'Second active comment' &&
    empty($byId[$secondId]['deleted_at']),
    'Independent live comment was changed by another comment delete'
);

$firstVersions = $byId[$firstId]['versions'] ?? [];
check(
    count($firstVersions) === 3 &&
    $firstVersions[0]['action'] === 'created' &&
    $firstVersions[0]['comment'] === 'First active comment' &&
    $firstVersions[1]['action'] === 'edited' &&
    $firstVersions[1]['comment'] === 'First active comment - edited' &&
    $firstVersions[2]['action'] === 'deleted' &&
    $firstVersions[2]['comment'] === 'First active comment - edited',
    'First comment version history is incomplete'
);

$secondVersions = $byId[$secondId]['versions'] ?? [];
check(
    count($secondVersions) === 1 &&
    $secondVersions[0]['action'] === 'created' &&
    $secondVersions[0]['comment'] === 'Second active comment',
    'Second live comment history is incorrect'
);

check(
    $model->updateLifecycleComment(
        1,
        $secondId,
        'Second active comment - edited'
    ) === true,
    'Independent live comment could not still be edited'
);

check(
    $model->updateLifecycleComment(
        1,
        $firstId,
        'Should fail'
    ) === false,
    'Deleted comment was editable'
);

echo "DEVICE_ACTIVE_LIFECYCLE_COMMENT_HISTORY=PASS\n";

/* DM-BL-001 physical-device grouping schema and read model */
$model = fresh_model($dbFile, $defaultsPath);
$db = new SQLite3($dbFile);

check(
    (int)$db->querySingle(
        "SELECT COUNT(*) FROM sqlite_master " .
        "WHERE type='table' AND name='physical_devices'"
    ) === 1,
    'physical_devices table was not created'
);

check(
    (int)$db->querySingle(
        "SELECT COUNT(*) FROM sqlite_master " .
        "WHERE type='table' AND name='physical_device_memberships'"
    ) === 1,
    'physical_device_memberships table was not created'
);

$db->exec("INSERT INTO physical_devices (name) VALUES ('Test Laptop')");
$groupId = (int)$db->lastInsertRowID();

$db->exec(
    "INSERT INTO physical_device_memberships (physical_device_id,mac) VALUES " .
    "($groupId,'AA:BB:CC:DD:EE:10')," .
    "($groupId,'aa:bb:cc:dd:ee:11')"
);
$db->close();

$group = $model->getPhysicalDeviceForMac('aa:bb:cc:dd:ee:10');

check(
    is_array($group) &&
    $group['id'] === $groupId &&
    $group['name'] === 'Test Laptop',
    'Physical-device group lookup failed'
);

check(
    count($group['members']) === 2 &&
    $group['members'][0]['mac'] === 'aa:bb:cc:dd:ee:10' &&
    $group['members'][1]['mac'] === 'aa:bb:cc:dd:ee:11',
    'Physical-device active member list is wrong'
);

check(
    $model->getPhysicalDeviceForMac('aa:bb:cc:dd:ee:99') === null,
    'Ungrouped MAC unexpectedly resolved to a physical-device group'
);

$db = new SQLite3($dbFile);
$db->exec("INSERT INTO physical_devices (name) VALUES ('Other Device')");
$otherGroupId = (int)$db->lastInsertRowID();

$duplicateActive = @$db->exec(
    "INSERT INTO physical_device_memberships (physical_device_id,mac) VALUES " .
    "($otherGroupId,'aa:bb:cc:dd:ee:10')"
);

check(
    $duplicateActive === false,
    'Same MAC was allowed in two active physical-device groups'
);

$db->exec(
    "UPDATE physical_device_memberships SET removed_at=CURRENT_TIMESTAMP " .
    "WHERE physical_device_id=$groupId AND lower(trim(mac))='aa:bb:cc:dd:ee:10'"
);

check(
    (int)$db->querySingle(
        "SELECT COUNT(*) FROM physical_device_memberships " .
        "WHERE physical_device_id=$groupId " .
        "AND lower(trim(mac))='aa:bb:cc:dd:ee:10' " .
        "AND removed_at IS NOT NULL"
    ) === 1,
    'Archived physical-device membership history was not retained'
);

check(
    $db->exec(
        "INSERT INTO physical_device_memberships (physical_device_id,mac) VALUES " .
        "($otherGroupId,'aa:bb:cc:dd:ee:10')"
    ) === true,
    'Archived membership prevented a later active membership'
);

$db->close();

$oldGroup = $model->getPhysicalDeviceForMac('aa:bb:cc:dd:ee:11');
$newGroup = $model->getPhysicalDeviceForMac('aa:bb:cc:dd:ee:10');

check(
    is_array($oldGroup) &&
    $oldGroup['id'] === $groupId &&
    count($oldGroup['members']) === 1 &&
    $oldGroup['members'][0]['mac'] === 'aa:bb:cc:dd:ee:11',
    'Archived membership remained in the old active member list'
);

check(
    is_array($newGroup) &&
    $newGroup['id'] === $otherGroupId &&
    count($newGroup['members']) === 1 &&
    $newGroup['members'][0]['mac'] === 'aa:bb:cc:dd:ee:10',
    'Re-added MAC did not resolve to its new active group'
);

echo "DEVICE_PHYSICAL_GROUP_READ_MODEL=PASS\n";

/* DM-BL-001 physical-device grouping write model */
$model = fresh_model($dbFile, $defaultsPath);
$db = new SQLite3($dbFile);

$db->exec(
    "INSERT INTO devices " .
    "(mac,ip,first_seen,last_seen,is_active,return_pending) VALUES " .
    "('aa:bb:cc:dd:ee:20','192.0.2.20',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,1,0)," .
    "('aa:bb:cc:dd:ee:21','192.0.2.21',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,1,1)"
);

$db->exec(
    "INSERT INTO device_lifecycles " .
    "(mac,status,first_seen,last_seen) VALUES " .
    "('aa:bb:cc:dd:ee:22','archived','2026-01-01 10:00:00','2026-02-01 10:00:00')"
);

$db->close();

$groupId = $model->createPhysicalDevice(
    'Test Workstation',
    'AA:BB:CC:DD:EE:20'
);

check($groupId > 0, 'Physical-device group was not created');

$group = $model->getPhysicalDeviceForMac('aa:bb:cc:dd:ee:20');
check(
    is_array($group) &&
    $group['id'] === $groupId &&
    $group['name'] === 'Test Workstation' &&
    count($group['members']) === 1 &&
    $group['members'][0]['mac'] === 'aa:bb:cc:dd:ee:20',
    'Created physical-device group is incorrect'
);

check(
    $model->linkPhysicalDeviceIdentity(
        $groupId,
        'AA:BB:CC:DD:EE:21'
    ) === true,
    'Known current MAC could not be linked'
);

check(
    $model->linkPhysicalDeviceIdentity(
        $groupId,
        'aa:bb:cc:dd:ee:22'
    ) === true,
    'Known historical MAC could not be linked'
);

$group = $model->getPhysicalDeviceForMac('aa:bb:cc:dd:ee:21');
check(
    is_array($group) &&
    $group['id'] === $groupId &&
    count($group['members']) === 3,
    'Linked identities were not returned as one physical device'
);

check(
    $model->linkPhysicalDeviceIdentity(
        $groupId,
        'aa:bb:cc:dd:ee:21'
    ) === false,
    'Duplicate active physical-device membership was accepted'
);

check(
    $model->linkPhysicalDeviceIdentity(
        $groupId,
        'aa:bb:cc:dd:ee:99'
    ) === false,
    'Unknown MAC identity was accepted'
);

check(
    $model->linkPhysicalDeviceIdentity(
        9999,
        'aa:bb:cc:dd:ee:21'
    ) === false,
    'Unknown physical-device group was accepted'
);

check(
    $model->createPhysicalDevice(
        'Duplicate Group',
        'aa:bb:cc:dd:ee:21'
    ) === 0,
    'A second active group was created for an already-grouped MAC'
);

$db = new SQLite3($dbFile);
check(
    (int)$db->querySingle(
        "SELECT COUNT(*) FROM physical_devices"
    ) === 1,
    'Failed group creation left an orphan physical-device row'
);

check(
    $db->querySingle(
        "SELECT return_pending FROM devices " .
        "WHERE mac='aa:bb:cc:dd:ee:21'"
    ) == 1,
    'Grouping write changed lifecycle return_pending state'
);
$db->close();

check(
    $model->removePhysicalDeviceIdentity(
        $groupId,
        'aa:bb:cc:dd:ee:20'
    ) === true,
    'Active physical-device membership could not be removed'
);

check(
    $model->getPhysicalDeviceForMac('aa:bb:cc:dd:ee:20') === null,
    'Removed MAC still resolved to its old active group'
);

$db = new SQLite3($dbFile);
check(
    (int)$db->querySingle(
        "SELECT COUNT(*) FROM physical_device_memberships " .
        "WHERE physical_device_id=$groupId " .
        "AND lower(trim(mac))='aa:bb:cc:dd:ee:20' " .
        "AND removed_at IS NOT NULL"
    ) === 1,
    'Removed physical-device membership history was not retained'
);
$db->close();

$newGroupId = $model->createPhysicalDevice(
    'Replacement Group',
    'aa:bb:cc:dd:ee:20'
);

check(
    $newGroupId > $groupId,
    'Removed MAC could not be explicitly grouped again'
);

$newGroup = $model->getPhysicalDeviceForMac('aa:bb:cc:dd:ee:20');
check(
    is_array($newGroup) &&
    $newGroup['id'] === $newGroupId &&
    count($newGroup['members']) === 1,
    'Regrouped MAC did not resolve to its new active group'
);

$oldGroup = $model->getPhysicalDeviceForMac('aa:bb:cc:dd:ee:21');
check(
    is_array($oldGroup) &&
    $oldGroup['id'] === $groupId &&
    count($oldGroup['members']) === 2,
    'Removing one identity changed other active group memberships'
);

check(
    $model->removePhysicalDeviceIdentity(
        $groupId,
        'aa:bb:cc:dd:ee:20'
    ) === false,
    'Already-removed membership was removed twice'
);

echo "DEVICE_PHYSICAL_GROUP_WRITE_MODEL=PASS\n";

echo "DEVICE_LIFECYCLE_ACTIONS_REGRESSION=PASS\n";
