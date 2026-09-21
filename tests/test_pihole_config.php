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

        $GLOBALS['dm_pihole_stub_model'] = true;
    } else {
        $GLOBALS['dm_pihole_stub_model'] = false;
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

    // Enabled accepts only the supported boolean values "0" and "1".
    $result = run_config_case(['pihole_enabled' => 'true']);
    expect_true($result['result'] === 'failed', 'Non-boolean enabled value accepted');
    expect_true(
        $result['message'] === 'Invalid Pi-hole enabled value',
        'Wrong message for invalid enabled value'
    );
    echo "PIHOLE_ENABLED_BOOLEAN_ONLY=PASS\n";

    // HTTP URL is rejected.
    $result = run_config_case([
        'pihole_enabled' => '1',
        'pihole_url' => 'http://192.0.2.53',
        'pihole_password' => 'secret',
    ]);
    expect_true($result['result'] === 'failed', 'HTTP URL was accepted');
    expect_true(
        $result['message'] === 'Pi-hole URL must use HTTPS',
        'HTTP URL was not rejected with the HTTPS message'
    );
    echo "PIHOLE_HTTP_URL_REJECTED=PASS\n";

    // Invalid URL is rejected.
    $result = run_config_case([
        'pihole_enabled' => '1',
        'pihole_url' => 'not-a-url',
        'pihole_password' => 'secret',
    ]);
    expect_true($result['result'] === 'failed', 'Invalid URL was accepted');
    expect_true(
        $result['message'] === 'Invalid Pi-hole URL',
        'Invalid URL was not rejected'
    );
    echo "PIHOLE_INVALID_URL_REJECTED=PASS\n";

    // Embedded credentials, query string and fragment are rejected.
    $unsafe_urls = [
        'https://user:pass@192.0.2.53',
        'https://192.0.2.53?test=1',
        'https://192.0.2.53#fragment',
    ];

    foreach ($unsafe_urls as $unsafe_url) {
        $result = run_config_case([
            'pihole_enabled' => '1',
            'pihole_url' => $unsafe_url,
            'pihole_password' => 'secret',
        ]);

        expect_true($result['result'] === 'failed', 'Unsafe URL was accepted');
        expect_true(
            $result['message']
            === 'Pi-hole URL must not contain credentials, query or fragment',
            'Unsafe Pi-hole URL was not rejected'
        );
    }
    echo "PIHOLE_UNSAFE_URL_COMPONENTS_REJECTED=PASS\n";

    // Empty app password is rejected when enabled.
    $result = run_config_case([
        'pihole_enabled' => '1',
        'pihole_url' => 'https://192.0.2.53',
        'pihole_password' => '',
    ]);
    expect_true($result['result'] === 'failed', 'Empty app password was accepted');
    expect_true(
        $result['message'] === 'Pi-hole app password must not be empty',
        'Empty app password was not rejected'
    );
    echo "PIHOLE_EMPTY_PASSWORD_REJECTED=PASS\n";

    if ($GLOBALS['dm_pihole_stub_model']) {
        \OPNsense\DeviceMonitor\DeviceMonitor::$savedConfig = null;

        // Valid HTTPS URL is accepted and persisted.
        $result = run_config_case([
            'pihole_enabled' => '1',
            'pihole_url' => 'https://192.0.2.53/',
            'pihole_password' => 'secret',
        ]);

        expect_true($result['result'] === 'saved', 'Valid Pi-hole config not saved');

        $saved = \OPNsense\DeviceMonitor\DeviceMonitor::$savedConfig;
        expect_true($saved['pihole_enabled'] === '1', 'Enabled value not saved');
        expect_true($saved['pihole_url'] === 'https://192.0.2.53/', 'URL not saved');
        expect_true($saved['pihole_password'] === 'secret', 'Password not saved');
        expect_true($saved['unbound_enabled'] === '0', 'Unbound default not applied');

        echo "PIHOLE_VALID_CONFIG_SAVED=PASS\n";

        // Disabled configuration is saved without any URL or password. The
        // controller performs no network I/O, so a disabled provider requires
        // no live Pi-hole access.
        \OPNsense\DeviceMonitor\DeviceMonitor::$savedConfig = null;

        $result = run_config_case(['pihole_enabled' => '0']);

        expect_true($result['result'] === 'saved', 'Disabled Pi-hole config not saved');

        $saved = \OPNsense\DeviceMonitor\DeviceMonitor::$savedConfig;
        expect_true($saved['pihole_enabled'] === '0', 'Disabled value not saved');
        expect_true($saved['pihole_url'] === '', 'URL should be empty when disabled');
        expect_true(
            $saved['pihole_password'] === '',
            'Password should be empty when disabled'
        );

        echo "PIHOLE_DISABLED_NO_PROVIDER_ACCESS=PASS\n";
    } else {
        echo "PIHOLE_VALID_CONFIG_SAVED=SKIP_REAL_MODEL\n";
        echo "PIHOLE_DISABLED_NO_PROVIDER_ACCESS=SKIP_REAL_MODEL\n";
    }

    echo "PIHOLE_CONFIG_REGRESSION=PASS\n";
}
