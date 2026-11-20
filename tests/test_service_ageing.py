"""A stale `unavailable` verdict ages to `unknown`, and unseen hosts lose their rows.

v2.11 service-liveness fix (O4, DECISIONS.md 52). `record_service_miss()` flips a
row to `unavailable` on the second consecutive failed observation and nothing ever
moved it back, so an endpoint that was down once stayed down forever - including
24 rows whose hosts had not been seen since 2026-09-21. `unavailable` is a verdict
about one run, not a permanent fact, so two windows apply:

  * an `unavailable` row whose `last_verified` is older than
    `SERVICE_UNKNOWN_AFTER_DAYS` becomes `unknown`;
  * rows whose host address has not been seen in `devices.last_seen` for
    `SERVICE_RETIRE_AFTER_DAYS` are deleted, together with their held alert.

Retirement is refused when no device at all is fresh, which is what a stopped
hostwatch looks like, and rows whose address has no `devices` record (gateway,
firewall, untracked server) are never retired - missing inventory is not evidence
of absence.

Every check drives `age_stale_service_state()` against a temporary database built
by the real `init_db()`, so the trigger and schema are the production ones.
"""
import builtins
import contextlib
import importlib.util
import io
import json
import sqlite3
import tempfile
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


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

SYDNEY = ZoneInfo("Australia/Sydney")
NOW = datetime(2026, 10, 31, 12, 0, 0, tzinfo=UTC)
STAMP = "%Y-%m-%d %H:%M:%S"

STALE_MAC = "aa:bb:cc:dd:ee:20"
STALE_IP = "198.51.100.20"
FRESH_MAC = "aa:bb:cc:dd:ee:21"
FRESH_IP = "198.51.100.21"
ORPHAN_IP = "198.51.100.22"


def load_module():
    """Load scan_network.py with defaults.json redirected to the checkout."""
    original_open = builtins.open

    def test_open(path, *args, **kwargs):
        if str(path).endswith('/models/OPNsense/DeviceMonitor/defaults.json'):
            path = DEFAULTS
        return original_open(path, *args, **kwargs)

    spec = importlib.util.spec_from_file_location(
        "devicemonitor_service_ageing_test",
        SOURCE,
    )
    module = importlib.util.module_from_spec(spec)
    builtins.open = test_open
    try:
        spec.loader.exec_module(module)
    finally:
        builtins.open = original_open

    module.log = lambda message: None
    # These cases pin the policy, not whichever timezone happens to run CI.
    module._system_local_timezone = lambda: UTC
    return module


def stamp(delta):
    return (NOW + delta).astimezone(UTC).strftime(STAMP)


def add_device(conn, mac, ip, last_seen):
    conn.execute(
        """
        INSERT INTO devices (mac, ip, vlan, is_active, last_seen)
        VALUES (?, ?, 'VLAN60', 0, ?)
        """,
        (mac, ip, last_seen),
    )


def add_service(conn, mac, ip, status, last_verified, miss_count=0, port=22):
    conn.execute(
        """
        INSERT INTO device_services (
            mac, ip, interface, service_type, port, protocol,
            status, detection_method, confidence, product, version,
            first_detected, last_verified, miss_count
        )
        VALUES (?, ?, 'VLAN60', 'SSH', ?, 'tcp', ?, 'ssh_banner',
                'verified', 'OpenSSH', '9.9', ?, ?, ?)
        """,
        (mac, ip, port, status, last_verified, last_verified, miss_count),
    )


def read_row(module, ip, port=22):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        return conn.execute(
            "SELECT status, miss_count FROM device_services "
            "WHERE ip = ? AND port = ?",
            (ip, port),
        ).fetchone()


def read_status(module, ip, port=22):
    row = read_row(module, ip, port)
    return row[0] if row else None


def service_count(module):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        return conn.execute("SELECT COUNT(*) FROM device_services").fetchone()[0]


def event_count(module, event_type=None):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        if event_type is None:
            return conn.execute(
                "SELECT COUNT(*) FROM device_activity_events"
            ).fetchone()[0]
        return conn.execute(
            "SELECT COUNT(*) FROM device_activity_events WHERE event_type = ?",
            (event_type,),
        ).fetchone()[0]


def pending_keys(module):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        return {
            row[0]
            for row in conn.execute("SELECT service_key FROM service_alert_pending")
        }


def alert_key(module, mac, ip, port=22):
    return module.service_alert_key({
        "mac": mac,
        "service_type": "SSH",
        "ip": ip,
        "port": port,
        "protocol": "tcp",
        "interface": "VLAN60",
        "detection_method": "ssh_banner",
    })

def test_window_constants():
    module = load_module()

    assert module.SERVICE_UNKNOWN_AFTER_DAYS >= 1, module.SERVICE_UNKNOWN_AFTER_DAYS
    assert module.SERVICE_RETIRE_AFTER_DAYS > module.SERVICE_UNKNOWN_AFTER_DAYS

    print("AGE_WINDOW_CONSTANTS=PASS")


def test_ageing_boundary():
    module = load_module()
    unknown_after = timedelta(days=module.SERVICE_UNKNOWN_AFTER_DAYS)

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, FRESH_MAC, FRESH_IP, stamp(timedelta(hours=-1)))
            # Exactly on the window: still an `unavailable` verdict.
            add_service(conn, FRESH_MAC, FRESH_IP, "unavailable",
                        stamp(-unknown_after), port=22)
            # One second outside it: no longer evidence of an outage.
            add_service(conn, FRESH_MAC, FRESH_IP, "unavailable",
                        stamp(-unknown_after - timedelta(seconds=1)), port=23)
            # One second inside it: untouched.
            add_service(conn, FRESH_MAC, FRESH_IP, "unavailable",
                        stamp(-unknown_after + timedelta(seconds=1)), port=24)
            conn.commit()

        aged, retired = module.age_stale_service_state(now=NOW)

        assert aged == 1, aged
        assert retired == 0, retired
        assert read_row(module, FRESH_IP, 22)[0] == "unavailable"
        assert read_row(module, FRESH_IP, 23)[0] == "unknown"
        assert read_row(module, FRESH_IP, 24)[0] == "unavailable"

    print("AGE_AFTER_WINDOW_ONLY=PASS")


def test_available_and_unknown_untouched():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, FRESH_MAC, FRESH_IP, stamp(timedelta(hours=-1)))
            add_service(conn, FRESH_MAC, FRESH_IP, "available",
                        stamp(timedelta(days=-400)), port=22)
            add_service(conn, FRESH_MAC, FRESH_IP, "unknown",
                        stamp(timedelta(days=-400)), port=23)
            conn.commit()

        aged, retired = module.age_stale_service_state(now=NOW)

        assert (aged, retired) == (0, 0), (aged, retired)
        assert read_row(module, FRESH_IP, 22)[0] == "available"
        assert read_row(module, FRESH_IP, 23)[0] == "unknown"

    print("AGE_OTHER_STATUSES_UNTOUCHED=PASS")


def test_miss_count_reset():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, FRESH_MAC, FRESH_IP, stamp(timedelta(hours=-1)))
            add_service(
                conn, FRESH_MAC, FRESH_IP, "unavailable",
                stamp(-timedelta(days=module.SERVICE_UNKNOWN_AFTER_DAYS + 1)),
                miss_count=module.SERVICE_MISS_THRESHOLD,
            )
            conn.commit()

        module.age_stale_service_state(now=NOW)

        status, misses = read_row(module, FRESH_IP)
        assert status == "unknown", status
        # The old miss streak belongs to the period that was aged away: an
        # endpoint that is still down must earn the verdict again (O3b), so a
        # single fresh sample cannot re-flip it to `unavailable`.
        assert misses == 0, misses

    print("AGE_RESETS_MISS_COUNT=PASS")


