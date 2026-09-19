import importlib.util
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
        "devicemonitor_hostname_provider_framework_test",
        SOURCE,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.log = lambda message: None
    return module


MAC = "AA:BB:CC:DD:EE:FF"
MAC_LOWER = MAC.lower()
IP = "192.0.2.10"


def make_device(hostname="", mac=MAC, ip=IP, **extra):
    device = {"mac": mac, "ip": ip, "hostname": hostname}
    device.update(extra)
    return device


class RaisingProvider:
    """A provider that always fails, used to prove failure isolation."""

    name = "raising"

    def lookup(self, device):
        raise RuntimeError("provider exploded")


class SyntheticProvider:
    """A mock future provider (Pi-hole style) that participates without
    touching core selection code. Deliberately duck-typed (no base-class
    inheritance) to prove the framework accepts any object exposing
    ``name`` + ``lookup``."""

    name = "pihole"

    def __init__(self, mapping):
        self.mapping = mapping

    def lookup(self, device):
        return self.mapping.get(str(device.get("mac") or "").lower())


def test_normalization():
    module = load_module()
    normalize = module.normalize_hostname

    assert normalize("  printer.local  ") == "printer.local"
    assert normalize("printer.local.") == "printer.local"
    assert normalize("printer..") == "printer"
    assert normalize("  ") == ""
    assert normalize(None) == ""
    assert normalize("") == ""

    print("HOSTNAME_PROVIDER_NORMALIZATION=PASS")


def test_valid_and_no_result():
    module = load_module()
    resolve = module.resolve_hostname
    Mapping = module.MappingHostnameProvider

    providers = [
        Mapping("isc", {MAC_LOWER: "isc-name"}, key="mac", lower=True)
    ]
    hostname, source = resolve(make_device(hostname=""), providers)
    assert hostname == "isc-name"
    assert source == "isc"

    hostname, source = resolve(
        make_device(hostname="hostwatch-name"), [Mapping("isc", {})]
    )
    assert hostname == "hostwatch-name"
    assert source == "hostwatch"

    print("HOSTNAME_PROVIDER_VALID_AND_NO_RESULT=PASS")


def test_provider_failure_isolation():
    module = load_module()
    resolve = module.resolve_hostname
    Mapping = module.MappingHostnameProvider

    providers = [
        RaisingProvider(),
        Mapping("isc", {MAC_LOWER: "isc-name"}, key="mac", lower=True),
    ]
    hostname, source = resolve(make_device(hostname=""), providers)
    assert hostname == "isc-name"
    assert source == "isc"

    hostname, source = resolve(
        make_device(hostname="hostwatch-name"), [RaisingProvider()]
    )
    assert hostname == "hostwatch-name"
    assert source == "hostwatch"

    print("HOSTNAME_PROVIDER_FAILURE_ISOLATION=PASS")


def test_precedence_deterministic():
    module = load_module()
    build = module.build_hostname_providers
    resolve = module.resolve_hostname

    providers = build(
        {MAC_LOWER: "isc-name"},
        {MAC_LOWER: "kea-name"},
        {MAC_LOWER: "dnsmasq-name"},
        {IP: "adguard-name"},
    )

    hostname, source = resolve(make_device(hostname="hostwatch-name"), providers)
    assert hostname == "adguard-name"
    assert source == "adguard"

    for _ in range(3):
        again, again_source = resolve(
            make_device(hostname="hostwatch-name"), providers
        )
        assert (again, again_source) == ("adguard-name", "adguard")

    print("HOSTNAME_PROVIDER_PRECEDENCE=PASS")


