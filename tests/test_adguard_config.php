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

        $GLOBALS['dm_adguard_stub_model'] = true;
    } else {
        $GLOBALS['dm_adguard_stub_model'] = false;
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
        $controller =
            new \OPNsense\DeviceMonitor\Api\ConfigController();

        $controller->request = new FakeRequest($values);

        return $controller->setAction();
    }

    $result = run_config_case([
        'adguard_rewrite_enabled' => '1',
        'adguard_url' => 'http://192.0.2.53',
        'adguard_username' => 'admin',
        'adguard_password' => 'secret',
    ]);

    expect_true($result['result'] === 'failed', 'Expected failed result');
    expect_true(
        $result['message'] === 'AdGuard URL must use HTTPS',
        'HTTP URL was not rejected'
    );

    echo "ADGUARD_HTTP_URL_REJECTED=PASS\n";

    $result = run_config_case([
        'adguard_rewrite_enabled' => '1',
        'adguard_url' => 'https://192.0.2.53',
        'adguard_username' => '',
        'adguard_password' => 'secret',
    ]);

    expect_true($result['result'] === 'failed', 'Expected failed result');
    expect_true(
        $result['message'] === 'AdGuard username must not be empty',
        'Missing username was not rejected'
    );

    echo "ADGUARD_MISSING_USERNAME_REJECTED=PASS\n";

    $result = run_config_case([
        'adguard_rewrite_enabled' => '1',
        'adguard_url' => 'https://192.0.2.53',
        'adguard_username' => 'admin',
        'adguard_password' => '',
    ]);

    expect_true($result['result'] === 'failed', 'Expected failed result');
    expect_true(
        $result['message'] === 'AdGuard password must not be empty',
        'Missing password was not rejected'
    );

    echo "ADGUARD_MISSING_PASSWORD_REJECTED=PASS\n";

    $invalid_urls = [
        'https://user:pass@192.0.2.53',
        'https://192.0.2.53?test=1',
        'https://192.0.2.53#fragment',
    ];

    foreach ($invalid_urls as $invalid_url) {
        $result = run_config_case([
            'adguard_rewrite_enabled' => '1',
            'adguard_url' => $invalid_url,
            'adguard_username' => 'admin',
            'adguard_password' => 'secret',
        ]);

        expect_true($result['result'] === 'failed', 'Expected failed result');
        expect_true(
            $result['message']
            === 'AdGuard URL must not contain credentials, query or fragment',
            'Unsafe AdGuard URL was not rejected'
        );
    }

    echo "ADGUARD_UNSAFE_URL_COMPONENTS_REJECTED=PASS\n";
    if ($GLOBALS['dm_adguard_stub_model']) {
        \OPNsense\DeviceMonitor\DeviceMonitor::$savedConfig = null;

        $result = run_config_case([
            'adguard_rewrite_enabled' => '1',
            'adguard_url' => 'https://192.0.2.53/',
            'adguard_username' => 'admin',
            'adguard_password' => 'secret',
        ]);

        expect_true(
            $result['result'] === 'saved',
            'Valid AdGuard config was not saved'
        );

        $saved =
            \OPNsense\DeviceMonitor\DeviceMonitor::$savedConfig;

        expect_true(
            $saved['adguard_rewrite_enabled'] === '1',
            'Enabled value not saved'
        );
        expect_true(
            $saved['adguard_url'] === 'https://192.0.2.53/',
            'URL not saved'
        );
        expect_true(
            $saved['adguard_username'] === 'admin',
            'Username not saved'
        );
        expect_true(
            $saved['adguard_password'] === 'secret',
            'Password not saved'
        );

        echo "ADGUARD_VALID_CONFIG_SAVED=PASS\n";
    } else {
        echo "ADGUARD_VALID_CONFIG_SAVED=SKIP_REAL_MODEL\n";
    }

    echo "ADGUARD_CONFIG_REGRESSION=PASS\n";
}
