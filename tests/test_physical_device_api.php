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
        public static $calls = [];
        public static $physicalDevice = null;
        public static $createResult = 0;
        public static $linkResult = false;
        public static $removeResult = false;

        public static function reset()
        {
            self::$calls = [];
            self::$physicalDevice = null;
            self::$createResult = 0;
            self::$linkResult = false;
            self::$removeResult = false;
        }

        public function getPhysicalDeviceForMac($mac)
        {
            self::$calls[] = ['get', $mac];
            return self::$physicalDevice;
        }

        public function createPhysicalDevice($name, $mac)
        {
            self::$calls[] = ['create', $name, $mac];
            return self::$createResult;
        }

        public function linkPhysicalDeviceIdentity($physicalDeviceId, $mac)
        {
            self::$calls[] = ['link', $physicalDeviceId, $mac];
            return self::$linkResult;
        }

        public function removePhysicalDeviceIdentity($physicalDeviceId, $mac)
        {
            self::$calls[] = ['remove', $physicalDeviceId, $mac];
            return self::$removeResult;
        }
    }
}

namespace {
    use OPNsense\DeviceMonitor\DeviceMonitor;

    class FakeRequest
    {
        private $post;
        private $postData;
        private $getData;

        public function __construct($post = false, $postData = [], $getData = [])
        {
            $this->post = $post;
            $this->postData = $postData;
            $this->getData = $getData;
        }

        public function isPost()
        {
            return $this->post;
        }

        public function getPost($key, $filter = null, $default = null)
        {
            return array_key_exists($key, $this->postData)
                ? $this->postData[$key]
                : $default;
        }

        public function get($key, $filter = null, $default = null)
        {
            return array_key_exists($key, $this->getData)
                ? $this->getData[$key]
                : $default;
        }
    }

    function check($ok, $message)
    {
        if (!$ok) {
            throw new \RuntimeException($message);
        }
    }

    $controllerPath = getenv('DM_DEVICES_CONTROLLER_PATH');
    if (!$controllerPath) {
        $controllerPath =
            __DIR__ .
            '/../src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/' .
            'DevicesController.php';
    }

    require_once $controllerPath;

    function controller_with($request)
    {
        $controller =
            new \OPNsense\DeviceMonitor\Api\DevicesController();
        $controller->request = $request;
        return $controller;
    }

    DeviceMonitor::reset();

    $response = controller_with(
        new FakeRequest(false, [], ['mac' => 'not-a-mac'])
    )->physicaldeviceAction();

    check(
        $response['result'] === 'failed' &&
        DeviceMonitor::$calls === [],
        'Physical-device read accepted an invalid MAC'
    );

    DeviceMonitor::$physicalDevice = [
        'id' => 7,
        'name' => 'Test Laptop',
        'members' => [
            ['mac' => 'aa:bb:cc:dd:ee:01']
        ]
    ];

    $response = controller_with(
        new FakeRequest(
            false,
            [],
            ['mac' => ' AA:BB:CC:DD:EE:01 ']
        )
    )->physicaldeviceAction();

    check(
        $response['result'] === 'ok' &&
        $response['mac'] === 'aa:bb:cc:dd:ee:01' &&
        $response['physical_device']['id'] === 7 &&
        DeviceMonitor::$calls === [
            ['get', 'aa:bb:cc:dd:ee:01']
        ],
        'Physical-device read action did not normalize/delegate correctly'
    );

    DeviceMonitor::reset();

    $response = controller_with(
        new FakeRequest(
            true,
            ['name' => '   ', 'mac' => 'aa:bb:cc:dd:ee:01']
        )
    )->createphysicaldeviceAction();

    check(
        $response['result'] === 'failed' &&
        DeviceMonitor::$calls === [],
        'Create action accepted an empty physical-device name'
    );

    $response = controller_with(
        new FakeRequest(
            false,
            ['name' => 'Laptop', 'mac' => 'aa:bb:cc:dd:ee:01']
        )
    )->createphysicaldeviceAction();

    check(
        $response['result'] === 'failed' &&
        DeviceMonitor::$calls === [],
        'Create action accepted a non-POST request'
    );

    DeviceMonitor::$createResult = 12;

    $response = controller_with(
        new FakeRequest(
            true,
            [
                'name' => ' Test Laptop ',
                'mac' => ' AA:BB:CC:DD:EE:01 '
            ]
        )
    )->createphysicaldeviceAction();

    check(
        $response['result'] === 'saved' &&
        $response['physical_device_id'] === 12 &&
        DeviceMonitor::$calls === [
            ['create', 'Test Laptop', 'aa:bb:cc:dd:ee:01']
        ],
        'Create action did not normalize/delegate correctly'
    );

    DeviceMonitor::reset();

    $response = controller_with(
        new FakeRequest(
            true,
            ['physical_device_id' => 0, 'mac' => 'aa:bb:cc:dd:ee:02']
        )
    )->linkphysicaldeviceidentityAction();

    check(
        $response['result'] === 'failed' &&
        DeviceMonitor::$calls === [],
        'Link action accepted an invalid physical-device ID'
    );

    DeviceMonitor::$linkResult = true;

    $response = controller_with(
        new FakeRequest(
            true,
            [
                'physical_device_id' => '12',
                'mac' => ' AA:BB:CC:DD:EE:02 '
            ]
        )
    )->linkphysicaldeviceidentityAction();

    check(
        $response['result'] === 'saved' &&
        DeviceMonitor::$calls === [
            ['link', 12, 'aa:bb:cc:dd:ee:02']
        ],
        'Link action did not normalize/delegate correctly'
    );

    DeviceMonitor::reset();
    DeviceMonitor::$removeResult = true;

    $response = controller_with(
        new FakeRequest(
            true,
            [
                'physical_device_id' => '12',
                'mac' => ' AA:BB:CC:DD:EE:02 '
            ]
        )
    )->removephysicaldeviceidentityAction();

    check(
        $response['result'] === 'removed' &&
        DeviceMonitor::$calls === [
            ['remove', 12, 'aa:bb:cc:dd:ee:02']
        ],
        'Remove action did not normalize/delegate correctly'
    );

    DeviceMonitor::reset();

    $response = controller_with(
        new FakeRequest(
            true,
            [
                'physical_device_id' => '12',
                'mac' => 'invalid'
            ]
        )
    )->removephysicaldeviceidentityAction();

    check(
        $response['result'] === 'failed' &&
        DeviceMonitor::$calls === [],
        'Remove action accepted an invalid MAC'
    );

    echo "DEVICE_PHYSICAL_GROUP_API=PASS\n";
}
