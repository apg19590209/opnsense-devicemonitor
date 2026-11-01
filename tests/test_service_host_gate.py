"""An outage verdict requires a host that Device Monitor can still see.

v2.11 service-liveness noise fix (O3a). Live measurement on the testbed on
31 October 2026: a single discovery cycle wrote 16 `SERVICE_UNAVAILABLE`
events, and every one of them belonged to a host with
`devices.is_active = 0` and `last_seen = 2026-09-21` — six-week-stale
inventory. Only 1 of the 26 tracked devices was active. SSH/NTP/Web/phase-3
build their probe sets from `device_services` rows without consulting host
liveness, so a dead host's services are re-probed every hour, fail, and are
written `unavailable`; when the host answers again they flip back. That pair is
the operator's "offline then back online" noise.

`service_endpoint_host_gate()` makes the *negative* verdict conditional:

  * an endpoint whose device record says `is_active = 0` is not observed, so its
    service status is left untouched (no flip, no activity event, no alert);
  * an endpoint on an active device still flips, so the original detection is
    unchanged;
  * an endpoint with **no** device record — a gateway, a server hostwatch does
    not track, the firewall itself — is still allowed to flip. Missing inventory
    is not evidence of absence, so the gate fails open.

These checks pin the helper's semantics and drive `discover_ssh_servers()` end
to end against a temporary database with the probe stubbed to fail.
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

INACTIVE_MAC = "aa:bb:cc:dd:ee:01"
INACTIVE_IP = "198.51.100.10"
ACTIVE_MAC = "aa:bb:cc:dd:ee:02"
ACTIVE_IP = "198.51.100.11"
UNTRACKED_IP = "198.51.100.12"


def load_module():
    """Load scan_network.py with defaults.json redirected to the checkout."""
    original_open = builtins.open

    def test_open(path, *args, **kwargs):
        if str(path).endswith('/models/OPNsense/DeviceMonitor/defaults.json'):
            path = DEFAULTS
        return original_open(path, *args, **kwargs)

    spec = importlib.util.spec_from_file_location(
        "devicemonitor_host_gate_test",
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
    """Create the schema, two device records and one SSH service per endpoint."""
    module.init_db()

    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        conn.execute(
            "UPDATE service_alert_state "
            "SET last_service_id = 0, last_activity_event_id = 0 WHERE id = 1"
        )
        for mac, ip, active in (
            (INACTIVE_MAC, INACTIVE_IP, 0),
            (ACTIVE_MAC, ACTIVE_IP, 1),
        ):
            conn.execute(
                """
                INSERT INTO devices (mac, ip, vlan, is_active, last_seen)
                VALUES (?, ?, 'VLAN60', ?, '2026-09-21 13:45:11')
                """,
                (mac, ip, active),
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
                        '2026-09-21 13:45:11', '2026-09-21 13:45:11')
                """,
                (mac, ip),
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
                    '2026-09-21 13:45:11', '2026-09-21 13:45:11')
            """,
            ("aa:bb:cc:dd:ee:03", UNTRACKED_IP),
        )
        conn.commit()


def stub_failing_probes(module):
    module._service_probe_candidates = lambda conn, *a, **k: {}
    module._nmap_tcp_service_candidates = lambda conn, *a, **k: []
    module._probe_ssh_service = lambda target, **kwargs: None


def read_status(module, ip):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        return conn.execute(
            "SELECT status FROM device_services WHERE ip = ? "
            "AND service_type = 'SSH' AND detection_method = 'ssh_banner'",
            (ip,),
        ).fetchone()[0]


def read_event_count(module, ip):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        rows = conn.execute(
            "SELECT details FROM device_activity_events "
            "WHERE event_type = 'SERVICE_UNAVAILABLE'"
        ).fetchall()
    return sum(1 for (details,) in rows if f"|{ip}|" in (details or ""))



def test_gate_helper_semantics():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            gate = module.service_endpoint_host_gate(conn)

        assert gate(INACTIVE_IP) is False, gate(INACTIVE_IP)
        assert gate(ACTIVE_IP) is True, gate(ACTIVE_IP)
        assert gate(UNTRACKED_IP) is True, gate(UNTRACKED_IP)
        assert gate("") is True
        assert gate(None) is True

    print("HOST_GATE_HELPER=PASS")


def test_inactive_host_is_not_flipped():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)
        stub_failing_probes(module)

        module.discover_ssh_servers(networks_fixture())

        assert read_status(module, INACTIVE_IP) == "available", "flipped"
        assert read_event_count(module, INACTIVE_IP) == 0, "event written"

    print("HOST_GATE_INACTIVE_UNTOUCHED=PASS")


def test_active_host_still_flips():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)
        stub_failing_probes(module)

        # Two consecutive failed runs: the miss counter flips the row on the
        # second one (Decision 49), so a single bad sample stays silent.
        module.discover_ssh_servers(networks_fixture())
        module.discover_ssh_servers(networks_fixture())

        assert read_status(module, ACTIVE_IP) == "unavailable", "not flipped"
        assert read_event_count(module, ACTIVE_IP) == 1, "no event"

    print("HOST_GATE_ACTIVE_FLIPS=PASS")


def test_untracked_endpoint_still_flips():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)
        stub_failing_probes(module)

        module.discover_ssh_servers(networks_fixture())
        module.discover_ssh_servers(networks_fixture())

        assert read_status(module, UNTRACKED_IP) == "unavailable", "not flipped"
        assert read_event_count(module, UNTRACKED_IP) == 1, "no event"

    print("HOST_GATE_UNTRACKED_FAILS_OPEN=PASS")


def main():
    test_gate_helper_semantics()
    test_inactive_host_is_not_flipped()
    test_active_host_still_flips()
    test_untracked_endpoint_still_flips()

    print("SERVICE_HOST_GATE=PASS")


if __name__ == "__main__":
    main()
