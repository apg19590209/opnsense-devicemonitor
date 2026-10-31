"""A CARP backup node must not report service outages it cannot observe.

v2.11 HA safety (Decision 50). `is_active` is derived from hostwatch plus a ping
fallback (`is_device_active()`), so on a CARP BACKUP node — which does not carry
the traffic — most devices read inactive. With the O3a host-active gate that
makes the standby silent, which is the *correct* answer, but nothing said so and
nothing stopped the standby from probing, flipping rows or mailing alerts while
its visibility is degraded.

`service_observation_allowed()` reads the CARP role of the monitored devices and
refuses service discovery and service alerts on a BACKUP node. A node with no
CARP at all behaves exactly as before, so a non-HA install is unaffected.

`service_visibility_summary()` covers the adjacent failure: if the gate has
nothing to observe, say so instead of silently suppressing outage verdicts.

These checks use synthetic `ifconfig` output, so no CARP configuration or second
node is required.
"""
import builtins
import importlib.util
import ipaddress
import os
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

IFCONFIG_BACKUP = """re0: flags=1008843<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST,LOWER_UP> metric 0 mtu 1500
\tinet 192.168.20.24 netmask 0xffffff00 broadcast 192.168.20.255
\tcarp: BACKUP vhid 1 advbase 1 advskew 100
lo0: flags=1008049<UP,LOOPBACK,RUNNING,MULTICAST,LOWER_UP> metric 0 mtu 16384
\tinet 127.0.0.1 netmask 0xff000000
"""

IFCONFIG_MASTER = """re0: flags=1008843<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST,LOWER_UP> metric 0 mtu 1500
\tinet 192.168.20.23 netmask 0xffffff00 broadcast 192.168.20.255
\tcarp: MASTER vhid 1 advbase 1 advskew 0
"""

IFCONFIG_NO_CARP = """re0: flags=1008843<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST,LOWER_UP> metric 0 mtu 1500
\tinet 192.168.20.23 netmask 0xffffff00 broadcast 192.168.20.255
"""

IFCONFIG_MIXED = """re0: flags=1008843<UP,BROADCAST,RUNNING> metric 0 mtu 1500
\tinet 192.168.20.23 netmask 0xffffff00 broadcast 192.168.20.255
\tcarp: MASTER vhid 1 advbase 1 advskew 0
vlan0.50: flags=1008843<UP,BROADCAST,RUNNING> metric 0 mtu 1500
\tinet 192.168.50.1 netmask 0xffffff00 broadcast 192.168.50.255
\tcarp: BACKUP vhid 3 advbase 1 advskew 100
"""


