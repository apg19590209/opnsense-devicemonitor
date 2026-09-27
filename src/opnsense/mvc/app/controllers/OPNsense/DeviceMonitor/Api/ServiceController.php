<?php

namespace OPNsense\DeviceMonitor\Api;

use OPNsense\Base\ApiControllerBase;
use OPNsense\Core\Backend;

class ServiceController extends ApiControllerBase
{
    /**
     * Run a manual scan
     */
    public function scanAction()
    {
        if ($this->request->isPost()) {
            $backend = new Backend();
            $response = $backend->configdRun("devicemonitor scan");
            return ['result' => 'ok', 'output' => $response];
        }
        
        return ['result' => 'failed'];
    }

    /**
     * Daemon status, checked through the configd status action.
     */
    public function statusAction()
    {
        $backend = new Backend();
        $output = trim($backend->configdRun('devicemonitor status'));
        $model = new \OPNsense\DeviceMonitor\DeviceMonitor();
        $pidFile = $model->getPidFilePath();
        $pid = file_exists($pidFile) ? trim(file_get_contents($pidFile)) : null;

        if ($output === 'running') {
            return [
                'result' => 'running',
                'pid' => $pid,
                'message' => 'Daemon is running'
            ];
        }

        return [
            'result' => 'stopped',
            'pid' => $pid,
            'message' => 'Daemon is not running'
        ];
    }

    /**
     * Start daemona
     */
    public function startAction()
    {
        if ($this->request->isPost()) {
            $status = $this->statusAction();
            if ($status['result'] === 'running') {
                return ['result' => 'already_running', 'message' => 'Daemon is already running'];
            }

            $backend = new Backend();
            $backend->configdRun('devicemonitor start');
            sleep(1);

            $status = $this->statusAction();
            if ($status['result'] === 'running') {
                return ['result' => 'started', 'message' => 'Daemon started successfully'];
            } else {
                return ['result' => 'failed', 'message' => 'Failed to start daemon'];
            }
        }
        return ['result' => 'failed'];
    }

    /**
     * Stop daemona
     */
    public function stopAction()
    {
        if ($this->request->isPost()) {
            $backend = new Backend();
            $backend->configdRun('devicemonitor stop');
            sleep(1);

            $status = $this->statusAction();
            if ($status['result'] === 'stopped') {
                return ['result' => 'stopped', 'message' => 'Daemon stopped successfully'];
            } else {
                return ['result' => 'failed', 'message' => 'Failed to stop daemon'];
            }
        }
        return ['result' => 'failed'];
    }

    /**
     * Restart daemona
     */
    public function restartAction()
    {
        if ($this->request->isPost()) {
            $backend = new Backend();
            $backend->configdRun('devicemonitor restart');
            sleep(2);
            return $this->statusAction();
        }
        return ['result' => 'failed'];
    }
}