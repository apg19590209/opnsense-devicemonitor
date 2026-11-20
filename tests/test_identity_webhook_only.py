"""Decision 36: identity-conflict alerts are webhook-only.

Pins the corrected identity delivery policy: one webhook leg that keeps the
HA suppression and cooldown behaviour, advances `notified_at` only when the
webhook reports a successful send, and leaves the stored
`identity_email_enabled` preference inert while new-device email/webhook and
scan-result email are untouched.
"""
import builtins
import importlib.util
import re
import sqlite3
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py"
DEFAULTS = ROOT / "src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json"
CONTROLLER = ROOT / "src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/ConfigController.php"
VIEW = ROOT / "src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt"
VERSION = re.search(
    r'^VERSION=([0-9.]+)$',
    (ROOT / 'install-unattended.sh').read_text(),
    re.M,
).group(1)
MANIFEST = ROOT / ("release/v%s-runtime.manifest" % VERSION)

IFCONFIG_MASTER = """re0: flags=1008843<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST> metric 0 mtu 1500
\tinet 192.168.20.1 netmask 0xffffff00 broadcast 192.168.20.255
\tcarp: MASTER vhid 1 advbase 1 advskew 0
"""

IFCONFIG_BACKUP = """re0: flags=1008843<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST> metric 0 mtu 1500
\tinet 192.168.20.24 netmask 0xffffff00 broadcast 192.168.20.255
\tcarp: BACKUP vhid 1 advbase 1 advskew 100
"""

EVENT = {
    "id": 7,
    "detected_at": "2026-11-15 01:00:00",
    "event_type": "IP_IDENTITY_CHANGED",
    "severity": "high",
    "mac": "aa:bb:cc:dd:ee:01",
    "other_mac": "aa:bb:cc:dd:ee:02",
    "ip": "192.168.20.50",
    "other_ip": "",
    "interface": "re0",
    "other_interface": "",
    "details": "{}",
}


def networks_fixture(device="re0"):
    import ipaddress
    return [{
        "name": "lan",
        "description": "LAN",
        "device": device,
        "ip": "192.168.20.1",
        "subnet": "24",
        "network": ipaddress.ip_network("192.168.20.0/24"),
    }]


def load_module():
    original_open = builtins.open

    def test_open(path, *args, **kwargs):
        if str(path).endswith("/models/OPNsense/DeviceMonitor/defaults.json"):
            path = DEFAULTS
        return original_open(path, *args, **kwargs)

    spec = importlib.util.spec_from_file_location("devicemonitor_identity_webhook_only", SOURCE)
    module = importlib.util.module_from_spec(spec)
    builtins.open = test_open
    try:
        spec.loader.exec_module(module)
    finally:
        builtins.open = original_open
    module.log = lambda message: None
    return module


def test_email_leg_and_ui_control_are_absent():
    module = load_module()
    for name in ("should_send_identity_mail", "send_identity_mail"):
        assert not hasattr(module, name), name
    source = SOURCE.read_text(encoding="utf-8")
    assert "notify_identity_mail" not in source
    view = VIEW.read_text(encoding="utf-8")
    assert "identity_email_enabled" not in view
    assert "Also email identity conflict alerts" not in view
    rows = {row.split()[2]: row.split() for row in MANIFEST.read_text().splitlines()}
    assert "src/opnsense/scripts/OPNsense/DeviceMonitor/notify_identity_mail.php" not in rows
    print("IDENTITY_EMAIL_LEG_ABSENT=PASS")


def test_webhook_gates_ignore_the_stored_preference():
    module = load_module()
    enabled = {
        "enabled": True,
        "identity_webhook_enabled": True,
        "webhook_enabled": True,
        "webhook_url": "https://example.invalid/hook",
        "identity_email_enabled": True,
        "email_enabled": True,
        "email_to": "operator@example.invalid",
    }
    events = [EVENT]
    assert module.should_send_identity_email(enabled, events) is True
    for off in ("enabled", "identity_webhook_enabled", "webhook_enabled"):
        assert module.should_send_identity_email(dict(enabled, **{off: False}), events) is False
    assert module.should_send_identity_email(dict(enabled, webhook_url=""), events) is False
    assert module.should_send_identity_email(enabled, []) is False
    assert module.should_send_identity_email(dict(enabled, identity_email_enabled=False), events) is True
    print("IDENTITY_WEBHOOK_GATES=PASS")


