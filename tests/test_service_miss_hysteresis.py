"""A live host's service needs a second failed run before it is called gone.

v2.11 service-liveness noise fix (O3b). O3a stopped a host that Device Monitor
cannot see from generating outage verdicts. A *live* host still flipped on one
failed observation, and discovery runs hourly, so a single bad sample became an
hour-long "outage" in the Devices view (the alert layer already confirms before
mailing, per Decision 47, but the inventory itself still lied for an hour).

`record_service_miss()` now counts consecutive failed observations:

  * the first miss increments `device_services.miss_count` and leaves `status`
    alone, so no activity event is written;
  * the second consecutive miss flips the row to `unavailable` once;
  * any successful verification resets the counter through
    `upsert_device_service()`, so isolated losses never accumulate.

These checks drive `discover_ssh_servers()` end to end against a temporary
database with the probe stubbed, so the real code path is exercised.
"""
import builtins
import importlib.util
import ipaddress
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "src"
    / "opnsense"
    / "scripts"
    / "OPNsense"
    / "DeviceMonitor"
    / "scan_network.py"
)
DEFAULTS = (
    ROOT
    / "src"
    / "opnsense"
    / "mvc"
    / "app"
    / "models"
    / "OPNsense"
    / "DeviceMonitor"
    / "defaults.json"
)

MAC = "aa:bb:cc:dd:ee:10"
IP = "198.51.100.10"


def load_module():
    """Load scan_network.py with defaults.json redirected to the checkout."""
    original_open = builtins.open

    def test_open(path, *args, **kwargs):
        if str(path).endswith('/models/OPNsense/DeviceMonitor/defaults.json'):
            path = DEFAULTS
        return original_open(path, *args, **kwargs)

    spec = importlib.util.spec_from_file_location(
        "devicemonitor_miss_hysteresis_test",
        SOURCE,
    )
    module = importlib.util.module_from_spec(spec)
    builtins.open = test_open
    try:
        spec.loader.exec_module(module)
    finally:
        builtins.open = original_open

    module.log = lambda message: None
    return module


def networks_fixture():
    return [{
        "name": "opt2",
        "description": "DMTEST",
        "device": "vlan0.60",
        "ip": "198.51.100.1",
        "subnet": "24",
        "network": ipaddress.ip_network("198.51.100.0/24"),
    }]


def seed(module):
    """Create the schema plus one active host carrying one verified SSH service."""
    module.init_db()

    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        conn.execute(
            "UPDATE service_alert_state "
            "SET last_service_id = 0, last_activity_event_id = 0 WHERE id = 1"
        )
        conn.execute(
            """
            INSERT INTO devices (mac, ip, vlan, is_active, last_seen)
            VALUES (?, ?, 'VLAN60', 1, '2026-10-31 10:00:00')
            """,
            (MAC, IP),
        )
        conn.execute(
            """
            INSERT INTO device_services (
                mac, ip, interface, service_type, port, protocol,
                status, detection_method, confidence,
                product, version, first_detected, last_verified
            )
            VALUES (?, ?, 'VLAN60', 'SSH', 22, 'tcp', 'available',
                    'ssh_banner', 'verified', 'OpenSSH', '9.9',
                    '2026-10-31 10:00:00', '2026-10-31 10:00:00')
            """,
            (MAC, IP),
        )
        conn.commit()


def stub_probes(module, succeeds):
    module._service_probe_candidates = lambda conn, *a, **k: {}
    module._nmap_tcp_service_candidates = lambda conn, *a, **k: []

    if succeeds:
        module._probe_ssh_service = lambda target, **kwargs: {
            "product": "SSH",
            "version": "OpenSSH_9.9",
        }
    else:
        module._probe_ssh_service = lambda target, **kwargs: None


def read_row(module):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        return conn.execute(
            "SELECT status, miss_count FROM device_services WHERE ip = ?",
            (IP,),
        ).fetchone()


def read_events(module):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM device_activity_events "
            "WHERE event_type = 'SERVICE_UNAVAILABLE'"
        ).fetchone()[0]



def test_threshold_constant():
    module = load_module()

    assert module.SERVICE_MISS_THRESHOLD >= 2, module.SERVICE_MISS_THRESHOLD
    assert module.SERVICE_MISS_THRESHOLD <= 3, module.SERVICE_MISS_THRESHOLD

    print("MISS_THRESHOLD_CONSTANT=PASS")


def test_first_miss_does_not_flip():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)
        stub_probes(module, succeeds=False)

        module.discover_ssh_servers(networks_fixture())

        status, misses = read_row(module)
        assert status == "available", status
        assert misses == 1, misses
        assert read_events(module) == 0, "event written on the first miss"

    print("MISS_FIRST_RUN_QUIET=PASS")


def test_second_miss_flips_once():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)
        stub_probes(module, succeeds=False)

        module.discover_ssh_servers(networks_fixture())
        module.discover_ssh_servers(networks_fixture())

        status, misses = read_row(module)
        assert status == "unavailable", status
        assert misses >= module.SERVICE_MISS_THRESHOLD, misses
        assert read_events(module) == 1, read_events(module)

        # A third failure must not write a second transition.
        module.discover_ssh_servers(networks_fixture())
        assert read_events(module) == 1, read_events(module)

    print("MISS_SECOND_RUN_FLIPS=PASS")


def test_success_between_misses_resets():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)

        stub_probes(module, succeeds=False)
        module.discover_ssh_servers(networks_fixture())

        status, misses = read_row(module)
        assert (status, misses) == ("available", 1), (status, misses)

        # The endpoint answers: the counter must be cleared.
        stub_probes(module, succeeds=True)
        module.discover_ssh_servers(networks_fixture())

        status, misses = read_row(module)
        assert (status, misses) == ("available", 0), (status, misses)

        # One further failure is again only the first miss.
        stub_probes(module, succeeds=False)
        module.discover_ssh_servers(networks_fixture())

        status, misses = read_row(module)
        assert (status, misses) == ("available", 1), (status, misses)
        assert read_events(module) == 0, read_events(module)

    print("MISS_SUCCESS_RESETS=PASS")


def test_unavailable_row_is_not_rewritten():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)
        stub_probes(module, succeeds=False)

        module.discover_ssh_servers(networks_fixture())
        module.discover_ssh_servers(networks_fixture())
        assert read_events(module) == 1, read_events(module)

        for _ in range(3):
            module.discover_ssh_servers(networks_fixture())

        assert read_events(module) == 1, read_events(module)

    print("MISS_ALREADY_DOWN_NO_REPEAT=PASS")


def main():
    test_threshold_constant()
    test_first_miss_does_not_flip()
    test_second_miss_flips_once()
    test_success_between_misses_resets()
    test_unavailable_row_is_not_rewritten()

    print("SERVICE_MISS_HYSTERESIS=PASS")


if __name__ == "__main__":
    main()