def test_retirement_boundary():
    module = load_module()
    retire_after = timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS)
    old_ip = "198.51.100.23"
    boundary_ip = "198.51.100.24"

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, FRESH_MAC, FRESH_IP, stamp(timedelta(hours=-1)))
            # Exactly on the window: the host may still come back, keep the row.
            add_device(conn, "aa:bb:cc:dd:ee:23", boundary_ip, stamp(-retire_after))
            # One second past it: retired.
            add_device(conn, "aa:bb:cc:dd:ee:24", old_ip,
                       stamp(-retire_after - timedelta(seconds=1)))
            add_service(conn, FRESH_MAC, FRESH_IP, "available", stamp(timedelta(0)))
            add_service(conn, "aa:bb:cc:dd:ee:23", boundary_ip, "available",
                        stamp(-retire_after))
            add_service(conn, "aa:bb:cc:dd:ee:24", old_ip, "available",
                        stamp(-retire_after - timedelta(days=1)))
            conn.commit()

        aged, retired = module.age_stale_service_state(now=NOW)

        assert (aged, retired) == (0, 1), (aged, retired)
        assert service_count(module) == 2, service_count(module)
        assert read_row(module, old_ip) is None
        assert read_row(module, boundary_ip) is not None

    print("RETIRE_AFTER_WINDOW_ONLY=PASS")


def test_endpoint_without_device_record_kept():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, FRESH_MAC, FRESH_IP, stamp(timedelta(hours=-1)))
            # A gateway or untracked server: no `devices` row exists for it.
            add_service(conn, "", ORPHAN_IP, "available",
                        stamp(-timedelta(days=90)))
            conn.commit()

        aged, retired = module.age_stale_service_state(now=NOW)

        assert (aged, retired) == (0, 0), (aged, retired)
        assert read_row(module, ORPHAN_IP) is not None

    print("RETIRE_SKIPS_UNTRACKED_ENDPOINT=PASS")


def test_refuses_when_no_host_is_fresh():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            # Every host is stale: the signature of a stopped hostwatch.
            add_device(conn, STALE_MAC, STALE_IP,
                       stamp(-timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS + 5)))
            add_service(
                conn, STALE_MAC, STALE_IP, "unavailable",
                stamp(-timedelta(days=module.SERVICE_UNKNOWN_AFTER_DAYS + 5)),
            )
            conn.commit()

        aged, retired = module.age_stale_service_state(now=NOW)

        assert aged == 1, aged
        assert retired == 0, retired
        row = read_row(module, STALE_IP)
        assert row is not None and row[0] == "unknown", row

    print("RETIRE_REFUSED_WITHOUT_FRESH_HOST=PASS")


def test_dry_run_writes_nothing():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, FRESH_MAC, FRESH_IP, stamp(timedelta(hours=-1)))
            add_device(conn, STALE_MAC, STALE_IP,
                       stamp(-timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS + 1)))
            add_service(
                conn, FRESH_MAC, FRESH_IP, "unavailable",
                stamp(-timedelta(days=module.SERVICE_UNKNOWN_AFTER_DAYS + 1)),
            )
            add_service(conn, STALE_MAC, STALE_IP, "available",
                        stamp(-timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS + 2)))
            conn.commit()

        aged, retired = module.age_stale_service_state(now=NOW, dry_run=True)

        assert (aged, retired) == (1, 1), (aged, retired)
        assert service_count(module) == 2, service_count(module)
        assert read_row(module, FRESH_IP)[0] == "unavailable"
        assert read_row(module, STALE_IP) is not None

        # The same call without the flag performs what the dry run reported.
        assert module.age_stale_service_state(now=NOW) == (1, 1)
        assert service_count(module) == 1, service_count(module)
        assert read_row(module, FRESH_IP)[0] == "unknown"

    print("AGE_DRY_RUN_ROUND_TRIP=PASS")


def test_pending_alert_removed_with_retired_row():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        retired_key = alert_key(module, STALE_MAC, STALE_IP)
        kept_key = alert_key(module, FRESH_MAC, FRESH_IP)

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, FRESH_MAC, FRESH_IP, stamp(timedelta(hours=-1)))
            add_device(conn, STALE_MAC, STALE_IP,
                       stamp(-timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS + 1)))
            add_service(conn, FRESH_MAC, FRESH_IP, "available", stamp(timedelta(0)))
            add_service(conn, STALE_MAC, STALE_IP, "available",
                        stamp(-timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS + 2)))
            conn.execute(
                "INSERT INTO service_alert_pending "
                "(service_key, mac, event_json, held_at) VALUES (?, ?, '{}', ?)",
                (retired_key, STALE_MAC, stamp(-timedelta(hours=1))),
            )
            conn.execute(
                "INSERT INTO service_alert_pending "
                "(service_key, mac, event_json, held_at) VALUES (?, ?, '{}', ?)",
                (kept_key, FRESH_MAC, stamp(-timedelta(hours=1))),
            )
            conn.commit()

        aged, retired = module.age_stale_service_state(now=NOW)

        assert (aged, retired) == (0, 1), (aged, retired)
        assert pending_keys(module) == {kept_key}, pending_keys(module)

    print("AGE_DROPS_HELD_ALERT_WITH_ROW=PASS")


def test_retirement_writes_no_activity_event():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, FRESH_MAC, FRESH_IP, stamp(timedelta(hours=-1)))
            add_device(conn, STALE_MAC, STALE_IP,
                       stamp(-timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS + 1)))
            # Retired by DELETE: the status trigger is UPDATE-only, so no event.
            add_service(conn, STALE_MAC, STALE_IP, "available",
                        stamp(-timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS + 2)))
            # Aged by UPDATE: one history-only SERVICE_CHANGED, never emailed.
            add_service(
                conn, FRESH_MAC, FRESH_IP, "unavailable",
                stamp(-timedelta(days=module.SERVICE_UNKNOWN_AFTER_DAYS + 1)),
            )
            conn.commit()

        aged, retired = module.age_stale_service_state(now=NOW)

        assert (aged, retired) == (1, 1), (aged, retired)
        assert event_count(module) == 1, event_count(module)
        assert event_count(module, "SERVICE_CHANGED") == 1
        assert event_count(module, "SERVICE_UNAVAILABLE") == 0
        assert event_count(module, "SERVICE_AVAILABLE") == 0

    print("AGE_ACTIVITY_EVENTS=PASS")


def test_scheduler_runs_ageing():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        calls = []
        module.discover_infrastructure_services = lambda networks: []
        module.age_stale_service_state = (
            lambda *a, **k: calls.append((a, k)) or (0, 0)
        )

        ran = module.run_scheduled_service_discovery(
            interval_seconds=3600,
            networks=[],
        )

        assert ran is True, ran
        assert len(calls) == 1, calls

    print("AGE_SCHEDULED_WITH_DISCOVERY=PASS")


