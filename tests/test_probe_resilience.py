"""Service probes must not read one lost packet as an outage.

v2.11 service-liveness noise fix (O1). Availability was decided by a single
probe attempt per discovery run, with timeouts below the initial TCP SYN
retransmit timer (web 0.6 s, SSH/NTP 0.8 s, DNS 1.5 s) and up to 32 concurrent
probes. A single dropped packet therefore produced a "service unavailable"
event, a matching "service recovered" event on the next hourly run, and two
emails for an outage that never happened. On the testbed the recorded
down/up pairs lasted exactly one discovery interval, 7 of 8 times.

These checks pin the replacement behaviour:

  * a transient SSH/HTTP failure on the first attempt is retried and does not
    become a verified negative;
  * retries are bounded by `SERVICE_PROBE_ATTEMPTS`;
  * an unanswered DNS query is retransmitted with the *same* transaction ID,
    so the reply to either transmission still matches the candidate;
  * the tuning constants stay above the SYN retransmit timer and the per
    protocol worker caps stay small.

The probes are driven with fake sockets, so no network traffic is generated.
"""
import builtins
import importlib.util
import inspect
import ipaddress
import socket
import sqlite3
import tempfile
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
        "devicemonitor_probe_resilience_test",
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
        "name": "opt2",
        "description": "DMTEST",
        "device": "vlan0.60",
        "ip": "198.51.100.1",
        "subnet": "24",
        "network": ipaddress.ip_network("198.51.100.0/24"),
    }]


class FakeSocket:
    """Minimal SSH/banner socket."""

    def __init__(self, banner=b"SSH-2.0-OpenSSH_9.9\r\n"):
        self.banner = banner
        self.sent = []
        self.closed = False

    def settimeout(self, value):
        pass

    def recv(self, size):
        if self.banner:
            data, self.banner = self.banner, b""
            return data
        return b""

    def sendall(self, data):
        self.sent.append(bytes(data))

    def close(self):
        self.closed = True


class FakeWebSocket:
    """Minimal HTTP socket that answers with a fixed response header."""

    def __init__(self, response):
        self.chunks = [response, b""]
        self.closed = False

    def settimeout(self, value):
        pass

    def sendall(self, data):
        pass

    def recv(self, size):
        if self.chunks:
            return self.chunks.pop(0)
        return b""

    def close(self):
        self.closed = True


class FakeDatagramSocket:
    """Minimal UDP socket that records sends and never receives."""

    def __init__(self):
        self.sent = []
        self.closed = False

    def setblocking(self, flag):
        pass

    def settimeout(self, value):
        pass

    def sendto(self, payload, address):
        self.sent.append((bytes(payload), address))

    def recvfrom(self, size):
        raise socket.timeout("simulated silence")

    def close(self):
        self.closed = True


def test_probe_tuning_constants():
    module = load_module()

    assert module.SERVICE_PROBE_ATTEMPTS >= 2
    assert module.SERVICE_PROBE_RETRY_DELAY > 0

    for name in ("dns", "ntp", "ssh", "web"):
        assert module.SERVICE_PROBE_TIMEOUTS[name] >= 2.0, name

    for name, workers in module.SERVICE_PROBE_WORKERS.items():
        assert 1 <= workers <= 16, (name, workers)

    for probe, name in (
        (module.discover_dns_servers, "dns"),
        (module._probe_ntp_service, "ntp"),
        (module._probe_ssh_service, "ssh"),
        (module._probe_web_service, "web"),
    ):
        default = inspect.signature(probe).parameters["timeout"].default
        assert default == module.SERVICE_PROBE_TIMEOUTS[name], (name, default)

    print("PROBE_TUNING_CONSTANTS=PASS")


def test_ssh_probe_retries_transient_failure():
    module = load_module()

    attempts = []
    good = FakeSocket()

    def create_connection(target, timeout=None):
        attempts.append((target, timeout))

        if len(attempts) == 1:
            raise OSError("simulated transient connect failure")

        return good

    module.socket.create_connection = create_connection
    module.time.sleep = lambda seconds: None

    result = module._probe_ssh_service(("198.51.100.10", 22))

    assert result == {
        "product": "SSH",
        "version": "OpenSSH_9.9",
    }, result
    assert len(attempts) == 2, attempts
    assert good.closed is True

    print("PROBE_SSH_RETRY_RECOVERS=PASS")


