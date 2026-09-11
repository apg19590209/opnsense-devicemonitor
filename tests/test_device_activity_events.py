import importlib.util
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


def load_module():
    import builtins

    repo_defaults = (
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

    real_open = builtins.open

    def test_open(path, *args, **kwargs):
        if str(path) == (
            "/usr/local/opnsense/mvc/app/models/OPNsense/"
            "DeviceMonitor/defaults.json"
        ):
            path = repo_defaults
        return real_open(path, *args, **kwargs)

    spec = importlib.util.spec_from_file_location(
        "devicemonitor_activity_events_test",
        SOURCE,
    )
    module = importlib.util.module_from_spec(spec)

    builtins.open = test_open
    try:
        spec.loader.exec_module(module)
    finally:
        builtins.open = real_open

    module.log = lambda message: None
    return module


def prepare_runtime(module):
    module.load_config = lambda: {"enabled": False}
    module.detect_source_capabilities = lambda: {
        "hostwatch": {"readable": True},
        "kea": {
            "queryable": False,
            "active": False,
            "lease4_get_all": False,
        },
        "isc": {"enabled": False},
        "dnsmasq": {"configured": False},
    }
    module.prime_hostwatch_lan_visibility = lambda: None
    module.get_dhcp_descriptions = lambda: {}
    module.get_kea_ipv4_leases = lambda: []
    module.get_dnsmasq_descriptions = lambda: {}
    module.get_adguard_rewrite_hostnames = lambda config: {}
    module.apply_hostname_provenance = lambda *args: None
    module.is_device_active = lambda *args: True
    module.detect_recent_hostwatch_identity_events = (
        lambda *args, **kwargs: 0
    )
    module.detect_recent_hostwatch_ipv6_identity_events = (
        lambda *args, **kwargs: 0
    )
    module.get_new_high_identity_events = lambda *args, **kwargs: []
    module.should_send_identity_email = lambda *args, **kwargs: False
    module.run_scheduled_service_discovery = lambda: None


def test_device_state_changes_are_historical_and_deduplicated():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.LOG_FILE = str(Path(tmp) / "devicemonitor.log")
        module.init_db()

        mac = "aa:bb:cc:dd:ee:ff"
        first_seen = "2026-09-01 10:00:00"
        old_last_seen = "2026-09-11 10:00:00"
        new_last_seen = "2026-09-12 08:00:00"

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            lifecycle_id = conn.execute(
                """
                INSERT INTO device_lifecycles (
                    mac,
                    status,
                    hostname,
                    hostname_source,
                    ip,
                    vendor,
                    vlan,
                    first_seen,
                    last_seen
                )
                VALUES (?, 'active', ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mac,
                    "old-host",
                    "hostwatch",
                    "192.168.20.10",
                    "Test Vendor",
                    "LAN",
                    first_seen,
                    old_last_seen,
                ),
            ).lastrowid

            conn.execute(
                """
                INSERT INTO devices (
                    mac,
                    ip,
                    hostname,
                    hostname_source,
                    vendor,
                    vlan,
                    first_seen,
                    last_seen,
                    is_active,
                    lifecycle_id,
                    return_pending
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, 0)
                """,
                (
                    mac,
                    "192.168.20.10",
                    "old-host",
                    "hostwatch",
                    "Test Vendor",
                    "LAN",
                    first_seen,
                    old_last_seen,
                    lifecycle_id,
                ),
            )

            conn.execute(
                """
                INSERT INTO known_macs (mac, first_seen, last_seen)
                VALUES (?, ?, ?)
                """,
                (mac, first_seen, old_last_seen),
            )
            conn.commit()

        device = {
            "mac": mac,
            "ip": "192.168.20.11",
            "hostname": "new-host",
            "hostname_source": "kea",
            "vendor": "Test Vendor",
            "vlan": "IOT",
            "first_seen": first_seen,
            "last_seen": new_last_seen,
        }

        prepare_runtime(module)
        module.get_hostwatch_devices = lambda: [dict(device)]

        assert module.full_scan() == 0

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            rows = conn.execute(
                """
                SELECT event_type, old_value, new_value, lifecycle_id
                FROM device_activity_events
                WHERE mac = ?
                ORDER BY id
                """,
                (mac,),
            ).fetchall()

        expected = [
            (
                "IP_CHANGED",
                "192.168.20.10",
                "192.168.20.11",
                lifecycle_id,
            ),
            (
                "HOSTNAME_CHANGED",
                "old-host",
                "new-host",
                lifecycle_id,
            ),
            (
                "HOSTNAME_SOURCE_CHANGED",
                "hostwatch",
                "kea",
                lifecycle_id,
            ),
            (
                "INTERFACE_CHANGED",
                "LAN",
                "IOT",
                lifecycle_id,
            ),
        ]

        assert rows == expected

        # Repeating the same observation must not create duplicate events.
        assert module.full_scan() == 0

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            count = conn.execute(
                """
                SELECT COUNT(*)
                FROM device_activity_events
                WHERE mac = ?
                """,
                (mac,),
            ).fetchone()[0]

        assert count == 4

    print("DEVICE_ACTIVITY_STATE_CHANGES=PASS")


def main():
    test_device_state_changes_are_historical_and_deduplicated()
    print("DEVICE_ACTIVITY_EVENTS_REGRESSION=PASS")


if __name__ == "__main__":
    main()
