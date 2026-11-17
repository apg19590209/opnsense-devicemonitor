<?php
/**
 * Transport classification and bounded, out-of-band Postfix observation.
 *
 * Correlation is by *proven* identity only: a queue ID the sender observed, or the
 * RFC 5322 Message-ID carried into the queue file. Recipient matching is never used,
 * because it would attach unrelated system mail or a concurrent notification.
 */

namespace OPNsense\DeviceMonitor;

if (!function_exists('OPNsense\\DeviceMonitor\\email_log_trim')) {
    function email_log_trim($value, $limit)
    {
        $value = trim((string)$value);
        return strlen($value) > $limit ? substr($value, 0, $limit) : $value;
    }
}

class EmailTransport
{
    const OBSERVE_MAX_AGE_SECONDS = 86400;

    public static function classify(array $result)
    {
        $state = strtolower((string)($result['result'] ?? ''));
        $message = EmailLog::sanitise((string)($result['message'] ?? ''), 500);
        $transport = EmailLog::sanitise((string)($result['transport'] ?? ''));

        if ($state === 'sent') {
            if ($transport === 'smtp') {
                return [EmailLog::STATE_ACCEPTED, $message !== '' ? $message : 'SMTP relay accepted'];
            }
            return [EmailLog::STATE_QUEUED, $message !== '' ? $message : 'Queued to local sendmail'];
        }
        if ($state === 'failed') {
            return [EmailLog::STATE_FAILED, $message !== '' ? $message : 'Transport failed'];
        }
        return [EmailLog::STATE_UNKNOWN, $message !== '' ? $message : 'No transport evidence'];
    }

    /**
     * Installed OPNsense paths for the Postfix queue tools. Overridable through a
     * single trusted constant so tests can substitute a fake binary; the default is
     * the path verified on the known nodes, with the base-system path as fallback.
     */
    public static $postqueueCandidates = [
        '/usr/local/sbin/postqueue',
        '/usr/sbin/postqueue',
    ];
    public static $postcatCandidates = [
        '/usr/local/sbin/postcat',
        '/usr/sbin/postcat',
    ];

    /**
     * Installed Postfix processing logs. OPNsense writes syslog-ng to daily
     * files plus a `latest.log` symlink; `mail.log` is the stock FreeBSD
     * symlink. Bounded reads only - never the whole history.
     */
    public static $logCandidates = [
        '/var/log/postfix/latest.log',
        '/var/log/mail.log',
        '/var/log/maillog',
    ];
    const LOG_MAX_FILES = 7;
    const LOG_MAX_BYTES = 4194304;

    public static function trustedBinary(array $candidates)
    {
        foreach ($candidates as $path) {
            if (is_string($path) && $path !== '' && @is_executable($path)) {
                return $path;
            }
        }
        return null;
    }

    /** Run a command with a hard timeout; never blocks a send indefinitely. */
    private static function runBounded(array $cmd, $timeout = 5)
    {
        if (!function_exists('proc_open')) {
            return [null, 'proc_open unavailable'];
        }
        $proc = @proc_open($cmd, [1 => ['pipe', 'w'], 2 => ['pipe', 'w']], $pipes);
        if (!is_resource($proc)) {
            return [null, 'cannot start process'];
        }
        stream_set_blocking($pipes[1], false);
        stream_set_blocking($pipes[2], false);
        $out = '';
        $deadline = microtime(true) + $timeout;
        while (microtime(true) < $deadline) {
            $out .= (string)stream_get_contents($pipes[1]);
            $status = proc_get_status($proc);
            if (!$status['running']) { break; }
            usleep(100000);
        }
        $out .= (string)stream_get_contents($pipes[1]);
        fclose($pipes[1]);
        fclose($pipes[2]);
        $running = proc_get_status($proc);
        if ($running['running']) {
            proc_terminate($proc);
            return [null, 'observation timed out'];
        }
        proc_close($proc);
        return [$out, null];
    }

