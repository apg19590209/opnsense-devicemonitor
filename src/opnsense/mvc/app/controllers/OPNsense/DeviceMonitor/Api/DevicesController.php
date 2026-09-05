<?php

namespace OPNsense\DeviceMonitor\Api;

use OPNsense\Base\ApiControllerBase;
use OPNsense\DeviceMonitor\DeviceMonitor;

/**
 * DevicesController
 * 
 * API controller for device management
 */
class DevicesController extends ApiControllerBase
{
    private function getPaths()
    {
        $defaultsFile = '/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json';
        
        if (file_exists($defaultsFile)) {
            $defaults = json_decode(file_get_contents($defaultsFile), true);
            return $defaults['paths'];  // ← Paths from defaults.json
        }
        
        // Fallback if defaults.json does not exist
        return [-1];
    }

    /**
     * Aktualizace custom hostname
     * POST /api/devicemonitor/devices/updatehostname
     */
    public function updatehostnameAction()
    {
        if ($this->request->isPost()) {
            $mac = $this->request->getPost('mac');
            $hostname = $this->request->getPost('hostname');
            
            if (empty($mac)) {
                return ['result' => 'failed', 'error' => 'MAC required'];
            }
            
            $model = new DeviceMonitor();
            if ($model->updateHostname($mac, $hostname)) {
                return ['result' => 'saved'];
            }
        }
        return ['result' => 'failed'];
    }

    /**
     * Device search for the Bootgrid table
     * GET/POST /api/devicemonitor/devices/search
     */
    public function searchAction()
    {
        
        try {
            $model = new DeviceMonitor();
            $devices = $model->getDevices();
            
            // Process Bootgrid parameters safely
            $current = 1;
            $rowCount = -1;
            $searchPhrase = '';
            $sort = [];
            
            if ($this->request->has('current')) {
                $current = intval($this->request->get('current'));
            }
            if ($this->request->has('rowCount')) {
                $rowCount = intval($this->request->get('rowCount'));
            }
            if ($this->request->has('searchPhrase')) {
                $searchPhrase = (string)$this->request->get('searchPhrase');
            }
            if ($this->request->has('sort')) {
                $sortData = $this->request->get('sort');
                if (is_array($sortData)) {
                    $sort = $sortData;
                }
            }
            
            // === 1. FILTERING ===
            if (!empty($searchPhrase) && strlen(trim($searchPhrase)) > 0) {
                $searchPhrase = strtolower(trim($searchPhrase));
                $filtered = [];
                
                foreach ($devices as $device) {
                    $match = false;
                    
                    // Check all fields
                    if (isset($device['mac']) && strpos(strtolower($device['mac']), $searchPhrase) !== false) {
                        $match = true;
                    }
                    if (isset($device['ip']) && strpos(strtolower($device['ip']), $searchPhrase) !== false) {
                        $match = true;
                    }
                    if (isset($device['hostname']) && strpos(strtolower($device['hostname']), $searchPhrase) !== false) {
                        $match = true;
                    }
                    if (isset($device['vendor']) && strpos(strtolower($device['vendor']), $searchPhrase) !== false) {
                        $match = true;
                    }
                    if (isset($device['vlan']) && strpos(strtolower($device['vlan']), $searchPhrase) !== false) {
                        $match = true;
                    }
                    if (isset($device['status']) && strpos(strtolower($device['status']), $searchPhrase) !== false) {
                        $match = true;
                    }
                    
                    if (isset($device['nmap_scan_status']) && strpos(strtolower($device['nmap_scan_status']), $searchPhrase) !== false) {
                        $match = true;
                    }

                    if ($match) {
                        $filtered[] = $device;
                    }
                }
                
                $devices = $filtered;
            }
            
            $total = count($devices);
            
            // === 2. SORTING ===
            if (!empty($sort) && is_array($sort)) {
                $sortColumn = key($sort);
                $sortOrder = $sort[$sortColumn];
                
                if ($sortColumn && in_array($sortColumn, ['mac', 'ip', 'hostname', 'vendor', 'vlan', 'first_seen', 'last_seen', 'status', 'nmap_scan_status'])) {
                    usort($devices, function($a, $b) use ($sortColumn, $sortOrder) {
                        $valA = isset($a[$sortColumn]) ? $a[$sortColumn] : '';
                        $valB = isset($b[$sortColumn]) ? $b[$sortColumn] : '';
                        
                        // Comparison
                        if ($valA == $valB) {
                            return 0;
                        }
                        
                        $result = ($valA < $valB) ? -1 : 1;
                        
                        // Apply sort direction
                        return ($sortOrder === 'desc') ? -$result : $result;
                    });
                }
            }
            
            // === 3. PAGINATION ===
            if ($rowCount > 0) {
                $offset = ($current - 1) * $rowCount;
                $devices = array_slice($devices, $offset, $rowCount);
            }
            
            // Re-index array because Bootgrid requires an indexed array
            $devices = array_values($devices);
            
            return [
                'rows' => $devices,
                'rowCount' => count($devices),
                'total' => $total,
                'current' => $current
            ];
            
        } catch (\Exception $e) {
            // Return empty data on error
            return [
                'rows' => [],
                'rowCount' => 0,
                'total' => 0,
                'current' => 1,
                'error' => $e->getMessage()
            ];
        }
    }

