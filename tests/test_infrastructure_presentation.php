<?php

namespace OPNsense\Base {
    class ApiControllerBase
    {
        public $request;
    }
}

namespace OPNsense\DeviceMonitor {
    class DeviceMonitor
    {
    }
}

namespace OPNsense\DeviceMonitor\Api {
    function file_exists($path)
    {
        if (
            $path ===
            '/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'
        ) {
            return true;
        }

        return \file_exists($path);
    }

    function file_get_contents($path)
    {
        if (
            $path ===
            '/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'
        ) {
            return json_encode([
                'paths' => [
                    'dbFile' => $GLOBALS['dm_presentation_db'],
                ],
            ]);
        }

        return \file_get_contents($path);
    }
}

namespace {
    function check_presentation($condition, $message)
    {
        if (!$condition) {
            throw new \RuntimeException($message);
        }
    }

    function run_email_renderer($payload)
    {
        $script = __DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor/'
            . 'notify_service_email.php';
        $descriptors = [
            0 => ['pipe', 'r'],
            1 => ['pipe', 'w'],
            2 => ['pipe', 'w'],
        ];
        $environment = array_merge($_ENV, ['DM_RENDER_ONLY' => '1']);
        $process = proc_open(
            [PHP_BINARY, $script],
            $descriptors,
            $pipes,
            null,
            $environment
        );

        check_presentation(is_resource($process), 'email renderer did not start');

        fwrite($pipes[0], json_encode($payload));
        fclose($pipes[0]);
        $stdout = stream_get_contents($pipes[1]);
        fclose($pipes[1]);
        $stderr = stream_get_contents($pipes[2]);
        fclose($pipes[2]);
        $status = proc_close($process);

        check_presentation(
            $status === 0,
            'email renderer failed: ' . trim($stderr)
        );

        $result = json_decode($stdout, true);
        check_presentation(
            is_array($result) && ($result['result'] ?? '') === 'rendered',
            'email renderer returned invalid output'
        );

        return $result;
    }

    $tmp = sys_get_temp_dir() . '/dm-service-presentation-' . getmypid();
    @mkdir($tmp, 0700, true);
    $dbPath = $tmp . '/devices.db';
    $GLOBALS['dm_presentation_db'] = $dbPath;

