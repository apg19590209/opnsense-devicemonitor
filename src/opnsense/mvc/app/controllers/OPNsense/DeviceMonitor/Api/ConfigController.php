<?php

namespace OPNsense\DeviceMonitor\Api;

use OPNsense\Base\ApiControllerBase;
use OPNsense\DeviceMonitor\DeviceMonitor;

require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/NotificationHandler.php');

/**
 * API controller for configuration management
 */
class ConfigController extends ApiControllerBase
{
    public function getAction()
    {
        $model = new DeviceMonitor();
        $config = $model->getConfig();
        /* The peer secret is write-only: expose only whether one is stored. */
        $config['email_log_peer_secret_set'] = !empty($config['email_log_peer_api_secret']) ? '1' : '0';
        unset($config['email_log_peer_api_secret']);
        return $config;
    }

    public function getversionAction()
    {
        $defaultsFile = '/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json';
        $defaults = json_decode(file_get_contents($defaultsFile), true);
        return ['version' => $defaults['version'] ?? '2.0'];
    }

    public function getinterfacesAction()
    {
        $result = [];
        try {
            $xml = @simplexml_load_file('/conf/config.xml');
            if ($xml && isset($xml->interfaces)) {
                foreach ($xml->interfaces->children() as $ifName => $ifData) {
                    $iface = trim((string)($ifData->if ?? ''));
                    $descr = trim((string)($ifData->descr ?? ''));
                    if (empty($iface)) continue;
                    if (empty($descr)) $descr = strtoupper($ifName);
                    if (preg_match('/vlan\d+\.(\d+)/i', $iface, $m)) {
                        $key = 'VLAN' . $m[1];
                    } else {
                        $key = strtoupper($iface);
                    }
                    $result[$key] = $descr;
                }
            }
        } catch (\Exception $e) {}
        return $result;
    }

