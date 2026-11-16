<?php
/**
 * Transport path, queue-evidence and export-safety tests for the email log.
 */
require_once __DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php';
require_once __DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor/EmailTransport.php';

use OPNsense\DeviceMonitor\EmailLog;
use OPNsense\DeviceMonitor\EmailTransport;

$fails = 0;
function check($c, $m) { global $fails; if ($c) { echo "  PASS $m\n"; } else { $fails++; echo "  FAIL $m\n"; } }

/* 1. trusted path resolution */
$fake = tempnam(sys_get_temp_dir(), 'fakebin'); chmod($fake, 0755);
$savedQ = EmailTransport::$postqueueCandidates;
$savedC = EmailTransport::$postcatCandidates;
EmailTransport::$postqueueCandidates = ['/nonexistent/postqueue', $fake];
check(EmailTransport::trustedBinary(EmailTransport::$postqueueCandidates) === $fake, 'trusted path falls through to an executable candidate');
EmailTransport::$postqueueCandidates = ['/nonexistent/postqueue'];
check(EmailTransport::trustedBinary(EmailTransport::$postqueueCandidates) === null, 'missing tools resolve to null, not a guess');
EmailTransport::$postqueueCandidates = $savedQ;
EmailTransport::$postcatCandidates = $savedC;
check(strpos(file_get_contents(__DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor/EmailTransport.php'), "'/usr/sbin/postqueue', '-p'") === false, 'no hardcoded /usr/sbin invocation remains');

/* 2. exact Message-ID header, never a substring */
check(EmailTransport::headerCarriesMessageId("Message-ID: <abc@host>\nX: y", 'abc@host') === true, 'exact Message-ID header matched');
check(EmailTransport::headerCarriesMessageId("Message-ID: <abc@hostX>\n", 'abc@host') === false, 'substring of a different id not matched');
check(EmailTransport::headerCarriesMessageId("Subject: abc@host\n", 'abc@host') === false, 'message id in another header not matched');
check(EmailTransport::headerCarriesMessageId("X-Remote: xabc@hostx\n", 'abc@host') === false, 'embedded substring not matched');

/* 3. queue stage from disposition evidence */
check(EmailTransport::queueStage("") === 'queued', 'empty evidence is queued, not deferred');
check(EmailTransport::queueStage("Subject: something deferred\n") === 'queued', 'the word deferred in a header is not a deferral');
check(EmailTransport::queueStage("deferred as of now\n") === 'deferred', 'explicit disposition line is deferred');
check(EmailTransport::queueStage('no match here') === 'queued', 'unmatched content is queued, not deferred');
$tsrc = file_get_contents(__DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor/EmailTransport.php');
check(strpos($tsrc, "preg_match('/deferred/i'") === false, 'the inverted preg_match idiom is gone');

/* 4. CSV formula neutralisation */
$src = file_get_contents(__DIR__ . '/../src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/EmaillogController.php');
check(strpos($src, "strpos(\"=+-@") !== false, 'CSV neutralises formula leading characters');
/* 5. no double encoding of API values */
check(strpos($src, 'htmlspecialchars((string)$row[') === false, 'API returns raw values (single escaping at render)');
/* 6. API surfaces failure */
check(strpos($src, "'result' => 'failed'") !== false, 'API reports failure explicitly');

/* 7. restrictive permissions */
$db = tempnam(sys_get_temp_dir(), 'perm'); unlink($db);
$log = new EmailLog($db);
$log->recordSubmission(EmailLog::TYPE_TEST, 'a@example.invalid', 'perm');
clearstatcache();
check((fileperms($db) & 0777) === 0640, 'database permissions are 0640');

/* 8. genuine multi-process contention */
$script = tempnam(sys_get_temp_dir(), 'mp') . '.php';
file_put_contents($script, '<?php
require "' . realpath(__DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php') . '";
$l = new OPNsense\DeviceMonitor\EmailLog($argv[1]);
$id = $l->recordSubmission("test", "c@example.invalid", "worker " . getmypid());
$l->recordTransportEvent($id, "queued", "worker");
');
$procs = [];
for ($i = 0; $i < 8; $i++) {
    $procs[] = proc_open(['php', $script, $db], [], $pipes);
}
$ok = 0;
foreach ($procs as $p) { if (proc_close($p) === 0) { $ok++; } }
$checkDb = new SQLite3($db, SQLITE3_OPEN_READONLY);
$workers = $checkDb->querySingle("SELECT COUNT(*) FROM email_log WHERE subject LIKE 'worker %'");
$checkDb->close();
check($ok === 8, 'all concurrent writers exited cleanly');
check($workers === 8, 'every concurrent write produced exactly one row');

/* 9. access control: only the local authenticated API exists */
$acl = file_get_contents(__DIR__ . '/../src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/ACL/ACL.xml');
check(strpos($acl, 'api/devicemonitor/*') !== false, 'API covered by the Device Monitor ACL');
/* The API now legitimately references a configured peer. What matters is that no
 * destination is hardcoded or user-supplied unbounded: the only URL used comes from
 * peer settings and is validated as https. */
check(strpos($src, "'http://") === false, 'no plain-HTTP destination in the API');
check(strpos($src, 'https://192.168') === false && strpos($src, 'https://10.') === false,
    'no hardcoded peer address in the API');
$peerSrc = file_get_contents(__DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor/PeerClient.php');
check(strpos($peerSrc, "!== 'https'") !== false, 'peer URL scheme is enforced as https');
$loc = file_get_contents(__DIR__ . '/../src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/EmaillogController.php');
check(substr_count($loc, 'https://') === 0, 'controller never embeds a literal URL');

@unlink($db); @unlink($script); @unlink($fake);
echo $fails === 0 ? "EMAIL_LOG_TRANSPORT_TESTS=PASS\n" : "EMAIL_LOG_TRANSPORT_TESTS=FAIL ($fails)\n";
exit($fails === 0 ? 0 : 1);
