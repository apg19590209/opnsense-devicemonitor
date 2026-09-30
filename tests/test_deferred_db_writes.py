"""Deferred (asynchronous) Nmap history writes must be lossless and equivalent.

v2.11 lifecycle, Task 1: the Nmap completion path hands its history row and
port rows to a single writer thread through a queue.Queue instead of writing
them inline, so the result parser never blocks on the SQLite write lock.

These checks pin the guarantees that make that refactor safe:

  * a queued job is committed once and fully drained by flush_db_writes();
  * the asynchronous path and the synchronous fallback produce identical rows;
  * re-scanning a host replaces its port rows instead of duplicating them;
  * non-numeric ports are skipped exactly as the inline loop skipped them;
  * a failed scan records its error and adds no port rows;
  * concurrent enqueues from several threads are all recorded.
"""
import builtins
import importlib.util
import sqlite3
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py'
DEFAULTS = ROOT / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'

SCHEMA = (
    '''CREATE TABLE nmap_scan_history (
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
    )''',
    '''CREATE TABLE nmap_scan_ports (
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
    )''',
)

SERVICES = [
    {'port': 22, 'protocol': 'tcp', 'state': 'open', 'service': 'ssh',
     'product': 'OpenSSH', 'service_version': '9.6', 'extra_info': ''},
    # Port is not numeric: the inline loop skipped these, and so must we.
    {'port': 'tcp', 'protocol': 'tcp', 'state': 'open', 'service': 'bad'},
    {'port': 443, 'protocol': 'tcp', 'state': 'open', 'service': 'https',
     'product': 'nginx', 'service_version': '1.25', 'extra_info': 'TLS'},
]


def load_module():
    original_open = builtins.open

    def test_open(path, *args, **kwargs):
        if str(path).endswith('/models/OPNsense/DeviceMonitor/defaults.json'):
            path = DEFAULTS
        return original_open(path, *args, **kwargs)

    spec = importlib.util.spec_from_file_location('dm_deferred_db', SOURCE)
    module = importlib.util.module_from_spec(spec)
    builtins.open = test_open
    try:
        spec.loader.exec_module(module)
    finally:
        builtins.open = original_open
    module.log = lambda message: None
    return module


def new_db(module, tmp):
    module.DB_FILE = str(Path(tmp) / 'devices.db')
    conn = sqlite3.connect(module.DB_FILE)
    for statement in SCHEMA:
        conn.execute(statement)
    conn.commit()
    conn.close()


def add_history(module, mac='aa:bb:cc:dd:ee:01'):
    conn = sqlite3.connect(module.DB_FILE)
    cursor = conn.execute(
        'INSERT INTO nmap_scan_history (mac, ip, scan_type, started_at) '
        'VALUES (?, ?, ?, ?)',
        (mac, '192.168.1.10', 'manual', '2026-09-30 12:00:00')
    )
    history_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return history_id


def build_job(history_id, services, scan_success=True,
              mac='aa:bb:cc:dd:ee:01', scan_error=None):
    return {
        'history_id': history_id,
        'mac': mac,
        'ip': '192.168.1.10',
        'vlan': 'lan',
        'finished_at': '2026-09-30 12:00:03',
        'scan_success': scan_success,
        'scan_error': scan_error,
        'services': services,
        'nmap_version': '7.95',
        'nmap_elapsed': 3.5,
        'os_hint': 'Linux 5.x',
        'email_sent': 1,
        'email_error': None,
    }


def query(db, sql, args=()):
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in conn.execute(sql, args)]
    finally:
        conn.close()


def test_async_job_is_committed_and_drained():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        new_db(module, tmp)
        history_id = add_history(module)

        inventory = []
        module.update_service_inventory_from_nmap = (
            lambda *a, **k: inventory.append(a[1:]) or 2
        )

        assert module.enqueue_db_write(build_job(history_id, SERVICES)) is True
        assert module.flush_db_writes(5.0) is True
        assert module._DB_WRITER_PENDING == 0

        history = query(
            module.DB_FILE,
            'SELECT * FROM nmap_scan_history WHERE id = ?',
            (history_id,)
        )[0]
        assert history['finished_at'] == '2026-09-30 12:00:03'
        assert history['success'] == 1
        assert history['error'] is None
        assert history['nmap_version'] == '7.95'
        assert history['nmap_elapsed'] == 3.5
        assert history['os_hint'] == 'Linux 5.x'
        assert history['email_sent'] == 1
        # open_port_count still counts every parsed service, exactly as the
        # inline loop did before the refactor.
        assert history['open_port_count'] == len(SERVICES)

        ports = query(
            module.DB_FILE,
            'SELECT * FROM nmap_scan_ports WHERE scan_history_id = ? '
            'ORDER BY port',
            (history_id,)
        )
        assert [port['port'] for port in ports] == [22, 443]
        assert ports[0]['service'] == 'ssh'
        assert ports[0]['product'] == 'OpenSSH'
        assert ports[0]['version'] == '9.6'
        assert ports[0]['state'] == 'open'
        assert ports[1]['extra_info'] == 'TLS'

        # The inventory hook ran on the writer thread with the job's identity.
        assert inventory and inventory[0][0] == 'aa:bb:cc:dd:ee:01'
        assert module.stop_db_writer() is True


