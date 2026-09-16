# Device Monitor — System Map

## Purpose

This file describes the Device Monitor environment, components, important paths and relationships.

Architectural behaviour is defined in `DECISIONS.md`.

Current project progress and current operating values belong in `PROJECT_STATE.md`, not in this system map.

## Primary environment

Primary deployment target:

- OPNsense 26.7.2_2
- primary OPNsense firewall

## Development environment topology

    Windows VS Code UI
        |
        v
    Remote SSH / Linuxulator-hosted VS Code Server
        |
        v
    FreeBSD 15.1-RELEASE authoritative checkout + native development toolchain
        |
        v
    SSH (`ssh opnsense-dm`)
        |
        v
    OPNsense 26.7.2_2 runtime/deployment target

Authoritative development checkout:

`/home/dmdev/src/opnsense-devicemonitor-upstream`

Native FreeBSD development toolchain:

    /bin/sh
    /usr/local/bin/bash
    /usr/local/bin/git
    /usr/local/bin/php
    /usr/local/bin/python3
    /usr/local/bin/node

The VS Code Server runs through FreeBSD Linuxulator compatibility, which is its
only intended use; normal project commands run on the native FreeBSD toolchain.

Windows checkout (fallback/reference only, no longer authoritative):

`C:\Users\apg19\Downloads\opnsense-devicemonitor-upstream`

Debian WSL remains secondary/fallback only and is not an authoritative Device
Monitor checkout.

The authoritative checkout should be confirmed from the current repository and
host when beginning work.

## TESTBED environment

Isolated OPNsense instance used for Device Monitor validation outside production.

Access and management:

- host alias `opnsense-testbed`
- management path is the LAN interface `vtnet1`, `192.168.56.2/24`, used for both
  GUI and SSH access
- workstation-local access configuration (keys, host aliases and credentials)
  remains in the untracked local rules file

Interfaces and uplink:

- OPNsense `26.7.3_11`
- LAN `vtnet1` `192.168.56.2/24`
- WAN `vtnet0` on VirtualBox NAT, address `10.0.2.15/24`, default gateway
  `10.0.2.2` — the default route and the path towards production and the Internet
- Device Monitor and Hostwatch are installed and running on the testbed;
  Hostwatch is bound to `vtnet1`
- DNS: the WAN DHCP DNS override is disabled, `/etc/resolv.conf` uses the local
  resolver `127.0.0.1`, and Unbound provides recursive resolution

Production isolation boundary:

- one persistent pf rule blocks outbound IPv4 traffic from the testbed to the
  production LAN `192.168.20.0/24`:
  `block drop out log quick on vtnet0 inet from any to 192.168.20.0/24`
  (rule UUID `527f4f3b-f82c-4ee8-b4ee-3a5e63df2c14`)
- the rule matches on the WAN out path (`vtnet0`), which is the testbed's only
  route towards `192.168.20.0/24`
- public Internet access, DNS resolution and management access over
  `192.168.56.2` are retained; isolation was verified before and after a testbed
  reboot
- limitation: only `192.168.20.0/24` is blocked; other
  host/production-reachable prefixes through the VirtualBox NAT uplink remain
  reachable

## Important production paths

### Device Monitor database

`/var/db/devicemonitor/devices.db`

Storage responsibilities include Device Monitor device/state persistence and related runtime/history data.

### Hostwatch database

`/var/db/hostwatch/hosts.db`

Hostwatch records network host observations used by Device Monitor.

Current-state interpretation behaviour is defined in `DECISIONS.md`.

### Device Monitor runtime scripts

`/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/`

This is the production location for Device Monitor runtime scripts.

## Major components

### Hostwatch

Hostwatch observes hosts on OPNsense interfaces and stores host observations.

Device Monitor consumes Hostwatch information.

### Device Monitor Python runtime

Responsibilities include:

- device discovery
- device state/history processing
- Hostwatch integration
- scan-queue processing
- targeted Nmap scanning
- retry handling
- identity-event detection
- notification processing

### Device Monitor SQLite database

Provides persistent Device Monitor storage used by runtime and UI/API components.

### OPNsense MVC/API layer

Provides Device Monitor configuration and UI/API access.

Relevant source-tree locations include:

`src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/`

`src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/`

`src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/`

### Device Monitor UI

The OPNsense UI consumes Device Monitor API/model information and presents Device Monitor data to the administrator.

### Nmap

Nmap is used by Device Monitor for security scanning.

Targeting and resource-behaviour requirements are defined in `DECISIONS.md`.

### Notifications

Device Monitor provides notification handling for ordinary device events and security-scan results.

Notification configuration is provided through the Device Monitor configuration/model layer.

Recipient and delivery behaviour are defined in `DECISIONS.md`.

### Infrastructure service discovery

Infrastructure Services uses the persistent `device_services` inventory in
the Device Monitor SQLite database.

Current discovery coverage includes:

- DHCP
- DNS
- NTP
- SSH
- HTTP/HTTPS Web/Admin
- SMB
- NFS
- RDP
- VNC
- WinRM
- SNMP
- LDAP/LDAPS
- Kerberos
- VPN endpoints

Evidence sources include:

- protocol-specific network probes
- existing structured targeted-Nmap evidence
- authoritative OPNsense runtime state for locally hosted WireGuard

Automatic Phase 3 discovery does not perform a fresh Nmap sweep over all
known devices.

The production UI is available at:

`Services -> Device Monitor -> Infrastructure Services`

### Scan queue

Security scans are coordinated through persistent queue data stored in the Device Monitor database.

The Python runtime processes queued scan work and records resulting scan history.

Queue retry, persistence and rate-limiting behaviour are defined in `DECISIONS.md`.

## Repository structure

Relevant repository areas include:

- `src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/`
  - API/controller logic
- `src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/`
  - OPNsense model and configuration schema
- `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/`
  - Device Monitor UI views
- Python runtime/scripts
  - exact repository path should be confirmed from the current checkout
- `Makefile`
  - development/install/test workflow where applicable

## High-level data flow

    Hostwatch
        |
        v
    Device Monitor Python runtime
        |
        +--> Device/state SQLite records
        |
        +--> IP & MAC conflict-event records
        |
        +--> Infrastructure-service inventory
        |
        +--> Persistent Nmap scan queue
        |        |
        |        v
        |      Nmap
        |        |
        |        v
        |      Scan history/results
        |
        +--> Notifications

    Device Monitor SQLite database
        |
        v
    OPNsense MVC/API
        |
        v
    Device Monitor UI

## Configuration relationship

Device Monitor configuration is provided through the OPNsense Device Monitor model/UI and consumed by the relevant runtime/UI components.

Exact configuration paths and schema details should be taken from current repository/system inspection rather than assumed.

Current operating values belong in `PROJECT_STATE.md`, not in this system map.