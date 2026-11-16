"""Identity events created during the current cycle must reach notification selection.

Regression for the ordering defect: `identity_event_start_id` was read *after* the
device loop, so a rotation-classified `IP_IDENTITY_CHANGED` recorded in that loop was
permanently invisible to `get_new_high_identity_events()` and never alerted.
"""
import builtins
import importlib.util
import json
import sqlite3
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py"
DEFAULTS = ROOT / "src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json"


def load_module():
    original_open = builtins.open

    def test_open(path, *args, **kwargs):
        if str(path).endswith("/models/OPNsense/DeviceMonitor/defaults.json"):
            path = DEFAULTS
        return original_open(path, *args, **kwargs)

    spec = importlib.util.spec_from_file_location("devicemonitor_identity_capture_order", SOURCE)
    module = importlib.util.module_from_spec(spec)
    builtins.open = test_open
    try:
        spec.loader.exec_module(module)
    finally:
        builtins.open = original_open
    module.log = lambda message: None
    return module


def db():
    module = load_module()
    tmp = tempfile.TemporaryDirectory()
    module.DB_FILE = str(Path(tmp.name) / "devices.db")
    module.init_db()
    return module, tmp


def seed_event(module, other_mac, event_type="IP_IDENTITY_CHANGED",
               mac="aa:bb:cc:dd:ee:01", ip="192.168.50.10"):
    with sqlite3.connect(module.DB_FILE) as conn:
        module.record_identity_event(conn, mac, event_type, "high",
                                     ip=ip, other_mac=other_mac,
                                     details=json.dumps({"source": "mac_rotation"}))
        conn.commit()


def test_start_snapshot_precedes_event_producers():
    """The high-water mark must be taken before anything can insert events."""
    text = SOURCE.read_text(encoding="utf-8")
    start = text.index("    identity_event_start_id = conn.execute(")
    rotation = next(i for i, line in enumerate(text.splitlines(keepends=True))
                    if "rotation = detect_mac_rotation(" in line)
    rotation_offset = len("".join(text.splitlines(keepends=True)[:rotation]))
    hostwatch = text.index("    identity_events = detect_recent_hostwatch_identity_events(")
    assert start < rotation_offset, "start_id snapshot must precede the rotation producer"
    assert start < hostwatch, "start_id snapshot must precede the hostwatch producer"
    print("IDENTITY_CAPTURE_ORDER_SNAPSHOT_FIRST=PASS")


def test_rotation_event_from_current_cycle_is_selected():
    module, tmp = db()
    with tmp:
        with sqlite3.connect(module.DB_FILE) as conn:
            start = conn.execute(
                "SELECT COALESCE(MAX(id), 0) FROM device_identity_events").fetchone()[0]
        seed_event(module, "aa:bb:cc:dd:ee:00")
        with sqlite3.connect(module.DB_FILE) as conn:
            selected = module.get_new_high_identity_events(conn, start)
    assert [e["event_type"] for e in selected] == ["IP_IDENTITY_CHANGED"], selected
    assert selected[0]["other_mac"] == "aa:bb:cc:dd:ee:00", selected
    print("IDENTITY_CAPTURE_ORDER_ROTATION_SELECTED=PASS")


def test_earlier_events_are_not_replayed():
    module, tmp = db()
    with tmp:
        seed_event(module, "aa:bb:cc:dd:ee:00")
        with sqlite3.connect(module.DB_FILE) as conn:
            start = conn.execute(
                "SELECT COALESCE(MAX(id), 0) FROM device_identity_events").fetchone()[0]
        seed_event(module, "aa:bb:cc:dd:ee:02", ip="192.168.50.11")
        with sqlite3.connect(module.DB_FILE) as conn:
            selected = module.get_new_high_identity_events(conn, start)
    assert len(selected) == 1 and selected[0]["ip"] == "192.168.50.11", selected
    print("IDENTITY_CAPTURE_ORDER_NO_REPLAY=PASS")


def test_dedupe_still_suppresses_repeats():
    module, tmp = db()
    with tmp:
        seed_event(module, "aa:bb:cc:dd:ee:00")
        with sqlite3.connect(module.DB_FILE) as conn:
            start = conn.execute(
                "SELECT COALESCE(MAX(id), 0) FROM device_identity_events").fetchone()[0]
        seed_event(module, "aa:bb:cc:dd:ee:00")  # identical unresolved event
        with sqlite3.connect(module.DB_FILE) as conn:
            rows = conn.execute("SELECT COUNT(*) FROM device_identity_events").fetchone()[0]
            selected = module.get_new_high_identity_events(conn, start)
    assert rows == 1, rows
    assert selected == [], selected
    print("IDENTITY_CAPTURE_ORDER_DEDUPE=PASS")


def test_medium_and_low_events_stay_unselected():
    module, tmp = db()
    with tmp:
        with sqlite3.connect(module.DB_FILE) as conn:
            start = conn.execute(
                "SELECT COALESCE(MAX(id), 0) FROM device_identity_events").fetchone()[0]
        with sqlite3.connect(module.DB_FILE) as conn:
            module.record_identity_event(conn, "aa:bb:cc:dd:ee:03",
                                         "MAC_MULTI_INTERFACE", "medium",
                                         ip="192.168.50.12")
            conn.commit()
        with sqlite3.connect(module.DB_FILE) as conn:
            selected = module.get_new_high_identity_events(conn, start)
    assert selected == [], selected
    print("IDENTITY_CAPTURE_ORDER_SEVERITY_FILTER=PASS")