    /**
     * Device statistics
     * GET /api/devicemonitor/devices/stats
     */
    public function statsAction()
    {
        
        $paths = $this->getPaths();
        $result = ['total' => 0, 'online' => 0];
        
        try {
            if (file_exists($paths['dbFile'])) {
                $db = new \SQLite3($paths['dbFile']);
                
                $result['total'] = (int)$db->querySingle(
                    "SELECT COUNT(*) FROM devices"
                );
                
                $result['online'] = (int)$db->querySingle(
                    "SELECT COUNT(*) FROM devices WHERE is_active = 1"
                );
                
                $db->close();
            }
        } catch (\Exception $e) {
            syslog(LOG_ERR, "DeviceMonitor stats error: " . $e->getMessage());
        }
        
        return $result;
    }

    /**
    * Quick online/offline status update from Hostwatch DB
     * POST /api/devicemonitor/devices/updatestatus
     */
    public function updatestatusAction()
    {
        
        $paths = $this->getPaths();
        
        // Zavolej scan_network.py s --update-only
        exec("{$paths['scanScript']} --update-only 2>&1", $output, $return_code);
        
        if ($return_code === 0) {
            // Reload statistics from the database
            return $this->statsAction();  // ← Correct
        }
        
        // Return an error if the scan failed
        return ['result' => 'error', 'online' => 0, 'total' => 0];
    }

    /**
     * Delete one device
     * POST /api/devicemonitor/devices/delete
     */
    public function deleteAction()
    {
        if ($this->request->isPost()) {
            $mac = $this->request->getPost('mac');
            $model = new DeviceMonitor();

            if ($model->deleteDevice($mac)) {
                return ['result' => 'deleted'];
            }
        }

        return ['result' => 'failed'];
    }

    /**
     * Ping a device and update its status
     * POST /api/devicemonitor/devices/pingdevice
     */
    public function pingdeviceAction()
    {
        if ($this->request->isPost()) {
            $ip  = $this->request->getPost('ip',  'string', '');
            $mac = $this->request->getPost('mac',  'string', '');

            if (empty($ip) || empty($mac)) {
                return ['result' => 'failed', 'error' => 'IP and MAC required'];
            }

            // Validace IP adresy
            if (!filter_var($ip, FILTER_VALIDATE_IP)) {
                return ['result' => 'failed', 'error' => 'Invalid IP'];
            }

            // Ping - 2 pakety, timeout 1s
            exec('ping -c 2 -W 1 ' . escapeshellarg($ip) . ' > /dev/null 2>&1', $out, $ret);
            $online = ($ret === 0) ? 1 : 0;

            // Aktualizuj DB
            $paths = $this->getPaths();
            try {
                $db = new \SQLite3($paths['dbFile']);
                $stmt = $db->prepare(
                    'UPDATE devices SET is_active = :active WHERE mac = :mac'
                );
                $stmt->bindValue(':active', $online, SQLITE3_INTEGER);
                $stmt->bindValue(':mac',    $mac,    SQLITE3_TEXT);
                $stmt->execute();
                $db->close();
            } catch (\Exception $e) {
                return ['result' => 'failed', 'error' => $e->getMessage()];
            }

            return [
                'result' => $online ? 'online' : 'offline',
                'ip'     => $ip,
                'mac'    => $mac
            ];
        }
        return ['result' => 'failed'];
    }

