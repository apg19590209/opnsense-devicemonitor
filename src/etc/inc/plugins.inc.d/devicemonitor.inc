<?php

function devicemonitor_services()
{
    /* O3 / DM-BL-008c - bind the plugin's own sidecar catalogue when the
     * binder is deployed. Guarded so a missing binder degrades to stock
     * gettext() instead of fataling inside the core services page. */
    if (is_file('/usr/local/etc/inc/devicemonitor_locale.inc')) {
        require_once 'devicemonitor_locale.inc';
        devicemonitor_bind_sidecar();
    }

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