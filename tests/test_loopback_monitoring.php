<?php

namespace OPNsense\Base {
    class ApiControllerBase
    {
        public $request;
    }
}

namespace {
    class FakeRequest
    {
        private $data;

        public function __construct(array $data)
        {
            $this->data = $data;
        }

        public function isPost()
        {
            return true;
        }

        public function getPost($name, $filter = null, $default = null)
        {
            return array_key_exists($name, $this->data)
                ? $this->data[$name]
                : $default;
        }
    }
}

namespace OPNsense\DeviceMonitor\Api {
    // Mock simplexml_load_file so the test never depends on a live
    // /conf/config.xml.
    function simplexml_load_file($path)
    {
        $xml = <<<XML
<opnsense>
  <interfaces>
    <lo0><enable>1</enable><if>lo0</if><ipaddr>127.0.0.1</ipaddr><subnet>8</subnet><descr>Loopback</descr></lo0>
    <loopback_test><enable>1</enable><if>lo1</if><ipaddr>127.0.0.1</ipaddr><subnet>8</subnet><descr>Loopback test</descr></loopback_test>
    <opt1><enable>1</enable><if>vlan0.50</if><ipaddr>192.168.50.1</ipaddr><subnet>24</subnet><descr>DMTEST</descr></opt1>
    <lan><enable>1</enable><if>re0</if><ipaddr>192.168.20.23</ipaddr><subnet>24</subnet><descr>LAN</descr></lan>
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
    // Only provide a stub when the real model was not already loaded through
    // the real NotificationHandler (i.e. on a testbed the real model wins).
    if (!class_exists(DeviceMonitor::class, false)) {
        class DeviceMonitor
        {
            public function getConfig()
            {
                return [];
            }

            public function setConfig($config)
            {
                return true;
            }
        }
    }
}

namespace {
    function expect_true($condition, $message)
    {
        if (!$condition) {
            throw new \RuntimeException($message);
        }
    }

    // The selector must not offer loopback, but must keep LAN and opt1.
    $controller = new \OPNsense\DeviceMonitor\Api\ConfigController();
    $controller->request = new FakeRequest([]);
    $result = $controller->getmonitoredinterfacesAction();

    expect_true(!array_key_exists('lo0', $result), 'lo0 must be absent from selector');
    expect_true(
        !array_key_exists('loopback_test', $result),
        'loopback by address must be absent from selector'
    );
    expect_true(array_key_exists('opt1', $result), 'opt1 must be present in selector');
    expect_true(array_key_exists('lan', $result), 'lan must be present in selector');

    echo "LOOPBACK_SELECTOR_ABSENT=PASS\n";

    // Save validation must reject loopback (crafted API request).
    $controller->request = new FakeRequest(['monitored_interfaces' => 'lo0']);
    $result = $controller->setAction();
    expect_true($result['result'] === 'failed', 'lo0 must be rejected by save validation');
    expect_true(
        strpos($result['message'], 'loopback') !== false,
        'loopback rejection message must mention loopback'
    );

    echo "LOOPBACK_SAVE_REJECTED=PASS\n";

    // A loopback address under a non-lo0 name must also be rejected.
    $controller->request = new FakeRequest(['monitored_interfaces' => 'loopback_test']);
    $result = $controller->setAction();
    expect_true($result['result'] === 'failed', 'loopback by address must be rejected');
    expect_true(
        strpos($result['message'], 'loopback') !== false,
        'loopback-by-address rejection message must mention loopback'
    );

    echo "LOOPBACK_SAVE_BY_ADDRESS_REJECTED=PASS\n";

    echo "LOOPBACK_MONITORING_REGRESSION=PASS\n";
}
