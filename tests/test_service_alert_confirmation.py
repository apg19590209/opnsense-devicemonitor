"""Outage alerts must be confirmed, not fired on a single sample.

v2.11 service-liveness noise fix (O2). Discovery runs hourly and a single failed
probe writes `unavailable`, which the activity trigger turns into
`SERVICE_UNAVAILABLE`; `select_service_alert_events()` then mailed both that
event and the matching `SERVICE_AVAILABLE` on the next run. On the testbed 7 of
8 recorded down/up pairs lasted exactly one discovery interval, i.e. the
service was reported offline and back online once per flap.

`process_service_alerts()` now runs a confirmation stage before delivery:

  * a first-time outage is held in `service_alert_pending` for
    `SERVICE_ALERT_CONFIRM_SECONDS` (longer than one discovery run);
  * a recovery inside that window deletes the hold and drops both emails, so a
    flap is silent;
  * a hold that survives the window releases the original event once, and the
    `SERVICE_ALERT_QUIET_SECONDS` window stops repeat emails for the same
    service;
  * a recovery is only emailed for an outage that was actually reported;
  * held events keep the alert cursor stopped, so the recovery is still read;
  * a failed delivery keeps the hold and is retried on the next cycle.

All checks run against a temporary database with the lock and the PHP mail
helper stubbed, so nothing is sent and no real state is touched.
"""
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

MAC = "aa:bb:cc:dd:ee:10"
IP = "192.168.50.20"
DETAILS = "DNS|192.168.50.20|53|udp|LAN|dns_query"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "devicemonitor_alert_confirmation_test",
        SOURCE,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.log = lambda message: None
    return module


def alert_config(**overrides):
    config = {
        "enabled": True,
        "email_enabled": True,
        "email_to": "admin@example.test",
        "service_email_enabled": True,
        "service_email_new": False,
        "service_email_unavailable": True,
        "service_email_recovered": True,
    }
    config.update(overrides)
    return config


def networks_fixture():
    return [{
        "name": "opt1",
        "description": "DMTEST",
        "device": "vlan0.50",
        "ip": "192.168.50.1",
        "subnet": "24",
        "network": ipaddress.ip_network("192.168.50.0/24"),
    }]


def seed(module):
    """Create the schema and one trusted DNS service on a fresh cursor."""
    module.init_db()

    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        conn.execute(
            "UPDATE service_alert_state "
            "SET last_service_id = 0, last_activity_event_id = 0 WHERE id = 1"
        )
        conn.execute(
            """
            INSERT INTO device_services (
                mac, ip, interface, service_type, port, protocol,
                status, detection_method, confidence,
                product, version, first_detected, last_verified
            )
            VALUES (?, ?, 'LAN', 'DNS', 53, 'udp', 'available',
                    'dns_query', 'verified', 'Test DNS', '1.0',
                    '2026-10-31 00:00:00', '2026-10-31 00:00:00')
            """,
            (MAC, IP),
        )
        conn.commit()


def add_activity(module, event_type, old_value, new_value, when):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        cursor = conn.execute(
            """
            INSERT INTO device_activity_events (
                mac, lifecycle_id, event_type, occurred_at,
                old_value, new_value, details
            )
            VALUES (?, 1, ?, ?, ?, ?, ?)
            """,
            (MAC, event_type, when, old_value, new_value, DETAILS),
        )
        conn.commit()
        return cursor.lastrowid


def stub_delivery(module, outcomes=(True,)):
    """Replace the lock and mail helper; return the list of sent batches."""
    sends = []
    responses = list(outcomes)
    token = object()

    module.acquire_service_alert_lock = lambda: token
    module.release_service_alert_lock = lambda value: None

    def fake_send(events):
        sends.append(list(events))
        if responses:
            return responses.pop(0)
        return True

    module.send_service_alert_email = fake_send
    return sends


def read_holds(module):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        return conn.execute(
            """
            SELECT service_key, notified, notified_at
            FROM service_alert_pending
            ORDER BY service_key
            """
        ).fetchall()


def read_cursor(module):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        return conn.execute(
            "SELECT last_service_id, last_activity_event_id "
            "FROM service_alert_state WHERE id = 1"
        ).fetchone()



def age_holds(module, seconds):
    """Push every outstanding hold further into the past."""
    when = (
        datetime.now() - timedelta(seconds=seconds)
    ).strftime('%Y-%m-%d %H:%M:%S')

    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        conn.execute(
            "UPDATE service_alert_pending SET held_at = ? WHERE notified = 0",
            (when,),
        )
        conn.commit()


def test_flap_is_silent():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)
        sends = stub_delivery(module)

        down_id = add_activity(
            module,
            "SERVICE_UNAVAILABLE",
            "available",
            "unavailable",
            "2026-10-31 01:00:00",
        )

        assert module.process_service_alerts(
            alert_config(),
            networks_fixture(),
        ) is True
        assert sends == [], sends

        holds = read_holds(module)
        assert len(holds) == 1, holds
        assert holds[0][1] == 0, holds
        # The hold lives in service_alert_pending, so the cursor has already
        # consumed the outage event; the recovery is matched by service key.
        assert read_cursor(module)[1] == down_id, read_cursor(module)

        up_id = add_activity(
            module,
            "SERVICE_AVAILABLE",
            "unavailable",
            "available",
            "2026-10-31 01:30:00",
        )

        assert module.process_service_alerts(
            alert_config(),
            networks_fixture(),
        ) is True
        assert sends == [], sends
        assert read_holds(module) == [], read_holds(module)
        assert read_cursor(module)[1] == up_id, read_cursor(module)

    print("ALERT_FLAP_SILENT=PASS")


