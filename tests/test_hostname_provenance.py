import importlib.util
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


def load_module():
    spec = importlib.util.spec_from_file_location(
        "devicemonitor_hostname_provenance_test",
        SOURCE,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.log = lambda message: None
    return module


def make_device(hostname="hostwatch-name"):
    return {
        "mac": "AA:BB:CC:DD:EE:FF",
        "ip": "192.0.2.10",
        "hostname": hostname,
    }


def apply(module, *, hostwatch="hostwatch-name",
          isc=None, kea=None, dnsmasq=None, adguard=None):
    mac = "aa:bb:cc:dd:ee:ff"
    ip = "192.0.2.10"

    device = make_device(hostwatch)

    module.apply_hostname_provenance(
        device,
        {mac: isc} if isc is not None else {},
        {mac: kea} if kea is not None else {},
        {mac: dnsmasq} if dnsmasq is not None else {},
        {ip: adguard} if adguard is not None else {},
    )

    return device


def test_hostname_precedence():
    module = load_module()

    cases = [
        (
            {},
            "hostwatch-name",
            "hostwatch",
        ),
        (
            {"isc": "isc-name"},
            "isc-name",
            "isc",
        ),
        (
            {"isc": "isc-name", "kea": "kea-name"},
            "kea-name",
            "kea",
        ),
        (
            {
                "isc": "isc-name",
                "kea": "kea-name",
                "dnsmasq": "dnsmasq-name",
            },
            "dnsmasq-name",
            "dnsmasq",
        ),
        (
            {
                "isc": "isc-name",
                "kea": "kea-name",
                "dnsmasq": "dnsmasq-name",
                "adguard": "adguard-name",
            },
            "adguard-name",
            "adguard",
        ),
    ]

    for sources, expected_hostname, expected_source in cases:
        device = apply(module, **sources)
        assert device["hostname"] == expected_hostname
        assert device["hostname_source"] == expected_source

    print("HOSTNAME_PROVENANCE_PRECEDENCE=PASS")


def test_hostwatch_hostname_is_not_modified():
    module = load_module()

    original = '  hostwatch-name  '
    device = apply(module, hostwatch=original)

    assert device['hostname'] == original
    assert device['hostname_source'] == 'hostwatch'

    print('HOSTNAME_PROVENANCE_HOSTWATCH_PRESERVED=PASS')


def test_blank_hostname_has_blank_source():
    module = load_module()

    device = apply(module, hostwatch="")

    assert device["hostname"] == ""
    assert device["hostname_source"] == ""

    print("HOSTNAME_PROVENANCE_BLANK=PASS")


def test_existing_database_migration():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        module.DB_FILE = str(Path(tmp) / "devices.db")
        module.LOG_FILE = str(Path(tmp) / "devicemonitor.log")

        with sqlite3.connect(module.DB_FILE) as conn:
            conn.execute(
                """
                CREATE TABLE devices (
                    mac TEXT PRIMARY KEY,
                    ip TEXT,
                    hostname TEXT,
                    vendor TEXT,
                    vlan TEXT,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    notified INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 0,
                    notification_pending INTEGER DEFAULT 0
                )
                """
            )

        module.init_db()

        with sqlite3.connect(module.DB_FILE) as conn:
            columns = {
                row[1]: row
                for row in conn.execute("PRAGMA table_info(devices)")
            }

        assert "hostname_source" in columns
        assert columns["hostname_source"][4] == "''"

    print("HOSTNAME_PROVENANCE_SCHEMA_MIGRATION=PASS")


def test_persistence_wiring():
    source = " ".join(
        SOURCE.read_text(encoding="utf-8").split()
    )

    assert (
        "SET ip = ?, hostname = ?, hostname_source = ?, vendor = ?, vlan = ?"
        in source
    )
    assert (
        "(mac, ip, hostname, hostname_source, vendor, vlan, first_seen, last_seen,"
        in source
    )
    assert (
        "device['hostname'], device['hostname_source']"
        in source
    )

    print("HOSTNAME_PROVENANCE_PERSISTENCE=PASS")


def main():
    test_hostname_precedence()
    test_hostwatch_hostname_is_not_modified()
    test_blank_hostname_has_blank_source()
    test_existing_database_migration()
    test_persistence_wiring()

    print("HOSTNAME_PROVENANCE_REGRESSION=PASS")


if __name__ == "__main__":
    main()
