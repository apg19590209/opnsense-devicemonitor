<?php
/**
 * Device Monitor email log — a dedicated, best-effort record of every email the
 * plugin attempts to send.
 *
 * Design constraints (see DECISIONS.md, email-log decision):
 *   * Lives in its own SQLite file; never in devices.db and never in the Postfix
 *     queue. Monitoring operations cannot be slowed or blocked by logging.
 *   * One logical email is one row. Transport events (submission, queue status,
 *     relay acceptance/last error) update that row through `recordTransportEvent`
 *     keyed by the caller's event_id, so one email never becomes several rows.
 *   * Writes are bounded and best-effort: any failure is swallowed after a
 *     sanitised diagnostic, because logging must never block or duplicate a send.
 *   * No message bodies, credentials or queue content are stored. Subject and
 *     recipient are administrative data and are stored verbatim but never
 *     exported without an explicit operator action.
 */

namespace OPNsense\DeviceMonitor;

class EmailLog
{
    const RETENTION_DAYS = 30;
    const BUSY_TIMEOUT_MS = 2000;
    const MAX_STRING = 255;
    const MAX_DETAIL = 500;

    /** Terminal and intermediate transport states. */
    const STATE_SUBMITTED = 'submitted';
    const STATE_QUEUED = 'queued';
    const STATE_ACCEPTED = 'accepted';
    const STATE_FAILED = 'failed';
    const STATE_UNKNOWN = 'unknown';

    /** Notification categories produced by the plugin. */
    const TYPE_TEST = 'test';
    const TYPE_NEW_DEVICE = 'new_device';
    const TYPE_SCAN_RESULT = 'scan_result';
    const TYPE_FAILOVER = 'failover';
    const TYPE_SERVICE = 'service';
    const TYPE_IDENTITY = 'identity';

    private static $instance = null;
    private $dbFile;
    private $diagnostic = null;

    public function __construct($dbFile = null)
    {
        if ($dbFile === null) {
            $defaults = json_decode(file_get_contents(
                '/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'
            ), true);
            $dbFile = $defaults['paths']['emailLogDb'] ?? '/var/db/devicemonitor/email_log.db';
        }
        $this->dbFile = $dbFile;
    }