def test_ssh_probe_retries_are_bounded():
    module = load_module()

    attempts = []

    def create_connection(target, timeout=None):
        attempts.append(target)
        raise OSError("simulated persistent connect failure")

    module.socket.create_connection = create_connection
    module.time.sleep = lambda seconds: None

    result = module._probe_ssh_service(("198.51.100.11", 22))

    assert result is None, result
    assert len(attempts) == module.SERVICE_PROBE_ATTEMPTS, attempts

    print("PROBE_RETRY_BOUNDED=PASS")



def test_web_probe_retries_transient_failure():
    module = load_module()

    attempts = []
    good = FakeWebSocket(
        b"HTTP/1.1 200 OK\r\nServer: lighttpd/1.4.59\r\n\r\n"
    )

    def create_connection(target, timeout=None):
        attempts.append(timeout)

        if len(attempts) == 1:
            raise OSError("simulated dropped SYN")

        return good

    module.socket.create_connection = create_connection
    module.time.sleep = lambda seconds: None

    result = module._probe_web_service(("198.51.100.12", 80, "http"))

    assert result == {
        "product": "lighttpd",
        "version": "1.4.59",
    }, result
    assert len(attempts) == 2, attempts
    assert good.closed is True

    print("PROBE_WEB_RETRY_RECOVERS=PASS")


def test_dns_probe_retransmits_identical_query():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.init_db = lambda: None

        with sqlite3.connect(module.DB_FILE) as conn:
            conn.execute(
                '''
                CREATE TABLE devices (
                    mac TEXT,
                    ip TEXT,
                    vlan TEXT,
                    is_active INTEGER,
                    last_seen TEXT
                )
                '''
            )
            conn.execute(
                '''
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
                    confidence TEXT NOT NULL
                )
                '''
            )
            conn.execute(
                "INSERT INTO devices VALUES (?, ?, ?, ?, ?)",
                (
                    "aa:bb:cc:dd:ee:01",
                    "198.51.100.10",
                    "VLAN60",
                    1,
                    "2026-10-31 10:00:00"
                ),
            )
            conn.execute(
                '''
                INSERT INTO device_services (
                    mac, ip, interface, service_type, port, protocol,
                    status, detection_method, confidence
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    "aa:bb:cc:dd:ee:01",
                    "198.51.100.10",
                    "VLAN60",
                    "DNS",
                    53,
                    "udp",
                    "available",
                    "dns_query",
                    "verified"
                ),
            )
            conn.commit()

        fake = FakeDatagramSocket()

        module.socket.socket = lambda *args, **kwargs: fake
        module.select.select = lambda *args, **kwargs: ([], [], [])
        module.time.sleep = lambda seconds: None

        result = module.discover_dns_servers(
            networks_fixture(),
            timeout=0.01
        )

        assert result == [], result
        assert len(fake.sent) == module.SERVICE_PROBE_ATTEMPTS, fake.sent

        payloads = [payload for payload, _address in fake.sent]
        assert payloads[0] == payloads[1], payloads
        assert fake.sent[0][1] == ("198.51.100.10", 53), fake.sent

        with sqlite3.connect(module.DB_FILE) as conn:
            status = conn.execute(
                "SELECT status FROM device_services WHERE ip = ?",
                ("198.51.100.10",),
            ).fetchone()[0]

        assert status == "unavailable", status

    print("PROBE_DNS_RETRANSMITS_SAME_TXID=PASS")


def main():
    test_probe_tuning_constants()
    test_ssh_probe_retries_transient_failure()
    test_ssh_probe_retries_are_bounded()
    test_web_probe_retries_transient_failure()
    test_dns_probe_retransmits_identical_query()

    print("PROBE_RESILIENCE=PASS")


if __name__ == "__main__":
    main()
