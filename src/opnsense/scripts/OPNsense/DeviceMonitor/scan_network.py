#!/usr/local/bin/python3

import sqlite3
import socket
import ssl
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, UTC, timedelta
import os
import json
import sys
import argparse
import subprocess
import re
import time
import select
import struct
import ipaddress
import xml.etree.ElementTree as ET

# ================================================================
# CONFIGURATION - ENABLE/DISABLE FEATURES
# ================================================================
DEBUG_LOGGING = True  # Set to False to disable logging

# ================================================================
# PATHS - ALL IN ONE PLACE
#
#          Pointer to the configuration file containing default values
#
# ================================================================
defaultsFile = '/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'

def load_defaults():
    with open(defaultsFile, 'r') as f:
        return json.load(f)

# Load at startup
_defaults = load_defaults()
PATHS = _defaults['paths']

# Paths instead of hard-coded values
HOSTWATCH_DB = PATHS['hostwatchDb']
CONFIG_FILE = PATHS['configFile']
DB_FILE = PATHS['dbFile']
DEFAULT_CONFIG = _defaults['config']
# ================================================================


def log(message):
    """Standard append logging"""
    if not DEBUG_LOGGING:
        return

    timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    with open("/var/log/devicemonitor.log", "a") as f:
        f.write(f"{timestamp} - {message}\n")

def load_config():
    """Load runtime configuration"""

    if not os.path.exists(CONFIG_FILE):
        if DEBUG_LOGGING:
            log(f"Config file not found: {CONFIG_FILE}, using defaults")
        return {
            'enabled': DEFAULT_CONFIG['enabled'] == '1',
            'email_enabled': DEFAULT_CONFIG.get('email_enabled', '1') == '1',
            'identity_email_enabled': DEFAULT_CONFIG.get('identity_email_enabled', '0') == '1',
            'email_to': DEFAULT_CONFIG.get('email_to', ''),
            'email_from': DEFAULT_CONFIG.get('email_from', 'devicemonitor@opnsense.local'),
            'webhook_enabled': DEFAULT_CONFIG.get('webhook_enabled', '0') == '1',
            'webhook_url': DEFAULT_CONFIG.get('webhook_url', ''),
            'scan_interval': int(DEFAULT_CONFIG.get('scan_interval', 300)),
            'email_vlans': DEFAULT_CONFIG.get('email_vlans', ''),
            'webhook_vlans': DEFAULT_CONFIG.get('webhook_vlans', ''),
            'targeted_nmap_enabled': DEFAULT_CONFIG.get('targeted_nmap_enabled', '1') == '1',
            'nmap_top_ports': int(DEFAULT_CONFIG.get('nmap_top_ports', 100)),
            'nmap_timing': int(DEFAULT_CONFIG.get('nmap_timing', 4)),
            'nmap_host_timeout': int(DEFAULT_CONFIG.get('nmap_host_timeout', 45)),
            'nmap_version_detection': DEFAULT_CONFIG.get('nmap_version_detection', '1') == '1',
            'nmap_max_per_cycle': int(DEFAULT_CONFIG.get('nmap_max_per_cycle', 2)),
            'apiEmailUrl': PATHS.get('apiEmailUrl', ''),
            'apiWebhookUrl': PATHS.get('apiWebhookUrl', '')
        }

    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

            return {
                'enabled': config.get('enabled', '0') == '1',
                'email_enabled': config.get('email_enabled', '1') == '1',
                'identity_email_enabled': config.get('identity_email_enabled', '0') == '1',
                'email_to': config.get('email_to', ''),
                'email_from': config.get('email_from', 'devicemonitor@opnsense.local'),
                'webhook_enabled': config.get('webhook_enabled', '0') == '1',
                'webhook_url': config.get('webhook_url', ''),
                'scan_interval': int(config.get('scan_interval', DEFAULT_CONFIG.get('scan_interval', 300))),
                'email_vlans': config.get('email_vlans', DEFAULT_CONFIG.get('email_vlans', '')),
                'webhook_vlans': config.get('webhook_vlans', DEFAULT_CONFIG.get('webhook_vlans', '')),
                'targeted_nmap_enabled': config.get('targeted_nmap_enabled', DEFAULT_CONFIG.get('targeted_nmap_enabled', '1')) == '1',
                'nmap_top_ports': int(config.get('nmap_top_ports', DEFAULT_CONFIG.get('nmap_top_ports', 100))),
                'nmap_timing': int(config.get('nmap_timing', DEFAULT_CONFIG.get('nmap_timing', 4))),
                'nmap_host_timeout': int(config.get('nmap_host_timeout', DEFAULT_CONFIG.get('nmap_host_timeout', 45))),
                'nmap_version_detection': config.get('nmap_version_detection', DEFAULT_CONFIG.get('nmap_version_detection', '1')) == '1',
                'nmap_max_per_cycle': int(config.get('nmap_max_per_cycle', DEFAULT_CONFIG.get('nmap_max_per_cycle', 2))),
                'apiEmailUrl': PATHS.get('apiEmailUrl', ''),
                'apiWebhookUrl': PATHS.get('apiWebhookUrl', '')
            }
    except Exception as e:
        if DEBUG_LOGGING:
            log(f"Config load error: {e}")
        return {
            'enabled': False,
            'email_enabled': True,
            'identity_email_enabled': False,
            'email_to': '',
            'email_from': 'devicemonitor@opnsense.local',
            'webhook_enabled': False,
            'webhook_url': '',
            'scan_interval': 300,
            'email_vlans':  '',
            'webhook_vlans': '',
            'targeted_nmap_enabled': True,
            'nmap_top_ports': 100,
            'nmap_timing': 4,
            'nmap_host_timeout': 45,
            'nmap_version_detection': True,
            'nmap_max_per_cycle': 2,
            'apiEmailUrl': PATHS.get('apiEmailUrl'),
            'apiWebhookUrl': PATHS.get('apiWebhookUrl')
        }




