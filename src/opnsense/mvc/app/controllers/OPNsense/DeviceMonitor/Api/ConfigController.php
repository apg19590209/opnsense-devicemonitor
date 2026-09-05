<?php

namespace OPNsense\DeviceMonitor\Api;

use OPNsense\Base\ApiControllerBase;
use OPNsense\DeviceMonitor\DeviceMonitor;

require_once('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/NotificationHandler.php');

/**
 * API controller for configuration management
 */
class ConfigController extends ApiControllerBase
{
    public function getAction()
    {
        $model = new DeviceMonitor();
        return $model->getConfig();
    }

    public function getversionAction()
    {
        $defaultsFile = '/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json';
        $defaults = json_decode(file_get_contents($defaultsFile), true);
        return ['version' => $defaults['version'] ?? '2.0'];
    }

    public function getinterfacesAction()
    {
        $result = [];
        try {
            $xml = @simplexml_load_file('/conf/config.xml');
            if ($xml && isset($xml->interfaces)) {
                foreach ($xml->interfaces->children() as $ifName => $ifData) {
                    $iface = trim((string)($ifData->if ?? ''));
                    $descr = trim((string)($ifData->descr ?? ''));
                    if (empty($iface)) continue;
                    if (empty($descr)) $descr = strtoupper($ifName);
                    if (preg_match('/vlan\d+\.(\d+)/i', $iface, $m)) {
                        $key = 'VLAN' . $m[1];
                    } else {
                        $key = strtoupper($iface);
                    }
                    $result[$key] = $descr;
                }
            }
        } catch (\Exception $e) {}
        return $result;
    }

