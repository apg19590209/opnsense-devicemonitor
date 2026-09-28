<?php

function devicemonitor_services()
{
    /* O3 / DM-BL-008c - bind the plugin's own sidecar catalogue when the binder is
     * deployed. Guarded so a missing binder degrades to the core translator instead
     * of fataling inside the core services page. */
    if (is_file('/usr/local/etc/inc/devicemonitor_locale.inc')) {
        require_once '/usr/local/etc/inc/devicemonitor_locale.inc';
        devicemonitor_bind_sidecar();
    }

    /* Escaped, like every other string on this page: devicemonitor_t() falls back to
     * the core OPNsense domain and then to the msgid. */
    $description = function_exists('devicemonitor_t')
        ? devicemonitor_t('Device Monitor - network device tracking')
        : gettext('Device Monitor - network device tracking');

    $services = [];
    $services[] = [
        'description' => $description,
        'configd' => [
            'restart' => ['devicemonitor restart'],
            'start'   => ['devicemonitor start'],
            'stop'    => ['devicemonitor stop'],
        ],
        'name'    => 'devicemonitor',
        'pidfile' => '/var/run/devicemonitor.pid',
    ];
    return $services;
}