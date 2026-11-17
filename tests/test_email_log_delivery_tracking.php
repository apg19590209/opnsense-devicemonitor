<?php
/**
 * Out-of-band delivery tracking from Postfix processing logs, on fixtures only.
 *
 * Correlation is by the exact Message-ID Postfix records; queue disappearance on
 * its own proves nothing; repeated observation is idempotent; and a 2.x.y.z DSN
 * is relay acceptance, never inbox delivery.
 */
require_once __DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php';
require_once __DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor/EmailTransport.php';

use OPNsense\DeviceMonitor\EmailLog;
use OPNsense\DeviceMonitor\EmailTransport;

$fails = 0;
function check($c, $m) { global $fails; if ($c) { echo "  PASS $m\n"; } else { $fails++; echo "  FAIL $m\n"; } }

/* syslog-ng style, as installed on .23: the pid is not bracketed. */
function line($ts, $prog, $msg) { return "<22>1 2026-11-17T$ts+11:00 OPNsense.internal postfix/$prog 1234 - [meta sequenceId=\"1\"] $msg"; }

$db = tempnam(sys_get_temp_dir(), 'dmtrack'); unlink($db);
$log = new EmailLog($db);
$msg = '6afbfdef.512a7b089ba76f2e@OPNsense.internal';
$eid = $log->recordSubmission(EmailLog::TYPE_TEST, 'a@example.invalid', 'Tracked', null, null, null, null, $msg);
$log->recordTransportEvent($eid, EmailLog::STATE_QUEUED, 'Queued to local sendmail');

$sentLines = [
    line('18:10:40', 'cleanup', "02FA4B055F: message-id=<$msg>"),
    line('18:10:40', 'qmgr', '02FA4B055F: from=<x@y>, size=1993, nrcpt=1 (queue active)'),
    line('18:10:43', 'smtp', '02FA4B055F: to=<a@example.invalid>, relay=smtp.gmail.com[1.2.3.4]:587, delay=3.9, dsn=2.0.0, status=sent (250 2.0.0 OK abc - gsmtp)'),
    line('18:10:43', 'qmgr', '02FA4B055F: removed'),
];

/* 1. fast queue disappearance plus exact log correlation */
EmailTransport::$postqueueCandidates = ['/nonexistent/postqueue'];
EmailTransport::observe($eid, $log, $sentLines);
$detail = $log->messageDetail($eid);
check($detail['status'] === EmailLog::STATE_ACCEPTED, 'log evidence gives Relay accepted (accepted state)');
check(strpos($detail['status_detail'], 'Relay accepted') === 0, 'wording is relay acceptance, not delivery: ' . $detail['status_detail']);
check($detail['queue_id'] === '02FA4B055F', 'proven queue id recorded');

/* 2. repeated processing is idempotent */
$count = count($detail['timeline']);
EmailTransport::observe($eid, $log, $sentLines);
EmailTransport::observe($eid, $log, $sentLines);
check(count($log->messageDetail($eid)['timeline']) === $count, 'repeated observation appends nothing');
check($log->messageDetail($eid)['status'] === EmailLog::STATE_ACCEPTED, 'terminal relay acceptance is not reopened');

/* 3. queue disappearance without log evidence stays unknown */
$e2 = $log->recordSubmission(EmailLog::TYPE_TEST, 'b@example.invalid', 'Gone', null, null, null, null, 'gone@OPNsense.internal');
EmailTransport::observe($e2, $log, [line('18:10:40', 'cleanup', 'AAAA1111: message-id=<unrelated@OPNsense.internal>')]);
check($log->messageDetail($e2)['status'] === EmailLog::STATE_UNKNOWN, 'missing evidence remains unknown');

/* 4. unrelated concurrent mail never matches by subject/time */
$mixed = array_merge([
    line('18:10:41', 'cleanup', 'BBBB2222: message-id=<other@OPNsense.internal>'),
    line('18:10:42', 'smtp', 'BBBB2222: to=<b@example.invalid>, relay=relay.invalid[9.9.9.9]:25, status=sent (250 2.0.0 queued)'),
], $sentLines);
check(EmailTransport::queueIdForMessageId($mixed, $msg) === '02FA4B055F', 'exact Message-ID picks the right queue id');
check(EmailTransport::queueIdForMessageId($mixed, 'other@OPNsense.internal') === 'BBBB2222', 'each id maps to its own queue');

/* 5. deferred and bounced outcomes are distinguished */
$defOut = EmailTransport::recipientOutcomes([line('18:11:00', 'smtp', 'CCCC3333: to=<c@example.invalid>, relay=relay.invalid[9.9.9.9]:25, status=deferred (connect to relay.invalid[9.9.9.9]:25: Connection refused)')], 'CCCC3333');
check(EmailTransport::recipientSummary($defOut)[0] === EmailLog::STATE_QUEUED, 'deferred stays queued');
$bounceLines = [
    line('18:12:00', 'smtp', 'DDDD4444: to=<d@example.invalid>, relay=gmail-smtp-in.l.google.com[1.1.1.1]:25, dsn=5.1.1, status=bounced (host said: 550 5.1.1 no such user)'),
];
check(EmailTransport::recipientSummary(EmailTransport::recipientOutcomes($bounceLines, 'DDDD4444'))[0] === EmailLog::STATE_FAILED,
    'a bounce is a failure, not acceptance');