    public function getmonitoredinterfacesAction()
    {
        $result = [];
        try {
            $xml = @simplexml_load_file('/conf/config.xml');
            if ($xml && isset($xml->interfaces)) {
                foreach ($xml->interfaces->children() as $ifName => $ifData) {
                    $name = (string)$ifName;
                    $enable = trim((string)($ifData->enable ?? ''));
                    $device = trim((string)($ifData->if ?? ''));
                    $ipaddr = trim((string)($ifData->ipaddr ?? ''));
                    $subnet = trim((string)($ifData->subnet ?? ''));
                    $descr = trim((string)($ifData->descr ?? ''));

                    if ($enable !== '1' || $device === '') {
                        continue;
                    }

                    $valid = (
                        filter_var($ipaddr, FILTER_VALIDATE_IP, FILTER_FLAG_IPV4) !== false
                        && ctype_digit($subnet) && $subnet !== ''
                        && (int)$subnet >= 1 && (int)$subnet <= 32
                    );
                    if (!$valid) {
                        continue;
                    }

                    if ($this->isLoopbackIpv4($ipaddr)) {
                        continue;
                    }

                    // Never offer the uplink: the daemon refuses it too, and a
                    // greyed-out entry is clearer than a save-time error.
                    if ($this->isUplinkInterface($name, $ifData, $ipaddr)) {
                        continue;
                    }

                    $result[$name] = [
                        'name' => $name,
                        'description' => $descr !== '' ? $descr : strtoupper($name),
                        'device' => $device,
                        'ipaddr' => $ipaddr,
                        'subnet' => $subnet,
                    ];
                }
            }
        } catch (\Exception $e) {}
        return $result;
    }
    /**
     * Read-only CARP state for the monitored interfaces plus the CARP virtual IPs
     * defined on this firewall. Consumed by the HA / CARP subtab.
     *
     * The role is derived the same way the daemon derives it: `ifconfig` prints
     * ``carp: MASTER|BACKUP vhid N ...`` on the device block, and MASTER wins over
     * BACKUP because a node that owns any monitored segment is observing it.
     * Nothing is stored, so the page can refresh this on demand.
     */
    public function getcarpstatusAction()
    {
        $model = new DeviceMonitor();
        $config = $model->getConfig();

        $override = strtolower(trim((string)($config['ha_role_override'] ?? 'auto')));
        if (!in_array($override, ['auto', 'master', 'backup'], true)) {
            $override = 'auto';
        }
        $overrideActive = ($override !== 'auto');

        /* An absent key means the setting predates the HA tab; the daemon then
         * behaves as it always has (CARP aware), which is what '1' means here. */
        $aware = !isset($config['ha_carp_enabled']) || ((string)$config['ha_carp_enabled'] === '1');
        $monitoringEnabled = ((string)($config['enabled'] ?? '0') === '1');

        $interfaceDevices = [];
        $vips = [];
        $configAvailable = true;
        $timezoneLabel = '';

        try {
            $xml = @simplexml_load_file('/conf/config.xml');
            if ($xml === false) {
                $configAvailable = false;
            }

            if ($xml && isset($xml->system->timezone)) {
                $configuredTimezone = trim((string)$xml->system->timezone);
                if ($configuredTimezone !== '') {
                    try {
                        new \DateTimeZone($configuredTimezone);
                        $timezoneLabel = $configuredTimezone;
                    } catch (\Exception $e) {
                        $timezoneLabel = '';
                    }
                }
            }

            if ($xml && isset($xml->interfaces)) {
                foreach ($xml->interfaces->children() as $ifName => $ifData) {
                    $device = trim((string)($ifData->if ?? ''));
                    if ($device !== '') {
                        $interfaceDevices[(string)$ifName] = $device;
                    }
                }
            }

            if ($xml && isset($xml->virtualip->vip)) {
                foreach ($xml->virtualip->vip as $vip) {
                    if (strtolower(trim((string)($vip->mode ?? ''))) !== 'carp') {
                        continue;
                    }
                    $vips[] = [
                        'interface' => trim((string)($vip->interface ?? '')),
                        'vhid' => trim((string)($vip->vhid ?? '')),
                        'subnet' => trim((string)($vip->subnet ?? '')),
                        'descr' => trim((string)($vip->descr ?? '')),
                    ];
                }
            }
        } catch (\Exception $e) {
            $configAvailable = false;
        }

        $monitored = [];
        foreach (explode(',', (string)($config['monitored_interfaces'] ?? '')) as $name) {
            $name = trim($name);
            if ($name !== '') {
                $monitored[] = $name;
            }
        }

        $carp = $this->carpStates();
        $states = $carp['states'];

        $seen = [];
        $resolvedMonitoredDevices = [];
        $unresolvedMonitoredInterfaces = [];
        foreach ($monitored as $name) {
            $device = $interfaceDevices[$name] ?? '';
            if ($device === '') {
                $unresolvedMonitoredInterfaces[] = $name;
                continue;
            }

            $resolvedMonitoredDevices[$device] = true;
            if (isset($states[$device])) {
                $seen[$states[$device]] = true;
            }
        }

        $monitoringScopeReady = count($monitored) > 0
            && count($unresolvedMonitoredInterfaces) === 0;
        $monitoringScopeReason = 'ready';
        if (count($monitored) === 0) {
            $monitoringScopeReason = 'no_monitored_interfaces';
        } elseif (count($unresolvedMonitoredInterfaces) > 0) {
            $monitoringScopeReason = 'unresolved_monitored_interfaces';
        }

        $role = 'none';
        $roleMixed = isset($seen['MASTER']) && isset($seen['BACKUP']);
        if (isset($seen['MASTER'])) {
            $role = 'MASTER';
        } elseif (isset($seen['BACKUP'])) {
            $role = 'BACKUP';
        }

        $mode = ($override === 'auto') ? $role : strtoupper($override);

        $observing = true;
        $reason = '';
        if ($aware && $mode === 'BACKUP') {
            $observing = false;
            $reason = ($override === 'backup') ? 'role override: backup' : 'CARP backup node';
        }

        /* A BACKUP node pauses only the observations that need MASTER traffic.
         * The daemon still performs the normal inventory scan, records
         * identity evidence, drains scheduled port discovery and ages its own
         * service state, so those must not be presented as paused. */
        $pausedActivities = [];
        if (!$observing) {
            $pausedActivities = [
                'visibility_priming',
                'service_discovery',
                'service_alerts',
                'identity_alerts',
                'new_device_alerts',
                'targeted_nmap',
            ];
        }

        /* The role needs both a readable ifconfig and config.xml's interface
         * map. An unreadable config must not fall through to a false non-HA
         * verdict merely because no monitored device could be resolved. */
        $roleAvailable = $carp['available'] && $configAvailable;
        $monitoringRolesKnown = $roleAvailable && $monitoringScopeReady;
        $effectiveModeKnown = $roleAvailable || $override !== 'auto';
        $roleUnknownObservationContinues = $aware
            && !$effectiveModeKnown
            && $observing
            && !$carp['available']
            && $configAvailable;
        $haStatus = 'non_ha';
        if (!$effectiveModeKnown) {
            $haStatus = 'unavailable';
        } elseif ($mode === 'BACKUP') {
            $haStatus = 'backup';
        } elseif ($mode === 'MASTER') {
            $haStatus = 'master';
        }

        /* Appliance-wide CARP absence is independent of monitoring scope. A
         * readable configuration with no CARP VIP plus readable ifconfig with
         * no CARP state anywhere proves the CARP controls are irrelevant even
         * when no monitored interface is selected. An empty selection or a
         * failed detector alone must never make that claim. */
        $applianceCarpState = 'unknown';
        if ($configAvailable && $carp['available']) {
            $applianceCarpState = (count($vips) > 0 || $carp['present'])
                ? 'present'
                : 'absent';
        }
        $applianceNonHa = ($applianceCarpState === 'absent' && !$overrideActive);

        /* Monitoring-scope readiness is separate from appliance-wide CARP
         * absence and from the role of the selected interfaces. The returned
         * reason lets the UI explain an empty or unresolved scope without
         * inferring anything from a failed detector or from CARP state that
         * exists outside the monitored selection. */
        $nonHaConfirmation = 'not_applicable';
        if ($haStatus === 'non_ha') {
            if ($applianceNonHa) {
                $nonHaConfirmation = 'appliance_non_ha';
            } elseif ((count($vips) > 0 || $carp['present']) && count($monitored) === 0) {
                $nonHaConfirmation = 'carp_present_no_monitored_interfaces';
            } elseif (count($vips) > 0) {
                $nonHaConfirmation = 'carp_vip_configured';
            } elseif ($carp['present']) {
                $nonHaConfirmation = 'carp_runtime_present_without_detected_role';
            } elseif (count($monitored) === 0) {
                $nonHaConfirmation = 'no_monitored_interfaces';
            } elseif (!$monitoringScopeReady) {
                $nonHaConfirmation = 'unresolved_monitored_interfaces';
            } else {
                $nonHaConfirmation = 'confirmed';
            }
        }
        $nonHaConfirmed = in_array($nonHaConfirmation, ['appliance_non_ha', 'confirmed'], true);
        $haRelevant = !$nonHaConfirmed;

        $lastScan = $this->lastSuccessfulLocalScan();

        $rows = [];
        foreach ($vips as $vip) {
            $device = $interfaceDevices[$vip['interface']] ?? '';
            $label = ($vip['subnet'] !== '') ? $vip['subnet'] : $vip['interface'];
            if ($vip['descr'] !== '') {
                $label .= ' (' . $vip['descr'] . ')';
            }
            $rows[] = [
                'vip' => $label,
                'vhid' => $vip['vhid'],
                'state' => ($device !== '' && isset($states[$device])) ? $states[$device] : 'unknown',
            ];
        }

        return [
            'result' => 'ok',
            'role' => $role,
            'mode' => $mode,
            'override' => $override,
            'observing' => $observing,
            'reason' => $reason,
            'role_available' => $roleAvailable,
            'config_available' => $configAvailable,
            'role_mixed' => $roleMixed,
            'carp_aware' => $aware,
            'appliance_carp_state' => $applianceCarpState,
            'appliance_non_ha_confirmed' => $applianceNonHa,
            'carp_vip_count' => count($vips),
            'carp_runtime_available' => $carp['available'],
            'carp_runtime_present' => $carp['present'],
            'ha_status' => $haStatus,
            'override_active' => $overrideActive,
            'non_ha_confirmation' => $nonHaConfirmation,
            'non_ha_confirmed' => $nonHaConfirmed,
            'ha_relevant' => $haRelevant,
            'monitoring_scope_ready' => $monitoringScopeReady,
            'monitoring_scope_reason' => $monitoringScopeReason,
            'monitoring_roles_known' => $monitoringRolesKnown,
            'node' => $this->nodeIdentity(),
            'node_local' => true,
            'monitoring_enabled' => $monitoringEnabled,
            'paused_activities' => $pausedActivities,
            'role_unknown_observation_continues' => $roleUnknownObservationContinues,
            'last_scan' => $lastScan['value'],
            'last_scan_state' => $lastScan['state'],
            'last_scan_timezone' => $timezoneLabel,
            'monitored_interfaces' => $monitored,
            'vips' => $rows,
        ];
    }

