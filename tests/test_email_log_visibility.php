<?php
/**
 * Soft deletion and visibility, on temporary databases only.
 *
 * Deletion must change nothing except the visibility marker: content, event id,
 * transport status and the complete timeline stay, the 30-day retention policy is
 * unchanged, and search/type/status/visibility bound the list and the export the
 * same way.
 */
require_once __DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php';

use OPNsense\DeviceMonitor\EmailLog;

$fails = 0;
function check($c, $m) { global $fails; if ($c) { echo "  PASS $m\n"; } else { $fails++; echo "  FAIL $m\n"; } }

$db = tempnam(sys_get_temp_dir(), 'dmvis'); unlink($db);
$log = new EmailLog($db);
$a = $log->recordSubmission(EmailLog::TYPE_TEST, 'a@example.invalid', 'Alpha kept');
$b = $log->recordSubmission(EmailLog::TYPE_NEW_DEVICE, 'b@example.invalid', 'Beta device');
$c = $log->recordSubmission(EmailLog::TYPE_TEST, 'c@example.invalid', 'Gamma kept');
$log->recordContent($a, '<p>Body stays</p><table><tr><td>Server:</td><td>n</td></tr></table>', 'html');
$log->recordTransportEvent($a, 'queued', 'first try', null, 'sender', 'QID1');
$log->recordTransportEvent($a, 'accepted', 'relay ok', null, 'observer', 'QID2');
$log->recordTransportEvent($b, 'failed', 'refused');
$before = $log->messageDetail($a);

/* 1. delete sets the marker only */
check($log->markDeleted($a) === true, 'delete succeeds');
$after = $log->messageDetail($a);
check($after['event_id'] === $a, 'event id retained');
check($after['content_text'] === $before['content_text'] && $after['content_text'] !== '', 'message content retained');
check($after['status'] === $before['status'] && $after['queue_id'] === $before['queue_id'], 'transport status and queue id retained');
check(count($after['timeline']) === count($before['timeline']) && count($after['timeline']) === 2, 'complete timeline retained');
check($after['deleted_utc'] !== '', 'visibility marker set');
$ev = (new SQLite3($db))->querySingle("SELECT COUNT(*) FROM email_log_events WHERE event_id='$a'");
check((int)$ev === 2, 'timeline rows untouched in storage');

/* 2. visibility filters, consistently for list and export */
check(count($log->query([])) === 2, 'default view is Active');
check(count($log->query(['visibility' => 'active'])) === 2, 'explicit Active');
check(count($log->query(['visibility' => 'deleted'])) === 1, 'Deleted view');
check(count($log->query(['visibility' => 'all'])) === 3, 'All view');
check(count($log->query(['visibility' => 'bogus'])) === 2, 'unknown visibility falls back to Active');
check(count($log->exportRows([])) === 2 && count($log->exportRows(['visibility' => 'deleted'])) === 1
    && count($log->exportRows(['visibility' => 'all'])) === 3, 'export follows visibility');
check(count($log->query(['search' => 'kept'])) === 1 && count($log->query(['search' => 'kept', 'visibility' => 'deleted'])) === 1,
    'search and visibility combine (the deleted Alpha is only in Deleted)');
check(count($log->query(['search' => 'kept', 'visibility' => 'all'])) === 2, 'search over All finds both');
check(count($log->query(['type' => 'new_device'])) === 1 && count($log->query(['type' => 'test'])) === 1,
    'type filter applies to Active');
check(count($log->query(['status' => 'failed'])) === 1 && count($log->query(['status' => 'accepted'])) === 0,
    'status filter applies; a deleted accepted row is not in Active');
check(count($log->query(['status' => 'accepted', 'visibility' => 'deleted'])) === 1, 'status filter in Deleted view');

