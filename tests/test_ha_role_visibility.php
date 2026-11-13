<?php

/**
 * HA-role visibility must use the existing getcarpstatus source and preserve
 * the daemon's distinction between detected CARP role, effective mode, and
 * whether observation is allowed.
 *
 * The test stubs ifconfig, config.xml and the hostname. It does not execute a
 * service action, read live CARP state or modify the node.
 */

namespace OPNsense\Base {
    class ApiControllerBase
    {
        public $request;
    }
}

namespace OPNsense\DeviceMonitor {
    class DeviceMonitor
    {
        public static $config = [];

        public function getConfig()
        {
            return self::$config;
        }
    }
}

namespace OPNsense\DeviceMonitor\Api {
    function simplexml_load_file($path)
    {
        return @\simplexml_load_string($GLOBALS['dm_ha_xml']);
    }

    function exec($command, &$output, &$status)
    {
        $output = $GLOBALS['dm_ha_ifconfig'];
        $status = $GLOBALS['dm_ha_exec_status'];
        return $status === 0 ? '' : false;
    }

    function gethostname()
    {
        return $GLOBALS['dm_ha_hostname'];
    }
}

namespace {
    $controllerSource = __DIR__
        . '/../src/opnsense/mvc/app/controllers/OPNsense/'
        . 'DeviceMonitor/Api/ConfigController.php';
    $source = file_get_contents($controllerSource);
    $externalRequire = "require_once('/usr/local/opnsense/scripts/OPNsense/"
        . "DeviceMonitor/NotificationHandler.php');\n";
    $isolated = str_replace($externalRequire, '', $source, $removed);
    if ($removed !== 1) {
        fwrite(STDERR, "FAIL: could not isolate NotificationHandler require\n");
        exit(1);
    }
    $controllerCopy = tempnam(sys_get_temp_dir(), 'dm-ha-controller-');
    file_put_contents($controllerCopy, $isolated);
    require_once $controllerCopy;
    unlink($controllerCopy);

    use OPNsense\DeviceMonitor\DeviceMonitor;
    use OPNsense\DeviceMonitor\Api\ConfigController;

    function check($condition, $message)
    {
        if (!$condition) {
            throw new \RuntimeException($message);
        }
    }

    function status_case($ifconfig, $execStatus = 0, $config = [], $xml = null)
    {
        DeviceMonitor::$config = array_merge([
            'ha_role_override' => 'auto',
            'ha_carp_enabled' => '1',
            'monitored_interfaces' => 'lan,opt1',
        ], $config);

        $GLOBALS['dm_ha_ifconfig'] = $ifconfig;
        $GLOBALS['dm_ha_exec_status'] = $execStatus;
        $GLOBALS['dm_ha_hostname'] = 'dm-node.test';
        $GLOBALS['dm_ha_xml'] = $xml === null ? <<<XML
<opnsense>
  <system><timezone>Australia/Sydney</timezone></system>
  <interfaces>
    <lan><if>re0</if></lan>
    <opt1><if>re1</if></opt1>
  </interfaces>
</opnsense>
XML
            : $xml;

        return (new ConfigController())->getcarpstatusAction();
    }