def init_db():
    """Initialize database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS devices (
        mac TEXT PRIMARY KEY,
        ip TEXT,
        hostname TEXT,
        vendor TEXT,
        vlan TEXT,
        last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
        notified INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 0,
        notification_pending INTEGER DEFAULT 0
    )''')

    # Add missing columns for backward compatibility
    try:
        c.execute('ALTER TABLE devices ADD COLUMN first_seen DATETIME DEFAULT CURRENT_TIMESTAMP')
    except:
        pass

    try:
        c.execute('ALTER TABLE devices ADD COLUMN custom_hostname TEXT DEFAULT NULL')
    except:
        pass

    try:
        c.execute('ALTER TABLE devices ADD COLUMN nmap_scan_pending INTEGER DEFAULT 0')
    except:
        pass

    try:
        c.execute('ALTER TABLE devices ADD COLUMN nmap_scan_attempts INTEGER DEFAULT 0')
    except:
        pass

    try:
        c.execute('ALTER TABLE devices ADD COLUMN nmap_next_attempt DATETIME DEFAULT NULL')
    except:
        pass

    try:
        c.execute('ALTER TABLE devices ADD COLUMN nmap_last_error TEXT DEFAULT NULL')
    except:
        pass

    # Tombstones for manually deleted devices. Historical Hostwatch records
    # must not immediately recreate a device that the user removed.
    c.execute('''CREATE TABLE IF NOT EXISTS deleted_devices (
        mac TEXT PRIMARY KEY,
        last_seen DATETIME,
        deleted_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # Permanent MAC history used to distinguish genuinely new devices from
    # previously known devices that have been deleted or recreated.
    c.execute('''CREATE TABLE IF NOT EXISTS known_macs (
        mac TEXT PRIMARY KEY,
        first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # Audit history for every targeted Nmap execution.
    c.execute('''CREATE TABLE IF NOT EXISTS nmap_scan_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mac TEXT NOT NULL,
        ip TEXT,
        scan_type TEXT NOT NULL,
        started_at DATETIME NOT NULL,
        finished_at DATETIME,
        success INTEGER,
        error TEXT,
        top_ports INTEGER,
        timing INTEGER,
        host_timeout INTEGER,
        version_detection INTEGER,
        nmap_version TEXT,
        nmap_elapsed REAL,
        os_hint TEXT,
        open_port_count INTEGER,
        email_sent INTEGER,
        email_error TEXT
    )''')

    # Add v2.6 history metadata columns to existing databases.
    history_columns = {
        row[1]
        for row in c.execute('PRAGMA table_info(nmap_scan_history)')
    }
    history_migrations = {
        'top_ports': 'INTEGER',
        'timing': 'INTEGER',
        'host_timeout': 'INTEGER',
        'version_detection': 'INTEGER',
        'nmap_version': 'TEXT',
        'nmap_elapsed': 'REAL',
        'os_hint': 'TEXT',
        'open_port_count': 'INTEGER',
        'email_sent': 'INTEGER',
        'email_error': 'TEXT',
    }
    for column, definition in history_migrations.items():
        if column not in history_columns:
            c.execute(
                f'ALTER TABLE nmap_scan_history '
                f'ADD COLUMN {column} {definition}'
            )

    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_nmap_scan_history_mac_started
        ON nmap_scan_history(mac, started_at DESC)
    ''')

    # Structured open-port results for each targeted scan.
    c.execute('''CREATE TABLE IF NOT EXISTS nmap_scan_ports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_history_id INTEGER NOT NULL,
        port INTEGER NOT NULL,
        protocol TEXT NOT NULL,
        state TEXT NOT NULL,
        service TEXT,
        product TEXT,
        version TEXT,
        extra_info TEXT,
        FOREIGN KEY(scan_history_id)
            REFERENCES nmap_scan_history(id)
            ON DELETE CASCADE,
        UNIQUE(scan_history_id, port, protocol)
    )''')

    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_nmap_scan_ports_history
        ON nmap_scan_ports(scan_history_id)
    ''')

    # Persistent infrastructure-service inventory.
    #
    # This is deliberately separate from individual Nmap scan history:
    # scan history records what one scan observed; device_services records
    # the latest known service role for a device.
    c.execute('''CREATE TABLE IF NOT EXISTS device_services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mac TEXT,
        ip TEXT NOT NULL,
        interface TEXT NOT NULL DEFAULT '',
        service_type TEXT NOT NULL,
        port INTEGER NOT NULL,
        protocol TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'available',
        detection_method TEXT NOT NULL,
        confidence TEXT NOT NULL,
        product TEXT,
        version TEXT,
        first_detected DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_verified DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(ip, service_type, port, protocol, detection_method, interface)
    )''')

    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_device_services_mac
        ON device_services(mac)
    ''')

    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_device_services_type
        ON device_services(service_type)
    ''')
    c.execute('''CREATE TABLE IF NOT EXISTS service_discovery_state (
        id INTEGER PRIMARY KEY CHECK(id = 1),
        last_run DATETIME
    )''')

    c.execute(
        '''
        INSERT OR IGNORE INTO service_discovery_state (id, last_run)
        VALUES (1, NULL)
        '''
    )
    # Observational identity anomaly events. v2.7 Phase A records evidence
    # only; it does not automatically alert, block, merge, or delete devices.
    c.execute('''CREATE TABLE IF NOT EXISTS device_identity_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mac TEXT NOT NULL,
        event_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        detected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        ip TEXT,
        other_ip TEXT,
        other_mac TEXT,
        interface TEXT,
        other_interface TEXT,
        details TEXT,
        resolved_at DATETIME
    )''')

    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_device_identity_events_mac_detected
        ON device_identity_events(mac, detected_at DESC)
    ''')

    identity_columns = {
        row[1]
        for row in c.execute('PRAGMA table_info(device_identity_events)')
    }
    if 'other_mac' not in identity_columns:
        c.execute(
            'ALTER TABLE device_identity_events '
            'ADD COLUMN other_mac TEXT'
        )

    # Seed historical MACs from both active and deleted device records.
    c.execute('''
        INSERT OR IGNORE INTO known_macs (mac, first_seen, last_seen)
        SELECT lower(trim(mac)), first_seen, last_seen
        FROM devices
        WHERE mac IS NOT NULL AND trim(mac) <> ''
    ''')

    c.execute('''
        INSERT OR IGNORE INTO known_macs (mac, first_seen, last_seen)
        SELECT lower(trim(mac)), last_seen, last_seen
        FROM deleted_devices
        WHERE mac IS NOT NULL AND trim(mac) <> ''
    ''')

    conn.commit()
    conn.close()


def get_hostwatch_devices():
    """Load devices directly from the OPNsense Hostwatch database"""
    devices = []

    if not os.path.exists(HOSTWATCH_DB):
        log("ERROR: Hostwatch database does not exist: " + HOSTWATCH_DB)
        return devices

    try:
        conn = sqlite3.connect(f'file:{HOSTWATCH_DB}?mode=ro', uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                interface_name,
                ip_address,
                ether_address,
                first_seen,
                last_seen,
                organization_name
            FROM v_hosts
            WHERE protocol = 'inet'
              AND ether_address NOT IN ('ff:ff:ff:ff:ff:ff', '00:00:00:00:00:00')
              AND ip_address NOT LIKE '169.254.%'
              AND NOT EXISTS (
                  SELECT 1
                  FROM v_hosts newer
                  WHERE newer.ether_address = v_hosts.ether_address
                    AND newer.protocol = 'inet'
                    AND (
                        newer.last_seen > v_hosts.last_seen
                        OR (
                            newer.last_seen = v_hosts.last_seen
                            AND newer.id > v_hosts.id
                        )
                    )
              )
            ORDER BY last_seen DESC
        ''')

        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            mac = (row['ether_address'] or '').lower().strip()
            if not mac:
                continue

            # Mapuj interface_name na VLAN popis
            iface = row['interface_name'] or ''
            vlan = map_interface_to_vlan(iface)

            vendor = row['organization_name'] or 'Unknown'
            if len(vendor) > 40:
                vendor = vendor[:37] + '...'

            devices.append({
                'mac': mac,
                'ip': row['ip_address'] or '',
                'hostname': '',
                'vendor': vendor,
                'vlan': vlan,
                'first_seen': row['first_seen'] or '',
                'last_seen': row['last_seen'] or '',
            })

        log(f"Hostwatch DB: loaded {len(devices)} devices")

    except Exception as e:
        log(f"Error reading Hostwatch DB: {e}")

    return devices


def map_interface_to_vlan(interface_name):
    """Convert interface_name such as vlan0.11 to a readable label such as VLAN11"""
    if not interface_name:
        return 'Unknown'

    # vlan0.11 → VLAN11
    match = re.search(r'vlan\d+\.(\d+)', interface_name, re.I)
    if match:
        return 'VLAN' + match.group(1)

    # igc0, igc1 → interface name
    return interface_name.upper()


def is_locally_administered_mac(mac):
    """Return True when the IEEE locally-administered bit is set."""
    try:
        first_octet = int((mac or '').split(':')[0], 16)
        return bool(first_octet & 0x02)
    except (ValueError, IndexError):
        return False

def get_dhcp_descriptions():
    """Load device labels from DHCP static mappings (/conf/config.xml)"""
    descriptions = {}
    try:
        tree = ET.parse('/conf/config.xml')
        root = tree.getroot()
        dhcpd = root.find('dhcpd')
        if dhcpd is None:
            return descriptions

        for iface in dhcpd:
            # Skip disabled ISC DHCP interfaces
            enable_el = iface.find('enable')
            if enable_el is None:
                continue
            for staticmap in iface.findall('staticmap'):
                mac_el = staticmap.find('mac')
                hostname_el = staticmap.find('hostname')
                descr_el = staticmap.find('descr')
                if mac_el is not None and mac_el.text:
                    mac = mac_el.text.lower().strip()
                    # Preferuj hostname, fallback na descr
                    if hostname_el is not None and hostname_el.text:
                        descriptions[mac] = hostname_el.text.strip()
                    elif descr_el is not None and descr_el.text:
                        descriptions[mac] = descr_el.text.strip()

        log(f"DHCP labels: {len(descriptions)} records")
    except Exception as e:
        log(f"Error reading config.xml: {e}")
    return descriptions

def get_dnsmasq_descriptions():
    """Load device labels from Dnsmasq Host Overrides (/conf/config.xml)"""
    descriptions = {}
    try:
        tree = ET.parse('/conf/config.xml')
        root = tree.getroot()
        dnsmasq = root.find('dnsmasq')
        if dnsmasq is None:
            return descriptions

        for host in dnsmasq.findall('hosts'):
            hw_el = host.find('hwaddr')
            host_el = host.find('host')
            descr_el = host.find('descr')
            if hw_el is not None and hw_el.text:
                mac = hw_el.text.lower().strip()
                # Preferuj host (hostname), fallback na descr
                if host_el is not None and host_el.text:
                    descriptions[mac] = host_el.text.strip()
                elif descr_el is not None and descr_el.text:
                    descriptions[mac] = descr_el.text.strip()

        log(f"Dnsmasq labels: {len(descriptions)} records")
    except Exception as e:
        log(f"Error reading Dnsmasq config.xml: {e}")
    return descriptions

KEA_READ_ONLY_COMMANDS = {
    'list-commands',
    'lease4-get-all',
}


def query_kea_command(command, timeout=5):
    """Run an approved read-only Kea command and return its JSON response."""
    if command not in KEA_READ_ONLY_COMMANDS:
        raise ValueError(f'Kea command is not approved as read-only: {command}')

    kea_socket = '/var/run/kea/kea4-ctrl-socket'
    request = json.dumps({'command': command}).encode() + bytes([10])

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        sock.connect(kea_socket)
        sock.sendall(request)

        response = b''
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            response += chunk

    return json.loads(response.decode())


def get_kea_ipv4_leases():
    """Return normalized Kea DHCPv4 leases without changing Kea state."""
    try:
        payload = query_kea_command('lease4-get-all')
    except Exception as e:
        log(f'Kea lease query failed: {e}')
        return []

    if payload.get('result') != 0:
        log(f'Kea lease query returned result {payload.get("result")}')
        return []

    leases = []
    now_ts = int(datetime.now(UTC).timestamp())

    for raw in (payload.get('arguments') or {}).get('leases') or []:
        ip = (raw.get('ip-address') or '').strip()
        mac = (raw.get('hw-address') or '').strip().lower()

        if not ip or not mac:
            continue

        try:
            parsed_ip = ipaddress.ip_address(ip)
            if parsed_ip.version != 4:
                continue
        except ValueError:
            continue

        cltt = int(raw.get('cltt') or 0)
        valid_lft = int(raw.get('valid-lft') or 0)
        expires_at = cltt + valid_lft if cltt and valid_lft else 0
        state = int(raw.get('state') or 0)

        leases.append({
            'ip': ip,
            'mac': mac,
            'hostname': (raw.get('hostname') or '').strip(),
            'subnet_id': raw.get('subnet-id'),
            'state': state,
            'cltt': cltt,
            'valid_lft': valid_lft,
            'expires_at': expires_at,
            'active': state == 0 and (expires_at == 0 or expires_at > now_ts),
        })

    return leases

def get_recent_hostwatch_ipv4_observations(minutes=15):
    """Return recent IPv4 Hostwatch observations without changing state."""
    if not os.path.exists(HOSTWATCH_DB):
        return []

    observations = []

    try:
        with sqlite3.connect(f'file:{HOSTWATCH_DB}?mode=ro', uri=True) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute('''
                SELECT interface_name, ip_address, ether_address,
                       first_seen, last_seen
                FROM v_hosts
                WHERE ether_address NOT IN
                      ('ff:ff:ff:ff:ff:ff', '00:00:00:00:00:00')
            ''').fetchall()
    except Exception as e:
        log(f'Hostwatch correlation query failed: {e}')
        return []

    for row in rows:
        ip = (row['ip_address'] or '').strip()
        mac = (row['ether_address'] or '').strip().lower()
        last_seen = row['last_seen'] or ''

        if not ip or not mac or not is_recently_seen(last_seen, minutes):
            continue

        try:
            parsed_ip = ipaddress.ip_address(ip)
            if parsed_ip.version != 4:
                continue
        except ValueError:
            continue

        if ip.startswith('169.254.'):
            continue

        observations.append({
            'ip': ip,
            'mac': mac,
            'interface': row['interface_name'] or '',
            'first_seen': row['first_seen'] or '',
            'last_seen': last_seen,
        })

    return observations


def correlate_hostwatch_kea(minutes=15):
    """Compare recent Hostwatch identity evidence with active Kea leases."""
    hostwatch = get_recent_hostwatch_ipv4_observations(minutes)
    kea_leases = [lease for lease in get_kea_ipv4_leases() if lease['active']]

    hostwatch_by_ip = {}
    for observation in hostwatch:
        hostwatch_by_ip.setdefault(observation['ip'], []).append(observation)

    for observations in hostwatch_by_ip.values():
        observations.sort(key=lambda item: item['last_seen'], reverse=True)

    kea_by_ip = {lease['ip']: lease for lease in kea_leases}

    agreement = []
    hostwatch_only = []
    kea_only = []
    mismatch = []
    mixed = []

    all_ips = sorted(set(hostwatch_by_ip) | set(kea_by_ip))

    for ip in all_ips:
        observations = hostwatch_by_ip.get(ip, [])
        lease = kea_by_ip.get(ip)

        if lease is None:
            hostwatch_only.extend(observations)
            continue

        if not observations:
            kea_only.append({
                'ip': ip,
                'mac': lease['mac'],
                'hostname': lease['hostname'],
                'subnet_id': lease['subnet_id'],
                'cltt': lease['cltt'],
                'expires_at': lease['expires_at'],
            })
            continue

        matching = [
            observation for observation in observations
            if observation['mac'] == lease['mac']
        ]
        conflicting = [
            observation for observation in observations
            if observation['mac'] != lease['mac']
        ]

        if matching and conflicting:
            mixed.append({
                'ip': ip,
                'kea_mac': lease['mac'],
                'kea_hostname': lease['hostname'],
                'kea_subnet_id': lease['subnet_id'],
                'matching_observations': matching,
                'conflicting_observations': conflicting,
            })
        elif matching:
            newest = matching[0]
            agreement.append({
                'ip': ip,
                'mac': lease['mac'],
                'interface': newest['interface'],
                'hostwatch_last_seen': newest['last_seen'],
                'kea_hostname': lease['hostname'],
                'kea_subnet_id': lease['subnet_id'],
            })
        else:
            mismatch.append({
                'ip': ip,
                'kea_mac': lease['mac'],
                'kea_hostname': lease['hostname'],
                'kea_subnet_id': lease['subnet_id'],
                'hostwatch_observations': observations,
            })

    return {
        'window_minutes': minutes,
        'agreement': agreement,
        'hostwatch_only': hostwatch_only,
        'kea_only': kea_only,
        'mismatch': mismatch,
        'mixed': mixed,
    }

def is_process_running(process_name):
    """Return True when an exact process name is currently running."""
    try:
        return subprocess.run(
            ['pgrep', '-x', process_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode == 0
    except Exception:
        return False

def detect_source_capabilities():
    """Report available identity/enrichment sources without changing state."""
    capabilities = {
        'hostwatch': {
            'path': HOSTWATCH_DB,
            'configured': bool(HOSTWATCH_DB),
            'readable': bool(HOSTWATCH_DB and os.path.isfile(HOSTWATCH_DB)
                             and os.access(HOSTWATCH_DB, os.R_OK)),
        },
        'kea': {
            'configured': False,
            'enabled': False,
            'active': False,
            'socket_present': False,
            'queryable': False,
            'lease4_get_all': False,
        },
        'isc': {
            'configured': False,
            'enabled': False,
            'active': False,
        },
        'dnsmasq': {
            'configured': False,
            'active': False,
        },
    }

    try:
        root = ET.parse('/conf/config.xml').getroot()

        isc = root.find('dhcpd')
        capabilities['isc']['configured'] = isc is not None
        if isc is not None:
            capabilities['isc']['enabled'] = any(
                iface.find('enable') is not None for iface in isc
            )

        capabilities['dnsmasq']['configured'] = (
            root.find('dnsmasq') is not None
        )

        kea = root.find('./OPNsense/Kea')
        if kea is not None:
            dhcp4 = kea.find('dhcp4')
            capabilities['kea']['configured'] = dhcp4 is not None
            if dhcp4 is not None:
                enabled_el = dhcp4.find('./general/enabled')
                capabilities['kea']['enabled'] = (
                    enabled_el is not None
                    and (enabled_el.text or '').strip() == '1'
                )
    except Exception as e:
        log(f'Source capability config check failed: {e}')

    capabilities['kea']['active'] = is_process_running('kea-dhcp4')
    capabilities['isc']['active'] = is_process_running('dhcpd')
    capabilities['dnsmasq']['active'] = is_process_running('dnsmasq')

    kea_socket = '/var/run/kea/kea4-ctrl-socket'
    capabilities['kea']['socket_present'] = os.path.exists(kea_socket)

    if capabilities['kea']['socket_present']:
        try:
            payload = query_kea_command('list-commands', timeout=2)
            capabilities['kea']['queryable'] = payload.get('result') == 0
            commands = payload.get('arguments') or []
            capabilities['kea']['lease4_get_all'] = (
                'lease4-get-all' in commands
            )
        except Exception as e:
            log(f'Kea capability query failed: {e}')

    capabilities['core_identity_source'] = (
        'hostwatch' if capabilities['hostwatch']['readable'] else 'unavailable'
    )

    capabilities['active_dhcp_services'] = [
        name for name in ('kea', 'isc', 'dnsmasq')
        if capabilities[name]['active']
    ]

    return capabilities

def is_recently_seen(last_seen_str, minutes=15):
    """True if the device was seen within the last N minutes using UTC comparison"""
    if not last_seen_str:
        return False
    try:
        last_seen = datetime.strptime(last_seen_str, '%Y-%m-%d %H:%M:%S')
        now_utc = datetime.now(UTC).replace(tzinfo=None)
        return (now_utc - last_seen).total_seconds() < minutes * 60
    except:
        return False


def upsert_device_service(
    conn,
    mac,
    ip,
    interface,
    service_type,
    port,
    protocol,
    detection_method,
    confidence,
    verified_at,
    status='available',
    product='',
    version=''
):
    """Insert or refresh one infrastructure-service endpoint."""
    mac = (mac or '').strip().lower() or None
    ip = (ip or '').strip()
    interface = (interface or '').strip()
    service_type = (service_type or '').strip().upper()
    protocol = (protocol or '').strip().lower()
    detection_method = (detection_method or '').strip()

    if not ip or not service_type or not protocol or not detection_method:
        return False

    conn.execute(
        '''
        INSERT INTO device_services (
            mac,
            ip,
            interface,
            service_type,
            port,
            protocol,
            status,
            detection_method,
            confidence,
            product,
            version,
            first_detected,
            last_verified
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(
            ip,
            service_type,
            port,
            protocol,
            detection_method,
            interface
        )
        DO UPDATE SET
            mac = COALESCE(excluded.mac, device_services.mac),
            status = excluded.status,
            confidence = excluded.confidence,
            product = excluded.product,
            version = excluded.version,
            last_verified = excluded.last_verified
        ''',
        (
            mac,
            ip,
            interface,
            service_type,
            int(port),
            protocol,
            status,
            detection_method,
            confidence,
            product or '',
            version or '',
            verified_at,
            verified_at,
        )
    )

    return True


def update_service_inventory_from_nmap(
    conn,
    mac,
    ip,
    interface,
    services,
    verified_at
):
    """Update infrastructure-service roles positively identified by Nmap."""
    recorded = 0

    for item in services or []:
        try:
            port = int(item.get('port'))
        except (TypeError, ValueError):
            continue

        protocol = str(item.get('protocol') or '').strip().lower()
        state = str(item.get('state') or '').strip().lower()
        service_name = str(item.get('service') or '').strip().lower()

        if state != 'open':
            continue

        # Port 53 by itself is not proof of DNS. Require Nmap service
        # identification as DNS/domain.
        if (
            port == 53
            and protocol in ('tcp', 'udp')
            and service_name in ('domain', 'dns')
        ):
            if upsert_device_service(
                conn,
                mac,
                ip,
                interface,
                'DNS',
                port,
                protocol,
                'nmap_service',
                'discovered',
                verified_at,
                product=str(item.get('product') or '').strip(),
                version=str(item.get('version') or '').strip()
            ):
                recorded += 1

    return recorded


def discover_dns_servers(timeout=1.5):
    """
    Verify DNS servers using one real UDP DNS query per active IPv4 device.

    A device is recorded only when it returns a syntactically valid DNS
    response with the matching transaction ID.
    """
    init_db()

    with sqlite3.connect(DB_FILE) as conn:
        rows = conn.execute(
            '''
            SELECT mac, ip, vlan, is_active
            FROM devices
            WHERE ip IS NOT NULL
              AND TRIM(ip) <> ''
            ORDER BY last_seen DESC
            '''
        ).fetchall()

        candidates = []
        seen_ips = set()
        device_by_ip = {}

        def add_dns_candidate(ip, mac=None, interface=''):
            ip = str(ip or '').strip()

            try:
                parsed = ipaddress.ip_address(ip)
            except ValueError:
                return

            if parsed.version != 4:
                return

            if (
                parsed.is_loopback
                or parsed.is_link_local
                or parsed.is_multicast
                or parsed.is_unspecified
            ):
                return

            if ip in seen_ips:
                return

            seen_ips.add(ip)

            candidates.append({
                'mac': (mac or '').strip().lower() or None,
                'ip': ip,
                'interface': (interface or '').strip()
            })

        # Build endpoint metadata from every known Device Monitor record.
        # Active devices are always DNS-verification candidates.
        for mac, ip, interface, is_active in rows:
            ip = str(ip or '').strip()

            if not ip:
                continue

            if ip not in device_by_ip:
                device_by_ip[ip] = {
                    'mac': (mac or '').strip().lower() or None,
                    'interface': (interface or '').strip()
                }

            if int(is_active or 0) == 1:
                add_dns_candidate(
                    ip,
                    mac,
                    interface
                )

        # Re-test every DNS endpoint previously verified by Device Monitor.
        # This lets a previously available resolver transition to unavailable
        # even when its owning device is now considered offline.
        known_dns = conn.execute(
            '''
            SELECT mac, ip, interface
            FROM device_services
            WHERE service_type = 'DNS'
              AND detection_method = 'dns_query'
            '''
        ).fetchall()

        for known_mac, known_ip, known_interface in known_dns:
            add_dns_candidate(
                known_ip,
                known_mac,
                known_interface
            )
        # Also verify resolvers configured on OPNsense itself. Infrastructure
        # services must not disappear merely because the endpoint is currently
        # considered offline by Device Monitor.
        try:
            with open(
                '/etc/resolv.conf',
                'r',
                encoding='utf-8',
                errors='ignore'
            ) as resolver_file:
                for line in resolver_file:
                    line = line.split('#', 1)[0].strip()

                    if not line.lower().startswith('nameserver '):
                        continue

                    parts = line.split()

                    if len(parts) < 2:
                        continue

                    resolver_ip = parts[1].strip()

                    try:
                        parsed = ipaddress.ip_address(resolver_ip)
                    except ValueError:
                        continue

                    if parsed.version != 4:
                        continue

                    metadata = device_by_ip.get(
                        resolver_ip,
                        {}
                    )

                    # Avoid inventorying an arbitrary public upstream as a
                    # local infrastructure device unless it already belongs
                    # to Device Monitor.
                    if not parsed.is_private and not metadata:
                        continue

                    add_dns_candidate(
                        resolver_ip,
                        metadata.get('mac'),
                        metadata.get('interface', '')
                    )

        except OSError as e:
            log(
                "[SERVICES] Unable to read configured DNS "
                f"resolvers: {e}"
            )

        if not candidates:
            return []

        log(
            "[SERVICES] DNS verification starting for "
            f"{len(candidates)} active IPv4 device(s)"
        )

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)

        pending = {}

        # example.com A query. We care about receiving a valid DNS
        # response, not what answer the resolver returns.
        qname = (
            b'\x07example'
            b'\x03com'
            b'\x00'
        )

        try:
            for candidate in candidates:
                # Generate a transaction ID not currently in use.
                for _ in range(100):
                    txid = int.from_bytes(os.urandom(2), 'big')
                    if txid not in pending:
                        break
                else:
                    continue

                packet = (
                    struct.pack(
                        '!HHHHHH',
                        txid,
                        0x0100,  # recursion desired
                        1,
                        0,
                        0,
                        0
                    )
                    + qname
                    + struct.pack('!HH', 1, 1)  # A / IN
                )

                try:
                    sock.sendto(
                        packet,
                        (candidate['ip'], 53)
                    )
                    pending[txid] = candidate
                except OSError:
                    continue

            found = []
            verified_ips = set()
            deadline = time.monotonic() + float(timeout)

            while pending:
                remaining = deadline - time.monotonic()

                if remaining <= 0:
                    break

                readable, _, _ = select.select(
                    [sock],
                    [],
                    [],
                    remaining
                )

                if not readable:
                    break

                try:
                    data, source = sock.recvfrom(4096)
                except OSError:
                    continue

                if len(data) < 12:
                    continue

                try:
                    (
                        rxid,
                        flags,
                        _questions,
                        _answers,
                        _authority,
                        _additional
                    ) = struct.unpack('!HHHHHH', data[:12])
                except struct.error:
                    continue

                candidate = pending.get(rxid)

                if candidate is None:
                    continue

                # The reply must come from the device that was queried.
                if source[0] != candidate['ip']:
                    continue

                # QR flag = this is a DNS response, not another query.
                if not (flags & 0x8000):
                    continue

                verified_at = datetime.now().strftime(
                    '%Y-%m-%d %H:%M:%S'
                )

                if upsert_device_service(
                    conn,
                    candidate['mac'],
                    candidate['ip'],
                    candidate['interface'],
                    'DNS',
                    53,
                    'udp',
                    'dns_query',
                    'verified',
                    verified_at
                ):
                    item = {
                        'service_type': 'DNS',
                        'ip': candidate['ip'],
                        'mac': candidate['mac'],
                        'interface': candidate['interface'],
                        'port': 53,
                        'protocol': 'udp',
                        'confidence': 'verified'
                    }

                    found.append(item)
                    verified_ips.add(candidate['ip'])

                    log(
                        "[SERVICES] DNS server verified: "
                        f"{candidate['ip']}"
                    )

                del pending[rxid]

            # Every candidate was actively queried during this run. Existing
            # dns_query inventory entries that did not answer are no longer
            # considered currently available. Preserve last_verified so the
            # UI can still show when the endpoint was last known-good.
            for candidate in candidates:
                candidate_ip = candidate['ip']

                if candidate_ip in verified_ips:
                    continue

                changed = conn.execute(
                    '''
                    UPDATE device_services
                    SET status = 'unavailable'
                    WHERE service_type = 'DNS'
                      AND detection_method = 'dns_query'
                      AND ip = ?
                      AND status <> 'unavailable'
                    ''',
                    (candidate_ip,)
                ).rowcount

                if changed:
                    log(
                        "[SERVICES] DNS server unavailable: "
                        f"{candidate_ip}"
                    )

            conn.commit()
            return found

        finally:
            sock.close()

def discover_dhcp_servers():
    """
    Actively discover DHCPv4 servers by DHCP OFFER.

    Only interfaces already represented by Device Monitor devices are probed.
    A DHCP server is recorded only when broadcast-dhcp-discover returns a
    Server Identifier IPv4 address.
    """
    init_db()

    with sqlite3.connect(DB_FILE) as conn:
        monitored = [
            str(row[0]).strip()
            for row in conn.execute(
                '''
                SELECT DISTINCT vlan
                FROM devices
                WHERE vlan IS NOT NULL
                  AND TRIM(vlan) <> ''
                '''
            )
            if row[0]
        ]

        try:
            result = subprocess.run(
                ['/sbin/ifconfig', '-l'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                log("[SERVICES] Unable to enumerate interfaces")
                return []

            actual_interfaces = {
                item.lower(): item
                for item in result.stdout.split()
            }
        except Exception as e:
            log(f"[SERVICES] Interface enumeration failed: {e}")
            return []

        excluded = {
            'lo0',
            'enc0',
            'pflog0',
            'pfsync0'
        }

        interfaces = []
        for configured in monitored:
            real_name = actual_interfaces.get(configured.lower())
            if not real_name:
                continue
            if real_name.lower() in excluded:
                continue
            if real_name not in interfaces:
                interfaces.append(real_name)

        found = []
        tested_interfaces = set()
        verified_by_interface = {}
        verified_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for interface in interfaces:
            cmd = [
                '/usr/local/bin/nmap',
                '--script', 'broadcast-dhcp-discover',
                '-e', interface,
                '-oX', '-'
            ]

            log(
                f"[SERVICES] DHCP discovery starting on {interface}"
            )

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=20
                )
            except subprocess.TimeoutExpired:
                log(
                    f"[SERVICES] DHCP discovery timeout on {interface}"
                )
                continue
            except Exception as e:
                log(
                    f"[SERVICES] DHCP discovery failed on "
                    f"{interface}: {e}"
                )
                continue

            if result.returncode != 0:
                log(
                    f"[SERVICES] DHCP discovery returned "
                    f"{result.returncode} on {interface}"
                )
                continue

            tested_interfaces.add(interface)
            output = result.stdout or ''

            # Nmap XML stores NSE output in script attributes. Looking at
            # the complete XML text also covers structured/script variations.
            candidates = re.findall(
                r'Server Identifier(?:\s*\([^)]*\))?'
                r'[^0-9]+'
                r'((?:\d{1,3}\.){3}\d{1,3})',
                output,
                flags=re.IGNORECASE
            )

            for server_ip in candidates:
                try:
                    parsed = ipaddress.ip_address(server_ip)
                    if parsed.version != 4:
                        continue
                except ValueError:
                    continue

                mac_row = conn.execute(
                    '''
                    SELECT mac
                    FROM devices
                    WHERE ip = ?
                    ORDER BY last_seen DESC
                    LIMIT 1
                    ''',
                    (server_ip,)
                ).fetchone()

                server_mac = mac_row[0] if mac_row else None

                if upsert_device_service(
                    conn,
                    server_mac,
                    server_ip,
                    interface,
                    'DHCP',
                    67,
                    'udp',
                    'dhcp_offer',
                    'verified',
                    verified_at
                ):
                    item = {
                        'service_type': 'DHCP',
                        'ip': server_ip,
                        'mac': server_mac,
                        'interface': interface,
                        'port': 67,
                        'protocol': 'udp',
                        'confidence': 'verified'
                    }

                    if item not in found:
                        found.append(item)

                    verified_by_interface.setdefault(
                        interface,
                        set()
                    ).add(server_ip)

                    log(
                        f"[SERVICES] DHCP server verified: "
                        f"{server_ip} via {interface}"
                    )

        for interface in tested_interfaces:
            verified_ips = verified_by_interface.get(
                interface,
                set()
            )

            known_rows = conn.execute(
                '''
                SELECT ip
                FROM device_services
                WHERE service_type = 'DHCP'
                  AND detection_method = 'dhcp_offer'
                  AND LOWER(interface) = LOWER(?)
                ''',
                (interface,)
            ).fetchall()

            for row in known_rows:
                known_ip = str(row[0] or '').strip()

                if not known_ip or known_ip in verified_ips:
                    continue

                changed = conn.execute(
                    '''
                    UPDATE device_services
                    SET status = 'unavailable'
                    WHERE service_type = 'DHCP'
                      AND detection_method = 'dhcp_offer'
                      AND ip = ?
                      AND LOWER(interface) = LOWER(?)
                      AND status <> 'unavailable'
                    ''',
                    (known_ip, interface)
                ).rowcount

                if changed:
                    log(
                        "[SERVICES] DHCP server unavailable: "
                        f"{known_ip} via {interface}"
                    )

        conn.commit()
        return found


def _valid_service_probe_ipv4(ip):
    """Return True for usable IPv4 service-discovery targets."""
    try:
        address = ipaddress.ip_address((ip or '').strip())
    except ValueError:
        return False

    return (
        address.version == 4
        and not address.is_unspecified
        and not address.is_loopback
        and not address.is_multicast
    )


def _service_probe_candidates(conn, limit=128):
    """
    Build a bounded set of IPv4 endpoints for infrastructure probing.

    Includes currently active Device Monitor devices plus endpoints already
    known to host infrastructure services.
    """
    candidates = {}

    def add_candidate(mac, ip, interface):
        ip = (ip or '').strip()

        if not _valid_service_probe_ipv4(ip):
            return

        mac = (mac or '').strip().lower()
        interface = (interface or '').strip()

        existing = candidates.get(ip)

        if existing is None:
            candidates[ip] = {
                'mac': mac,
                'interface': interface
            }
            return

        if not existing.get('mac') and mac:
            existing['mac'] = mac

        if not existing.get('interface') and interface:
            existing['interface'] = interface

    try:
        rows = conn.execute(
            '''
            SELECT mac, ip, vlan
            FROM devices
            WHERE is_active = 1
            ORDER BY last_seen DESC
            LIMIT ?
            ''',
            (int(limit),)
        ).fetchall()

        for mac, ip, interface in rows:
            add_candidate(mac, ip, interface)
    except Exception as e:
        log(f"[SERVICES] Unable to load active probe candidates: {e}")

    try:
        rows = conn.execute(
            '''
            SELECT mac, ip, interface
            FROM device_services
            ORDER BY last_verified DESC
            '''
        ).fetchall()

        for mac, ip, interface in rows:
            add_candidate(mac, ip, interface)
    except Exception as e:
        log(f"[SERVICES] Unable to load known service candidates: {e}")

    return candidates


def _nmap_tcp_service_candidates(conn):
    """Return bounded structured Nmap TCP service evidence."""
    try:
        tables = {
            row[0]
            for row in conn.execute(
                '''
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name IN ('nmap_scan_history', 'nmap_scan_ports')
                '''
            ).fetchall()
        }

        if {
            'nmap_scan_history',
            'nmap_scan_ports'
        } - tables:
            return []

        return conn.execute(
            '''
            SELECT DISTINCT
                h.ip,
                p.port,
                LOWER(COALESCE(p.service, ''))
            FROM nmap_scan_ports p
            JOIN nmap_scan_history h
              ON h.id = p.scan_history_id
            WHERE p.protocol = 'tcp'
              AND p.state = 'open'
              AND h.ip IS NOT NULL
              AND h.ip != ''
            ORDER BY h.id DESC
            LIMIT 1000
            '''
        ).fetchall()

    except Exception as e:
        log(f"[SERVICES] Unable to read Nmap service evidence: {e}")
        return []


def _probe_ntp_service(ip, timeout=0.8):
    """Verify NTP using a real client request and matching originate time."""
    request = bytearray(48)

    # LI=0, VN=4, Mode=3 (client)
    request[0] = 0x23

    ntp_now = time.time() + 2208988800
    seconds = int(ntp_now)
    fraction = int(
        (ntp_now - seconds) * 4294967296
    )

    struct.pack_into(
        '!II',
        request,
        40,
        seconds,
        fraction
    )

    expected_originate = bytes(request[40:48])

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.settimeout(timeout)
        sock.sendto(bytes(request), (ip, 123))

        data, source = sock.recvfrom(512)

        if source[0] != ip or len(data) < 48:
            return None

        mode = data[0] & 0x07
        version = (data[0] >> 3) & 0x07

        if mode != 4:
            return None

        # Server should echo our transmit timestamp as originate timestamp.
        if data[24:32] != expected_originate:
            return None

        return {
            'product': 'NTP',
            'version': f'v{version}'
        }

    except (OSError, socket.timeout):
        return None

    finally:
        sock.close()


def discover_ntp_servers():
    """Protocol-verify NTP servers on known infrastructure endpoints."""
    init_db()

    discovered = []
    verified = set()

    with sqlite3.connect(DB_FILE) as conn:
        candidates = _service_probe_candidates(conn)

        previous = conn.execute(
            '''
            SELECT DISTINCT ip
            FROM device_services
            WHERE service_type = 'NTP'
              AND detection_method = 'ntp_query'
            '''
        ).fetchall()

        for row in previous:
            ip = (row[0] or '').strip()

            if (
                _valid_service_probe_ipv4(ip)
                and ip not in candidates
            ):
                candidates[ip] = {
                    'mac': '',
                    'interface': ''
                }

        targets = sorted(candidates.keys())

        if targets:
            workers = min(16, len(targets))

            with ThreadPoolExecutor(max_workers=workers) as pool:
                results = list(
                    pool.map(_probe_ntp_service, targets)
                )

            verified_at = datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'
            )

            for ip, result in zip(targets, results):
                if result is None:
                    continue

                meta = candidates[ip]

                upsert_device_service(
                    conn,
                    meta.get('mac', ''),
                    ip,
                    meta.get('interface', ''),
                    'NTP',
                    123,
                    'udp',
                    'ntp_query',
                    'verified',
                    verified_at,
                    product=result.get('product', ''),
                    version=result.get('version', '')
                )

                verified.add(ip)

                discovered.append({
                    'service_type': 'NTP',
                    'ip': ip,
                    'mac': meta.get('mac', ''),
                    'interface': meta.get('interface', ''),
                    'port': 123,
                    'protocol': 'udp',
                    'detection_method': 'ntp_query',
                    'confidence': 'verified',
                    'product': result.get('product', ''),
                    'version': result.get('version', '')
                })

                log(
                    f"[SERVICES] NTP server verified: "
                    f"{ip}:123/udp"
                )

        tested = set(targets)

        for row in previous:
            ip = (row[0] or '').strip()

            if ip in tested and ip not in verified:
                conn.execute(
                    '''
                    UPDATE device_services
                    SET status = 'unavailable'
                    WHERE ip = ?
                      AND service_type = 'NTP'
                      AND detection_method = 'ntp_query'
                    ''',
                    (ip,)
                )

        conn.commit()

    log(
        f"[SERVICES] NTP discovery complete: "
        f"{len(discovered)} verified"
    )

    return discovered


def _probe_ssh_service(target, timeout=0.8):
    """Verify SSH by receiving an SSH protocol identification banner."""
    ip, port = target

    try:
        sock = socket.create_connection(
            (ip, port),
            timeout=timeout
        )
    except OSError:
        return None

    try:
        sock.settimeout(timeout)
        data = b''

        while len(data) < 1024:
            try:
                chunk = sock.recv(256)
            except socket.timeout:
                break

            if not chunk:
                break

            data += chunk

            for line in data.splitlines():
                if line.startswith(b'SSH-'):
                    banner = line.decode(
                        'ascii',
                        errors='replace'
                    ).strip()

                    parts = banner.split('-', 2)

                    software = (
                        parts[2]
                        if len(parts) >= 3
                        else banner
                    )

                    return {
                        'product': 'SSH',
                        'version': software
                    }

        return None

    except OSError:
        return None

    finally:
        sock.close()


def discover_ssh_servers():
    """Protocol-verify SSH services using server identification banners."""
    init_db()

    discovered = []
    verified = set()

    with sqlite3.connect(DB_FILE) as conn:
        candidates = _service_probe_candidates(conn)
        targets = {}

        # Standard SSH port on current/known infrastructure endpoints.
        for ip, meta in candidates.items():
            targets[(ip, 22)] = meta

        previous = conn.execute(
            '''
            SELECT DISTINCT ip, port, mac, interface
            FROM device_services
            WHERE service_type = 'SSH'
              AND detection_method = 'ssh_banner'
            '''
        ).fetchall()

        for ip, port, mac, interface in previous:
            ip = (ip or '').strip()

            try:
                port = int(port)
            except (TypeError, ValueError):
                continue

            if not _valid_service_probe_ipv4(ip):
                continue

            targets.setdefault(
                (ip, port),
                {
                    'mac': (mac or '').strip().lower(),
                    'interface': (interface or '').strip()
                }
            )

        # Reuse Nmap service/version evidence to find non-standard SSH ports,
        # but still require a real SSH banner before marking verified.
        for ip, port, service in _nmap_tcp_service_candidates(conn):
            ip = (ip or '').strip()

            try:
                port = int(port)
            except (TypeError, ValueError):
                continue

            if (
                service == 'ssh'
                and _valid_service_probe_ipv4(ip)
                and 1 <= port <= 65535
            ):
                targets.setdefault(
                    (ip, port),
                    candidates.get(
                        ip,
                        {
                            'mac': '',
                            'interface': ''
                        }
                    )
                )

        target_list = sorted(targets.keys())

        if target_list:
            workers = min(24, len(target_list))

            with ThreadPoolExecutor(max_workers=workers) as pool:
                results = list(
                    pool.map(_probe_ssh_service, target_list)
                )

            verified_at = datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'
            )

            for target, result in zip(target_list, results):
                if result is None:
                    continue

                ip, port = target
                meta = targets[target]

                upsert_device_service(
                    conn,
                    meta.get('mac', ''),
                    ip,
                    meta.get('interface', ''),
                    'SSH',
                    port,
                    'tcp',
                    'ssh_banner',
                    'verified',
                    verified_at,
                    product=result.get('product', ''),
                    version=result.get('version', '')
                )

                verified.add(target)

                discovered.append({
                    'service_type': 'SSH',
                    'ip': ip,
                    'mac': meta.get('mac', ''),
                    'interface': meta.get('interface', ''),
                    'port': port,
                    'protocol': 'tcp',
                    'detection_method': 'ssh_banner',
                    'confidence': 'verified',
                    'product': result.get('product', ''),
                    'version': result.get('version', '')
                })

                log(
                    f"[SERVICES] SSH server verified: "
                    f"{ip}:{port}/tcp "
                    f"{result.get('version', '')}"
                )

        tested = set(target_list)

        for ip, port, mac, interface in previous:
            try:
                key = ((ip or '').strip(), int(port))
            except (TypeError, ValueError):
                continue

            if key in tested and key not in verified:
                conn.execute(
                    '''
                    UPDATE device_services
                    SET status = 'unavailable'
                    WHERE ip = ?
                      AND port = ?
                      AND service_type = 'SSH'
                      AND detection_method = 'ssh_banner'
                    ''',
                    key
                )

        conn.commit()

    log(
        f"[SERVICES] SSH discovery complete: "
        f"{len(discovered)} verified"
    )

    return discovered


def _probe_web_service(target, timeout=0.6):
    """
    Verify an HTTP/HTTPS endpoint using a real request and HTTP response.
    TLS certificate validation is deliberately disabled because local
    infrastructure commonly uses private/self-signed certificates.
    """
    ip, port, scheme = target

    try:
        sock = socket.create_connection(
            (ip, port),
            timeout=timeout
        )
    except OSError:
        return None

    try:
        sock.settimeout(timeout)

        if scheme == 'https':
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            sock = context.wrap_socket(
                sock,
                server_hostname=ip
            )
            sock.settimeout(timeout)

        request = (
            f"GET / HTTP/1.0\r\n"
            f"Host: {ip}\r\n"
            f"User-Agent: OPNsense-DeviceMonitor/2.8\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        ).encode('ascii')

        sock.sendall(request)

        data = b''

        while len(data) < 8192:
            try:
                chunk = sock.recv(1024)
            except socket.timeout:
                break

            if not chunk:
                break

            data += chunk

            if b'\r\n\r\n' in data:
                break

        if not data:
            return None

        text = data.decode(
            'iso-8859-1',
            errors='replace'
        )

        lines = text.splitlines()

        if not lines or not lines[0].startswith('HTTP/'):
            return None

        server = ''

        for line in lines[1:]:
            if line.lower().startswith('server:'):
                server = line.split(':', 1)[1].strip()
                break

        product = scheme.upper()
        version = ''

        if server:
            if '/' in server:
                product, version = server.split('/', 1)
                product = product.strip()
                version = version.strip()
            else:
                product = server

        return {
            'product': product,
            'version': version
        }

    except (
        OSError,
        socket.timeout,
        ssl.SSLError
    ):
        return None

    finally:
        try:
            sock.close()
        except Exception:
            pass


def discover_web_admin_services():
    """
    Protocol-verify common Web/Admin HTTP and HTTPS endpoints.

    Common ports are tested on current infrastructure candidates.
    Structured Nmap HTTP service evidence adds non-standard ports, but a real
    HTTP response is still required before a service becomes verified.
    """
    init_db()

    discovered = []
    verified = set()

    with sqlite3.connect(DB_FILE) as conn:
        candidates = _service_probe_candidates(conn)
        targets = {}

        common_ports = (
            (80, 'http'),
            (443, 'https'),
            (8080, 'http'),
            (8443, 'https')
        )

        for ip, meta in candidates.items():
            for port, scheme in common_ports:
                targets[(ip, port, scheme)] = meta

        previous = conn.execute(
            '''
            SELECT DISTINCT
                ip,
                port,
                detection_method,
                mac,
                interface
            FROM device_services
            WHERE service_type = 'WEB_ADMIN'
              AND detection_method IN (
                  'http_response',
                  'https_response'
              )
            '''
        ).fetchall()

        for ip, port, method, mac, interface in previous:
            ip = (ip or '').strip()

            try:
                port = int(port)
            except (TypeError, ValueError):
                continue

            if not _valid_service_probe_ipv4(ip):
                continue

            scheme = (
                'https'
                if method == 'https_response'
                else 'http'
            )

            targets.setdefault(
                (ip, port, scheme),
                {
                    'mac': (mac or '').strip().lower(),
                    'interface': (interface or '').strip()
                }
            )

        secure_ports = {
            443,
            8443,
            9443,
            5001
        }

        for ip, port, service in _nmap_tcp_service_candidates(conn):
            ip = (ip or '').strip()

            try:
                port = int(port)
            except (TypeError, ValueError):
                continue

            if (
                'http' not in service
                or not _valid_service_probe_ipv4(ip)
                or port < 1
                or port > 65535
            ):
                continue

            scheme = (
                'https'
                if (
                    'https' in service
                    or 'ssl' in service
                    or port in secure_ports
                )
                else 'http'
            )

            targets.setdefault(
                (ip, port, scheme),
                candidates.get(
                    ip,
                    {
                        'mac': '',
                        'interface': ''
                    }
                )
            )

        target_list = sorted(targets.keys())

        if target_list:
            workers = min(32, len(target_list))

            with ThreadPoolExecutor(max_workers=workers) as pool:
                results = list(
                    pool.map(_probe_web_service, target_list)
                )

            verified_at = datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'
            )

            for target, result in zip(target_list, results):
                if result is None:
                    continue

                ip, port, scheme = target
                meta = targets[target]

                method = (
                    'https_response'
                    if scheme == 'https'
                    else 'http_response'
                )

                upsert_device_service(
                    conn,
                    meta.get('mac', ''),
                    ip,
                    meta.get('interface', ''),
                    'WEB_ADMIN',
                    port,
                    'tcp',
                    method,
                    'verified',
                    verified_at,
                    product=result.get('product', ''),
                    version=result.get('version', '')
                )

                verified.add(
                    (ip, port, method)
                )

                discovered.append({
                    'service_type': 'WEB_ADMIN',
                    'ip': ip,
                    'mac': meta.get('mac', ''),
                    'interface': meta.get('interface', ''),
                    'port': port,
                    'protocol': 'tcp',
                    'detection_method': method,
                    'confidence': 'verified',
                    'product': result.get('product', ''),
                    'version': result.get('version', '')
                })

                log(
                    f"[SERVICES] Web service verified: "
                    f"{scheme}://{ip}:{port}"
                )

        tested = {
            (
                ip,
                port,
                (
                    'https_response'
                    if scheme == 'https'
                    else 'http_response'
                )
            )
            for ip, port, scheme in target_list
        }

        for ip, port, method, mac, interface in previous:
            try:
                key = (
                    (ip or '').strip(),
                    int(port),
                    method
                )
            except (TypeError, ValueError):
                continue

            if key in tested and key not in verified:
                conn.execute(
                    '''
                    UPDATE device_services
                    SET status = 'unavailable'
                    WHERE ip = ?
                      AND port = ?
                      AND service_type = 'WEB_ADMIN'
                      AND detection_method = ?
                    ''',
                    key
                )

        conn.commit()

    log(
        f"[SERVICES] Web/Admin discovery complete: "
        f"{len(discovered)} verified"
    )

    return discovered


def discover_infrastructure_services():
    """Run all supported infrastructure-service discovery."""
    services = []

    discoveries = (
        ('DHCP', discover_dhcp_servers),
        ('DNS', discover_dns_servers),
        ('NTP', discover_ntp_servers),
        ('SSH', discover_ssh_servers),
        ('WEB_ADMIN', discover_web_admin_services),
    )

    for name, discovery in discoveries:
        try:
            found = discovery()

            if found:
                services.extend(found)

        except Exception as e:
            log(
                f"[SERVICES] {name} discovery failed: {e}"
            )

    completed_at = datetime.now().strftime(
        '%Y-%m-%d %H:%M:%S'
    )

    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                '''
                INSERT INTO service_discovery_state (id, last_run)
                VALUES (1, ?)
                ON CONFLICT(id)
                DO UPDATE SET last_run = excluded.last_run
                ''',
                (completed_at,)
            )
            conn.commit()

    except Exception as e:
        log(
            f"[SERVICES] Unable to update discovery state: {e}"
        )

    return services


def run_scheduled_service_discovery(interval_seconds=3600):
    """
    Run infrastructure discovery at most once per interval.

    Discovery failure is observational and must never make the normal
    Device Monitor scan fail.
    """
    try:
        init_db()

        with sqlite3.connect(DB_FILE) as conn:
            row = conn.execute(
                '''
                SELECT last_run
                FROM service_discovery_state
                WHERE id = 1
                '''
            ).fetchone()

        last_run = row[0] if row else None

        if last_run:
            try:
                last_dt = datetime.strptime(
                    last_run,
                    '%Y-%m-%d %H:%M:%S'
                )

                age = (
                    datetime.now() - last_dt
                ).total_seconds()

                if age < interval_seconds:
                    log(
                        "[SERVICES] Scheduled discovery not due "
                        f"({int(age)}s since last run)"
                    )
                    return False

            except (TypeError, ValueError):
                pass

        services = discover_infrastructure_services()

        log(
            "[SERVICES] Scheduled discovery completed: "
            f"{len(services)} verified service(s)"
        )

        return True

    except Exception as e:
        log(
            "[SERVICES] Scheduled discovery failed: "
            f"{e}"
        )
        return False

def config_bool(value, default=False):
    """Convert configuration values such as 0/1 strings safely to bool."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0

    text = str(value).strip().lower()
    if text in ('1', 'true', 'yes', 'on', 'enabled'):
        return True
    if text in ('0', 'false', 'no', 'off', 'disabled', ''):
        return False
    return default