    /** True only for an exact `Message-ID: <value>` header line. */
    public static function headerCarriesMessageId($content, $messageId)
    {
        if (!is_string($content) || $messageId === '') {
            return false;
        }
        foreach (preg_split('/\r?\n/', $content) as $line) {
            if (preg_match('/^Message-ID:\s*<([^>]+)>\s*$/i', $line, $m)) {
                if ($m[1] === $messageId) {
                    return true;
                }
            }
        }
        return false;
    }

    /**
     * Derive the queue stage from the queue file's disposition record block. Only
     * an explicit deferred status counts; absence of evidence is plain queued.
     */
    public static function queueStage($content)
    {
        if (!is_string($content)) {
            return 'queued';
        }
        foreach (preg_split('/\r?\n/', $content) as $line) {
            // Postfix writes queue disposition lines as e.g. "deferred ...".
            if (preg_match('/^\s*deferred\b/i', $line)) {
                return 'deferred';
            }
        }
        return 'queued';
    }

    /**
     * Find the queue entry for a message by proven identity.
     *
     * A Message-ID is emitted by Postfix as an X-Postfix-Queue-ID-free header we
     * control, so we scan each queue file's headers for our own Message-ID. Queue IDs
     * the sender never observed are reported as unknown rather than guessed.
     */
    public static function findQueueEntry($messageId)
    {
        if ($messageId === '') {
            return [null, 'no message id recorded'];
        }
        $postqueue = self::trustedBinary(self::$postqueueCandidates);
        $postcat = self::trustedBinary(self::$postcatCandidates);
        if ($postqueue === null || $postcat === null) {
            return [null, 'Postfix queue tools not found at a trusted path'];
        }
        list($listing, $error) = self::runBounded([$postqueue, '-p'], 5);
        if ($listing === null) {
            return [null, 'postqueue unavailable: ' . $error];
        }
        $queueIds = [];
        foreach (preg_split('/\r?\n/', (string)$listing) as $line) {
            if (preg_match('/^([0-9A-F]{6,})\s+\d+/', $line, $m)) {
                $queueIds[] = $m[1];
            }
        }
        foreach (array_slice($queueIds, 0, 50) as $qid) {
            list($content, $err) = self::runBounded([$postcat, '-q', '-h', $qid], 5);
            if ($content === null) { continue; }
            if (self::headerCarriesMessageId($content, $messageId)) {
                return [$qid, null];
            }
        }
        return [null, 'no queue file carries the recorded message id'];
    }

    /** One processing-log line: syslog-ng (<pri>1 ISO host prog pid ...) or classic. */
    public static function parseLogLine($line)
    {
        $line = rtrim((string)$line, "\r\n");
        if ($line === '') {
            return null;
        }
        /* syslog-ng writes "<pri>1 ISO host postfix/prog pid - ..."; the pid is
         * not bracketed, so it is optional here. */
        if (preg_match('/^<\d+>\d\s+(\S+)\s+\S+\s+(postfix\/[\w-]+)(?:\[\d+\])?\s/u', $line, $m)) {
            return ['ts' => (string)strtotime($m[1]), 'program' => $m[2], 'body' => $line];
        }
        if (preg_match('/^(\w{3}\s+\d{1,2}\s+\d\d:\d\d:\d\d)\s+\S+\s+(postfix\/[\w-]+)(?:\[\d+\])?\s/u', $line, $m)) {
            $ts = strtotime($m[1] . ' ' . date('Y'));
            return ['ts' => (string)($ts === false ? 0 : $ts), 'program' => $m[2], 'body' => $line];
        }
        return null;
    }

    /** The exact Message-ID Postfix recorded for a queue ID (one cleanup line). */
    public static function queueIdForMessageId($lines, $messageId)
    {
        if ($messageId === '') {
            return null;
        }
        foreach ((array)$lines as $line) {
            $parsed = self::parseLogLine($line);
            if ($parsed === null || $parsed['program'] !== 'postfix/cleanup') {
                continue;
            }
            if (preg_match('/\b([0-9A-F]{4,}): message-id=<([^>]+)>/', $parsed['body'], $m)
                && $m[2] === $messageId) {
                return $m[1];
            }
        }
        return null;
    }