    $master = [
        're0: flags=1008843<UP,BROADCAST,RUNNING>',
        "\tcarp: MASTER vhid 1 advbase 1 advskew 0",
        're1: flags=1008843<UP,BROADCAST,RUNNING>',
    ];
    $backup = [
        're0: flags=1008843<UP,BROADCAST,RUNNING>',
        "\tcarp: BACKUP vhid 1 advbase 1 advskew 100",
        're1: flags=1008843<UP,BROADCAST,RUNNING>',
    ];
    $mixed = [
        're0: flags=1008843<UP,BROADCAST,RUNNING>',
        "\tcarp: MASTER vhid 1 advbase 1 advskew 0",
        're1: flags=1008843<UP,BROADCAST,RUNNING>',
        "\tcarp: BACKUP vhid 2 advbase 1 advskew 100",
    ];
    $noCarp = [
        're0: flags=1008843<UP,BROADCAST,RUNNING>',
        "\tinet 192.0.2.10 netmask 0xffffff00",
        're1: flags=1008843<UP,BROADCAST,RUNNING>',
    ];
    $liveNoCarp = [
        'lo0: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST>',
        "\tinet 127.0.0.1 netmask 0xff000000",
        're0: flags=1008843<UP,BROADCAST,RUNNING>',
        "\tinet 192.168.20.23 netmask 0xffffff00",
        'iwm0_wlan0: flags=1008843<UP,BROADCAST,RUNNING>',
        'vlan0.50: flags=1008843<UP,BROADCAST,RUNNING>',
    ];
    $initCarp = [
        're0: flags=1008843<UP,BROADCAST,RUNNING>',
        "\tcarp: INIT vhid 1 advbase 1 advskew 0",
    ];
    $paused = [
        'visibility_priming',
        'service_discovery',
        'service_alerts',
        'identity_alerts',
        'new_device_alerts',
        'targeted_nmap',
    ];

    $result = status_case($master);
    check($result['role'] === 'MASTER', 'MASTER role not detected');
    check($result['mode'] === 'MASTER', 'MASTER effective mode not retained');
    check($result['role_mixed'] === false, 'MASTER-only node marked mixed');
    check($result['ha_status'] === 'master', 'MASTER status not returned');
    check($result['observing'] === true, 'MASTER observation unexpectedly paused');
    check($result['paused_activities'] === [], 'MASTER returned paused activities');
    check($result['role_available'] === true, 'MASTER role marked unavailable');
    check($result['config_available'] === true, 'MASTER config marked unavailable');
    check($result['override_active'] === false, 'MASTER marked override active');
    check($result['non_ha_confirmed'] === false, 'MASTER marked as non-HA');
    check($result['ha_relevant'] === true, 'MASTER hid HA relevance');
    check($result['role_unknown_observation_continues'] === false,
        'MASTER was marked as running without a known role');
    check($result['monitoring_enabled'] === false,
        'monitoring-disabled default was not reported');
    check($result['node'] === 'dm-node.test', 'node identity not returned');
    check($result['node_local'] === true, 'node-local ownership not returned');
    check($result['last_scan_timezone'] === 'Australia/Sydney',
        'configured scan timezone was not returned');
    echo "HA_VISIBILITY_MASTER=PASS\n";

    $result = status_case($master, 0, [], <<<XML
<opnsense>
  <system><timezone>Invalid/Zone</timezone></system>
  <interfaces>
    <lan><if>re0</if></lan>
    <opt1><if>re1</if></opt1>
  </interfaces>
</opnsense>
XML
    );
    check($result['last_scan_timezone'] === '',
        'invalid configured timezone was exposed as a verified label');
    echo "HA_VISIBILITY_TIMEZONE=PASS\n";

    $result = status_case($master, 0, ['enabled' => '1']);
    check($result['monitoring_enabled'] === true,
        'monitoring-enabled state was not reported');
    $result = status_case($master, 0, ['enabled' => '0']);
    check($result['monitoring_enabled'] === false,
        'monitoring-disabled state was not reported');
    echo "HA_VISIBILITY_MONITORING_STATE=PASS\n";

    $result = status_case($backup);
    check($result['role'] === 'BACKUP', 'BACKUP role not detected');
    check($result['mode'] === 'BACKUP', 'BACKUP effective mode not retained');
    check($result['ha_status'] === 'backup', 'BACKUP status not returned');
    check($result['observing'] === false, 'BACKUP observation not paused');
    check($result['paused_activities'] === $paused, 'BACKUP paused activity list drifted');
    check($result['carp_aware'] === true, 'CARP awareness flag missing');
    check($result['role_unknown_observation_continues'] === false,
        'BACKUP was marked as running without a known role');
    echo "HA_VISIBILITY_BACKUP=PASS\n";