def run_targeted_scan_with_history(device, config, scan_type):
    """Run a targeted scan and record its scan and email audit history."""
    if scan_type not in ('manual', 'automatic'):
        raise ValueError(f"Invalid scan type: {scan_type}")

    mac = (device.get('mac') or '').strip().lower()
    ip = (device.get('ip') or '').strip()
    started_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    history_id = None

    top_ports = int(config.get('nmap_top_ports', 100))
    timing = int(config.get('nmap_timing', 4))
    host_timeout = int(config.get('nmap_host_timeout', 45))
    version_detection = config_bool(
        config.get('nmap_version_detection', True),
        True
    )

    try:
        with sqlite3.connect(DB_FILE) as history_conn:
            cursor = history_conn.execute(
                '''
                INSERT INTO nmap_scan_history (
                    mac,
                    ip,
                    scan_type,
                    started_at,
                    top_ports,
                    timing,
                    host_timeout,
                    version_detection
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    mac,
                    ip,
                    scan_type,
                    started_at,
                    top_ports,
                    timing,
                    host_timeout,
                    1 if version_detection else 0,
                )
            )
            history_id = cursor.lastrowid
    except Exception as e:
        log(f"[NMAP] Unable to create scan history row: {e}")

    details = {
        'scan_success': False,
        'scan_error': None,
        'services': [],
        'nmap_version': '',
        'nmap_elapsed': None,
        'os_hint': None,
        'email_sent': None,
        'email_error': None,
    }

    try:
        operation_success, error, details = targeted_scan_and_email(
            device,
            config
        )
        details = details or {}
    except Exception as e:
        if history_id is not None:
            finished_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            try:
                with sqlite3.connect(DB_FILE) as history_conn:
                    history_conn.execute(
                        '''
                        UPDATE nmap_scan_history
                        SET finished_at = ?, success = 0, error = ?
                        WHERE id = ?
                        ''',
                        (finished_at, str(e)[:1000], history_id)
                    )
            except Exception as history_error:
                log(
                    "[NMAP] Unable to finish scan history row: "
                    f"{history_error}"
                )
        raise

    if history_id is not None:
        finished_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        scan_success = bool(details.get('scan_success'))
        scan_error = details.get('scan_error')

        if not scan_success and not scan_error:
            scan_error = error or 'Unknown targeted scan failure'

        if scan_error:
            scan_error = str(scan_error)[:1000]

        services = details.get('services') or []
        email_sent = details.get('email_sent')
        email_error = details.get('email_error')

        if email_sent is not None:
            email_sent = 1 if email_sent else 0

        if email_error:
            email_error = str(email_error)[:1000]

        try:
            with sqlite3.connect(DB_FILE) as history_conn:
                history_conn.execute('PRAGMA foreign_keys = ON')

                history_conn.execute(
                    '''
                    UPDATE nmap_scan_history
                    SET finished_at = ?,
                        success = ?,
                        error = ?,
                        nmap_version = ?,
                        nmap_elapsed = ?,
                        os_hint = ?,
                        open_port_count = ?,
                        email_sent = ?,
                        email_error = ?
                    WHERE id = ?
                    ''',
                    (
                        finished_at,
                        1 if scan_success else 0,
                        scan_error,
                        details.get('nmap_version') or None,
                        details.get('nmap_elapsed'),
                        details.get('os_hint') or None,
                        len(services),
                        email_sent,
                        email_error,
                        history_id,
                    )
                )

                history_conn.execute(
                    'DELETE FROM nmap_scan_ports '
                    'WHERE scan_history_id = ?',
                    (history_id,)
                )

                if scan_success:
                    discovered_count = update_service_inventory_from_nmap(
                        history_conn,
                        mac,
                        ip,
                        device.get('vlan') or '',
                        services,
                        finished_at
                    )
                    if discovered_count:
                        log(
                            "[SERVICES] Updated "
                            f"{discovered_count} infrastructure service(s) "
                            f"for {mac}"
                        )

                for service in services:
                    try:
                        port_number = int(service.get('port'))
                    except (TypeError, ValueError):
                        continue

                    history_conn.execute(
                        '''
                        INSERT INTO nmap_scan_ports (
                            scan_history_id,
                            port,
                            protocol,
                            state,
                            service,
                            product,
                            version,
                            extra_info
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''',
                        (
                            history_id,
                            port_number,
                            str(service.get('protocol') or ''),
                            str(service.get('state') or 'open'),
                            str(service.get('service') or 'unknown'),
                            str(service.get('product') or ''),
                            str(service.get('service_version') or ''),
                            str(service.get('extra_info') or ''),
                        )
                    )

        except Exception as e:
            log(f"[NMAP] Unable to finish scan history row: {e}")

    # Preserve existing operational semantics:
    # email failure still causes automatic retry/backoff.
    return operation_success, error

def targeted_scan_and_email(device, config):
    """Run one targeted Nmap scan, email it, and return structured results."""
    ip = (device.get('ip') or '').strip()

    details = {
        'scan_success': False,
        'scan_error': None,
        'services': [],
        'nmap_version': '',
        'nmap_elapsed': None,
        'os_hint': None,
        'email_sent': None,
        'email_error': None,
    }

    # Hard safety guard: one literal IP only. No CIDR, ranges or hostnames.
    try:
        parsed_ip = ipaddress.ip_address(ip)
    except ValueError:
        error = f"Invalid target IP: {ip!r}"
        details['scan_error'] = error
        log(f"[NMAP] {error}")
        return False, error, details

    if parsed_ip.version != 4:
        error = f"IPv6 target skipped: {ip}"
        details['scan_error'] = error
        log(f"[NMAP] {error}")
        return False, error, details

    nmap_top_ports = int(config.get('nmap_top_ports', 100))
    nmap_timing = int(config.get('nmap_timing', 4))
    nmap_host_timeout = int(config.get('nmap_host_timeout', 45))
    nmap_version_detection = config_bool(
        config.get('nmap_version_detection', True),
        True
    )

    scan_cmd = [
        '/usr/local/bin/nmap',
        '-Pn',
        f'-T{nmap_timing}',
        '--top-ports', str(nmap_top_ports),
    ]

    if nmap_version_detection:
        scan_cmd.extend(['-sV', '--version-light'])

    scan_cmd.extend([
        '--host-timeout', f'{nmap_host_timeout}s',
        '-oX', '-',
        ip
    ])

    log(f"[NMAP] Starting targeted scan: {ip}")

    try:
        result = subprocess.run(
            scan_cmd,
            capture_output=True,
            text=True,
            timeout=nmap_host_timeout + 5
        )
    except subprocess.TimeoutExpired:
        error = f"Targeted scan timeout: {ip}"
        details['scan_error'] = error
        log(f"[NMAP] {error}")
        return False, error, details
    except Exception as e:
        error = f"Targeted scan failed to start for {ip}: {e}"
        details['scan_error'] = error
        log(f"[NMAP] {error}")
        return False, error, details

    if result.returncode != 0:
        error = (
            f"Scan failed for {ip}, code={result.returncode}: "
            f"{result.stderr[:200]}"
        )
        details['scan_error'] = error
        log(f"[NMAP] {error}")
        return False, error, details

    try:
        root = ET.fromstring(result.stdout)
    except Exception as e:
        error = f"Invalid XML output for {ip}: {e}"
        details['scan_error'] = error
        log(f"[NMAP] {error}")
        return False, error, details

    services = []
    os_hints = []

    for port in root.findall('.//port'):
        state_el = port.find('state')
        if state_el is None or state_el.get('state') != 'open':
            continue

        service_el = port.find('service')
        service_name = ''
        product = ''
        service_version = ''
        extra_info = ''

        if service_el is not None:
            service_name = service_el.get('name', '')
            product = service_el.get('product', '') or ''
            service_version = service_el.get('version', '') or ''
            extra_info = service_el.get('extrainfo', '') or ''

            ostype = service_el.get('ostype')
            if ostype and ostype not in os_hints:
                os_hints.append(ostype)

        version_parts = [
            value
            for value in (product, service_version, extra_info)
            if value
        ]

        services.append({
            'port': port.get('portid', ''),
            'protocol': port.get('protocol', ''),
            'state': 'open',
            'service': service_name or 'unknown',

            # Preserve the existing email-friendly combined version field.
            'version': ' '.join(version_parts),

            # v2.6 structured fields for persistent history.
            'product': product,
            'service_version': service_version,
            'extra_info': extra_info,
        })

    runstats = root.find('./runstats/finished')
    duration = ''
    elapsed_value = None

    if runstats is not None and runstats.get('elapsed'):
        elapsed_text = runstats.get('elapsed')
        duration = f"{elapsed_text} seconds"
        try:
            elapsed_value = float(elapsed_text)
        except (TypeError, ValueError):
            elapsed_value = None

    os_hint = ', '.join(os_hints) if os_hints else 'Not identified'

    details.update({
        'scan_success': True,
        'scan_error': None,
        'services': services,
        'nmap_version': root.get('version', '') or '',
        'nmap_elapsed': elapsed_value,
        'os_hint': os_hint,
    })

    payload = {
        'ip': ip,
        'mac': device.get('mac', ''),
        'hostname': device.get('hostname', '') or 'Unknown',
        'vendor': device.get('vendor', '') or 'Unknown',
        'vlan': device.get('vlan', ''),
        'first_seen': device.get('first_seen', ''),
        'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'duration': duration,
        'os_hint': os_hint,
        'services': services
    }

    safe_ip = ip.replace('.', '_')
    json_file = (
        f"/tmp/devicemonitor-scan-{os.getpid()}-{safe_ip}.json"
    )

    try:
        with open(json_file, 'w') as f:
            json.dump(payload, f)

        mail_result = subprocess.run(
            [
                '/usr/local/bin/php',
                '/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/'
                'notify_scan_email.php',
                json_file
            ],
            capture_output=True,
            text=True,
            timeout=20
        )

        if mail_result.returncode != 0:
            error = (
                f"Scan email failed for {ip}: "
                f"{mail_result.stderr[:200]}"
            )
            details['email_sent'] = False
            details['email_error'] = error
            log(f"[NMAP] {error}")
            return False, error, details

        details['email_sent'] = True
        details['email_error'] = None

        log(
            f"[NMAP] Targeted scan email sent for {ip}: "
            f"{len(services)} open service(s)"
        )
        return True, "", details

    except subprocess.TimeoutExpired:
        error = f"Scan email timeout for {ip}"
        details['email_sent'] = False
        details['email_error'] = error
        log(f"[NMAP] {error}")
        return False, error, details

    except Exception as e:
        error = f"Scan email error for {ip}: {e}"
        details['email_sent'] = False
        details['email_error'] = error
        log(f"[NMAP] {error}")
        return False, error, details

    finally:
        try:
            if os.path.exists(json_file):
                os.unlink(json_file)
        except Exception:
            pass

def send_email_via_php_api(new_devices):
    """Mark devices in the database for email delivery"""
    if not new_devices:
        return

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Pending must represent exactly this delivery channel's filtered set.
        cursor.execute("UPDATE devices SET notification_pending = 0")

        # Mark devices for notification
        for device in new_devices:
            cursor.execute("""
                UPDATE devices
                SET notification_pending = 1
                WHERE mac = ?
            """, (device['mac'],))

        conn.commit()
        # log(f"[EMAIL] Marked {len(new_devices)} devices for notification")

        # Call PHP without parameters
        result = subprocess.run(
            ['/usr/local/sbin/configctl', 'devicemonitor', 'sendEmailNotification'],
            capture_output=True,
            text=True,
            timeout=30
        )

        # log(f"[EMAIL] configctl returned: {result.returncode}")
        # if result.stdout:
        #     log(f"[EMAIL] stdout: {result.stdout[:200]}")
        if result.stderr:
            log(f"[EMAIL] stderr: {result.stderr[:200]}")

    except Exception as e:
        log(f"[EMAIL] Error: {e}")


def send_webhook_via_php_api(new_devices):
    """Mark devices in the database for webhook delivery"""
    if not new_devices:
        return

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Pending must represent exactly this delivery channel's filtered set.
        cursor.execute("UPDATE devices SET notification_pending = 0")

        # Mark devices for notification
        for device in new_devices:
            cursor.execute("""
                UPDATE devices
                SET notification_pending = 1
                WHERE mac = ?
            """, (device['mac'],))

        conn.commit()
        # log(f"[WEBHOOK] Marked {len(new_devices)} devices for notification")

        # Call PHP without parameters
        result = subprocess.run(
            ['/usr/local/sbin/configctl', 'devicemonitor', 'sendWebhookNotification'],
            capture_output=True,
            text=True,
            timeout=30
        )

        # log(f"[WEBHOOK] configctl returned: {result.returncode}")
        # if result.stdout:
        #     log(f"[WEBHOOK] stdout: {result.stdout[:200]}")
        if result.stderr:
            log(f"[WEBHOOK] stderr: {result.stderr[:200]}")

    except Exception as e:
        log(f"[WEBHOOK] Error: {e}")


def get_new_high_identity_events(conn, start_id):
    """Return qualifying identity events inserted during this scan cycle."""
    columns = [
        'detected_at',
        'event_type',
        'severity',
        'mac',
        'other_mac',
        'ip',
        'other_ip',
        'interface',
        'other_interface',
        'details',
    ]

    rows = conn.execute('''
        SELECT detected_at, event_type, severity, mac, other_mac,
               ip, other_ip, interface, other_interface, details
        FROM device_identity_events
        WHERE id > ?
          AND severity = 'high'
          AND event_type IN (
              'IP_IDENTITY_CHANGED',
              'IPV6_IDENTITY_CHANGED'
          )
        ORDER BY id ASC
    ''', (int(start_id),)).fetchall()

    return [dict(zip(columns, row)) for row in rows]


def should_send_identity_email(config, events):
    """Return whether this scan cycle should emit an identity alert."""
    return bool(
        events
        and config.get('enabled')
        and config.get('email_enabled')
        and config.get('identity_email_enabled')
        and config.get('email_to')
    )


def send_identity_email(events):
    """Send one batched identity alert without affecting scan success."""
    if not events:
        return True

    helper = (
        '/usr/local/opnsense/scripts/OPNsense/'
        'DeviceMonitor/notify_identity_email.php'
    )

    try:
        result = subprocess.run(
            ['/usr/local/bin/php', helper],
            input=json.dumps({'events': events}),
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            detail = (result.stderr or result.stdout or '').strip()
            log(
                '[IDENTITY-EMAIL] Failed: ' +
                (detail[:500] if detail else f'exit {result.returncode}')
            )
            return False

        try:
            response = json.loads(result.stdout or '{}')
        except (json.JSONDecodeError, TypeError):
            log('[IDENTITY-EMAIL] Failed: invalid helper response')
            return False

        status = response.get('result')
        message = str(response.get('message') or '').strip()

        if status == 'skipped':
            log(
                '[IDENTITY-EMAIL] Skipped: ' +
                (message if message else 'helper declined notification')
            )
            return False

        if status != 'sent':
            log(
                '[IDENTITY-EMAIL] Failed: unexpected helper result ' +
                repr(status)
            )
            return False

        log(
            f'[IDENTITY-EMAIL] Sent batched alert for '
            f'{len(events)} high-severity event(s)'
        )
        return True

    except subprocess.TimeoutExpired:
        log('[IDENTITY-EMAIL] Failed: email process timed out')
        return False
    except Exception as e:
        log(f'[IDENTITY-EMAIL] Failed: {e}')
        return False

# ================================================================
# MAIN FUNCTIONS - REFACTORED
# ================================================================

def record_identity_event(conn, mac, event_type, severity,
                          ip='', other_ip='', interface='', other_interface='',
                          details='', other_mac=''):
    """Record an identity event unless an equivalent recent event exists."""
    existing = conn.execute('''
        SELECT id
        FROM device_identity_events
        WHERE mac = ?
          AND event_type = ?
          AND COALESCE(ip, '') = ?
          AND COALESCE(other_ip, '') = ?
          AND COALESCE(other_mac, '') = ?
          AND COALESCE(interface, '') = ?
          AND COALESCE(other_interface, '') = ?
          AND resolved_at IS NULL
          AND detected_at >= datetime('now', '-15 minutes')
        LIMIT 1
    ''', (mac, event_type, ip, other_ip, other_mac,
          interface, other_interface)).fetchone()

    if existing:
        return False

    conn.execute('''
        INSERT INTO device_identity_events
            (mac, event_type, severity, ip, other_ip, other_mac,
             interface, other_interface, details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (mac, event_type, severity, ip, other_ip, other_mac,
          interface, other_interface, details))
    return True


def detect_recent_hostwatch_identity_events(conn, minutes=5, kea_leases=None):
    """Detect recent duplicate-MAC evidence without changing device state."""
    if not os.path.exists(HOSTWATCH_DB):
        return 0

    try:
        hw_conn = sqlite3.connect(f'file:{HOSTWATCH_DB}?mode=ro', uri=True)
        hw_conn.row_factory = sqlite3.Row
        rows = hw_conn.execute('''
            SELECT interface_name, ip_address, ether_address, last_seen
            FROM v_hosts
            WHERE protocol = 'inet'
              AND ether_address NOT IN
                  ('ff:ff:ff:ff:ff:ff', '00:00:00:00:00:00')
              AND ip_address NOT LIKE '169.254.%'
        ''').fetchall()
        hw_conn.close()
    except Exception as e:
        log(f'Identity detection: Hostwatch read failed: {e}')
        return 0

    recent = {}
    ip_owners = {}
    kea_by_ip = {
        lease['ip']: lease
        for lease in (kea_leases or [])
        if lease.get('active') and lease.get('ip') and lease.get('mac')
    }

    for row in rows:
        mac = (row['ether_address'] or '').lower().strip()
        ip = row['ip_address'] or ''
        iface = row['interface_name'] or ''
        last_seen = row['last_seen'] or ''

        if not mac or not is_recently_seen(last_seen, minutes):
            continue

        try:
            if ipaddress.ip_address(ip).version != 4:
                continue
        except ValueError:
            continue

        recent.setdefault(mac, []).append({
            'ip': ip,
            'interface': iface,
            'last_seen': last_seen,
        })

        ip_owners.setdefault(ip, []).append({
            'mac': mac,
            'interface': iface,
            'last_seen': last_seen,
        })

    created = 0

    for mac, observations in recent.items():
        ips = sorted({o['ip'] for o in observations if o['ip']})
        interfaces = sorted({o['interface'] for o in observations if o['interface']})
        details = json.dumps({
            'window_minutes': minutes,
            'locally_administered': is_locally_administered_mac(mac),
            'observations': observations,
        }, sort_keys=True)

        if len(ips) > 1:
            if record_identity_event(
                conn, mac, 'MAC_MULTI_IP', 'medium',
                ips[0], ips[1], '', '', details
            ):
                created += 1

        # Require the same IPv4 address on two interfaces within 60 seconds.
        # This avoids flagging normal interface moves or stale Hostwatch rows.
        interface_conflicts = []
        for observed_ip in ips:
            ip_observations = [
                o for o in observations
                if o['ip'] == observed_ip and o['interface']
            ]

            for index, first in enumerate(ip_observations):
                for second in ip_observations[index + 1:]:
                    if first['interface'] == second['interface']:
                        continue

                    try:
                        first_seen = datetime.strptime(
                            first['last_seen'], '%Y-%m-%d %H:%M:%S'
                        )
                        second_seen = datetime.strptime(
                            second['last_seen'], '%Y-%m-%d %H:%M:%S'
                        )
                    except (TypeError, ValueError):
                        continue

                    delta = abs((first_seen - second_seen).total_seconds())
                    if delta <= 60:
                        first_iface, second_iface = sorted((
                            first['interface'], second['interface']
                        ))
                        interface_conflicts.append((
                            delta, observed_ip, first_iface, second_iface
                        ))

        if interface_conflicts:
            delta, conflict_ip, first_iface, second_iface = min(
                interface_conflicts
            )
            interface_details = json.dumps({
                'window_minutes': minutes,
                'interface_time_delta_seconds': delta,
                'locally_administered': is_locally_administered_mac(mac),
                'observations': observations,
            }, sort_keys=True)

            if record_identity_event(
                conn, mac, 'MAC_MULTI_INTERFACE', 'medium',
                conflict_ip, '', first_iface, second_iface,
                interface_details
            ):
                created += 1

    for ip, observations in ip_owners.items():
        macs = sorted({o['mac'] for o in observations if o['mac']})
        if len(macs) <= 1:
            continue

        details_data = {
            'window_minutes': minutes,
            'observations': observations,
        }

        kea_lease = kea_by_ip.get(ip)
        if kea_lease:
            if kea_lease['mac'] in macs:
                kea_status = 'matches_one_hostwatch_mac'
            else:
                kea_status = 'conflicts_with_all_hostwatch_macs'

            details_data['kea_evidence'] = {
                'status': kea_status,
                'mac': kea_lease['mac'],
                'hostname': kea_lease.get('hostname', ''),
                'subnet_id': kea_lease.get('subnet_id'),
                'cltt': kea_lease.get('cltt'),
                'expires_at': kea_lease.get('expires_at'),
            }

        details = json.dumps(details_data, sort_keys=True)

        if record_identity_event(
            conn,
            macs[0],
            'IP_IDENTITY_CHANGED',
            'high',
            ip=ip,
            details=details,
            other_mac=macs[1]
        ):
            created += 1

    return created

def detect_recent_hostwatch_ipv6_identity_events(conn, minutes=5):
    """Detect strong non-link-local IPv6 ownership conflicts."""
    if not os.path.exists(HOSTWATCH_DB):
        return 0

    try:
        with sqlite3.connect(f'file:{HOSTWATCH_DB}?mode=ro', uri=True) as hw_conn:
            hw_conn.row_factory = sqlite3.Row
            rows = hw_conn.execute('''
                SELECT interface_name, ip_address, ether_address, last_seen
                FROM v_hosts
                WHERE protocol = 'inet6'
                  AND ether_address NOT IN
                      ('ff:ff:ff:ff:ff:ff', '00:00:00:00:00:00')
            ''').fetchall()
    except Exception as e:
        log(f'IPv6 identity detection: Hostwatch read failed: {e}')
        return 0

    owners = {}

    for row in rows:
        ip_text = (row['ip_address'] or '').strip()
        mac = (row['ether_address'] or '').strip().lower()
        interface = row['interface_name'] or ''
        last_seen = row['last_seen'] or ''

        if not ip_text or not mac or not is_recently_seen(last_seen, minutes):
            continue

        try:
            parsed_ip = ipaddress.ip_address(ip_text)
        except ValueError:
            continue

        if parsed_ip.version != 6:
            continue

        # Link-local addresses are normal per-interface identity evidence and
        # are deliberately excluded from anomaly scoring.
        if parsed_ip.is_link_local:
            continue

        # Ignore non-unicast/special addresses. Only ULA or globally routable
        # IPv6 addresses participate in conflict detection.
        if parsed_ip.is_unspecified or parsed_ip.is_loopback or parsed_ip.is_multicast:
            continue

        ula = parsed_ip in ipaddress.ip_network('fc00::/7')
        if not ula and not parsed_ip.is_global:
            continue

        canonical_ip = str(parsed_ip)
        owners.setdefault(canonical_ip, []).append({
            'mac': mac,
            'interface': interface,
            'last_seen': last_seen,
        })

    created = 0

    for ip, observations in owners.items():
        macs = sorted({item['mac'] for item in observations if item['mac']})
        if len(macs) <= 1:
            continue

        parsed_ip = ipaddress.ip_address(ip)
        scope = (
            'ula'
            if parsed_ip in ipaddress.ip_network('fc00::/7')
            else 'global'
        )

        details = json.dumps({
            'window_minutes': minutes,
            'address_scope': scope,
            'observations': observations,
        }, sort_keys=True)

        if record_identity_event(
            conn,
            macs[0],
            'IPV6_IDENTITY_CHANGED',
            'high',
            ip=ip,
            details=details,
            other_mac=macs[1],
        ):
            created += 1

    return created

def update_status_only():
    """Quick online/offline status update from Hostwatch DB"""
    log("Quick status update (hostwatch DB)")
    init_db()

    devices = get_hostwatch_devices()
    if not devices:
        log("No data from Hostwatch DB")
        print("ERROR: No hostwatch data")
        return 1

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE devices SET is_active = 0")
    for d in devices:
        if is_recently_seen(d.get('last_seen', '')):
            cursor.execute(
                "UPDATE devices SET is_active = 1, last_seen = ? WHERE mac = ?",
                (d.get('last_seen', ''), d['mac'])
            )

    conn.commit()
    online = conn.execute("SELECT COUNT(*) FROM devices WHERE is_active = 1").fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
    conn.close()

    log(f"Status: {online}/{total} online")
    print(f"OK: {online}/{total} online")
    return 0


def full_scan():
    """Full scan from OPNsense Hostwatch DB with DHCP labels"""
    log("Starting full scan from Hostwatch DB...")
    config = load_config()
    init_db()

    capabilities = detect_source_capabilities()
    log(
        'Identity sources: '
        f'Hostwatch={capabilities["hostwatch"]["readable"]}, '
        f'Kea={capabilities["kea"]["queryable"]}, '
        f'ISC={capabilities["isc"]["enabled"]}, '
        f'Dnsmasq={capabilities["dnsmasq"]["configured"]}'
    )

    # 1. Data z hostwatch
    devices = get_hostwatch_devices()
    if not devices:
        log("ERROR: No data from Hostwatch DB")
        return 1

    # 2. DHCP labels from ISC and Dnsmasq, with Dnsmasq taking precedence
    dhcp_descriptions = get_dhcp_descriptions()
    dnsmasq_descriptions = get_dnsmasq_descriptions()
    dhcp_descriptions.update(dnsmasq_descriptions)  # Dnsmasq overrides ISC when the same MAC exists

    # 3. Update local database
    new_devices = []
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB_FILE)
    conn.execute('UPDATE devices SET is_active = 0, notification_pending = 0')

    for device in devices:
        mac = device['mac']
        if not mac:
            continue

        # Enrich with DHCP description
        if mac in dhcp_descriptions:
            device['hostname'] = dhcp_descriptions[mac]

        is_active = 1 if is_recently_seen(device.get('last_seen', '')) else 0
        last_seen = device.get('last_seen') or now
        first_seen = device.get('first_seen') or now

        # If the user manually deleted this device, ignore the same historical
        # Hostwatch record. A genuinely newer last_seen means the device has
        # returned to the network, so remove the tombstone and add it again.
        deleted_row = conn.execute(
            'SELECT last_seen FROM deleted_devices WHERE mac = ?', (mac,)
        ).fetchone()
        if deleted_row:
            deleted_last_seen = deleted_row[0] or ''
            if deleted_last_seen and last_seen <= deleted_last_seen:
                continue
            conn.execute('DELETE FROM deleted_devices WHERE mac = ?', (mac,))

        known_row = conn.execute(
            'SELECT mac FROM known_macs WHERE mac = ?', (mac,)
        ).fetchone()
        is_truly_new = known_row is None

        if is_truly_new:
            conn.execute('''
                INSERT INTO known_macs (mac, first_seen, last_seen)
                VALUES (?, ?, ?)
            ''', (mac, first_seen, last_seen))
        else:
            conn.execute(
                'UPDATE known_macs SET last_seen = ? WHERE mac = ?',
                (last_seen, mac)
            )

        row = conn.execute(
            'SELECT mac, custom_hostname FROM devices WHERE mac = ?', (mac,)
        ).fetchone()

        if row:
            hostname = row[1] if row[1] else device['hostname']
            conn.execute('''
                UPDATE devices
                SET ip = ?, hostname = ?, vendor = ?, vlan = ?,
                    last_seen = ?, is_active = ?
                WHERE mac = ?
            ''', (device['ip'], hostname, device['vendor'],
                  device['vlan'], last_seen, is_active, mac))
        else:
            conn.execute('''
                INSERT INTO devices
                    (mac, ip, hostname, vendor, vlan, first_seen, last_seen,
                     is_active, notification_pending)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
            ''', (mac, device['ip'], device['hostname'], device['vendor'],
                  device['vlan'], first_seen, last_seen, is_active))
            device['first_seen'] = first_seen
            if is_truly_new:
                new_devices.append(device)

    identity_event_start_id = conn.execute(
        'SELECT COALESCE(MAX(id), 0) FROM device_identity_events'
    ).fetchone()[0]

    kea_identity_leases = []
    if (
        capabilities['kea']['active']
        and capabilities['kea']['queryable']
        and capabilities['kea']['lease4_get_all']
    ):
        kea_identity_leases = get_kea_ipv4_leases()

    identity_events = detect_recent_hostwatch_identity_events(
        conn,
        minutes=5,
        kea_leases=kea_identity_leases,
    )
    identity_events += detect_recent_hostwatch_ipv6_identity_events(
        conn,
        minutes=5,
    )

    if identity_events:
        log(f'Identity detection: recorded {identity_events} event(s)')

    conn.commit()

    new_high_identity_events = get_new_high_identity_events(
        conn,
        identity_event_start_id,
    )

    online = conn.execute(
        "SELECT COUNT(*) FROM devices WHERE is_active = 1"
    ).fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
    conn.close()

    if should_send_identity_email(config, new_high_identity_events):
        send_identity_email(new_high_identity_events)

    # Infrastructure-service discovery is intentionally rate-limited.
    # It must not add DHCP/DNS probes to every normal monitoring cycle.
    run_scheduled_service_discovery()

    # 4. Notifications filtered by VLAN
    log(f"New devices: {len(new_devices)}, Online: {online}/{total}")
    if new_devices and config['enabled']:
        email_vlans   = set(v.strip() for v in config.get('email_vlans',  '').split(',') if v.strip())
        webhook_vlans = set(v.strip() for v in config.get('webhook_vlans', '').split(',') if v.strip())
        email_devs    = [d for d in new_devices if not email_vlans   or d.get('vlan','') in email_vlans]
        webhook_devs  = [d for d in new_devices if not webhook_vlans or d.get('vlan','') in webhook_vlans]
        if email_devs and config.get('email_enabled') and config.get('email_to'):
            send_email_via_php_api(email_devs)

            if config.get('targeted_nmap_enabled', True):
                # Queue every newly detected emailed device for a targeted scan.
                # New queue entries always start with a clean retry state.
                with sqlite3.connect(DB_FILE) as queue_conn:
                    for device in email_devs:
                        queue_conn.execute('''
                            UPDATE devices
                            SET nmap_scan_pending = 1,
                                nmap_scan_attempts = 0,
                                nmap_next_attempt = NULL,
                                nmap_last_error = NULL
                            WHERE mac = ?
                        ''', (device['mac'],))

                log(f"[NMAP] Queued {len(email_devs)} new device(s) for targeted scanning")

        if webhook_devs and config.get('webhook_enabled') and config.get('webhook_url'):
            send_webhook_via_php_api(webhook_devs)

    # Drain a bounded number of queued targeted scans each cycle.
    # Retry backoff after failures: 15m, 1h, 6h, 24h, then stop.
    if (
        config['enabled']
        and config.get('email_enabled')
        and config.get('email_to')
        and config.get('targeted_nmap_enabled', True)
    ):
        retry_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        nmap_max_per_cycle = int(config.get('nmap_max_per_cycle', 2))

        with sqlite3.connect(DB_FILE) as queue_conn:
            queue_conn.row_factory = sqlite3.Row
            scan_rows = queue_conn.execute('''
                SELECT mac, ip, hostname, vendor, vlan, first_seen,
                       nmap_scan_attempts, nmap_next_attempt, nmap_last_error
                FROM devices
                WHERE nmap_scan_pending = 1
                  AND (nmap_next_attempt IS NULL OR nmap_next_attempt <= ?)
                ORDER BY first_seen ASC
                LIMIT ?
            ''', (retry_now, nmap_max_per_cycle)).fetchall()

        for row in scan_rows:
            device = dict(row)
            success, error = run_targeted_scan_with_history(device, config, 'automatic')

            if success:
                with sqlite3.connect(DB_FILE) as queue_conn:
                    queue_conn.execute('''
                        UPDATE devices
                        SET nmap_scan_pending = 0,
                            nmap_scan_attempts = 0,
                            nmap_next_attempt = NULL,
                            nmap_last_error = NULL
                        WHERE mac = ?
                    ''', (device['mac'],))

                log(f"[NMAP] Targeted scan completed for {device['mac']}")
                continue

            attempts = int(device.get('nmap_scan_attempts') or 0) + 1
            error = (error or 'Unknown targeted scan failure')[:1000]

            retry_delays = {
                1: timedelta(minutes=15),
                2: timedelta(hours=1),
                3: timedelta(hours=6),
                4: timedelta(hours=24),
            }

            if attempts >= 5:
                with sqlite3.connect(DB_FILE) as queue_conn:
                    queue_conn.execute('''
                        UPDATE devices
                        SET nmap_scan_pending = 0,
                            nmap_scan_attempts = ?,
                            nmap_next_attempt = NULL,
                            nmap_last_error = ?
                        WHERE mac = ?
                    ''', (attempts, error, device['mac']))

                log(
                    f"[NMAP] Targeted scan permanently failed for "
                    f"{device['mac']} after {attempts} attempts: {error}"
                )
            else:
                next_attempt = (
                    datetime.now() + retry_delays[attempts]
                ).strftime('%Y-%m-%d %H:%M:%S')

                with sqlite3.connect(DB_FILE) as queue_conn:
                    queue_conn.execute('''
                        UPDATE devices
                        SET nmap_scan_pending = 1,
                            nmap_scan_attempts = ?,
                            nmap_next_attempt = ?,
                            nmap_last_error = ?
                        WHERE mac = ?
                    ''', (attempts, next_attempt, error, device['mac']))

                log(
                    f"[NMAP] Targeted scan attempt {attempts} failed for "
                    f"{device['mac']}; retry scheduled for {next_attempt}: {error}"
                )

        with sqlite3.connect(DB_FILE) as queue_conn:
            remaining_scans = queue_conn.execute(
                'SELECT COUNT(*) FROM devices WHERE nmap_scan_pending = 1'
            ).fetchone()[0]

        if remaining_scans:
            log(f"[NMAP] {remaining_scans} targeted scan(s) remain queued")
    # Do not leave stale pending flags between scans/channels.
    with sqlite3.connect(DB_FILE) as cleanup_conn:
        cleanup_conn.execute('UPDATE devices SET notification_pending = 0')

    return 0


def manual_targeted_scan(mac):
    """Run one targeted Nmap scan for an existing device without changing queue state."""
    mac = (mac or '').strip().lower()

    if not re.fullmatch(r'(?:[0-9a-f]{2}:){5}[0-9a-f]{2}', mac):
        print(f"ERROR: Invalid MAC address: {mac}", file=sys.stderr)
        return 2

    init_db()

    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            '''
            SELECT mac, ip, hostname, vendor, vlan, first_seen
            FROM devices
            WHERE lower(mac) = ?
            ''',
            (mac,)
        ).fetchone()

    if row is None:
        print(f"ERROR: Device not found: {mac}", file=sys.stderr)
        return 3

    device = dict(row)
    config = load_config()

    success, error = run_targeted_scan_with_history(device, config, 'manual')

    if success:
        print(f"Targeted Nmap scan completed for {mac}")
        return 0

    print(f"ERROR: {error or 'Targeted Nmap scan failed'}", file=sys.stderr)
    return 1