def test_cli_dry_run():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, FRESH_MAC, FRESH_IP, stamp(timedelta(hours=-1)))
            add_service(
                conn, FRESH_MAC, FRESH_IP, "unavailable",
                stamp(-timedelta(days=module.SERVICE_UNKNOWN_AFTER_DAYS + 1)),
            )
            conn.commit()

        original_argv = module.sys.argv
        module.sys.argv = ["scan_network.py", "--age-services", "--dry-run"]
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                code = module._main_dispatch()
        finally:
            module.sys.argv = original_argv

        payload = json.loads(output.getvalue())
        assert code == 0, code
        assert payload == {
            "result": "ok",
            "dry_run": True,
            "aged": 1,
            "retired": 0,
        }, payload
        assert read_row(module, FRESH_IP)[0] == "unavailable"

    print("AGE_CLI_DRY_RUN=PASS")


def device_last_seen(module, ip):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        row = conn.execute(
            "SELECT last_seen FROM devices WHERE ip = ?", (ip,)
        ).fetchone()
    return row[0] if row else None


def device_count(module):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        return conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0]


def test_verified_service_refreshes_device_last_seen():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, STALE_MAC, STALE_IP,
                       stamp(-timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS + 1)))
            add_service(conn, STALE_MAC, STALE_IP, "available", stamp(-timedelta(days=40)))
            conn.commit()

        stale_seen = device_last_seen(module, STALE_IP)

        # A service answer alone records endpoint presence, not device identity.
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            module.upsert_device_service(
                conn, STALE_MAC, STALE_IP, "VLAN60", "SSH", 22, "tcp",
                "ssh_banner", "verified", stamp(timedelta(0)),
            )
            conn.commit()

        assert device_last_seen(module, STALE_IP) == stale_seen, (
            "an unqualified service answer must not refresh device presence")
        assert read_checked(module, STALE_IP) == stamp(timedelta(0)), (
            "the service row still records endpoint presence")

        # A current, observed association for this MAC and IP is presence evidence.
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            module.upsert_device_service(
                conn, STALE_MAC, STALE_IP, "VLAN60", "SSH", 22, "tcp",
                "ssh_banner", "verified", stamp(timedelta(0)),
                presence_assoc=(STALE_MAC.upper(), STALE_IP),
            )
            conn.commit()

        assert device_last_seen(module, STALE_IP) == stamp(timedelta(0))

        aged, retired = module.age_stale_service_state(now=NOW)

        assert (aged, retired) == (0, 0), (aged, retired)
        assert read_row(module, STALE_IP) is not None

    print("AGE_PRESENCE_NEEDS_OBSERVED_ASSOCIATION=PASS")


def test_association_must_match_mac_and_ip():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        stale_seen = stamp(-timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS + 1))
        other_ip = "198.51.100.30"
        other_mac = "aa:bb:cc:dd:ee:30"

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, STALE_MAC, STALE_IP, stale_seen)
            add_device(conn, FRESH_MAC, STALE_IP, stamp(timedelta(hours=-1)))
            add_device(conn, other_mac, other_ip, stale_seen)
            conn.commit()

        cases = (
            # A different MAC sharing the IP: neither device moves.
            (other_mac, other_ip, (other_mac, STALE_IP)),
            # The same MAC at another IP: no device at STALE_IP moves.
            (STALE_MAC, STALE_IP, (other_mac, other_ip)),
            # MAC with no device row.
            (STALE_MAC, STALE_IP, ("aa:bb:cc:dd:ee:99", STALE_IP)),
            # Empty MAC, as an IP-only answer would supply.
            (STALE_MAC, STALE_IP, ("", STALE_IP)),
            # No association at all.
            (STALE_MAC, STALE_IP, None),
        )
        for _mac, _ip, assoc in cases:
            with closing(sqlite3.connect(module.DB_FILE)) as conn:
                module.upsert_device_service(
                    conn, STALE_MAC, STALE_IP, "VLAN60", "SSH", 22, "tcp",
                    "ssh_banner", "verified", stamp(timedelta(0)),
                    presence_assoc=assoc,
                )
                conn.commit()
            assert device_last_seen(module, STALE_IP) == stale_seen, assoc
            assert device_last_seen(module, other_ip) == stale_seen, assoc

    print("AGE_ASSOCIATION_MATCHES_MAC_AND_IP=PASS")


def test_dhcp_success_records_endpoint_but_not_device_presence():
    """Real DHCP discovery: the service row advances; no device timestamp moves."""
    module = load_module()
    import ipaddress

    class Result:
        def __init__(self, stdout=''):
            self.returncode, self.stdout, self.stderr = 0, stdout, ''

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ['/sbin/ifconfig', '-l']:
            return Result('em0\n')
        return Result('<script output="Server Identifier: %s"/>' % STALE_IP)

    original_run = module.subprocess.run
    module.subprocess.run = fake_run
    try:
        with tempfile.TemporaryDirectory() as tmp:
            module.DB_FILE = str(Path(tmp) / "devices.db")
            module.init_db()
            stale_seen = stamp(-timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS + 1))
            with closing(sqlite3.connect(module.DB_FILE)) as conn:
                add_device(conn, STALE_MAC, STALE_IP, stale_seen)
                conn.commit()
            networks = [{'device': 'em0', 'name': 'lan',
                         'network': ipaddress.ip_network('198.51.100.0/24')}]
            module.discover_dhcp_servers(networks)
            assert device_last_seen(module, STALE_IP) == stale_seen, (
                'DHCP newest-row ownership must not refresh device presence')
            assert read_checked(module, STALE_IP, port=67) is not None, (
                'endpoint presence is still recorded on the service row')
    finally:
        module.subprocess.run = original_run

    print("AGE_DHCP_DOES_NOT_REFRESH_DEVICE=PASS")


def test_responding_service_without_hostwatch_keeps_the_row():
    """Decision 53's protection without a device-identity claim (service-only presence)."""
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        stale_seen = stamp(-timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS + 5))
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, STALE_MAC, STALE_IP, stale_seen)
            add_device(conn, FRESH_MAC, FRESH_IP, stamp(timedelta(hours=-1)))
            add_service(conn, STALE_MAC, STALE_IP, "available", stamp(timedelta(hours=-1)))
            conn.commit()

        # Repeated successful service-only observations keep the row, and the
        # device timestamp is never claimed as fresh.
        for offset in (5, 10, 15):
            assert module.age_stale_service_state(
                now=NOW + timedelta(hours=offset)) == (0, 0)
            assert device_last_seen(module, STALE_IP) == stale_seen
            with closing(sqlite3.connect(module.DB_FILE)) as conn:
                module.upsert_device_service(
                    conn, STALE_MAC, STALE_IP, "VLAN60", "SSH", 22, "tcp",
                    "ssh_banner", "verified", stamp(timedelta(hours=offset)),
                )
                conn.commit()
            assert device_last_seen(module, STALE_IP) == stale_seen

    # The window is the configured retirement period from the last success, in its
    # own database per case. Timestamps have one-second resolution and the cutoff is
    # inclusive, like the device predicate: a success exactly at it is still fresh.
    # A service exactly at or inside the cutoff is retained. A service outside it is
    # retired when an unrelated fresh host exists; in-place deletion of the last row at
    # an address is covered by test_retirement_guard_boundary_is_inclusive_integrated().
    for seconds, expected in ((-3600, (0, 0)), (-1, (0, 0)), (0, (0, 0))):
        with tempfile.TemporaryDirectory() as tmp:
            module.DB_FILE = str(Path(tmp) / "devices.db")
            module.init_db()
            at = NOW + timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS,
                                 hours=-1, seconds=seconds)
            keeper = (at.astimezone(UTC) - timedelta(days=1)).strftime(STAMP)
            with closing(sqlite3.connect(module.DB_FILE)) as conn:
                add_device(conn, STALE_MAC, STALE_IP, stale_seen)
                add_device(conn, FRESH_MAC, FRESH_IP, keeper)
                add_service(conn, STALE_MAC, STALE_IP, "available",
                            stamp(timedelta(hours=-1)))
                conn.commit()
            assert module.age_stale_service_state(now=at) == expected, (seconds, expected)

    print("AGE_RESPONDING_SERVICE_KEEPS_ROW=PASS")