def test_rescan_replaces_ports():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        new_db(module, tmp)
        history_id = add_history(module)
        module.update_service_inventory_from_nmap = lambda *a, **k: 0

        assert module.enqueue_db_write(build_job(history_id, SERVICES))
        assert module.flush_db_writes(5.0)

        single = [{'port': 80, 'protocol': 'tcp', 'state': 'open',
                   'service': 'http'}]
        assert module.enqueue_db_write(build_job(history_id, single))
        assert module.flush_db_writes(5.0)

        ports = query(
            module.DB_FILE,
            'SELECT * FROM nmap_scan_ports WHERE scan_history_id = ?',
            (history_id,)
        )
        assert len(ports) == 1
        assert ports[0]['port'] == 80
        assert module.stop_db_writer() is True


def test_failed_scan_records_error_without_ports():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        new_db(module, tmp)
        history_id = add_history(module)

        called = []
        module.update_service_inventory_from_nmap = (
            lambda *a, **k: called.append(1)
        )

        assert module.enqueue_db_write(build_job(
            history_id, [], scan_success=False, scan_error='nmap failed'
        ))
        assert module.flush_db_writes(5.0)

        history = query(
            module.DB_FILE,
            'SELECT * FROM nmap_scan_history WHERE id = ?',
            (history_id,)
        )[0]
        assert history['success'] == 0
        assert history['error'] == 'nmap failed'
        assert query(
            module.DB_FILE,
            'SELECT * FROM nmap_scan_ports WHERE scan_history_id = ?',
            (history_id,)
        ) == []
        assert not called
        assert module.stop_db_writer() is True


def test_sync_fallback_matches_async():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        new_db(module, tmp)
        module.update_service_inventory_from_nmap = lambda *a, **k: 0

        async_id = add_history(module)
        sync_id = add_history(module)

        assert module.enqueue_db_write(build_job(async_id, SERVICES))
        assert module.flush_db_writes(5.0)

        # The fallback path the scan uses when the writer is unavailable.
        with sqlite3.connect(module.DB_FILE) as conn:
            conn.execute('PRAGMA foreign_keys = ON')
            module._db_write_apply(conn, build_job(sync_id, SERVICES))

        strip = ('id', 'scan_history_id')

        def shape(history_id):
            history = query(
                module.DB_FILE,
                'SELECT * FROM nmap_scan_history WHERE id = ?',
                (history_id,)
            )[0]
            ports = query(
                module.DB_FILE,
                'SELECT * FROM nmap_scan_ports WHERE scan_history_id = ? '
                'ORDER BY port',
                (history_id,)
            )
            return (
                {k: v for k, v in history.items() if k not in strip},
                [{k: v for k, v in port.items() if k not in strip}
                 for port in ports],
            )

        assert shape(async_id) == shape(sync_id)
        assert module.stop_db_writer() is True


def test_concurrent_enqueues_are_all_recorded():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        new_db(module, tmp)
        module.update_service_inventory_from_nmap = lambda *a, **k: 0

        history_ids = [
            add_history(module, f'aa:bb:cc:dd:ee:{index:02x}')
            for index in range(16)
        ]

        def worker(chunk):
            for history_id in chunk:
                assert module.enqueue_db_write(build_job(history_id, SERVICES))

        threads = [
            threading.Thread(target=worker, args=(history_ids[i::4],))
            for i in range(4)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert module.flush_db_writes(15.0) is True
        assert module._DB_WRITER_PENDING == 0

        # 16 scans x 2 valid ports; the non-numeric port is skipped.
        assert query(
            module.DB_FILE, 'SELECT COUNT(*) AS n FROM nmap_scan_ports'
        )[0]['n'] == 32
        assert query(
            module.DB_FILE,
            'SELECT COUNT(*) AS n FROM nmap_scan_history '
            'WHERE finished_at IS NOT NULL'
        )[0]['n'] == 16
        assert module.stop_db_writer() is True


def test_flush_without_writer_is_true():
    module = load_module()
    assert module._DB_WRITER_THREAD is None
    assert module.flush_db_writes(1.0) is True
    assert module.stop_db_writer() is True


def main():
    test_async_job_is_committed_and_drained()
    test_rescan_replaces_ports()
    test_failed_scan_records_error_without_ports()
    test_sync_fallback_matches_async()
    test_concurrent_enqueues_are_all_recorded()
    test_flush_without_writer_is_true()
    print('DEFERRED_DB_WRITES=PASS')


if __name__ == '__main__':
    main()

