<?php
/**
 * Bulk soft deletion and restoration on temporary databases. No live data is touched.
 */
require_once __DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php';

use OPNsense\DeviceMonitor\EmailLog;

$fails = 0;
function check($c, $m) { global $fails; if ($c) { echo "  PASS $m\n"; } else { $fails++; echo "  FAIL $m\n"; } }

$db = tempnam(sys_get_temp_dir(), 'dmbulk'); unlink($db);
$log = new EmailLog($db);
$a = $log->recordSubmission(EmailLog::TYPE_TEST, 'a@example.invalid', 'Alpha');
$b = $log->recordSubmission(EmailLog::TYPE_SERVICE, 'b@example.invalid', 'Beta');
$c = $log->recordSubmission(EmailLog::TYPE_TEST, 'c@example.invalid', 'Gamma');
$log->recordContent($a, '<p>kept</p>', 'text');
$log->recordTransportEvent($a, 'accepted', 'relay ok');

/* 1. bulk delete reports the real count and ignores junk */
check($log->markDeletedMany([$a, $b, 'not-an-id', '00000000000000000000000000000000']) === 2,
    'bulk delete affects exactly the valid, active entries');
check(count($log->query([])) === 1, 'one entry remains active');
check(count($log->query(['visibility' => 'deleted'])) === 2, 'both selected entries are deleted');

/* 2. content, status and timeline survive */
$row = $log->messageDetail($a);
check($row['content_text'] === '<p>kept</p>' && $row['status'] === 'accepted', 'content and status retained');
check(count($row['timeline']) === 2, 'timeline retained (accepted event plus the bulk delete event)');

/* 3. repeated delete does not double count */
check($log->markDeletedMany([$a]) === 0, 'deleting an already deleted entry affects nothing');

/* 4. restore many */
check($log->restoreMany([$a, $b, 'junk-id']) === 2, 'restore affects the two deleted entries');
check(count($log->query([])) === 3, 'all three are active again');

/* 5. filtered scope is irrelevant to delete-all: everything active goes */
check($log->markAllDeleted() === 3, 'delete all affects every active entry regardless of filters');
check(count($log->query([])) === 0, 'no entry remains in the active view');
check(count($log->query(['visibility' => 'deleted'])) === 3, 'all entries are restorable');
check(count($log->query(['visibility' => 'all'])) === 3, 'no entry was destroyed');

/* 6. retention still applies to bulk-deleted entries */
$old = new SQLite3($db);
$old->exec("UPDATE email_log SET created_utc = '2026-01-01 00:00:00'");
$old->close();
check($log->prune(EmailLog::RETENTION_DAYS) >= 1, 'bulk-deleted entries expire under normal retention');

@unlink($db);
echo $fails === 0 ? "EMAIL_LOG_BULK_TESTS=PASS\n" : "EMAIL_LOG_BULK_TESTS=FAIL ($fails)\n";
exit($fails === 0 ? 0 : 1);