def test_presence_boundary_follows_legacy_timezone_convention():
    """The guard uses the same conservative `_timestamp_age` as ageing, in any timezone.

    A naive stored success is protected when its conservative age is no more than the
    retirement window after normalizing the injected clock to the whole-second cutoff
    used by device inventory. The boundary is inclusive and identical under UTC and a
    legacy local zone, and a future-dated value is treated as fresh (no skew policy).
    """
    from zoneinfo import ZoneInfo
    module = load_module()
    days = module.SERVICE_RETIRE_AFTER_DAYS
    now = NOW + timedelta(microseconds=750000)
    freshness_now = now.replace(microsecond=0)

    def protected(verified, legacy_tz):
        age = module._timestamp_age(verified, freshness_now, legacy_tz)
        return age is not None and age <= timedelta(days=days)

    for legacy_tz in (UTC, ZoneInfo("Australia/Sydney")):
        cutoff = (now.astimezone(UTC) - timedelta(days=days)).strftime(STAMP)
        assert protected(cutoff, legacy_tz), (legacy_tz, "exact cutoff")
        fresh = (now.astimezone(UTC) - timedelta(days=days)
                 + timedelta(seconds=1)).strftime(STAMP)
        assert protected(fresh, legacy_tz), (legacy_tz, "one second inside")
        expired = (now.astimezone(UTC) - timedelta(days=days)
                   - timedelta(seconds=1)).strftime(STAMP)
        assert not protected(expired, legacy_tz), (legacy_tz, "one second outside")
        future = (now.astimezone(UTC) + timedelta(days=3)).strftime(STAMP)
        assert protected(future, legacy_tz), (legacy_tz, "future-dated")

    # A naive legacy-local value written 30 days ago in AEDT is 29d13h old under the
    # nearest-interpretation rule, so it is protected; this is the same up-to-offset
    # slack the ageing reader already has, not a guard-specific tolerance.
    sydney = ZoneInfo("Australia/Sydney")
    legacy_local = (now.astimezone(sydney) - timedelta(days=days)).replace(
        tzinfo=None).strftime(STAMP)
    assert protected(legacy_local, sydney)

    print("AGE_PRESENCE_BOUNDARY_LEGACY_TZ=PASS")


def test_non_qualifying_verification_does_not_protect():
    """Authoritative, miss-only, stale-Nmap and malformed timestamps are not presence."""
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        stale = stamp(-timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS + 5))
        fresh = stamp(timedelta(hours=-1))
        cases = []
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, FRESH_MAC, FRESH_IP, fresh)
            for index, (method, confidence, verified) in enumerate((
                    ("authoritative", "authoritative", fresh),
                    ("ssh_banner", "verified", stale),
                    ("nmap_service", "discovered",
                     stamp(-timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS + 60))),
                    ("ssh_banner", "verified", "not-a-timestamp"),
                    ("ssh_banner", "verified", ""),
            )):
                mac = "aa:bb:cc:dd:ee:%02x" % (0x40 + index)
                ip = "198.51.100.%d" % (40 + index)
                add_device(conn, mac, ip, stale)
                conn.execute(
                    "INSERT INTO device_services (mac, ip, interface, service_type, port,"
                    " protocol, status, detection_method, confidence, product, version,"
                    " first_detected, last_verified, last_checked, miss_count)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)",
                    (mac, ip, 'em0', 'SSH', 22, 'tcp', 'available', method,
                     confidence, '', '', fresh, verified, fresh))
                cases.append((mac, ip))
            conn.commit()

        aged, retired = module.age_stale_service_state(now=NOW)
        assert retired == len(cases), (aged, retired)
        for _mac, ip in cases:
            assert read_row(module, ip) is None, ip

    print("AGE_NON_QUALIFYING_VERIFICATION_NOT_PROTECTED=PASS")


def test_dry_run_reports_protection_without_writes():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        stale = stamp(-timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS + 5))
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, FRESH_MAC, FRESH_IP, stamp(timedelta(hours=-1)))
            add_device(conn, STALE_MAC, STALE_IP, stale)
            add_device(conn, "aa:bb:cc:dd:ee:61", "198.51.100.61", stale)
            add_service(conn, STALE_MAC, STALE_IP, "available", stamp(timedelta(hours=-1)))
            add_service(conn, "aa:bb:cc:dd:ee:61", "198.51.100.61", "available",
                        stamp(-timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS + 2)))
            conn.commit()

        assert module.age_stale_service_state(now=NOW, dry_run=True) == (0, 1)
        assert service_count(module) == 2
        assert module.age_stale_service_state(now=NOW) == (0, 1)
        assert service_count(module) == 1
        assert read_row(module, STALE_IP) is not None
        assert read_row(module, "198.51.100.61") is None

    print("AGE_DRY_RUN_RESPECTS_PROTECTION=PASS")


def test_retirement_guard_boundary_is_inclusive_integrated():
    """The real retirement path keeps evidence exactly at the cutoff.

    Each case has stale device inventory at its own address and an unrelated fresh host,
    so only the service guard can keep the row: the global no-fresh-host refusal and the
    device `last_seen` predicate never apply. Canonical evidence is read with both UTC
    and Sydney (the system legacy zone the scheduler uses) using a microsecond-bearing
    `now`; one second outside retires. Separate legacy-local coverage below retains the
    conservative ambiguous-domain policy.
    """
    module = load_module()
    days = module.SERVICE_RETIRE_AFTER_DAYS
    now = NOW + timedelta(microseconds=750000)
    stale_seen = stamp(-timedelta(days=days + 5))

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, FRESH_MAC, FRESH_IP, stamp(timedelta(hours=-1)))
            for index, (label, offset) in enumerate((
                    ("exact", timedelta(0)),
                    ("inside", timedelta(seconds=1)),
                    ("outside", -timedelta(seconds=1)),
            )):
                mac = "aa:bb:cc:dd:ee:%02x" % (0x70 + index)
                ip = "198.51.100.%d" % (0x70 + index)
                add_device(conn, mac, ip, stale_seen)
                add_service(conn, mac, ip, "available",
                            (now - timedelta(days=days) + offset).strftime(STAMP))
            conn.commit()

        aged, retired = module.age_stale_service_state(now=now, legacy_tz=UTC)
        assert (aged, retired) == (0, 1), (aged, retired)
        assert read_row(module, "198.51.100.112") is not None
        assert read_row(module, "198.51.100.113") is not None
        assert read_row(module, "198.51.100.114") is None
        assert service_count(module) == 2, service_count(module)
        assert device_last_seen(module, "198.51.100.112") == stale_seen
        assert device_last_seen(module, "198.51.100.113") == stale_seen

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()
        sydney_stale_seen = (
            now - timedelta(days=days + 5)
        ).strftime(STAMP)
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, FRESH_MAC, FRESH_IP, stamp(timedelta(hours=-1)))
            for index, (label, offset) in enumerate((
                    ("exact", timedelta(0)),
                    ("inside", timedelta(seconds=1)),
                    ("outside", -timedelta(seconds=1)),
            )):
                mac = "aa:bb:cc:dd:ee:%02x" % (0x80 + index)
                ip = "198.51.100.%d" % (0x80 + index)
                add_device(conn, mac, ip, sydney_stale_seen)
                add_service(conn, mac, ip, "available",
                            (now - timedelta(days=days) + offset)
                            .strftime(STAMP))
            conn.commit()

        aged, retired = module.age_stale_service_state(now=now, legacy_tz=SYDNEY)
        assert (aged, retired) == (0, 1), (aged, retired)
        assert read_row(module, "198.51.100.128") is not None
        assert read_row(module, "198.51.100.129") is not None
        assert read_row(module, "198.51.100.130") is None
        assert device_last_seen(module, "198.51.100.128") == sydney_stale_seen
        assert device_last_seen(module, "198.51.100.129") == sydney_stale_seen

    print("AGE_RETIREMENT_GUARD_INCLUSIVE_INTEGRATED=PASS")


