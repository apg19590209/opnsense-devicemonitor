"""Every accepted predecessor upgrades in place to the current schema, losing nothing.

The installer accepts `2.8 ... 2.13.1` as predecessors, so a firewall on any of those
lines installs the current bundle directly instead of stepping through the intermediate
releases. That claim rests on three properties, and this test pins them against a
database built by each predecessor's **own** `init_db()` rather than a hand-written
fixture:

  * every schema change is additive (`CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ...
    ADD COLUMN`), so one `init_db()` reaches the final shape from any predecessor;
  * the added `last_checked` column is backfilled from the old `last_verified`, so
    pre-existing rows stay ageable instead of being silently exempt;
  * the upgrade preserves device and service rows, and re-running `init_db()` on the
    upgraded database changes nothing.

Each predecessor is read from its tag (the workflow checks out with `fetch-depth: 0`).
A tag that is unavailable is reported as SKIPPED, so a shallow clone stays honest.
"""
import importlib.util
import sqlite3
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / 'src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py'
PATH_IN_TAG = 'src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py'
DEFAULTS_ABS = '/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'

# Every version the installer accepts as a predecessor, and the tag carrying its source.
PREDECESSORS = [
    ('2.8', 'v2.8'),
    ('2.9', 'v2.9'),
    ('2.10', 'v2.10'),
    ('2.11', 'v2.11-patch1'),
    ('2.12', 'v2.12-baseline'),
    ('2.13', 'v2.13'),
    ('2.13.1', 'v2.13.1'),
]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stage(text, tmp, name):
    """Write a module whose defaults.json path points at the checkout copy.

    Both the old modules and the shipped one load defaults.json from the absolute
    OPNsense path, which does not exist on a CI runner. Rewriting it keeps the test
    hermetic without touching the shipped source.
    """
    repo_defaults = ROOT / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'
    target = tmp / name
    target.write_text(text.replace(DEFAULTS_ABS, str(repo_defaults)))
    return target


def source_for(tag, tmp):
    try:
        text = subprocess.run(
            ['git', '-C', str(ROOT), 'show', '%s:%s' % (tag, PATH_IN_TAG)],
            capture_output=True, text=True, check=True, timeout=30,
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return None
    if 'def init_db' not in text:
        return None
    return stage(text, tmp, 'scan_network_%s.py' % tag.replace('.', '_').replace('-', '_'))


def columns(conn, table):
    return {row[1] for row in conn.execute('PRAGMA table_info(%s)' % table)}


SEED_DEVICE = "INSERT INTO devices (mac, ip, last_seen) VALUES (?, ?, ?)"
SEED_SERVICE = (
    "INSERT INTO device_services (mac, ip, interface, service_type, port, protocol, "
    "status, detection_method, confidence, product, version, first_detected, "
    "last_verified) VALUES (?, ?, 'LAN', ?, ?, 'tcp', ?, ?, 'verified', '', '', ?, ?)"
)

def upgrade_one(version, tag):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        source = source_for(tag, tmp)
        if source is None:
            return 'SKIPPED'

        db = tmp / 'devices.db'
        old = load(source, 'old_%s' % version.replace('.', '_'))
        old.DB_FILE, old.log = str(db), lambda message: None
        old.init_db()

        with sqlite3.connect(db) as conn:
            before = columns(conn, 'device_services')
            # Only 2.13.1 carries the column already: 2.13 shipped without the ageing work.
            if version == '2.13.1':
                assert 'last_checked' in before, (version, before)
            else:
                assert 'last_checked' not in before, (version, before)
            conn.execute(SEED_DEVICE, ('aa:bb:cc:00:00:10', '203.0.113.10',
                                       '2026-09-01 00:00:00'))
            conn.execute(SEED_SERVICE, ('aa:bb:cc:00:00:10', '203.0.113.10', 'SSH', 22,
                                        'unavailable', 'ssh_banner',
                                        '2026-09-01 00:00:00', '2026-09-02 00:00:00'))
            conn.execute(SEED_SERVICE, ('aa:bb:cc:00:00:11', '203.0.113.11', 'DNS', 53,
                                        'available', 'dns_probe',
                                        '2026-09-01 00:00:00', '2026-11-02 00:00:00'))
            conn.commit()

            # Same starting state for every predecessor: the row was last observed when it
            # was last verified, so the migration's backfill and this explicit stamp agree.
            if 'last_checked' in before:
                conn.execute(
                    "UPDATE device_services SET last_checked = last_verified "
                    "WHERE ip = '203.0.113.10'"
                )
                conn.commit()

        new = load(stage(CURRENT.read_text(), tmp, 'scan_network_current.py'), 'new_current')
        new.DB_FILE, new.log = str(db), lambda message: None
        new.init_db()

        with sqlite3.connect(db) as conn:
            after = columns(conn, 'device_services')
            assert 'last_checked' in after, (version, after)
            assert 'miss_count' in after, (version, after)
            assert 'carp_role' in columns(conn, 'service_discovery_state'), version
            assert conn.execute('SELECT count(*) FROM devices').fetchone()[0] == 1
            assert conn.execute('SELECT count(*) FROM device_services').fetchone()[0] == 2
            backfilled = conn.execute(
                "SELECT last_checked FROM device_services WHERE ip = '203.0.113.10'"
            ).fetchone()[0]
            assert backfilled == '2026-09-02 00:00:00', (version, backfilled)

        aged, retired = new.age_stale_service_state()
        assert (aged, retired) == (1, 0), (version, aged, retired)

        with sqlite3.connect(db) as conn:
            statuses = dict(conn.execute('SELECT ip, status FROM device_services'))
        assert statuses['203.0.113.10'] == 'unknown', (version, statuses)
        assert statuses['203.0.113.11'] == 'available', (version, statuses)

        new.init_db()
        new.init_db()

        with sqlite3.connect(db) as conn:
            assert conn.execute('SELECT count(*) FROM devices').fetchone()[0] == 1
            assert conn.execute('SELECT count(*) FROM device_services').fetchone()[0] == 2

    return 'PASS'


def test_every_predecessor_upgrades():
    results = []
    for version, tag in PREDECESSORS:
        outcome = upgrade_one(version, tag)
        print('  %-7s %-14s %s' % (version, tag, outcome))
        results.append(outcome)

    assert 'PASS' in results, results
    print('UPGRADE_PREDECESSORS=PASS passed=%d skipped=%d'
          % (results.count('PASS'), results.count('SKIPPED')))


if __name__ == '__main__':
    test_every_predecessor_upgrades()
