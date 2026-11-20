<?php
/**
 * Plugin-wide timestamp convention for Device Monitor.
 *
 * Timestamps are stored and transported as naive UTC text in
 * "YYYY-MM-DD HH:MM:SS" form. Infrastructure Services and Device Activity use
 * the shared server-side display formatter below. Email Log keeps its
 * browser-local formatter and toConfiguredZone() fallback. No offset or
 * abbreviation is hardcoded here, and historical text is never rewritten.
 */
namespace OPNsense\DeviceMonitor;

final class PluginTimestamps
{
    const FORMAT = 'Y-m-d H:i:s';
    const DISPLAY_FORMAT = 'Y-m-d H:i:s T';

    /** Validate the exact stored UTC text form without normalising it. */
    public static function isStoredUtcTimestamp($value)
    {
        $value = (string)$value;
        if ($value === '') {
            return false;
        }
        $dt = \DateTimeImmutable::createFromFormat(
            '!' . self::FORMAT,
            $value,
            new \DateTimeZone('UTC')
        );

        return $dt !== false && $dt->format(self::FORMAT) === $value;
    }

    /**
     * Format a proven UTC value once for display in the configured zone.
     * Invalid values are returned verbatim so callers cannot normalise
     * malformed or ambiguous historical text by accident.
     */
    public static function formatForDisplay($value, $zone = null)
    {
        $value = (string)$value;
        if (!self::isStoredUtcTimestamp($value)) {
            return $value;
        }
        $zone = $zone === null
            ? date_default_timezone_get()
            : trim((string)$zone);
        if ($zone === '' || !in_array($zone, \DateTimeZone::listIdentifiers(), true)) {
            return $value;
        }
        try {
            $dt = \DateTimeImmutable::createFromFormat(
                '!' . self::FORMAT,
                $value,
                new \DateTimeZone('UTC')
            );
            return $dt
                ->setTimezone(new \DateTimeZone($zone))
                ->format(self::DISPLAY_FORMAT);
        } catch (\Throwable $e) {
            return $value;
        }
    }

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
    public static function toConfiguredZone($value, $configFile = '/conf/config.xml')
    {
        $value = self::clean($value);
        if ($value === '') {
            return '';
        }
        $zone = self::configuredZoneName($configFile);
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