def test_retirement_alert_failure_rolls_back_service_delete():
    """A post-DELETE pending-alert failure rolls back retirement as one unit.

    The status-ageing update is deliberately committed before the retirement lock, so it
    remains visible while the service row and its held alert are restored together. Dry
    run reports both actions but writes neither.
    """
    module = load_module()
    days = module.SERVICE_RETIRE_AFTER_DAYS
    retired_key = alert_key(module, STALE_MAC, STALE_IP)

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, FRESH_MAC, FRESH_IP, stamp(timedelta(hours=-1)))
            add_device(conn, STALE_MAC, STALE_IP,
                       stamp(-timedelta(days=days + 5)))
            add_service(
                conn, FRESH_MAC, FRESH_IP, "unavailable",
                stamp(-timedelta(days=module.SERVICE_UNKNOWN_AFTER_DAYS + 1)),
            )
            add_service(conn, STALE_MAC, STALE_IP, "available",
                        stamp(-timedelta(days=days + 2)))
            conn.execute(
                "INSERT INTO service_alert_pending "
                "(service_key, mac, event_json, held_at) VALUES (?, ?, '{}', ?)",
                (retired_key, STALE_MAC, stamp(-timedelta(hours=1))),
            )
            conn.execute(
                """
                CREATE TRIGGER fail_pending_alert_delete
                BEFORE DELETE ON service_alert_pending
                BEGIN
                    SELECT RAISE(ABORT, 'injected pending-alert deletion failure');
                END
                """
            )
            conn.commit()

        assert module.age_stale_service_state(now=NOW, dry_run=True) == (1, 1)
        assert service_count(module) == 2
        assert read_row(module, STALE_IP) == ("available", 0)
        assert pending_keys(module) == {retired_key}

        # The service DELETE succeeds, the pending-alert DELETE fails, and the
        # retirement transaction restores both rows. Ageing's earlier commit remains.
        assert module.age_stale_service_state(now=NOW) == (1, 0)
        assert service_count(module) == 2
        assert read_row(module, FRESH_IP) == ("unknown", 0)
        assert read_row(module, STALE_IP) == ("available", 0)
        assert pending_keys(module) == {retired_key}

        # The dry-run count reflects the committed ageing update but still reports the
        # rolled-back retirement candidate and itself writes nothing.
        assert module.age_stale_service_state(now=NOW, dry_run=True) == (0, 1)
        assert service_count(module) == 2
        assert pending_keys(module) == {retired_key}

    print("AGE_ALERT_FAILURE_ROLLS_BACK_RETIREMENT=PASS")


def test_retirement_transaction_blocks_a_concurrent_refresh():
    """Selection and deletion are one write transaction, in both journal modes.

    Two connections, a temporary database, no sleeps or threads. The interceptor runs the
    real function and fires only at the DELETE statement, with the retirement's write
    lock held. A second connection then has two attempts: refresh the selected service's
    ``last_verified`` (in place for a delete-mode row) and, once, insert a fresh device at
    the stale address. Neither can interpose, so the retirement deletes exactly the
    selected row and its pending alert and leaves both fresh rows intact.
    """
    module = load_module()
    days = module.SERVICE_RETIRE_AFTER_DAYS
    stale_seen = stamp(-timedelta(days=days + 5))
    verified = (NOW - timedelta(days=days + 2)).strftime(STAMP)

    class Recorder(sqlite3.Connection):
        attempts = []
        fired = False

    def concurrent_writer(conn):
        def attempt(sql, params):
            try:
                conn.execute(sql, params)
                conn.commit()
                Recorder.attempts.append("committed")
            except sqlite3.OperationalError as exc:
                conn.rollback()
                Recorder.attempts.append("blocked: %s" % str(exc).split(":", 1)[0])
        attempt(
            "UPDATE device_services SET last_verified = ?, last_checked = ? "
            "WHERE ip = ? AND mac = ?",
            (stamp(timedelta(0)), stamp(timedelta(0)), STALE_IP, STALE_MAC),
        )
        attempt(
            "INSERT INTO devices (mac, ip, vlan, is_active, last_seen) "
            "VALUES ('aa:bb:cc:dd:ee:2f', ?, 'VLAN60', 0, ?)",
            (STALE_IP, stamp(timedelta(hours=-1))),
        )

    def trace(statement):
        if (not Recorder.fired
                and statement.lstrip().upper().startswith("DELETE FROM DEVICE_SERVICES")):
            Recorder.fired = True
            concurrent_writer(writer)

    for journal in ("delete", "wal"):
        with tempfile.TemporaryDirectory() as tmp:
            module.DB_FILE = str(Path(tmp) / "devices.db")
            module.init_db()
            with closing(sqlite3.connect(module.DB_FILE)) as conn:
                assert conn.execute(f"PRAGMA journal_mode = {journal}").fetchone()[0] == journal
                add_device(conn, FRESH_MAC, FRESH_IP, stamp(timedelta(hours=-1)))
                add_service(conn, FRESH_MAC, FRESH_IP, "available", stamp(timedelta(0)))
                add_device(conn, STALE_MAC, STALE_IP, stale_seen)
                add_service(conn, STALE_MAC, STALE_IP, "available", verified)
                conn.executemany(
                    "INSERT INTO service_alert_pending "
                    "(service_key, mac, event_json, held_at) VALUES (?, ?, '{}', ?)",
                    [
                        (alert_key(module, STALE_MAC, STALE_IP), STALE_MAC, stamp(timedelta(0))),
                        (alert_key(module, FRESH_MAC, FRESH_IP), FRESH_MAC, stamp(timedelta(0))),
                    ],
                )
                conn.commit()

            Recorder.attempts = []
            Recorder.fired = False
            writer = sqlite3.connect(module.DB_FILE, timeout=0.2)
            writer.execute("PRAGMA busy_timeout = 200")
            outer = sqlite3.connect(module.DB_FILE, factory=Recorder)
            outer.set_trace_callback(trace)
            try:
                result = module.age_stale_service_state(conn=outer, now=NOW)
            finally:
                outer.close()
                writer.close()

            label = (journal, result, Recorder.attempts)
            assert Recorder.fired, label
            assert result == (0, 1), label
            assert len(Recorder.attempts) == 2, label
            assert all(a.startswith("blocked") for a in Recorder.attempts), label
            with closing(sqlite3.connect(module.DB_FILE)) as conn:
                assert conn.execute(
                    "SELECT COUNT(*) FROM device_services WHERE ip = ?", (STALE_IP,)
                ).fetchone()[0] == 0, label
                assert conn.execute(
                    "SELECT COUNT(*) FROM service_alert_pending WHERE mac = ?", (STALE_MAC,)
                ).fetchone()[0] == 0, label
                assert conn.execute(
                    "SELECT COUNT(*) FROM device_services WHERE ip = ?", (FRESH_IP,)
                ).fetchone()[0] == 1, label
                assert conn.execute(
                    "SELECT COUNT(*) FROM service_alert_pending WHERE mac = ?", (FRESH_MAC,)
                ).fetchone()[0] == 1, label

    print("AGE_RETIREMENT_TRANSACTION_BLOCKS_REFRESH=PASS")