    $db = new \SQLite3($dbPath);
    $db->exec(
        'CREATE TABLE devices (
            mac TEXT PRIMARY KEY,
            ip TEXT,
            hostname TEXT,
            custom_hostname TEXT,
            vendor TEXT,
            vlan TEXT,
            last_seen DATETIME
        )'
    );
    $db->exec(
        'CREATE TABLE device_services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mac TEXT,
            ip TEXT NOT NULL,
            interface TEXT NOT NULL DEFAULT "",
            service_type TEXT NOT NULL,
            port INTEGER NOT NULL,
            protocol TEXT NOT NULL,
            status TEXT NOT NULL,
            detection_method TEXT NOT NULL,
            confidence TEXT NOT NULL,
            product TEXT,
            version TEXT,
            first_detected DATETIME,
            last_verified DATETIME,
            last_checked DATETIME
        )'
    );
    $db->exec(
        'CREATE TABLE device_activity_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mac TEXT,
            lifecycle_id INTEGER,
            event_type TEXT,
            occurred_at DATETIME,
            old_value TEXT,
            new_value TEXT,
            details TEXT
        )'
    );

    $devices = [
        ['aa:bb:cc:dd:ee:20', '192.168.50.21', 'stored-mac-host', '', 'Vendor A', 'LAN', '2026-11-20 01:00:00'],
        ['aa:bb:cc:dd:ee:21', '192.168.50.20', 'first-match', '', 'Vendor B', 'LAN', '2026-11-20 00:50:00'],
        ['aa:bb:cc:dd:ee:22', '192.168.50.20', 'second-match', '', '<script>alert(1)</script>', 'VLAN50', '2026-11-20 00:40:00'],
    ];
    $insertDevice = $db->prepare(
        'INSERT INTO devices
         (mac, ip, hostname, custom_hostname, vendor, vlan, last_seen)
         VALUES (?, ?, ?, ?, ?, ?, ?)'
    );
    foreach ($devices as $device) {
        foreach ($device as $index => $value) {
            $insertDevice->bindValue($index + 1, $value, SQLITE3_TEXT);
        }
        $insertDevice->execute();
        $insertDevice->reset();
    }

    $insertService = $db->prepare(
        'INSERT INTO device_services
         (mac, ip, interface, service_type, port, protocol, status,
          detection_method, confidence, product, version, first_detected,
          last_verified, last_checked)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    );
    $services = [
        ['aa:bb:cc:dd:ee:20', '192.168.50.20', 'LAN', 'DNS', 53, 'udp', 'unavailable', 'dns_query', 'verified', 'Test DNS', '1.0', '2026-11-19 22:00:00', '2026-11-19 23:10:02', '2026-11-20 00:10:02'],
        ['aa:bb:cc:dd:ee:20', '192.168.50.20', 'LAN', 'DNS', 53, 'udp', 'available', 'dns_query_alt', 'verified', 'Test DNS', '1.0', '2026-11-19 22:00:00', '2026-11-19 23:20:02', '2026-11-20 00:20:02'],
        ['aa:bb:cc:dd:ee:23', '192.168.50.23', 'opt1', 'VPN', 51820, 'udp', 'available', 'authoritative_runtime', 'verified', 'WireGuard', 'wg0', '2026-11-19 22:00:00', '2026-11-19 23:30:00', '2026-11-20 00:30:00'],
        ['aa:bb:cc:dd:ee:24', '192.168.50.24', '', 'SSH', 22, 'tcp', '', '', '', '', '', '', '', ''],
    ];
    foreach ($services as $service) {
        foreach ($service as $index => $value) {
            $type = is_int($value) ? SQLITE3_INTEGER : SQLITE3_TEXT;
            $insertService->bindValue($index + 1, $value, $type);
        }
        $insertService->execute();
        $insertService->reset();
    }

    $db->exec(
        "INSERT INTO device_activity_events
         (mac, lifecycle_id, event_type, occurred_at, old_value, new_value, details)
         VALUES (
            'aa:bb:cc:dd:ee:20', 1, 'SERVICE_UNAVAILABLE',
            '2026-11-20 00:10:02', 'available', 'unavailable',
            'DNS|192.168.50.20|53|udp|LAN|dns_query'
         )"
    );
    $db->close();

    require_once(
        __DIR__ .
        '/../src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/' .
        'DevicesController.php'
    );

    $controller =
        new \OPNsense\DeviceMonitor\Api\DevicesController();
    $response = $controller->servicesAction();
    $rows = [];
    foreach ($response['rows'] ?? [] as $row) {
        $rows[(int)$row['id']] = $row;
    }

    check_presentation(count($rows) === 4, 'service row count changed');
    check_presentation(
        $rows[1]['last_checked'] === '2026-11-20 00:10:02',
        'last_checked was not exposed'
    );
    check_presentation(
        $rows[1]['evidence_kind'] === 'probe',
        'probe evidence classification is wrong'
    );
    check_presentation(
        $rows[3]['evidence_kind'] === 'authoritative',
        'authoritative detection did not take precedence'
    );
    check_presentation(
        $rows[4]['evidence_kind'] === 'unknown',
        'unknown evidence classification is wrong'
    );
    check_presentation(
        count($rows[1]['inventory_matches']['by_mac']) === 1 &&
        $rows[1]['inventory_matches']['by_mac'][0]['ip'] === '192.168.50.21',
        'by_mac lookup is wrong'
    );
    check_presentation(
        count($rows[1]['inventory_matches']['by_ip']) === 2,
        'shared-IP lookups were not preserved'
    );
    check_presentation(
        $rows[1]['inventory_matches']['by_ip'][0]['vlan'] === 'LAN' &&
        $rows[1]['inventory_matches']['by_ip'][1]['vlan'] === 'VLAN50',
        'shared-IP lookup ordering is not deterministic'
    );
    check_presentation(
        $rows[1]['inventory_matches']['by_ip'][1]['vendor'] ===
            '<script>alert(1)</script>',
        'hostile inventory text was changed by the API'
    );
    check_presentation(
        $rows[4]['inventory_matches']['by_mac'] === [] &&
        $rows[4]['inventory_matches']['by_ip'] === [] &&
        in_array($rows[4]['last_checked'], [null, ''], true),
        'missing inventory and timestamp data were not preserved'
    );
    check_presentation(
        array_key_exists('hostname', $rows[1]) &&
        array_key_exists('custom_hostname', $rows[1]),
        'existing API fields were removed'
    );
    check_presentation(
        isset($response['recent_changes'][0]['inventory_matches']),
        'recent changes lack page-response inventory lookups'
    );

    $rendered = run_email_renderer([
        'events' => [[
            'event_type' => 'SERVICE_UNAVAILABLE',
            'alert_eligible' => true,
            'occurred_at' => '2026-11-20 00:10:02',
            'service_type' => 'DNS',
            'mac' => 'aa:bb:cc:dd:ee:20',
            'ip' => '192.168.50.20',
            'port' => 53,
            'protocol' => 'udp',
            'interface' => '<script>alert(2)</script>',
            'detection_method' => 'dns_query',
            'old_value' => 'available',
            'new_value' => 'unavailable',
            'product' => '<script>alert(2)</script>',
        ]],
    ]);
    $html = $rendered['html'];

    check_presentation(
        strpos($html, 'Stored MAC attribution') !== false,
        'email MAC attribution label is missing'
    );
    check_presentation(
        strpos($html, 'Recorded status after event') !== false,
        'email recorded-status label is missing'
    );
    check_presentation(
        strpos($html, 'Current inventory lookups and latest check timestamps') !== false,
        'email provenance limitation is missing'
    );
    check_presentation(
        strpos($html, '<script>alert(2)</script>') === false,
        'email did not escape hostile input'
    );
    check_presentation(
        strpos($html, '&lt;script&gt;alert(2)&lt;/script&gt;') !== false,
        'email lost escaped hostile input'
    );

    @unlink($dbPath);
    @rmdir($tmp);

    echo "INFRASTRUCTURE_API_SHARED_IP=PASS\n";
    echo "INFRASTRUCTURE_API_EVIDENCE_KIND=PASS\n";
    echo "INFRASTRUCTURE_API_COMPAT_FIELDS=PASS\n";
    echo "INFRASTRUCTURE_API_HOSTILE_TEXT=PASS\n";
    echo "SERVICE_ALERT_EMAIL_PRESENTATION=PASS\n";
    echo "SERVICE_ALERT_EMAIL_RENDER_ONLY=NO_SEND\n";
    echo "INFRASTRUCTURE_PRESENTATION=PASS\n";
}