    /**
     * Map interface device names to their CARP state from `ifconfig -a`.
     *
     * The availability flag is separate from an empty state map: a readable
     * ifconfig with no CARP line is positive appliance-wide evidence, while an
     * unreadable command must not be shown as non-HA or promoted to MASTER.
     * `present` also records INIT and non-MASTER/BACKUP CARP lines so an
     * appliance with CARP outside the monitored selection is not mistaken for
     * a standalone node.
     *
     * @return array{states: array<string,string>, available: bool, present: bool}
     */
    private function carpStates()
    {
        $states = [];
        $present = false;
        $output = [];
        $status = 1;

        @exec('/sbin/ifconfig -a 2>/dev/null', $output, $status);

        $device = null;

        foreach ($output as $line) {
            if (!preg_match('/^\s/', $line)) {
                if (preg_match('/^([A-Za-z0-9_.\-]+):/', $line, $match)) {
                    $device = $match[1];
                }
                continue;
            }

            if ($device === null || stripos(ltrim($line), 'carp:') !== 0) {
                continue;
            }

            $present = true;

            $fields = preg_split('/\s+/', trim($line));
            $state = strtoupper((string)($fields[1] ?? ''));

            if ($state === 'MASTER' || $state === 'BACKUP') {
                $states[$device] = $state;
            }
        }

        return [
            'states' => $states,
            'available' => ($status === 0 && count($output) > 0),
            'present' => $present,
        ];
    }

    /**
     * Hostname is the node identity shown to the operator. It is deliberately
     * limited to the node name: no address, credential or peer URL is exposed.
     */
    private function nodeIdentity()
    {
        $hostname = @gethostname();

        if (!is_string($hostname) || trim($hostname) === '') {
            $hostname = @php_uname('n');
        }

        return trim((string)$hostname);
    }

    /**
     * Return the most recent successful scheduled daemon scan and whether the
     * local history was available at all.
     *
     * monitor_daemon.py appends this exact local-time line only after the scan
     * subprocess exits zero: ``[YYYY-MM-DD HH:MM:SS] Scan completed
     * successfully``. Reading the existing log avoids inventing scan state and
     * avoids changing the database for a read-only UI view. The reverse scan
     * stops at the newest match and keeps memory bounded for a large log.
     */
    private function lastSuccessfulLocalScan($logFile = '/var/log/devicemonitor.log')
    {
        if (!is_file($logFile) || !is_readable($logFile)) {
            return ['state' => 'unavailable', 'value' => ''];
        }

        $handle = @fopen($logFile, 'rb');
        if ($handle === false) {
            return ['state' => 'unavailable', 'value' => ''];
        }

        try {
            $size = @filesize($logFile);
            if (!is_int($size)) {
                return ['state' => 'unavailable', 'value' => ''];
            }

            $position = $size;
            $carry = '';
            $chunkSize = 65536;
            $pattern = '/^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] '
                . 'Scan completed successfully\s*$/m';

            while ($position > 0) {
                $readSize = min($chunkSize, $position);
                $position -= $readSize;

                if (@fseek($handle, $position, SEEK_SET) !== 0) {
                    return ['state' => 'unavailable', 'value' => ''];
                }

                $data = @fread($handle, $readSize);
                if (!is_string($data) || strlen($data) !== $readSize) {
                    return ['state' => 'unavailable', 'value' => ''];
                }

                $buffer = $data . $carry;
                if (preg_match_all($pattern, $buffer, $matches)) {
                    return ['state' => 'found', 'value' => (string)end($matches[1])];
                }

                $newline = strpos($buffer, "\n");
                $carry = ($newline === false) ? $buffer : substr($buffer, 0, $newline);
            }
        } finally {
            @fclose($handle);
        }

        return ['state' => 'none', 'value' => ''];
    }