def test_refresh_committed_before_retirement_selection_is_protected():
    """A refresh committed before retirement selection is honoured, not deleted."""
    module = load_module()
    days = module.SERVICE_RETIRE_AFTER_DAYS
    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, FRESH_MAC, FRESH_IP, stamp(timedelta(hours=-1)))
            add_device(conn, STALE_MAC, STALE_IP,
                       stamp(-timedelta(days=days + 5)))
            add_service(conn, STALE_MAC, STALE_IP, "available",
                        stamp(-timedelta(days=days + 2)))
            conn.commit()
        with closing(sqlite3.connect(module.DB_FILE, timeout=5)) as conn:
            conn.execute(
                "UPDATE device_services SET last_verified = ?, last_checked = ? WHERE ip = ?",
                (stamp(-timedelta(hours=1)), stamp(-timedelta(hours=1)), STALE_IP),
            )
            conn.commit()
        assert module.age_stale_service_state(now=NOW) == (0, 0)
        assert read_row(module, STALE_IP) is not None

    print("AGE_REFRESH_BEFORE_SELECTION_SURVIVES=PASS")


def test_authoritative_service_does_not_refresh_device():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        stale_seen = stamp(-timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS + 1))

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, STALE_MAC, STALE_IP, stale_seen)
            # A fresh host keeps the retirement pass from refusing outright.
            add_device(conn, FRESH_MAC, FRESH_IP, stamp(timedelta(hours=-1)))
            conn.commit()

            # Configuration, not an answer: it must not keep the row alive.
            module.upsert_device_service(
                conn, STALE_MAC, STALE_IP, "VLAN60", "SSH", 22, "tcp",
                "authoritative", "authoritative", stamp(timedelta(0)),
                status="available",
            )
            conn.commit()

        assert device_last_seen(module, STALE_IP) == stale_seen

        aged, retired = module.age_stale_service_state(now=NOW)

        assert (aged, retired) == (0, 1), (aged, retired)
        assert read_row(module, STALE_IP) is None

    print("AGE_AUTHORITATIVE_DOES_NOT_REFRESH=PASS")


def test_refresh_never_invents_or_rewinds_device():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        future_seen = stamp(timedelta(hours=2))

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, FRESH_MAC, FRESH_IP, future_seen)
            conn.commit()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            # No device row for this address: discovery must not create one.
            module.upsert_device_service(
                conn, "", ORPHAN_IP, "VLAN60", "SSH", 22, "tcp",
                "ssh_banner", "verified", stamp(timedelta(0)),
            )
            # An older verification must not move a newer timestamp backwards.
            module.upsert_device_service(
                conn, FRESH_MAC, FRESH_IP, "VLAN60", "SSH", 22, "tcp",
                "ssh_banner", "verified", stamp(-timedelta(hours=5)),
            )
            conn.commit()

        assert device_count(module) == 1, device_count(module)
        assert device_last_seen(module, FRESH_IP) == future_seen
        assert device_last_seen(module, ORPHAN_IP) is None

    print("AGE_REFRESH_IS_FORWARD_ONLY=PASS")


def test_utc11_and_utc_writers_store_the_same_instant():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        local_verified = datetime(2026, 11, 12, 21, 44, tzinfo=SYDNEY)
        utc_verified = datetime(2026, 11, 12, 10, 44, tzinfo=UTC)
        expected = "2026-11-12 10:44:00"

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, FRESH_MAC, FRESH_IP, stamp(-timedelta(days=60)))
            module.upsert_device_service(
                conn, FRESH_MAC, FRESH_IP, "VLAN60", "SSH", 22, "tcp",
                "ssh_banner", "verified", local_verified,
                presence_assoc=(FRESH_MAC, FRESH_IP),
            )
            add_device(conn, STALE_MAC, STALE_IP, stamp(-timedelta(days=60)))
            module.upsert_device_service(
                conn, STALE_MAC, STALE_IP, "VLAN60", "SSH", 22, "tcp",
                "ssh_banner", "verified", utc_verified,
                presence_assoc=(STALE_MAC, STALE_IP),
            )
            conn.commit()

        assert device_last_seen(module, FRESH_IP) == expected
        assert device_last_seen(module, STALE_IP) == expected

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            assert conn.execute(
                "SELECT last_verified, last_checked FROM device_services "
                "WHERE ip = ?", (FRESH_IP,)
            ).fetchone() == (expected, expected)
            assert conn.execute(
                "SELECT last_verified, last_checked FROM device_services "
                "WHERE ip = ?", (STALE_IP,)
            ).fetchone() == (expected, expected)

            module.record_service_miss(
                conn, "SSH", "ssh_banner", FRESH_IP, 22, "VLAN60",
                checked_at=local_verified,
            )
            conn.commit()

        assert read_checked(module, FRESH_IP) == expected

    print("TIMESTAMP_UTC11_AND_UTC=PASS")


def test_utc11_legacy_presence_and_retirement_are_conservative():
    module = load_module()
    now = datetime(2026, 11, 12, 11, 0, tzinfo=UTC)
    local_now = now.astimezone(SYDNEY)
    retire_after = timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS)

    utc_boundary = (now - retire_after).strftime(STAMP)
    utc_past = (now - retire_after - timedelta(seconds=1)).strftime(STAMP)
    utc_early_window = (now - retire_after + timedelta(hours=10)).strftime(STAMP)
    local_boundary = (local_now - retire_after).strftime(STAMP)
    local_delayed = (
        local_now - retire_after - timedelta(hours=11) + timedelta(seconds=1)
    ).strftime(STAMP)
    local_expired = (
        local_now - retire_after - timedelta(hours=11) - timedelta(seconds=1)
    ).strftime(STAMP)

    assert module._timestamp_age(
        (now - timedelta(hours=1)).strftime(STAMP), now, SYDNEY
    ) == timedelta(hours=1)
    assert module._timestamp_age(
        (local_now - timedelta(hours=1)).strftime(STAMP), now, SYDNEY
    ) == timedelta(hours=1)

    assert module.is_recently_seen(
        (local_now - timedelta(minutes=5)).strftime(STAMP),
        now=now,
        legacy_tz=SYDNEY,
    )
    assert not module.is_recently_seen(
        (now - timedelta(minutes=20)).strftime(STAMP),
        now=now,
        legacy_tz=SYDNEY,
    )

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, FRESH_MAC, FRESH_IP, utc_boundary)
            add_service(conn, FRESH_MAC, FRESH_IP, "available", utc_boundary)

            add_device(conn, STALE_MAC, STALE_IP, utc_past)
            add_service(conn, STALE_MAC, STALE_IP, "available", utc_past)

            early_mac = "aa:bb:cc:dd:ee:30"
            early_ip = "198.51.100.30"
            add_device(conn, early_mac, early_ip, utc_early_window)
            add_service(conn, early_mac, early_ip, "available", utc_early_window)

            local_mac = "aa:bb:cc:dd:ee:31"
            local_ip = "198.51.100.31"
            add_device(conn, local_mac, local_ip, local_boundary)
            add_service(conn, local_mac, local_ip, "available", local_boundary)

            delayed_mac = "aa:bb:cc:dd:ee:33"
            delayed_ip = "198.51.100.33"
            add_device(conn, delayed_mac, delayed_ip, local_delayed)
            add_service(conn, delayed_mac, delayed_ip, "available", local_delayed)

            expired_mac = "aa:bb:cc:dd:ee:34"
            expired_ip = "198.51.100.34"
            add_device(conn, expired_mac, expired_ip, local_expired)
            add_service(conn, expired_mac, expired_ip, "available", local_expired)

            add_device(conn, "aa:bb:cc:dd:ee:32", "198.51.100.32",
                       stamp(-timedelta(hours=1)))
            conn.commit()

        aged, retired = module.age_stale_service_state(
            now=now, legacy_tz=SYDNEY
        )

        assert (aged, retired) == (0, 2), (aged, retired)
        assert read_row(module, FRESH_IP) is not None
        assert read_row(module, early_ip) is not None
        assert read_row(module, local_ip) is not None
        assert read_row(module, delayed_ip) is not None
        assert read_row(module, STALE_IP) is None
        assert read_row(module, expired_ip) is None

    print("TIMESTAMP_UTC11_RETIREMENT_BOUNDARY=PASS")


