<?php
/**
 * Device Monitor email log.
 *
 * A dedicated, fail-open record of every email the plugin attempts to send.
 *
 *   * Own SQLite file (paths.emailLogDb). Never devices.db, never the Postfix queue.
 *   * One logical email = one `email_log` row. Every transport outcome appends a row
 *     to `email_log_events`, so the UI can show a genuine chronological timeline.
 *   * Correlation uses a transport identity the sender actually observed (queue id
 *     or message id), never a recipient match.
 *   * Nothing here may block delivery: every public method swallows failure and
 *     reports it through lastDiagnostic(). No shell execution is used.
 */

namespace OPNsense\DeviceMonitor;

class EmailLog
{
    const RETENTION_DAYS = 30;
    const BUSY_TIMEOUT_MS = 2000;
    const MAX_STRING = 255;
    const MAX_DETAIL = 500;

    const STATE_SUBMITTED = 'submitted';
    const STATE_QUEUED = 'queued';
    const STATE_ACCEPTED = 'accepted';
    const STATE_FAILED = 'failed';
    const STATE_UNKNOWN = 'unknown';

    const TYPE_TEST = 'test';
    const TYPE_NEW_DEVICE = 'new_device';
    const TYPE_SCAN_RESULT = 'scan_result';
    const TYPE_FAILOVER = 'failover';
    const TYPE_SERVICE = 'service';
    const TYPE_IDENTITY = 'identity';

    private $dbFile;
    private $diagnostic = null;

    public function __construct($dbFile = null)
    {
        $this->dbFile = $dbFile ?: self::defaultDbFile();
    }

    public static function defaultDbFile()
    {
        $defaults = @json_decode(@file_get_contents(
            '/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'
        ), true);
        return $defaults['paths']['emailLogDb'] ?? '/var/db/devicemonitor/email_log.db';
    }

    private static $instance = null;

    /** Shared instance used by the senders; tests may replace it by construction. */
    public static function instance()
    {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    /** Test seam: install a recorder bound to a specific database. */
    public static function setInstance($log)
    {
        self::$instance = $log;
    }

    public function lastDiagnostic()
    {
        return $this->diagnostic;
    }

    private function fail($message)
    {
        $this->diagnostic = self::sanitise($message, self::MAX_DETAIL);
        return null;
    }

    private function connect()
    {
        $dir = dirname($this->dbFile);
        if (!is_dir($dir)) {
            @mkdir($dir, 0750, true);
        }
        $db = new \SQLite3($this->dbFile);
        // Restrictive permissions on the database and its WAL/SHM siblings; the
        // log holds administrative subject and recipient data.
        @chmod($this->dbFile, 0640);
        foreach (['-wal', '-shm'] as $suffix) {
            if (file_exists($this->dbFile . $suffix)) {
                @chmod($this->dbFile . $suffix, 0640);
            }
        }
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
            transport TEXT NOT NULL DEFAULT \'\',
            queue_id TEXT NOT NULL DEFAULT \'\',
            message_id TEXT NOT NULL DEFAULT \'\'
        )');
        $db->exec('CREATE TABLE IF NOT EXISTS email_log_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            occurred_utc DATETIME NOT NULL,
            stage TEXT NOT NULL,
            status TEXT NOT NULL,
            detail TEXT NOT NULL DEFAULT \'\',
            evidence TEXT NOT NULL DEFAULT \'\',
            source TEXT NOT NULL DEFAULT \'sender\'
        )');
        $db->exec('CREATE INDEX IF NOT EXISTS idx_email_log_created ON email_log(created_utc)');
        $db->exec('CREATE INDEX IF NOT EXISTS idx_email_log_type ON email_log(notification_type)');
        $db->exec('CREATE INDEX IF NOT EXISTS idx_email_log_status ON email_log(status)');
        $db->exec('CREATE INDEX IF NOT EXISTS idx_email_log_events ON email_log_events(event_id, occurred_utc)');
    }

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

    public static function sanitiseRecipient($value)
    {
        $parts = array_map('trim', explode(',', (string)$value));
        $parts = array_values(array_filter($parts, function ($p) { return $p !== ''; }));
        return self::sanitise(implode(', ', array_slice($parts, 0, 10)));
    }

    public static function newEventId()
    {
        return bin2hex(random_bytes(16));
    }

    /** RFC 5322 Message-ID the transport will emit (or already emitted). */
    public static function newMessageId($nodeId = '')
    {
        $host = $nodeId !== '' ? $nodeId : 'devicemonitor';
        return sprintf('%x.%s@%s', time(), bin2hex(random_bytes(8)), $host);
    }

    /**
     * Node identity without shell execution: hostname plus the addresses the kernel
     * reports for this host, so a shared hostname never identifies a node alone.
     */
    public static function currentNode()
    {
        $host = trim((string)@gethostname());
        $ip = '';
        if (function_exists('net_get_interfaces')) {
            $ifs = @net_get_interfaces();
            if (is_array($ifs)) {
                foreach (['re0', 'vtnet0', 'igc0', 'em0'] as $name) {
                    if (!isset($ifs[$name]['unicast'])) {
                        continue;
                    }
                    foreach ($ifs[$name]['unicast'] as $addr) {
                        $candidate = (string)($addr['address'] ?? '');
                        if (filter_var($candidate, FILTER_VALIDATE_IP, FILTER_FLAG_IPV4)
                            && strpos($candidate, '127.') !== 0) {
                            $ip = $candidate;
                            break 2;
                        }
                    }
                }
            }
        }
        return ['host' => $host, 'ip' => $ip];
    }

