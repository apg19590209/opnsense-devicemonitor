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
        if str(path) == "/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json":
            path = repo_defaults
        return real_open(path, *args, **kwargs)

    spec = importlib.util.spec_from_file_location(
        "devicemonitor_lifecycle_return_test",
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


def test_pending_return_survives_init_db():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.LOG_FILE = str(Path(tmp) / "devicemonitor.log")

        module.init_db()

        mac = "aa:bb:cc:dd:ee:ff"

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute(
                """
                INSERT INTO device_lifecycles
                    (mac, status, first_seen, last_seen, archived_at)
                VALUES (?, 'archived',
                        '2026-09-01 10:00:00',
                        '2026-09-02 10:00:00',
                        '2026-09-02 10:05:00')
                """,
                (mac,),
            )

            conn.execute(
                """
                INSERT INTO devices
                    (mac, lifecycle_id, return_pending)
                VALUES (?, NULL, 1)
                """,
                (mac,),
            )

            conn.execute(
                """
                INSERT INTO deleted_devices
                    (mac, last_seen)
                VALUES (?, '2026-09-02 10:00:00')
                """,
                (mac,),
            )

            conn.commit()

        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            device = conn.execute(
                """
                SELECT lifecycle_id, return_pending
                FROM devices
                WHERE mac = ?
                """,
                (mac,),
            ).fetchone()

            active_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM device_lifecycles
                WHERE mac = ? AND status = 'active'
                """,
                (mac,),
            ).fetchone()[0]

            archived_count = conn.execute(
                """
                SELECT COUNT(*)
                FROM device_lifecycles
                WHERE mac = ? AND status = 'archived'
                """,
                (mac,),
            ).fetchone()[0]

        assert device == (None, 1)
        assert active_count == 0
        assert archived_count == 1

    print("DEVICE_PENDING_RETURN_BACKFILL=PASS")



def test_returning_device_gets_fresh_first_seen():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.LOG_FILE = str(Path(tmp) / "devicemonitor.log")
        module.init_db()

        mac = "aa:bb:cc:dd:ee:ff"
        original_first = "2026-09-01 10:00:00"
        deleted_last = "2026-09-02 10:00:00"
        returned_at = "2026-09-11 12:00:00"

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            lifecycle_id = conn.execute(
                """
                INSERT INTO device_lifecycles
                    (mac, status, first_seen, last_seen, archived_at)
                VALUES (?, 'archived', ?, ?, ?)
                """,
                (mac, original_first, deleted_last, deleted_last),
            ).lastrowid

            conn.execute(
                """
                INSERT INTO devices
                    (mac, first_seen, last_seen, lifecycle_id, return_pending)
                VALUES (?, ?, ?, ?, 0)
                """,
                (mac, original_first, deleted_last, lifecycle_id),
            )

            conn.execute(
                """
                INSERT INTO deleted_devices (mac, last_seen)
                VALUES (?, ?)
                """,
                (mac, deleted_last),
            )

            conn.execute(
                """
                INSERT OR REPLACE INTO known_macs
                    (mac, first_seen, last_seen)
                VALUES (?, ?, ?)
                """,
                (mac, original_first, deleted_last),
            )
            conn.commit()

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
        module.get_hostwatch_devices = lambda: [{
            "mac": mac,
            "ip": "192.168.20.50",
            "hostname": "returned-device",
            "hostname_source": "hostwatch",
            "vendor": "Test Vendor",
            "vlan": "LAN",
            "first_seen": original_first,
            "last_seen": returned_at,
        }]
        module.get_dhcp_descriptions = lambda: {}
        module.get_kea_ipv4_leases = lambda: []
        module.get_dnsmasq_descriptions = lambda: {}
        module.get_adguard_rewrite_hostnames = lambda config: {}
        module.apply_hostname_provenance = lambda *args: None
        module.is_device_active = lambda *args: True
        module.detect_recent_hostwatch_identity_events = lambda *args, **kwargs: 0
        module.detect_recent_hostwatch_ipv6_identity_events = lambda *args, **kwargs: 0
        module.get_new_high_identity_events = lambda *args, **kwargs: []
        module.should_send_identity_email = lambda *args, **kwargs: False
        module.run_scheduled_service_discovery = lambda: None

        assert module.full_scan() == 0

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            device = conn.execute(
                """
                SELECT first_seen, lifecycle_id, return_pending
                FROM devices WHERE mac = ?
                """,
                (mac,),
            ).fetchone()

            lifecycle_first = conn.execute(
                """
                SELECT first_seen
                FROM device_lifecycles WHERE id = ?
                """,
                (lifecycle_id,),
            ).fetchone()[0]

            known_first = conn.execute(
                """
                SELECT first_seen
                FROM known_macs WHERE mac = ?
                """,
                (mac,),
            ).fetchone()[0]

        assert device == (returned_at, None, 1)
        assert lifecycle_first == original_first
        assert known_first == original_first

    print("DEVICE_RETURN_FIRST_SEEN_REGRESSION=PASS")

def main():
    test_pending_return_survives_init_db()
    test_returning_device_gets_fresh_first_seen()
    print("DEVICE_LIFECYCLE_RETURN_REGRESSION=PASS")


if __name__ == "__main__":
    main()