    $result = status_case($noCarp);
    check($result['role'] === 'none', 'non-HA role not represented as none');
    check($result['mode'] === 'none', 'non-HA effective mode changed');
    check($result['ha_status'] === 'non_ha', 'non-HA status not returned');
    check($result['observing'] === true, 'non-HA observation unexpectedly paused');
    check($result['paused_activities'] === [], 'non-HA returned paused activities');
    check($result['override_active'] === false, 'non-HA marked override active');
    check($result['appliance_carp_state'] === 'absent',
        'positive non-HA did not report appliance-wide CARP absence');
    check($result['appliance_non_ha_confirmed'] === true,
        'positive non-HA did not retain its appliance proof');
    check($result['carp_vip_count'] === 0, 'positive non-HA reported a CARP VIP');
    check($result['carp_runtime_present'] === false,
        'positive non-HA reported a runtime CARP state');
    check($result['monitoring_scope_ready'] === true,
        'selected monitored interfaces were not marked ready');
    check($result['monitoring_scope_reason'] === 'ready',
        'selected monitored interfaces returned an imprecise scope reason');
    check($result['monitoring_roles_known'] === true,
        'selected monitored interface roles were not marked known');
    check($result['non_ha_confirmation'] === 'appliance_non_ha',
        'positive non-HA did not return a confirmed reason');
    check($result['non_ha_confirmed'] === true, 'positive non-HA not confirmed');
    check($result['ha_relevant'] === false, 'positive non-HA retained HA relevance');
    echo "HA_VISIBILITY_NON_HA=PASS\n";

    $result = status_case($noCarp, 0, ['ha_role_override' => 'master']);
    check($result['role'] === 'none', 'non-HA override changed detected role');
    check($result['mode'] === 'MASTER', 'non-HA master override lost effective mode');
    check($result['override_active'] === true, 'non-HA override not marked active');
    check($result['non_ha_confirmed'] === false, 'active override hid HA relevance');
    check($result['ha_relevant'] === true, 'active override did not retain HA relevance');
    echo "HA_VISIBILITY_NON_HA_OVERRIDE=PASS\n";

    $result = status_case($noCarp, 0, [
        'ha_carp_enabled' => '0',
    ]);
    check($result['carp_aware'] === false, 'non-HA awareness-off flag missing');
    check($result['non_ha_confirmed'] === true, 'awareness-off non-HA not confirmed');
    check($result['ha_relevant'] === false, 'awareness-off non-HA retained HA relevance');
    echo "HA_VISIBILITY_NON_HA_AWARENESS_OFF=PASS\n";

    $result = status_case([], 1);
    check($result['role_available'] === false, 'unavailable ifconfig marked available');
    check($result['ha_status'] === 'unavailable', 'unavailable status not returned');
    check($result['mode'] === 'none', 'unavailable auto mode should remain none');
    check($result['paused_activities'] === [], 'unavailable role invented paused activities');
    check($result['non_ha_confirmed'] === false, 'detector failure was marked non-HA');
    check($result['ha_relevant'] === true, 'detector failure hid HA relevance');
    check($result['appliance_carp_state'] === 'unknown',
        'detector failure was presented as a known appliance CARP state');
    check($result['appliance_non_ha_confirmed'] === false,
        'detector failure was presented as appliance-wide non-HA');
    check($result['role_unknown_observation_continues'] === true,
        'unavailable CARP observation was not identified from backend state');
    echo "HA_VISIBILITY_UNAVAILABLE=PASS\n";

    $result = status_case($master, 0, [], '<broken');
    check($result['config_available'] === false, 'unreadable config marked available');
    check($result['role_available'] === false, 'role marked available without config mapping');
    check($result['ha_status'] === 'unavailable', 'unreadable config reported as non-HA');
    check($result['non_ha_confirmed'] === false, 'unreadable config was confirmed non-HA');
    check($result['ha_relevant'] === true, 'unreadable config hid HA relevance');
    check($result['role_unknown_observation_continues'] === false,
        'unreadable config was presented as confirmed observation policy');
    echo "HA_VISIBILITY_CONFIG_UNAVAILABLE=PASS\n";

