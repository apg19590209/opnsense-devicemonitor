#!/usr/local/bin/python3

import sqlite3
import socket
from datetime import datetime, UTC, timedelta
import os
import json
import sys
import argparse
import subprocess
import re
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
            'socket_present': False,
            'queryable': False,
            'lease4_get_all': False,
        },
        'isc': {
            'configured': False,
            'enabled': False,
        },
        'dnsmasq': {
            'configured': False,
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

    kea_socket = '/var/run/kea/kea4-ctrl-socket'
    capabilities['kea']['socket_present'] = os.path.exists(kea_socket)

    if capabilities['kea']['socket_present']:
        try:
            request = json.dumps({'command': 'list-commands'}).encode() + bytes([10])
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                sock.connect(kea_socket)
                sock.sendall(request)
                response = b''
                while True:
                    chunk = sock.recv(65536)
                    if not chunk:
                        break
                    response += chunk

            payload = json.loads(response.decode())
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


def detect_recent_hostwatch_identity_events(conn, minutes=5):
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

        details = json.dumps({
            'window_minutes': minutes,
            'observations': observations,
        }, sort_keys=True)

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

    identity_events = detect_recent_hostwatch_identity_events(conn, minutes=5)
    if identity_events:
        log(f'Identity detection: recorded {identity_events} event(s)')

    conn.commit()
    online = conn.execute(
        "SELECT COUNT(*) FROM devices WHERE is_active = 1"
    ).fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
    conn.close()

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

    args = parser.parse_args()

    # Verbose mode
    global DEBUG_LOGGING
    if args.verbose:
        DEBUG_LOGGING = True

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