def test_legacy_unknown_age_is_not_premature_and_eventually_expires():
    module = load_module()
    now = datetime(2026, 11, 12, 11, 0, tzinfo=UTC)
    local_now = now.astimezone(SYDNEY)
    age_after = timedelta(days=module.SERVICE_UNKNOWN_AFTER_DAYS)

    utc_boundary = (now - age_after).strftime(STAMP)
    utc_expired = (now - age_after - timedelta(seconds=1)).strftime(STAMP)
    local_boundary = (local_now - age_after).strftime(STAMP)
    local_delayed = (
        local_now - age_after - timedelta(hours=11) + timedelta(seconds=1)
    ).strftime(STAMP)
    local_expired = (
        local_now - age_after - timedelta(hours=11) - timedelta(seconds=1)
    ).strftime(STAMP)

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_service(conn, "aa:bb:cc:dd:ee:40", "198.51.100.40",
                        "unavailable", utc_boundary, port=2240)
            add_service(conn, "aa:bb:cc:dd:ee:41", "198.51.100.41",
                        "unavailable", utc_expired, port=2241)
            add_service(conn, "aa:bb:cc:dd:ee:42", "198.51.100.42",
                        "unavailable", local_boundary, port=2242)
            add_service(conn, "aa:bb:cc:dd:ee:43", "198.51.100.43",
                        "unavailable", local_delayed, port=2243)
            add_service(conn, "aa:bb:cc:dd:ee:44", "198.51.100.44",
                        "unavailable", local_expired, port=2244)
            conn.commit()

        aged, retired = module.age_stale_service_state(
            now=now, legacy_tz=SYDNEY
        )

        assert (aged, retired) == (2, 0), (aged, retired)
        assert read_status(module, "198.51.100.40", 2240) == "unavailable"
        assert read_status(module, "198.51.100.41", 2241) == "unknown"
        assert read_status(module, "198.51.100.42", 2242) == "unavailable"
        assert read_status(module, "198.51.100.43", 2243) == "unavailable"
        assert read_status(module, "198.51.100.44", 2244) == "unknown"

    print("TIMESTAMP_UNKNOWN_AGE_BOUNDARY=PASS")


def test_dst_timestamp_boundaries_are_history_aware():
    module = load_module()

    assert module.utc_timestamp(
        datetime(2026, 10, 4, 1, 59, 59, tzinfo=SYDNEY)
    ) == "2026-10-03 15:59:59"
    assert module.utc_timestamp(
        datetime(2026, 10, 4, 3, 0, 0, tzinfo=SYDNEY)
    ) == "2026-10-03 16:00:00"

    ambiguous = datetime(2026, 4, 5, 2, 30, tzinfo=SYDNEY)
    assert module.utc_timestamp(ambiguous.replace(fold=0)) == \
        "2026-04-04 15:30:00"
    assert module.utc_timestamp(ambiguous.replace(fold=1)) == \
        "2026-04-04 16:30:00"

    spring_now = datetime(2026, 10, 3, 16, 30, tzinfo=UTC)
    assert module._timestamp_age(
        "2026-10-04 01:15:00", spring_now, SYDNEY
    ) == timedelta(hours=1, minutes=15)
    assert module._timestamp_age(
        "2026-10-04 03:25:00", spring_now, SYDNEY
    ) == timedelta(minutes=5)

    fall_now = datetime(2026, 4, 4, 16, 30, tzinfo=UTC)
    fall_ages = module._timestamp_age_bounds(
        "2026-04-05 02:16:00", fall_now, SYDNEY
    )
    assert timedelta(minutes=14) in fall_ages, fall_ages
    assert timedelta(hours=1, minutes=14) in fall_ages, fall_ages
    assert module.is_recently_seen(
        "2026-04-05 02:16:00", now=fall_now, legacy_tz=SYDNEY
    )

    new_york = ZoneInfo("America/New_York")
    cutoff_now = datetime(2026, 4, 1, 12, 0, tzinfo=UTC)
    assert module._conservative_cutoff(
        cutoff_now, 30, new_york
    ) == "2026-03-02 07:00:00"
    assert module._conservative_cutoff(
        datetime(2026, 11, 8, 6, 30, tzinfo=UTC), 7, new_york
    ) == "2026-11-01 00:30:00"

    canonical_now = datetime(2026, 11, 12, 12, 0, tzinfo=UTC)
    assert module._timestamp_age(
        (canonical_now - timedelta(hours=20)).strftime(STAMP),
        canonical_now,
        SYDNEY,
    ) == timedelta(hours=20)
    assert module._timestamp_age(
        (canonical_now - timedelta(hours=6)).strftime(STAMP),
        canonical_now,
        new_york,
    ) == timedelta(hours=1)

    print("TIMESTAMP_DST_BOUNDARIES=PASS")


def main():
    test_window_constants()
    test_ageing_boundary()
    test_available_and_unknown_untouched()
    test_miss_count_reset()
    test_retirement_boundary()
    test_endpoint_without_device_record_kept()
    test_refuses_when_no_host_is_fresh()
    test_dry_run_writes_nothing()
    test_pending_alert_removed_with_retired_row()
    test_retirement_writes_no_activity_event()
    test_scheduler_runs_ageing()
    test_cli_dry_run()
    test_verified_service_refreshes_device_last_seen()
    test_association_must_match_mac_and_ip()
    test_dhcp_success_records_endpoint_but_not_device_presence()
    test_responding_service_without_hostwatch_keeps_the_row()
    test_retirement_guard_boundary_is_inclusive_integrated()
    test_retirement_alert_failure_rolls_back_service_delete()
    test_retirement_transaction_blocks_a_concurrent_refresh()
    test_refresh_committed_before_retirement_selection_is_protected()
    test_presence_boundary_follows_legacy_timezone_convention()
    test_non_qualifying_verification_does_not_protect()
    test_dry_run_reports_protection_without_writes()
    test_authoritative_service_does_not_refresh_device()
    test_refresh_never_invents_or_rewinds_device()
    test_utc11_and_utc_writers_store_the_same_instant()
    test_utc11_legacy_presence_and_retirement_are_conservative()
    test_legacy_unknown_age_is_not_premature_and_eventually_expires()
    test_dst_timestamp_boundaries_are_history_aware()
    test_recent_probe_prevents_ageing()
    test_miss_stamps_last_checked_and_prevents_reflip_cycle()
    test_init_db_adds_and_backfills_last_checked()
    test_retirement_keeps_address_with_a_fresh_device_row()
    test_retirement_drops_address_with_only_stale_rows()
    test_nmap_evidence_age_bound()

    print("SERVICE_AGEING=PASS")

