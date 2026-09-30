"""The shutdown drain must cover SIGTERM, not just the normal exit path.

v2.11 lifecycle, Tasks 6 and 7: a hard stop can leave records sitting in the
deferred writer queue. Task 6 drains on `main()`'s exit path, which covers normal
and error returns and SIGINT. SIGTERM never runs a `finally`, and
`service devicemonitor stop` sends SIGTERM, so Task 7 adds a handler that drains
with the same bound and then re-raises the signal.

These checks pin that behaviour:

  * `main()` installs the handler (a wiring pin, asserted against the source);
  * the handler commits a job that is still in flight when the signal arrives;
  * the handler always re-raises, so the exit status stays death-by-SIGTERM;
  * a second SIGTERM does not drain twice;
  * a platform that refuses the handler degrades to the exit-path drain.

The handler is driven directly and `_reraise_sigterm()` is stubbed, so the test
process is never signalled or killed. The end-to-end behaviour this models was
also measured out of process, with the real handler and a real SIGTERM: without
it returncode -15 and the queued row never committed; with it returncode -15 and
the row committed.
"""
import builtins
import importlib.util
import inspect
import signal
import sqlite3
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py'
DEFAULTS = ROOT / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'


def load_module():
    """Load scan_network.py with defaults.json redirected and logs captured."""
    original_open = builtins.open

    def test_open(path, *args, **kwargs):
        if str(path).endswith('/models/OPNsense/DeviceMonitor/defaults.json'):
            path = DEFAULTS
        return original_open(path, *args, **kwargs)

    spec = importlib.util.spec_from_file_location('dm_shutdown_drain', SOURCE)
    module = importlib.util.module_from_spec(spec)
    builtins.open = test_open
    try:
        spec.loader.exec_module(module)
    finally:
        builtins.open = original_open

    notes = []
    module.log = lambda message: notes.append(message)
    module.subprocess = SimpleNamespace(
        run=lambda *args, **kwargs: SimpleNamespace(returncode=0)
    )
    return module, notes


def install_signal_recorder(module):
    """Replace the module's `signal` with a recorder, returning the call list."""
    calls = []
    module.signal = SimpleNamespace(
        SIGTERM=signal.SIGTERM,
        SIG_DFL=signal.SIG_DFL,
        signal=lambda sig, handler: calls.append((sig, handler)),
    )
    return calls


def queue_one_job(module, tmp, delay=0.4):
    """Create the schema, add a history row and enqueue its completion."""
    module.DB_FILE = str(Path(tmp) / 'devices.db')
    module._db_health_checked_path = None
    module._SIGTERM_DRAIN_DONE = False
    module.init_db()
    module.update_service_inventory_from_nmap = lambda *a, **k: 0

    conn = sqlite3.connect(module.DB_FILE)
    cursor = conn.execute(
        'INSERT INTO nmap_scan_history (mac, ip, scan_type, started_at) '
        'VALUES (?, ?, ?, ?)',
        ('aa:bb:cc:dd:ee:01', '192.168.1.10', 'manual', '2026-10-01 00:00:00')
    )
    history_id = cursor.lastrowid
    conn.commit()
    conn.close()

    real_apply = module._db_write_apply

    def slow_apply(conn, job):
        time.sleep(delay)
        return real_apply(conn, job)

    module._db_write_apply = slow_apply
    assert module.enqueue_db_write({
        'history_id': history_id,
        'mac': 'aa:bb:cc:dd:ee:01',
        'ip': '192.168.1.10',
        'vlan': 'lan',
        'finished_at': '2026-10-01 00:00:03',
        'scan_success': True,
        'scan_error': None,
        'services': [],
        'nmap_version': '7.95',
        'nmap_elapsed': 3.5,
        'os_hint': 'Linux 5.x',
        'email_sent': 0,
        'email_error': None,
    })
    return history_id


def finished_at(module, history_id):
    conn = sqlite3.connect(module.DB_FILE)
    try:
        return conn.execute(
            'SELECT finished_at FROM nmap_scan_history WHERE id = ?',
            (history_id,)
        ).fetchone()[0]
    finally:
        conn.close()


def test_main_installs_the_sigterm_handler():
    module, notes = load_module()
    calls = install_signal_recorder(module)

    module._install_sigterm_drain()

    assert calls == [(signal.SIGTERM, module._sigterm_drain_handler)], calls

    # Wiring pin: the handler only protects a real run if main() installs it and
    # keeps the matching exit-path drain.
    main_source = inspect.getsource(module.main)
    assert '_install_sigterm_drain()' in main_source
    assert 'flush_db_writes(SHUTDOWN_DRAIN_TIMEOUT)' in main_source
    assert module.SHUTDOWN_DRAIN_TIMEOUT == 5.0


def test_sigterm_commits_a_job_that_is_still_in_flight():
    module, notes = load_module()
    reraised = []
    module._reraise_sigterm = lambda: reraised.append(1)

    with tempfile.TemporaryDirectory() as tmp:
        history_id = queue_one_job(module, tmp, delay=0.4)
        assert module._DB_WRITER_PENDING == 1
        assert finished_at(module, history_id) is None   # still sitting in the queue

        module._sigterm_drain_handler(signal.SIGTERM, None)

        assert finished_at(module, history_id) == '2026-10-01 00:00:03'
        assert module._DB_WRITER_PENDING == 0
        assert module._SIGTERM_DRAIN_DONE is True
        assert reraised == [1], 'must re-raise so the exit stays death-by-SIGTERM'
        assert any('SIGTERM received' in n for n in notes), notes
        assert module.stop_db_writer() is True


def test_second_sigterm_does_not_drain_again():
    module, notes = load_module()
    reraised = []
    module._reraise_sigterm = lambda: reraised.append(1)

    with tempfile.TemporaryDirectory() as tmp:
        queue_one_job(module, tmp, delay=0.1)
        module._sigterm_drain_handler(signal.SIGTERM, None)

        drains = []
        module.flush_db_writes = lambda timeout=10.0: drains.append(timeout) or True
        module._sigterm_drain_handler(signal.SIGTERM, None)

        assert drains == [], 'a repeated SIGTERM means stop now, not drain twice'
        assert reraised == [1, 1]
        assert module.stop_db_writer() is True


def test_platform_that_refuses_the_handler_is_not_fatal():
    module, notes = load_module()

    def refuse(sig, handler):
        raise ValueError('signal only works in main thread')

    module.signal = SimpleNamespace(
        SIGTERM=signal.SIGTERM, SIG_DFL=signal.SIG_DFL, signal=refuse
    )

    module._install_sigterm_drain()      # must not raise

    assert any('Could not install the SIGTERM drain handler' in n for n in notes), notes


def main():
    test_main_installs_the_sigterm_handler()
    test_sigterm_commits_a_job_that_is_still_in_flight()
    test_second_sigterm_does_not_drain_again()
    test_platform_that_refuses_the_handler_is_not_fatal()
    print('SHUTDOWN_DRAIN=PASS')


if __name__ == '__main__':
    main()
