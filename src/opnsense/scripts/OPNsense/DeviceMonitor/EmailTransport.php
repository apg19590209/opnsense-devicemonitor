<?php
/**
 * Transport-outcome classification and best-effort Postfix correlation for the
 * Device Monitor email log.
 *
 * The classification never upgrades an outcome on hope: only evidence the
 * transport actually produced is used, and anything unproven stays UNKNOWN.
 * Relay acceptance is recorded as such and is never described as inbox receipt.
 */

namespace OPNsense\DeviceMonitor;

class EmailTransport
{
    /** Map a sender's result array to (status, detail). */
    public static function classify(array $result)
    {
        $state = strtolower((string)($result['result'] ?? ''));
        $message = EmailLog::sanitise((string)($result['message'] ?? ''), 500);
        $transport = EmailLog::sanitise((string)($result['transport'] ?? ''));

        if ($state === 'sent') {
            if ($transport === 'smtp') {
                // The Direct SMTP helper exits 0 only after the server accepted the
                // message, which is relay acceptance — not inbox receipt.
                return [EmailLog::STATE_ACCEPTED, $message !== '' ? $message : 'SMTP relay accepted'];
            }
            // sendmail queues the message; acceptance by the relay happens later.
            return [EmailLog::STATE_QUEUED, $message !== '' ? $message : 'Queued to local sendmail'];
        }
        if ($state === 'failed') {
            return [EmailLog::STATE_FAILED, $message !== '' ? $message : 'Transport failed'];
        }
        if ($state === 'skipped') {
            return [EmailLog::STATE_UNKNOWN, $message !== '' ? $message : 'Skipped by channel guard'];
        }
        return [EmailLog::STATE_UNKNOWN, $message !== '' ? $message : 'No transport evidence'];
    }

    /**
     * Best-effort Postfix evidence. Only advisory: a missing queue is not proof of
     * delivery, and a queue-ID in the maildrop is not proof of acceptance.
     */
    public static function correlatePostfix($eventId, $emailTo)
    {
        if (!function_exists('shell_exec') || $emailTo === '') {
            return;
        }
        $queue = @shell_exec('/usr/local/sbin/postqueue -j 2>/dev/null');
        if (!is_string($queue) || trim($queue) === '') {
            return;
        }
        $recipient = strtolower(trim(explode(',', $emailTo)[0]));
        $found = null;
        foreach (preg_split('/\r?\n/', $queue) as $line) {
            $entry = json_decode(trim($line), true);
            if (!is_array($entry) || empty($entry['recipients'])) {
                continue;
            }
            foreach ($entry['recipients'] as $rcpt) {
                if (strtolower((string)($rcpt['address'] ?? '')) === $recipient) {
                    $found = $entry;
                    break 2;
                }
            }
        }
        if ($found === null) {
            return;
        }
        $queueName = (string)($found['queue_name'] ?? '');
        $queueId = (string)($found['queue_id'] ?? '');
        // Queue presence is weaker evidence than a transport result: never downgrade
        // an accepted or failed outcome, only fill in a still-unknown one.
        $db = EmailLog::instance();
        $existing = $db->currentStatus($eventId);
        if (in_array($existing, [EmailLog::STATE_ACCEPTED, EmailLog::STATE_FAILED], true)) {
            return;
        }
        $status = in_array($queueName, ['maildrop', 'incoming', 'active', 'deferred'], true)
            ? EmailLog::STATE_QUEUED
            : EmailLog::STATE_UNKNOWN;
        $db->recordTransportEvent(
            $eventId,
            $status,
            'Postfix queue ' . $queueName,
            $queueId,
            'postqueue: queue present'
        );
    }
}
