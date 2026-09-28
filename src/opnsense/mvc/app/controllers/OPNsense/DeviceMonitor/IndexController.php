<?php

namespace OPNsense\DeviceMonitor;

class IndexController extends \OPNsense\Base\IndexController
{
    /*
     * O3 / DM-BL-008c - sidecar catalogue binding.
     *
     * Registers the plugin's own "devicemonitor" text domain so this plugin's
     * strings can be translated without ever touching the OPNsense core
     * catalogues under /usr/local/share/locale.
     *
     * Guarded on purpose: if the binder has not been deployed, the page must
     * still render with stock behaviour rather than fatal on a missing include.
     */
    public function initialize()
    {
        parent::initialize();

        if (is_file('/usr/local/etc/inc/devicemonitor_locale.inc')) {
            require_once 'devicemonitor_locale.inc';
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
