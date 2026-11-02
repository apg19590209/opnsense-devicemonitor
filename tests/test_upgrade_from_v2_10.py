"""A 2.10 database upgrades in place to the current schema, losing nothing.

The supported predecessor list spans 2.8 … 2.13.1, so a firewall on the 2.10 or
2.11 line can install the current bundle directly instead of stepping through
2.11 and 2.12. That claim rests on three properties, and this test pins them
against a database built by the *v2.10 code itself* rather than a hand-written
fixture:

  * every schema change between the lines is additive (`CREATE TABLE IF NOT
    EXISTS`, `ALTER TABLE … ADD COLUMN`), so one `init_db()` reaches the final
    shape from any predecessor;
  * the added `last_checked` column is backfilled from the old `last_verified`,
    so pre-existing rows stay ageable instead of being silently exempt;
  * the upgrade preserves device and service rows, and re-running `init_db()` on
    the upgraded database changes nothing.

The v2.10 source is read from the `v2.10` tag, which the workflow checks out with
`fetch-depth: 0`. Without the tag the test reports SKIPPED instead of failing, so
a shallow local clone does not produce a false red.
"""
import importlib.util
import sqlite3
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / 'src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py'
PATH_IN_TAG = 'src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py'
STAMP = '%Y-%m-%d %H:%M:%S'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def columns(conn, table):
    return {row[1] for row in conn.execute('PRAGMA table_info(%s)' % table)}


def old_source(tmp):
    try:
        text = subprocess.run(
            ['git', '-C', str(ROOT), 'show', 'v2.10:%s' % PATH_IN_TAG],
            capture_output=True, text=True, check=True, timeout=30,
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return None
    if 'def init_db' not in text:
        return None

    # The v2.10 module loads defaults.json from the absolute OPNsense path, which does
    # not exist on a CI runner. Point it at the checkout's own copy so the test is
    # hermetic; only PATHS/defaults are read at import time and the database path is
    # overridden below.
    repo_defaults = ROOT / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'
    text = text.replace(
        "/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json",
        str(repo_defaults),
    )

    target = tmp / 'scan_network_210.py'
    target.write_text(text)
    return target


def test_v2_10_database_upgrades_in_place():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        source = old_source(tmp)
        if source is None:
            print('UPGRADE_2_10=SKIPPED (v2.10 tag not available)')
            return

        db = tmp / 'devices.db'

        old = load(source, 'sn210')
        old.DB_FILE = str(db)
        old.init_db()

        with sqlite3.connect(db) as conn:
            before_columns = columns(conn, 'device_services')
            assert 'last_checked' not in before_columns, before_columns
            assert 'miss_count' not in before_columns, before_columns
            assert 'carp_role' not in columns(conn, 'service_discovery_state')

            conn.execute(
                "INSERT INTO devices (mac, ip, last_seen) VALUES (?, ?, ?)",
                ('aa:bb:cc:00:00:10', '203.0.113.10', '2026-09-01 00:00:00'),
            )
            conn.execute(
                "INSERT INTO device_services (mac, ip, interface, service_type, port, "
                "protocol, status, detection_method, confidence, product, version, "
                "first_detected, last_verified) VALUES (?, ?, 'LAN', 'SSH', 22, 'tcp', "
                "'unavailable', 'ssh_banner', 'verified', '', '', ?, ?)",
                ('aa:bb:cc:00:00:10', '203.0.113.10', '2026-09-01 00:00:00',
                 '2026-09-02 00:00:00'),
            )
            conn.execute(
                "INSERT INTO device_services (mac, ip, interface, service_type, port, "
                "protocol, status, detection_method, confidence, product, version, "
                "first_detected, last_verified) VALUES (?, ?, 'LAN', 'DNS', 53, 'tcp', "
                "'available', 'dns_probe', 'verified', '', '', ?, ?)",
                ('aa:bb:cc:00:00:11', '203.0.113.11', '2026-09-01 00:00:00',
                 '2026-11-02 00:00:00'),
            )
            conn.commit()

        new = load(CURRENT, 'sn_current')
        new.DB_FILE = str(db)
        new.init_db()

        with sqlite3.connect(db) as conn:
            after_columns = columns(conn, 'device_services')
            assert 'last_checked' in after_columns, after_columns
            assert 'miss_count' in after_columns, after_columns
            assert 'carp_role' in columns(conn, 'service_discovery_state')

            assert conn.execute('SELECT count(*) FROM devices').fetchone()[0] == 1
            assert conn.execute('SELECT count(*) FROM device_services').fetchone()[0] == 2

            backfilled = conn.execute(
                "SELECT last_checked FROM device_services WHERE ip = '203.0.113.10'"
            ).fetchone()[0]
            assert backfilled == '2026-09-02 00:00:00', backfilled

        aged, retired = new.age_stale_service_state()
        assert (aged, retired) == (1, 0), (aged, retired)

        with sqlite3.connect(db) as conn:
            statuses = dict(conn.execute('SELECT ip, status FROM device_services'))
        assert statuses['203.0.113.10'] == 'unknown', statuses
        assert statuses['203.0.113.11'] == 'available', statuses

        new.init_db()
        new.init_db()

        with sqlite3.connect(db) as conn:
            assert conn.execute('SELECT count(*) FROM devices').fetchone()[0] == 1
            assert conn.execute('SELECT count(*) FROM device_services').fetchone()[0] == 2
            assert 'last_checked' in columns(conn, 'device_services')

    print('UPGRADE_2_10=PASS')


if __name__ == '__main__':
    test_v2_10_database_upgrades_in_place()
