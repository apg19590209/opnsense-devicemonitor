# Device Monitor — System Map

## Purpose

This file describes the Device Monitor environment, components, important paths and relationships.

Architectural behaviour is defined in `DECISIONS.md`.

Current project progress and current operating values belong in `PROJECT_STATE.md`, not in this system map.

## Primary environment

Primary deployment target:

- OPNsense 26.7.2_2
- primary OPNsense firewall

Development has also been performed from a Windows checkout under:

`C:\Users\apg19\Downloads\opnsense-devicemonitor-*`

The exact active checkout should be confirmed from the current repository when beginning work.

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