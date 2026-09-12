<?php

namespace OPNsense\DeviceMonitor;

class DeviceMonitor
{
    // ================================================================
    // PATHS - ALL IN ONE PLACE
    //
    //          Pointer to the configuration file containing default values
    //
    // ================================================================
    private static $defaultsFile = '/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json';
    private static $data = null;

    private static function loadDefaults()
    {
        if (self::$data === null) {
            $json = file_get_contents(self::$defaultsFile);
            self::$data = json_decode($json, true);
        }
        return self::$data;
    }

    public static function getPaths()
    {
        $data = self::loadDefaults();
        return $data['paths'];
    }

    public static function getPath($key)
    {
        $paths = self::getPaths();
        return isset($paths[$key]) ? $paths[$key] : null;
    }

    private static function formatUtcForDisplay($value)
    {
        $value = trim((string)$value);

        if ($value === '') {
            return $value;
        }

        try {
            $utc = new \DateTimeZone('UTC');
            $local = new \DateTimeZone(date_default_timezone_get());
            $date = new \DateTimeImmutable($value, $utc);

            return $date
                ->setTimezone($local)
                ->format('d.m.Y - H:i:s T');
        } catch (\Exception $e) {
            return $value;
        }
    }


    public static function getConfig()
    {
        $data = self::loadDefaults();
        $configFilePath = $data['paths']['configFile'];

        // Load config.json if it exists
        if (file_exists($configFilePath)) {
            $json = file_get_contents($configFilePath);
            $savedConfig = json_decode($json, true);

            // Merge saved values over current defaults. This makes newly
            // added settings (for example Direct SMTP) available immediately
            // after an upgrade without deleting the existing config.json.
            if ($savedConfig !== null && is_array($savedConfig)) {
                unset($savedConfig['paths']);
                $config = array_merge($data['config'], $savedConfig);
                $config['paths'] = $data['paths'];
                return $config;
            }
        }

        // Otherwise return defaults
        $config = $data['config'];
        $config['paths'] = $data['paths'];
        return $config;
    }


    // ========================================
    // PATH ACCESSORS (for Controllers)
    // ========================================


    /**
     * Return the PID file path
     */
    public function getPidFilePath()
    {
        return self::getPath('pidFile');
    }


    /**
     * Return the database path
     */
    public function getDbFilePath()
    {
        return self::getPath('dbFile');
    }

    /**
     * Return the configuration file path
     */
    public function getConfigFilePath()
    {
        return self::getPath('configFile');
    }

    private function recordTimelineActivityEvent(
        $db,
        $mac,
        $lifecycleId,
        $eventType,
        $oldValue = null,
        $newValue = null,
        $details = null,
        $occurredAt = null
    ) {
        $stmt = $db->prepare(
            'INSERT INTO device_activity_events ' .
            '(mac, lifecycle_id, event_type, occurred_at, ' .
            'old_value, new_value, details) ' .
            'VALUES (:mac, :lifecycle_id, :event_type, ' .
            'COALESCE(:occurred_at, CURRENT_TIMESTAMP), ' .
            ':old_value, :new_value, :details)'
        );

        if ($stmt === false) {
            return false;
        }

        $stmt->bindValue(
            ':mac',
            strtolower(trim((string)$mac)),
            SQLITE3_TEXT
        );

        if ($lifecycleId === null || (int)$lifecycleId <= 0) {
            $stmt->bindValue(':lifecycle_id', null, SQLITE3_NULL);
        } else {
            $stmt->bindValue(
                ':lifecycle_id',
                (int)$lifecycleId,
                SQLITE3_INTEGER
            );
        }

        $stmt->bindValue(
            ':event_type',
            trim((string)$eventType),
            SQLITE3_TEXT
        );

        foreach (
            [
                ':old_value' => $oldValue,
                ':new_value' => $newValue,
                ':details' => $details,
                ':occurred_at' => $occurredAt
            ] as $name => $value
        ) {
            $stmt->bindValue(
                $name,
                $value,
                $value === null ? SQLITE3_NULL : SQLITE3_TEXT
            );
        }

        return $stmt->execute() !== false;
    }

