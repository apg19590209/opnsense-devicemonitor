"""Opt-in port discovery must stay single-host and fail closed."""
import builtins
import importlib.util
import ipaddress
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py'
DEFAULTS = ROOT / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'


def load_module():
    original_open = builtins.open

    def test_open(path, *args, **kwargs):
        if str(path).endswith('/models/OPNsense/DeviceMonitor/defaults.json'):
            path = DEFAULTS
        return original_open(path, *args, **kwargs)

    spec = importlib.util.spec_from_file_location('dm_port_discovery', SOURCE)
    module = importlib.util.module_from_spec(spec)
    builtins.open = test_open
    try:
        spec.loader.exec_module(module)
    finally:
        builtins.open = original_open
    module.log = lambda message: None
    return module


def test_selected_host_and_schedule():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / 'devices.db')
        module.PORT_DISCOVERY_LOCK = str(Path(tmp) / 'port.lock')
        conn = sqlite3.connect(module.DB_FILE)
        conn.execute('CREATE TABLE devices (mac TEXT PRIMARY KEY, ip TEXT)')
        conn.executemany(
            'INSERT INTO devices VALUES (?, ?)', [
                ('aa:bb:cc:dd:ee:01', '192.0.2.20'),
                ('aa:bb:cc:dd:ee:02', '198.51.100.21')
            ]
        )
        conn.commit()
        conn.close()
        module.init_db = lambda: None
        with sqlite3.connect(module.DB_FILE) as conn:
            conn.executescript('''
                CREATE TABLE port_discovery_targets(
                    mac TEXT PRIMARY KEY, enabled INTEGER,
                    next_scan_at TEXT, last_scan_at TEXT, last_error TEXT);
                CREATE TABLE port_discovery_results(
                    id INTEGER PRIMARY KEY, mac TEXT, ip TEXT,
                    started_at TEXT, finished_at TEXT, success INTEGER,
                    error TEXT);
                CREATE TABLE port_discovery_ports(
                    result_id INTEGER, port INTEGER, protocol TEXT,
                    service TEXT, product TEXT, version TEXT);
            ''')
        network = {'network': ipaddress.ip_network('192.0.2.0/24')}
        module.resolve_monitored_networks = lambda config: ([network], None)
        module.load_config = lambda: {}
        module.ip_is_in_scope = lambda ip, nets: (
            ipaddress.ip_address(ip) in nets[0]['network']
        )
        calls = []

        def fake_run(command, **kwargs):
            calls.append(command)
            return SimpleNamespace(returncode=0, stderr='', stdout='''
                <nmaprun>
                  <host><ports><port protocol="tcp" portid="12815">
                    <state state="open"/>
                    <service name="unknown"/>
                  </port></ports></host>
                  <runstats><finished exit="success"/></runstats>
                </nmaprun>''')

        module.subprocess.run = fake_run
        assert module.port_discovery_target('aa:bb:cc:dd:ee:02', True) == 2
        assert module.port_discovery_target('aa:bb:cc:dd:ee:01', True) == 0
        with sqlite3.connect(module.DB_FILE) as conn:
            conn.execute(
                'INSERT INTO port_discovery_targets(mac, enabled, '
                'next_scan_at) VALUES (?, 1, ?)',
                ('aa:bb:cc:dd:ee:02', '2000-01-01 00:00:00')
            )
        assert module.run_port_discovery() == 0
        assert len(calls) == 1
        assert calls[0][-1] == '192.0.2.20'
        assert calls[0].count('192.0.2.20') == 1
        assert calls[0][calls[0].index('-p') + 1] == '1-65535'
        assert module.run_port_discovery() == 0
        assert len(calls) == 1, 'weekly target should not run again immediately'
        with sqlite3.connect(module.DB_FILE) as conn:
            port = conn.execute(
                'SELECT port, protocol, service FROM port_discovery_ports'
            ).fetchone()
            assert port == (12815, 'tcp', 'unknown'), port
        assert module.port_discovery_target('aa:bb:cc:dd:ee:01', False) == 0
        assert module.run_port_discovery() == 0
        assert len(calls) == 1
        module.subprocess.run = lambda command, **kwargs: SimpleNamespace(
            returncode=0, stderr='', stdout=
            '<nmaprun><runstats><finished exit="timeout"/></runstats></nmaprun>'
        )
        assert module.run_port_discovery('aa:bb:cc:dd:ee:01') == 1
        with sqlite3.connect(module.DB_FILE) as conn:
            latest = conn.execute(
                'SELECT success, error FROM port_discovery_results '
                'ORDER BY id DESC LIMIT 1'
            ).fetchone()
            assert latest[0] == 0 and 'incomplete' in latest[1], latest
            assert conn.execute(
                'SELECT COUNT(*) FROM port_discovery_ports'
            ).fetchone()[0] == 1, 'previous successful evidence is preserved'


if __name__ == '__main__':
    test_selected_host_and_schedule()
    print('PORT_DISCOVERY=PASS')
