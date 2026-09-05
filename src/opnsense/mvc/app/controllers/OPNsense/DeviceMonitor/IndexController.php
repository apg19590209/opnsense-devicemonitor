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