    /**
     * Return recent targeted Nmap scan history
     * GET /api/devicemonitor/devices/scanhistory
     */
    public function scanhistoryAction()
    {
        $result = [
            'rows' => [],
            'total' => 0,
            'unresolved' => 0,
            'resolved' => 0
        ];

        try {
            $paths = $this->getPaths();

            if (
                !isset($paths['dbFile']) ||
                !is_file($paths['dbFile'])
            ) {
                return $result;
            }

            $dbPath = $paths['dbFile'];

            $limit = (int)$this->request->get('limit', 'int', 10);
            $limit = max(1, min(500, $limit));

            $db = new \SQLite3(
                $dbPath,
                SQLITE3_OPEN_READONLY
            );
            $db->busyTimeout(2000);

            $historyExists = (int)$db->querySingle(
                "SELECT COUNT(*) " .
                "FROM sqlite_master " .
                "WHERE type = 'table' " .
                "AND name = 'nmap_scan_history'"
            );

            if ($historyExists !== 1) {
                $db->close();
                return $result;
            }

            $result['total'] = (int)$db->querySingle(
                'SELECT COUNT(*) FROM nmap_scan_history'
            );

            /*
             * Detect v2.6 columns dynamically so an older database
             * remains readable until its scanner-side migration runs.
             */
            $historyColumns = [];

            $columnResult = $db->query(
                'PRAGMA table_info(nmap_scan_history)'
            );

            while ($column = $columnResult->fetchArray(SQLITE3_ASSOC)) {
                $historyColumns[$column['name']] = true;
            }

            $optionalColumns = [
                'top_ports',
                'timing',
                'host_timeout',
                'version_detection',
                'nmap_version',
                'nmap_elapsed',
                'os_hint',
                'open_port_count',
                'email_sent',
                'email_error'
            ];

            $selectColumns = [
                'id',
                'mac',
                'ip',
                'scan_type',
                'started_at',
                'finished_at',
                'success',
                'error'
            ];

            foreach ($optionalColumns as $column) {
                if (isset($historyColumns[$column])) {
                    $selectColumns[] = $column;
                } else {
                    $selectColumns[] = 'NULL AS ' . $column;
                }
            }

            $historySql =
                'SELECT ' .
                implode(', ', $selectColumns) .
                ' FROM nmap_scan_history ' .
                'ORDER BY id DESC ' .
                'LIMIT :limit';

            $stmt = $db->prepare($historySql);
            $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);

            $query = $stmt->execute();

            $rowsById = [];
            $historyIds = [];

            while ($row = $query->fetchArray(SQLITE3_ASSOC)) {
                $row['id'] = (int)$row['id'];

                if ($row['success'] !== null) {
                    $row['success'] = (int)$row['success'];
                }

                foreach ([
                    'top_ports',
                    'timing',
                    'host_timeout',
                    'version_detection',
                    'open_port_count',
                    'email_sent'
                ] as $integerField) {
                    if ($row[$integerField] !== null) {
                        $row[$integerField] =
                            (int)$row[$integerField];
                    }
                }

                if ($row['nmap_elapsed'] !== null) {
                    $row['nmap_elapsed'] =
                        (float)$row['nmap_elapsed'];
                }

                $row['ports'] = [];

                $rowsById[$row['id']] = $row;
                $historyIds[] = $row['id'];
            }

            /*
             * Fetch all ports for the returned history rows in one query.
             * IDs originate from SQLite and are explicitly cast to int.
             */
            if (count($historyIds) > 0) {
                $portsExists = (int)$db->querySingle(
                    "SELECT COUNT(*) " .
                    "FROM sqlite_master " .
                    "WHERE type = 'table' " .
                    "AND name = 'nmap_scan_ports'"
                );

                if ($portsExists === 1) {
                    $safeIds = array_map(
                        'intval',
                        $historyIds
                    );

                    $portsSql =
                        'SELECT ' .
                        'scan_history_id, ' .
                        'port, ' .
                        'protocol, ' .
                        'state, ' .
                        'service, ' .
                        'product, ' .
                        'version, ' .
                        'extra_info ' .
                        'FROM nmap_scan_ports ' .
                        'WHERE scan_history_id IN (' .
                        implode(',', $safeIds) .
                        ') ' .
                        'ORDER BY scan_history_id DESC, ' .
                        'port ASC, protocol ASC';

                    $portQuery = $db->query($portsSql);

                    while (
                        $port =
                        $portQuery->fetchArray(SQLITE3_ASSOC)
                    ) {
                        $historyId =
                            (int)$port['scan_history_id'];

                        if (!isset($rowsById[$historyId])) {
                            continue;
                        }

                        $port['scan_history_id'] = $historyId;
                        $port['port'] = (int)$port['port'];

                        $rowsById[$historyId]['ports'][] = $port;
                    }
                }
            }

            foreach ($historyIds as $historyId) {
                $result['rows'][] = $rowsById[$historyId];
            }

            $db->close();

        } catch (\Throwable $e) {
            error_log(
                'DeviceMonitor scan history error: ' .
                $e->getMessage()
            );

            return [
                'rows' => [],
                'total' => 0,
                'error' => 'Unable to load scan history'
            ];
        }

