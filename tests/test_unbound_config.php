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

    require_once __DIR__
        . '/../src/opnsense/mvc/app/controllers/OPNsense/'
        . 'DeviceMonitor/Api/ConfigController.php';
}

namespace OPNsense\DeviceMonitor {
    if (!class_exists(DeviceMonitor::class, false)) {
        class DeviceMonitor
        {
            public static $savedConfig = null;

            public function getConfig()
            {
                return [];
            }

            public function setConfig($config)
            {
                self::$savedConfig = $config;
                return true;
            }
        }

        $GLOBALS['dm_unbound_stub_model'] = true;
    } else {
        $GLOBALS['dm_unbound_stub_model'] = false;
    }
}

namespace {
    function expect_true($condition, $message)
    {
        if (!$condition) {
            throw new \RuntimeException($message);
        }
    }

    function run_config_case(array $values)
    {
        $controller = new \OPNsense\DeviceMonitor\Api\ConfigController();
        $controller->request = new FakeRequest($values);
        return $controller->setAction();
    }

    // Only "0" and "1" are accepted for the Unbound opt-in flag.
    foreach (['2', 'true', 'on', 'yes', ''] as $bad_value) {
        $result = run_config_case(['unbound_enabled' => $bad_value]);
        expect_true(
            $result['result'] === 'failed',
            'Invalid Unbound value accepted: ' . var_export($bad_value, true)
        );
        expect_true(
            $result['message'] === 'Invalid Unbound enabled value',
            'Wrong message for invalid Unbound value'
        );
    }
    echo "UNBOUND_ENABLED_BOOLEAN_ONLY=PASS\n";

    if ($GLOBALS['dm_unbound_stub_model']) {
        \OPNsense\DeviceMonitor\DeviceMonitor::$savedConfig = null;

        $result = run_config_case(['unbound_enabled' => '1']);
        expect_true($result['result'] === 'saved', 'unbound_enabled=1 not saved');
        expect_true(
            \OPNsense\DeviceMonitor\DeviceMonitor::$savedConfig['unbound_enabled'] === '1',
            'Enabled value not saved'
        );
        echo "UNBOUND_ENABLED_ONE_SAVED=PASS\n";

        \OPNsense\DeviceMonitor\DeviceMonitor::$savedConfig = null;

        $result = run_config_case(['unbound_enabled' => '0']);
        expect_true($result['result'] === 'saved', 'unbound_enabled=0 not saved');
        expect_true(
            \OPNsense\DeviceMonitor\DeviceMonitor::$savedConfig['unbound_enabled'] === '0',
            'Disabled value not saved'
        );
        echo "UNBOUND_ENABLED_ZERO_SAVED=PASS\n";
    } else {
        echo "UNBOUND_ENABLED_ONE_SAVED=SKIP_REAL_MODEL\n";
        echo "UNBOUND_ENABLED_ZERO_SAVED=SKIP_REAL_MODEL\n";
    }

    echo "UNBOUND_CONFIG_REGRESSION=PASS\n";
}
