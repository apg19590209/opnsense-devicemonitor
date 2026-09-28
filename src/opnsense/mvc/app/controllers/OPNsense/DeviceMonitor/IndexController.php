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