        return $result;
    }

    /**
     * Run a manual targeted Nmap scan for one existing device
     * POST /api/devicemonitor/devices/nmapscan
     */
    public function nmapscanAction()
    {
        if (!$this->request->isPost()) {
            return ['result' => 'failed', 'error' => 'POST required'];
        }

        $mac = strtolower(trim(
            (string)$this->request->getPost('mac', 'string', '')
        ));

        if (!preg_match('/^(?:[0-9a-f]{2}:){5}[0-9a-f]{2}$/', $mac)) {
            return ['result' => 'failed', 'error' => 'Invalid MAC address'];
        }

        $paths = $this->getPaths();

        if (
            !isset($paths['scanScript']) ||
            !is_file($paths['scanScript'])
        ) {
            return ['result' => 'failed', 'error' => 'Scanner unavailable'];
        }

        $command =
            escapeshellarg($paths['scanScript']) .
            ' --scan-mac ' .
            escapeshellarg($mac) .
            ' 2>&1';

        $output = [];
        $returnCode = 1;
        exec($command, $output, $returnCode);

        $message = trim(implode("\n", $output));

        if ($returnCode === 0) {
            return [
                'result' => 'scanned',
                'message' => $message !== ''
                    ? $message
                    : 'Targeted Nmap scan completed'
            ];
        }

        return [
            'result' => 'failed',
            'error' => $message !== ''
                ? $message
                : 'Targeted Nmap scan failed',
            'code' => $returnCode
        ];
    }


    /**
     * Clear the entire database
     * POST /api/devicemonitor/devices/clear
     */
    public function clearAction()
    {
        if ($this->request->isPost()) {
            $model = new DeviceMonitor();
            $model->clearAll();
            return ['result' => 'cleared'];
        }

        return ['result' => 'failed'];
    }
    /**
     * Resolve or reopen an identity event.
     * POST /api/devicemonitor/devices/identityeventstatus
     */
    public function identityeventstatusAction()
    {
        if (!$this->request->isPost()) {
            return ['result' => 'failed', 'error' => 'POST required'];
        }

        $id = (int)$this->request->getPost('id', 'int', 0);
        $resolved = (int)$this->request->getPost(
            'resolved',
            'int',
            -1
        );

        if ($id < 1 || !in_array($resolved, [0, 1], true)) {
            return ['result' => 'failed', 'error' => 'Invalid request'];
        }

        try {
            $paths = $this->getPaths();

            if (!isset($paths['dbFile']) || !is_file($paths['dbFile'])) {
                return ['result' => 'failed', 'error' => 'Database not found'];
            }

            $db = new \SQLite3(
                $paths['dbFile'],
                SQLITE3_OPEN_READWRITE
            );
            $db->busyTimeout(2000);

            $tableExists = (int)$db->querySingle(
                "SELECT COUNT(*) " .
                "FROM sqlite_master " .
                "WHERE type = 'table' " .
                "AND name = 'device_identity_events'"
            );

            if ($tableExists !== 1) {
                $db->close();
                return ['result' => 'failed', 'error' => 'Table not found'];
            }

            $check = $db->prepare(
                'SELECT id FROM device_identity_events WHERE id = :id'
            );
            $check->bindValue(':id', $id, SQLITE3_INTEGER);
            $row = $check->execute()->fetchArray(SQLITE3_ASSOC);

            if (!$row) {
                $db->close();
                return ['result' => 'failed', 'error' => 'Event not found'];
            }

            $sql = $resolved === 1
                ? 'UPDATE device_identity_events ' .
                  'SET resolved_at = CURRENT_TIMESTAMP WHERE id = :id'
                : 'UPDATE device_identity_events ' .
                  'SET resolved_at = NULL WHERE id = :id';

            $stmt = $db->prepare($sql);
            $stmt->bindValue(':id', $id, SQLITE3_INTEGER);
            $stmt->execute();
            $db->close();

            return [
                'result' => 'saved',
                'id' => $id,
                'resolved' => $resolved === 1
            ];
        } catch (\Throwable $e) {
            return ['result' => 'failed', 'error' => $e->getMessage()];
        }
    }
    /**
     * Return recent device identity events
     * GET /api/devicemonitor/devices/identityevents
     */
    public function identityeventsAction()
    {
        $result = [
            'rows' => [],
            'total' => 0,
            'unresolved' => 0,
            'resolved' => 0
        ];

        try {
            $paths = $this->getPaths();

            if (!isset($paths['dbFile']) || !is_file($paths['dbFile'])) {
                return $result;
            }

            $limit = (int)$this->request->get('limit', 'int', 100);
            $limit = max(1, min(500, $limit));

            $status = strtolower(trim(
                (string)$this->request->get('status', 'string', 'all')
            ));

            if (!in_array($status, ['all', 'unresolved', 'resolved'], true)) {
                $status = 'all';
            }

            $whereClause = '';
            if ($status === 'unresolved') {
                $whereClause = ' WHERE resolved_at IS NULL';
            } elseif ($status === 'resolved') {
                $whereClause = ' WHERE resolved_at IS NOT NULL';
            }

            $db = new \SQLite3(
                $paths['dbFile'],
                SQLITE3_OPEN_READONLY
            );
            $db->busyTimeout(2000);

            $tableExists = (int)$db->querySingle(
                "SELECT COUNT(*) " .
                "FROM sqlite_master " .
                "WHERE type = 'table' " .
                "AND name = 'device_identity_events'"
            );

            if ($tableExists !== 1) {
                $db->close();
                return $result;
            }

            $result['unresolved'] = (int)$db->querySingle(
                'SELECT COUNT(*) FROM device_identity_events ' .
                'WHERE resolved_at IS NULL'
            );

            $result['resolved'] = (int)$db->querySingle(
                'SELECT COUNT(*) FROM device_identity_events ' .
                'WHERE resolved_at IS NOT NULL'
            );

            $result['total'] = (int)$db->querySingle(
                'SELECT COUNT(*) FROM device_identity_events' .
                $whereClause
            );

            $stmt = $db->prepare(
                'SELECT id, mac, event_type, severity, detected_at, ' .
                'ip, other_ip, other_mac, interface, other_interface, ' .
                'details, resolved_at ' .
                'FROM device_identity_events' .
                $whereClause .
                ' ORDER BY id DESC LIMIT :limit'
            );
            $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);

            $query = $stmt->execute();

            while ($row = $query->fetchArray(SQLITE3_ASSOC)) {
                $row['id'] = (int)$row['id'];
                $result['rows'][] = $row;
            }

            $db->close();
        } catch (\Throwable $e) {
            return $result;
        }

        return $result;
    }
}