    public function updateHostname($mac, $hostname)
    {
        $db = $this->getDb();
        $mac = strtolower(trim((string)$mac));
        $hostname = trim((string)$hostname);

        if ($mac === '') {
            $db->close();
            return false;
        }

        if (!$db->exec('BEGIN IMMEDIATE TRANSACTION')) {
            $db->close();
            return false;
        }

        try {
            $stmt = $db->prepare(
                'SELECT custom_hostname, lifecycle_id FROM devices ' .
                'WHERE lower(trim(mac)) = :mac LIMIT 1'
            );

            if ($stmt === false) {
                throw new \RuntimeException(
                    'Unable to prepare friendly-name lookup'
                );
            }

            $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
            $result = $stmt->execute();
            $device = $result
                ? $result->fetchArray(SQLITE3_ASSOC)
                : false;

            if (!$device) {
                throw new \RuntimeException('Device not found');
            }

            $oldHostname = trim(
                (string)($device['custom_hostname'] ?? '')
            );
            $lifecycleId = isset($device['lifecycle_id'])
                ? (int)$device['lifecycle_id']
                : 0;

            if ($oldHostname === $hostname) {
                if (!$db->exec('COMMIT')) {
                    throw new \RuntimeException(
                        'Unable to commit unchanged friendly name'
                    );
                }

                $db->close();
                return true;
            }

            $stmt = $db->prepare(
                'UPDATE devices SET custom_hostname = :hostname ' .
                'WHERE lower(trim(mac)) = :mac'
            );

            if ($stmt === false) {
                throw new \RuntimeException(
                    'Unable to prepare friendly-name update'
                );
            }

            $stmt->bindValue(
                ':hostname',
                $hostname === '' ? null : $hostname,
                $hostname === '' ? SQLITE3_NULL : SQLITE3_TEXT
            );
            $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);

            if ($stmt->execute() === false || $db->changes() !== 1) {
                throw new \RuntimeException(
                    'Unable to update friendly name'
                );
            }

            if ($lifecycleId > 0) {
                $stmt = $db->prepare(
                    'UPDATE device_lifecycles ' .
                    'SET custom_hostname = :hostname ' .
                    "WHERE id = :id AND status = 'active'"
                );

                if ($stmt === false) {
                    throw new \RuntimeException(
                        'Unable to prepare lifecycle friendly-name update'
                    );
                }

                $stmt->bindValue(
                    ':hostname',
                    $hostname === '' ? null : $hostname,
                    $hostname === '' ? SQLITE3_NULL : SQLITE3_TEXT
                );
                $stmt->bindValue(':id', $lifecycleId, SQLITE3_INTEGER);

                if ($stmt->execute() === false) {
                    throw new \RuntimeException(
                        'Unable to update lifecycle friendly name'
                    );
                }
            }

            if (!$this->recordTimelineActivityEvent(
                $db,
                $mac,
                $lifecycleId,
                'FRIENDLY_NAME_CHANGED',
                $oldHostname,
                $hostname,
                'User-updated friendly name'
            )) {
                throw new \RuntimeException(
                    'Unable to record friendly-name history'
                );
            }

            if (!$db->exec('COMMIT')) {
                throw new \RuntimeException(
                    'Unable to commit friendly-name update'
                );
            }

            $db->close();
            return true;
        } catch (\Throwable $e) {
            @$db->exec('ROLLBACK');
            $db->close();
            return false;
        }
    }

    public function setIdentityEventResolved($id, $resolved)
    {
        $db = $this->getDb();
        $id = (int)$id;
        $resolved = (bool)$resolved;

        if ($id <= 0) {
            $db->close();
            return false;
        }

        if (!$db->exec('BEGIN IMMEDIATE TRANSACTION')) {
            $db->close();
            return false;
        }

        try {
            $tableExists = (int)$db->querySingle(
                "SELECT COUNT(*) FROM sqlite_master " .
                "WHERE type = 'table' " .
                "AND name = 'device_identity_events'"
            );

            if ($tableExists !== 1) {
                throw new \RuntimeException(
                    'Identity-event table not found'
                );
            }

            $columns = [];
            $columnResult = $db->query(
                'PRAGMA table_info(device_identity_events)'
            );

            while (
                $columnResult &&
                ($column = $columnResult->fetchArray(SQLITE3_ASSOC))
            ) {
                $columns[$column['name']] = true;
            }

            $lifecycleSelect =
                isset($columns['lifecycle_id'])
                    ? 'lifecycle_id'
                    : 'NULL AS lifecycle_id';

            $stmt = $db->prepare(
                'SELECT id, mac, event_type, resolved_at, ' .
                $lifecycleSelect . ' ' .
                'FROM device_identity_events WHERE id = :id'
            );

            if ($stmt === false) {
                throw new \RuntimeException(
                    'Unable to prepare identity-event lookup'
                );
            }

            $stmt->bindValue(':id', $id, SQLITE3_INTEGER);
            $result = $stmt->execute();
            $event = $result
                ? $result->fetchArray(SQLITE3_ASSOC)
                : false;

            if (!$event) {
                throw new \RuntimeException('Identity event not found');
            }

            $mac = strtolower(trim((string)($event['mac'] ?? '')));
            $eventType = trim((string)($event['event_type'] ?? ''));
            $resolvedAt = trim((string)($event['resolved_at'] ?? ''));
            $lifecycleId = isset($event['lifecycle_id'])
                ? (int)$event['lifecycle_id']
                : 0;
            $wasResolved = $resolvedAt !== '';

            if ($resolved === $wasResolved) {
                if (!$db->exec('COMMIT')) {
                    throw new \RuntimeException(
                        'Unable to commit unchanged identity status'
                    );
                }

                $db->close();
                return true;
            }

            if ($resolved) {
                $stmt = $db->prepare(
                    'UPDATE device_identity_events ' .
                    'SET resolved_at = CURRENT_TIMESTAMP ' .
                    'WHERE id = :id'
                );

                if ($stmt === false) {
                    throw new \RuntimeException(
                        'Unable to prepare identity resolution'
                    );
                }

                $stmt->bindValue(':id', $id, SQLITE3_INTEGER);

                if ($stmt->execute() === false || $db->changes() !== 1) {
                    throw new \RuntimeException(
                        'Unable to resolve identity event'
                    );
                }
            } else {
                if (!$this->recordTimelineActivityEvent(
                    $db,
                    $mac,
                    $lifecycleId,
                    'IDENTITY_RESOLVED',
                    'unresolved',
                    'resolved',
                    $eventType,
                    $resolvedAt
                )) {
                    throw new \RuntimeException(
                        'Unable to preserve identity resolution history'
                    );
                }

                if (!$this->recordTimelineActivityEvent(
                    $db,
                    $mac,
                    $lifecycleId,
                    'IDENTITY_REOPENED',
                    'resolved',
                    'unresolved',
                    $eventType
                )) {
                    throw new \RuntimeException(
                        'Unable to record identity reopen history'
                    );
                }

                $stmt = $db->prepare(
                    'UPDATE device_identity_events ' .
                    'SET resolved_at = NULL WHERE id = :id'
                );

                if ($stmt === false) {
                    throw new \RuntimeException(
                        'Unable to prepare identity reopen'
                    );
                }

                $stmt->bindValue(':id', $id, SQLITE3_INTEGER);

                if ($stmt->execute() === false || $db->changes() !== 1) {
                    throw new \RuntimeException(
                        'Unable to reopen identity event'
                    );
                }
            }

            if (!$db->exec('COMMIT')) {
                throw new \RuntimeException(
                    'Unable to commit identity-event status'
                );
            }

            $db->close();
            return true;
        } catch (\Throwable $e) {
            @$db->exec('ROLLBACK');
            $db->close();
            return false;
        }
    }

    public function updateComments($mac, $comments)
    {
        $db = $this->getDb();
        $comments = trim((string)$comments);

        if ($comments === '') {
            $stmt = $db->prepare('UPDATE devices SET comments = NULL WHERE mac = :mac');
            $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
        } else {
            $stmt = $db->prepare('UPDATE devices SET comments = :comments WHERE mac = :mac');
            $stmt->bindValue(':comments', $comments, SQLITE3_TEXT);
            $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
        }

        $stmt->execute();
        $changes = $db->changes();
        $db->close();
        return $changes > 0;
    }


    public function getLifecycleComments($lifecycleId)
    {
        $db = $this->getDb();
        $lifecycleId = (int)$lifecycleId;

        if ($lifecycleId <= 0) {
            $db->close();
            return [];
        }

        $stmt = $db->prepare(
            'SELECT id, lifecycle_id, comment, created_at, updated_at, deleted_at ' .
            'FROM device_comments ' .
            'WHERE lifecycle_id = :lifecycle_id ' .
            'ORDER BY created_at DESC, id DESC'
        );

        if ($stmt === false) {
            $db->close();
            return [];
        }

        $stmt->bindValue(
            ':lifecycle_id',
            $lifecycleId,
            SQLITE3_INTEGER
        );

        $result = $stmt->execute();
        $comments = [];

        if ($result !== false) {
            while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
                $versionStmt = $db->prepare(
                    'SELECT id, comment_id, lifecycle_id, comment, action, created_at ' .
                    'FROM device_comment_versions ' .
                    'WHERE comment_id = :comment_id ' .
                    'AND lifecycle_id = :lifecycle_id ' .
                    'ORDER BY created_at ASC, id ASC'
                );

                $versions = [];
                if ($versionStmt !== false) {
                    $versionStmt->bindValue(
                        ':comment_id',
                        (int)$row['id'],
                        SQLITE3_INTEGER
                    );
                    $versionStmt->bindValue(
                        ':lifecycle_id',
                        $lifecycleId,
                        SQLITE3_INTEGER
                    );

                    $versionResult = $versionStmt->execute();
                    if ($versionResult !== false) {
                        while (
                            $version = $versionResult->fetchArray(
                                SQLITE3_ASSOC
                            )
                        ) {
                            $version['created_at'] =
                                self::formatUtcForDisplay(
                                    $version['created_at'] ?? ''
                                );
                            $versions[] = $version;
                        }
                    }
                }

                foreach (
                    ['created_at', 'updated_at', 'deleted_at'] as $field
                ) {
                    $row[$field] = self::formatUtcForDisplay(
                        $row[$field] ?? ''
                    );
                }

                $row['versions'] = $versions;
                $comments[] = $row;
            }
        }

        $db->close();
        return $comments;
    }

    public function addLifecycleComment($lifecycleId, $comment)
    {
        $db = $this->getDb();
        $lifecycleId = (int)$lifecycleId;
        $comment = trim((string)$comment);

        if ($lifecycleId <= 0 || $comment === '') {
            $db->close();
            return 0;
        }

        try {
            if (!$db->exec('BEGIN IMMEDIATE TRANSACTION')) {
                throw new \RuntimeException(
                    'Unable to begin comment transaction'
                );
            }

            $stmt = $db->prepare(
                "SELECT id FROM device_lifecycles " .
                "WHERE id = :id AND status = 'active' LIMIT 1"
            );
            if ($stmt === false) {
                throw new \RuntimeException(
                    'Unable to validate comment lifecycle'
                );
            }

            $stmt->bindValue(':id', $lifecycleId, SQLITE3_INTEGER);
            $result = $stmt->execute();
            $row = $result
                ? $result->fetchArray(SQLITE3_ASSOC)
                : false;

            if (!$row) {
                throw new \RuntimeException(
                    'Lifecycle is not active'
                );
            }

            $stmt = $db->prepare(
                'INSERT INTO device_comments (lifecycle_id, comment) ' .
                'VALUES (:lifecycle_id, :comment)'
            );
            if ($stmt === false) {
                throw new \RuntimeException(
                    'Unable to prepare comment insert'
                );
            }

            $stmt->bindValue(
                ':lifecycle_id',
                $lifecycleId,
                SQLITE3_INTEGER
            );
            $stmt->bindValue(':comment', $comment, SQLITE3_TEXT);

            if ($stmt->execute() === false) {
                throw new \RuntimeException(
                    'Unable to insert comment'
                );
            }

            $commentId = (int)$db->lastInsertRowID();

            $stmt = $db->prepare(
                'INSERT INTO device_comment_versions ' .
                '(comment_id, lifecycle_id, comment, action) ' .
                "VALUES (:comment_id, :lifecycle_id, :comment, 'created')"
            );
            if ($stmt === false) {
                throw new \RuntimeException(
                    'Unable to prepare comment history insert'
                );
            }

            $stmt->bindValue(
                ':comment_id',
                $commentId,
                SQLITE3_INTEGER
            );
            $stmt->bindValue(
                ':lifecycle_id',
                $lifecycleId,
                SQLITE3_INTEGER
            );
            $stmt->bindValue(':comment', $comment, SQLITE3_TEXT);

            if ($stmt->execute() === false) {
                throw new \RuntimeException(
                    'Unable to insert comment history'
                );
            }

            if (!$db->exec('COMMIT')) {
                throw new \RuntimeException(
                    'Unable to commit comment transaction'
                );
            }

            $db->close();
            return $commentId;
        } catch (\Exception $e) {
            $db->exec('ROLLBACK');
            $db->close();
            return 0;
        }
    }

    public function updateLifecycleComment(
        $lifecycleId,
        $commentId,
        $comment
    ) {
        $db = $this->getDb();
        $lifecycleId = (int)$lifecycleId;
        $commentId = (int)$commentId;
        $comment = trim((string)$comment);

        if ($lifecycleId <= 0 || $commentId <= 0 || $comment === '') {
            $db->close();
            return false;
        }

        try {
            if (!$db->exec('BEGIN IMMEDIATE TRANSACTION')) {
                throw new \RuntimeException(
                    'Unable to begin comment update transaction'
                );
            }

            $stmt = $db->prepare(
                'UPDATE device_comments SET comment = :comment, ' .
                'updated_at = CURRENT_TIMESTAMP ' .
                'WHERE id = :id AND lifecycle_id = :lifecycle_id ' .
                'AND deleted_at IS NULL ' .
                'AND EXISTS (' .
                'SELECT 1 FROM device_lifecycles ' .
                "WHERE id = :lifecycle_id AND status = 'active'" .
                ')'
            );

            if ($stmt === false) {
                throw new \RuntimeException(
                    'Unable to prepare comment update'
                );
            }

            $stmt->bindValue(':comment', $comment, SQLITE3_TEXT);
            $stmt->bindValue(':id', $commentId, SQLITE3_INTEGER);
            $stmt->bindValue(
                ':lifecycle_id',
                $lifecycleId,
                SQLITE3_INTEGER
            );

            if ($stmt->execute() === false || $db->changes() <= 0) {
                throw new \RuntimeException(
                    'Comment update was not applied'
                );
            }

            $stmt = $db->prepare(
                'INSERT INTO device_comment_versions ' .
                '(comment_id, lifecycle_id, comment, action) ' .
                "VALUES (:comment_id, :lifecycle_id, :comment, 'edited')"
            );

            if ($stmt === false) {
                throw new \RuntimeException(
                    'Unable to prepare comment history update'
                );
            }

            $stmt->bindValue(
                ':comment_id',
                $commentId,
                SQLITE3_INTEGER
            );
            $stmt->bindValue(
                ':lifecycle_id',
                $lifecycleId,
                SQLITE3_INTEGER
            );
            $stmt->bindValue(':comment', $comment, SQLITE3_TEXT);

            if ($stmt->execute() === false) {
                throw new \RuntimeException(
                    'Unable to insert comment edit history'
                );
            }

            if (!$db->exec('COMMIT')) {
                throw new \RuntimeException(
                    'Unable to commit comment update transaction'
                );
            }

            $db->close();
            return true;
        } catch (\Exception $e) {
            $db->exec('ROLLBACK');
            $db->close();
            return false;
        }
    }

    public function deleteLifecycleComment($lifecycleId, $commentId)
    {
        $db = $this->getDb();
        $lifecycleId = (int)$lifecycleId;
        $commentId = (int)$commentId;

        if ($lifecycleId <= 0 || $commentId <= 0) {
            $db->close();
            return false;
        }

        try {
            if (!$db->exec('BEGIN IMMEDIATE TRANSACTION')) {
                throw new \RuntimeException(
                    'Unable to begin comment delete transaction'
                );
            }

            $stmt = $db->prepare(
                'SELECT c.comment FROM device_comments c ' .
                'JOIN device_lifecycles l ON l.id = c.lifecycle_id ' .
                'WHERE c.id = :id AND c.lifecycle_id = :lifecycle_id ' .
                'AND c.deleted_at IS NULL ' .
                "AND l.status = 'active' LIMIT 1"
            );

            if ($stmt === false) {
                throw new \RuntimeException(
                    'Unable to prepare comment delete validation'
                );
            }

            $stmt->bindValue(':id', $commentId, SQLITE3_INTEGER);
            $stmt->bindValue(
                ':lifecycle_id',
                $lifecycleId,
                SQLITE3_INTEGER
            );

            $result = $stmt->execute();
            $row = $result
                ? $result->fetchArray(SQLITE3_ASSOC)
                : false;

            if (!$row) {
                throw new \RuntimeException(
                    'Comment is not available for deletion'
                );
            }

            $comment = (string)$row['comment'];

            $stmt = $db->prepare(
                'UPDATE device_comments SET deleted_at = CURRENT_TIMESTAMP ' .
                'WHERE id = :id AND lifecycle_id = :lifecycle_id ' .
                'AND deleted_at IS NULL'
            );

            if ($stmt === false) {
                throw new \RuntimeException(
                    'Unable to prepare comment delete'
                );
            }

            $stmt->bindValue(':id', $commentId, SQLITE3_INTEGER);
            $stmt->bindValue(
                ':lifecycle_id',
                $lifecycleId,
                SQLITE3_INTEGER
            );

            if ($stmt->execute() === false || $db->changes() <= 0) {
                throw new \RuntimeException(
                    'Comment delete was not applied'
                );
            }

            $stmt = $db->prepare(
                'INSERT INTO device_comment_versions ' .
                '(comment_id, lifecycle_id, comment, action) ' .
                "VALUES (:comment_id, :lifecycle_id, :comment, 'deleted')"
            );

            if ($stmt === false) {
                throw new \RuntimeException(
                    'Unable to prepare comment delete history'
                );
            }

            $stmt->bindValue(
                ':comment_id',
                $commentId,
                SQLITE3_INTEGER
            );
            $stmt->bindValue(
                ':lifecycle_id',
                $lifecycleId,
                SQLITE3_INTEGER
            );
            $stmt->bindValue(':comment', $comment, SQLITE3_TEXT);

            if ($stmt->execute() === false) {
                throw new \RuntimeException(
                    'Unable to insert comment delete history'
                );
            }

            if (!$db->exec('COMMIT')) {
                throw new \RuntimeException(
                    'Unable to commit comment delete transaction'
                );
            }

            $db->close();
            return true;
        } catch (\Exception $e) {
            $db->exec('ROLLBACK');
            $db->close();
            return false;
        }
    }


    public function getDeviceLifecycles($mac)
    {
        $db = $this->getDb();
        $mac = strtolower(trim((string)$mac));

        if ($mac === '') {
            $db->close();
            return [];
        }

        $stmt = $db->prepare(
            'SELECT l.*, ' .
            '(SELECT COUNT(*) FROM device_comments c ' .
            'WHERE c.lifecycle_id = l.id) ' .
            'AS comment_count ' .
            'FROM device_lifecycles l ' .
            'WHERE lower(trim(l.mac)) = :mac ' .
            'ORDER BY COALESCE(l.first_seen, l.created_at) DESC, l.id DESC'
        );

        if ($stmt === false) {
            $db->close();
            return [];
        }

        $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
        $result = $stmt->execute();

        $lifecycles = [];

        if ($result !== false) {
            while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
                $row['id'] = (int)$row['id'];
                $row['comment_count'] = (int)$row['comment_count'];

                foreach (
                    ['first_seen', 'last_seen', 'archived_at', 'created_at']
                    as $field
                ) {
                    $row[$field] = self::formatUtcForDisplay(
                        $row[$field] ?? ''
                    );
                }

                $lifecycles[] = $row;
            }
        }

        $db->close();
        return $lifecycles;
    }

    /**
     * Return a normalized chronological activity timeline for one device.
     *
     * Existing authoritative history tables remain authoritative. This method
     * only aggregates and normalizes them; it does not duplicate history.
     */
    public function getDeviceTimeline($mac, $limit = 200)
    {
        $db = $this->getDb();
        $mac = strtolower(trim((string)$mac));
        $limit = max(1, min(500, (int)$limit));

        if ($mac === '') {
            $db->close();
            return [];
        }

        $events = [];

        $append = function (
            $source,
            $eventType,
            $timestamp,
            $lifecycleId,
            $recordId,
            array $data = []
        ) use (&$events) {
            $timestamp = trim((string)$timestamp);

            if ($timestamp === '') {
                return;
            }

            $events[] = [
                'source' => (string)$source,
                'event_type' => (string)$eventType,
                'occurred_at_utc' => $timestamp,
                'occurred_at' => self::formatUtcForDisplay($timestamp),
                'lifecycle_id' =>
                    $lifecycleId === null || $lifecycleId === ''
                        ? null
                        : (int)$lifecycleId,
                'record_id' => (int)$recordId,
                'data' => $data
            ];
        };

        $tableExists = static function ($db, $table) {
            $name = \SQLite3::escapeString((string)$table);

            return (int)$db->querySingle(
                "SELECT COUNT(*) FROM sqlite_master " .
                "WHERE type='table' AND name='" . $name . "'"
            ) === 1;
        };

        /*
         * Lifecycle start/archive history.
         *
         * last_seen is intentionally not emitted as an activity event.
         */
        if ($tableExists($db, 'device_lifecycles')) {
            $stmt = $db->prepare(
                'SELECT id, first_seen, archived_at, created_at ' .
                'FROM device_lifecycles ' .
                'WHERE lower(trim(mac)) = :mac ' .
                'ORDER BY MAX(' .
                "COALESCE(archived_at, ''), " .
                "COALESCE(first_seen, created_at, '')" .
                ') DESC, id DESC LIMIT :limit'
            );

            if ($stmt !== false) {
                $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
                $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);
                $result = $stmt->execute();

                while (
                    $result &&
                    ($row = $result->fetchArray(SQLITE3_ASSOC))
                ) {
                    $startedAt = trim(
                        (string)($row['first_seen'] ?? '')
                    );

                    if ($startedAt === '') {
                        $startedAt =
                            (string)($row['created_at'] ?? '');
                    }

                    $append(
                        'lifecycle',
                        'LIFECYCLE_STARTED',
                        $startedAt,
                        $row['id'],
                        $row['id']
                    );

                    if (
                        trim(
                            (string)($row['archived_at'] ?? '')
                        ) !== ''
                    ) {
                        $append(
                            'lifecycle',
                            'LIFECYCLE_ARCHIVED',
                            $row['archived_at'],
                            $row['id'],
                            $row['id']
                        );
                    }
                }
            }
        }

        /*
         * Timestamped lifecycle note history.
         *
         * Backfilled "migrated" versions are intentionally hidden because
         * they do not represent a user action at the migration timestamp.
         */
        if (
            $tableExists($db, 'device_comment_versions') &&
            $tableExists($db, 'device_lifecycles')
        ) {
            $stmt = $db->prepare(
                'SELECT v.id, v.comment_id, v.lifecycle_id, v.comment, ' .
                'v.action, v.created_at ' .
                'FROM device_comment_versions v ' .
                'JOIN device_lifecycles l ON l.id = v.lifecycle_id ' .
                'WHERE lower(trim(l.mac)) = :mac ' .
                "AND lower(trim(COALESCE(v.action, ''))) <> 'migrated' " .
                'ORDER BY v.created_at DESC, v.id DESC LIMIT :limit'
            );

            if ($stmt !== false) {
                $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
                $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);
                $result = $stmt->execute();

                while (
                    $result &&
                    ($row = $result->fetchArray(SQLITE3_ASSOC))
                ) {
                    $action = strtolower(trim(
                        (string)($row['action'] ?? '')
                    ));

                    if ($action === 'created') {
                        $eventType = 'NOTE_CREATED';
                    } elseif (
                        $action === 'edited' ||
                        $action === 'updated'
                    ) {
                        $eventType = 'NOTE_UPDATED';
                    } elseif (
                        $action === 'deleted' ||
                        $action === 'archived'
                    ) {
                        $eventType = 'NOTE_ARCHIVED';
                    } else {
                        $eventType = 'NOTE_CHANGED';
                    }

                    $append(
                        'note',
                        $eventType,
                        $row['created_at'] ?? '',
                        $row['lifecycle_id'] ?? null,
                        $row['id'],
                        [
                            'comment_id' =>
                                (int)$row['comment_id'],
                            'action' =>
                                (string)($row['action'] ?? ''),
                            'comment' =>
                                (string)($row['comment'] ?? '')
                        ]
                    );
                }
            }
        }

        /*
         * Device state/service transitions persisted by the scanner.
         */
        if ($tableExists($db, 'device_activity_events')) {
            $stmt = $db->prepare(
                'SELECT id, lifecycle_id, event_type, occurred_at, ' .
                'old_value, new_value, details ' .
                'FROM device_activity_events ' .
                'WHERE lower(trim(mac)) = :mac ' .
                'ORDER BY occurred_at DESC, id DESC LIMIT :limit'
            );

            if ($stmt !== false) {
                $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
                $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);
                $result = $stmt->execute();

                while (
                    $result &&
                    ($row = $result->fetchArray(SQLITE3_ASSOC))
                ) {
                    $append(
                        'activity',
                        $row['event_type'] ?? 'ACTIVITY_CHANGED',
                        $row['occurred_at'] ?? '',
                        $row['lifecycle_id'] ?? null,
                        $row['id'],
                        [
                            'old_value' =>
                                $row['old_value'] ?? null,
                            'new_value' =>
                                $row['new_value'] ?? null,
                            'details' =>
                                $row['details'] ?? null
                        ]
                    );
                }
            }
        }

        /*
         * Identity anomaly detection and resolution.
         */
        if ($tableExists($db, 'device_identity_events')) {
            $columns = [];
            $columnResult = $db->query(
                'PRAGMA table_info(device_identity_events)'
            );

            while (
                $columnResult &&
                ($column = $columnResult->fetchArray(SQLITE3_ASSOC))
            ) {
                $columns[$column['name']] = true;
            }

            $lifecycleSelect =
                isset($columns['lifecycle_id'])
                    ? 'lifecycle_id'
                    : 'NULL AS lifecycle_id';

            $stmt = $db->prepare(
                'SELECT id, ' . $lifecycleSelect . ', ' .
                'event_type, severity, detected_at, ip, other_ip, ' .
                'other_mac, interface, other_interface, details, ' .
                'resolved_at ' .
                'FROM device_identity_events ' .
                'WHERE lower(trim(mac)) = :mac ' .
                'ORDER BY MAX(' .
                "COALESCE(resolved_at, ''), " .
                "COALESCE(detected_at, '')" .
                ') DESC, id DESC LIMIT :limit'
            );

            if ($stmt !== false) {
                $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
                $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);
                $result = $stmt->execute();

                while (
                    $result &&
                    ($row = $result->fetchArray(SQLITE3_ASSOC))
                ) {
                    $identityData = [
                        'severity' =>
                            (string)($row['severity'] ?? ''),
                        'ip' => $row['ip'] ?? null,
                        'other_ip' => $row['other_ip'] ?? null,
                        'other_mac' => $row['other_mac'] ?? null,
                        'interface' => $row['interface'] ?? null,
                        'other_interface' =>
                            $row['other_interface'] ?? null,
                        'details' => $row['details'] ?? null
                    ];

                    $append(
                        'identity',
                        $row['event_type'] ?? 'IDENTITY_CHANGED',
                        $row['detected_at'] ?? '',
                        $row['lifecycle_id'] ?? null,
                        $row['id'],
                        $identityData
                    );

                    if (
                        trim(
                            (string)($row['resolved_at'] ?? '')
                        ) !== ''
                    ) {
                        $resolvedData = $identityData;
                        $resolvedData['identity_event_type'] =
                            (string)($row['event_type'] ?? '');

                        $append(
                            'identity',
                            'IDENTITY_RESOLVED',
                            $row['resolved_at'],
                            $row['lifecycle_id'] ?? null,
                            $row['id'],
                            $resolvedData
                        );
                    }
                }
            }
        }

        /*
         * Targeted Nmap result history.
         */
        if ($tableExists($db, 'nmap_scan_history')) {
            $columns = [];
            $columnResult = $db->query(
                'PRAGMA table_info(nmap_scan_history)'
            );

            while (
                $columnResult &&
                ($column = $columnResult->fetchArray(SQLITE3_ASSOC))
            ) {
                $columns[$column['name']] = true;
            }

            $lifecycleSelect =
                isset($columns['lifecycle_id'])
                    ? 'lifecycle_id'
                    : 'NULL AS lifecycle_id';

            $osSelect =
                isset($columns['os_hint'])
                    ? 'os_hint'
                    : 'NULL AS os_hint';

            $portCountSelect =
                isset($columns['open_port_count'])
                    ? 'open_port_count'
                    : 'NULL AS open_port_count';

            $stmt = $db->prepare(
                'SELECT id, ' . $lifecycleSelect . ', ' .
                'mac, ip, scan_type, started_at, finished_at, ' .
                'success, error, ' .
                $osSelect . ', ' .
                $portCountSelect . ' ' .
                'FROM nmap_scan_history ' .
                'WHERE lower(trim(mac)) = :mac ' .
                'ORDER BY COALESCE(finished_at, started_at) DESC, ' .
                'id DESC LIMIT :limit'
            );

            if ($stmt !== false) {
                $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
                $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);
                $result = $stmt->execute();

                while (
                    $result &&
                    ($row = $result->fetchArray(SQLITE3_ASSOC))
                ) {
                    $timestamp = trim(
                        (string)($row['finished_at'] ?? '')
                    );

                    if ($timestamp === '') {
                        $timestamp =
                            (string)($row['started_at'] ?? '');
                    }

                    $success =
                        $row['success'] === null
                            ? null
                            : (int)$row['success'];

                    $eventType =
                        $success === 0
                            ? 'NMAP_SCAN_FAILED'
                            : 'NMAP_SCAN_COMPLETED';

                    $append(
                        'scan',
                        $eventType,
                        $timestamp,
                        $row['lifecycle_id'] ?? null,
                        $row['id'],
                        [
                            'ip' => $row['ip'] ?? null,
                            'scan_type' =>
                                $row['scan_type'] ?? null,
                            'success' => $success,
                            'error' => $row['error'] ?? null,
                            'os_hint' =>
                                $row['os_hint'] ?? null,
                            'open_port_count' =>
                                $row['open_port_count'] === null
                                    ? null
                                    : (int)$row['open_port_count']
                        ]
                    );
                }
            }
        }

        /*
         * Initial verified service discovery is already retained by
         * device_services.first_detected. Only stable endpoint identity
         * fields are emitted here because status/product/version are mutable
         * current-state fields rather than historical snapshots.
         */
        if ($tableExists($db, 'device_services')) {
            $stmt = $db->prepare(
                'SELECT id, ip, interface, service_type, port, protocol, ' .
                'detection_method, first_detected ' .
                'FROM device_services ' .
                'WHERE lower(trim(mac)) = :mac ' .
                'ORDER BY first_detected DESC, id DESC LIMIT :limit'
            );

            if ($stmt !== false) {
                $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
                $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);
                $result = $stmt->execute();

                while (
                    $result &&
                    ($row = $result->fetchArray(SQLITE3_ASSOC))
                ) {
                    $append(
                        'service',
                        'SERVICE_DISCOVERED',
                        $row['first_detected'] ?? '',
                        null,
                        $row['id'],
                        [
                            'ip' => $row['ip'] ?? null,
                            'interface' =>
                                $row['interface'] ?? null,
                            'service_type' =>
                                $row['service_type'] ?? null,
                            'port' =>
                                isset($row['port'])
                                    ? (int)$row['port']
                                    : null,
                            'protocol' =>
                                $row['protocol'] ?? null,
                            'detection_method' =>
                                $row['detection_method'] ?? null
                        ]
                    );
                }
            }
        }

        $db->close();

        usort($events, static function ($a, $b) {
            $timeCompare = strcmp(
                (string)$b['occurred_at_utc'],
                (string)$a['occurred_at_utc']
            );

            if ($timeCompare !== 0) {
                return $timeCompare;
            }

            $recordCompare =
                (int)$b['record_id'] <=>
                (int)$a['record_id'];

            if ($recordCompare !== 0) {
                return $recordCompare;
            }

            return strcmp(
                (string)$a['source'],
                (string)$b['source']
            );
        });

        return array_slice($events, 0, $limit);
    }

    public function getDeviceLifecycleState($mac)
    {
        $db = $this->getDb();
        $mac = strtolower(trim((string)$mac));

        if ($mac === '') {
            $db->close();
            return null;
        }

        $stmt = $db->prepare(
            'SELECT lifecycle_id, return_pending, is_active FROM devices ' .
            'WHERE lower(trim(mac)) = :mac LIMIT 1'
        );

        if ($stmt === false) {
            $db->close();
            return null;
        }

        $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
        $result = $stmt->execute();
        $row = $result
            ? $result->fetchArray(SQLITE3_ASSOC)
            : false;

        $db->close();

        if (!$row) {
            return null;
        }

        return [
            'lifecycle_id' => $row['lifecycle_id'] === null
                ? null
                : (int)$row['lifecycle_id'],
            'return_pending' => (int)$row['return_pending'],
            'is_active' => isset($row['is_active'])
                ? (int)$row['is_active']
                : 0
        ];
    }

    /**
     * Return the active user-confirmed physical-device group for one MAC.
     *
     * This is read-only and does not alter device, lifecycle or identity state.
     */
    public function getPhysicalDeviceForMac($mac)
    {
        $db = $this->getDb();
        $mac = strtolower(trim((string)$mac));

        if ($mac === '') {
            $db->close();
            return null;
        }

        $stmt = $db->prepare(
            'SELECT p.id, p.name, p.created_at, p.updated_at, p.archived_at, ' .
            'm.added_at AS membership_added_at ' .
            'FROM physical_device_memberships m ' .
            'JOIN physical_devices p ON p.id = m.physical_device_id ' .
            'WHERE lower(trim(m.mac)) = :mac ' .
            'AND m.removed_at IS NULL ' .
            'AND p.archived_at IS NULL ' .
            'ORDER BY m.id DESC LIMIT 1'
        );

        if ($stmt === false) {
            $db->close();
            return null;
        }

        $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
        $result = $stmt->execute();
        $group = $result
            ? $result->fetchArray(SQLITE3_ASSOC)
            : false;

        if (!$group) {
            $db->close();
            return null;
        }

        $group['id'] = (int)$group['id'];
        $group['members'] = [];

        $memberStmt = $db->prepare(
            'SELECT id, mac, added_at ' .
            'FROM physical_device_memberships ' .
            'WHERE physical_device_id = :physical_device_id ' .
            'AND removed_at IS NULL ' .
            'ORDER BY lower(trim(mac)), id'
        );

        if ($memberStmt === false) {
            $db->close();
            return null;
        }

        $memberStmt->bindValue(
            ':physical_device_id',
            $group['id'],
            SQLITE3_INTEGER
        );
        $memberResult = $memberStmt->execute();

        if ($memberResult !== false) {
            while ($member = $memberResult->fetchArray(SQLITE3_ASSOC)) {
                $member['id'] = (int)$member['id'];
                $member['mac'] = strtolower(
                    trim((string)($member['mac'] ?? ''))
                );
                $group['members'][] = $member;
            }
        }

        $db->close();
        return $group;
    }

    /**
     * Save configuration
     * @param array $data Data to save
     * @return bool True if saving succeeded
     */
    public function setConfig($data)
    {
        $file_name = self::getPath('configFile');

        // Ensure the directory exists without blocking the save
        $dir = dirname($file_name);
        if (!is_dir($dir)) {
            try {
                @mkdir($dir, 0755, true);
            } catch (\Exception $e) {
                // Ignore the error and attempt to save the file anyway
            }
        }

        // Paths are runtime metadata from defaults.json, not user settings.
        // Do not duplicate them into config.json.
        unset($data['paths']);

        // The config may contain an SMTP password, therefore keep it readable
        // only by root/system services.
        $json = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
        $result = @file_put_contents($file_name, $json, LOCK_EX);

        if ($result !== false) {
            @chmod($file_name, 0600);
            return true;
        }

        return false;
    }


    // ========================================
    // DATABASE
    // ========================================

    private function getDb()
    {
        $file_mame = self::getPath('dbFile');
        $dbDir = dirname($file_mame);
        if (!is_dir($dbDir)) {
            mkdir($dbDir, 0755, true);
        }

        if (!file_exists($file_mame)) {
            $this->initDatabase();
        }

        $db = new \SQLite3($file_mame);
        $db->busyTimeout(5000);

        // Migration for existing installations: getDb() is also used by GUI
        // actions, so do not rely on scan_network.py having run first.
        $db->exec('CREATE TABLE IF NOT EXISTS deleted_devices (
            mac TEXT PRIMARY KEY,
            last_seen DATETIME,
            deleted_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )');

        // Per-device user comments.
        @$db->exec('ALTER TABLE devices ADD COLUMN comments TEXT DEFAULT NULL');

        // Device lifecycle and multi-comment history.
        $db->exec('CREATE TABLE IF NOT EXISTS device_lifecycles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mac TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT \'active\',
            custom_hostname TEXT DEFAULT NULL,
            hostname TEXT DEFAULT NULL,
            hostname_source TEXT DEFAULT \'\',
            ip TEXT DEFAULT NULL,
            vendor TEXT DEFAULT NULL,
            vlan TEXT DEFAULT NULL,
            first_seen DATETIME,
            last_seen DATETIME,
            archived_at DATETIME DEFAULT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )');

        $db->exec("CREATE UNIQUE INDEX IF NOT EXISTS idx_device_lifecycles_active_mac
            ON device_lifecycles(mac) WHERE status = 'active'");

        $db->exec('CREATE INDEX IF NOT EXISTS idx_device_lifecycles_mac_status
            ON device_lifecycles(mac, status)');

        // User-confirmed physical-device grouping. This is an additive layer
        // above MAC identities; memberships are archived with removed_at.
        $db->exec('CREATE TABLE IF NOT EXISTS physical_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT NULL,
            archived_at DATETIME DEFAULT NULL
        )');

        $db->exec('CREATE TABLE IF NOT EXISTS physical_device_memberships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            physical_device_id INTEGER NOT NULL,
            mac TEXT NOT NULL,
            added_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            removed_at DATETIME DEFAULT NULL
        )');

        $db->exec('CREATE INDEX IF NOT EXISTS idx_physical_device_memberships_group
            ON physical_device_memberships(physical_device_id, removed_at)');

        $db->exec('CREATE UNIQUE INDEX IF NOT EXISTS idx_physical_device_memberships_active_mac
            ON physical_device_memberships(lower(trim(mac)))
            WHERE removed_at IS NULL');

        $db->exec('CREATE TABLE IF NOT EXISTS device_activity_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mac TEXT NOT NULL,
            lifecycle_id INTEGER DEFAULT NULL,
            event_type TEXT NOT NULL,
            occurred_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            old_value TEXT DEFAULT NULL,
            new_value TEXT DEFAULT NULL,
            details TEXT DEFAULT NULL
        )');

        $db->exec('CREATE INDEX IF NOT EXISTS idx_device_activity_events_mac_occurred
            ON device_activity_events(mac, occurred_at DESC)');

        $db->exec('CREATE INDEX IF NOT EXISTS idx_device_activity_events_lifecycle_occurred
            ON device_activity_events(lifecycle_id, occurred_at DESC)');

        $db->exec('CREATE TABLE IF NOT EXISTS device_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lifecycle_id INTEGER NOT NULL,
            comment TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT NULL,
            deleted_at DATETIME DEFAULT NULL
        )');

        $db->exec('CREATE INDEX IF NOT EXISTS idx_device_comments_lifecycle_created
            ON device_comments(lifecycle_id, created_at DESC)');

        $db->exec('CREATE TABLE IF NOT EXISTS device_comment_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comment_id INTEGER NOT NULL,
            lifecycle_id INTEGER NOT NULL,
            comment TEXT NOT NULL,
            action TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )');

        $db->exec('CREATE INDEX IF NOT EXISTS idx_device_comment_versions_comment_created
            ON device_comment_versions(comment_id, created_at ASC, id ASC)');

        $db->exec(
            "INSERT INTO device_comment_versions " .
            "(comment_id, lifecycle_id, comment, action, created_at) " .
            "SELECT c.id, c.lifecycle_id, c.comment, " .
            "CASE WHEN c.updated_at IS NOT NULL THEN 'migrated' ELSE 'created' END, " .
            "COALESCE(c.updated_at, c.created_at, CURRENT_TIMESTAMP) " .
            "FROM device_comments c " .
            "WHERE NOT EXISTS (" .
            "SELECT 1 FROM device_comment_versions v " .
            "WHERE v.comment_id = c.id" .
            ")"
        );

        $db->exec(
            "INSERT INTO device_comment_versions " .
            "(comment_id, lifecycle_id, comment, action, created_at) " .
            "SELECT c.id, c.lifecycle_id, c.comment, 'deleted', c.deleted_at " .
            "FROM device_comments c " .
            "WHERE c.deleted_at IS NOT NULL " .
            "AND NOT EXISTS (" .
            "SELECT 1 FROM device_comment_versions v " .
            "WHERE v.comment_id = c.id AND v.action = 'deleted'" .
            ")"
        );

        @$db->exec('ALTER TABLE devices ADD COLUMN lifecycle_id INTEGER DEFAULT NULL');
        @$db->exec('ALTER TABLE devices ADD COLUMN return_pending INTEGER DEFAULT 0');
        @$db->exec('ALTER TABLE nmap_scan_history ADD COLUMN lifecycle_id INTEGER DEFAULT NULL');
        @$db->exec('ALTER TABLE device_identity_events ADD COLUMN lifecycle_id INTEGER DEFAULT NULL');

        // Nmap targeted-scan queue and retry state.
        @$db->exec('ALTER TABLE devices ADD COLUMN nmap_scan_pending INTEGER DEFAULT 0');
        @$db->exec('ALTER TABLE devices ADD COLUMN nmap_scan_attempts INTEGER DEFAULT 0');
        @$db->exec('ALTER TABLE devices ADD COLUMN nmap_next_attempt DATETIME DEFAULT NULL');
        @$db->exec('ALTER TABLE devices ADD COLUMN nmap_last_error TEXT DEFAULT NULL');

        if (!$this->backfillDeviceLifecycles($db)) {
            $db->close();
            throw new \RuntimeException(
                'Unable to backfill device lifecycles'
            );
        }


        return $db;
    }


    private function findActiveLifecycleId($db, $mac)
    {
        $mac = strtolower(trim((string)$mac));
        if ($mac === '') {
            return 0;
        }

        $stmt = $db->prepare(
            "SELECT id FROM device_lifecycles " .
            "WHERE mac = :mac AND status = 'active' LIMIT 1"
        );
        $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
        $result = $stmt->execute();
        $row = $result ? $result->fetchArray(SQLITE3_ASSOC) : false;

        return $row ? (int)$row['id'] : 0;
    }

    private function createLifecycle($db, $device, $firstSeen = null)
    {
        $mac = strtolower(trim((string)($device['mac'] ?? '')));
        if ($mac === '') {
            return 0;
        }

        $existing = $this->findActiveLifecycleId($db, $mac);
        if ($existing > 0) {
            return $existing;
        }

        if ($firstSeen === null || trim((string)$firstSeen) === '') {
            $firstSeen = $device['first_seen'] ?? null;
        }

        $stmt = $db->prepare(
            "INSERT INTO device_lifecycles " .
            "(mac, status, custom_hostname, hostname, hostname_source, " .
            "ip, vendor, vlan, first_seen, last_seen) " .
            "VALUES (:mac, 'active', :custom_hostname, :hostname, " .
            ":hostname_source, :ip, :vendor, :vlan, :first_seen, :last_seen)"
        );

        $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);

        foreach (['custom_hostname', 'hostname', 'ip', 'vendor', 'vlan'] as $field) {
            $value = $device[$field] ?? null;
            $stmt->bindValue(
                ':' . $field,
                $value,
                $value === null ? SQLITE3_NULL : SQLITE3_TEXT
            );
        }

        $stmt->bindValue(
            ':hostname_source',
            $device['hostname_source'] ?? '',
            SQLITE3_TEXT
        );

        $stmt->bindValue(
            ':first_seen',
            $firstSeen,
            $firstSeen === null ? SQLITE3_NULL : SQLITE3_TEXT
        );

        $lastSeen = $device['last_seen'] ?? null;
        $stmt->bindValue(
            ':last_seen',
            $lastSeen,
            $lastSeen === null ? SQLITE3_NULL : SQLITE3_TEXT
        );

        if ($stmt->execute() === false) {
            return 0;
        }

        return (int)$db->lastInsertRowID();
    }

    private function updateLifecycleSnapshot($db, $lifecycleId, $device)
    {
        $lifecycleId = (int)$lifecycleId;
        if ($lifecycleId <= 0) {
            return false;
        }

        $stmt = $db->prepare(
            "UPDATE device_lifecycles SET " .
            "custom_hostname = :custom_hostname, hostname = :hostname, " .
            "hostname_source = :hostname_source, ip = :ip, vendor = :vendor, " .
            "vlan = :vlan, last_seen = :last_seen " .
            "WHERE id = :id AND status = 'active'"
        );

        foreach (['custom_hostname', 'hostname', 'ip', 'vendor', 'vlan', 'last_seen'] as $field) {
            $value = $device[$field] ?? null;
            $stmt->bindValue(
                ':' . $field,
                $value,
                $value === null ? SQLITE3_NULL : SQLITE3_TEXT
            );
        }

        $stmt->bindValue(
            ':hostname_source',
            $device['hostname_source'] ?? '',
            SQLITE3_TEXT
        );
        $stmt->bindValue(':id', $lifecycleId, SQLITE3_INTEGER);

        return $stmt->execute() !== false;
    }

    private function archiveLifecycle($db, $lifecycleId)
    {
        $lifecycleId = (int)$lifecycleId;
        if ($lifecycleId <= 0) {
            return false;
        }

        $stmt = $db->prepare(
            "UPDATE device_lifecycles " .
            "SET status = 'archived', archived_at = CURRENT_TIMESTAMP " .
            "WHERE id = :id AND status = 'active'"
        );
        $stmt->bindValue(':id', $lifecycleId, SQLITE3_INTEGER);
        $stmt->execute();

        return $db->changes() > 0;
    }

    private function backfillDeviceLifecycles($db)
    {
        $result = $db->query(
            'SELECT * FROM devices ' .
            'WHERE (lifecycle_id IS NULL OR lifecycle_id = 0) ' .
            'AND COALESCE(return_pending, 0) = 0'
        );

        if ($result === false) {
            return false;
        }

        $devices = [];
        while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $devices[] = $row;
        }

        if (empty($devices)) {
            return true;
        }

        if (!$db->exec('BEGIN IMMEDIATE TRANSACTION')) {
            return false;
        }

        try {
            foreach ($devices as $device) {
                $mac = strtolower(trim((string)($device['mac'] ?? '')));
                if ($mac === '') {
                    continue;
                }

                $lifecycleId = $this->findActiveLifecycleId($db, $mac);

                if ($lifecycleId <= 0) {
                    $lifecycleId = $this->createLifecycle(
                        $db,
                        $device,
                        $device['first_seen'] ?? null
                    );
                }

                if ($lifecycleId <= 0) {
                    throw new \RuntimeException(
                        'Unable to create device lifecycle'
                    );
                }

                if (!$this->updateLifecycleSnapshot(
                    $db,
                    $lifecycleId,
                    $device
                )) {
                    throw new \RuntimeException(
                        'Unable to update device lifecycle'
                    );
                }

                $stmt = $db->prepare(
                    'UPDATE devices SET lifecycle_id = :lifecycle_id, ' .
                    'return_pending = 0 WHERE mac = :mac AND ' .
                    '(lifecycle_id IS NULL OR lifecycle_id = 0)'
                );

                if ($stmt === false) {
                    throw new \RuntimeException(
                        'Unable to prepare lifecycle assignment'
                    );
                }

                $stmt->bindValue(
                    ':lifecycle_id',
                    $lifecycleId,
                    SQLITE3_INTEGER
                );
                $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);

                if ($stmt->execute() === false) {
                    throw new \RuntimeException(
                        'Unable to assign device lifecycle'
                    );
                }

                $legacyComment = trim(
                    (string)($device['comments'] ?? '')
                );

                if ($legacyComment !== '') {
                    $stmt = $db->prepare(
                        'SELECT id FROM device_comments ' .
                        'WHERE lifecycle_id = :lifecycle_id ' .
                        'AND deleted_at IS NULL ' .
                        'AND comment = :comment LIMIT 1'
                    );

                    if ($stmt === false) {
                        throw new \RuntimeException(
                            'Unable to check legacy comment'
                        );
                    }

                    $stmt->bindValue(
                        ':lifecycle_id',
                        $lifecycleId,
                        SQLITE3_INTEGER
                    );
                    $stmt->bindValue(
                        ':comment',
                        $legacyComment,
                        SQLITE3_TEXT
                    );

                    $commentResult = $stmt->execute();
                    $existingComment = $commentResult
                        ? $commentResult->fetchArray(SQLITE3_ASSOC)
                        : false;

                    if (!$existingComment) {
                        $stmt = $db->prepare(
                            'INSERT INTO device_comments ' .
                            '(lifecycle_id, comment) ' .
                            'VALUES (:lifecycle_id, :comment)'
                        );

                        if ($stmt === false) {
                            throw new \RuntimeException(
                                'Unable to prepare legacy comment migration'
                            );
                        }

                        $stmt->bindValue(
                            ':lifecycle_id',
                            $lifecycleId,
                            SQLITE3_INTEGER
                        );
                        $stmt->bindValue(
                            ':comment',
                            $legacyComment,
                            SQLITE3_TEXT
                        );

                        if ($stmt->execute() === false) {
                            throw new \RuntimeException(
                                'Unable to migrate legacy comment'
                            );
                        }
                    }
                }
            }

            if (!$db->exec('COMMIT')) {
                throw new \RuntimeException(
                    'Unable to commit lifecycle backfill'
                );
            }

            return true;
        } catch (\Exception $e) {
            $db->exec('ROLLBACK');
            return false;
        }
    }

    private function initDatabase()
    {
        $file_mame = self::getPath('dbFile');
        $db = new \SQLite3($file_mame);

        $db->exec('CREATE TABLE IF NOT EXISTS devices (
            mac TEXT PRIMARY KEY,
            ip TEXT,
            hostname TEXT,
            hostname_source TEXT DEFAULT \'\',
            vendor TEXT,
            vlan TEXT,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            notified INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 0,
            notification_pending INTEGER DEFAULT 0
        )');

        $db->exec('CREATE INDEX IF NOT EXISTS idx_last_seen ON devices(last_seen)');

        $db->exec('CREATE TABLE IF NOT EXISTS deleted_devices (
            mac TEXT PRIMARY KEY,
            last_seen DATETIME,
            deleted_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )');

        // Migration: add columns for older databases
        @$db->exec('ALTER TABLE devices ADD COLUMN first_seen DATETIME DEFAULT CURRENT_TIMESTAMP');
        @$db->exec('ALTER TABLE devices ADD COLUMN custom_hostname TEXT DEFAULT NULL');
        @$db->exec("ALTER TABLE devices ADD COLUMN hostname_source TEXT DEFAULT ''");
        @$db->exec('ALTER TABLE devices ADD COLUMN comments TEXT DEFAULT NULL');
        @$db->exec('ALTER TABLE devices ADD COLUMN nmap_scan_pending INTEGER DEFAULT 0');
        @$db->exec('ALTER TABLE devices ADD COLUMN nmap_scan_attempts INTEGER DEFAULT 0');
        @$db->exec('ALTER TABLE devices ADD COLUMN nmap_next_attempt DATETIME DEFAULT NULL');
        @$db->exec('ALTER TABLE devices ADD COLUMN nmap_last_error TEXT DEFAULT NULL');


        $db->close();
        chmod($file_mame, 0644);
    }

    // ========================================
    // DEVICES - CRUD OPERATIONS
    // ========================================

    /**
     * Retrieve all devices from the database
     * @return array Device list adjusted according to configuration
     */
    public function getDevices()
    {
        $devices = [];
        $file_mame = self::getPath('dbFile');

        if (file_exists($file_mame)) {
            $db = $this->getDb();
            $result = $db->query('SELECT * FROM devices ORDER BY last_seen DESC');

            // Load the current infrastructure-service inventory once so the
            // Devices API can expose compact service badges without one
            // database query per device.
            $serviceMapByIp = [];
            $serviceMapByMac = [];

            $serviceTableExists = (int)$db->querySingle(
                "SELECT COUNT(*) FROM sqlite_master " .
                "WHERE type = 'table' AND name = 'device_services'"
            ) > 0;

            if ($serviceTableExists) {
                $serviceResult = $db->query(
                    "SELECT mac, ip, service_type, port, protocol, " .
                    "detection_method, confidence, product, version, " .
                    "last_verified " .
                    "FROM device_services " .
                    "WHERE status = 'available' " .
                    "ORDER BY service_type, port, protocol"
                );

                while ($service = $serviceResult->fetchArray(SQLITE3_ASSOC)) {
                    $serviceIp = trim((string)($service['ip'] ?? ''));
                    $serviceMac = strtolower(
                        trim((string)($service['mac'] ?? ''))
                    );

                    if ($serviceIp !== '') {
                        if (!isset($serviceMapByIp[$serviceIp])) {
                            $serviceMapByIp[$serviceIp] = [];
                        }
                        $serviceMapByIp[$serviceIp][] = $service;
                    }

                    if ($serviceMac !== '') {
                        if (!isset($serviceMapByMac[$serviceMac])) {
                            $serviceMapByMac[$serviceMac] = [];
                        }
                        $serviceMapByMac[$serviceMac][] = $service;
                    }
                }
            }
            while ($row = $result->fetchArray(SQLITE3_ASSOC)) {

                // Determine status from the is_active column instead of time
                $row['status'] = (isset($row['is_active']) && $row['is_active'] == 1) ? 'online' : 'offline';

                // Vendor may be NULL; normalise it
                if (empty($row['vendor'])) {
                    $row['vendor'] = 'Unknown';
                }

                // Stored device timestamps are UTC; display them in the
                // OPNsense local timezone, including daylight-saving changes.
                $row['first_seen'] = self::formatUtcForDisplay(
                    $row['first_seen'] ?? ''
                );
                $row['last_seen'] = self::formatUtcForDisplay(
                    $row['last_seen'] ?? ''
                );

                if (!empty($row['nmap_next_attempt'])) {
                    $timestamp = strtotime($row['nmap_next_attempt']);
                    if ($timestamp !== false) {
                        $row['nmap_next_attempt'] = date('d.m.Y - H:i:s', $timestamp);
                    }
                }

                $row['nmap_scan_attempts'] = (int)($row['nmap_scan_attempts'] ?? 0);
                $scanPending = (int)($row['nmap_scan_pending'] ?? 0);

                if ($scanPending === 1) {
                    $row['nmap_scan_status'] =
                        $row['nmap_scan_attempts'] > 0 ? 'retrying' : 'pending';
                } elseif (
                    $row['nmap_scan_attempts'] >= 5 &&
                    !empty($row['nmap_last_error'])
                ) {
                    $row['nmap_scan_status'] = 'failed';
                } else {
                    $row['nmap_scan_status'] = '';
                }
                $deviceIp = trim((string)($row['ip'] ?? ''));
                $deviceMac = strtolower(
                    trim((string)($row['mac'] ?? ''))
                );

                // Service roles belong to an endpoint IP. Prefer the IP
                // mapping and use MAC only as a fallback.
                if (
                    $deviceIp !== '' &&
                    isset($serviceMapByIp[$deviceIp])
                ) {
                    $row['services'] = $serviceMapByIp[$deviceIp];
                } elseif (
                    $deviceMac !== '' &&
                    isset($serviceMapByMac[$deviceMac])
                ) {
                    $row['services'] = $serviceMapByMac[$deviceMac];
                } else {
                    $row['services'] = [];
                }

                $devices[] = $row;
            }

            $db->close();
        }

        return $devices;
    }

    public function startNewLifecycle($mac)
    {
        $db = $this->getDb();
        $mac = strtolower(trim((string)$mac));

        if ($mac === '') {
            $db->close();
            return false;
        }

        if (!$db->exec('BEGIN IMMEDIATE TRANSACTION')) {
            $db->close();
            return false;
        }

        try {
            $stmt = $db->prepare(
                'SELECT * FROM devices WHERE mac = :mac'
            );
            $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
            $result = $stmt->execute();
            $device = $result
                ? $result->fetchArray(SQLITE3_ASSOC)
                : false;

            if (
                !$device ||
                (int)($device['return_pending'] ?? 0) !== 1
            ) {
                throw new \RuntimeException(
                    'Device is not awaiting lifecycle resolution'
                );
            }

            if ($this->findActiveLifecycleId($db, $mac) > 0) {
                throw new \RuntimeException(
                    'Device already has an active lifecycle'
                );
            }

            $lifecycleId = $this->createLifecycle(
                $db,
                $device,
                $device['first_seen'] ?? null
            );

            if ($lifecycleId <= 0) {
                throw new \RuntimeException(
                    'Unable to create device lifecycle'
                );
            }

            $stmt = $db->prepare(
                'UPDATE devices ' .
                'SET lifecycle_id = :lifecycle_id, return_pending = 0 ' .
                'WHERE mac = :mac AND return_pending = 1'
            );
            $stmt->bindValue(
                ':lifecycle_id',
                $lifecycleId,
                SQLITE3_INTEGER
            );
            $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);

            if ($stmt->execute() === false || $db->changes() !== 1) {
                throw new \RuntimeException(
                    'Unable to attach new device lifecycle'
                );
            }

            $stmt = $db->prepare(
                'DELETE FROM deleted_devices WHERE mac = :mac'
            );
            $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);

            if ($stmt->execute() === false) {
                throw new \RuntimeException(
                    'Unable to resolve deleted-device tombstone'
                );
            }

            if (!$db->exec('COMMIT')) {
                throw new \RuntimeException(
                    'Unable to commit new lifecycle'
                );
            }

            $db->close();
            return $lifecycleId;
        } catch (\Exception $e) {
            $db->exec('ROLLBACK');
            $db->close();
            return false;
        }
    }


    public function relinkLifecycle($mac, $lifecycleId)
    {
        $db = $this->getDb();
        $mac = strtolower(trim((string)$mac));
        $lifecycleId = (int)$lifecycleId;

        if ($mac === '' || $lifecycleId <= 0) {
            $db->close();
            return false;
        }

        if (!$db->exec('BEGIN IMMEDIATE TRANSACTION')) {
            $db->close();
            return false;
        }

        try {
            $stmt = $db->prepare(
                'SELECT * FROM devices WHERE mac = :mac'
            );
            $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
            $result = $stmt->execute();
            $device = $result
                ? $result->fetchArray(SQLITE3_ASSOC)
                : false;

            if (
                !$device ||
                (int)($device['return_pending'] ?? 0) !== 1
            ) {
                throw new \RuntimeException(
                    'Device is not awaiting lifecycle resolution'
                );
            }

            if ($this->findActiveLifecycleId($db, $mac) > 0) {
                throw new \RuntimeException(
                    'Device already has an active lifecycle'
                );
            }

            $stmt = $db->prepare(
                "SELECT id, custom_hostname, archived_at " .
                "FROM device_lifecycles " .
                "WHERE id = :id AND mac = :mac AND status = 'archived'"
            );
            $stmt->bindValue(':id', $lifecycleId, SQLITE3_INTEGER);
            $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
            $result = $stmt->execute();
            $lifecycle = $result
                ? $result->fetchArray(SQLITE3_ASSOC)
                : false;

            if (!$lifecycle) {
                throw new \RuntimeException(
                    'Archived lifecycle not found for device'
                );
            }

            if (
                trim((string)($device['custom_hostname'] ?? '')) === '' &&
                trim((string)($lifecycle['custom_hostname'] ?? '')) !== ''
            ) {
                $device['custom_hostname'] = $lifecycle['custom_hostname'];
            }

            $archivedAt = trim(
                (string)($lifecycle['archived_at'] ?? '')
            );

            if (
                $archivedAt !== '' &&
                !$this->recordTimelineActivityEvent(
                    $db,
                    $mac,
                    $lifecycleId,
                    'LIFECYCLE_ARCHIVED',
                    'active',
                    'archived',
                    'Preserved before lifecycle relink',
                    $archivedAt
                )
            ) {
                throw new \RuntimeException(
                    'Unable to preserve lifecycle archive history'
                );
            }

            $stmt = $db->prepare(
                "UPDATE device_lifecycles " .
                "SET status = 'active', archived_at = NULL " .
                "WHERE id = :id AND mac = :mac AND status = 'archived'"
            );
            $stmt->bindValue(':id', $lifecycleId, SQLITE3_INTEGER);
            $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);

            if ($stmt->execute() === false || $db->changes() !== 1) {
                throw new \RuntimeException(
                    'Unable to reactivate device lifecycle'
                );
            }

            if (!$this->updateLifecycleSnapshot(
                $db,
                $lifecycleId,
                $device
            )) {
                throw new \RuntimeException(
                    'Unable to update reactivated lifecycle'
                );
            }

            $stmt = $db->prepare(
                'UPDATE devices ' .
                'SET lifecycle_id = :lifecycle_id, return_pending = 0, ' .
                'custom_hostname = :custom_hostname ' .
                'WHERE mac = :mac AND return_pending = 1'
            );
            $stmt->bindValue(
                ':lifecycle_id',
                $lifecycleId,
                SQLITE3_INTEGER
            );
            $stmt->bindValue(
                ':custom_hostname',
                $device['custom_hostname'] ?? null,
                ($device['custom_hostname'] ?? null) === null
                    ? SQLITE3_NULL
                    : SQLITE3_TEXT
            );
            $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);

            if ($stmt->execute() === false || $db->changes() !== 1) {
                throw new \RuntimeException(
                    'Unable to attach reactivated lifecycle'
                );
            }

            if (!$this->recordTimelineActivityEvent(
                $db,
                $mac,
                $lifecycleId,
                'LIFECYCLE_RELINKED',
                'archived',
                'active',
                'Returning device relinked to archived lifecycle'
            )) {
                throw new \RuntimeException(
                    'Unable to record lifecycle relink history'
                );
            }

            $stmt = $db->prepare(
                'DELETE FROM deleted_devices WHERE mac = :mac'
            );
            $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);

            if ($stmt->execute() === false) {
                throw new \RuntimeException(
                    'Unable to resolve deleted-device tombstone'
                );
            }

            if (!$db->exec('COMMIT')) {
                throw new \RuntimeException(
                    'Unable to commit lifecycle relink'
                );
            }

            $db->close();
            return true;
        } catch (\Exception $e) {
            $db->exec('ROLLBACK');
            $db->close();
            return false;
        }
    }


    public function deleteDevice($mac)
    {
        $db = $this->getDb();
        $mac = strtolower(trim($mac));

        $db->exec('BEGIN IMMEDIATE TRANSACTION');
        try {
            $stmt = $db->prepare(
                'SELECT * FROM devices WHERE mac = :mac'
            );
            $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
            $result = $stmt->execute();
            $row = $result ? $result->fetchArray(SQLITE3_ASSOC) : false;

            if (!$row) {
                $db->exec('ROLLBACK');
                $db->close();
                return false;
            }

            $lifecycleId = (int)($row['lifecycle_id'] ?? 0);

            if ($lifecycleId <= 0) {
                throw new \RuntimeException(
                    'Device has no active lifecycle'
                );
            }

            if (!$this->updateLifecycleSnapshot(
                $db,
                $lifecycleId,
                $row
            )) {
                throw new \RuntimeException(
                    'Unable to update device lifecycle'
                );
            }

            if (!$this->archiveLifecycle($db, $lifecycleId)) {
                throw new \RuntimeException(
                    'Unable to archive device lifecycle'
                );
            }

            $stmt = $db->prepare(
                'INSERT OR REPLACE INTO deleted_devices ' .
                '(mac, last_seen, deleted_at) ' .
                'VALUES (:mac, :last_seen, CURRENT_TIMESTAMP)'
            );
            $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
            $stmt->bindValue(
                ':last_seen',
                $row['last_seen'] ?? '',
                SQLITE3_TEXT
            );

            if ($stmt->execute() === false) {
                throw new \RuntimeException(
                    'Unable to create deleted-device tombstone'
                );
            }

            $stmt = $db->prepare(
                'DELETE FROM devices WHERE mac = :mac'
            );
            $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);

            if ($stmt->execute() === false) {
                throw new \RuntimeException(
                    'Unable to delete device'
                );
            }

            $changes = $db->changes();

            if (!$db->exec('COMMIT')) {
                throw new \RuntimeException(
                    'Unable to commit device deletion'
                );
            }

            $db->close();
            return $changes > 0;
        } catch (\Exception $e) {
            $db->exec('ROLLBACK');
            $db->close();
            return false;
        }
    }

    public function clearAll()
    {
        $db = $this->getDb();

        if (!$db->exec('BEGIN IMMEDIATE TRANSACTION')) {
            $db->close();
            return false;
        }

        try {
            $result = $db->query('SELECT * FROM devices');

            if ($result === false) {
                throw new \RuntimeException(
                    'Unable to read devices for lifecycle archive'
                );
            }

            $devices = [];
            while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
                $devices[] = $row;
            }

            foreach ($devices as $device) {
                $lifecycleId = (int)($device['lifecycle_id'] ?? 0);

                if ($lifecycleId <= 0) {
                    throw new \RuntimeException(
                        'Device has no active lifecycle'
                    );
                }

                if (!$this->updateLifecycleSnapshot(
                    $db,
                    $lifecycleId,
                    $device
                )) {
                    throw new \RuntimeException(
                        'Unable to update device lifecycle'
                    );
                }

                if (!$this->archiveLifecycle(
                    $db,
                    $lifecycleId
                )) {
                    throw new \RuntimeException(
                        'Unable to archive device lifecycle'
                    );
                }
            }

            if (!$db->exec(
                'INSERT OR REPLACE INTO deleted_devices ' .
                '(mac, last_seen, deleted_at) ' .
                'SELECT mac, last_seen, CURRENT_TIMESTAMP FROM devices'
            )) {
                throw new \RuntimeException(
                    'Unable to create deleted-device tombstones'
                );
            }

            if (!$db->exec('DELETE FROM devices')) {
                throw new \RuntimeException(
                    'Unable to clear devices'
                );
            }

            if (!$db->exec('COMMIT')) {
                throw new \RuntimeException(
                    'Unable to commit clear-all operation'
                );
            }

            $db->close();
            return true;
        } catch (\Exception $e) {
            $db->exec('ROLLBACK');
            $db->close();
            return false;
        }
    }

}