    public static function instance()
    {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    /** Reasons the last write failed, for the UI's logging-health note. */
    public function lastDiagnostic()
    {
        return $this->diagnostic;
    }

    private function connect()
    {
        $dir = dirname($this->dbFile);
        if (!is_dir($dir)) {
            @mkdir($dir, 0750, true);
        }
        $db = new \SQLite3($this->dbFile);
        $db->busyTimeout(self::BUSY_TIMEOUT_MS);
        $db->exec('PRAGMA journal_mode = WAL');
        $db->exec('PRAGMA synchronous = NORMAL');
        return $db;
    }

    private function ensureSchema($db)
    {
        $db->exec('CREATE TABLE IF NOT EXISTS email_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL UNIQUE,
            created_utc DATETIME NOT NULL,
            updated_utc DATETIME NOT NULL,
            node_id TEXT NOT NULL,
            node_ip TEXT NOT NULL DEFAULT \'\',
            node_role TEXT NOT NULL DEFAULT \'unknown\',
            notification_type TEXT NOT NULL,
            recipient TEXT NOT NULL DEFAULT \'\',
            subject TEXT NOT NULL DEFAULT \'\',
            status TEXT NOT NULL DEFAULT \'unknown\',
            status_detail TEXT NOT NULL DEFAULT \'\',
            queue_id TEXT NOT NULL DEFAULT \'\',
            postfix_queue_id TEXT NOT NULL DEFAULT \'\',
            evidence TEXT NOT NULL DEFAULT \'\'
        )');
        $db->exec('CREATE INDEX IF NOT EXISTS idx_email_log_created ON email_log(created_utc)');
        $db->exec('CREATE INDEX IF NOT EXISTS idx_email_log_type ON email_log(notification_type)');
        $db->exec('CREATE INDEX IF NOT EXISTS idx_email_log_status ON email_log(status)');
    }

    /** Sanitise arbitrary text for storage: bounded, no control characters. */
    public static function sanitise($value, $limit = self::MAX_STRING)
    {
        $value = is_string($value) ? $value : (string)$value;
        $value = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/', '', $value);
        $value = trim(preg_replace('/\s+/', ' ', $value));
        if (strlen($value) > $limit) {
            $value = substr($value, 0, $limit);
        }
        return $value;
    }

    /**
     * Recipient is reduced to a bounded single address list. Credentials never
     * appear here; callers pass exactly what they resolved.
     */
    public static function sanitiseRecipient($value)
    {
        $parts = array_map('trim', explode(',', (string)$value));
        $parts = array_values(array_filter($parts, function ($p) { return $p !== ''; }));
        return self::sanitise(implode(', ', array_slice($parts, 0, 10)));
    }

    /** Stable identity for one logical email. */
    public static function newEventId()
    {
        return bin2hex(random_bytes(16));
    }

    /** Current CARP role, best-effort; unknown when the probe fails. */
    public static function currentRole()
    {
        $out = @shell_exec('/sbin/ifconfig 2>/dev/null');
        if (is_string($out)) {
            if (preg_match('/carp:\s*(MASTER|BACKUP)/', $out, $m)) {
                return strtolower($m[1]);
            }
            return 'non_ha';
        }
        return 'unknown';
    }

    /** Local node identity: IPv4 of re0/management interface plus hostname. */
    public static function currentNode()
    {
        $host = trim((string)@gethostname());
        $ip = '';
        $out = @shell_exec("/sbin/ifconfig 2>/dev/null");
        if (is_string($out) && preg_match('/inet (\d+\.\d+\.\d+\.\d+) /', $out, $m)) {
            $ip = $m[1];
        }
        return ['host' => $host, 'ip' => $ip];
    }

    /**
     * Record the start of a logical email. Returns the event id used for later
     * transport updates, or null when logging is unavailable.
     */
    public function recordSubmission($type, $recipient, $subject, $eventId = null, $nodeId = null, $nodeIp = null, $role = null)
    {
        $eventId = $eventId ?: self::newEventId();
        $node = self::currentNode();
        $now = gmdate('Y-m-d H:i:s');
        try {
            $db = $this->connect();
            $this->ensureSchema($db);
            $stmt = $db->prepare(
                'INSERT INTO email_log (event_id, created_utc, updated_utc, node_id, node_ip, node_role,
                    notification_type, recipient, subject, status, status_detail, evidence)
                 VALUES (:e, :c, :u, :n, :ip, :r, :t, :to, :s, :st, :d, :ev)'
            );
            $stmt->bindValue(':e', $eventId, SQLITE3_TEXT);
            $stmt->bindValue(':c', $now, SQLITE3_TEXT);
            $stmt->bindValue(':u', $now, SQLITE3_TEXT);
            $stmt->bindValue(':n', self::sanitise($nodeId !== null ? $nodeId : $node['host']), SQLITE3_TEXT);
            $stmt->bindValue(':ip', self::sanitise($nodeIp !== null ? $nodeIp : $node['ip']), SQLITE3_TEXT);
            $stmt->bindValue(':r', self::sanitise($role !== null ? $role : self::currentRole()), SQLITE3_TEXT);
            $stmt->bindValue(':t', self::sanitise($type), SQLITE3_TEXT);
            $stmt->bindValue(':to', self::sanitiseRecipient($recipient), SQLITE3_TEXT);
            $stmt->bindValue(':s', self::sanitise($subject), SQLITE3_TEXT);
            $stmt->bindValue(':st', self::STATE_SUBMITTED, SQLITE3_TEXT);
            $stmt->bindValue(':d', '', SQLITE3_TEXT);
            $stmt->bindValue(':ev', 'submission', SQLITE3_TEXT);
            $stmt->execute();
            $db->close();
            $this->diagnostic = null;
            return $eventId;
        } catch (\Throwable $e) {
            $this->diagnostic = self::sanitise($e->getMessage(), self::MAX_DETAIL);
            return null;
        }
    }