    public function setAction()
    {
        if (!$this->request->isPost()) {
            return ['result' => 'failed', 'message' => 'Must be a POST request'];
        }

        $model = new DeviceMonitor();

        $enabled = $this->request->getPost('enabled', 'string', '0');
        $email_enabled = $this->request->getPost('email_enabled', 'string', '0');
        $identity_email_enabled = $this->request->getPost('identity_email_enabled', 'string', '0');
        $email_to = trim($this->request->getPost('email_to', 'string', ''));
        $email_from = trim($this->request->getPost('email_from', 'string', 'devicemonitor@opnsense.local'));
        $email_method = strtolower(trim($this->request->getPost('email_method', 'string', 'sendmail')));
        $smtp_host = trim($this->request->getPost('smtp_host', 'string', ''));
        $smtp_port = (int)$this->request->getPost('smtp_port', 'int', 587);
        $smtp_encryption = strtolower(trim($this->request->getPost('smtp_encryption', 'string', 'starttls')));
        $smtp_username = trim($this->request->getPost('smtp_username', 'string', ''));
        $smtp_password = $this->request->getPost('smtp_password', 'string', '');

        $webhook_enabled = $this->request->getPost('webhook_enabled', 'string', '0');
        $webhook_url = $this->request->getPost('webhook_url', 'string', '');
        $scan_interval = $this->request->getPost('scan_interval', 'int', 300);
        $email_vlans = $this->request->getPost('email_vlans', 'string', '');
        $webhook_vlans = $this->request->getPost('webhook_vlans', 'string', '');

        $targeted_nmap_enabled = $this->request->getPost('targeted_nmap_enabled', 'string', '1');
        $nmap_top_ports = (int)$this->request->getPost('nmap_top_ports', 'int', 100);
        $nmap_timing = (int)$this->request->getPost('nmap_timing', 'int', 4);
        $nmap_host_timeout = (int)$this->request->getPost('nmap_host_timeout', 'int', 45);
        $nmap_version_detection = $this->request->getPost('nmap_version_detection', 'string', '1');
        $nmap_max_per_cycle = (int)$this->request->getPost('nmap_max_per_cycle', 'int', 2);

        if (!in_array($identity_email_enabled, ['0', '1'], true)) {
            return ['result' => 'failed', 'message' => 'Invalid identity email enabled value'];
        }

        if (!in_array($email_method, ['sendmail', 'smtp'], true)) {
            return ['result' => 'failed', 'message' => 'Invalid email delivery method'];
        }

        if (!in_array($smtp_encryption, ['none', 'starttls', 'ssl'], true)) {
            return ['result' => 'failed', 'message' => 'Invalid SMTP encryption type'];
        }

        if ($email_enabled == '1') {
            if (empty($email_to) || !filter_var($email_to, FILTER_VALIDATE_EMAIL)) {
                return ['result' => 'failed', 'message' => 'Invalid recipient email address'];
            }

            if (empty($email_from) || !filter_var($email_from, FILTER_VALIDATE_EMAIL)) {
                return ['result' => 'failed', 'message' => 'Invalid sender email address'];
            }

            if ($email_method === 'smtp') {
                if ($smtp_host === '') {
                    return ['result' => 'failed', 'message' => 'SMTP server must not be empty'];
                }
                if ($smtp_port < 1 || $smtp_port > 65535) {
                    return ['result' => 'failed', 'message' => 'SMTP port must be between 1 and 65535'];
                }
            }
        }

        if ($webhook_enabled == '1') {
            if (empty($webhook_url)) {
                return ['result' => 'failed', 'message' => 'Webhook URL must not be empty'];
            }
            if (!filter_var($webhook_url, FILTER_VALIDATE_URL)) {
                return ['result' => 'failed', 'message' => 'Invalid webhook URL'];
            }
        }

        if ($scan_interval < 60 || $scan_interval > 3600) {
            return ['result' => 'failed', 'message' => 'Scan interval must be between 60 and 3600 seconds'];
        }

        if (!in_array($targeted_nmap_enabled, ['0', '1'], true)) {
            return ['result' => 'failed', 'message' => 'Invalid targeted Nmap enabled value'];
        }

        if ($nmap_top_ports < 1 || $nmap_top_ports > 1000) {
            return ['result' => 'failed', 'message' => 'Nmap top ports must be between 1 and 1000'];
        }

        if ($nmap_timing < 0 || $nmap_timing > 5) {
            return ['result' => 'failed', 'message' => 'Nmap timing template must be between 0 and 5'];
        }

        if ($nmap_host_timeout < 10 || $nmap_host_timeout > 300) {
            return ['result' => 'failed', 'message' => 'Nmap host timeout must be between 10 and 300 seconds'];
        }

        if (!in_array($nmap_version_detection, ['0', '1'], true)) {
            return ['result' => 'failed', 'message' => 'Invalid Nmap version detection value'];
        }

        if ($nmap_max_per_cycle < 1 || $nmap_max_per_cycle > 10) {
            return ['result' => 'failed', 'message' => 'Nmap scans per cycle must be between 1 and 10'];
        }

        $config = $model->getConfig();
        $config['enabled'] = $enabled;
        $config['email_enabled'] = $email_enabled;
        $config['identity_email_enabled'] = $identity_email_enabled;
        $config['email_to'] = $email_to;
        $config['email_from'] = $email_from;
        $config['email_method'] = $email_method;
        $config['smtp_host'] = $smtp_host;
        $config['smtp_port'] = $smtp_port;
        $config['smtp_encryption'] = $smtp_encryption;
        $config['smtp_username'] = $smtp_username;
        $config['smtp_password'] = $smtp_password;
        $config['webhook_enabled'] = $webhook_enabled;
        $config['webhook_url'] = $webhook_url;
        $config['scan_interval'] = (int)$scan_interval;
        $config['email_vlans'] = $email_vlans;
        $config['webhook_vlans'] = $webhook_vlans;
        $config['targeted_nmap_enabled'] = $targeted_nmap_enabled;
        $config['nmap_top_ports'] = $nmap_top_ports;
        $config['nmap_timing'] = $nmap_timing;
        $config['nmap_host_timeout'] = $nmap_host_timeout;
        $config['nmap_version_detection'] = $nmap_version_detection;
        $config['nmap_max_per_cycle'] = $nmap_max_per_cycle;

        if ($model->setConfig($config)) {
            return ['result' => 'saved', 'message' => 'Configuration saved'];
        }

        return ['result' => 'failed', 'message' => 'Failed to save configuration'];
    }

    public function testemailAction()
    {
        $handler = new \NotificationHandler();
        $handler->fLog("Preparing to send test email", 'EMAIL');
        $result = $handler->sendEmail(true);

        $logMessage = "Test email result: " . (($result['result'] === 'sent' || $result['result'] === 'ok') ? "SUCCESS" : "FAILED");
        if ($result['result'] !== 'sent' && $result['result'] !== 'ok') {
            $logMessage .= " | Reason: " . ($result['message'] ?? 'Unknown error');
        }
        $handler->fLog($logMessage, "EMAIL-ConfigController");
        return $result;
    }

    public function testWebhookAction()
    {
        $handler = new \NotificationHandler();
        $handler->fLog("Preparing to send test webhook", 'WEBHOOK');
        $result = $handler->sendWebhook(true, $this->request->getPost('webhook_url', 'string', ''));

        $logMessage = "Test webhook result: " . (($result['result'] === 'sent' || $result['result'] === 'ok') ? "SUCCESS" : "FAILED");
        if ($result['result'] !== 'sent' && $result['result'] !== 'ok') {
            $logMessage .= " | Reason: " . ($result['message'] ?? 'Unknown error');
        }
        $handler->fLog($logMessage, "WEBHOOK-ConfigController");
        return $result;
    }
}