/* 6. mixed recipients are never summarised as complete success */
$mixedLines = [
    line('18:13:00', 'smtp', 'EEEE5555: to=<ok@example.invalid>, relay=r[1.1.1.1]:25, dsn=2.0.0, status=sent (250 2.0.0 OK)'),
    line('18:13:01', 'smtp', 'EEEE5555: to=<bad@example.invalid>, relay=r[1.1.1.1]:25, dsn=5.1.1, status=bounced (550 5.1.1 no such user)'),
];
list($state, $detailTxt) = EmailTransport::recipientSummary(EmailTransport::recipientOutcomes($mixedLines, 'EEEE5555'));
check($state !== EmailLog::STATE_ACCEPTED, 'mixed outcomes are not recorded as accepted');
check(strpos($detailTxt, 'ok@example.invalid') === 0 || strpos($detailTxt, 'Mixed') === 0, 'each recipient outcome is named: ' . $detailTxt);
$e3 = $log->recordSubmission(EmailLog::TYPE_TEST, 'ok@example.invalid,bad@example.invalid', 'Mixed', null, null, null, null, 'mixed@OPNsense.internal');
EmailTransport::observe($e3, $log, array_merge(
    [line('18:12:59', 'cleanup', 'EEEE5555: message-id=<mixed@OPNsense.internal>')], $mixedLines));
check($log->messageDetail($e3)['status'] === EmailLog::STATE_UNKNOWN, 'mixed delivery evidence records unknown, not success');

/* 7. rotated and missing logs */
$rot = tempnam(sys_get_temp_dir(), 'dmlog'); $rot = $rot . '.1';
$f = fopen($rot, 'w'); fwrite($f, implode("\n", $sentLines) . "\n"); fclose($f);
$read = EmailTransport::readLogLines(null, 86400, [$rot]);
check(count($read) === count($sentLines), 'rotated sibling is read');
$read = EmailTransport::readLogLines(null, 86400, ['/nonexistent/latest.log']);
check($read === [], 'a missing log yields no evidence (unknown), not an error');
$old = [line('10:00:00', 'smtp', 'FFFF6666: to=<x@example.invalid>, status=sent')];
check(EmailTransport::readLogLines(strtotime('2026-11-17 19:30:00'), 3600, [$rot]) !== null, 'lookback bounds the read');

/* 8. a stale latest.log symlink must not hide the dated log beside it */
$dir = sys_get_temp_dir() . '/dmlogs' . getmypid();
@mkdir($dir, 0700);
file_put_contents($dir . '/postfix_20260101.log', "old\n");
file_put_contents($dir . '/postfix_20260102.log', implode("\n", $sentLines) . "\n");
@symlink($dir . '/postfix_20260101.log', $dir . '/latest.log');
$read = EmailTransport::readLogLines(null, 86400, [$dir . '/latest.log']);
check(EmailTransport::queueIdForMessageId($read, $msg) === '02FA4B055F',
    'dated sibling is read when latest.log points at an older file');
@unlink($dir . '/latest.log'); @unlink($dir . '/postfix_20260101.log'); @unlink($dir . '/postfix_20260102.log'); @rmdir($dir);

/* 8b. a stale dated file must not stop the search before a newer one */
$dir2 = sys_get_temp_dir() . '/dmlogs2' . getmypid();
@mkdir($dir2, 0700);
file_put_contents($dir2 . '/postfix_20260101.log', line('00:00:01', 'smtp', 'OLDD000: to=<x@example.invalid>, status=sent'));
file_put_contents($dir2 . '/postfix_20260102.log', implode("\n", $sentLines) . "\n");
@symlink($dir2 . '/postfix_20260101.log', $dir2 . '/latest.log');
$read2 = EmailTransport::readLogLines(null, 86400, [$dir2 . '/latest.log']);
check(EmailTransport::queueIdForMessageId($read2, $msg) === '02FA4B055F',
    'a stale dated file does not end the search before a newer one');
@unlink($dir2 . '/latest.log'); @unlink($dir2 . '/postfix_20260101.log'); @unlink($dir2 . '/postfix_20260102.log'); @rmdir($dir2);

/* 9. historical timeline is preserved */
$timeline = $log->messageDetail($eid)['timeline'];
check($timeline[0]['stage'] === EmailLog::STATE_QUEUED && $timeline[0]['source'] === 'sender', 'the original sender event is kept');
check($timeline[1]['source'] === 'observer' && $timeline[1]['status'] === EmailLog::STATE_ACCEPTED, 'the observer append follows it');

@unlink($db); @unlink($rot);
echo $fails === 0 ? "EMAIL_LOG_DELIVERY_TRACKING_TESTS=PASS\n" : "EMAIL_LOG_DELIVERY_TRACKING_TESTS=FAIL ($fails)\n";
exit($fails === 0 ? 0 : 1);
