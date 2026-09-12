import builtins
import importlib.util
import json
import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


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
        "devicemonitor_service_alert_test",
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


def alert_config(**overrides):
    config = {
        "enabled": True,
        "email_enabled": True,
        "email_to": "admin@example.test",
        "service_email_enabled": True,
        "service_email_new": True,
        "service_email_unavailable": True,
        "service_email_recovered": True,
    }
    config.update(overrides)
    return config


def seed_alert_events(module):
    module.init_db()

    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        conn.execute(
            """
            UPDATE service_alert_state
            SET last_service_id = 0,
                last_activity_event_id = 0
            WHERE id = 1
            """
        )

        conn.execute(
            """
            INSERT INTO device_services (
                mac, ip, interface, service_type, port, protocol,
                status, detection_method, confidence,
                product, version, first_detected, last_verified
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "aa:aa:aa:aa:aa:11",
                "192.0.2.11",
                "LAN",
                "SSH",
                22,
                "tcp",
                "available",
                "nmap_service",
                "discovered",
                "",
                "",
                "2026-09-12 01:00:00",
                "2026-09-12 01:00:00",
            ),
        )
        discovered_id = conn.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]

        conn.execute(
            """
            INSERT INTO device_services (
                mac, ip, interface, service_type, port, protocol,
                status, detection_method, confidence,
                product, version, first_detected, last_verified
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "aa:aa:aa:aa:aa:12",
                "192.0.2.12",
                "LAN",
                "DNS",
                53,
                "udp",
                "available",
                "dns_query",
                "verified",
                "Test DNS",
                "1.0",
                "2026-09-12 02:00:00",
                "2026-09-12 02:00:00",
            ),
        )
        trusted_id = conn.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]

        conn.execute(
            """
            INSERT INTO device_activity_events (
                mac, lifecycle_id, event_type, occurred_at,
                old_value, new_value, details
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "aa:aa:aa:aa:aa:12",
                1,
                "SERVICE_CHANGED",
                "2026-09-12 03:00:00",
                "available",
                "degraded",
                "DNS|192.0.2.12|53|udp|LAN|dns_query",
            ),
        )
        changed_id = conn.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]

        conn.execute(
            """
            INSERT INTO device_activity_events (
                mac, lifecycle_id, event_type, occurred_at,
                old_value, new_value, details
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "aa:aa:aa:aa:aa:12",
                1,
                "SERVICE_UNAVAILABLE",
                "2026-09-12 04:00:00",
                "available",
                "unavailable",
                "DNS|192.0.2.12|53|udp|LAN|dns_query",
            ),
        )
        unavailable_id = conn.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]

        conn.execute(
            """
            INSERT INTO device_activity_events (
                mac, lifecycle_id, event_type, occurred_at,
                old_value, new_value, details
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "aa:aa:aa:aa:aa:12",
                1,
                "SERVICE_AVAILABLE",
                "2026-09-12 05:00:00",
                "unavailable",
                "available",
                "DNS|192.0.2.12|53|udp|LAN|dns_query",
            ),
        )
        recovered_id = conn.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]

        conn.commit()

    return {
        "discovered": discovered_id,
        "trusted": trusted_id,
        "changed": changed_id,
        "unavailable": unavailable_id,
        "recovered": recovered_id,
    }


def read_cursor(module):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        return conn.execute(
            """
            SELECT last_service_id, last_activity_event_id
            FROM service_alert_state
            WHERE id = 1
            """
        ).fetchone()


def test_reader_filtering_and_global_gates():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.LOG_FILE = str(Path(tmp) / "devicemonitor.log")
        ids = seed_alert_events(module)

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            events = module.get_pending_service_alert_events(conn)

        by_key = {
            (event["source"], event["record_id"]): event
            for event in events
        }

        assert by_key[
            ("device_services", ids["discovered"])
        ]["alert_eligible"] is False

        assert by_key[
            ("device_services", ids["trusted"])
        ]["alert_eligible"] is True

        for activity_id in (
            ids["changed"],
            ids["unavailable"],
            ids["recovered"],
        ):
            event = by_key[("device_activity_events", activity_id)]
            assert event["alert_eligible"] is True
            assert event["confidence"] == "verified"
            assert event["product"] == "Test DNS"
            assert event["version"] == "1.0"

        selected = module.select_service_alert_events(
            alert_config(),
            events,
        )
        selected_types = [event["event_type"] for event in selected]

        assert "SERVICE_DISCOVERED" in selected_types
        assert "SERVICE_UNAVAILABLE" in selected_types
        assert "SERVICE_AVAILABLE" in selected_types
        assert "SERVICE_CHANGED" not in selected_types

        for disabled_config in (
            alert_config(enabled=False),
            alert_config(email_enabled=False),
            alert_config(email_to=""),
            alert_config(service_email_enabled=False),
        ):
            assert module.select_service_alert_events(
                disabled_config,
                events,
            ) == []

    print("SERVICE_ALERT_READER_FILTERS=PASS")
    print("SERVICE_ALERT_GLOBAL_GATES=PASS")
    print("SERVICE_CHANGED_EMAIL_V1=NO")


def test_helper_invocation_contract():
    module = load_module()
    calls = []

    def fake_run(command, **kwargs):
        calls.append((list(command), kwargs))
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({
                "result": "sent",
                "message": "ok",
            }),
            stderr="",
        )

    module.subprocess.run = fake_run

    event = {
        "event_type": "SERVICE_DISCOVERED",
        "alert_eligible": True,
        "service_type": "DNS",
    }

    assert module.send_service_alert_email([event]) is True
    assert len(calls) == 1

    command, kwargs = calls[0]
    assert command == [
        "/usr/local/bin/php",
        (
            "/usr/local/opnsense/scripts/OPNsense/"
            "DeviceMonitor/notify_service_email.php"
        ),
    ]
    assert json.loads(kwargs["input"]) == {"events": [event]}
    assert kwargs["timeout"] == 30

    module.subprocess.run = lambda *args, **kwargs: SimpleNamespace(
        returncode=0,
        stdout=json.dumps({
            "result": "skipped",
            "message": "Email disabled",
        }),
        stderr="",
    )
    assert module.send_service_alert_email([event]) is False

    print("SERVICE_ALERT_HELPER_CONTRACT=PASS")


def test_failure_retry_success_and_disabled_cursor_behavior():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.LOG_FILE = str(Path(tmp) / "devicemonitor.log")
        ids = seed_alert_events(module)

        lock_token = object()
        releases = []

        module.acquire_service_alert_lock = lambda: lock_token
        module.release_service_alert_lock = (
            lambda value: releases.append(value)
        )

        config = alert_config(service_email_recovered=False)

        module.send_service_alert_email = lambda events: False
        assert module.process_service_alerts(config) is False

        assert read_cursor(module) == (
            ids["discovered"],
            ids["changed"],
        )
        assert releases == [lock_token]

        releases.clear()
        module.send_service_alert_email = lambda events: True
        assert module.process_service_alerts(config) is True

        assert read_cursor(module) == (
            ids["trusted"],
            ids["recovered"],
        )
        assert releases == [lock_token]

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute(
                """
                UPDATE service_alert_state
                SET last_service_id = 0,
                    last_activity_event_id = 0
                WHERE id = 1
                """
            )
            conn.commit()

        sends = []
        module.send_service_alert_email = (
            lambda events: sends.append(events) or True
        )

        assert module.process_service_alerts(
            alert_config(service_email_enabled=False)
        ) is True

        assert sends == []
        assert read_cursor(module) == (
            ids["trusted"],
            ids["recovered"],
        )

    print("SERVICE_ALERT_FAILED_DELIVERY_RETRY=PASS")
    print("SERVICE_ALERT_SUCCESS_CURSOR_ADVANCE=PASS")
    print("SERVICE_ALERT_DISABLED_SEND=NO")
    print("SERVICE_ALERT_DISABLED_CURSOR_ADVANCE=PASS")


def test_real_nonblocking_lock():
    module = load_module()

    if os.name == "nt":
        print("SERVICE_ALERT_REAL_LOCK=SKIP_WINDOWS")
        return

    with tempfile.TemporaryDirectory() as tmp:
        lock_path = str(Path(tmp) / "service-alerts.lock")
        real_open = os.open

        def redirected_open(path, flags, mode=0o777):
            if path == "/var/run/devicemonitor-service-alerts.lock":
                path = lock_path
            return real_open(path, flags, mode)

        with mock.patch("os.open", side_effect=redirected_open):
            first = module.acquire_service_alert_lock()
            assert first is not None

            try:
                second = module.acquire_service_alert_lock()
                assert second is None
            finally:
                module.release_service_alert_lock(first)

            third = module.acquire_service_alert_lock()
            assert third is not None
            module.release_service_alert_lock(third)

    print("SERVICE_ALERT_REAL_LOCK=PASS")


def test_busy_lock_skips_without_processing():
    module = load_module()

    module.acquire_service_alert_lock = lambda: None

    def forbidden_init():
        raise AssertionError(
            "Busy service-alert lock entered processor"
        )

    module.init_db = forbidden_init

    assert module.process_service_alerts(alert_config()) is True

    print("SERVICE_ALERT_BUSY_LOCK_SKIP=PASS")


def main():
    test_reader_filtering_and_global_gates()
    test_helper_invocation_contract()
    test_failure_retry_success_and_disabled_cursor_behavior()
    test_real_nonblocking_lock()
    test_busy_lock_skips_without_processing()
    print("DM_BL003_SERVICE_ALERT_REGRESSION=PASS")


if __name__ == "__main__":
    main()
