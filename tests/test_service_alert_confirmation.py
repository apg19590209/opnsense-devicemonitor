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

MAC = "aa:bb:cc:dd:ee:10"
IP = "192.168.50.20"
DETAILS = "DNS|192.168.50.20|53|udp|LAN|dns_query"


def load_module():
    """Load scan_network.py with defaults.json redirected to the checkout.

    The module reads the *installed* defaults path at import time, which does not
    exist on a CI runner, so the read is redirected to the repository copy.
    """
    original_open = builtins.open

    def test_open(path, *args, **kwargs):
        if str(path).endswith('/models/OPNsense/DeviceMonitor/defaults.json'):
            path = DEFAULTS
        return original_open(path, *args, **kwargs)

    spec = importlib.util.spec_from_file_location(
        "devicemonitor_alert_confirmation_test",
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


def add_activity(
    module,
    event_type,
    old_value,
    new_value,
    when,
    mac=MAC,
    ip=IP,
    details=DETAILS,
):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        previous = conn.execute(
            '''
            SELECT status
            FROM device_services
            WHERE LOWER(COALESCE(mac, '')) = LOWER(?)
              AND ip = ?
            ''',
            (mac, ip),
        ).fetchone()
        conn.execute(
            '''
            UPDATE device_services
            SET status = ?
            WHERE LOWER(COALESCE(mac, '')) = LOWER(?)
              AND ip = ?
            ''',
            (new_value, mac, ip),
        )

        if previous is not None and previous[0] != new_value:
            activity_id = conn.execute(
                '''
                SELECT MAX(id)
                FROM device_activity_events
                WHERE LOWER(mac) = LOWER(?) AND details = ?
                ''',
                (mac, details),
            ).fetchone()[0]
        else:
            identity = conn.execute(
                '''
                SELECT id, alert_generation
                FROM device_services
                WHERE LOWER(COALESCE(mac, '')) = LOWER(?)
                  AND ip = ?
                ''',
                (mac, ip),
            ).fetchone()
            activity_id = conn.execute(
                """
                INSERT INTO device_activity_events (
                    mac, lifecycle_id, event_type, occurred_at,
                    old_value, new_value, details, service_id,
                    service_generation
                )
                VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mac,
                    event_type,
                    when,
                    old_value,
                    new_value,
                    details,
                    identity[0] if identity else None,
                    identity[1] if identity else None,
                ),
            ).lastrowid
        conn.commit()
        return activity_id


def add_hold(
    module,
    *,
    mac=MAC,
    ip=IP,
    service_type='DNS',
    port=53,
    protocol='udp',
    interface='LAN',
    detection_method='dns_query',
    notified=0,
    held_at='2020-01-01 00:00:00',
    include_identity=True,
    service_id=None,
    service_generation=None,
):
    event = {
        'event_type': 'SERVICE_UNAVAILABLE',
        'mac': mac,
        'service_type': service_type,
        'ip': ip,
        'port': port,
        'protocol': protocol,
        'interface': interface,
        'detection_method': detection_method,
        'occurred_at': held_at,
        'alert_eligible': True,
        'in_scope': True,
    }
    key = module.service_alert_key(event)

    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        if include_identity:
            if service_id is None or service_generation is None:
                current = conn.execute(
                    '''
                    SELECT id, alert_generation
                    FROM device_services
                    WHERE LOWER(COALESCE(mac, '')) = LOWER(?)
                      AND ip = ?
                    ''',
                    (mac, ip),
                ).fetchone()
                if current is None:
                    raise AssertionError(
                        "hold fixture has no current service identity"
                    )
                service_id = current[0]
                service_generation = current[1]

            event['service_id'] = service_id
            event['service_generation'] = service_generation

        conn.execute(
            '''
            INSERT OR REPLACE INTO service_alert_pending (
                service_key, mac, event_json, held_at, notified, notified_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (
                key,
                mac,
                json.dumps(event, sort_keys=True),
                held_at,
                notified,
                held_at if notified else None,
            ),
        )
        conn.commit()

    return key, event


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


def relabel_service(module, mac, status='unavailable'):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        module.upsert_device_service(
            conn,
            mac,
            IP,
            'LAN',
            'DNS',
            53,
            'udp',
            'dns_query',
            'verified',
            '2026-10-31 01:30:00',
            status=status,
            product='Test DNS',
            version='1.0',
        )
        conn.commit()


def read_hold_row(module, key):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        return conn.execute(
            '''
            SELECT service_key, notified, held_at
            FROM service_alert_pending
            WHERE service_key = ?
            ''',
            (key,),
        ).fetchone()


def service_mac(module):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        return conn.execute(
            'SELECT mac FROM device_services WHERE ip = ?',
            (IP,),
        ).fetchone()[0]


def current_identity(module):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        return conn.execute(
            '''
            SELECT id, alert_generation, status
            FROM device_services
            WHERE ip = ?
            ''',
            (IP,),
        ).fetchone()


def activity_event(module, event_id):
    with closing(sqlite3.connect(module.DB_FILE)) as conn:
        row = conn.execute(
            '''
            SELECT mac, lifecycle_id, event_type, occurred_at, old_value,
                   new_value, details, service_id, service_generation
            FROM device_activity_events
            WHERE id = ?
            ''',
            (event_id,),
        ).fetchone()

    details = str(row[6] or '').split('|', 5)
    details += [''] * (6 - len(details))
    service_type, ip, port, protocol, interface, detection_method = details

    return {
        'source': 'device_activity_events',
        'record_id': event_id,
        'event_type': row[2],
        'occurred_at': row[3],
        'mac': row[0],
        'lifecycle_id': row[1],
        'service_id': row[7],
        'service_generation': row[8],
        'service_type': service_type,
        'ip': ip,
        'port': int(port or 0),
        'protocol': protocol,
        'interface': interface,
        'detection_method': detection_method,
        'old_value': row[4],
        'new_value': row[5],
        'confidence': 'verified',
        'product': 'Test DNS',
        'version': '1.0',
        'alert_eligible': True,
        'in_scope': True,
    }


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


def test_deleted_endpoint_hold_is_dropped():
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

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            activity_count = conn.execute(
                "SELECT COUNT(*) FROM device_activity_events"
            ).fetchone()[0]
            conn.execute("DELETE FROM device_services WHERE ip = ?", (IP,))
            conn.commit()

        assert module.process_service_alerts(
            alert_config(), networks_fixture()
        ) is True

        assert sends == []
        assert read_holds(module) == []
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            assert conn.execute(
                "SELECT COUNT(*) FROM device_activity_events"
            ).fetchone()[0] == activity_count

    print("ALERT_DELETED_ENDPOINT_HOLD_DROPPED=PASS")


def test_stale_event_cannot_reinsert_after_relabel():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)

        add_activity(
            module,
            "SERVICE_UNAVAILABLE",
            "available",
            "unavailable",
            "2026-10-31 01:00:00",
        )
        module.process_service_alerts(alert_config(), networks_fixture())
        key, event = add_hold(module)
        relabel_service(module, "aa:bb:cc:dd:ee:20")

        assert read_hold_row(module, key) is None

        now = (
            datetime.strptime("2026-10-31 01:00:00", "%Y-%m-%d %H:%M:%S")
            + timedelta(seconds=module.SERVICE_ALERT_CONFIRM_SECONDS + 60)
        )
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            deliverable, held, suppressed = (
                module.apply_service_alert_confirmation(conn, [event], now)
            )

        assert deliverable == []
        assert held == []
        assert suppressed == [event]
        assert read_holds(module) == []

    print("ALERT_STALE_EVENT_REINSERT_BLOCKED=PASS")


def test_relabel_removes_only_old_undelivered_hold():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute(
                "UPDATE device_services SET status = 'unavailable' WHERE ip = ?",
                (IP,),
            )
            conn.commit()

        old_key, _ = add_hold(module)
        unrelated_key, _ = add_hold(
            module,
            mac="aa:bb:cc:dd:ee:30",
            ip="192.168.50.30",
            service_id=999,
            service_generation=1,
        )
        relabel_service(module, "aa:bb:cc:dd:ee:20")

        assert service_mac(module) == "aa:bb:cc:dd:ee:20"
        assert read_hold_row(module, old_key) is None
        assert read_hold_row(module, unrelated_key) is not None

    print("ALERT_A_TO_B_HOLD_RECONCILED=PASS")
    print("ALERT_UNRELATED_ENDPOINT_HOLD_RETAINED=PASS")


def test_relabel_removes_malformed_same_endpoint_hold():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute(
                "UPDATE device_services SET status = 'unavailable' WHERE ip = ?",
                (IP,),
            )
            conn.commit()

        key, _ = add_hold(module)
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute(
                '''
                UPDATE service_alert_pending
                SET event_json = '{'
                WHERE service_key = ?
                ''',
                (key,),
            )
            conn.commit()

        relabel_service(module, "aa:bb:cc:dd:ee:21")

        assert read_hold_row(module, key) is None

    print("ALERT_MALFORMED_SAME_ENDPOINT_HOLD_RECONCILED=PASS")


def test_unchanged_identity_preserves_hold_and_history():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute(
                "UPDATE device_services SET status = 'unavailable' WHERE ip = ?",
                (IP,),
            )
            activity_before = conn.execute(
                '''
                SELECT id, mac, event_type, occurred_at, old_value,
                       new_value, details
                FROM device_activity_events
                ORDER BY id
                '''
            ).fetchall()
            conn.commit()

        key, _ = add_hold(module, held_at="2026-10-31 01:00:00")
        relabel_service(module, MAC)

        assert read_hold_row(module, key) == (
            key,
            0,
            "2026-10-31 01:00:00",
        )
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            assert conn.execute(
                '''
                SELECT id, mac, event_type, occurred_at, old_value,
                       new_value, details
                FROM device_activity_events
                ORDER BY id
                '''
            ).fetchall() == activity_before

    print("ALERT_UNCHANGED_HOLD_RETAINED=PASS")
    print("ALERT_ACTIVITY_HISTORY_UNCHANGED=PASS")


def test_mac_empty_and_null_transitions():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute(
                "UPDATE device_services SET status = 'unavailable' WHERE ip = ?",
                (IP,),
            )
            conn.commit()

        key, _ = add_hold(module, held_at="2026-10-31 01:00:00")
        relabel_service(module, '')
        assert service_mac(module) == MAC
        assert read_hold_row(module, key) is not None

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute(
                "UPDATE device_services SET mac = NULL WHERE ip = ?",
                (IP,),
            )
            conn.commit()

        empty_key, _ = add_hold(module, mac='')
        relabel_service(module, "aa:bb:cc:dd:ee:40")

        assert service_mac(module) == "aa:bb:cc:dd:ee:40"
        assert read_hold_row(module, empty_key) is None

    print("ALERT_NONEMPTY_TO_EMPTY_IDENTITY_UNCHANGED=PASS")
    print("ALERT_EMPTY_TO_NONEMPTY_HOLD_RECONCILED=PASS")


def test_a_to_b_to_a_starts_fresh_hold():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)
        # CI runs unprivileged, so the real process lock is unavailable.
        sends = stub_delivery(module)

        add_activity(
            module,
            "SERVICE_UNAVAILABLE",
            "available",
            "unavailable",
            "2026-10-31 01:00:00",
        )
        module.process_service_alerts(alert_config(), networks_fixture())

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute(
                "UPDATE service_alert_pending SET held_at = ?",
                ("2020-01-01 00:00:00",),
            )
            conn.commit()

        relabel_service(module, "aa:bb:cc:dd:ee:20", status='available')
        relabel_service(module, MAC, status='available')
        add_activity(
            module,
            "SERVICE_UNAVAILABLE",
            "available",
            "unavailable",
            "2026-10-31 02:00:00",
        )
        assert module.process_service_alerts(
            alert_config(), networks_fixture()
        ) is True

        holds = read_holds(module)
        assert len(holds) == 1
        key = holds[0][0]
        row = read_hold_row(module, key)
        assert row[2] != "2020-01-01 00:00:00"
        service_id, generation, status = current_identity(module)
        assert (generation, status) == (3, "unavailable")
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            payload = conn.execute(
                "SELECT event_json FROM service_alert_pending "
                "WHERE service_key = ?",
                (key,),
            ).fetchone()[0]
        held_event = json.loads(payload)
        assert (
            held_event["service_id"],
            held_event["service_generation"],
        ) == (service_id, generation)
        assert sends == []

    print("ALERT_A_TO_B_TO_A_STARTS_FRESH_HOLD=PASS")


def test_a_to_b_to_a_old_events_cannot_displace_current_hold():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)
        stub_delivery(module)

        old_outage_id = add_activity(
            module,
            "SERVICE_UNAVAILABLE",
            "available",
            "unavailable",
            "2026-10-31 01:00:00",
        )
        old_outage = activity_event(module, old_outage_id)
        module.process_service_alerts(alert_config(), networks_fixture())

        relabel_service(module, "aa:bb:cc:dd:ee:20", status='available')
        relabel_service(module, MAC, status='unavailable')
        module.process_service_alerts(alert_config(), networks_fixture())

        service_id, generation, _ = current_identity(module)
        assert (service_id, generation) == (
            old_outage['service_id'],
            3,
        )

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            current_payload = conn.execute(
                "SELECT event_json FROM service_alert_pending"
            ).fetchone()[0]
        current_event = json.loads(current_payload)
        current_key = module.service_alert_key(current_event)
        held_at = read_hold_row(module, current_key)[2]

        old_recovery = dict(old_outage)
        old_recovery.update({
            'record_id': old_outage_id + 1000,
            'event_type': 'SERVICE_AVAILABLE',
            'old_value': 'unavailable',
            'new_value': 'available',
        })

        now = datetime.now()
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            deliverable, held, suppressed = (
                module.apply_service_alert_confirmation(
                    conn,
                    [old_outage, old_recovery],
                    now,
                )
            )

        assert deliverable == []
        assert held == []
        assert suppressed == [old_outage, old_recovery]
        assert read_hold_row(module, current_key)[2] == held_at

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            deliverable, held, suppressed = (
                module.apply_service_alert_confirmation(
                    conn,
                    [old_outage, current_event],
                    now,
                )
            )

        assert deliverable == []
        assert held == [current_event]
        assert suppressed == [old_outage]
        assert read_hold_row(module, current_key)[2] == held_at

    print("A_TO_B_TO_A_OLD_OUTAGE_REJECTED=PASS")
    print("A_TO_B_TO_A_OLD_RECOVERY_REJECTED=PASS")
    print("STALE_BATCH_EVENT_CANNOT_DISPLACE_CURRENT=PASS")


def test_delete_recreate_same_endpoint_rejects_old_generation_events():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)
        stub_delivery(module)

        old_outage_id = add_activity(
            module,
            "SERVICE_UNAVAILABLE",
            "available",
            "unavailable",
            "2026-10-31 01:00:00",
        )
        old_outage = activity_event(module, old_outage_id)
        old_recovery = dict(old_outage)
        old_recovery.update({
            'record_id': old_outage_id + 1000,
            'event_type': 'SERVICE_AVAILABLE',
            'old_value': 'unavailable',
            'new_value': 'available',
        })
        module.process_service_alerts(alert_config(), networks_fixture())

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute("DELETE FROM device_services WHERE ip = ?", (IP,))
            conn.commit()

        relabel_service(module, MAC)

        new_service_id, new_generation, new_status = current_identity(module)
        assert new_service_id != old_outage['service_id']
        assert new_generation == 1
        assert new_status == 'unavailable'

        # The upsert reconciles the old lifetime's undelivered hold even though
        # endpoint, MAC and generation text are identical to the replacement.
        assert read_holds(module) == []
        current_key, current_event = add_hold(module)

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            deliverable, held, suppressed = (
                module.apply_service_alert_confirmation(
                    conn,
                    [old_outage, old_recovery],
                    datetime.now() + timedelta(
                        seconds=module.SERVICE_ALERT_CONFIRM_SECONDS + 60
                    ),
                )
            )

        assert deliverable == []
        assert held == []
        assert suppressed == [old_outage, old_recovery]
        assert read_hold_row(module, current_key) is not None
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            payload = conn.execute(
                "SELECT event_json FROM service_alert_pending"
            ).fetchone()[0]
        assert json.loads(payload)['service_id'] == new_service_id

    print("DELETE_RECREATE_SAME_MAC_OLD_OUTAGE_REJECTED=PASS")
    print("DELETE_RECREATE_SAME_MAC_OLD_RECOVERY_REJECTED=PASS")


def test_simultaneous_mac_and_status_change_captures_new_generation():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)
        old_service_id, old_generation, old_status = current_identity(module)

        relabel_service(module, "aa:bb:cc:dd:ee:60")
        service_id, generation, status = current_identity(module)

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            event = conn.execute(
                '''
                SELECT mac, event_type, service_id, service_generation
                FROM device_activity_events
                ORDER BY id DESC
                LIMIT 1
                '''
            ).fetchone()

        assert service_id == old_service_id
        assert old_generation == 1
        assert generation == old_generation + 1
        assert old_status == 'available'
        assert status == 'unavailable'
        assert event == (
            "aa:bb:cc:dd:ee:60",
            "SERVICE_UNAVAILABLE",
            service_id,
            generation,
        )

    print("SIMULTANEOUS_MAC_STATUS_CAPTURES_GENERATION=PASS")


def test_legacy_and_malformed_undelivered_holds_are_suppressed():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)
        stub_delivery(module)
        service_id, generation, _ = current_identity(module)

        add_activity(
            module,
            "SERVICE_UNAVAILABLE",
            "available",
            "unavailable",
            "2026-10-31 01:00:00",
        )
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            history_before = conn.execute(
                "SELECT COUNT(*) FROM device_activity_events"
            ).fetchone()[0]
            conn.execute(
                '''
                UPDATE service_alert_state
                SET last_service_id = (
                        SELECT COALESCE(MAX(id), 0) FROM device_services
                    ),
                    last_activity_event_id = (
                        SELECT COALESCE(MAX(id), 0)
                        FROM device_activity_events
                    )
                WHERE id = 1
                '''
            )
            conn.commit()

        add_hold(
            module,
            mac="aa:bb:cc:dd:ee:70",
            ip="192.168.50.70",
            include_identity=False,
        )
        add_hold(
            module,
            mac="aa:bb:cc:dd:ee:71",
            ip="192.168.50.71",
            service_id=service_id,
            service_generation=0,
        )

        partial_key, partial_event = add_hold(module, mac=MAC)
        del partial_event['service_generation']
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute(
                '''
                UPDATE service_alert_pending
                SET event_json = ?
                WHERE service_key = ?
                ''',
                (json.dumps(partial_event), partial_key),
            )
            conn.execute(
                '''
                INSERT INTO service_alert_pending (
                    service_key, mac, event_json, held_at, notified
                )
                VALUES ('malformed-json', '', '{', ?, 0)
                ''',
                ("2020-01-01 00:00:00",),
            )
            conn.commit()

        legacy_delivered_key, _ = add_hold(
            module,
            mac="aa:bb:cc:dd:ee:72",
            ip="192.168.50.72",
            notified=1,
            include_identity=False,
        )

        assert module.process_service_alerts(
            alert_config(),
            networks_fixture(),
        ) is True

        assert read_hold_row(module, legacy_delivered_key) is not None
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            remaining = conn.execute(
                "SELECT service_key FROM service_alert_pending"
            ).fetchall()
            history_after = conn.execute(
                "SELECT COUNT(*) FROM device_activity_events"
            ).fetchone()[0]

        assert remaining == [(legacy_delivered_key,)]
        assert history_after == history_before
        assert generation == 1

    print("LEGACY_UNDELIVERED_HOLD_SUPPRESSED=PASS")
    print("MALFORMED_UNDELIVERED_HOLDS_SUPPRESSED=PASS")
    print("LEGACY_DELIVERED_HOLD_RETAINED=PASS")
    print("LEGACY_HOLD_SUPPRESSION_PRESERVES_HISTORY=PASS")


def test_missing_partial_and_malformed_event_pairs_fail_closed():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)
        service_id, generation, _ = current_identity(module)
        base = {
            'event_type': 'SERVICE_UNAVAILABLE',
            'mac': MAC,
            'service_type': 'DNS',
            'ip': IP,
            'port': 53,
            'protocol': 'udp',
            'interface': 'LAN',
            'detection_method': 'dns_query',
            'old_value': 'available',
            'new_value': 'unavailable',
            'alert_eligible': True,
            'in_scope': True,
        }
        missing = dict(base, record_id=1001)
        partial = dict(base, record_id=1002, service_id=service_id)
        malformed = dict(
            base,
            record_id=1003,
            service_id=service_id,
            service_generation='not-a-generation',
        )
        zero = dict(
            base,
            record_id=1004,
            service_id=0,
            service_generation=generation,
        )

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            deliverable, held, suppressed = (
                module.apply_service_alert_confirmation(
                    conn,
                    [missing, partial, malformed, zero],
                    datetime.now(),
                )
            )

        assert deliverable == []
        assert held == []
        assert suppressed == [missing, partial, malformed, zero]
        assert read_holds(module) == []

    print("MISSING_PAIR_EVENT_NOT_HELD_OR_RELEASED=PASS")
    print("PARTIAL_AND_MALFORMED_EVENT_PAIRS_REJECTED=PASS")


def test_delivered_hold_is_retained_on_relabel():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute(
                "UPDATE device_services SET status = 'unavailable' WHERE ip = ?",
                (IP,),
            )
            conn.commit()

        key, _ = add_hold(
            module,
            notified=1,
            held_at="2026-10-31 01:00:00",
        )
        relabel_service(module, "aa:bb:cc:dd:ee:50")

        assert read_hold_row(module, key) is not None
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            reminders = module.collect_service_alert_reminders(
                conn,
                {'email_reminder_service': 1},
                datetime.now(),
            )

        assert len(reminders) == 1
        assert reminders[0]['service_generation'] == 1

    print("ALERT_DELIVERED_ROW_RETAINED_ON_RELABEL=PASS")
    print("ALERT_DELIVERED_REMINDER_POLICY_UNCHANGED=PASS")


def test_relabel_failure_rolls_back_atomically():
    module = load_module()

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        seed(module)

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute(
                "UPDATE device_services SET status = 'unavailable' WHERE ip = ?",
                (IP,),
            )
            conn.commit()

        key, _ = add_hold(module)
        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            conn.execute(
                '''
                CREATE TRIGGER fail_pending_delete
                BEFORE DELETE ON service_alert_pending
                BEGIN
                    SELECT RAISE(ABORT, 'injected pending delete failure');
                END
                '''
            )
            conn.commit()

        with closing(sqlite3.connect(module.DB_FILE)) as conn:
            try:
                module.upsert_device_service(
                    conn,
                    "aa:bb:cc:dd:ee:20",
                    IP,
                    'LAN',
                    'DNS',
                    53,
                    'udp',
                    'dns_query',
                    'verified',
                    '2026-10-31 01:30:00',
                    status='unavailable',
                )
            except sqlite3.IntegrityError:
                conn.rollback()
            else:
                raise AssertionError("injected reconciliation failure was ignored")

        assert service_mac(module) == MAC
        assert read_hold_row(module, key) is not None

    print("ALERT_RECONCILIATION_FAILURE_ROLLS_BACK=PASS")


def test_two_connection_relabel_validation():
    module = load_module()

    for journal_mode in ('DELETE', 'WAL'):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            module.DB_FILE = str(Path(tmp) / "devices.db")
            seed(module)

            with closing(sqlite3.connect(module.DB_FILE)) as conn:
                conn.execute(
                    '''
                    UPDATE device_services
                    SET status = 'unavailable'
                    WHERE ip = ?
                    ''',
                    (IP,),
                )
                conn.execute(
                    'PRAGMA journal_mode=' + journal_mode
                )
                conn.commit()

            key, event = add_hold(module)
            writer = sqlite3.connect(module.DB_FILE, timeout=1)
            reader = sqlite3.connect(module.DB_FILE, timeout=0.05)
            try:
                writer.execute('BEGIN IMMEDIATE')
                module.upsert_device_service(
                    writer,
                    "aa:bb:cc:dd:ee:20",
                    IP,
                    'LAN',
                    'DNS',
                    53,
                    'udp',
                    'dns_query',
                    'verified',
                    '2026-10-31 01:30:00',
                    status='unavailable',
                )

                try:
                    reader.execute('BEGIN IMMEDIATE')
                except sqlite3.OperationalError:
                    locked = True
                else:
                    locked = False
                    reader.rollback()

                assert locked
                writer.commit()

                reader.execute('BEGIN IMMEDIATE')
                expired = module.collect_expired_service_alert_holds(
                    reader,
                    datetime.now()
                    + timedelta(
                        seconds=module.SERVICE_ALERT_CONFIRM_SECONDS + 60
                    ),
                )
                deliverable, held, suppressed = (
                    module.apply_service_alert_confirmation(
                        reader,
                        [event],
                        datetime.now()
                        + timedelta(
                            seconds=module.SERVICE_ALERT_CONFIRM_SECONDS + 60
                        ),
                    )
                )
            finally:
                writer.close()
                reader.close()

            assert expired == []
            assert deliverable == []
            assert held == []
            assert suppressed == [event]
            assert read_hold_row(module, key) is None

    print("ALERT_RELABEL_DELETE_INTERLEAVING=PASS")
    print("ALERT_RELABEL_WAL_INTERLEAVING=PASS")


def main():
    test_flap_is_silent()
    test_sustained_outage_is_delivered_once()
    test_recovery_after_delivery_is_emailed()
    test_unheld_recovery_is_dropped()
    test_failed_delivery_keeps_hold_for_retry()
    test_held_outage_does_not_block_later_events()
    test_deleted_endpoint_hold_is_dropped()
    test_stale_event_cannot_reinsert_after_relabel()
    test_relabel_removes_only_old_undelivered_hold()
    test_relabel_removes_malformed_same_endpoint_hold()
    test_unchanged_identity_preserves_hold_and_history()
    test_mac_empty_and_null_transitions()
    test_a_to_b_to_a_starts_fresh_hold()
    test_a_to_b_to_a_old_events_cannot_displace_current_hold()
    test_delete_recreate_same_endpoint_rejects_old_generation_events()
    test_simultaneous_mac_and_status_change_captures_new_generation()
    test_legacy_and_malformed_undelivered_holds_are_suppressed()
    test_missing_partial_and_malformed_event_pairs_fail_closed()
    test_delivered_hold_is_retained_on_relabel()
    test_relabel_failure_rolls_back_atomically()
    test_two_connection_relabel_validation()

    print("SERVICE_ALERT_CONFIRMATION=PASS")


if __name__ == "__main__":
    main()