def main():
    """Main entry point with argument parsing"""

    # Parsuj argumenty
    parser = argparse.ArgumentParser(
        description='OPNsense Device Monitor - Network Scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s                    # Full scan (default)
  %(prog)s --update-only      # Quick status update (hostwatch DB)
  %(prog)s --scan-mac MAC     # Targeted Nmap scan for one existing device
  %(prog)s --verbose          # Full scan with verbose output
  %(prog)s --help             # Show this help
        '''
    )

    parser.add_argument(
        '--update-only',
        action='store_true',
        help='Quick mode: only update online/offline status via hostwatch DB'
    )

    parser.add_argument(
        '--scan-mac',
        metavar='MAC',
        help='Run one targeted Nmap scan for an existing device'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--discover-services',
        action='store_true',
        help='Discover infrastructure services such as DHCP servers'
    )
    args = parser.parse_args()

    # Verbose mode
    global DEBUG_LOGGING
    if args.verbose:
        DEBUG_LOGGING = True
    if args.discover_services:
        services = discover_infrastructure_services()

        print(json.dumps({
            'result': 'ok',
            'services': services
        }))
        return 0

    try:
        # Dispatch according to mode
        if args.scan_mac:
            return manual_targeted_scan(args.scan_mac)
        if args.update_only:
            return update_status_only()
        return full_scan()

    except KeyboardInterrupt:
        log("Scan interrupted by user")
        print("\nInterrupted")
        return 1
    except Exception as e:
        log(f"Fatal error: {e}")
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
