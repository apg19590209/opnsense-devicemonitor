"""A single (non-HA) firewall must behave exactly as it did before the CARP gate.

v2.12 gates service observation, service alerts, new-device alerts, identity
alerts and the targeted-scan drain on the CARP role, so an HA standby stays
quiet. That gate is only safe if it is fail-open: a node with no CARP at all, an
unreadable `ifconfig`, a `carp: INIT` state (a standby that has not settled yet)
or CARP on an interface that is not monitored must all keep scanning and
alerting.

`tests/test_carp_role_gate.py` proves the BACKUP/MASTER decision. This file
proves the other direction, and it does so through `full_scan()` itself rather
than through the decision function alone: the same synthetic device is fed to a
CARP-less node (alerts must arrive) and, as a negative control, to a BACKUP node
(alerts must not arrive). The control matters — without it a harness that
silently skipped every dispatch would still "pass" the non-HA case.

`ifconfig_text` is injected at the gate, so no CARP pair, no second node and no
real `ifconfig` output is needed.
"""
import builtins
import importlib.util
import ipaddress
import os
import sqlite3
import tempfile
from datetime import datetime
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

# A plain single-node firewall: two physical NICs, loopback, no CARP anywhere.
IFCONFIG_SINGLE_NODE = """vtnet0: flags=1008843<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST> metric 0 mtu 1500
\tether 00:11:22:33:44:55
\tinet 192.168.20.1 netmask 0xffffff00 broadcast 192.168.20.255
vtnet1: flags=1008843<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST> metric 0 mtu 1500
\tether 00:11:22:33:44:56
\tinet 203.0.113.10 netmask 0xffffff00 broadcast 203.0.113.255
lo0: flags=1008049<UP,LOOPBACK,RUNNING,MULTICAST> metric 0 mtu 16384
\tinet 127.0.0.1 netmask 0xff000000
pflog0: flags=100<UP> metric 0 mtu 33160
"""

# CARP configured but not settled: neither MASTER nor BACKUP, so it carries no
# ownership information.
IFCONFIG_CARP_INIT = """re0: flags=1008843<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST> metric 0 mtu 1500
\tinet 192.168.20.24 netmask 0xffffff00 broadcast 192.168.20.255
\tcarp: INIT vhid 1 advbase 1 advskew 100
"""

# CARP on a segment this node does not monitor: still a single-node install as
# far as Device Monitor is concerned.
IFCONFIG_CARP_ELSEWHERE = """re0: flags=1008843<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST> metric 0 mtu 1500
\tinet 192.168.20.1 netmask 0xffffff00 broadcast 192.168.20.255
em9: flags=1008843<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST> metric 0 mtu 1500
\tinet 192.168.99.1 netmask 0xffffff00 broadcast 192.168.99.255
\tcarp: BACKUP vhid 7 advbase 1 advskew 100
"""

IFCONFIG_BACKUP = """re0: flags=1008843<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST,LOWER_UP> metric 0 mtu 1500
\tinet 192.168.20.24 netmask 0xffffff00 broadcast 192.168.20.255
\tcarp: BACKUP vhid 1 advbase 1 advskew 100
"""


