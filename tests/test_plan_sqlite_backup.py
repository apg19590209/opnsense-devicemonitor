"""The deployment plan's database backup is a SQLite snapshot, not a raw file copy (M3).

`verification/DEPLOY-2.13.3-23-PLAN.md` §2 replaced `tar` of the live `devices.db` with
`sqlite3 .backup`, because a tar of a database being written is not a consistent snapshot.
This suite executes the same primitive against a synthetic database, asserts the snapshot
passes `quick_check` and preserves every row, and (when the node has one) reads the live
database read-only to prove the same holds there.

Nothing here writes to `/var/db/devicemonitor`.
"""
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'verification/DEPLOY-2.13.3-23-PLAN.md'
LIVE_DB = Path('/var/db/devicemonitor/devices.db')

SNAPSHOT = '''
import sqlite3, sys
src = sqlite3.connect('file:%s?mode=ro', uri=True)
dst = sqlite3.connect(sys.argv[1])
src.backup(dst)
assert dst.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
dst.close(); src.close()
'''


def test_plan_uses_a_consistent_backup():
    """The plan must not tell an operator to tar a live database."""
    section = PLAN.read_text()
    start = section.index('## 2. Backup verification')
    end = section.index('## 3. Install')
    body = section[start:end]
    assert 'src.backup(dst)' in body, 'the documented backup is not a SQLite snapshot'
    assert 'path=ro' in body or 'mode=ro' in body, 'the source is not opened read-only'
    assert not re.search(r'tar -czf [^\n]*/var/db/devicemonitor\s*$', body, re.M), \
        'the plan still tars the live data directory'
    print('  plan section          sqlite3 .backup, read-only source')


def test_snapshot_preserves_rows_and_integrity():
    """The documented primitive produces an intact copy with every row."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        source = tmp / 'devices.db'
        copy = tmp / 'snapshot.db'
        with sqlite3.connect(source) as conn:
            conn.execute('CREATE TABLE devices (mac TEXT, ip TEXT)')
            conn.execute('CREATE TABLE device_services (mac TEXT, status TEXT)')
            conn.executemany('INSERT INTO devices VALUES (?, ?)',
                             [('aa:bb:cc:00:00:%02d' % i, '203.0.113.%d' % i)
                              for i in range(25)])
            conn.executemany('INSERT INTO device_services VALUES (?, ?)',
                             [('aa:bb:cc:00:00:%02d' % i, 'available') for i in range(25)])
            conn.commit()

        code = SNAPSHOT % str(source)
        done = subprocess.run([sys.executable, '-c', code, str(copy)],
                              capture_output=True, text=True, timeout=120)
        assert done.returncode == 0, (done.stdout, done.stderr)

        with sqlite3.connect(copy) as conn:
            assert conn.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
            assert conn.execute('SELECT count(*) FROM devices').fetchone()[0] == 25
            assert conn.execute('SELECT count(*) FROM device_services').fetchone()[0] == 25
    print('  snapshot              25 rows preserved, quick_check ok')


def test_live_database_is_readable_and_intact():
    """Read-only integrity check of the node's database, when there is one."""
    if not LIVE_DB.is_file():
        print('  live database         absent on this host (skipped, nothing written)')
        return
    conn = sqlite3.connect('file:%s?mode=ro' % LIVE_DB, uri=True)
    try:
        assert conn.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
        devices = conn.execute('SELECT count(*) FROM devices').fetchone()[0]
        services = conn.execute('SELECT count(*) FROM device_services').fetchone()[0]
    finally:
        conn.close()
    print('  live database         quick_check ok, devices=%d services=%d' % (devices, services))


CASES = [
    test_plan_uses_a_consistent_backup,
    test_snapshot_preserves_rows_and_integrity,
    test_live_database_is_readable_and_intact,
]


def main():
    for case in CASES:
        case()
        print('  %-38s PASS' % case.__name__)
    print('PLAN_SQLITE_BACKUP=PASS cases=%d' % len(CASES))


if __name__ == '__main__':
    main()