    private function ipv4SubnetRange($ip, $prefix)
    {
        $ipLong = ip2long($ip);
        if ($ipLong === false || $prefix < 1 || $prefix > 32) {
            return null;
        }
        $mask = (-1 << (32 - $prefix)) & 0xFFFFFFFF;
        $start = $ipLong & $mask;
        $end = $start | (~$mask & 0xFFFFFFFF);
        return [$start, $end];
    }

    private function isLoopbackIpv4($ip)
    {
        $ipLong = ip2long($ip);
        if ($ipLong === false) {
            return false;
        }
        $loStart = ip2long('127.0.0.0');
        $loEnd = ip2long('127.255.255.255');
        return $ipLong >= $loStart && $ipLong <= $loEnd;
    }

    /**
     * True when an interface is the WAN/uplink and must not be monitored.
     *
     * Mirrors resolve_monitored_networks() in scan_network.py: the assignment
     * name "wan" is refused outright, and any interface carrying a gateway on a
     * non-RFC1918 address is an uplink. A gateway on private space is an
     * internal segment using policy routing and stays selectable.
     */
    private function isUplinkInterface($name, $ifData, $ipaddr)
    {
        if (strtolower((string)$name) === 'wan') {
            return true;
        }

        $gateway = trim((string)($ifData->gateway ?? ''));

        if ($gateway === '') {
            return false;
        }

        $ipLong = ip2long($ipaddr);
        if ($ipLong === false) {
            return false;
        }

        foreach (['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'] as $cidr) {
            [$network, $prefix] = explode('/', $cidr);
            $range = $this->ipv4SubnetRange($network, (int)$prefix);
            if ($range !== null && $ipLong >= $range[0] && $ipLong <= $range[1]) {
                return false;
            }
        }

        return true;
    }

