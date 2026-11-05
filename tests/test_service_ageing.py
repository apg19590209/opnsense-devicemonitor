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

NOW = datetime(2026, 10, 31, 12, 0, 0)
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
    return module


def stamp(delta):
    return (NOW + delta).strftime(STAMP)


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
                        stamp(-retire_after))
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
            add_service(conn, STALE_MAC, STALE_IP, "available", stamp(timedelta(0)))
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
            add_service(conn, STALE_MAC, STALE_IP, "available", stamp(timedelta(0)))
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
            add_service(conn, STALE_MAC, STALE_IP, "available", stamp(timedelta(0)))
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

        # A probe that answers is presence evidence: hostwatch alone is not.
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            module.upsert_device_service(
                conn, STALE_MAC, STALE_IP, "VLAN60", "SSH", 22, "tcp",
                "ssh_banner", "verified", stamp(timedelta(0)),
            )
            conn.commit()

        assert device_last_seen(module, STALE_IP) == stamp(timedelta(0))

        aged, retired = module.age_stale_service_state(now=NOW)

        assert (aged, retired) == (0, 0), (aged, retired)
        assert read_row(module, STALE_IP) is not None

    print("AGE_VERIFIED_SERVICE_REFRESHES_DEVICE=PASS")


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
    test_authoritative_service_does_not_refresh_device()
    test_refresh_never_invents_or_rewinds_device()
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
            add_service(conn, STALE_MAC, STALE_IP, "available", stamp(timedelta(0)))
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
        assert read_checked(module, FRESH_IP) == stamp(-timedelta(days=9))

        # Backfilled from last_verified, so the old row still ages.
        assert module.age_stale_service_state(now=NOW) == (1, 0)

    print("AGE_LAST_CHECKED_MIGRATION=PASS")
if __name__ == "__main__":
    main()