/* 3. filtered pagination */
$page1 = $log->query(['visibility' => 'all'], 2, 0);
$page2 = $log->query(['visibility' => 'all'], 2, 2);
check(count($page1) === 2 && count($page2) === 1, 'pagination follows the filtered set');
$ids = array_merge(array_column($page1, 'event_id'), array_column($page2, 'event_id'));
check(count(array_unique($ids)) === 3, 'pages never overlap');

/* 4. repeated and invalid operations */
check($log->markDeleted($a) === null, 'second delete is refused');
check($log->restore($b) === null, 'restoring an active entry is refused');
check($log->markDeleted('not-an-id') === null, 'invalid reference refused');
check($log->markDeleted('00000000000000000000000000000000') === null, 'unknown entry refused');

/* 5. restore returns the entry unchanged */
check($log->restore($a) === true, 'restore succeeds');
$restored = $log->messageDetail($a);
check($restored['deleted_utc'] === '' && count($log->query([])) === 3, 'restored row is Active again');
check($restored['content_text'] === $before['content_text'] && count($restored['timeline']) === 2, 'restore keeps content and history');

/* 6. retention is unchanged: deleted entries expire with everything else */
$log->markDeleted($b);
$old = (new SQLite3($db));
$old->exec("UPDATE email_log SET created_utc = '2026-01-01 00:00:00' WHERE event_id = '$b'");
$old->close();
$removed = $log->prune(EmailLog::RETENTION_DAYS);
check($removed >= 1, 'an old deleted entry is pruned by the normal retention');
check($log->messageDetail($b) === null, 'deleted entry is not archived beyond retention');
check((new SQLite3($db))->querySingle("SELECT COUNT(*) FROM email_log_events WHERE event_id='$b'") == 0,
    'its timeline rows expire with it');

/* 7. schema upgrade is additive and repeatable */
$oldDb = tempnam(sys_get_temp_dir(), 'dmv3'); unlink($oldDb);
$seed = new SQLite3($oldDb);
$seed->exec('CREATE TABLE email_log (id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL UNIQUE,
    created_utc DATETIME NOT NULL, updated_utc DATETIME NOT NULL, node_id TEXT NOT NULL,
    node_ip TEXT NOT NULL DEFAULT "", node_role TEXT NOT NULL DEFAULT "unknown",
    notification_type TEXT NOT NULL, recipient TEXT NOT NULL DEFAULT "", subject TEXT NOT NULL DEFAULT "",
    status TEXT NOT NULL DEFAULT "unknown", status_detail TEXT NOT NULL DEFAULT "",
    transport TEXT NOT NULL DEFAULT "", queue_id TEXT NOT NULL DEFAULT "", message_id TEXT NOT NULL DEFAULT "",
    content_text TEXT, content_format TEXT NOT NULL DEFAULT "", content_truncated INTEGER NOT NULL DEFAULT 0)');
$seed->exec('PRAGMA user_version = 2');
$seed->exec("INSERT INTO email_log (event_id, created_utc, updated_utc, node_id, notification_type, subject, status)
    VALUES ('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', '2026-11-01 00:00:00', '2026-11-01 00:00:00', 'n', 'test', 'legacy', 'submitted')");
$seed->close();
$upgraded = new EmailLog($oldDb);
check(count($upgraded->query([])) === 1, 'existing rows stay active after the upgrade');
check(count($upgraded->query(['visibility' => 'deleted'])) === 0, 'nothing is hidden by the upgrade');
check((new SQLite3($oldDb))->querySingle('PRAGMA user_version') == 3, 'version 3 recorded');
$upgraded->prune();
check((new SQLite3($oldDb))->querySingle('PRAGMA user_version') == 3, 'upgrade is repeatable');

@unlink($db);
@unlink($oldDb);
echo $fails === 0 ? "EMAIL_LOG_VISIBILITY_TESTS=PASS\n" : "EMAIL_LOG_VISIBILITY_TESTS=FAIL ($fails)\n";
exit($fails === 0 ? 0 : 1);