    public function setAction()
    {
        if (!$this->request->isPost()) {
            return ['result' => 'failed', 'message' => 'Must be a POST request'];
        }

        $model = new DeviceMonitor();

        $enabled = $this->request->getPost('enabled', 'string', '0');
        $email_enabled = $this->request->getPost('email_enabled', 'string', '0');
        $identity_webhook_enabled = $this->request->getPost('identity_webhook_enabled', 'string', '0');
        // Decision 36: identity-conflict alerts are webhook-only. The key stays a
        // stored preference for configuration compatibility; the Settings view no
        // longer posts it, so an existing value is preserved rather than reset.
        $identity_email_enabled = (string)($config['identity_email_enabled'] ?? '0');
        $service_email_enabled = $this->request->getPost('service_email_enabled', 'string', '0');
        $service_email_new = $this->request->getPost('service_email_new', 'string', '1');
        $service_email_unavailable = $this->request->getPost('service_email_unavailable', 'string', '1');
        $service_email_recovered = $this->request->getPost('service_email_recovered', 'string', '1');
        $email_to = trim($this->request->getPost('email_to', 'string', ''));
        $email_from = trim($this->request->getPost('email_from', 'string', 'devicemonitor@opnsense.local'));
        $email_method = strtolower(trim($this->request->getPost('email_method', 'string', 'sendmail')));
        $smtp_host = trim($this->request->getPost('smtp_host', 'string', ''));
        $smtp_port = (int)$this->request->getPost('smtp_port', 'int', 587);
        $smtp_encryption = strtolower(trim($this->request->getPost('smtp_encryption', 'string', '')));
        if ($smtp_encryption === '') {
            // Port 25 falls back to an explicit unencrypted session; other ports keep STARTTLS.
            $smtp_encryption = ($smtp_port === 25) ? 'none' : 'starttls';
        }
        $smtp_username = trim($this->request->getPost('smtp_username', 'string', ''));
        $smtp_password = $this->request->getPost('smtp_password', 'string', '');

        $adguard_rewrite_enabled = $this->request->getPost('adguard_rewrite_enabled', 'string', '0');
        $adguard_url = trim($this->request->getPost('adguard_url', 'string', ''));
        $adguard_username = trim($this->request->getPost('adguard_username', 'string', ''));
        $adguard_password = $this->request->getPost('adguard_password', 'string', '');

        $pihole_enabled = $this->request->getPost('pihole_enabled', 'string', '0');
        $pihole_url = trim($this->request->getPost('pihole_url', 'string', ''));
        $pihole_password = $this->request->getPost('pihole_password', 'string', '');

        $unbound_enabled = $this->request->getPost('unbound_enabled', 'string', '0');

        /* HA / CARP. The role override is a closed set: anything else falls back
         * to detection so a corrupted POST can never pin a node silently. */
        $ha_carp_enabled = $this->request->getPost('ha_carp_enabled', 'string', '1');
        $ha_role_override = strtolower(trim($this->request->getPost('ha_role_override', 'string', 'auto')));
        $ha_notify_failover = $this->request->getPost('ha_notify_failover', 'string', '0');

        if (!in_array($ha_carp_enabled, ['0', '1'], true)) {
            return ['result' => 'failed', 'message' => 'Invalid ha_carp_enabled value'];
        }

        if (!in_array($ha_notify_failover, ['0', '1'], true)) {
            return ['result' => 'failed', 'message' => 'Invalid ha_notify_failover value'];
        }

        if (!in_array($ha_role_override, ['auto', 'master', 'backup'], true)) {
            return ['result' => 'failed', 'message' => 'Invalid ha_role_override value'];
        }

        $webhook_enabled = $this->request->getPost('webhook_enabled', 'string', '0');
        $webhook_url = $this->request->getPost('webhook_url', 'string', '');
        $scan_interval = $this->request->getPost('scan_interval', 'int', 300);
        $email_vlans = $this->request->getPost('email_vlans', 'string', '');
        $webhook_vlans = $this->request->getPost('webhook_vlans', 'string', '');
        $peer_enabled = $this->request->getPost('email_log_peer_enabled', 'string', '0');
        $peer_url = trim($this->request->getPost('email_log_peer_url', 'string', ''));
        $peer_api_key = trim($this->request->getPost('email_log_peer_api_key', 'string', ''));
        $peer_api_secret = $this->request->getPost('email_log_peer_api_secret', 'string', '');
        $peer_ca_pem = (string)$this->request->getPost('email_log_peer_ca_pem', 'string', '');
        $peer_timeout = (int)$this->request->getPost('email_log_peer_timeout', 'int', 8);
        $monitored_interfaces_raw = trim($this->request->getPost('monitored_interfaces', 'string', ''));

        $targeted_nmap_enabled = $this->request->getPost('targeted_nmap_enabled', 'string', '1');
        $nmap_top_ports = (int)$this->request->getPost('nmap_top_ports', 'int', 100);
        $nmap_timing = (int)$this->request->getPost('nmap_timing', 'int', 4);
        $nmap_host_timeout = (int)$this->request->getPost('nmap_host_timeout', 'int', 45);
        $nmap_version_detection = $this->request->getPost('nmap_version_detection', 'string', '1');
        $nmap_max_per_cycle = (int)$this->request->getPost('nmap_max_per_cycle', 'int', 2);

        /* Repeat interval for unchanged state, per email category, in minutes.
         * 0 (the default) means "only when the state changes". */
        $email_reminder_scan = (int)$this->request->getPost('email_reminder_scan', 'int', 0);
        $email_reminder_service = (int)$this->request->getPost('email_reminder_service', 'int', 0);
        $email_reminder_identity = (int)$this->request->getPost('email_reminder_identity', 'int', 0);
        $email_reminder_new_device = (int)$this->request->getPost('email_reminder_new_device', 'int', 0);

        if (!in_array($identity_webhook_enabled, ['0', '1'], true)) {
            return ['result' => 'failed', 'message' => 'Invalid identity webhook enabled value'];
        }

        if (!in_array($identity_email_enabled, ['0', '1'], true)) {
            $identity_email_enabled = '0';
        }

        foreach ([
            'service_email_enabled' => $service_email_enabled,
            'service_email_new' => $service_email_new,
            'service_email_unavailable' => $service_email_unavailable,
            'service_email_recovered' => $service_email_recovered,
        ] as $setting => $value) {
            if (!in_array($value, ['0', '1'], true)) {
                return ['result' => 'failed', 'message' => 'Invalid ' . $setting . ' value'];
            }
        }

        if (!in_array($email_method, ['sendmail', 'smtp'], true)) {
            return ['result' => 'failed', 'message' => 'Invalid email delivery method'];
        }

        if (!in_array($smtp_encryption, ['none', 'starttls', 'ssl'], true)) {
            return ['result' => 'failed', 'message' => 'Invalid SMTP encryption type'];
        }

        if (!in_array($adguard_rewrite_enabled, ['0', '1'], true)) {
            return ['result' => 'failed', 'message' => 'Invalid AdGuard rewrite enabled value'];
        }

        if ($adguard_rewrite_enabled === '1') {
            if ($adguard_url === '' || !filter_var($adguard_url, FILTER_VALIDATE_URL)) {
                return ['result' => 'failed', 'message' => 'Invalid AdGuard URL'];
            }

            $adguard_url_parts = parse_url($adguard_url);

            if (
                !is_array($adguard_url_parts)
                || !in_array(strtolower((string)($adguard_url_parts['scheme'] ?? '')), ['http', 'https'], true)
            ) {
                return ['result' => 'failed', 'message' => 'AdGuard URL must use http or https'];
            }

            if (
                isset($adguard_url_parts['user'])
                || isset($adguard_url_parts['pass'])
                || isset($adguard_url_parts['query'])
                || isset($adguard_url_parts['fragment'])
            ) {
                return [
                    'result' => 'failed',
                    'message' => 'AdGuard URL must not contain credentials, query or fragment'
                ];
            }

            if ($adguard_username === '') {
                return ['result' => 'failed', 'message' => 'AdGuard username must not be empty'];
            }

            if ($adguard_password === '') {
                return ['result' => 'failed', 'message' => 'AdGuard password must not be empty'];
            }
        }

        if (!in_array($pihole_enabled, ['0', '1'], true)) {
            return ['result' => 'failed', 'message' => 'Invalid Pi-hole enabled value'];
        }

        if ($pihole_enabled === '1') {
            if ($pihole_url === '' || !filter_var($pihole_url, FILTER_VALIDATE_URL)) {
                return ['result' => 'failed', 'message' => 'Invalid Pi-hole URL'];
            }

            $pihole_url_parts = parse_url($pihole_url);

            if (
                !is_array($pihole_url_parts)
                || strtolower((string)($pihole_url_parts['scheme'] ?? '')) !== 'https'
            ) {
                return ['result' => 'failed', 'message' => 'Pi-hole URL must use HTTPS'];
            }

            if (
                isset($pihole_url_parts['user'])
                || isset($pihole_url_parts['pass'])
                || isset($pihole_url_parts['query'])
                || isset($pihole_url_parts['fragment'])
            ) {
                return [
                    'result' => 'failed',
                    'message' => 'Pi-hole URL must not contain credentials, query or fragment'
                ];
            }

            if ($pihole_password === '') {
                return ['result' => 'failed', 'message' => 'Pi-hole app password must not be empty'];
            }
        }

        if (!in_array($unbound_enabled, ['0', '1'], true)) {
            return ['result' => 'failed', 'message' => 'Invalid Unbound enabled value'];
        }

        if ($email_enabled == '1') {
            if (empty($email_to) || !filter_var($email_to, FILTER_VALIDATE_EMAIL)) {
                return ['result' => 'failed', 'message' => 'Invalid recipient email address'];
            }

            if (empty($email_from) || !filter_var($email_from, FILTER_VALIDATE_EMAIL)) {
                return ['result' => 'failed', 'message' => 'Invalid sender email address'];
            }

            if ($email_method === 'smtp') {
                if ($smtp_host === '') {
                    return ['result' => 'failed', 'message' => 'SMTP server must not be empty'];
                }
                if ($smtp_port < 1 || $smtp_port > 65535) {
                    return ['result' => 'failed', 'message' => 'SMTP port must be between 1 and 65535'];
                }
            }
        }

        if ($webhook_enabled == '1') {
            if (empty($webhook_url)) {
                return ['result' => 'failed', 'message' => 'Webhook URL must not be empty'];
            }
            if (!filter_var($webhook_url, FILTER_VALIDATE_URL)) {
                return ['result' => 'failed', 'message' => 'Invalid webhook URL'];
            }
        }

        if ($scan_interval < 60 || $scan_interval > 3600) {
            return ['result' => 'failed', 'message' => 'Scan interval must be between 60 and 3600 seconds'];
        }

        if (!in_array($targeted_nmap_enabled, ['0', '1'], true)) {
            return ['result' => 'failed', 'message' => 'Invalid targeted Nmap enabled value'];
        }

        if ($nmap_top_ports < 1 || $nmap_top_ports > 1000) {
            return ['result' => 'failed', 'message' => 'Nmap top ports must be between 1 and 1000'];
        }

        if ($nmap_timing < 0 || $nmap_timing > 5) {
            return ['result' => 'failed', 'message' => 'Nmap timing template must be between 0 and 5'];
        }

        if ($nmap_host_timeout < 10 || $nmap_host_timeout > 300) {
            return ['result' => 'failed', 'message' => 'Nmap host timeout must be between 10 and 300 seconds'];
        }

        if (!in_array($nmap_version_detection, ['0', '1'], true)) {
            return ['result' => 'failed', 'message' => 'Invalid Nmap version detection value'];
        }

        if ($nmap_max_per_cycle < 1 || $nmap_max_per_cycle > 10) {
            return ['result' => 'failed', 'message' => 'Nmap scans per cycle must be between 1 and 10'];
        }

        foreach ([
            'email_reminder_scan' => $email_reminder_scan,
            'email_reminder_service' => $email_reminder_service,
            'email_reminder_identity' => $email_reminder_identity,
            'email_reminder_new_device' => $email_reminder_new_device,
        ] as $reminder_setting => $reminder_value) {
            if ($reminder_value < 0 || $reminder_value > 1440) {
                return [
                    'result' => 'failed',
                    'message' => 'Invalid ' . $reminder_setting . ' value (0-1440 minutes)'
                ];
            }
        }

        $monitored_interfaces = [];
        $monitored_ranges = [];
        if ($monitored_interfaces_raw !== '') {
            $names = array_values(array_unique(
                array_filter(array_map('trim', explode(',', $monitored_interfaces_raw)), 'strlen')
            ));

            $xml = @simplexml_load_file('/conf/config.xml');
            if (!$xml || !isset($xml->interfaces)) {
                return ['result' => 'failed', 'message' => 'Cannot read /conf/config.xml'];
            }

            foreach ($names as $name) {
                if (!preg_match('/^[A-Za-z0-9_]+$/', $name)) {
                    return ['result' => 'failed', 'message' => 'Monitored interface name is invalid'];
                }

                $ifData = $xml->interfaces->{$name} ?? null;
                if (!$ifData) {
                    return ['result' => 'failed', 'message' => 'Monitored interface "' . $name . '" does not exist'];
                }
                if (trim((string)($ifData->enable ?? '')) !== '1') {
                    return ['result' => 'failed', 'message' => 'Monitored interface "' . $name . '" is not enabled'];
                }
                $device = trim((string)($ifData->if ?? ''));
                if ($device === '') {
                    return ['result' => 'failed', 'message' => 'Monitored interface "' . $name . '" has no device'];
                }
                $ipaddr = trim((string)($ifData->ipaddr ?? ''));
                $subnet = trim((string)($ifData->subnet ?? ''));
                if (filter_var($ipaddr, FILTER_VALIDATE_IP, FILTER_FLAG_IPV4) === false) {
                    return ['result' => 'failed', 'message' => 'Monitored interface "' . $name . '" has no valid static IPv4 address'];
                }
                if ($this->isLoopbackIpv4($ipaddr)) {
                    return ['result' => 'failed', 'message' => 'Monitored interface "' . $name . '" uses a loopback address and cannot be monitored'];
                }
                if ($this->isUplinkInterface($name, $ifData, $ipaddr)) {
                    return ['result' => 'failed', 'message' => 'Monitored interface "' . $name . '" is the WAN/uplink; Device Monitor monitors internal segments only'];
                }
                if (
                    $subnet === '' ||
                    !ctype_digit($subnet) ||
                    (int)$subnet < 1 ||
                    (int)$subnet > 32
                ) {
                    return ['result' => 'failed', 'message' => 'Monitored interface "' . $name . '" subnet prefix must be between 1 and 32'];
                }

                $range = $this->ipv4SubnetRange($ipaddr, (int)$subnet);
                if ($range === null) {
                    return ['result' => 'failed', 'message' => 'Monitored interface "' . $name . '" has an invalid IPv4 subnet'];
                }

                foreach ($monitored_ranges as $existing) {
                    if (!($range[1] < $existing[0] || $existing[1] < $range[0])) {
                        return [
                            'result' => 'failed',
                            'message' => 'Monitored interfaces "' . $existing[2] . '" and "' . $name . '" overlap; select non-overlapping subnets only'
                        ];
                    }
                }

                $monitored_ranges[] = [$range[0], $range[1], $name];
                $monitored_interfaces[] = $name;
            }
        }

        $config = $model->getConfig();
        $config['enabled'] = $enabled;
        $config['email_enabled'] = $email_enabled;
        $config['service_email_enabled'] = $service_email_enabled;
        $config['service_email_new'] = $service_email_new;
        $config['service_email_unavailable'] = $service_email_unavailable;
        $config['service_email_recovered'] = $service_email_recovered;
        $config['email_to'] = $email_to;
        $config['email_from'] = $email_from;
        $config['email_method'] = $email_method;
        $config['smtp_host'] = $smtp_host;
        $config['smtp_port'] = $smtp_port;
        $config['smtp_encryption'] = $smtp_encryption;
        $config['smtp_username'] = $smtp_username;
        $config['smtp_password'] = $smtp_password;
        $config['adguard_rewrite_enabled'] = $adguard_rewrite_enabled;
        $config['adguard_url'] = $adguard_url;
        $config['adguard_username'] = $adguard_username;
        $config['adguard_password'] = $adguard_password;
        $config['pihole_enabled'] = $pihole_enabled;
        $config['pihole_url'] = $pihole_url;
        $config['pihole_password'] = $pihole_password;
        $config['unbound_enabled'] = $unbound_enabled;
        $config['ha_carp_enabled'] = $ha_carp_enabled;
        $config['ha_role_override'] = $ha_role_override;
        $config['ha_notify_failover'] = $ha_notify_failover;
        $config['webhook_enabled'] = $webhook_enabled;
        $config['webhook_url'] = $webhook_url;
        $config['identity_webhook_enabled'] = $identity_webhook_enabled;
        $config['identity_email_enabled'] = $identity_email_enabled;
        $config['scan_interval'] = (int)$scan_interval;
        $config['email_vlans'] = $email_vlans;
        $config['webhook_vlans'] = $webhook_vlans;

        /* Peer settings: the URL must be https and the secret is write-only. An
         * empty secret field keeps whatever is stored; the value is never returned. */
        if ($peer_enabled !== '0' && $peer_enabled !== '1') {
            return ['result' => 'failed', 'message' => 'Invalid peer enabled value'];
        }
        if ($peer_url !== '') {
            $parts = parse_url($peer_url);
            if (!is_array($parts) || !isset($parts['scheme'], $parts['host'])
                || strtolower($parts['scheme']) !== 'https'
                || isset($parts['user']) || isset($parts['pass'])
                || isset($parts['query']) || isset($parts['fragment'])) {
                return ['result' => 'failed', 'message' => 'Peer URL must be an absolute https:// URL without credentials, query or fragment'];
            }
        }
        if ($peer_timeout < 2 || $peer_timeout > 30) {
            return ['result' => 'failed', 'message' => 'Peer timeout must be between 2 and 30 seconds'];
        }
        if ($peer_ca_pem !== '' && strpos($peer_ca_pem, 'BEGIN CERTIFICATE') === false) {
            return ['result' => 'failed', 'message' => 'Peer CA must be PEM certificate content'];
        }
        $config['email_log_peer_enabled'] = $peer_enabled;
        $config['email_log_peer_url'] = $peer_url;
        $config['email_log_peer_api_key'] = $peer_api_key;
        $config['email_log_peer_ca_pem'] = $peer_ca_pem;
        $config['email_log_peer_timeout'] = (string)$peer_timeout;
        if ($peer_api_secret !== '') {
            $config['email_log_peer_api_secret'] = $peer_api_secret;
        }
        $config['monitored_interfaces'] = implode(',', $monitored_interfaces);
        $config['targeted_nmap_enabled'] = $targeted_nmap_enabled;
        $config['nmap_top_ports'] = $nmap_top_ports;
        $config['nmap_timing'] = $nmap_timing;
        $config['nmap_host_timeout'] = $nmap_host_timeout;
        $config['nmap_version_detection'] = $nmap_version_detection;
        $config['nmap_max_per_cycle'] = $nmap_max_per_cycle;
        $config['email_reminder_scan'] = $email_reminder_scan;
        $config['email_reminder_service'] = $email_reminder_service;
        $config['email_reminder_identity'] = $email_reminder_identity;
        $config['email_reminder_new_device'] = $email_reminder_new_device;

        /* O4 / DM-BL-008c - sidecar translation toggle.
         * Written only when the form actually posts the field, so an older settings
         * page or a partial API call can never silently switch the sidecar off. A
         * missing key stays enabled (see defaults.json and devicemonitor_locale.inc). */
        $sidecar_translation_enabled = $this->request->getPost('sidecar_translation_enabled', 'string', null);
        if ($sidecar_translation_enabled !== null) {
            $config['sidecar_translation_enabled'] =
                (trim((string)$sidecar_translation_enabled) === '1') ? '1' : '0';
        }

        if ($model->setConfig($config)) {
            return ['result' => 'saved', 'message' => 'Configuration saved'];
        }

        return ['result' => 'failed', 'message' => 'Failed to save configuration'];
    }

