<?php
/*
 * Device Monitor - sidecar translation binder.
 *
 * O3 / DM-BL-008c (framework) and O4 (view call sites).
 *
 * Binds the plugin's own "devicemonitor" text domain under
 * /usr/local/opnsense/mvc/app/languages (<locale>/LC_MESSAGES/devicemonitor.mo),
 * the only layout bindtextdomain() can resolve, and exposes the global translator
 * the Device Monitor views call.
 *
 * Fallback chain: sidecar catalogue -> core OPNsense catalogue (read-only) -> msgid.
 * The core catalogues under /usr/local/share/locale are never read or written by
 * this file; the core domain is only asked for a translation.
 *
 * This file is part of the guarded runtime payload (release/v2.10-runtime.manifest):
 * the views call devicemonitor_t(), so a system without it must not render a Device
 * Monitor page. It is required, guarded on is_file(), from
 * IndexController::initialize() and from plugins.inc.d/devicemonitor.inc.
 */

if (!defined('DEVMONITOR_SIDECAR_DOMAIN')) {
    define('DEVMONITOR_SIDECAR_DOMAIN', 'devicemonitor');
}
if (!defined('DEVMONITOR_SIDECAR_DIR')) {
    define('DEVMONITOR_SIDECAR_DIR', '/usr/local/opnsense/mvc/app/languages');
}
if (!defined('DEVMONITOR_CORE_DOMAIN')) {
    define('DEVMONITOR_CORE_DOMAIN', 'OPNsense');
}

/*
 * The sidecar toggle. A missing key - or an unreadable configuration - keeps the
 * sidecar enabled, because the default in defaults.json is "1" and the fallback
 * chain is safe either way. Only an explicit "0" disables it.
 */
function devicemonitor_sidecar_enabled()
{
    static $enabled = null;

    if ($enabled !== null) {
        return $enabled;
    }

    $enabled = true;

    if (class_exists('\OPNsense\DeviceMonitor\DeviceMonitor')) {
        try {
            $config = \OPNsense\DeviceMonitor\DeviceMonitor::getConfig();
            if (isset($config['sidecar_translation_enabled'])) {
                $enabled = ((string)$config['sidecar_translation_enabled'] === '1');
            }
        } catch (\Throwable $error) {
            $enabled = true;
        }
    }

    return $enabled;
}

/*
 * Bind the sidecar domain. Returns false when the toggle is off, in which case
 * devicemonitor_translate() resolves through the core domain exactly as the stock
 * view translator does.
 */
function devicemonitor_bind_sidecar()
{
    if (!devicemonitor_sidecar_enabled()) {
        return false;
    }

    if (!function_exists('bindtextdomain')) {
        return false;
    }

    bindtextdomain(DEVMONITOR_SIDECAR_DOMAIN, DEVMONITOR_SIDECAR_DIR);
    if (function_exists('bind_textdomain_codeset')) {
        bind_textdomain_codeset(DEVMONITOR_SIDECAR_DOMAIN, 'UTF-8');
    }

    return true;
}

/*
 * Raw (unescaped) translation: the JavaScript-context counterpart of
 * ViewTranslator::query(). Never echo this into HTML.
 */
function devicemonitor_raw($message_id, array $placeholders = [])
{
    $message_id = (string)$message_id;

    if ($message_id === '') {
        return '';
    }

    $translated = null;

    if (devicemonitor_sidecar_enabled() && function_exists('dgettext')) {
        $sidecar = dgettext(DEVMONITOR_SIDECAR_DOMAIN, $message_id);
        if ($sidecar !== '' && $sidecar !== $message_id) {
            $translated = $sidecar;
        }
    }

    if ($translated === null && function_exists('dgettext')) {
        $core = dgettext(DEVMONITOR_CORE_DOMAIN, $message_id);
        if ($core !== '' && $core !== $message_id) {
            $translated = $core;
        }
    }

    if ($translated === null) {
        $translated = $message_id;
    }

    if ($placeholders !== []) {
        $translated = devicemonitor_interpolate($translated, $placeholders);
    }

    return $translated;
}

/*
 * HTML-safe translation, the drop-in replacement for the views' former
 * $lang->_() calls. Escaping matches OPNsense\Base\ViewTranslator with
 * view_html_safe set (ENT_QUOTES | ENT_HTML401, newline as &#10;), so migrating a
 * call site cannot change how a string is emitted.
 */
function devicemonitor_t($message_id, array $placeholders = [])
{
    $text = devicemonitor_raw($message_id, $placeholders);

    return str_replace("\n", '&#10;', htmlspecialchars($text, ENT_QUOTES | ENT_HTML401));
}

/*
 * Placeholder handling for the two forms the plugin uses: sprintf-style positional
 * arguments, and %name% tokens.
 */
function devicemonitor_interpolate($text, array $placeholders)
{
    if (array_is_list($placeholders)) {
        return vsprintf($text, $placeholders);
    }

    $tokens = [];
    foreach ($placeholders as $name => $value) {
        $tokens['%' . $name . '%'] = (string)$value;
    }

    return strtr($text, $tokens);
}