    $result = status_case($noCarp, 0, [
        'monitored_interfaces' => '',
    ], '<broken');
    check($result['config_available'] === false, 'empty-scope unreadable config marked available');
    check($result['ha_status'] === 'unavailable',
        'empty-scope unreadable config was reported as non-HA');
    check($result['appliance_carp_state'] === 'unknown',
        'empty-scope unreadable config established appliance CARP absence');
    check($result['non_ha_confirmed'] === false,
        'empty-scope unreadable config confirmed non-HA');
    echo "HA_VISIBILITY_CONFIG_UNAVAILABLE_EMPTY_SCOPE=PASS\n";

    $liveXml = <<<XML
<opnsense>
  <system><timezone>Australia/Sydney</timezone></system>
  <interfaces>
    <lo0><if>lo0</if></lo0>
    <lan><if>re0</if></lan>
    <wan><if>iwm0_wlan0</if></wan>
    <opt1><if>vlan0.50</if></opt1>
  </interfaces>
</opnsense>
XML;
    $result = status_case($liveNoCarp, 0, [
        'monitored_interfaces' => '',
        'enabled' => '0',
    ], $liveXml);
    check($result['ha_status'] === 'non_ha', 'no monitored interface lost detector status');
    check($result['role'] === 'none' && $result['mode'] === 'none',
        'no monitored interface changed the detector output');
    check($result['appliance_carp_state'] === 'absent',
        'actual .23 shape did not prove appliance-wide CARP absence');
    check($result['appliance_non_ha_confirmed'] === true,
        'actual .23 appliance proof was not retained');
    check($result['monitoring_scope_ready'] === false,
        'actual .23 empty monitored selection was marked ready');
    check($result['monitoring_scope_reason'] === 'no_monitored_interfaces',
        'actual .23 empty monitored selection returned an imprecise reason');
    check($result['monitoring_roles_known'] === false,
        'actual .23 empty monitored selection was marked role-known');
    check($result['non_ha_confirmation'] === 'appliance_non_ha',
        'actual .23 shape returned an imprecise confirmation reason');
    check($result['non_ha_confirmed'] === true,
        'actual .23 appliance-wide CARP absence was not confirmed');
    check($result['ha_relevant'] === false,
        'actual .23 appliance-wide CARP absence retained HA relevance');
    check($result['monitoring_enabled'] === false,
        'disabled monitoring was not retained with no monitored interface');
    echo "HA_VISIBILITY_LIVE_APPLIANCE_NON_HA=PASS\n";

    $result = status_case($noCarp, 0, [
        'monitored_interfaces' => 'wan',
    ]);
    check($result['monitoring_scope_ready'] === false,
        'unresolved monitored interface was marked ready');
    check($result['monitoring_scope_reason'] === 'unresolved_monitored_interfaces',
        'unresolved monitored interface returned an imprecise scope reason');
    check($result['monitoring_roles_known'] === false,
        'unresolved monitored interface roles were marked known');
    check($result['non_ha_confirmed'] === true,
        'appliance-wide CARP absence was masked by an unresolved monitored selection');
    echo "HA_VISIBILITY_UNRESOLVED_MONITORED_INTERFACE=PASS\n";

    $result = status_case($noCarp, 0, [
        'monitored_interfaces' => '',
        'ha_role_override' => 'master',
    ], $liveXml);
    check($result['override_active'] === true, 'empty-scope override was not marked active');
    check($result['mode'] === 'MASTER', 'empty-scope override lost effective mode');
    check($result['ha_status'] === 'master', 'empty-scope override lost effective status');
    check($result['appliance_carp_state'] === 'absent',
        'empty-scope override changed appliance-wide CARP evidence');
    check($result['non_ha_confirmed'] === false,
        'empty-scope override was presented as non-HA');
    check($result['ha_relevant'] === true,
        'empty-scope override hid HA relevance');
    echo "HA_VISIBILITY_EMPTY_SCOPE_OVERRIDE=PASS\n";