    public function testemailAction()
    {
        $handler = new \NotificationHandler();
        $handler->fLog("Preparing to send test email", 'EMAIL');
        $result = $handler->sendEmail(true);

        $logMessage = "Test email result: " . (($result['result'] === 'sent' || $result['result'] === 'ok') ? "SUCCESS" : "FAILED");
        if ($result['result'] !== 'sent' && $result['result'] !== 'ok') {
            $logMessage .= " | Reason: " . ($result['message'] ?? 'Unknown error');
        }
        $handler->fLog($logMessage, "EMAIL-ConfigController");
        return $result;
    }

    public function testWebhookAction()
    {
        $handler = new \NotificationHandler();
        $handler->fLog("Preparing to send test webhook", 'WEBHOOK');

        /* A test needs an explicit URL from the form. Absent, empty and
         * whitespace-only values are rejected here rather than handed to curl. */
        $webhook_url = trim((string)$this->request->getPost('webhook_url', 'string', ''));
        if ($webhook_url === '') {
            $handler->fLog("Test webhook result: FAILED | Reason: Webhook URL required", "WEBHOOK-ConfigController");
            return ['result' => 'failed', 'message' => 'Webhook URL required'];
        }

        /* The test frame carries explicit topic and message keys. sendWebhook()
         * skips endpoint detection for a caller-owned frame and posts it as
         * generic JSON, so the Discord-compatible "content" key is added here
         * when the URL is a Discord webhook (Discord rejects a topic/message
         * frame). hostname and timestamp are filled in by sendWebhook(). */
        $test_message = 'Device Monitor webhook is working!';
        /* The custom topic name is parsed from the URL the operator entered: the
         * last non-empty path segment carries it, so
         * https://ntfy.sh/opnsense_monitor -> opnsense_monitor. Query strings and
         * fragments never contribute, and a value without a host, or without a
         * path segment, falls back to the hostname. */
        $topic = gethostname() ?: 'Device Monitor';
        $url_host = (string)parse_url($webhook_url, PHP_URL_HOST);
        $url_path = (string)parse_url($webhook_url, PHP_URL_PATH);
        $url_segments = array_values(array_filter(explode('/', $url_path), 'strlen'));
        if ($url_host !== '' && $url_segments !== []) {
            $topic = rawurldecode((string)end($url_segments));
        }
        $payload = [
            'topic' => $topic,
            'message' => $test_message,
        ];
        if (stripos($webhook_url, 'discord') !== false) {
            $payload['content'] = $test_message;
            $payload['username'] = 'OPNsense Device Monitor';
        }

        $result = $handler->sendWebhook(true, $webhook_url, $payload);

        $logMessage = "Test webhook result: " . (($result['result'] === 'sent' || $result['result'] === 'ok') ? "SUCCESS" : "FAILED");
        if ($result['result'] !== 'sent' && $result['result'] !== 'ok') {
            $logMessage .= " | Reason: " . ($result['message'] ?? 'Unknown error');
        }
        $handler->fLog($logMessage, "WEBHOOK-ConfigController");
        return $result;
    }