def test_source_preserved():
    module = load_module()
    build = module.build_hostname_providers
    resolve = module.resolve_hostname

    empty = {}

    cases = [
        ({MAC_LOWER: "isc-name"}, empty, empty, empty, "isc"),
        (empty, {MAC_LOWER: "kea-name"}, empty, empty, "kea"),
        (empty, empty, {MAC_LOWER: "dnsmasq-name"}, empty, "dnsmasq"),
        (empty, empty, empty, {IP: "adguard-name"}, "adguard"),
    ]

    for isc, kea, dnsmasq, adguard, expected_source in cases:
        providers = build(isc, kea, dnsmasq, adguard)
        hostname, source = resolve(make_device(hostname=""), providers)
        assert source == expected_source
        assert hostname.endswith("-name")

    print("HOSTNAME_PROVIDER_SOURCE_PRESERVED=PASS")


def test_weaker_empty_does_not_erase():
    module = load_module()
    resolve = module.resolve_hostname
    Mapping = module.MappingHostnameProvider

    providers = [
        Mapping("adguard", {IP: "adguard-name"}, key="ip"),
        Mapping("kea", {}, key="mac", lower=True),
    ]
    hostname, source = resolve(make_device(hostname=""), providers)
    assert hostname == "adguard-name"
    assert source == "adguard"

    print("HOSTNAME_PROVIDER_NO_ERASE_ON_EMPTY=PASS")


def test_duplicate_candidate_idempotent():
    module = load_module()
    resolve = module.resolve_hostname
    Mapping = module.MappingHostnameProvider

    providers = [
        Mapping("kea", {MAC_LOWER: "same-name"}, key="mac", lower=True)
    ]
    first = resolve(make_device(hostname=""), providers)
    second = resolve(make_device(hostname=""), providers)
    assert first == second == ("same-name", "kea")

    print("HOSTNAME_PROVIDER_IDEMPOTENT=PASS")


def test_friendly_name_and_device_untouched():
    module = load_module()
    resolve = module.resolve_hostname
    Mapping = module.MappingHostnameProvider

    device = make_device(
        hostname="hostwatch-name", custom_hostname="User Friendly Name"
    )
    providers = [
        Mapping("kea", {MAC_LOWER: "kea-name"}, key="mac", lower=True)
    ]

    hostname, source = resolve(device, providers)

    assert hostname == "kea-name"
    assert source == "kea"
    assert device["custom_hostname"] == "User Friendly Name"
    assert device["hostname"] == "hostwatch-name"

    print("HOSTNAME_PROVIDER_FRIENDLY_NAME_UNTouched=PASS")


def test_no_providers_matches_baseline():
    module = load_module()
    resolve = module.resolve_hostname

    hostname, source = resolve(make_device(hostname="hostwatch-name"), [])
    assert hostname == "hostwatch-name"
    assert source == "hostwatch"

    hostname, source = resolve(make_device(hostname=""), [])
    assert hostname == ""
    assert source == ""

    print("HOSTNAME_PROVIDER_BASELINE=PASS")


def test_synthetic_provider_plugs_in():
    module = load_module()
    resolve = module.resolve_hostname
    Mapping = module.MappingHostnameProvider

    # A mock future provider participates purely via name + lookup, without
    # modifying resolve_hostname or any existing provider.
    providers = [
        Mapping("adguard", {}, key="ip"),
        SyntheticProvider({MAC_LOWER: "pihole-name"}),
        Mapping("kea", {MAC_LOWER: "kea-name"}, key="mac", lower=True),
    ]

    hostname, source = resolve(make_device(hostname=""), providers)
    assert hostname == "pihole-name"
    assert source == "pihole"

    print("HOSTNAME_PROVIDER_SYNTHETIC_EXTENSIBILITY=PASS")


def main():
    test_normalization()
    test_valid_and_no_result()
    test_provider_failure_isolation()
    test_precedence_deterministic()
    test_source_preserved()
    test_weaker_empty_does_not_erase()
    test_duplicate_candidate_idempotent()
    test_friendly_name_and_device_untouched()
    test_no_providers_matches_baseline()
    test_synthetic_provider_plugs_in()

    print("HOSTNAME_PROVIDER_FRAMEWORK_REGRESSION=PASS")


if __name__ == "__main__":
    main()
