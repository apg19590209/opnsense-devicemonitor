<?php
/**
 * Transport classification and bounded, out-of-band Postfix observation.
 *
 * Correlation is by *proven* identity only: a queue ID the sender observed, or the
 * RFC 5322 Message-ID carried into the queue file. Recipient matching is never used,
 * because it would attach unrelated system mail or a concurrent notification.
 */

namespace OPNsense\DeviceMonitor;

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
        list($listing, $error) = self::runBounded(['/usr/sbin/postqueue', '-p'], 5);
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
            list($content, $err) = self::runBounded(['/usr/sbin/postcat', '-q', '-h', $qid], 5);
            if ($content === null) { continue; }
            if (strpos($content, $messageId) !== false) {
                return [$qid, null];
            }
        }
        return [null, 'no queue file carries the recorded message id'];
    }

    /**
     * Observe one logical email whose transport was sendmail/submission-only.
     * Called from a scheduled action, never from the sending path.
     */
    public static function observe($eventId, $log)
    {
        $current = $log->currentStatus($eventId);
        if (!$current) { return; }
        if (in_array($current['status'], [EmailLog::STATE_ACCEPTED, EmailLog::STATE_FAILED], true)) {
            return;
        }
        $age = strtotime($current['updated_utc'] ?? '') ?: 0;
        if ($age !== 0 && (time() - $age) > self::OBSERVE_MAX_AGE_SECONDS) {
            $log->recordTransportEvent($eventId, EmailLog::STATE_UNKNOWN,
                'No further evidence within the observation window', 'observation window expired', 'observer', null, null, 'observation');
            return;
        }
        list($queueId, $reason) = self::findQueueEntry((string)($current['message_id'] ?? ''));
        if ($queueId === null) {
            /* The queue file is gone. That proves nothing: it may have been delivered,
             * bounced, expired elsewhere or moved between queue directories. */
            $log->recordTransportEvent($eventId, EmailLog::STATE_UNKNOWN,
                'Queue entry not observable; delivery state unknown', $reason, 'observer', null, null, 'observation');
            return;
        }
        list($content, $err) = self::runBounded(['/usr/sbin/postcat', '-q', '-h', $queueId], 5);
        $stage = 'queued';
        $detail = 'Present in Postfix queue';
        if (is_string($content) && preg_match('/deferred/i', $content) !== false) {
            $stage = 'deferred';
        }
        $log->recordTransportEvent($eventId, EmailLog::STATE_QUEUED, $detail, 'postcat header match', 'observer', $queueId, null, $stage);
    }
}