    /**
     * Attach a transport outcome to an existing logical email. Never inserts a
     * duplicate row for a transport event; an unknown event_id is ignored (the
     * submission itself may already have failed to log).
     */
    public function recordTransportEvent($eventId, $status, $detail = '', $queueId = null, $evidence = null)
    {
        if (!$eventId) {
            return false;
        }
        $now = gmdate('Y-m-d H:i:s');
        try {
            $db = $this->connect();
            $this->ensureSchema($db);
            $stmt = $db->prepare(
                'UPDATE email_log SET updated_utc = :u, status = :st, status_detail = :d,
                    queue_id = COALESCE(:q, queue_id), evidence = COALESCE(:ev, evidence)
                 WHERE event_id = :e'
            );
            $stmt->bindValue(':u', $now, SQLITE3_TEXT);
            $stmt->bindValue(':st', self::sanitise($status), SQLITE3_TEXT);
            $stmt->bindValue(':d', self::sanitise($detail, self::MAX_DETAIL), SQLITE3_TEXT);
            $stmt->bindValue(':q', $queueId === null ? null : self::sanitise($queueId), SQLITE3_TEXT);
            $stmt->bindValue(':ev', $evidence === null ? null : self::sanitise($evidence), SQLITE3_TEXT);
            $stmt->bindValue(':e', $eventId, SQLITE3_TEXT);
            $stmt->execute();
            $db->close();
            return true;
        } catch (\Throwable $e) {
            $this->diagnostic = self::sanitise($e->getMessage(), self::MAX_DETAIL);
            return false;
        }
    }

    /** Current status for one logical email, or null when unknown/absent. */
    public function currentStatus($eventId)
    {
        if (!$eventId) {
            return null;
        }
        try {
            $db = $this->connect();
            $this->ensureSchema($db);
            $stmt = $db->prepare('SELECT status FROM email_log WHERE event_id = :e');
            $stmt->bindValue(':e', $eventId, SQLITE3_TEXT);
            $res = $stmt->execute();
            $row = $res->fetchArray(SQLITE3_ASSOC);
            $db->close();
            return $row ? $row['status'] : null;
        } catch (\Throwable $e) {
            return null;
        }
    }

    /** Delete only email-log rows older than the retention window. */
    public function prune($days = self::RETENTION_DAYS)
    {
        $cutoff = gmdate('Y-m-d H:i:s', time() - ($days * 86400));
        try {
            $db = $this->connect();
            $this->ensureSchema($db);
            $stmt = $db->prepare('DELETE FROM email_log WHERE created_utc < :c');
            $stmt->bindValue(':c', $cutoff, SQLITE3_TEXT);
            $stmt->execute();
            $removed = $db->changes();
            $db->close();
            return $removed;
        } catch (\Throwable $e) {
            $this->diagnostic = self::sanitise($e->getMessage(), self::MAX_DETAIL);
            return 0;
        }
    }

    /** Read rows for the local UI. Bounded page size, escaped by the caller. */
    public function query(array $filters = [], $limit = 50, $offset = 0)
    {
        $limit = max(1, min(500, (int)$limit));
        $offset = max(0, (int)$offset);
        $where = [];
        $args = [];
        if (!empty($filters['type'])) {
            $where[] = 'notification_type = :t';
            $args[':t'] = $filters['type'];
        }
        if (!empty($filters['status'])) {
            $where[] = 'status = :s';
            $args[':s'] = $filters['status'];
        }
        if (!empty($filters['search'])) {
            $where[] = '(subject LIKE :q OR recipient LIKE :q)';
            $args[':q'] = '%' . str_replace(['%', '_'], ['\%', '\_'], $filters['search']) . '%';
        }
        $sql = 'SELECT * FROM email_log';
        if ($where) {
            $sql .= ' WHERE ' . implode(' AND ', $where);
        }
        $sql .= ' ORDER BY created_utc DESC, id DESC LIMIT :l OFFSET :o';
        try {
            $db = $this->connect();
            $this->ensureSchema($db);
            $stmt = $db->prepare($sql);
            foreach ($args as $k => $v) {
                $stmt->bindValue($k, $v, SQLITE3_TEXT);
            }
            $stmt->bindValue(':l', $limit, SQLITE3_INTEGER);
            $stmt->bindValue(':o', $offset, SQLITE3_INTEGER);
            $res = $stmt->execute();
            $rows = [];
            while ($row = $res->fetchArray(SQLITE3_ASSOC)) {
                $rows[] = $row;
            }
            $db->close();
            return $rows;
        } catch (\Throwable $e) {
            $this->diagnostic = self::sanitise($e->getMessage(), self::MAX_DETAIL);
            return [];
        }
    }
}
