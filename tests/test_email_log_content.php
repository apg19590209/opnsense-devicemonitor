<?php
/**
 * Message content capture, redaction, truncation, upgrade and detail shape.
 * No mail is sent and no production database is touched.
 */
require_once __DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php';

use OPNsense\DeviceMonitor\EmailLog;

$fails = 0;
function check($c, $m) { global $fails; if ($c) { echo "  PASS $m\n"; } else { $fails++; echo "  FAIL $m\n"; } }

$db = tempnam(sys_get_temp_dir(), 'dmcontent'); unlink($db);
$log = new EmailLog($db);

/* 1. HTML is converted to readable text, never stored as markup */
$html = '<html><body><h1>Device Monitor</h1><p>New device <b>aa:bb</b> online.</p>'
      . '<img src="http://tracker.invalid/pixel.png"><script>alert(1)</script>'
      . '<style>.x{}</style></body></html>';
$id = $log->recordSubmission(EmailLog::TYPE_TEST, 'a@example.invalid', 'Subject', null, null, null, null, null, $html, 'html');
$row = $log->messageDetail($id);
check(strpos($row['content_text'], 'New device aa:bb online.') !== false, 'readable text derived from HTML');
check(strpos($row['content_text'], '<') === false, 'no markup stored');
check(strpos($row['content_text'], 'tracker.invalid') === false, 'image source not retained');
check(strpos($row['content_text'], 'alert(1)') === false, 'script body discarded');
check($row['content_format'] === 'html', 'format recorded');

/* 2. plain-text bodies preserved with newlines */
$plain = "Line one\nLine two\n\nLine four";
$id2 = $log->recordSubmission(EmailLog::TYPE_SERVICE, 'a@example.invalid', 'Plain', null, null, null, null, null, $plain, 'text');
$row2 = $log->messageDetail($id2);
check($row2['content_text'] === $plain, 'plain text preserved verbatim');
check($row2['content_format'] === 'text', 'text format recorded');

/* 3. truncation is bounded and flagged */
$big = str_repeat("x", 30000);
$id3 = $log->recordSubmission(EmailLog::TYPE_TEST, 'a@example.invalid', 'Big', null, null, null, null, null, $big, 'text');
$row3 = $log->messageDetail($id3);
check(strlen($row3['content_text']) === EmailLog::MAX_CONTENT, 'content bounded');
check((int)$row3['content_truncated'] === 1, 'truncation flagged');

/* 4. no content stored for older-style rows */
$id4 = $log->recordSubmission(EmailLog::TYPE_TEST, 'a@example.invalid', 'No body');
$row4 = $log->messageDetail($id4);
check($row4['content_text'] === null, 'absent body stored as NULL, not fabricated');
check($log->messageDetail($id4)['content_text'] === null, 'detail keeps NULL (UI shows unavailable)');

/* 5. recordContent is fail-open and does not duplicate rows */
$log->recordContent($id4, '<p>late body</p>', 'html');
$after = $log->messageDetail($id4);
check(strpos($after['content_text'], 'late body') !== false, 'late content attached to the same row');
$count = (new SQLite3($db))->querySingle('SELECT COUNT(*) FROM email_log');
check((int)$count === 4, 'no extra rows created');

/* 6. content is not returned in the list payload */
$rows = $log->query([], 10, 0);
$hasContentKeys = false;
foreach ($rows as $r) { if (array_key_exists('content_text', $r)) { $hasContentKeys = true; } }
check(!$hasContentKeys, 'list payload omits the body');

/* 7. versioned upgrade: an old database gains the columns, rows survive */
$old = tempnam(sys_get_temp_dir(), 'dmold'); unlink($old);
$c = new SQLite3($old);
$c->exec('CREATE TABLE email_log (id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL UNIQUE,
    created_utc DATETIME NOT NULL, updated_utc DATETIME NOT NULL, node_id TEXT NOT NULL,
    node_ip TEXT NOT NULL DEFAULT "", node_role TEXT NOT NULL DEFAULT "unknown",
    notification_type TEXT NOT NULL, recipient TEXT NOT NULL DEFAULT "", subject TEXT NOT NULL DEFAULT "",
    status TEXT NOT NULL DEFAULT "unknown", status_detail TEXT NOT NULL DEFAULT "",
    transport TEXT NOT NULL DEFAULT "", queue_id TEXT NOT NULL DEFAULT "",
    message_id TEXT NOT NULL DEFAULT "")');
$c->exec("INSERT INTO email_log (event_id, created_utc, updated_utc, node_id, notification_type, subject, status)
    VALUES ('legacy1', '2026-11-01 00:00:00', '2026-11-01 00:00:00', 'n', 'test', 'old', 'submitted')");
$c->close();
$oldLog = new OPNsense\DeviceMonitor\EmailLog($old);
$legacy = $oldLog->messageDetail('legacy1');
check($legacy !== null && $legacy['subject'] === 'old', 'existing row preserved through upgrade');
check(array_key_exists('content_text', $legacy) && $legacy['content_text'] === null, 'upgrade added content column with NULL');
check((new SQLite3($old))->querySingle('PRAGMA user_version') == 3, 'schema version recorded');
$oldLog->messageDetail('legacy1');
check((new SQLite3($old))->querySingle('PRAGMA user_version') == 3, 'upgrade is repeatable');
check(array_key_exists('deleted_utc', $legacy) && $legacy['deleted_utc'] === '', 'upgrade added the visibility column with existing rows active');
check((new SQLite3($old))->querySingle("SELECT COUNT(*) FROM pragma_table_info('email_log') WHERE name='deleted_utc'") == 1, 'visibility column added exactly once');

/* 8. no credential columns exist */
$cols = [];
$res = (new SQLite3($db, SQLITE3_OPEN_READONLY))->query('PRAGMA table_info(email_log)');
while ($r = $res->fetchArray(SQLITE3_ASSOC)) { $cols[] = $r['name']; }
foreach (['password', 'smtp_password', 'auth'] as $bad) {
    check(!in_array($bad, $cols, true), "no $bad column");
}

@unlink($db); @unlink($old);
echo $fails === 0 ? "EMAIL_LOG_CONTENT_TESTS=PASS\n" : "EMAIL_LOG_CONTENT_TESTS=FAIL ($fails)\n";
exit($fails === 0 ? 0 : 1);
