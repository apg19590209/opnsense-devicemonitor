"""O4-ageing diagnostic: real upsert/ageing on a temporary database, stubbed boundaries only.

Reproduces E1 (old MAC and current MAC share an IP), E2 (MAC moved to another IP),
E3 (endpoint answers, MAC unknown) and E1b (stale owner row, no probe). The DHCP
discovery path is exercised for real; only subprocess (ifconfig -l and nmap) and the
clock are stubbed. No network, host or live DB.

Corrected outcomes after the presence-attribution change:
  E1  - the service row advances its own timestamps and its MAC is reassigned by the
        ordering heuristic; no device row is refreshed. aged=0, retired=0.
  E1b - no probe: the stale-owner row ages to unknown and is RETAINED because another
        device at the IP is fresh (and its own last success is far outside the
        retirement window, so the presence guard does not apply either). aged=1,
        retired=0. Shared-IP retention remains the unresolved backlog item.
  E2  - owner moved to another IP, no fresh device at the old IP: aged=1, retired=1.
  E3  - the DHCP path still assigns the newest device at the IP; no device refresh.
These are fixture results, not host acceptance.
"""
import builtins
import importlib.util
import ipaddress
import sqlite3
import tempfile
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py'
DEFAULTS = Path(__file__).resolve().parents[1] / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'
NOW = datetime(2026, 10, 31, 12, 0, 0, tzinfo=UTC)
STAMP = '%Y-%m-%d %H:%M:%S'
IP = '198.51.100.10'
OLD_MAC, NEW_MAC = 'aa:bb:cc:dd:ee:10', 'aa:bb:cc:dd:ee:11'
OTHER_IP = '198.51.100.20'


def load_module():
    original_open = builtins.open

    def test_open(path, *args, **kwargs):
        if str(path).endswith('/models/OPNsense/DeviceMonitor/defaults.json'):
            path = DEFAULTS
        return original_open(path, *args, **kwargs)

    spec = importlib.util.spec_from_file_location('devicemonitor_o4_diag', SOURCE)
    module = importlib.util.module_from_spec(spec)
    builtins.open = test_open
    try:
        spec.loader.exec_module(module)
    finally:
        builtins.open = original_open
    module.log = lambda message: None
    module._system_local_timezone = lambda: UTC
    return module


def stamp(delta):
    return (NOW + delta).astimezone(UTC).strftime(STAMP)


def add_device(conn, mac, ip, last_seen):
    conn.execute('INSERT INTO devices (mac, ip, vlan, is_active, last_seen) VALUES (?,?,?,0,?)',
                 (mac, ip, 'VLAN60', last_seen))


def add_service(conn, mac, ip, status='available', last='', port=67, method='dhcp_offer'):
    conn.execute(
        'INSERT INTO device_services (mac, ip, interface, service_type, port, protocol, status,'
        ' detection_method, confidence, product, version, first_detected, last_verified,'
        ' last_checked, miss_count) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)',
        (mac, ip, 'em0', 'DHCP', port, 'udp', status, method, 'verified', '', '',
         last, last, last))


def nmap_output(server_ip):
    return ('<port><script id="broadcast-dhcp-discover" output="'
            'Server Identifier: %s">' % server_ip + '</script></port>')


def run_discovery(module, server_ip, at):
    """Real discover_dhcp_servers; only subprocess and the clock are stubbed."""
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if cmd[:2] == ['/sbin/ifconfig', '-l']:
            return type('R', (), {'returncode': 0, 'stdout': 'em0\n', 'stderr': ''})()
        if cmd[0].endswith('nmap'):
            return type('R', (), {'returncode': 0, 'stdout': nmap_output(server_ip), 'stderr': ''})()
        raise AssertionError('unexpected subprocess %r' % (cmd,))

    original_run, original_ts = module.subprocess.run, module.utc_timestamp
    module.subprocess.run = fake_run
    module.utc_timestamp = lambda value=None: at if value is None else original_ts(value)
    try:
        module.discover_dhcp_servers([{'device': 'em0', 'name': 'lan', 'network': ipaddress.ip_network('198.51.100.0/24')}])
    finally:
        module.subprocess.run, module.utc_timestamp = original_run, original_ts
    return calls


