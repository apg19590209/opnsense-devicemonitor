<?php
/**
 * Plugin-wide timestamp convention for Device Monitor.
 *
 * Timestamps are stored and transported as naive UTC text in
 * "YYYY-MM-DD HH:MM:SS" form. Presentation converts them once, in the
 * browser, using its own timezone rules and abbreviation (the same
 * convention as the Change Summary's formatBrowserLocalTime()), falling back
 * to Python's zoneinfo (the engine behind scan_network.utc_timestamp) when the
 * browser cannot format the value. No offset or abbreviation is hardcoded
 * here, and historical text is never rewritten.
 */
namespace OPNsense\DeviceMonitor;

final class PluginTimestamps
{
    const FORMAT = 'Y-m-d H:i:s';

    /** Validate and normalise an API-supplied timestamp to the stored form. */
    public static function clean($value)
    {
        $value = trim((string)$value);
        if ($value === '') {
            return '';
        }
        $dt = \DateTimeImmutable::createFromFormat(self::FORMAT, $value, new \DateTimeZone('UTC'));
        return $dt === false ? '' : $dt->format(self::FORMAT);
    }

    /**
     * Convert a stored UTC timestamp for the server-side fallback renderer,
     * using the OPNsense-configured zone (DST rules included).
     */
    public static function toConfiguredZone($value)
    {
        $value = self::clean($value);
        if ($value === '') {
            return '';
        }
        $zone = self::configuredZoneName();
        try {
            $dt = \DateTimeImmutable::createFromFormat(self::FORMAT, $value, new \DateTimeZone('UTC'));
            return $dt->setTimezone(new \DateTimeZone($zone))->format(self::FORMAT);
        } catch (\Throwable $e) {
            return $value;
        }
    }

    /**
     * The configured OPNsense timezone, used only when known and valid. The
     * legacy config file is read directly so scripts that run outside the MVC
     * framework resolve the same zone the GUI stores.
     */
    public static function configuredZoneName($configFile = '/conf/config.xml')
    {
        $zone = '';
        if (is_readable($configFile)) {
            $xml = @simplexml_load_file($configFile);
            if ($xml !== false && isset($xml->system->timezone)) {
                $zone = trim((string)$xml->system->timezone);
            }
        }
        return $zone !== '' && in_array($zone, \DateTimeZone::listIdentifiers(), true) ? $zone : 'UTC';
    }
}