def run_cycle(ifconfig, identity_events, send_result, overrides=None):
    """Run one full_scan() with patched edges; return webhook calls and DB state."""
    module = load_module()
    calls = {"identity": [], "new_device": [], "email": [], "discovery": []}
    cfg = dict(module.load_config())
    cfg.update({
        "enabled": True,
        "monitored_interfaces": "lan",
        "identity_webhook_enabled": True,
        "webhook_enabled": True,
        "webhook_url": "https://example.invalid/hook",
        "email_enabled": True,
        "email_to": "netops@example.invalid",
        "identity_email_enabled": True,
        "service_email_enabled": False,
        "targeted_nmap_enabled": False,
        "email_vlans": "",
        "webhook_vlans": "",
        "email_reminder_new_device": 0,
        "email_reminder_identity": 0,
        "email_reminder_scan": 0,
        "email_reminder_service": 0,
    })
    cfg.update(overrides or {})

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()
        real_gate = module.service_observation_allowed

        def gate(networks, network_text=None, config=None):
            return real_gate(networks, ifconfig, config=config)

        module.service_observation_allowed = gate
        module.load_config = lambda: cfg
        module.resolve_monitored_networks = lambda cfg: (networks_fixture(), None)
        module.detect_source_capabilities = lambda: {
            "hostwatch": {"readable": True},
            "kea": {"active": False, "queryable": False, "lease4_get_all": False,
                    "enabled": False},
            "isc": {"enabled": False},
            "dnsmasq": {"configured": False},
        }
        real_subprocess = module.subprocess

        class Shim:
            DEVNULL = real_subprocess.DEVNULL
            PIPE = real_subprocess.PIPE
            TimeoutExpired = real_subprocess.TimeoutExpired

            class Done:
                def __init__(self, code):
                    self.returncode = code

            @staticmethod
            def run(args, *a, **k):
                return Shim.Done(1)

        module.subprocess = Shim
        module.get_hostwatch_devices = lambda networks: [{
            "mac": "aa:bb:cc:dd:ee:99",
            "ip": "192.168.20.99",
            "hostname": "",
            "hostname_source": "none",
            "vendor": "",
            "vlan": "",
            "first_seen": "2026-11-15 00:00:00",
            "last_seen": "2026-11-15 01:00:00",
        }]
        module.get_dhcp_descriptions = lambda: {}
        module.get_kea_ipv4_leases = lambda: []
        module.get_dnsmasq_descriptions = lambda: {}
        module.get_unbound_hostnames = lambda: {}
        module.get_adguard_rewrite_hostnames = lambda cfg: {}
        module.get_pihole_hostnames = lambda cfg: {}
        module.apply_hostname_provenance = lambda *a, **k: None
        module.is_device_active = lambda *a, **k: True
        module.detect_recent_hostwatch_identity_events = lambda *a, **k: 0
        module.detect_recent_hostwatch_ipv6_identity_events = lambda *a, **k: 0
        # The detector is exercised elsewhere; seed its recorded event so this
        # harness measures only the delivery/notified_at behaviour.
        with sqlite3.connect(module.DB_FILE) as conn:
            for event in identity_events:
                conn.execute(
                    "INSERT INTO device_identity_events (id, mac, event_type, severity, ip,"
                    " other_ip, other_mac, interface, other_interface, details)"
                    " VALUES (?, ?, ?, ?, ?, '', ?, ?, '', ?)",
                    (event["id"], event["mac"], event["event_type"], event["severity"],
                     event["ip"], event["other_mac"], event["interface"], event["details"]))
            conn.commit()
        module.get_new_high_identity_events = lambda conn, start: list(identity_events)
        module.get_pending_high_identity_reminders = lambda conn, cfg: []
        module.send_identity_email = (
            lambda events: calls["identity"].append(list(events)) is None and send_result
        )
        module.run_scheduled_service_discovery = (
            lambda *a, **k: calls["discovery"].append(1) or []
        )
        module.process_service_alerts = lambda cfg, nets: None
        module.send_email_via_php_api = lambda d, s: calls["email"].append(list(d))
        module.send_webhook_via_php_api = lambda d, s: calls["new_device"].append(list(d))

        rc = module.full_scan()
        assert rc == 0, rc
        with sqlite3.connect(module.DB_FILE) as conn:
            rows = conn.execute("SELECT id, notified_at FROM device_identity_events").fetchall()
    return calls, rows