def test_full_scan_alerts_on_a_rotation_event_from_the_same_cycle():
    """End-to-end: the cycle's own rotation event must reach the delivery call.

    The device loop records the rotation before anything queries
    `get_new_high_identity_events()`. If the snapshot were taken after the loop
    (the defect), the cycle logs the rotation but delivers nothing.
    """
    module = load_module()
    delivered = []
    events = []

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()
        cfg = dict(module.load_config())
        cfg.update({
            "enabled": True,
            "monitored_interfaces": "lan",
            "identity_webhook_enabled": True,
            "webhook_enabled": True,
            "webhook_url": "https://example.invalid/hook",
            "email_enabled": True,
            "email_to": "netops@example.invalid",
            "service_email_enabled": False,
            "targeted_nmap_enabled": False,
            "email_vlans": "",
            "webhook_vlans": "",
            "email_reminder_new_device": 0,
            "email_reminder_identity": 0,
            "email_reminder_scan": 0,
            "email_reminder_service": 0,
        })
        devices = [{
            "mac": "02:bb:cc:dd:ee:02",
            "ip": "192.168.50.20",
            "hostname": "",
            "hostname_source": "none",
            "vendor": "",
            "vlan": "",
            "first_seen": "2026-11-15 00:00:00",
            "last_seen": "2026-11-15 01:00:00",
        }]
        with sqlite3.connect(module.DB_FILE) as conn:
            conn.execute(
                "INSERT INTO devices (mac, ip, hostname, hostname_source, vendor, vlan,"
                " first_seen, last_seen, is_active, notification_pending)"
                " VALUES (?, ?, '', 'none', '', '', ?, ?, 1, 0)",
                ("aa:bb:cc:dd:ee:01", "192.168.50.20",
                 "2026-11-15 00:00:00", "2026-11-15 01:00:00"))
            # Only the displaced owner is known: the incoming MAC must look new
            # so the rotation classifier runs.
            conn.execute("INSERT INTO known_macs (mac) VALUES (?)",
                         ("aa:bb:cc:dd:ee:01",))
            conn.commit()

        module.load_config = lambda: cfg
        module.resolve_monitored_networks = lambda c: ([{
            "name": "lan", "description": "LAN", "device": "re0",
            "ip": "192.168.50.1", "subnet": "24",
            "network": __import__("ipaddress").ip_network("192.168.50.0/24"),
        }], None)
        module.service_observation_allowed = lambda *a, **k: (True, None, "no CARP")
        module.detect_source_capabilities = lambda: {
            "hostwatch": {"readable": True},
            "kea": {"active": False, "queryable": False, "lease4_get_all": False,
                    "enabled": False},
            "isc": {"enabled": False},
            "dnsmasq": {"configured": False},
        }

        class Shim:
            DEVNULL = module.subprocess.DEVNULL
            PIPE = module.subprocess.PIPE
            TimeoutExpired = module.subprocess.TimeoutExpired

            class Done:
                returncode = 1

            @staticmethod
            def run(*a, **k):
                return Shim.Done()

        module.subprocess = Shim
        module.get_hostwatch_devices = lambda networks: devices
        module.get_dhcp_descriptions = lambda: {}
        module.get_kea_ipv4_leases = lambda: []
        module.get_dnsmasq_descriptions = lambda: {}
        module.get_unbound_hostnames = lambda: {}
        module.get_adguard_rewrite_hostnames = lambda c: {}
        module.get_pihole_hostnames = lambda c: {}
        module.apply_hostname_provenance = lambda *a, **k: None
        module.is_device_active = lambda *a, **k: True
        module.detect_recent_hostwatch_identity_events = lambda *a, **k: 0
        module.detect_recent_hostwatch_ipv6_identity_events = lambda *a, **k: 0
        module.should_send_identity_email = lambda c, e: bool(e)
        module.send_identity_email = (
            lambda evts: delivered.append([e["id"] for e in evts]) is None and True)
        module.run_scheduled_service_discovery = lambda *a, **k: []
        module.process_service_alerts = lambda c, n: None
        module.send_email_via_php_api = lambda d, s: None
        module.send_webhook_via_php_api = lambda d, s: None

        assert module.full_scan() == 0
        with sqlite3.connect(module.DB_FILE) as conn:
            events = conn.execute(
                "SELECT id, event_type, severity, notified_at FROM device_identity_events"
            ).fetchall()

    assert len(events) == 1, events
    assert events[0][1] == "IP_IDENTITY_CHANGED" and events[0][2] == "high", events
    assert delivered == [[events[0][0]]], (delivered, events)
    assert events[0][3], "notified_at must be set after a successful delivery"
    print("IDENTITY_CAPTURE_ORDER_FULL_SCAN_DELIVERS=PASS")


def main():
    test_start_snapshot_precedes_event_producers()
    test_rotation_event_from_current_cycle_is_selected()
    test_earlier_events_are_not_replayed()
    test_dedupe_still_suppresses_repeats()
    test_medium_and_low_events_stay_unselected()
    test_full_scan_alerts_on_a_rotation_event_from_the_same_cycle()
    print("IDENTITY_EVENT_CAPTURE_ORDER_REGRESSION=PASS")


if __name__ == "__main__":
    main()
