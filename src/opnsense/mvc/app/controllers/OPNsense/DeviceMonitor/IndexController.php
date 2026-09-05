<?php

namespace OPNsense\DeviceMonitor;

class IndexController extends \OPNsense\Base\IndexController
{
    public function devicesAction()
    {
        $this->view->pick('OPNsense/DeviceMonitor/devices');
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

    public function scanhistoryAction()
    {
        $this->view->pick('OPNsense/DeviceMonitor/scanhistory');
    }

    public function settingsAction()
    {
        $this->view->pick('OPNsense/DeviceMonitor/settings');
    }
}