    public function recordSubmission($type, $recipient, $subject, $eventId = null, $nodeId = null, $nodeIp = null, $role = null, $messageId = null)
    {
        try {
            $eventId = $eventId ?: self::newEventId();
            $node = self::currentNode();
            $now = gmdate('Y-m-d H:i:s');
            $db = $this->connect();
            $this->ensureSchema($db);
            $stmt = $db->prepare(
                'INSERT INTO email_log (event_id, created_utc, updated_utc, node_id, node_ip, node_role,
                    notification_type, recipient, subject, status, status_detail, transport, queue_id, message_id)
                 VALUES (:e, :c, :u, :n, :ip, :r, :t, :to, :s, :st, :d, \'\', \'\', :mid)'
            );
            $stmt->bindValue(':e', $eventId, SQLITE3_TEXT);
            $stmt->bindValue(':c', $now, SQLITE3_TEXT);
            $stmt->bindValue(':u', $now, SQLITE3_TEXT);
            $stmt->bindValue(':n', self::sanitise($nodeId !== null ? $nodeId : $node['host']), SQLITE3_TEXT);
            $stmt->bindValue(':ip', self::sanitise($nodeIp !== null ? $nodeIp : $node['ip']), SQLITE3_TEXT);
            $stmt->bindValue(':r', self::sanitise($role !== null ? $role : 'unknown'), SQLITE3_TEXT);
            $stmt->bindValue(':t', self::sanitise($type), SQLITE3_TEXT);
            $stmt->bindValue(':to', self::sanitiseRecipient($recipient), SQLITE3_TEXT);
            $stmt->bindValue(':s', self::sanitise($subject), SQLITE3_TEXT);
            $stmt->bindValue(':st', self::STATE_SUBMITTED, SQLITE3_TEXT);
            $stmt->bindValue(':d', '', SQLITE3_TEXT);
            $stmt->bindValue(':mid', self::sanitise((string)$messageId), SQLITE3_TEXT);
            $stmt->execute();
            $db->close();
            $this->diagnostic = null;
            return $eventId;
        } catch (\Throwable $e) {
            return $this->fail($e->getMessage());
        }
    }

    /**
     * Append one transport/observation event. Never rewrites history: a later stage
     * adds a row, and only the email_log summary columns move forward.
     */
    public function recordTransportEvent($eventId, $status, $detail = '', $evidence = null, $source = 'sender', $queueId = null, $transport = null, $stage = null)
    {
        if (!$eventId) {
            return false;
        }
        $db = null;
        $inTransaction = false;
        try {
            $now = gmdate('Y-m-d H:i:s');
            $db = $this->connect();
            $this->ensureSchema($db);
            $db->exec('BEGIN IMMEDIATE');
            $inTransaction = true;
            $ins = $db->prepare(
                'INSERT INTO email_log_events (event_id, occurred_utc, stage, status, detail, evidence, source)
                 VALUES (:e, :o, :g, :s, :d, :ev, :src)'
            );
            $ins->bindValue(':e', $eventId, SQLITE3_TEXT);
            $ins->bindValue(':o', $now, SQLITE3_TEXT);
            $ins->bindValue(':g', self::sanitise($stage !== null ? $stage : $status), SQLITE3_TEXT);
            $ins->bindValue(':s', self::sanitise($status), SQLITE3_TEXT);
            $ins->bindValue(':d', self::sanitise($detail, self::MAX_DETAIL), SQLITE3_TEXT);
            $ins->bindValue(':ev', self::sanitise((string)$evidence), SQLITE3_TEXT);
            $ins->bindValue(':src', self::sanitise($source), SQLITE3_TEXT);
            $ins->execute();
            $upd = $db->prepare(
                'UPDATE email_log SET updated_utc = :u, status = :s, status_detail = :d,
                    transport = CASE WHEN :tr = \'\' THEN transport ELSE :tr END,
                    queue_id = CASE WHEN :q = \'\' THEN queue_id ELSE :q END
                 WHERE event_id = :e'
            );
            $upd->bindValue(':u', $now, SQLITE3_TEXT);
            $upd->bindValue(':s', self::sanitise($status), SQLITE3_TEXT);
            $upd->bindValue(':d', self::sanitise($detail, self::MAX_DETAIL), SQLITE3_TEXT);
            $upd->bindValue(':tr', self::sanitise((string)$transport), SQLITE3_TEXT);
            $upd->bindValue(':q', self::sanitise((string)$queueId), SQLITE3_TEXT);
            $upd->bindValue(':e', $eventId, SQLITE3_TEXT);
            $upd->execute();
            $db->exec('COMMIT');
            $inTransaction = false;
            $db->close();
            return true;
        } catch (\Throwable $e) {
            if ($inTransaction && $db instanceof \SQLite3) {
                try { $db->exec('ROLLBACK'); } catch (\Throwable $ignored) {}
            }
            if ($db instanceof \SQLite3) {
                try { $db->close(); } catch (\Throwable $ignored) {}
            }
            return (bool)$this->fail($e->getMessage());
        }
    }