    public function sendEmailAction()
    {
        $handler = new \NotificationHandler();
        $handler->fLog("Preparing to send email notification", 'EMAIL');
        $result = $handler->sendEmail(false);

        $logMessage = "Email notification result: ";
        if ($result['result'] === 'sent') {
            $logMessage .= "SUCCESS";
        } elseif ($result['result'] === 'skipped') {
            $logMessage .= "SKIPPED";
        } else {
            $logMessage .= "FAILED";
            $logMessage .= " | Reason: " . ($result['message'] ?? 'Unknown error');
        }
        $handler->fLog($logMessage, "EMAIL-ConfigController");
        return $result;
    }

    public function sendWebhookAction()
    {
        $handler = new \NotificationHandler();
        $handler->fLog("Preparing to send webhook notification", 'WEBHOOK');

        /* Strict guard. The parameter used to reach the handler as '' whenever the
         * caller omitted it; the handler only short-circuits on null, so the
         * "Webhook disabled" guard was bypassed and delivery was attempted to an
         * empty URL. Absent, null, empty and whitespace-only values are now all
         * detected, and an unresolvable endpoint stops here. */
        $webhook_url = trim((string)$this->request->getPost('webhook_url', 'string', ''));
        if ($webhook_url === '') {
            $backendConfig = \OPNsense\DeviceMonitor\DeviceMonitor::getConfig();
            $configured_url = isset($backendConfig['webhook_url'])
                ? trim((string)$backendConfig['webhook_url'])
                : '';
            $configured_enabled = isset($backendConfig['webhook_enabled'])
                ? ((string)$backendConfig['webhook_enabled'] === '1')
                : false;

            if ($configured_url === '' || !$configured_enabled) {
                $handler->fLog("Webhook notification result: SKIPPED | Reason: Webhook disabled", "WEBHOOK-ConfigController");
                return ['result' => 'skipped', 'message' => 'Webhook disabled'];
            }

            $webhook_url = $configured_url;
        }

        $result = $handler->sendWebhook(false, $webhook_url);

        $logMessage = "Webhook notification result: ";
        if ($result['result'] === 'sent' || $result['result'] === 'ok') {
            $logMessage .= "SUCCESS";
        } elseif ($result['result'] === 'skipped') {
            $logMessage .= "SKIPPED";
        } else {
            $logMessage .= "FAILED";
            $logMessage .= " | Reason: " . ($result['message'] ?? 'Unknown error');
        }
        $handler->fLog($logMessage, "WEBHOOK-ConfigController");
        return $result;
    }
}