    $carpVipXml = <<<XML
<opnsense>
  <interfaces>
    <lan><if>re0</if></lan>
    <opt1><if>re1</if></opt1>
  </interfaces>
  <virtualip>
    <vip><mode>carp</mode><interface>lan</interface><vhid>1</vhid><subnet>192.0.2.1</subnet></vip>
  </virtualip>
</opnsense>
XML;
    $result = status_case($noCarp, 0, [], $carpVipXml);
    check($result['non_ha_confirmation'] === 'carp_vip_configured',
        'configured CARP VIP returned an imprecise confirmation reason');
    check($result['non_ha_confirmed'] === false,
        'configured CARP VIP was treated as no CARP configuration');
    check($result['ha_relevant'] === true,
        'configured CARP VIP hid HA relevance');
    echo "HA_VISIBILITY_CARP_CONFIGURED=PASS\n";

    $result = status_case($noCarp, 0, [
        'monitored_interfaces' => '',
    ], $carpVipXml);
    check($result['appliance_carp_state'] === 'present',
        'configured CARP VIP was not reported at appliance scope');
    check($result['carp_vip_count'] === 1,
        'configured CARP VIP count was not reported');
    check($result['monitoring_scope_ready'] === false,
        'CARP with empty monitoring scope was marked ready');
    check($result['monitoring_scope_reason'] === 'no_monitored_interfaces',
        'CARP with empty monitoring scope returned an imprecise scope reason');
    check($result['non_ha_confirmation'] === 'carp_present_no_monitored_interfaces',
        'CARP with empty monitoring scope did not return a scope-specific reason');
    check($result['non_ha_confirmed'] === false,
        'CARP with empty monitoring scope was confirmed non-HA');
    check($result['ha_relevant'] === true,
        'CARP with empty monitoring scope hid HA relevance');
    echo "HA_VISIBILITY_CARP_CONFIGURED_EMPTY_SCOPE=PASS\n";

    $result = status_case($initCarp, 0, [
        'monitored_interfaces' => '',
    ], $liveXml);
    check($result['role'] === 'none',
        'CARP INIT was incorrectly promoted to an observing role');
    check($result['carp_runtime_present'] === true,
        'CARP INIT was not recognized as runtime CARP presence');
    check($result['appliance_carp_state'] === 'present',
        'CARP INIT was presented as appliance-wide CARP absence');
    check($result['non_ha_confirmation'] === 'carp_present_no_monitored_interfaces',
        'CARP INIT with empty scope returned an imprecise reason');
    check($result['non_ha_confirmed'] === false,
        'CARP INIT with empty scope was confirmed non-HA');
    echo "HA_VISIBILITY_CARP_INIT_EMPTY_SCOPE=PASS\n";

    $result = status_case($mixed);
    check($result['role'] === 'MASTER', 'mixed role must retain daemon MASTER precedence');
    check($result['role_mixed'] === true, 'mixed CARP role not flagged');
    check($result['mode'] === 'MASTER', 'mixed effective mode should be MASTER');
    check($result['observing'] === true, 'mixed MASTER state should observe');
    check($result['paused_activities'] === [], 'mixed MASTER state returned paused activities');
    echo "HA_VISIBILITY_MIXED=PASS\n";

    $result = status_case($backup, 0, [
        'ha_role_override' => 'master',
    ]);
    check($result['role'] === 'BACKUP', 'override changed detected role');
    check($result['mode'] === 'MASTER', 'master override did not change effective mode');
    check($result['ha_status'] === 'master', 'master override status incorrect');
    check($result['observing'] === true, 'master override observation incorrect');
    check($result['paused_activities'] === [], 'master override returned paused activities');
    echo "HA_VISIBILITY_OVERRIDE_MASTER=PASS\n";

    $result = status_case($backup, 0, [
        'ha_role_override' => 'backup',
    ]);
    check($result['role'] === 'BACKUP', 'backup override changed detected role');
    check($result['mode'] === 'BACKUP', 'backup override effective mode incorrect');
    check($result['ha_status'] === 'backup', 'backup override status incorrect');
    check($result['paused_activities'] === $paused, 'backup override did not pause exact activities');
    echo "HA_VISIBILITY_OVERRIDE_BACKUP=PASS\n";