def load_module():
    """Load scan_network.py with defaults.json redirected to the checkout."""
    original_open = builtins.open

    def test_open(path, *args, **kwargs):
        if str(path).endswith('/models/OPNsense/DeviceMonitor/defaults.json'):
            path = DEFAULTS
        return original_open(path, *args, **kwargs)

    spec = importlib.util.spec_from_file_location(
        "devicemonitor_non_ha_test",
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


def networks_fixture(device="vtnet0"):
    return [{
        "name": "lan",
        "description": "LAN",
        "device": device,
        "ip": "192.168.20.1",
        "subnet": "24",
        "network": ipaddress.ip_network("192.168.20.0/24"),
    }]


def devices_fixture():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return [{
        "mac": "aa:bb:cc:dd:ee:01",
        "ip": "192.168.20.50",
        "hostname": "laptop",
        "hostname_source": "hostwatch",
        "vendor": "Test Vendor",
        "vlan": "lan",
        "first_seen": now,
        "last_seen": now,
    }]


def test_no_carp_allows_observation():
    module = load_module()

    allowed, role, reason = module.service_observation_allowed(
        networks_fixture(),
        IFCONFIG_SINGLE_NODE,
    )

    assert allowed is True, (allowed, role, reason)
    assert role is None, role
    assert reason == '', reason

    # INIT carries no ownership: treat it as a single-node install, not a standby.
    allowed, role, _ = module.service_observation_allowed(
        networks_fixture("re0"),
        IFCONFIG_CARP_INIT,
    )
    assert (allowed, role) == (True, None), (allowed, role)

    # CARP on an unmonitored interface must not silence a monitored segment.
    allowed, role, _ = module.service_observation_allowed(
        networks_fixture("re0"),
        IFCONFIG_CARP_ELSEWHERE,
    )
    assert (allowed, role) == (True, None), (allowed, role)

    print("NON_HA_NO_CARP_ALLOWS=PASS")


def test_unreadable_ifconfig_allows_observation():
    module = load_module()

    class _BrokenSubprocess:
        class TimeoutExpired(Exception):
            pass

        @staticmethod
        def run(*args, **kwargs):
            raise OSError("ifconfig: not found")

    class _HungSubprocess:
        class TimeoutExpired(Exception):
            pass

        @staticmethod
        def run(*args, **kwargs):
            raise _HungSubprocess.TimeoutExpired("ifconfig", 10)

    class _EmptySubprocess:
        class TimeoutExpired(Exception):
            pass

        class _Result:
            stdout = ''

        @staticmethod
        def run(*args, **kwargs):
            return _EmptySubprocess._Result()

    original = module.subprocess
    try:
        for shim, label in (
            (_BrokenSubprocess, 'missing'),
            (_HungSubprocess, 'timeout'),
            (_EmptySubprocess, 'empty'),
        ):
            module.subprocess = shim
            allowed, role, _ = module.service_observation_allowed(
                networks_fixture()
            )
            assert allowed is True, (label, allowed)
            assert role is None, (label, role)
    finally:
        module.subprocess = original

    print("NON_HA_UNREADABLE_IFCONFIG_ALLOWS=PASS")


def test_role_is_not_persisted_as_backup():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = os.path.join(tmp, "devices.db")
        module.init_db()

        # Nothing to announce: no transition from "no CARP" to "no CARP".
        assert module.record_carp_role(None) is False
        assert module.record_carp_role(None) is False

        with sqlite3.connect(module.DB_FILE) as conn:
            row = conn.execute(
                "SELECT carp_role FROM service_discovery_state WHERE id = 1"
            ).fetchone()

        assert row is not None, "service_discovery_state row missing"
        assert not row[0], row[0]

        # And the reverse, so the storage path is proven live: a BACKUP role is
        # stored and a repeated observation is not re-logged.
        assert module.record_carp_role("BACKUP") is True
        assert module.record_carp_role("BACKUP") is False

        with sqlite3.connect(module.DB_FILE) as conn:
            assert conn.execute(
                "SELECT carp_role FROM service_discovery_state WHERE id = 1"
            ).fetchone()[0] == "BACKUP"

    print("NON_HA_ROLE_NOT_BACKUP=PASS")


def run_full_scan(ifconfig_text, device="vtnet0"):
    """Drive full_scan() with a fixed CARP verdict and record every dispatch."""
    module = load_module()
    calls = {
        "gate": [],
        "prime": [],
        "discovery": [],
        "service_alerts": [],
        "email": [],
        "webhook": [],
        "identity_mail": [],
        "external": [],
    }
    messages = []

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = os.path.join(tmp, "devices.db")
        module.log = messages.append

        config = dict(module.load_config())
        config.update({
            "enabled": True,
            "monitored_interfaces": "lan",
            "email_enabled": True,
            "email_to": "netops@example.net",
            "identity_email_enabled": True,
            "identity_webhook_enabled": False,
            "service_email_enabled": False,
            "webhook_enabled": False,
            "targeted_nmap_enabled": False,
            "email_vlans": "",
            "webhook_vlans": "",
            "email_reminder_new_device": 0,
            "email_reminder_identity": 0,
            "email_reminder_scan": 0,
            "email_reminder_service": 0,
        })

        real_gate = module.service_observation_allowed

        def gate(networks, network_text=None, config=None):
            # full_scan() calls the gate without ifconfig text; the synthetic
            # output is injected here so the real decision logic still runs.
            verdict = real_gate(
                networks,
                ifconfig_text,
                config=config,
            )
            calls["gate"].append(verdict)
            return verdict

        module.service_observation_allowed = gate
        module.load_config = lambda: config
        module.resolve_monitored_networks = (
            lambda cfg: (networks_fixture(device), None)
        )
        module.detect_source_capabilities = lambda: {
            "hostwatch": {"readable": True},
            "kea": {
                "active": False,
                "queryable": False,
                "lease4_get_all": False,
                "enabled": False,
            },
            "isc": {"enabled": False},
            "dnsmasq": {"configured": False},
        }
        # The real priming function is left in place: its first act is the CARP
        # gate, which is exactly what this harness must exercise. Only the ICMP
        # probe boundary is stubbed, so a non-HA sweep records probes and a
        # BACKUP node records none.
        real_subprocess = module.subprocess

        class _ProbeShim:
            DEVNULL = real_subprocess.DEVNULL
            PIPE = real_subprocess.PIPE
            TimeoutExpired = real_subprocess.TimeoutExpired

            class _Done:
                def __init__(self, returncode):
                    self.returncode = returncode

            @staticmethod
            def run(args, *a, **k):
                command = args[0] if args else ''
                if command == '/sbin/ping':
                    calls["prime"].append(args[-1])
                    return _ProbeShim._Done(1)
                calls["external"].append(command)
                return _ProbeShim._Done(1)

        module.subprocess = _ProbeShim

        module.get_hostwatch_devices = lambda networks: devices_fixture()
        module.get_dhcp_descriptions = lambda: {}
        module.get_kea_ipv4_leases = lambda: []
        module.get_dnsmasq_descriptions = lambda: {}
        module.get_unbound_hostnames = lambda: {}
        module.get_adguard_rewrite_hostnames = lambda cfg: {}
        module.get_pihole_hostnames = lambda cfg: {}
        module.apply_hostname_provenance = lambda *args, **kwargs: None
        module.is_device_active = lambda *args, **kwargs: True
        module.detect_recent_hostwatch_identity_events = (
            lambda *args, **kwargs: 0
        )
        module.detect_recent_hostwatch_ipv6_identity_events = (
            lambda *args, **kwargs: 0
        )
        module.get_new_high_identity_events = lambda conn, start: []
        module.get_pending_high_identity_reminders = lambda conn, cfg: []
        module.should_send_identity_mail = lambda cfg, events: True
        module.should_send_identity_email = lambda cfg, events: False
        module.send_identity_mail = (
            lambda events: calls["identity_mail"].append(events) is None
        )
        module.send_identity_email = lambda events: False
        module.run_scheduled_service_discovery = (
            lambda *args, **kwargs: calls["discovery"].append(args) or []
        )
        module.process_service_alerts = (
            lambda cfg, networks: calls["service_alerts"].append(networks)
        )
        module.send_email_via_php_api = (
            lambda devices, in_scope: calls["email"].append(list(devices))
            or True
        )
        module.send_webhook_via_php_api = (
            lambda devices, in_scope: calls["webhook"].append(list(devices))
            or True
        )

        rc = module.full_scan()

        with sqlite3.connect(module.DB_FILE) as conn:
            role = conn.execute(
                "SELECT carp_role FROM service_discovery_state WHERE id = 1"
            ).fetchone()[0]

    return rc, calls, role, "\n".join(messages)


def test_single_node_full_scan_still_alerts():
    rc, calls, role, log_text = run_full_scan(IFCONFIG_SINGLE_NODE)

    assert rc == 0, rc
    assert calls["gate"], "full_scan never consulted the CARP gate"

    allowed, carp_role, reason = calls["gate"][0]
    assert allowed is True, (allowed, carp_role, reason)
    assert carp_role is None, carp_role
    assert not role, role

    # Nothing may be skipped on a node without CARP.
    assert calls["prime"], "visibility priming skipped without CARP"
    assert calls["discovery"], "service discovery skipped without CARP"
    assert calls["service_alerts"], "service alerts skipped without CARP"
    assert calls["identity_mail"], "identity mail skipped without CARP"
    assert len(calls["email"]) == 1, calls["email"]
    assert calls["email"][0][0]["mac"] == "aa:bb:cc:dd:ee:01", calls["email"]
    assert not calls["external"], calls["external"]

    for suppressed in (
        "not announced",
        "skipping service discovery",
        "not alerted",
    ):
        assert suppressed not in log_text, log_text

    print("NON_HA_FULL_SCAN_ALERTS=PASS")


def test_backup_control_suppresses_the_same_scan():
    """Negative control: the harness must notice a BACKUP node going silent."""
    rc, calls, role, log_text = run_full_scan(IFCONFIG_BACKUP, device="re0")

    assert rc == 0, rc
    allowed, carp_role, _ = calls["gate"][0]
    assert allowed is False, (allowed, carp_role)
    assert carp_role == "BACKUP", carp_role
    assert role == "BACKUP", role

    assert not calls["prime"], "priming ran on a CARP backup node"
    assert not calls["discovery"], "discovery ran on a CARP backup node"
    assert not calls["service_alerts"], "service alerts ran on a CARP backup"
    assert not calls["identity_mail"], "identity mail sent from a CARP backup"
    assert not calls["email"], f"new-device email sent from a backup: {calls}"
    assert "not announced" in log_text, log_text

    print("NON_HA_CONTROL_BACKUP_SILENT=PASS")


def main():
    test_no_carp_allows_observation()
    test_unreadable_ifconfig_allows_observation()
    test_role_is_not_persisted_as_backup()
    test_single_node_full_scan_still_alerts()
    test_backup_control_suppresses_the_same_scan()

    print("NON_HA_OPERATION=PASS")


if __name__ == "__main__":
    main()


