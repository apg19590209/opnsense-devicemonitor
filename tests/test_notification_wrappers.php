<?php
/**
 * Real NotificationHandler wrapper tests with mocked transports.
 *
 * Proves that logging never changes what the senders return or throw, and never
 * causes a duplicate send. No live mail is produced.
 */
require_once __DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php';

$fails = 0;
function check($c, $m) { global $fails; if ($c) { echo "  PASS $m\n"; } else { $fails++; echo "  FAIL $m\n"; } }

/* Load NotificationHandler with its model/require path satisfied by thin stubs so
 * the real class body runs unmodified. */
$tmpDb = tempnam(sys_get_temp_dir(), 'dmwrap'); unlink($tmpDb);
$log = null; // bound to $tmpDb after the handler is loaded
$stubs = tempnam(sys_get_temp_dir(), 'dmstub'); unlink($stubs);

/* The handler loads the model from DM_MODEL_PATH; point it at a stub file. */
$modelStub = tempnam(sys_get_temp_dir(), 'dmmodel') . '.php';
file_put_contents($modelStub, '<?php namespace OPNsense\\DeviceMonitor; class DeviceMonitor {
    public static $config = ["email_enabled" => "1", "email_to" => "ops@example.invalid",
        "email_from" => "dm@example.invalid", "email_method" => "sendmail"];
    public function getConfig() { return self::$config; }
}');
putenv('DM_MODEL_PATH=' . $modelStub);
putenv('DM_LIB_DIR=' . realpath(__DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor'));
require_once __DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor/NotificationHandler.php';

/* Bind the recorder to a temporary database BEFORE any wrapper runs, so this
 * suite can never write fixture rows into a host's real email log. */
$log = new OPNsense\DeviceMonitor\EmailLog($tmpDb);
OPNsense\DeviceMonitor\EmailLog::setInstance($log);

class TestableHandler extends NotificationHandler {
    public $calls = 0;
    public $reply;
    public function setReply($r) { $this->reply = $r; }
    protected function _sendCustomEmail($subject, $html, $messageId = null) {
        $this->calls++;
        if ($this->reply instanceof Throwable) { throw $this->reply; }
        return $this->reply;
    }
    protected function _sendEmail($is_test = false, $messageId = null) {
        $this->calls++;
        if ($this->reply instanceof Throwable) { throw $this->reply; }
        return $this->reply;
    }
}

/* Successful send: original return value preserved, exactly one send. */
$h = new TestableHandler();
$expected = ['result' => 'sent', 'message' => 'ok', 'transport' => 'sendmail'];
$h->setReply($expected);
$got = $h->sendCustomEmail('Subj', '<p>x</p>', OPNsense\DeviceMonitor\EmailLog::TYPE_TEST);
check($got === $expected, 'success: original return value preserved verbatim');
check($h->calls === 1, 'success: exactly one send');

/* Failed transport: failure result preserved, one send. */
$h = new TestableHandler();
$expected = ['result' => 'failed', 'message' => 'boom', 'transport' => 'sendmail'];
$h->setReply($expected);
check($h->sendCustomEmail('S', 'b') === $expected, 'failure: original result preserved');
check($h->calls === 1, 'failure: exactly one send');

/* Skipped transport: preserved. */
$h = new TestableHandler();
$expected = ['result' => 'skipped', 'message' => 'Email disabled'];
$h->setReply($expected);
check($h->sendCustomEmail('S', 'b') === $expected, 'skipped: original result preserved');

/* Exception propagates unchanged, and is sent once. */
$h = new TestableHandler();
$h->setReply(new RuntimeException('transport exploded'));
$thrown = null;
try { $h->sendCustomEmail('S', 'b'); } catch (Throwable $e) { $thrown = $e; }
check($thrown instanceof RuntimeException && $thrown->getMessage() === 'transport exploded', 'exception survives logging');
check($h->calls === 1, 'exception: exactly one send');

/* Logging unavailable: send still happens and returns the same value. */
$broken = new OPNsense\DeviceMonitor\EmailLog('/dev/null/nope/log.db');
OPNsense\DeviceMonitor\EmailLog::setInstance($broken);
$h = new TestableHandler();
$expected = ['result' => 'sent', 'message' => 'ok'];
$h->setReply($expected);
check($h->sendCustomEmail('S', 'b') === $expected, 'logging failure: delivery unaffected');
check($h->calls === 1, 'logging failure: no duplicate send');

/* sendEmail() wrapper: test and real modes preserved. */
OPNsense\DeviceMonitor\EmailLog::setInstance($log);
$h = new TestableHandler();
$expected = ['result' => 'skipped', 'message' => 'No pending notifications'];
$h->setReply($expected);
check($h->sendEmail(false) === $expected, 'sendEmail(real): original result preserved');
check($h->calls === 1, 'sendEmail(real): exactly one send');
$h = new TestableHandler();
$h->setReply(['result' => 'sent', 'message' => 'ok', 'transport' => 'sendmail']);
check($h->sendEmail(true)['result'] === 'sent', 'sendEmail(test): original result preserved');
check($h->calls === 1, 'sendEmail(test): exactly one send');

/* No sender-path queue correlation remains. */
$src = file_get_contents(__DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor/NotificationHandler.php');
check(strpos($src, 'correlatePostfix') === false, 'no correlatePostfix on the send path');
$scan = file_get_contents(__DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor/notify_scan_email.php');
check(strpos($scan, 'correlatePostfix') === false, 'scan helper has no send-path correlation');

/* Real subjects, not placeholders. */
check(preg_match("/OPNsense: .* new device\(s\) detected/", $src) === 1, 'new-device subject is the emitted one');
check(strpos($src, 'New device notification') === false, 'placeholder new-device label is gone');

/* Guard: this suite must never have written to the host's live log. */
$live = '/var/db/devicemonitor/email_log.db';
if (is_file($live)) {
    $n = (new SQLite3($live, SQLITE3_OPEN_READONLY))->querySingle(
        "SELECT COUNT(*) FROM email_log WHERE subject IN ('Subj','S','Timeline','concurrent 0')");
    check($n === 0, 'no fixture rows leaked into the live email log');
}

@unlink($tmpDb);
@unlink($modelStub);
echo $fails === 0 ? "NOTIFICATION_WRAPPER_TESTS=PASS\n" : "NOTIFICATION_WRAPPER_TESTS=FAIL ($fails)\n";
exit($fails === 0 ? 0 : 1);