def snapshot(module):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        devices = conn.execute('SELECT mac, ip, last_seen FROM devices ORDER BY mac').fetchall()
        services = conn.execute('SELECT id, mac, ip, status, last_verified, last_checked FROM device_services ORDER BY id').fetchall()
        pending = conn.execute('SELECT service_key FROM service_alert_pending ORDER BY service_key').fetchall()
        events = conn.execute('SELECT event_type, mac FROM device_activity_events ORDER BY id').fetchall()
    return {'devices': devices, 'services': services, 'pending': pending, 'events': events}


def age(module, at):
    return module.age_stale_service_state(now=at)


def fresh_db(module, tmp):
    module.DB_FILE = str(Path(tmp) / 'devices.db')
    module.init_db()


def case_e1(module):
    print('E1 old MAC A and current MAC B share an IP')
    with tempfile.TemporaryDirectory() as tmp:
        fresh_db(module, tmp)
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            # A is the stale owner; B is fresh at the same IP (as recorded in E1).
            add_device(conn, OLD_MAC, IP, stamp(timedelta(days=-65)))
            add_device(conn, NEW_MAC, IP, stamp(timedelta(days=-1)))
            add_service(conn, OLD_MAC, IP, 'unavailable', stamp(timedelta(days=-40)))
            conn.execute('INSERT INTO service_alert_pending (service_key, mac, event_json, held_at) VALUES (?,?,?,?)',
                         ('pending-old', OLD_MAC, '{}', stamp(timedelta(days=-40))))
            conn.commit()
        before = snapshot(module)
        run_discovery(module, IP, stamp(timedelta(0)))
        after_probe = snapshot(module)
        aged, retired = age(module, NOW)
        after_age = snapshot(module)
        print(' devices before:', before['devices'])
        print(' devices after probe:', after_probe['devices'])
        print(' service after probe:', after_probe['services'])
        print(' age:', aged, retired)
        print(' pending after:', after_age['pending'], 'events:', after_age['events'])


def case_e2(module):
    print('E2 MAC A moved to another IP')
    with tempfile.TemporaryDirectory() as tmp:
        fresh_db(module, tmp)
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, OLD_MAC, OTHER_IP, stamp(timedelta(days=-1)))
            add_device(conn, 'aa:bb:cc:dd:ee:22', IP, stamp(timedelta(days=-100)))
            add_service(conn, OLD_MAC, IP, 'unavailable', stamp(timedelta(days=-40)))
            conn.commit()
        before = snapshot(module)
        aged, retired = age(module, NOW)
        after_age = snapshot(module)
        print(' devices:', before['devices'])
        print(' service before:', before['services'])
        print(' age:', aged, retired, 'service after:', after_age['services'])


def case_e3(module):
    print('E3 endpoint answers, MAC cannot be established')
    with tempfile.TemporaryDirectory() as tmp:
        fresh_db(module, tmp)
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, OLD_MAC, IP, stamp(timedelta(days=-60)))
            conn.commit()
        run_discovery(module, IP, stamp(timedelta(0)))
        after_probe = snapshot(module)
        aged, retired = age(module, NOW)
        after_age = snapshot(module)
        print(' devices after probe:', after_probe['devices'])
        print(' service after probe:', after_probe['services'])
        print(' age:', aged, retired, 'service after:', after_age['services'])


def case_e1b(module):
    print('E1b stale owner row, fresh stranger at the IP, no probe this cycle')
    with tempfile.TemporaryDirectory() as tmp:
        fresh_db(module, tmp)
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, OLD_MAC, IP, stamp(timedelta(days=-65)))
            add_device(conn, NEW_MAC, IP, stamp(timedelta(days=-1)))
            add_service(conn, OLD_MAC, IP, 'unavailable', stamp(timedelta(days=-40)))
            conn.commit()
        aged, retired = age(module, NOW)
        print(' age:', aged, retired, snapshot(module)['services'])


def main():
    module = load_module()
    case_e1(module)
    case_e1b(module)
    case_e2(module)
    case_e3(module)


if __name__ == '__main__':
    main()