    public function currentStatus($eventId)
    {
        try {
            $db = $this->connect();
            $this->ensureSchema($db);
            $stmt = $db->prepare('SELECT status, message_id FROM email_log WHERE event_id = :e');
            $stmt->bindValue(':e', $eventId, SQLITE3_TEXT);
            $row = $stmt->execute()->fetchArray(SQLITE3_ASSOC);
            $db->close();
            return $row ?: null;
        } catch (\Throwable $e) {
            return $this->fail($e->getMessage());
        }
    }

    public function timeline($eventId)
    {
        try {
            $db = $this->connect();
            $this->ensureSchema($db);
            $stmt = $db->prepare('SELECT occurred_utc, stage, status, detail, evidence, source
                FROM email_log_events WHERE event_id = :e ORDER BY occurred_utc ASC, id ASC');
            $stmt->bindValue(':e', $eventId, SQLITE3_TEXT);
            $res = $stmt->execute();
            $rows = [];
            while ($row = $res->fetchArray(SQLITE3_ASSOC)) { $rows[] = $row; }
            $db->close();
            return $rows;
        } catch (\Throwable $e) {
            $this->fail($e->getMessage());
            return [];
        }
    }

    /** Emails still awaiting stronger evidence, oldest first, bounded. */
    public function pendingForObservation($limit = 20)
    {
        $limit = max(1, min(100, (int)$limit));
        try {
            $db = $this->connect();
            $this->ensureSchema($db);
            $stmt = $db->prepare("SELECT event_id, message_id, updated_utc FROM email_log
                WHERE status IN ('submitted', 'queued') AND message_id != ''
                ORDER BY created_utc ASC LIMIT :l");
            $stmt->bindValue(':l', $limit, SQLITE3_INTEGER);
            $res = $stmt->execute();
            $rows = [];
            while ($row = $res->fetchArray(SQLITE3_ASSOC)) { $rows[] = $row; }
            $db->close();
            return $rows;
        } catch (\Throwable $e) {
            $this->fail($e->getMessage());
            return [];
        }
    }

    /** Delete expired log rows and every event that belongs to them. */
    public function prune($days = self::RETENTION_DAYS)
    {
        $cutoff = gmdate('Y-m-d H:i:s', time() - ($days * 86400));
        try {
            $db = $this->connect();
            $this->ensureSchema($db);
            $db->exec('BEGIN IMMEDIATE');
            $db->exec("CREATE TEMP TABLE IF NOT EXISTS expired_ids AS
                SELECT event_id FROM email_log WHERE created_utc < '$cutoff'");
            $db->exec('DELETE FROM email_log_events WHERE event_id IN (SELECT event_id FROM expired_ids)');
            $db->exec("DELETE FROM email_log WHERE created_utc < '$cutoff'");
            $removed = $db->changes();
            $db->exec('DROP TABLE IF EXISTS expired_ids');
            $db->exec('COMMIT');
            $db->close();
            return $removed;
        } catch (\Throwable $e) {
            return 0;
        }
    }

    public function query(array $filters = [], $limit = 50, $offset = 0)
    {
        $limit = max(1, min(500, (int)$limit));
        $offset = max(0, (int)$offset);
        $where = [];
        $args = [];
        if (!empty($filters['type'])) { $where[] = 'notification_type = :t'; $args[':t'] = $filters['type']; }
        if (!empty($filters['status'])) { $where[] = 'status = :s'; $args[':s'] = $filters['status']; }
        if (!empty($filters['search'])) {
            $where[] = '(subject LIKE :q ESCAPE \'\\\' OR recipient LIKE :q ESCAPE \'\\\')';
            $args[':q'] = '%' . str_replace(['%', '_', '\\'], ['\%', '\_', '\\\\'], $filters['search']) . '%';
        }
        $sql = 'SELECT * FROM email_log';
        if ($where) { $sql .= ' WHERE ' . implode(' AND ', $where); }
        $sql .= ' ORDER BY created_utc DESC, id DESC LIMIT :l OFFSET :o';
        try {
            $db = $this->connect();
            $this->ensureSchema($db);
            $stmt = $db->prepare($sql);
            foreach ($args as $k => $v) { $stmt->bindValue($k, $v, SQLITE3_TEXT); }
            $stmt->bindValue(':l', $limit, SQLITE3_INTEGER);
            $stmt->bindValue(':o', $offset, SQLITE3_INTEGER);
            $res = $stmt->execute();
            $rows = [];
            while ($row = $res->fetchArray(SQLITE3_ASSOC)) { $rows[] = $row; }
            $db->close();
            foreach ($rows as &$row) { $row['timeline'] = $this->timeline($row['event_id']); }
            return $rows;
        } catch (\Throwable $e) {
            $this->fail($e->getMessage());
            return [];
        }
    }
}