def test_sustained_outage_is_delivered_once():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)
        sends = stub_delivery(module)

        add_activity(
            module,
            "SERVICE_UNAVAILABLE",
            "available",
            "unavailable",
            "2026-10-31 01:00:00",
        )
        assert module.process_service_alerts(
            alert_config(),
            networks_fixture(),
        ) is True
        assert sends == [], sends

        age_holds(module, module.SERVICE_ALERT_CONFIRM_SECONDS + 60)

        assert module.process_service_alerts(
            alert_config(),
            networks_fixture(),
        ) is True

        assert len(sends) == 1, sends
        assert [e["event_type"] for e in sends[0]] == ["SERVICE_UNAVAILABLE"]

        holds = read_holds(module)
        assert len(holds) == 1, holds
        assert holds[0][1] == 1, holds

        assert module.process_service_alerts(
            alert_config(),
            networks_fixture(),
        ) is True
        assert len(sends) == 1, sends

        add_activity(
            module,
            "SERVICE_UNAVAILABLE",
            "available",
            "unavailable",
            "2026-10-31 02:00:00",
        )
        assert module.process_service_alerts(
            alert_config(),
            networks_fixture(),
        ) is True
        assert len(sends) == 1, sends

    print("ALERT_OUTAGE_CONFIRMED_ONCE=PASS")
    print("ALERT_QUIET_WINDOW=PASS")



def test_recovery_after_delivery_is_emailed():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)
        sends = stub_delivery(module)

        add_activity(
            module,
            "SERVICE_UNAVAILABLE",
            "available",
            "unavailable",
            "2026-10-31 01:00:00",
        )
        module.process_service_alerts(alert_config(), networks_fixture())
        age_holds(module, module.SERVICE_ALERT_CONFIRM_SECONDS + 60)
        module.process_service_alerts(alert_config(), networks_fixture())
        assert len(sends) == 1, sends

        add_activity(
            module,
            "SERVICE_AVAILABLE",
            "unavailable",
            "available",
            "2026-10-31 03:00:00",
        )
        assert module.process_service_alerts(
            alert_config(),
            networks_fixture(),
        ) is True

        assert len(sends) == 2, sends
        assert [e["event_type"] for e in sends[1]] == ["SERVICE_AVAILABLE"]
        assert read_holds(module) == [], read_holds(module)

    print("ALERT_RECOVERY_AFTER_OUTAGE=PASS")


def test_unheld_recovery_is_dropped():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)
        sends = stub_delivery(module)

        up_id = add_activity(
            module,
            "SERVICE_AVAILABLE",
            "unavailable",
            "available",
            "2026-10-31 01:00:00",
        )

        assert module.process_service_alerts(
            alert_config(),
            networks_fixture(),
        ) is True
        assert sends == [], sends
        assert read_holds(module) == [], read_holds(module)
        assert read_cursor(module)[1] == up_id, read_cursor(module)

    print("ALERT_UNREPORTED_RECOVERY_DROPPED=PASS")


def test_failed_delivery_keeps_hold_for_retry():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)
        sends = stub_delivery(module, outcomes=(False,))

        add_activity(
            module,
            "SERVICE_UNAVAILABLE",
            "available",
            "unavailable",
            "2026-10-31 01:00:00",
        )
        module.process_service_alerts(alert_config(), networks_fixture())
        age_holds(module, module.SERVICE_ALERT_CONFIRM_SECONDS + 60)

        assert module.process_service_alerts(
            alert_config(),
            networks_fixture(),
        ) is False
        assert len(sends) == 1, sends

        holds = read_holds(module)
        assert len(holds) == 1, holds
        assert holds[0][1] == 0, holds

        assert module.process_service_alerts(
            alert_config(),
            networks_fixture(),
        ) is True
        assert len(sends) == 2, sends

        holds = read_holds(module)
        assert holds[0][1] == 1, holds

    print("ALERT_CONFIRMATION_RETRY=PASS")


def test_held_outage_does_not_block_later_events():
    """An outstanding hold must not delay an unrelated service's alert."""
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)
        sends = stub_delivery(module)

        add_activity(
            module,
            "SERVICE_UNAVAILABLE",
            "available",
            "unavailable",
            "2026-10-31 01:00:00",
        )
        assert module.process_service_alerts(
            alert_config(),
            networks_fixture(),
        ) is True
        assert sends == [], sends
        assert len(read_holds(module)) == 1, read_holds(module)

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            cursor = conn.execute(
                """
                INSERT INTO device_services (
                    mac, ip, interface, service_type, port, protocol,
                    status, detection_method, confidence,
                    product, version, first_detected, last_verified
                )
                VALUES ('aa:bb:cc:dd:ee:11', '192.168.50.21', 'LAN', 'SSH', 22,
                        'tcp', 'available', 'nmap_service', 'verified',
                        'OpenSSH', '9.9', '2026-10-31 02:00:00',
                        '2026-10-31 02:00:00')
                """
            )
            conn.commit()
            new_id = cursor.lastrowid

        assert module.process_service_alerts(
            alert_config(service_email_new=True),
            networks_fixture(),
        ) is True

        delivered = [event for batch in sends for event in batch]
        assert [event["record_id"] for event in delivered] == [new_id], delivered
        assert delivered[0]["ip"] == "192.168.50.21", delivered

    print("ALERT_HELD_OUTAGE_NOT_BLOCKING=PASS")


def main():
    test_flap_is_silent()
    test_sustained_outage_is_delivered_once()
    test_recovery_after_delivery_is_emailed()
    test_unheld_recovery_is_dropped()
    test_failed_delivery_keeps_hold_for_retry()
    test_held_outage_does_not_block_later_events()

    print("SERVICE_ALERT_CONFIRMATION=PASS")


if __name__ == "__main__":
    main()
