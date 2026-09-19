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
        public static $summary = [];
        public static $throwMessage = null;

        public static function reset()
        {
            self::$calls = [];
            self::$summary = [
                'start' => '',
                'end' => '',
                'category' => 'all',
                'limit' => 50,
                'offset' => 0,
                'total' => 0,
                'summary' => ['total' => 0],
                'events' => []
            ];
            self::$throwMessage = null;
        }

        public function getChangeSummary($start, $end, $category, $limit, $offset)
        {
            self::$calls[] = [$start, $end, $category, $limit, $offset];

            if (self::$throwMessage !== null) {
                throw new \InvalidArgumentException(self::$throwMessage);
            }

            return array_merge(self::$summary, [
                'start' => $start,
                'end' => $end,
                'category' => $category,
                'limit' => $limit,
                'offset' => $offset
            ]);
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

    /* Valid request: explicit custom range delegates exact values. */
    $response = controller_with(
        new FakeRequest(
            false,
            [],
            [
                'window' => 'custom',
                'start' => '2026-09-14 00:00:00',
                'end' => '2026-09-16 23:59:59',
                'category' => 'all',
                'limit' => 50,
                'offset' => 0
            ]
        )
    )->changesummaryAction();

    check(
        $response['result'] === 'ok' &&
        count(DeviceMonitor::$calls) === 1 &&
        DeviceMonitor::$calls[0][0] === '2026-09-14 00:00:00' &&
        DeviceMonitor::$calls[0][1] === '2026-09-16 23:59:59' &&
        DeviceMonitor::$calls[0][2] === 'all' &&
        DeviceMonitor::$calls[0][3] === 50 &&
        DeviceMonitor::$calls[0][4] === 0,
        'Custom-range delegation is wrong'
    );

    foreach (
        [
            'result',
            'start',
            'end',
            'category',
            'limit',
            'offset',
            'total',
            'summary',
            'events',
            'window'
        ] as $key
    ) {
        check(
            array_key_exists($key, $response),
            'Response missing key ' . $key
        );
    }

    DeviceMonitor::reset();

    /* Default window resolves server-side and delegates. */
    $response = controller_with(
        new FakeRequest(false, [], [])
    )->changesummaryAction();

    check(
        $response['result'] === 'ok' &&
        count(DeviceMonitor::$calls) === 1 &&
        DeviceMonitor::$calls[0][0] !== '' &&
        DeviceMonitor::$calls[0][1] !== '' &&
        DeviceMonitor::$calls[0][2] === 'all' &&
        DeviceMonitor::$calls[0][3] === 50 &&
        DeviceMonitor::$calls[0][4] === 0,
        'Default-window delegation is wrong'
    );

    DeviceMonitor::reset();

    /* Unknown category is rejected without calling the model. */
    $response = controller_with(
        new FakeRequest(false, [], ['category' => 'bogus'])
    )->changesummaryAction();

    check(
        $response['result'] === 'failed' &&
        isset($response['error']) &&
        DeviceMonitor::$calls === [],
        'Unknown category was not rejected cleanly'
    );

    DeviceMonitor::reset();

    /* Negative offset and out-of-range limits are clamped. */
    $response = controller_with(
        new FakeRequest(
            false,
            [],
            ['limit' => 0, 'offset' => -5, 'category' => 'device']
        )
    )->changesummaryAction();

    check(
        $response['result'] === 'ok' &&
        DeviceMonitor::$calls[0][3] === 1 &&
        DeviceMonitor::$calls[0][4] === 0 &&
        DeviceMonitor::$calls[0][2] === 'device',
        'Limit/offset clamping is wrong'
    );

    DeviceMonitor::reset();

    $response = controller_with(
        new FakeRequest(false, [], ['limit' => 9999, 'offset' => 0])
    )->changesummaryAction();

    check(
        $response['result'] === 'ok' &&
        DeviceMonitor::$calls[0][3] === 200,
        'Excessive limit was not bounded'
    );

    DeviceMonitor::reset();

    /* Model validation failures map to a failed response. */
    DeviceMonitor::$throwMessage = 'Date range must not exceed 90 days';

    $response = controller_with(
        new FakeRequest(
            false,
            [],
            [
                'window' => 'custom',
                'start' => '2026-01-01 00:00:00',
                'end' => '2026-06-01 00:00:00'
            ]
        )
    )->changesummaryAction();

    check(
        $response['result'] === 'failed' &&
        $response['error'] === 'Date range must not exceed 90 days',
        'Model validation failure was not mapped to a failed response'
    );

    DeviceMonitor::reset();

    /* Empty response shape. */
    $response = controller_with(
        new FakeRequest(false, [], [])
    )->changesummaryAction();

    check(
        $response['result'] === 'ok' &&
        $response['total'] === 0 &&
        $response['events'] === [],
        'Empty response shape is wrong'
    );

    echo "DEVICE_CHANGE_SUMMARY_API=PASS\n";
}
