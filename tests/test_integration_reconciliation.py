"""Pin the behaviours that must survive the main/2.13 reconciliation.

The v2.12 line carries the state-change scan and alert refactor, identity email,
repeat reminders, configuration visibility and non-HA fail-open behaviour. The
2.13 line carries CARP role gating, standby hygiene, O4 ageing and the verified
installer payload. This suite exercises the combined tree rather than either
parent alone, so a future conflict resolution cannot pass by keeping one side.
"""
import builtins
import importlib.util
import ipaddress
import json
import sqlite3
import tempfile
from contextlib import closing
from datetime import datetime, timedelta
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
MANIFEST = ROOT / "release" / "v2.14.0-runtime.manifest"

IFCONFIG_BACKUP = """re0: flags=1008843<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST> metric 0 mtu 1500
\tinet 192.168.20.24 netmask 0xffffff00 broadcast 192.168.20.255
\tcarp: BACKUP vhid 1 advbase 1 advskew 100
"""


def load_module():
    original_open = builtins.open

    def test_open(path, *args, **kwargs):
        if str(path).endswith('/models/OPNsense/DeviceMonitor/defaults.json'):
            path = DEFAULTS
        return original_open(path, *args, **kwargs)

    spec = importlib.util.spec_from_file_location(
        "devicemonitor_integration_reconciliation_test",
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
        "name": "lan",
        "description": "LAN",
        "device": "re0",
        "ip": "192.168.20.1",
        "subnet": "24",
        "network": ipaddress.ip_network("192.168.20.0/24"),
    }]


def test_combined_defaults_and_config_loading():
    defaults = json.loads(DEFAULTS.read_text())
    config = defaults["config"]

    assert defaults["version"] == "2.14.0"
    for key in (
        "identity_email_enabled",
        "email_reminder_scan",
        "email_reminder_service",
        "email_reminder_identity",
        "email_reminder_new_device",
        "visibility_prime_interval",
        "ha_carp_enabled",
        "ha_role_override",
        "ha_notify_failover",
    ):
        assert key in config, key

    module = load_module()
    file_values = {
        "identity_email_enabled": "1",
        "email_reminder_scan": "5",
        "email_reminder_service": "10",
        "email_reminder_identity": "15",
        "email_reminder_new_device": "30",
        "visibility_prime_interval": "60",
        "ha_carp_enabled": "0",
        "ha_role_override": "master",
        "ha_notify_failover": "1",
    }

    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        config_path.write_text(json.dumps(file_values))
        module.CONFIG_FILE = str(config_path)
        loaded = module.load_config()

    assert loaded["identity_email_enabled"] is True
    assert loaded["email_reminder_scan"] == 5
    assert loaded["email_reminder_service"] == 10
    assert loaded["email_reminder_identity"] == 15
    assert loaded["email_reminder_new_device"] == 30
    assert loaded["visibility_prime_interval"] == 60
    assert loaded["ha_carp_enabled"] is False
    assert loaded["ha_role_override"] == "master"
    assert loaded["ha_notify_failover"] is True

    print("INTEGRATION_DEFAULTS_COMBINED=PASS")


def test_carp_gate_combines_fail_open_and_override():
    module = load_module()

    denied = module.service_observation_allowed(
        networks_fixture(),
        IFCONFIG_BACKUP,
        config={"ha_carp_enabled": "1", "ha_role_override": "auto"},
    )
    assert denied == (False, "BACKUP", "CARP backup node"), denied

    overridden = module.service_observation_allowed(
        networks_fixture(),
        IFCONFIG_BACKUP,
        config={"ha_carp_enabled": "1", "ha_role_override": "master"},
    )
    assert overridden == (True, "MASTER", ""), overridden

    disabled = module.service_observation_allowed(
        networks_fixture(),
        IFCONFIG_BACKUP,
        config={"ha_carp_enabled": "0", "ha_role_override": "auto"},
    )
    assert disabled == (True, "BACKUP", ""), disabled

    print("INTEGRATION_CARP_FAIL_OPEN_AND_OVERRIDE=PASS")


