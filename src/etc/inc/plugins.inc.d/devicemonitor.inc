<?php

function devicemonitor_services()
{
    $services = [];
    $services[] = [
        'description' => gettext('Device Monitor - network device tracking'),
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