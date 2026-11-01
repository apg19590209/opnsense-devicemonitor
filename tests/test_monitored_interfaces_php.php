<?php

/**
 * The uplink must never be selectable as a monitored interface (Decision 51).
 *
 * The daemon refuses it in resolve_monitored_networks(); the controller mirrors
 * the same rule so the picker cannot offer it and a stale form post cannot save
 * it. This pins the controller half:
 *
 *   - `wan` is refused by name, whatever its address;
 *   - an interface carrying a gateway on a non-RFC1918 address is refused;
 *   - a gateway on private space (policy routing) stays selectable;
 *   - a public segment with no gateway (DMZ) stays selectable.
 *
 * simplexml_load_file() is overridden in the controller's namespace, so no live
 * /conf/config.xml is read and nothing on the host is touched. A gateway here
 * is configuration data only: no link is configured, raised or brought down.
 */

namespace OPNsense\Base {
    class ApiControllerBase
    {
        public $request;
    }
}

namespace OPNsense\DeviceMonitor\Api {
    function simplexml_load_file($path)
    {
        $xml = <<<XML
<opnsense>
  <interfaces>
    <lan><enable>1</enable><if>re0</if><ipaddr>192.168.20.23</ipaddr><subnet>24</subnet><descr>LAN</descr></lan>
    <wan><enable>1</enable><if>em0</if><ipaddr>203.0.113.10</ipaddr><subnet>24</subnet><descr>WAN</descr></wan>
    <opt3><enable>1</enable><if>em1</if><ipaddr>198.51.100.2</ipaddr><subnet>24</subnet><descr>UPLINK2</descr><gateway>WAN2_GW</gateway></opt3>
    <opt4><enable>1</enable><if>em2</if><ipaddr>10.10.10.1</ipaddr><subnet>24</subnet><descr>POLICYROUTE</descr><gateway>LAN_GW</gateway></opt4>
    <opt5><enable>1</enable><if>em3</if><ipaddr>192.0.2.50</ipaddr><subnet>24</subnet><descr>DMZ</descr></opt5>
  </interfaces>
</opnsense>
XML;
        return \simplexml_load_string($xml);
    }
}

namespace {
    require_once __DIR__
        . '/../src/opnsense/mvc/app/controllers/OPNsense/'
        . 'DeviceMonitor/Api/ConfigController.php';
}

namespace OPNsense\DeviceMonitor {
    if (!class_exists('OPNsense\DeviceMonitor\DeviceMonitor', false)) {
        class DeviceMonitor
        {
        }
    }
}

namespace {
    $reflection = new \ReflectionClass(
        \OPNsense\DeviceMonitor\Api\ConfigController::class
    );
    $controller = $reflection->newInstanceWithoutConstructor();

    $uplink = $reflection->getMethod('isUplinkInterface');
    $uplink->setAccessible(true);

    $xml = \simplexml_load_string(
        '<ifs>'
        . '<wan></wan>'
        . '<opt3><gateway>WAN2_GW</gateway></opt3>'
        . '<opt4><gateway>LAN_GW</gateway></opt4>'
        . '<opt5></opt5>'
        . '</ifs>'
    );

    $cases = [
        ['wan', $xml->wan, '203.0.113.10', true],
        ['opt3', $xml->opt3, '198.51.100.2', true],
        ['opt4', $xml->opt4, '10.10.10.1', false],
        ['wan', $xml->wan, '192.168.20.23', true],
        ['opt5', $xml->opt5, '192.0.2.50', false],
    ];

    foreach ($cases as [$name, $node, $ip, $expected]) {
        $actual = $uplink->invoke($controller, $name, $node, $ip);

        if ($actual !== $expected) {
            fwrite(
                STDERR,
                sprintf(
                    "FAIL: isUplinkInterface(%s, %s) returned %s, expected %s\n",
                    $name,
                    $ip,
                    var_export($actual, true),
                    var_export($expected, true)
                )
            );
            exit(1);
        }
    }

    echo "MONITORED_PHP_UPLINK_RULE=PASS\n";

    $picker = $controller->getmonitoredinterfacesAction();
    $offered = array_keys($picker);
    sort($offered);

    $expected_offered = ['lan', 'opt4', 'opt5'];
    sort($expected_offered);

    if ($offered !== $expected_offered) {
        fwrite(
            STDERR,
            'FAIL: picker offered ' . json_encode($offered)
            . ' expected ' . json_encode($expected_offered) . "\n"
        );
        exit(1);
    }

    echo "MONITORED_PHP_PICKER=PASS\n";
    echo "MONITORED_INTERFACES_PHP=PASS\n";
}