def test_standby_hygiene_still_ages_without_observation():
    module = load_module()
    now = datetime(2026, 11, 5, 12, 0, 0)

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute(
                "INSERT INTO devices (mac, ip, last_seen) VALUES (?, ?, ?)",
                ("aa:bb:cc:dd:ee:90", "198.51.100.90",
                 (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.execute(
                """
                INSERT INTO device_services (
                    mac, ip, interface, service_type, port, protocol, status,
                    detection_method, confidence, first_detected, last_verified,
                    last_checked, miss_count
                ) VALUES (?, ?, 'LAN', 'SSH', 22, 'tcp', 'unavailable',
                          'ssh_banner', 'verified', ?, ?, ?, 2)
                """,
                ("aa:bb:cc:dd:ee:90", "198.51.100.90",
                 (now - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S"),
                 (now - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S"),
                 (now - timedelta(days=8)).strftime("%Y-%m-%d %H:%M:%S")),
            )
            conn.commit()

        assert module.age_stale_service_state(now=now) == (1, 0)

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            status = conn.execute(
                "SELECT status FROM device_services WHERE ip = '198.51.100.90'"
            ).fetchone()[0]
        assert status == "unknown", status

    print("INTEGRATION_STANDBY_AGEING=PASS")


def test_scan_state_change_and_reminder_refactor():
    module = load_module()
    mac = "aa:bb:cc:dd:ee:91"
    device = {"mac": mac, "ip": "198.51.100.91"}
    services = [{
        "port": 22,
        "protocol": "tcp",
        "service": "ssh",
        "product": "OpenSSH",
        "service_version": "9.9",
        "extra_info": "",
    }]

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        assert module.scan_state_changed(device, services, device["ip"]) is True
        assert module.scan_email_reminder_due(device, 0) is False

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            cursor = conn.execute(
                """
                INSERT INTO nmap_scan_history (
                    mac, ip, scan_type, started_at, finished_at, success,
                    email_sent
                ) VALUES (?, ?, 'automatic', ?, ?, 1, 1)
                """,
                (mac, device["ip"], "2026-11-05 10:00:00", "2026-11-05 10:01:00"),
            )
            history_id = cursor.lastrowid
            conn.execute(
                """
                INSERT INTO nmap_scan_ports (
                    scan_history_id, port, protocol, state, service, product,
                    version, extra_info
                ) VALUES (?, 22, 'tcp', 'open', 'ssh', 'OpenSSH', '9.9', '')
                """,
                (history_id,),
            )
            conn.commit()

        assert module.scan_state_changed(device, services, device["ip"]) is False
        changed = [dict(services[0], port=443, service="https")]
        assert module.scan_state_changed(device, changed, device["ip"]) is True
        assert module.scan_email_reminder_due(device, 1) is True

    print("INTEGRATION_STATE_CHANGE_AND_REMINDER=PASS")


def test_identity_email_and_webhook_legs_remain_independent():
    module = load_module()
    events = [{"event_type": "IP_IDENTITY_CHANGED"}]
    both = {
        "enabled": True,
        "email_enabled": True,
        "email_to": "operator@example.invalid",
        "identity_email_enabled": True,
        "webhook_enabled": True,
        "webhook_url": "https://example.invalid/hook",
        "identity_webhook_enabled": True,
    }

    assert module.should_send_identity_mail(both, events) is True
    assert module.should_send_identity_email(both, events) is True
    assert module.should_send_identity_mail(dict(both, identity_email_enabled=False), events) is False
    assert module.should_send_identity_email(dict(both, identity_webhook_enabled=False), events) is False

    print("INTEGRATION_IDENTITY_LEGS_INDEPENDENT=PASS")


def test_ui_controller_and_candidate_manifest_are_combined():
    controller = (
        ROOT
        / "src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/ConfigController.php"
    ).read_text()
    settings = (
        ROOT
        / "src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt"
    ).read_text()
    workflow = (ROOT / ".github/workflows/ci.yml").read_text()

    for token in (
        "identity_email_enabled",
        "email_reminder_identity",
        "ha_carp_enabled",
        "ha_role_override",
        "ha_notify_failover",
    ):
        assert token in controller, token
        assert token in settings, token

    assert "python3 tests/test_non_ha_operation.py" in workflow
    assert "python3 tests/test_service_ageing.py" in workflow
    assert "python3 tests/test_probe_resilience.py" in workflow

    manifest = MANIFEST.read_text().splitlines()
    rows = {parts[2]: parts for parts in (line.split() for line in manifest)}
    assert rows["src/opnsense/scripts/OPNsense/DeviceMonitor/notify_failover.php"][1] == "755"
    assert rows["src/opnsense/scripts/OPNsense/DeviceMonitor/notify_identity_mail.php"][1] == "644"
    assert len(rows) == 42, len(rows)

    print("INTEGRATION_UI_CONTROLLER_MANIFEST=PASS")


CASES = [
    test_combined_defaults_and_config_loading,
    test_carp_gate_combines_fail_open_and_override,
    test_standby_hygiene_still_ages_without_observation,
    test_scan_state_change_and_reminder_refactor,
    test_identity_email_and_webhook_legs_remain_independent,
    test_ui_controller_and_candidate_manifest_are_combined,
]


def main():
    for case in CASES:
        case()
        print("  %-52s PASS" % case.__name__)
    print("INTEGRATION_RECONCILIATION=PASS cases=%d" % len(CASES))


if __name__ == "__main__":
    main()