def test_nmap_evidence_age_bound():
    module = load_module()
    day = timedelta(days=module.SERVICE_UNKNOWN_AFTER_DAYS)

    def at(delta):
        return (NOW + delta).strftime("%Y-%m-%d %H:%M:%S")

    assert module.nmap_evidence_is_current(at(timedelta(hours=-1)), now=NOW)
    assert module.nmap_evidence_is_current(at(-day), now=NOW)
    assert not module.nmap_evidence_is_current(
        at(-day - timedelta(seconds=1)), now=NOW
    )
    assert module.nmap_evidence_is_current("", now=NOW)
    assert module.nmap_evidence_is_current("not-a-date", now=NOW)

    print("NMAP_EVIDENCE_AGE_BOUND=PASS")


def test_retirement_keeps_address_with_a_fresh_device_row():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            # One legacy row for the address is stale, a live VRRP/CARP row is not.
            add_device(conn, STALE_MAC, STALE_IP,
                       stamp(-timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS + 20)))
            add_device(conn, FRESH_MAC, STALE_IP, stamp(timedelta(hours=-2)))
            add_service(conn, STALE_MAC, STALE_IP, "available", stamp(timedelta(0)))
            conn.commit()

        aged, retired = module.age_stale_service_state(now=NOW)

        assert (aged, retired) == (0, 0), (aged, retired)
        assert read_row(module, STALE_IP) is not None

    print("RETIRE_KEEPS_ADDRESS_WITH_FRESH_ROW=PASS")


def test_retirement_drops_address_with_only_stale_rows():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        stale_seen = stamp(-timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS + 20))

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, STALE_MAC, STALE_IP, stale_seen)
            add_device(conn, "aa:bb:cc:dd:ee:29", STALE_IP, stale_seen)
            add_device(conn, FRESH_MAC, FRESH_IP, stamp(timedelta(hours=-1)))
            add_service(conn, STALE_MAC, STALE_IP, "available",
                        stamp(-timedelta(days=module.SERVICE_RETIRE_AFTER_DAYS + 2)))
            conn.commit()

        aged, retired = module.age_stale_service_state(now=NOW)

        assert (aged, retired) == (0, 1), (aged, retired)
        assert read_row(module, STALE_IP) is None

    print("RETIRE_DROPS_ADDRESS_WITH_ONLY_STALE_ROWS=PASS")


def read_checked(module, ip, port=22):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        return conn.execute(
            "SELECT last_checked FROM device_services WHERE ip = ? AND port = ?",
            (ip, port),
        ).fetchone()[0]


def test_recent_probe_prevents_ageing():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, FRESH_MAC, FRESH_IP, stamp(timedelta(hours=-1)))
            # Last success long ago, but the endpoint is still being observed.
            add_service(conn, FRESH_MAC, FRESH_IP, "unavailable",
                        stamp(-timedelta(days=30)))
            conn.execute(
                "UPDATE device_services SET last_checked = ? WHERE ip = ?",
                (stamp(timedelta(hours=-1)), FRESH_IP),
            )
            conn.commit()

        aged, retired = module.age_stale_service_state(now=NOW)

        assert (aged, retired) == (0, 0), (aged, retired)
        assert read_row(module, FRESH_IP)[0] == "unavailable"

    print("AGE_RECENT_PROBE_NOT_AGED=PASS")


def test_miss_stamps_last_checked_and_prevents_reflip_cycle():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            add_device(conn, FRESH_MAC, FRESH_IP, stamp(timedelta(hours=-1)))
            add_service(conn, FRESH_MAC, FRESH_IP, "unavailable",
                        stamp(-timedelta(days=30)))
            conn.execute(
                "UPDATE device_services SET last_checked = ? WHERE ip = ?",
                (stamp(-timedelta(days=30)), FRESH_IP),
            )
            conn.commit()

        # Abandoned row: aged once.
        assert module.age_stale_service_state(now=NOW) == (1, 0)
        assert read_row(module, FRESH_IP)[0] == "unknown"

        # The endpoint is probed again and fails: counter and time both move.
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            module.record_service_miss(
                conn, "SSH", "ssh_banner", FRESH_IP, 22, "VLAN60",
                checked_at=stamp(timedelta(minutes=-50)),
            )
            conn.commit()

        assert read_checked(module, FRESH_IP) == stamp(timedelta(minutes=-50))
        assert read_row(module, FRESH_IP) == ("unknown", 1)

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            module.record_service_miss(
                conn, "SSH", "ssh_banner", FRESH_IP, 22, "VLAN60",
                checked_at=stamp(timedelta(minutes=-20)),
            )
            conn.commit()

        assert read_row(module, FRESH_IP) == ("unavailable", 2)

        # The next ageing pass must not touch a row observed 20 minutes ago,
        # even though its last success is a month old.
        assert module.age_stale_service_state(now=NOW) == (0, 0)
        assert read_row(module, FRESH_IP)[0] == "unavailable"

    print("AGE_MISS_ADVANCES_LAST_CHECKED=PASS")


def test_init_db_adds_and_backfills_last_checked():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")

        # A pre-Decision-54 database: device_services without last_checked.
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute(
                """
                CREATE TABLE device_services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mac TEXT,
                    ip TEXT NOT NULL,
                    interface TEXT NOT NULL DEFAULT '',
                    service_type TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    protocol TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'available',
                    detection_method TEXT NOT NULL,
                    confidence TEXT NOT NULL,
                    product TEXT,
                    version TEXT,
                    first_detected DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_verified DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    miss_count INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(ip, service_type, port, protocol,
                           detection_method, interface)
                )
                """
            )
            conn.execute(
                "INSERT INTO device_services (mac, ip, interface, service_type, "
                "port, protocol, status, detection_method, confidence, "
                "first_detected, last_verified) "
                "VALUES (?, ?, 'VLAN60', 'SSH', 22, 'tcp', 'unavailable', "
                "'ssh_banner', 'verified', ?, ?)",
                (FRESH_MAC, FRESH_IP, stamp(-timedelta(days=9)),
                 stamp(-timedelta(days=9))),
            )
            conn.commit()

        module.init_db()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            columns = {
                row[1]
                for row in conn.execute("PRAGMA table_info(device_services)")
            }

        assert "last_checked" in columns, columns
        assert {
            "first_detected_utc",
            "last_verified_utc",
            "last_checked_utc",
        } <= columns
        assert read_checked(module, FRESH_IP) == stamp(-timedelta(days=9))

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            markers = conn.execute(
                "SELECT first_detected_utc, last_verified_utc, "
                "last_checked_utc FROM device_services WHERE ip = ?",
                (FRESH_IP,),
            ).fetchone()
        assert markers == (None, None, None)

        # Backfilled from last_verified, so the old row still ages.
        assert module.age_stale_service_state(now=NOW) == (1, 0)

    print("AGE_LAST_CHECKED_MIGRATION=PASS")
    print("AGE_TIMESTAMP_PROVENANCE_MIGRATION=PASS")
if __name__ == "__main__":
    main()