    /**
     * Per-recipient outcomes for one queue ID. A dropped/bounced recipient line
     * counts only with an explicit Postfix action, so an unrelated recipient is
     * never folded into another recipient's success.
     */
    public static function recipientOutcomes($lines, $queueId)
    {
        $outcomes = [];
        foreach ((array)$lines as $line) {
            $parsed = self::parseLogLine($line);
            if ($parsed === null || $parsed['program'] !== 'postfix/smtp') {
                continue;
            }
            $body = $parsed['body'];
            if (!preg_match('/\b' . preg_quote($queueId, '/') . ': to=<([^>]*)>/', $body, $m)) {
                continue;
            }
            $recipient = strtolower(trim($m[1]));
            if ($recipient === '') {
                continue;
            }
            if (preg_match('/\bstatus=(sent|deferred|bounced)\b/', $body, $st)) {
                $reason = '';
                if (preg_match('/\(([^()]*(?:\([^()]*\)[^()]*)*)\)\s*$/', $body, $why)) {
                    $reason = $why[1];
                }
                $outcomes[$recipient] = [
                    'status' => $st[1],
                    'relay_accepted' => $st[1] === 'sent',
                    // A 2.x.y.z DSN reason is relay acceptance, never inbox delivery.
                    'dsn' => preg_match('/\bdsn=(\d+\.\d+\.\d+)\b/', $body, $dsn) ? $dsn[1] : '',
                    'reason' => email_log_trim($reason, 300),
                ];
            } elseif (preg_match('/\bdisconnect from\b/', $body)) {
                $outcomes[$recipient] = ['status' => 'unknown', 'relay_accepted' => false, 'dsn' => '', 'reason' => ''];
            }
        }
        return $outcomes;
    }

    public static function recipientSummary(array $outcomes)
    {
        if (empty($outcomes)) {
            return [EmailLog::STATE_UNKNOWN, 'No per-recipient transport record found'];
        }
        $counts = ['sent' => 0, 'deferred' => 0, 'bounced' => 0, 'unknown' => 0];
        foreach ($outcomes as $o) {
            $counts[$o['status']] = ($counts[$o['status']] ?? 0) + 1;
        }
        $parts = [];
        foreach (['sent', 'deferred', 'bounced', 'unknown'] as $k) {
            if ($counts[$k] > 0) {
                $parts[] = $counts[$k] . ' ' . $k;
            }
        }
        $detail = implode(', ', $parts) . ' (' . count($outcomes) . ' recipient' . (count($outcomes) === 1 ? '' : 's') . ')';
        $kinds = count(array_filter($counts, function ($n) { return $n > 0; }));
        if ($kinds > 1) {
            // Mixed outcomes are never reported as a complete success.
            $state = $counts['bounced'] > 0 && $counts['sent'] === 0 ? EmailLog::STATE_FAILED : EmailLog::STATE_UNKNOWN;
            return [$state, 'Mixed outcomes: ' . $detail];
        }
        if ($counts['sent'] > 0) {
            return [EmailLog::STATE_ACCEPTED, 'Relay accepted for ' . $detail];
        }
        if ($counts['bounced'] > 0) {
            return [EmailLog::STATE_FAILED, 'Bounced: ' . $detail];
        }
        if ($counts['deferred'] > 0) {
            return [EmailLog::STATE_QUEUED, 'Deferred: ' . $detail];
        }
        return [EmailLog::STATE_UNKNOWN, 'No decisive transport record: ' . $detail];
    }

