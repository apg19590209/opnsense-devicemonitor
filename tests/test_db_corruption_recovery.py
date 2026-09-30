"""init_db() must self-heal a malformed devices.db instead of failing every scan.

v2.11 lifecycle, Task 2: a hard crash, power fault or filesystem locking loop can
leave the database malformed. init_db() probes PRAGMA quick_check, quarantines the
database and its WAL sidecars with a .corrupt-* suffix (never deleting them), and
rebuilds a pristine schema so the daemon keeps running.

These checks pin the guarantees that make that recovery safe:

  * a missing database is a first run, not corruption;
  * a malformed database is quarantined byte-for-byte and replaced by a valid one;
  * the -wal and -shm sidecars move with it, so stale frames cannot be replayed;
  * a healthy database is left untouched and its rows survive re-initialisation;
  * the health probe runs once per process instead of on every init_db() call.
"""
import builtins
import importlib.util
import os
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py'
DEFAULTS = ROOT / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'

GARBAGE = b'this is not a sqlite database, it is a truncated substitute'


def load_module():
    """Load scan_network.py with its defaults.json redirected and logs captured."""
    original_open = builtins.open

    def test_open(path, *args, **kwargs):
        if str(path).endswith('/models/OPNsense/DeviceMonitor/defaults.json'):
            path = DEFAULTS
        return original_open(path, *args, **kwargs)

    spec = importlib.util.spec_from_file_location('dm_db_recovery', SOURCE)
    module = importlib.util.module_from_spec(spec)
    builtins.open = test_open
    try:
        spec.loader.exec_module(module)
    finally:
        builtins.open = original_open

    notes = []
    module.log = lambda message: notes.append(message)
    # `logger` is the only external command on the recovery path; stub it out so
    # a test run never emits a syslog line and never shells out.
    module.subprocess = SimpleNamespace(
        run=lambda *args, **kwargs: SimpleNamespace(returncode=0)
    )
    return module, notes


def use_temp_db(module, tmp, name='devices.db'):
    """Point the module at a temp database and clear the probe cache."""
    path = str(Path(tmp) / name)
    module.DB_FILE = path
    module._db_health_checked_path = None
    return path


def quarantine_files(path):
    """Return the .corrupt-* quarantine files sitting next to `path`."""
    directory = os.path.dirname(path)
    prefix = os.path.basename(path) + '.corrupt-'
    return sorted(
        os.path.join(directory, entry)
        for entry in os.listdir(directory)
        if entry.startswith(prefix)
    )


def table_names(path):
    conn = sqlite3.connect(path)
    try:
        return {
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    finally:
        conn.close()


def test_missing_database_is_not_corruption():
    module, notes = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        path = use_temp_db(module, tmp)
        assert not os.path.exists(path)

        module.init_db()

        assert os.path.exists(path)
        assert 'devices' in table_names(path)
        assert quarantine_files(path) == []
        assert [n for n in notes if 'DB RECOVERY' in n] == []


def test_corrupt_database_is_quarantined_and_rebuilt():
    module, notes = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        path = use_temp_db(module, tmp)
        Path(path).write_bytes(GARBAGE)

        module.init_db()

        # The original bytes are preserved, not deleted.
        moved = quarantine_files(path)
        assert len(moved) == 1, moved
        assert Path(moved[0]).read_bytes() == GARBAGE

        # A pristine, valid schema now stands at the original path.
        names = table_names(path)
        assert 'devices' in names
        assert 'nmap_scan_history' in names
        assert module._db_health_problem(path) is None

        alerts = [n for n in notes if 'DB RECOVERY' in n]
        assert any('failed its integrity check' in n for n in alerts), alerts
        assert any('quarantined' in n for n in alerts), alerts
        assert any('NOT restored automatically' in n for n in alerts), alerts


def test_wal_sidecars_are_quarantined_too():
    module, notes = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        path = use_temp_db(module, tmp)
        Path(path).write_bytes(GARBAGE)
        Path(path + '-wal').write_bytes(b'stale wal frames')
        Path(path + '-shm').write_bytes(b'stale shm')

        module.init_db()

        for suffix in ('-wal', '-shm'):
            assert not os.path.exists(path + suffix), suffix
        assert len(quarantine_files(path + '-wal')) == 1
        assert len(quarantine_files(path + '-shm')) == 1
        assert 'devices' in table_names(path)


def test_healthy_database_rows_survive_reinitialisation():
    module, notes = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        path = use_temp_db(module, tmp)
        module.init_db()

        conn = sqlite3.connect(path)
        conn.execute(
            "INSERT INTO devices (mac, ip, hostname) VALUES (?, ?, ?)",
            ('aa:bb:cc:dd:ee:01', '192.168.1.10', 'laptop')
        )
        conn.commit()
        conn.close()

        module.init_db()
        module.init_db()

        assert quarantine_files(path) == []
        conn = sqlite3.connect(path)
        try:
            rows = conn.execute('SELECT mac, hostname FROM devices').fetchall()
        finally:
            conn.close()
        assert rows == [('aa:bb:cc:dd:ee:01', 'laptop')]
        assert [n for n in notes if 'DB RECOVERY' in n] == []


def test_health_probe_runs_once_per_path():
    module, notes = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        first = use_temp_db(module, tmp, 'one.db')
        module.init_db()
        assert module._db_health_checked_path == first

        calls = []
        module._db_health_problem = lambda p: calls.append(p) or None
        module.init_db()
        module.init_db()
        assert calls == [], 'the probe must be skipped once the path is checked'

        module._db_health_checked_path = None
        module.init_db()
        assert calls == [first], calls


def main():
    test_missing_database_is_not_corruption()
    test_corrupt_database_is_quarantined_and_rebuilt()
    test_wal_sidecars_are_quarantined_too()
    test_healthy_database_rows_survive_reinitialisation()
    test_health_probe_runs_once_per_path()
    print('DB_CORRUPTION_RECOVERY=PASS')


if __name__ == '__main__':
    main()
