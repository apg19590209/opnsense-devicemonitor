import importlib.util
import io
import ipaddress
import sqlite3
import tempfile
from contextlib import closing, redirect_stdout
from datetime import datetime, timedelta, UTC
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


def networks_fixture():
    return [{
        "name": "opt1",
        "description": "DMTEST",
        "device": "vlan0.50",
        "ip": "192.168.50.1",
        "subnet": "24",
        "network": ipaddress.ip_network("192.168.50.0/24"),
    }]


def prepare_runtime(module):
    module.load_config = lambda: {"enabled": False, "monitored_interfaces": "opt1"}
    module.resolve_monitored_networks = lambda config: (networks_fixture(), None)
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
    module.prime_selected_interface_visibility = lambda networks: None
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
    module.run_scheduled_service_discovery = lambda networks=None: None


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
                    "192.168.50.10",
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
                    "192.168.50.10",
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
            "ip": "192.168.50.11",
            "hostname": "new-host",
            "hostname_source": "kea",
            "vendor": "Test Vendor",
            "vlan": "IOT",
            "first_seen": first_seen,
            "last_seen": new_last_seen,
        }

        prepare_runtime(module)
        module.get_hostwatch_devices = lambda networks: [dict(device)]

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
                "192.168.50.10",
                "192.168.50.11",
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