    /** Bounded log lines, newest first, stopping once the lookback window is passed. */
    public static function readLogLines($now = null, $windowSeconds = self::OBSERVE_MAX_AGE_SECONDS, $candidates = null)
    {
        $now = $now === null ? time() : (int)$now;
        $files = [];
        foreach ($candidates === null ? self::$logCandidates : $candidates as $path) {
            $real = @realpath($path);
            if ($real === false || !is_readable($real)) {
                continue;
            }
            $files[] = $real;
            // Rotated siblings of the same base name, newest first.
            for ($i = 1; $i <= self::LOG_MAX_FILES; $i++) {
                foreach ([$real . '.' . $i, $real . '.gz.' . $i, $real . '.bz2.' . $i] as $rot) {
                    if (is_readable($rot)) {
                        $files[] = $rot;
                    }
                }
            }
        }
        $lines = [];
        $budget = self::LOG_MAX_BYTES;
        foreach (array_unique($files) as $file) {
            if ($budget <= 0) {
                break;
            }
            $chunk = @file_get_contents($file, false, null, 0, min($budget, self::LOG_MAX_BYTES));
            if ($chunk === false) {
                continue;
            }
            $budget -= strlen($chunk);
            foreach (array_reverse(preg_split('/\r?\n/', $chunk)) as $line) {
                $parsed = self::parseLogLine($line);
                if ($parsed === null) {
                    continue;
                }
                if ($parsed['ts'] !== '' && ((int)$parsed['ts'] > 0) && ((int)$parsed['ts'] < $now - $windowSeconds)) {
                    return $lines;
                }
                $lines[] = $line;
            }
        }
        return $lines;
    }

    /**
     * Observe one logical email. Queue evidence first (proven identity), then the
     * processing log for messages that already left the queue. Missing evidence is
     * recorded as unknown; queue disappearance alone proves nothing.
     */
    public static function observe($eventId, $log, $lines = null)
    {
        $current = $log->currentStatus($eventId);
        if (!$current) { return; }
        if (in_array($current['status'], [EmailLog::STATE_ACCEPTED, EmailLog::STATE_FAILED], true)) {
            return;
        }
        $age = strtotime($current['updated_utc'] ?? '') ?: 0;
        if ($age !== 0 && (time() - $age) > self::OBSERVE_MAX_AGE_SECONDS) {
            self::record($log, $eventId, EmailLog::STATE_UNKNOWN,
                'No further evidence within the observation window', 'observation window expired');
            return;
        }
        $messageId = (string)($current['message_id'] ?? '');

        list($queueId, $reason) = self::findQueueEntry($messageId);
        if ($queueId !== null) {
            list($content, $err) = self::runBounded([self::trustedBinary(self::$postcatCandidates), '-q', '-h', $queueId], 5);
            $stage = self::queueStage((string)$content);
            self::record($log, $eventId, EmailLog::STATE_QUEUED, 'Present in Postfix queue',
                'postcat header match', $queueId, $stage);
            return;
        }

        $lines = $lines === null ? self::readLogLines() : $lines;
        $loggedQueueId = self::queueIdForMessageId($lines, $messageId);
        if ($loggedQueueId === null) {
            /* Neither the queue nor the log carries our exact Message-ID. The queue
             * file may simply have gone; that proves neither delivery nor failure. */
            self::record($log, $eventId, EmailLog::STATE_UNKNOWN,
                'Queue entry not observable; delivery state unknown', $reason);
            return;
        }
        $outcomes = self::recipientOutcomes($lines, $loggedQueueId);
        list($state, $detail) = self::recipientSummary($outcomes);
        $evidence = [];
        foreach ($outcomes as $recipient => $o) {
            $evidence[] = $recipient . ' ' . $o['status'] . ($o['dsn'] !== '' ? ' dsn=' . $o['dsn'] : '') . ($o['reason'] !== '' ? ' ' . $o['reason'] : '');
        }
        self::record($log, $eventId, $state, $detail, 'postfix log message-id match: ' . $loggedQueueId
            . (empty($evidence) ? '' : '; ' . implode('; ', $evidence)), $loggedQueueId);
    }

    /**
     * Append one observation unless an identical one is already the latest event,
     * so repeated passes never duplicate history.
     */
    private static function record($log, $eventId, $state, $detail, $evidence = '', $queueId = null)
    {
        $timeline = $log->timeline($eventId);
        $last = end($timeline);
        if (is_array($last) && $last['source'] === 'observer' && $last['status'] === $state
            && $last['detail'] === $detail && $last['evidence'] === $evidence) {
            return;
        }
        $log->recordTransportEvent($eventId, $state, $detail, $evidence, 'observer', $queueId, null, 'observation');
    }
}
