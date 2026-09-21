import importlib.util
import inspect
import json
import os
import tempfile
import xml.etree.ElementTree as ET
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

MAC = "AA:BB:CC:DD:EE:FF"
MAC_LOWER = MAC.lower()
IP = "192.0.2.10"


def load_module(log=None):
    spec = importlib.util.spec_from_file_location(
        "devicemonitor_unbound_test", SOURCE
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.log = log if log is not None else (lambda message: None)
    return module


def build_config(hosts=None, aliases=None, has_unbound=True):
    root = ET.Element("opnsense")
    if has_unbound:
        opnsense = ET.SubElement(root, "OPNsense")
        unbound = ET.SubElement(opnsense, "Unbound")
        if hosts is not None:
            hosts_el = ET.SubElement(unbound, "hosts")
            for h in hosts:
                host = ET.SubElement(hosts_el, "host")
                if h.get("uuid"):
                    host.set("uuid", h["uuid"])
                for key, val in h.items():
                    if key == "uuid":
                        continue
                    ET.SubElement(host, key).text = str(val)
        if aliases is not None:
            aliases_el = ET.SubElement(unbound, "aliases")
            for a in aliases:
                alias = ET.SubElement(aliases_el, "alias")
                for key, val in a.items():
                    ET.SubElement(alias, key).text = str(val)
    return ET.ElementTree(root)


def patch_config(module, hosts=None, aliases=None, has_unbound=True):
    module.ET.parse = lambda path: build_config(hosts, aliases, has_unbound)


def test_host_override_returns_hostname():
    module = load_module()
    patch_config(
        module,
        hosts=[
            {"enabled": "1", "rr": "A", "server": IP, "hostname": "  printer.  "},
        ],
    )
    mapping = module.get_unbound_hostnames()
    assert mapping == {IP: "printer"}

    print("UNBOUND_HOST_OVERRIDE=PASS")


def test_no_records_returns_empty():
    module = load_module()
    patch_config(module, hosts=[])
    assert module.get_unbound_hostnames() == {}

    patch_config(module, has_unbound=False)
    assert module.get_unbound_hostnames() == {}

    print("UNBOUND_NO_RECORDS=PASS")


def test_malformed_and_missing_source():
    module = load_module()

    def failing_parse(path):
        raise OSError("no config")

    module.ET.parse = failing_parse
    assert module.get_unbound_hostnames() == {}

    print("UNBOUND_MISSING_SOURCE=PASS")


def test_duplicate_records_deterministic():
    module = load_module()
    patch_config(
        module,
        hosts=[
            {"rr": "A", "server": IP, "hostname": "first"},
            {"rr": "A", "server": IP, "hostname": "second"},
        ],
    )
    # Later override wins deterministically for a duplicate IP.
    assert module.get_unbound_hostnames() == {IP: "second"}

    print("UNBOUND_DUPLICATE_DETERMINISTIC=PASS")


def test_non_a_and_disabled_skipped():
    module = load_module()
    patch_config(
        module,
        hosts=[
            {"enabled": "0", "rr": "A", "server": IP, "hostname": "disabled"},
            {"rr": "AAAA", "server": "2001:db8::1", "hostname": "v6"},
        ],
    )
    assert module.get_unbound_hostnames() == {}

    print("UNBOUND_SKIP_NON_A_DISABLED=PASS")


def test_alias_secondary_name():
    module = load_module()

    # An alias never overrides a specific primary override name.
    patch_config(
        module,
        hosts=[{"uuid": "host-uuid-1", "rr": "A", "server": IP, "hostname": "primary"}],
        aliases=[{"enabled": "1", "host": "host-uuid-1", "hostname": "alias-name"}],
    )
    assert module.get_unbound_hostnames() == {IP: "primary"}

    # A wildcard override has no specific name; the alias supplies it.
    patch_config(
        module,
        hosts=[{"uuid": "host-uuid-1", "rr": "A", "server": IP, "hostname": "*"}],
        aliases=[{"enabled": "1", "host": "host-uuid-1", "hostname": "alias-name"}],
    )
    assert module.get_unbound_hostnames() == {IP: "alias-name"}

    print("UNBOUND_ALIAS=PASS")


def test_source_is_unbound():
    module = load_module()
    build = module.build_hostname_providers
    resolve = module.resolve_hostname

    providers = build({}, {}, {}, {}, {}, {IP: "unbound-name"})
    hostname, source = resolve({"mac": MAC, "ip": IP, "hostname": ""}, providers)
    assert hostname == "unbound-name"
    assert source == "unbound"

    print("UNBOUND_SOURCE=PASS")


def test_precedence_against_all_providers():
    module = load_module()
    build = module.build_hostname_providers
    resolve = module.resolve_hostname

    def winner(isc=None, kea=None, dnsmasq=None, adguard=None, pihole=None,
               unbound=None, hostwatch="hostwatch-name"):
        providers = build(
            {MAC_LOWER: isc} if isc else {},
            {MAC_LOWER: kea} if kea else {},
            {MAC_LOWER: dnsmasq} if dnsmasq else {},
            {IP: adguard} if adguard else {},
            {MAC_LOWER: pihole} if pihole else {},
            {IP: unbound} if unbound else {},
        )
        return resolve({"mac": MAC, "ip": IP, "hostname": hostwatch}, providers)

    # Unbound is stronger than Pi-hole and Hostwatch.
    assert winner(unbound="u", pihole="p") == ("u", "unbound")
    assert winner(unbound="u") == ("u", "unbound")

    # Unbound is weaker than ISC, Kea, Dnsmasq and AdGuard.
    assert winner(unbound="u", isc="i") == ("i", "isc")
    assert winner(unbound="u", kea="k") == ("k", "kea")
    assert winner(unbound="u", dnsmasq="d") == ("d", "dnsmasq")
    assert winner(unbound="u", adguard="a") == ("a", "adguard")

    print("UNBOUND_PRECEDENCE=PASS")


def test_retained_hostname_not_erased():
    module = load_module()
    build = module.build_hostname_providers
    resolve = module.resolve_hostname

    providers = build({}, {}, {}, {}, {}, {})  # unbound empty
    hostname, source = resolve(
        {"mac": MAC, "ip": IP, "hostname": "retained"}, providers
    )
    assert hostname == "retained"
    assert source == "hostwatch"

    print("UNBOUND_NO_ERASE=PASS")


def test_friendly_name_untouched():
    module = load_module()
    build = module.build_hostname_providers
    resolve = module.resolve_hostname

    device = {"mac": MAC, "ip": IP, "hostname": "", "custom_hostname": "Friend"}
    providers = build({}, {}, {}, {}, {}, {IP: "unbound-name"})
    hostname, source = resolve(device, providers)

    assert hostname == "unbound-name"
    assert source == "unbound"
    assert device["custom_hostname"] == "Friend"

    print("UNBOUND_FRIENDLY_NAME=PASS")


def test_duplicate_idempotent():
    module = load_module()
    build = module.build_hostname_providers
    resolve = module.resolve_hostname

    providers = build({}, {}, {}, {}, {}, {IP: "same-name"})
    first = resolve({"mac": MAC, "ip": IP, "hostname": ""}, providers)
    second = resolve({"mac": MAC, "ip": IP, "hostname": ""}, providers)
    assert first == second == ("same-name", "unbound")

    print("UNBOUND_IDEMPOTENT=PASS")


def test_resolve_hostname_has_no_unbound_branch():
    module = load_module()
    source = inspect.getsource(module.resolve_hostname).lower()
    assert "unbound" not in source

    print("UNBOUND_GENERIC_RESOLVER=PASS")


def test_apply_wrapper_accepts_unbound():
    module = load_module()

    device = {"mac": MAC, "ip": IP, "hostname": ""}
    module.apply_hostname_provenance(
        device, {}, {}, {}, {}, {}, {IP: "unbound-name"}
    )
    assert device["hostname"] == "unbound-name"
    assert device["hostname_source"] == "unbound"

    print("UNBOUND_APPLY_WRAPPER=PASS")


def test_unbound_defaults_off_when_key_absent():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        cfg = os.path.join(tmp, "config.json")
        with open(cfg, "w", encoding="utf-8") as handle:
            json.dump({"enabled": "0"}, handle)

        module.CONFIG_FILE = cfg
        config = module.load_config()

        assert config["unbound_enabled"] is False
        assert config["pihole_enabled"] is False

    print("UNBOUND_DEFAULT_OFF=PASS")


def test_unbound_config_boolean_only():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        cfg = os.path.join(tmp, "config.json")

        for raw, expected in [
            ("0", False),
            ("1", True),
            ("true", False),
            ("on", False),
            ("", False),
        ]:
            with open(cfg, "w", encoding="utf-8") as handle:
                json.dump({"unbound_enabled": raw}, handle)

            module.CONFIG_FILE = cfg
            assert module.load_config()["unbound_enabled"] is expected

    print("UNBOUND_BOOLEAN_ONLY=PASS")


def test_disabled_unbound_provider_not_constructed():
    module = load_module()
    build = module.build_hostname_providers

    disabled = build({}, {}, {}, {}, {}, {})
    assert "unbound" not in [provider.name for provider in disabled]

    enabled = build({}, {}, {}, {}, {}, {IP: "unbound-name"})
    assert "unbound" in [provider.name for provider in enabled]

    print("UNBOUND_DISABLED_NOT_CONSTRUCTED=PASS")


def test_unbound_call_site_gated_by_config():
    module = load_module()
    source = SOURCE.read_text(encoding="utf-8")

    # The runtime must only invoke the Unbound provider when the opt-in flag is
    # set; otherwise an empty mapping is used without touching config.xml.
    assert "config.get('unbound_enabled')" in source
    assert "get_unbound_hostnames() if" in source

    print("UNBOUND_GATED_BY_CONFIG=PASS")


def test_full_precedence_all_enabled():
    module = load_module()
    build = module.build_hostname_providers
    resolve = module.resolve_hostname

    providers = build(
        {MAC_LOWER: "isc-name"},
        {MAC_LOWER: "kea-name"},
        {MAC_LOWER: "dnsmasq-name"},
        {IP: "adguard-name"},
        {MAC_LOWER: "pihole-name"},
        {IP: "unbound-name"},
    )

    hostname, source = resolve(
        {"mac": MAC, "ip": IP, "hostname": "hostwatch-name"}, providers
    )

    assert hostname == "adguard-name"
    assert source == "adguard"

    print("UNBOUND_FULL_PRECEDENCE_ALL_ENABLED=PASS")


def main():
    test_host_override_returns_hostname()
    test_no_records_returns_empty()
    test_malformed_and_missing_source()
    test_duplicate_records_deterministic()
    test_non_a_and_disabled_skipped()
    test_alias_secondary_name()
    test_source_is_unbound()
    test_precedence_against_all_providers()
    test_retained_hostname_not_erased()
    test_friendly_name_untouched()
    test_duplicate_idempotent()
    test_resolve_hostname_has_no_unbound_branch()
    test_apply_wrapper_accepts_unbound()
    test_unbound_defaults_off_when_key_absent()
    test_unbound_config_boolean_only()
    test_disabled_unbound_provider_not_constructed()
    test_unbound_call_site_gated_by_config()
    test_full_precedence_all_enabled()

    print("UNBOUND_PROVIDER_REGRESSION=PASS")


if __name__ == "__main__":
    main()