def test_service_status_transitions_are_historical_and_deduplicated():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.LOG_FILE = str(Path(tmp) / "devicemonitor.log")
        module.init_db()

        mac = "aa:bb:cc:dd:ee:ff"

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            lifecycle_id = conn.execute(
                """
                INSERT INTO device_lifecycles (
                    mac,
                    status,
                    first_seen,
                    last_seen
                )
                VALUES (
                    ?,
                    'active',
                    '2026-09-12 08:00:00',
                    '2026-09-12 08:00:00'
                )
                """,
                (mac,),
            ).lastrowid

            conn.execute(
                """
                INSERT INTO devices (
                    mac,
                    ip,
                    vlan,
                    lifecycle_id,
                    return_pending
                )
                VALUES (?, ?, ?, ?, 0)
                """,
                (
                    mac,
                    "192.168.50.10",
                    "LAN",
                    lifecycle_id,
                ),
            )

            conn.execute(
                """
                INSERT INTO device_services (
                    mac,
                    ip,
                    interface,
                    service_type,
                    port,
                    protocol,
                    status,
                    detection_method,
                    confidence
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mac,
                    "192.168.50.10",
                    "LAN",
                    "SSH",
                    22,
                    "tcp",
                    "available",
                    "ssh_banner",
                    "verified",
                ),
            )

            # First real transition: available -> unavailable.
            conn.execute(
                """
                UPDATE device_services
                SET status = 'unavailable'
                WHERE mac = ?
                  AND service_type = 'SSH'
                  AND port = 22
                """,
                (mac,),
            )

            # Same status again must not create a duplicate event.
            conn.execute(
                """
                UPDATE device_services
                SET status = 'unavailable'
                WHERE mac = ?
                  AND service_type = 'SSH'
                  AND port = 22
                """,
                (mac,),
            )
            conn.commit()

            rows = conn.execute(
                """
                SELECT event_type,
                       old_value,
                       new_value,
                       details,
                       lifecycle_id
                FROM device_activity_events
                WHERE mac = ?
                ORDER BY id
                """,
                (mac,),
            ).fetchall()

            assert rows == [
                (
                    "SERVICE_UNAVAILABLE",
                    "available",
                    "unavailable",
                    "SSH|192.168.50.10|22|tcp|LAN|ssh_banner",
                    lifecycle_id,
                )
            ]

            # Exercise the real service upsert path for recovery.
            assert module.upsert_device_service(
                conn,
                mac,
                "192.168.50.10",
                "LAN",
                "SSH",
                22,
                "tcp",
                "ssh_banner",
                "verified",
                "2026-09-12 09:00:00",
                status="available",
                product="OpenSSH",
                version="9",
            )

            # Repeating the same available observation must not duplicate it.
            assert module.upsert_device_service(
                conn,
                mac,
                "192.168.50.10",
                "LAN",
                "SSH",
                22,
                "tcp",
                "ssh_banner",
                "verified",
                "2026-09-12 09:05:00",
                status="available",
                product="OpenSSH",
                version="9",
            )

            conn.commit()

            rows = conn.execute(
                """
                SELECT event_type,
                       old_value,
                       new_value,
                       details,
                       lifecycle_id
                FROM device_activity_events
                WHERE mac = ?
                ORDER BY id
                """,
                (mac,),
            ).fetchall()

        assert rows == [
            (
                "SERVICE_UNAVAILABLE",
                "available",
                "unavailable",
                "SSH|192.168.50.10|22|tcp|LAN|ssh_banner",
                lifecycle_id,
            ),
            (
                "SERVICE_AVAILABLE",
                "unavailable",
                "available",
                "SSH|192.168.50.10|22|tcp|LAN|ssh_banner",
                lifecycle_id,
            ),
        ]

    print("DEVICE_ACTIVITY_SERVICE_TRANSITIONS=PASS")


def test_out_of_scope_rows_are_not_reset():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.LOG_FILE = str(Path(tmp) / "devicemonitor.log")
        module.init_db()

        out_mac = "aa:bb:cc:dd:ee:01"
        in_mac = "aa:bb:cc:dd:ee:02"

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute(
                "INSERT INTO devices (mac, ip, is_active) VALUES (?, ?, 1)",
                (out_mac, "192.168.20.10"),
            )
            conn.execute(
                "INSERT INTO devices (mac, ip, is_active) VALUES (?, ?, 1)",
                (in_mac, "192.168.50.10"),
            )
            conn.commit()

        prepare_runtime(module)
        module.get_hostwatch_devices = lambda networks: [{
            "mac": in_mac,
            "ip": "192.168.50.10",
            "hostname": "in-scope",
            "hostname_source": "hostwatch",
            "vendor": "Test Vendor",
            "vlan": "VLAN50",
            "first_seen": "2026-09-01 10:00:00",
            "last_seen": "2026-09-12 08:00:00",
        }]

        assert module.full_scan() == 0

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            out_is_active = conn.execute(
                "SELECT is_active FROM devices WHERE mac = ?", (out_mac,)
            ).fetchone()[0]

        assert out_is_active == 1, out_is_active

    print("DEVICE_OUT_OF_SCOPE_NOT_RESET=PASS")


def test_out_of_scope_queue_does_not_starve_in_scope_scan():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.LOG_FILE = str(Path(tmp) / "devicemonitor.log")
        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute(
                "INSERT INTO devices (mac, ip, first_seen, nmap_scan_pending, "
                "nmap_scan_attempts) VALUES (?, ?, ?, 1, 0)",
                ("aa:bb:cc:dd:ee:01", "192.168.20.10", "2026-01-01 00:00:00"),
            )
            conn.execute(
                "INSERT INTO devices (mac, ip, first_seen, nmap_scan_pending, "
                "nmap_scan_attempts) VALUES (?, ?, ?, 1, 0)",
                ("aa:bb:cc:dd:ee:02", "192.168.20.11", "2026-01-01 00:00:01"),
            )
            conn.execute(
                "INSERT INTO devices (mac, ip, first_seen, nmap_scan_pending, "
                "nmap_scan_attempts) VALUES (?, ?, ?, 1, 0)",
                ("aa:bb:cc:dd:ee:03", "192.168.50.10", "2026-01-01 00:00:02"),
            )
            conn.commit()

        prepare_runtime(module)
        module.load_config = lambda: {
            "enabled": True,
            "monitored_interfaces": "opt1",
            "email_enabled": True,
            "email_to": "admin@example.test",
            "targeted_nmap_enabled": True,
            "nmap_max_per_cycle": 1,
            "email_vlans": "",
            "webhook_vlans": "",
        }
        module.get_unbound_hostnames = lambda: {}
        module.get_pihole_hostnames = lambda config: {}
        module.process_service_alerts = lambda config, networks: True
        module.send_email_via_php_api = lambda new_devices, in_scope_macs: None
        module.send_webhook_via_php_api = lambda new_devices, in_scope_macs: None

        scanned = []
        module.run_targeted_scan_with_history = (
            lambda device, config, scan_type: (scanned.append(device["mac"]) or True, "")
        )

        module.get_hostwatch_devices = lambda networks: [{
            "mac": "aa:bb:cc:dd:ee:03",
            "ip": "192.168.50.10",
            "hostname": "in-scope",
            "hostname_source": "hostwatch",
            "vendor": "Test Vendor",
            "vlan": "VLAN50",
            "first_seen": "2026-01-01 00:00:02",
            "last_seen": "2026-09-12 08:00:00",
        }]

        assert module.full_scan() == 0

        assert scanned == ["aa:bb:cc:dd:ee:03"], scanned

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            for mac in ("aa:bb:cc:dd:ee:01", "aa:bb:cc:dd:ee:02"):
                row = conn.execute(
                    "SELECT nmap_scan_pending, nmap_scan_attempts "
                    "FROM devices WHERE mac = ?",
                    (mac,),
                ).fetchone()
                assert row == (1, 0), (mac, row)

    print("DEVICE_OUT_OF_SCOPE_QUEUE_NO_STARVATION=PASS")


def test_out_of_scope_kea_does_not_trigger_identity():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.LOG_FILE = str(Path(tmp) / "devicemonitor.log")
        module.init_db()

        hw_path = str(Path(tmp) / "hostwatch.db")
        recent = (
            datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=30)
        ).strftime("%Y-%m-%d %H:%M:%S")

        with closing(sqlite3.connect(hw_path)) as hw_conn:
            hw_conn.execute(
                "CREATE TABLE v_hosts (id INTEGER PRIMARY KEY, interface_name TEXT, "
                "ip_address TEXT, ether_address TEXT, last_seen TEXT, protocol TEXT)"
            )
            hw_conn.execute(
                "INSERT INTO v_hosts (interface_name, ip_address, ether_address, "
                "last_seen, protocol) VALUES (?, ?, ?, ?, 'inet')",
                ("vlan0.50", "192.168.50.10", "aa:bb:cc:dd:ee:01", recent),
            )
            hw_conn.commit()

        module.HOSTWATCH_DB = hw_path

        # Conflicting out-of-scope Kea lease sharing the in-scope host's MAC.
        kea_leases = [{
            "ip": "192.168.20.10",
            "mac": "aa:bb:cc:dd:ee:01",
            "hostname": "out-of-scope",
            "active": True,
            "subnet_id": 1,
            "cltt": 1,
            "expires_at": 1,
        }]

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            created = module.detect_recent_hostwatch_identity_events(
                conn,
                minutes=5,
                kea_leases=kea_leases,
                networks=networks_fixture(),
            )

        assert created == 0, created

    print("DEVICE_OUT_OF_SCOPE_KEA_INERT=PASS")


def test_update_status_only_reports_scoped_totals():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.LOG_FILE = str(Path(tmp) / "devicemonitor.log")
        module.init_db()

        module.load_config = lambda: {"monitored_interfaces": "opt1"}
        module.resolve_monitored_networks = lambda config: (networks_fixture(), None)

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute(
                "INSERT INTO devices (mac, ip, is_active) VALUES ('aa:bb:cc:dd:ee:01', '192.168.50.10', 1)"
            )
            conn.execute(
                "INSERT INTO devices (mac, ip, is_active) VALUES ('aa:bb:cc:dd:ee:02', '192.168.50.11', 0)"
            )
            conn.execute(
                "INSERT INTO devices (mac, ip, is_active) VALUES ('aa:bb:cc:dd:ee:03', '192.168.20.10', 1)"
            )
            conn.execute(
                "INSERT INTO devices (mac, ip, is_active) VALUES ('aa:bb:cc:dd:ee:04', '192.168.20.11', 1)"
            )
            conn.execute(
                "INSERT INTO devices (mac, ip, is_active) VALUES ('aa:bb:cc:dd:ee:05', '192.168.20.12', 0)"
            )
            conn.commit()

        module.get_hostwatch_devices = lambda networks: [{
            "mac": "aa:bb:cc:dd:ee:01",
            "ip": "192.168.50.10",
            "hostname": "in-scope",
            "vendor": "V",
            "vlan": "VLAN50",
            "first_seen": "2026-09-01 10:00:00",
            "last_seen": "2026-09-12 08:00:00",
        }]
        module.is_device_active = lambda *args: True

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = module.update_status_only()

        assert rc == 0, rc
        assert "OK: 1/2 online" in buf.getvalue(), buf.getvalue()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            rows = conn.execute(
                "SELECT mac, is_active FROM devices "
                "WHERE ip LIKE '192.168.20.%' ORDER BY mac"
            ).fetchall()
            assert rows == [
                ("aa:bb:cc:dd:ee:03", 1),
                ("aa:bb:cc:dd:ee:04", 1),
                ("aa:bb:cc:dd:ee:05", 0),
            ], rows

    print("DEVICE_UPDATE_ONLY_SCOPED_TOTALS=PASS")


def test_full_scan_reports_scoped_totals():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.LOG_FILE = str(Path(tmp) / "devicemonitor.log")
        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute(
                "INSERT INTO devices (mac, ip, is_active) VALUES ('aa:bb:cc:dd:ee:01', '192.168.50.10', 1)"
            )
            conn.execute(
                "INSERT INTO devices (mac, ip, is_active) VALUES ('aa:bb:cc:dd:ee:02', '192.168.50.11', 0)"
            )
            conn.execute(
                "INSERT INTO devices (mac, ip, is_active) VALUES ('aa:bb:cc:dd:ee:03', '192.168.20.10', 1)"
            )
            conn.execute(
                "INSERT INTO devices (mac, ip, is_active) VALUES ('aa:bb:cc:dd:ee:04', '192.168.20.11', 1)"
            )
            conn.commit()

        prepare_runtime(module)
        module.get_unbound_hostnames = lambda: {}
        module.get_pihole_hostnames = lambda config: {}
        module.process_service_alerts = lambda config, networks: True

        messages = []
        module.log = lambda message: messages.append(message)

        module.get_hostwatch_devices = lambda networks: [{
            "mac": "aa:bb:cc:dd:ee:01",
            "ip": "192.168.50.10",
            "hostname": "in-scope",
            "hostname_source": "hostwatch",
            "vendor": "V",
            "vlan": "VLAN50",
            "first_seen": "2026-09-01 10:00:00",
            "last_seen": "2026-09-12 08:00:00",
        }]

        assert module.full_scan() == 0

        online_msg = [m for m in messages if "Online:" in m]
        assert online_msg, messages
        assert "Online: 1/2" in online_msg[0], online_msg[0]

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            rows = conn.execute(
                "SELECT mac, is_active FROM devices "
                "WHERE ip LIKE '192.168.20.%' ORDER BY mac"
            ).fetchall()
            assert rows == [
                ("aa:bb:cc:dd:ee:03", 1),
                ("aa:bb:cc:dd:ee:04", 1),
            ], rows

    print("DEVICE_FULL_SCAN_SCOPED_TOTALS=PASS")


def main():
    test_device_state_changes_are_historical_and_deduplicated()
    test_service_status_transitions_are_historical_and_deduplicated()
    test_out_of_scope_rows_are_not_reset()
    test_out_of_scope_queue_does_not_starve_in_scope_scan()
    test_out_of_scope_kea_does_not_trigger_identity()
    test_update_status_only_reports_scoped_totals()
    test_full_scan_reports_scoped_totals()
    print("DEVICE_ACTIVITY_EVENTS_REGRESSION=PASS")


if __name__ == "__main__":
    main()
