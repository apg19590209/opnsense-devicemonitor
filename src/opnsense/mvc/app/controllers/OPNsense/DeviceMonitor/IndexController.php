<?php

namespace OPNsense\DeviceMonitor;

class IndexController extends \OPNsense\Base\IndexController
{
    /*
     * O4 / DM-BL-008c - bind the plugin's own "devicemonitor" text domain before any
     * view is rendered. The views call the global devicemonitor_t(), which this
     * binder defines, so the include is not optional for a Device Monitor page: if
     * the file is missing the page must fail rather than resolve English silently.
     */
    public function initialize()
    {
        parent::initialize();

        require_once '/usr/local/etc/inc/devicemonitor_locale.inc';

        if (function_exists('devicemonitor_bind_sidecar')) {
            devicemonitor_bind_sidecar();
        }

        $this->registerVoltFunctions();
    }

    /*
     * The framework's ControllerBase registers only its own Volt functions
     * (theme_file_or_default, file_exists, cache_safe), so Volt compiled the views'
     * {{ devicemonitor_t('...') }} as an unknown macro and every Device Monitor page
     * aborted with Phalcon\Mvc\View\Engine\Volt\Exceptions\MacroNotFound: the outer
     * GUI rendered while the content block stayed blank. Live evidence:
     * /var/lib/php/tmp/PHP_errors.log entries at 2026-09-29 08:58, 09:02 and 09:07.
     * Wrap the engine the framework registered and add the sidecar translator to its
     * compiler so the views keep resolving through the O4 sidecar chain.
     */
    private function registerVoltFunctions()
    {
        $engines = $this->view->getRegisteredEngines();
        $parent = $engines['.volt'] ?? null;

        $this->view->registerEngines([
            '.volt' => function ($view) use ($parent) {
                $engine = is_callable($parent) ? $parent($view) : $this->voltEngine($view);
                $engine->getCompiler()->addFunction('devicemonitor_t', 'devicemonitor_t');
                return $engine;
            },
        ]);
    }

    /*
     * Fallback only, for an OPNsense build that registers no '.volt' engine: mirrors
     * the framework's own engine construction so a plugin page cannot blank out, and
     * registers the same functions the framework does plus the sidecar translator.
     */
    private function voltEngine($view)
    {
        $appcfg = new \OPNsense\Core\AppConfig();
        $engine = new \Phalcon\Mvc\View\Engine\Volt($view);
        $engine->setOptions([
            'path' => $appcfg->application->cacheDir . '/',
            'separator' => '_',
        ]);

        $compiler = $engine->getCompiler();
        foreach ([
            'theme_file_or_default' => 'view_fetch_themed_filename',
            'file_exists' => 'view_file_exists',
            'cache_safe' => 'view_cache_safe',
            'devicemonitor_t' => 'devicemonitor_t',
        ] as $func_name => $function) {
            $compiler->addFunction($func_name, $function);
        }
        $compiler->addFilter('safe', 'view_html_safe');

        return $engine;
    }

    public function devicesAction()
    {
        $this->view->pick('OPNsense/DeviceMonitor/devices');
    }

    public function physicaldevicesAction()
    {
        $this->view->pick('OPNsense/DeviceMonitor/physicaldevices');
        $this->view->title = gettext('Services') . ': ' . gettext('Device Monitor') . ': ' . gettext('Devices');
        $this->view->headTitle = gettext('Devices') . ' | ' . gettext('Device Monitor') . ' | ' . gettext('Services');
    }
    
    public function identityeventsAction()
    {
        $status = (string)$this->request->getQuery('status');

        if (!in_array($status, ['all', 'unresolved', 'resolved'], true)) {
            $status = 'all';
        }

        $this->view->identityEventsStatus = $status;
        $this->view->pick('OPNsense/DeviceMonitor/identityevents');
    }

    public function devicehistoryAction()
    {
        $mac = strtolower(trim((string)$this->request->getQuery('mac')));
        $this->view->deviceHistoryMac = $mac;
        $this->view->pick('OPNsense/DeviceMonitor/devicehistory');
    }

    public function activitytimelineAction()
    {
        $mac = strtolower(trim((string)$this->request->getQuery('mac')));
        $this->view->activityTimelineMac = $mac;
        $this->view->pick('OPNsense/DeviceMonitor/activitytimeline');
    }

    public function scanhistoryAction()
    {
        $this->view->pick('OPNsense/DeviceMonitor/scanhistory');
    }

    public function changesummaryAction()
    {
        $this->view->pick('OPNsense/DeviceMonitor/changesummary');
    }

    public function settingsAction()
    {
        $this->view->pick('OPNsense/DeviceMonitor/settings');
    }

    public function infrastructureservicesAction()
    {
        $this->view->portDiscoveryPage = false;
        $this->view->pick(
            'OPNsense/DeviceMonitor/infrastructureservices'
        );
    }

    public function portdiscoveryAction()
    {
        $this->view->portDiscoveryPage = true;
        $this->view->pick(
            'OPNsense/DeviceMonitor/infrastructureservices'
        );
    }
}
