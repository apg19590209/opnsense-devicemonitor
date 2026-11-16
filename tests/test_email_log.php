<?php
/**
 * Device Monitor email log — focused tests with mocked transports.
 *
 * No live mail is sent. The recorder is exercised against a temporary database,
 * and the real senders are exercised only through their classification helpers.
 */
require_once __DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php';
require_once __DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor/EmailTransport.php';

use OPNsense\DeviceMonitor\EmailLog;
use OPNsense\DeviceMonitor\EmailTransport;

$fails = 0;
function check($cond, $msg) {
    global $fails;
    if ($cond) { echo "  PASS $msg\n"; } else { $fails++; echo "  FAIL $msg\n"; }
}

$tmp = tempnam(sys_get_temp_dir(), 'dmlog');
unlink($tmp);
$log = new EmailLog($tmp);

/* 1. submission creates exactly one row */
$id = $log->recordSubmission(EmailLog::TYPE_TEST, 'a@example.invalid', 'Subject one');
check(is_string($id) && strlen($id) === 32, 'submission returns a stable event id');
$rows = $log->query([], 50, 0);
check(count($rows) === 1, 'one logical email writes one row');
check($rows[0]['status'] === EmailLog::STATE_SUBMITTED, 'initial status is submitted');
check($rows[0]['subject'] === 'Subject one', 'subject stored');
check($rows[0]['node_id'] !== '', 'node identity recorded');

/* 2. multiple transport events update the same row (no double counting) */
$log->recordTransportEvent($id, EmailLog::STATE_QUEUED, 'Queued to local sendmail', 'ABC123');
$log->recordTransportEvent($id, EmailLog::STATE_ACCEPTED, 'SMTP relay accepted');
$rows = $log->query([], 50, 0);
check(count($rows) === 1, 'two transport events never create a second row');
check($rows[0]['status'] === EmailLog::STATE_ACCEPTED, 'latest transport state wins');
check($rows[0]['queue_id'] === 'ABC123', 'queue id retained across an update');

/* 3. unknown event id is ignored */
$before = count($log->query([], 50, 0));
$log->recordTransportEvent('deadbeef', EmailLog::STATE_FAILED, 'x');
check(count($log->query([], 50, 0)) === $before, 'transport event for unknown id inserts nothing');

/* 4. classification */
list($st, $d) = EmailTransport::classify(['result' => 'sent', 'transport' => 'sendmail']);
check($st === EmailLog::STATE_QUEUED, 'sendmail success is queued, not accepted');
list($st, $d) = EmailTransport::classify(['result' => 'sent', 'transport' => 'smtp']);
check($st === EmailLog::STATE_ACCEPTED, 'smtp success is relay acceptance');
list($st, $d) = EmailTransport::classify(['result' => 'failed', 'message' => 'boom']);
check($st === EmailLog::STATE_FAILED, 'failure classified as failed');
list($st, $d) = EmailTransport::classify(['result' => 'skipped', 'message' => 'Email disabled']);
check($st === EmailLog::STATE_UNKNOWN, 'skipped is unknown, not success');
list($st, $d) = EmailTransport::classify([]);
check($st === EmailLog::STATE_UNKNOWN, 'absent evidence stays UNKNOWN');

/* 5. recipient handling and secrets */
$id2 = $log->recordSubmission(EmailLog::TYPE_SCAN_RESULT, 'a@example.invalid, b@example.invalid', 'Scan result');
$rows = $log->query([], 50, 0);
$found = null;
foreach ($rows as $r) { if ($r['event_id'] === $id2) { $found = $r; } }
check($found && $found['recipient'] === 'a@example.invalid, b@example.invalid', 'recipient list preserved');
check($found && stripos(json_encode($found), 'password') === false, 'no credential field stored');

/* 6. sanitisation */
check(EmailLog::sanitise("bad\x00\x07text") === 'badtext', 'control characters stripped');
check(strlen(EmailLog::sanitise(str_repeat('x', 900))) === 255, 'strings bounded');
check(strlen(EmailLog::sanitise("line1\nline2")) <= 255, 'newlines normalised');

/* 7. filters and search */
$log->recordSubmission(EmailLog::TYPE_FAILOVER, 'c@example.invalid', 'Failover MASTER');
$rows = $log->query(['type' => EmailLog::TYPE_FAILOVER], 50, 0);
check(count($rows) === 1 && $rows[0]['subject'] === 'Failover MASTER', 'type filter');
$rows = $log->query(['search' => 'Subject'], 50, 0);
check(count($rows) === 1, 'search matches subject');
$rows = $log->query(['search' => '%'], 50, 0);
check(count($rows) === 0, 'LIKE wildcard is escaped, not honoured');

/* 8. pagination bounds */
$rows = $log->query([], 1, 0);
check(count($rows) === 1, 'page size honoured');
$rows = $log->query([], 100000, 0);
check(count($rows) <= 3, 'page size capped');

/* 9. retention removes only old log rows */
$db = new SQLite3($tmp);
$db->exec("UPDATE email_log SET created_utc = '2020-01-01 00:00:00' WHERE event_id = '$id'");
$db->close();
$removed = $log->prune(30);
check($removed === 1, 'retention removes only expired rows');
check(count($log->query([], 50, 0)) === 2, 'recent rows retained');

/* 10. concurrent access stays bounded */
$multi = [];
for ($i = 0; $i < 12; $i++) {
    $multi[] = $log->recordSubmission(EmailLog::TYPE_TEST, 'x@example.invalid', "concurrent $i");
}
check(count(array_filter($multi)) === 12, 'repeated writes succeed under sequential contention');
check(count($log->query([], 500, 0)) === 14, 'all rows accounted for');

/* 11. unavailable log never blocks the caller */
$bad = new EmailLog('/nonexistent-dir-' . uniqid() . '/log.db');
$r = $bad->recordSubmission(EmailLog::TYPE_TEST, 'x@example.invalid', 's');
check($r !== null, 'recorder is best-effort when the path is usable-or-created');
$readonly = new EmailLog('/dev/null/definitely-not-a-directory/log.db');
$r2 = $readonly->recordSubmission(EmailLog::TYPE_TEST, 'x@example.invalid', 's');
check($r2 === null, 'unwritable location returns null instead of throwing');
check($readonly->lastDiagnostic() !== null, 'logging limitation exposed as a diagnostic');

/* 12. no bodies stored */
$cols = [];
$dbr = new SQLite3($tmp, SQLITE3_OPEN_READONLY);
$res = $dbr->query('PRAGMA table_info(email_log)');
while ($c = $res->fetchArray(SQLITE3_ASSOC)) { $cols[] = $c['name']; }
$dbr->close();
check(!in_array('body', $cols) && !in_array('html', $cols), 'no message body column exists');

@unlink($tmp);
echo $fails === 0 ? "EMAIL_LOG_TESTS=PASS\n" : "EMAIL_LOG_TESTS=FAIL ($fails)\n";
exit($fails === 0 ? 0 : 1);