    $result = status_case($backup, 0, [
        'ha_carp_enabled' => '0',
    ]);
    check($result['role'] === 'BACKUP', 'awareness-off changed detected role');
    check($result['mode'] === 'BACKUP', 'awareness-off changed effective mode');
    check($result['carp_aware'] === false, 'awareness-off flag not returned');
    check($result['ha_status'] === 'backup', 'awareness-off status should remain BACKUP');
    check($result['observing'] === true, 'awareness-off incorrectly paused observation');
    check($result['paused_activities'] === [], 'awareness-off incorrectly paused activities');
    check($result['non_ha_confirmed'] === false, 'awareness-off BACKUP marked non-HA');
    check($result['ha_relevant'] === true, 'awareness-off BACKUP hid HA relevance');
    echo "HA_VISIBILITY_AWARENESS_OFF=PASS\n";

    $result = status_case([], 1, [
        'ha_carp_enabled' => '0',
    ]);
    check($result['role_available'] === false, 'awareness-off hid unavailable detector state');
    check($result['ha_status'] === 'unavailable', 'awareness-off unavailable status lost');
    check($result['observing'] === true, 'awareness-off unavailable paused observation');
    check($result['paused_activities'] === [], 'awareness-off unavailable paused activities');
    check($result['role_unknown_observation_continues'] === false,
        'awareness-off was marked as fail-open observation');
    echo "HA_VISIBILITY_AWARENESS_OFF_UNAVAILABLE=PASS\n";

    $result = status_case([], 1, [
        'ha_role_override' => 'backup',
    ]);
    check($result['role_available'] === false, 'override hid unavailable detector state');
    check($result['mode'] === 'BACKUP', 'override backup effective mode lost');
    check($result['ha_status'] === 'backup', 'override backup status lost');
    check($result['paused_activities'] === $paused, 'override backup lost paused activities');
    check($result['role_unknown_observation_continues'] === false,
        'backup override was marked as observation without a policy');
    echo "HA_VISIBILITY_OVERRIDE_UNAVAILABLE=PASS\n";

    $reflection = new \ReflectionClass(ConfigController::class);
    $lastScan = $reflection->getMethod('lastSuccessfulLocalScan');
    $lastScan->setAccessible(true);
    $controller = $reflection->newInstanceWithoutConstructor();

    $log = tempnam(sys_get_temp_dir(), 'dm-ha-log-');
    file_put_contents(
        $log,
        "[2026-01-01 10:00:00] Scan completed successfully\n"
        . "[2026-01-01 10:05:00] Scan failed with code 1\n"
        . "[2026-01-02 11:22:33] Scan completed successfully\n"
    );
    $scan = $lastScan->invoke($controller, $log);
    check(
        $scan['state'] === 'found' && $scan['value'] === '2026-01-02 11:22:33',
        'last successful scan did not select the latest success line'
    );
    file_put_contents($log, "[2026-01-02 11:22:33] Scan failed with code 1\n");
    $scan = $lastScan->invoke($controller, $log);
    check(
        $scan['state'] === 'none' && $scan['value'] === '',
        'failed scan was reported as a successful history entry'
    );
    file_put_contents(
        $log,
        "[2026-01-03 09:00:00] Scan completed successfully\n"
        . str_repeat("[2026-01-03 09:01:00] unrelated log line\n", 5000)
    );
    $scan = $lastScan->invoke($controller, $log);
    check(
        $scan['state'] === 'found' && $scan['value'] === '2026-01-03 09:00:00',
        'success outside the tail window was not found'
    );
    unlink($log);
    $scan = $lastScan->invoke($controller, $log);
    check(
        $scan['state'] === 'unavailable' && $scan['value'] === '',
        'missing scan log was not distinguished from readable history'
    );
    echo "HA_VISIBILITY_LAST_SCAN=PASS\n";

    echo "HA_ROLE_VISIBILITY=PASS cases=23\n";
}