def load_module():
    """Load scan_network.py with defaults.json redirected to the checkout."""
    original_open = builtins.open

    def test_open(path, *args, **kwargs):
        if str(path).endswith('/models/OPNsense/DeviceMonitor/defaults.json'):
            path = DEFAULTS
        return original_open(path, *args, **kwargs)

    spec = importlib.util.spec_from_file_location(
        "devicemonitor_carp_role_test",
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


def networks_fixture(device="re0"):
    return [{
        "name": "lan",
        "description": "LAN",
        "device": device,
        "ip": "192.168.20.23",
        "subnet": "24",
        "network": ipaddress.ip_network("192.168.20.0/24"),
    }]



def test_carp_role_parsing():
    module = load_module()

    assert module.parse_carp_roles(IFCONFIG_BACKUP) == {"re0": "BACKUP"}
    assert module.parse_carp_roles(IFCONFIG_MASTER) == {"re0": "MASTER"}
    assert module.parse_carp_roles(IFCONFIG_NO_CARP) == {}

    mixed = module.parse_carp_roles(IFCONFIG_MIXED)
    assert mixed == {"re0": "MASTER", "vlan0.50": "BACKUP"}, mixed

    print("CARP_ROLE_PARSE_PASS")


def test_role_decision():
    module = load_module()

    assert module.detect_carp_role(["re0"], IFCONFIG_BACKUP) == "BACKUP"
    assert module.detect_carp_role(["re0"], IFCONFIG_MASTER) == "MASTER"
    assert module.detect_carp_role(["re0"], IFCONFIG_NO_CARP) is None

    # A node that is master on any monitored segment observes for all of them.
    mixed = module.detect_carp_role(["re0", "vlan0.50"], IFCONFIG_MIXED)
    assert mixed == "MASTER", mixed

    # Only monitored devices count.
    assert module.detect_carp_role(["em9"], IFCONFIG_BACKUP) is None

    print("CARP_ROLE_DECISION_PASS")


def test_backup_node_denies_observation():
    module = load_module()

    denied = module.service_observation_allowed(
        networks_fixture(),
        IFCONFIG_BACKUP,
    )
    assert denied[0] is False, denied
    assert denied[1] == "BACKUP", denied

    allowed = module.service_observation_allowed(
        networks_fixture(),
        IFCONFIG_MASTER,
    )
    assert allowed[0] is True, allowed
    assert allowed[1] == "MASTER", allowed

    print("CARP_BACKUP_DENIES=PASS")
    print("CARP_MASTER_ALLOWS=PASS")


def test_absent_carp_allows():
    module = load_module()

    allowed = module.service_observation_allowed(
        networks_fixture(),
        IFCONFIG_NO_CARP,
    )

    assert allowed[0] is True, allowed
    assert allowed[1] is None, allowed

    print("CARP_ABSENT_ALLOWS=PASS")


def test_backup_skips_discovery():
    module = load_module()

    def forbidden(networks):
        raise AssertionError(
            "service discovery ran on a CARP backup node"
        )

    module.service_observation_allowed = lambda networks, text=None: (
        False,
        "BACKUP",
        "CARP backup node",
    )
    module.discover_dhcp_servers = forbidden
    module.discover_dns_servers = forbidden
    module.discover_ntp_servers = forbidden
    module.discover_ssh_servers = forbidden
    module.discover_web_admin_services = forbidden
    module.discover_phase3_services = forbidden

    assert module.discover_infrastructure_services(
        networks_fixture()
    ) == []

    print("CARP_BACKUP_SKIPS_DISCOVERY=PASS")


def test_full_scan_consults_the_role():
    source = SOURCE.read_text()

    start = source.index("def full_scan():")
    end = source.index("\ndef ", start + 10)
    body = source[start:end]

    assert "service_observation_allowed(" in body, "full_scan ignores CARP role"

    gate = body.index("service_observation_allowed(")
    discovery = body.index("run_scheduled_service_discovery(")
    alerts = body.index("process_service_alerts(")

    assert gate < discovery, "gate must precede discovery"
    assert gate < alerts, "gate must precede alert processing"

    print("CARP_GATE_WIRED_IN_FULL_SCAN=PASS")


def test_visibility_summary():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute(
                """
                INSERT INTO devices (mac, ip, vlan, is_active, last_seen)
                VALUES ('aa:bb:cc:dd:ee:01', '192.168.20.50', 'LAN', 0,
                        '2026-09-21 13:45:11')
                """
            )
            conn.commit()

            warning = module.service_visibility_summary(
                conn,
                networks_fixture(),
            )

            assert warning is not None, "no warning with zero active devices"
            assert "0 active devices" in warning, warning

            conn.execute("UPDATE devices SET is_active = 1")
            conn.commit()

            assert module.service_visibility_summary(
                conn,
                networks_fixture(),
            ) is None

            # Out-of-scope activity must not clear the warning.
            conn.execute(
                "UPDATE devices SET is_active = 0, ip = '10.9.9.9'"
            )
            conn.commit()

            assert module.service_visibility_summary(
                conn,
                networks_fixture(),
            ) is not None

    print("CARP_VISIBILITY_WARNING=PASS")


def main():
    test_carp_role_parsing()
    test_role_decision()
    test_backup_node_denies_observation()
    test_absent_carp_allows()
    test_backup_skips_discovery()
    test_full_scan_consults_the_role()
    test_visibility_summary()

    print("CARP_ROLE_GATE=PASS")


if __name__ == "__main__":
    main()
