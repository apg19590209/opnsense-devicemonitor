<?php
/*
 * Sidecar resolution probe for tests/test_sidecar_catalogue.py.
 *
 * Reproduces the production path without OPNsense: the shipped binder
 * (src/etc/inc/devicemonitor_locale.inc), a real compiled plugin catalogue in the
 * <locale>/LC_MESSAGES/devicemonitor.mo layout, a stand-in core OPNsense domain, and
 * the sidecar toggle. Reports what devicemonitor_t() / devicemonitor_raw() resolve.
 *
 * Input  (JSON on stdin): locale, langcode, sidecar_dir, core_dir, enabled, keys
 * Output (JSON on stdout): sidecar_enabled, bound, values {key: {t, raw}}
 *
 * Environment: DM_PROBE_TOGGLE=0 stands in for sidecar_translation_enabled = "0".
 */

namespace OPNsense\DeviceMonitor {
    /* Stand-in for the plugin model, so the binder's toggle lookup is exercised
       without the OPNsense MVC library or a live configuration file. */
    class DeviceMonitor
    {
        public static function getConfig()
        {
            return [
                'sidecar_translation_enabled' => getenv('DM_PROBE_TOGGLE') === '0' ? '0' : '1',
                'webhook_url' => 'https://example.invalid/hook',
                'webhook_enabled' => '1',
            ];
        }
    }
}

namespace {
    $input = json_decode(stream_get_contents(STDIN), true, 512, JSON_THROW_ON_ERROR);
    $locale = $input['locale'];
    $langcode = $input['langcode'] ?? str_replace('_', '-', $locale);
    $sidecarDir = $input['sidecar_dir'];
    $coreDir = $input['core_dir'];
    $keys = $input['keys'] ?? [];
    $enabled = $input['enabled'] ?? true;

    /* The binder only defines these when they are undefined, so the probe can point
       the sidecar domain at a compiled test tree and leave the real install alone. */
    define('DEVMONITOR_SIDECAR_DIR', $sidecarDir);

    $catalogue = $locale . '.UTF-8';
    putenv('LANG=' . $catalogue);
    putenv('LANGUAGE=' . $catalogue);
    putenv('LC_ALL=' . $catalogue);
    setlocale(LC_ALL, $catalogue);

    /* The core domain is what the binder falls back to; bind it read-only, exactly as
       the production entry point does for /usr/local/share/locale. */
    bindtextdomain('OPNsense', $coreDir);
    bind_textdomain_codeset('OPNsense', 'UTF-8');

    require_once __DIR__ . '/../src/etc/inc/devicemonitor_locale.inc';

    if (!function_exists('view_html_safe')) {
        /* Same encoding as /usr/local/opnsense/www/index.php. */
        function view_html_safe($text)
        {
            return str_replace("\n", '&#10;', htmlspecialchars($text ?? '', ENT_QUOTES | ENT_HTML401));
        }
    }

    $bound = devicemonitor_bind_sidecar();

    $values = [];
    foreach ($keys as $key) {
        $values[$key] = [
            't' => devicemonitor_t($key),
            'raw' => devicemonitor_raw($key),
        ];
    }

    echo json_encode(
        [
            'sidecar_enabled' => devicemonitor_sidecar_enabled(),
            'bound' => (bool)$bound,
            'locale' => setlocale(LC_MESSAGES, 0),
            'langcode' => $langcode,
            'values' => $values,
        ],
        JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR
    );
}
