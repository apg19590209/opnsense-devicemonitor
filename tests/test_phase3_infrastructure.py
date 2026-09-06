import importlib.util
import ipaddress
import sqlite3
import tempfile
import threading
import time
from pathlib import Path
from types import SimpleNamespace


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
    spec = importlib.util.spec_from_file_location(
        "devicemonitor_phase3_test",
        SOURCE,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.log = lambda message: None
    return module


def forbidden_auto_nmap(candidates):
    raise AssertionError(
        "Automatic Phase 3 discovery invoked fresh Nmap identification"
    )


def test_no_automatic_nmap():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        module.DB_FILE = str(tmp_path / "devices.db")
        module.LOG_FILE = str(tmp_path / "devicemonitor.log")

        module._service_probe_candidates = (
            lambda conn, *args, **kwargs: {}
        )
        module._phase3_nmap_rows = lambda conn: []
        module._discover_local_wireguard = (
            lambda conn, candidates: []
        )
        module._probe_phase3_nmap_identification = (
            forbidden_auto_nmap
        )

        result = module.discover_phase3_services()

        assert result == [], result

    print("PHASE3_NO_AUTOMATIC_NMAP=PASS")


def test_nmap_single_host_and_strong_evidence():
    module = load_module()

    candidates = {
        "192.0.2.10": {},
        "192.0.2.11": {},
        "192.0.2.12": {},
    }

    calls = []
    state = {
        "active": 0,
        "max_active": 0,
    }
    lock = threading.Lock()

    def fake_run(command, **kwargs):
        with lock:
            state["active"] += 1
            state["max_active"] = max(
                state["max_active"],
                state["active"],
            )

        try:
            time.sleep(0.01)

            command = list(command)
            calls.append((command, kwargs))

            target = command[-1]
            protocol = "udp" if "-sU" in command else "tcp"

            if protocol == "tcp":
                ports = ""
            elif target == "192.0.2.10":
                ports = """
                    <port protocol="udp" portid="161">
                      <state state="open"/>
                      <service name="snmp"/>
                    </port>
                """
            elif target == "192.0.2.11":
                ports = """
                    <port protocol="udp" portid="161">
                      <state state="open|filtered"/>
                      <service name="snmp"/>
                    </port>
                """
            else:
                ports = """
                    <port protocol="udp" portid="9999">
                      <state state="open"/>
                      <service name="unknown"/>
                    </port>
                """

            xml = f"""
                <nmaprun>
                  <host>
                    <address
                      addr="{target}"
                      addrtype="ipv4"
                    />
                    <ports>
                      {ports}
                    </ports>
                  </host>
                </nmaprun>
            """

            return SimpleNamespace(
                returncode=0,
                stdout=xml,
                stderr="",
            )

        finally:
            with lock:
                state["active"] -= 1

    module.subprocess.run = fake_run

    identified = module._probe_phase3_nmap_identification(
        candidates
    )

    # Three hosts x TCP/UDP = six serial Nmap invocations.
    assert len(calls) == 6, len(calls)
    assert state["max_active"] == 1, state

    for command, kwargs in calls:
        target = command[-1]

        parsed = ipaddress.ip_address(target)
        assert parsed.version == 4
        assert str(parsed) == target

        candidate_args = [
            value
            for value in command
            if value in candidates
        ]

        assert candidate_args == [target], command
        assert kwargs["timeout"] == 12, kwargs

    # Only the genuinely open and identified SNMP result is accepted.
    assert len(identified) == 1, identified

    row = identified[0]

    assert row[0] == "192.0.2.10", row
    assert row[2] == 161, row
    assert row[3] == "udp", row
    assert row[4] == "snmp", row

    print("PHASE3_SINGLE_HOST_NMAP=PASS")
    print("PHASE3_NMAP_SERIAL=PASS")
    print("PHASE3_STRONG_NMAP_EVIDENCE=PASS")


def test_smb_single_host_nmap():
    module = load_module()

    target_ip = "192.0.2.50"
    calls = []

    class FakeSocket:
        def close(self):
            return None

    module.socket.create_connection = (
        lambda target, timeout=None: FakeSocket()
    )

    def fake_run(command, **kwargs):
        calls.append((list(command), kwargs))

        return SimpleNamespace(
            returncode=0,
            stdout=(
                "| smb-protocols:\n"
                "|   2.02\n"
                "|   3.0\n"
                "|   3.1.1\n"
            ),
            stderr="",
        )

    module.subprocess.run = fake_run

    result = module._probe_smb_service(
        (target_ip, 445)
    )

    assert result is not None
    assert len(calls) == 1

    command, kwargs = calls[0]

    assert command[-1] == target_ip, command
    assert command.count(target_ip) == 1, command
    assert "-p" in command
    assert "445" in command
    assert "--script" in command
    assert "smb-protocols" in command
    assert kwargs["timeout"] == 5

    parsed = ipaddress.ip_address(command[-1])
    assert parsed.version == 4

    print("PHASE3_SMB_SINGLE_HOST_NMAP=PASS")


def test_probe_pool_bounds_and_smb_serialization():
    module = load_module()

    executor_workers = []
    pool_targets = []
    probe_calls = []

    state = {
        "in_pool": False,
    }

    class FakeExecutor:
        def __init__(self, max_workers):
            executor_workers.append(max_workers)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def map(self, function, items):
            items = list(items)
            pool_targets.extend(items)

            state["in_pool"] = True
            try:
                return [
                    function(item)
                    for item in items
                ]
            finally:
                state["in_pool"] = False

    def fake_probe(target):
        probe_calls.append(
            (target, state["in_pool"])
        )

        return {
            "product": "Regression Test",
            "version": target[3],
        }

    module.ThreadPoolExecutor = FakeExecutor
    module._probe_phase3_target = fake_probe

    lightweight = [
        (
            "RDP",
            f"192.0.2.{index + 1}",
            4000 + index,
            "rdp_negotiation",
        )
        for index in range(14)
    ]

    smb = [
        (
            "SMB",
            "192.0.2.100",
            445,
            "smb_protocols",
        ),
        (
            "SMB",
            "192.0.2.101",
            445,
            "smb_protocols",
        ),
    ]

    targets = lightweight + smb

    results = module._run_phase3_protocol_probes(
        targets
    )

    assert len(results) == len(targets)

    # Lightweight concurrency must never exceed 12.
    assert executor_workers == [12], executor_workers

    # SMB must never enter the concurrent worker pool.
    assert pool_targets == lightweight, pool_targets

    lightweight_calls = [
        (target, in_pool)
        for target, in_pool in probe_calls
        if target[0] != "SMB"
    ]

    smb_calls = [
        (target, in_pool)
        for target, in_pool in probe_calls
        if target[0] == "SMB"
    ]

    assert len(lightweight_calls) == 14
    assert all(in_pool for _, in_pool in lightweight_calls)

    assert len(smb_calls) == 2
    assert all(
        not in_pool
        for _, in_pool in smb_calls
    )

    print(
        "PHASE3_LIGHTWEIGHT_POOL_BOUND=PASS "
        "max_workers=12"
    )
    print("PHASE3_SMB_SERIAL=PASS")


def test_active_service_lifecycle():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        module.DB_FILE = str(tmp_path / "devices.db")
        module.LOG_FILE = str(tmp_path / "devicemonitor.log")

        test_ip = "192.168.254.250"

        module._service_probe_candidates = (
            lambda conn, *args, **kwargs: {
                test_ip: {
                    "mac": "02:00:00:00:00:10",
                    "interface": "TEST",
                }
            }
        )

        module._phase3_nmap_rows = lambda conn: []
        module._discover_local_wireguard = (
            lambda conn, candidates: []
        )
        module._probe_phase3_nmap_identification = (
            forbidden_auto_nmap
        )

        module.init_db()

        expected = {
            ("SMB", 445, "smb_protocols"),
            ("NFS", 2049, "nfs_rpc"),
            ("RDP", 3389, "rdp_negotiation"),
            ("VNC", 5900, "vnc_banner"),
            ("WINRM", 5985, "winrm_http"),
            ("WINRM", 5986, "winrm_https"),
            ("LDAP", 389, "ldap_bind"),
            ("LDAPS", 636, "ldaps_bind"),
        }

        def success_runner(targets):
            return [
                {
                    "product": "Lifecycle Test",
                    "version": target[3],
                }
                for target in targets
            ]

        # Cycle 1: verification succeeds.
        module._run_phase3_protocol_probes = (
            success_runner
        )

        module.discover_phase3_services()

        with sqlite3.connect(module.DB_FILE) as conn:
            rows = conn.execute(
                """
                SELECT
                    service_type,
                    port,
                    detection_method,
                    status,
                    last_verified
                FROM device_services
                WHERE ip = ?
                  AND detection_method IN (
                    'smb_protocols',
                    'nfs_rpc',
                    'rdp_negotiation',
                    'vnc_banner',
                    'winrm_http',
                    'winrm_https',
                    'ldap_bind',
                    'ldaps_bind'
                  )
                ORDER BY service_type, port
                """,
                (test_ip,),
            ).fetchall()

        actual = {
            (row[0], int(row[1]), row[2])
            for row in rows
        }

        assert actual == expected, actual
        assert all(
            row[3] == "available"
            for row in rows
        )

        first_verified = {
            (row[0], int(row[1]), row[2]): row[4]
            for row in rows
        }

        print(
            "PHASE3_AVAILABLE=PASS "
            f"services={len(rows)}"
        )

        # Cycle 2: verification fails.
        module._run_phase3_protocol_probes = (
            lambda targets: [
                None
                for _ in targets
            ]
        )

        module.discover_phase3_services()

        with sqlite3.connect(module.DB_FILE) as conn:
            rows = conn.execute(
                """
                SELECT
                    service_type,
                    port,
                    detection_method,
                    status,
                    last_verified
                FROM device_services
                WHERE ip = ?
                  AND detection_method IN (
                    'smb_protocols',
                    'nfs_rpc',
                    'rdp_negotiation',
                    'vnc_banner',
                    'winrm_http',
                    'winrm_https',
                    'ldap_bind',
                    'ldaps_bind'
                  )
                ORDER BY service_type, port
                """,
                (test_ip,),
            ).fetchall()

        assert len(rows) == len(expected)
        assert all(
            row[3] == "unavailable"
            for row in rows
        )

        for row in rows:
            key = (
                row[0],
                int(row[1]),
                row[2],
            )

            assert (
                row[4]
                == first_verified[key]
            ), (
                f"last_verified changed on failure "
                f"for {key}"
            )

        print(
            "PHASE3_UNAVAILABLE=PASS "
            "last_verified_preserved=YES"
        )

        # Cycle 3: service recovers.
        old_time = "2000-01-01 00:00:00"

        with sqlite3.connect(module.DB_FILE) as conn:
            conn.execute(
                """
                UPDATE device_services
                SET last_verified = ?
                WHERE ip = ?
                """,
                (old_time, test_ip),
            )
            conn.commit()

        module._run_phase3_protocol_probes = (
            success_runner
        )

        module.discover_phase3_services()

        with sqlite3.connect(module.DB_FILE) as conn:
            rows = conn.execute(
                """
                SELECT status, last_verified
                FROM device_services
                WHERE ip = ?
                  AND detection_method IN (
                    'smb_protocols',
                    'nfs_rpc',
                    'rdp_negotiation',
                    'vnc_banner',
                    'winrm_http',
                    'winrm_https',
                    'ldap_bind',
                    'ldaps_bind'
                  )
                """,
                (test_ip,),
            ).fetchall()

        assert len(rows) == len(expected)
        assert all(
            row[0] == "available"
            for row in rows
        )
        assert all(
            row[1] != old_time
            for row in rows
        )

        print(
            "PHASE3_RECOVERY=PASS "
            "last_verified_refreshed=YES"
        )


def main():
    test_no_automatic_nmap()
    test_nmap_single_host_and_strong_evidence()
    test_smb_single_host_nmap()
    test_probe_pool_bounds_and_smb_serialization()
    test_active_service_lifecycle()

    print("PHASE3_CI_REGRESSION=PASS")


if __name__ == "__main__":
    main()