def test_master_success_advances_notified_at():
    calls, rows = run_cycle(IFCONFIG_MASTER, [EVENT], True)
    assert calls["identity"], calls
    assert [event["id"] for event in calls["identity"][0]] == [EVENT["id"]], calls
    assert len(rows) == 1 and rows[0][0] == EVENT["id"] and rows[0][1], rows
    print("IDENTITY_MASTER_NOTIFIED_ON_SUCCESS=PASS")


def test_failed_send_does_not_advance_notified_at():
    for label, result in (("send failed", False), ("send skipped", False)):
        calls, rows = run_cycle(IFCONFIG_MASTER, [EVENT], result)
        assert calls["identity"], (label, calls)
        assert rows == [(EVENT["id"], None)], (label, rows)
    print("IDENTITY_FAILED_SEND_NOT_RECORDED=PASS")


def test_backup_suppresses_webhook_and_notified_at():
    calls, rows = run_cycle(IFCONFIG_BACKUP, [EVENT], True)
    assert not calls["identity"], calls
    assert rows == [(EVENT["id"], None)], rows
    assert calls["new_device"] == [], calls
    print("IDENTITY_BACKUP_SUPPRESSED=PASS")


def test_cooldown_dedupes_the_same_event():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()
        with sqlite3.connect(module.DB_FILE) as conn:
            first = module.record_identity_event(
                conn, EVENT["mac"], "IP_IDENTITY_CHANGED", "high",
                ip=EVENT["ip"], other_mac=EVENT["other_mac"])
            conn.commit()
            second = module.record_identity_event(
                conn, EVENT["mac"], "IP_IDENTITY_CHANGED", "high",
                ip=EVENT["ip"], other_mac=EVENT["other_mac"])
            conn.commit()
    assert first is True and second is False, (first, second)
    print("IDENTITY_COOLDOWN_DEDUPE=PASS")


def test_email_paths_unaffected():
    module = load_module()
    source = SOURCE.read_text(encoding="utf-8")
    for name in ("send_email_via_php_api", "send_webhook_via_php_api",
                 "notify_scan_email.php", "nmap_scan_pending"):
        assert name in source, name
    # identity_email_enabled is still accepted by the controller and preserved
    # without being acted on; the scanner no longer reads it as a setting.
    controller = CONTROLLER.read_text(encoding="utf-8")
    assert "identity_email_enabled" in controller
    defaults = DEFAULTS.read_text(encoding="utf-8")
    assert '"identity_email_enabled": "0"' in defaults
    loaded = module.load_config()
    assert "identity_email_enabled" not in loaded
    print("EMAIL_PATHS_AND_INERT_KEY=PASS")


def main():
    test_email_leg_and_ui_control_are_absent()
    test_webhook_gates_ignore_the_stored_preference()
    test_master_success_advances_notified_at()
    test_failed_send_does_not_advance_notified_at()
    test_backup_suppresses_webhook_and_notified_at()
    test_cooldown_dedupes_the_same_event()
    test_email_paths_unaffected()
    print("IDENTITY_WEBHOOK_ONLY=PASS")


if __name__ == "__main__":
    main()
