<?php
/**
 * Management identity for presentation.
 *
 * The displayed address is the configured management interface (LAN, falling back
 * to any configured interface with a static IPv4 address) rather than whichever
 * NIC happens to answer first. The role is the live CARP state. Nothing here is
 * recorded against email history: rows keep the role captured when they were made.
 */
namespace OPNsense\DeviceMonitor;

final class NodeIdentity
{
    /** Declared order of preference for the management interface. */
    const INTERFACE_ORDER = ['lan', 'opt1', 'opt2', 'opt3', 'opt4', 'opt5'];

    public static function local()
    {
        $host = trim((string)@gethostname());
        $ip = self::managementAddress();
        $role = self::currentRole();
        return [
            'node_id' => $host,
            'node_ip' => $ip,
            'role' => $role,
            // The single rendered form: "hostname — management IP — role".
            'label' => self::label($host, $ip, $role),
        ];
    }

    /** Configured interface address, from config.xml, never an interface scan. */
    public static function managementAddress($config = null)
    {
        $config = $config ?: self::config();
        if ($config === null || !isset($config->interfaces)) {
            return '';
        }
        $names = array_keys((array)$config->interfaces->children());
        $ordered = array_merge(array_intersect(self::INTERFACE_ORDER, $names), array_diff($names, self::INTERFACE_ORDER));
        foreach ($ordered as $name) {
            $if = $config->interfaces->{$name};
            if (!isset($if->ipaddr)) {
                continue;
            }
            $addr = trim((string)$if->ipaddr);
            if (filter_var($addr, FILTER_VALIDATE_IP, FILTER_FLAG_IPV4)
                && strpos($addr, '127.') !== 0) {
                return $addr;
            }
        }
        return '';
    }

    /** Live CARP role of the first vhid, or 'unknown'. */
    public static function currentRole()
    {
        $out = @shell_exec("ifconfig 2>/dev/null | grep -oE 'carp: [A-Z]+' | head -1 | awk '{print $2}'");
        return trim((string)$out) !== '' ? strtolower(trim((string)$out)) : 'unknown';
    }

    public static function label($host, $ip, $role)
    {
        $parts = array_filter([trim((string)$host), trim((string)$ip), trim((string)$role)], 'strlen');
        return implode(" \u{2014} ", $parts);
    }

    private static function config()
    {
        if (class_exists('OPNsense\\Core\\Config')) {
            try {
                return \OPNsense\Core\Config::getInstance()->object();
            } catch (\Throwable $e) {
                return null;
            }
        }
        if (is_readable('/conf/config.xml')) {
            $xml = @simplexml_load_file('/conf/config.xml');
            return $xml === false ? null : $xml;
        }
        return null;
    }
}
