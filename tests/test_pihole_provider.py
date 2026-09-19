import importlib.util
import inspect
import io
import json
import socket
import urllib.error
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

AUTH_PAYLOAD = {"session": {"valid": True, "sid": "test-sid-123"}}
LEASES_PAYLOAD = {
    "leases": [
        {"hwaddr": MAC, "ip": IP, "name": "  printer.local.  "},
        {"hwaddr": "bb:cc:dd:ee:ff:00", "ip": "192.0.2.20", "name": "other-host"},
    ]
}


def load_module(log=None):
    spec = importlib.util.spec_from_file_location(
        "devicemonitor_pihole_test", SOURCE
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.log = log if log is not None else (lambda message: None)
    return module


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, limit=None):
        data = json.dumps(self._payload).encode("utf-8")
        return data if limit is None else data[:limit]


def patch_urlopen(module, auth=AUTH_PAYLOAD, leases=LEASES_PAYLOAD):
    """Patch module.urllib.request.urlopen and record the requests made."""
    calls = []

    def fake_urlopen(request, timeout=None, context=None):
        calls.append(request)
        url = request.full_url

        if url.endswith("/api/auth"):
            result = auth
        elif url.endswith("/api/dhcp/leases"):
            result = leases
        else:
            result = RuntimeError("unexpected URL: " + url)

        if isinstance(result, Exception):
            raise result
        return FakeResponse(result)

    module.urllib.request.urlopen = fake_urlopen
    return calls


def enabled_config(url="https://pi.hole", password="app-password"):
    return {
        "pihole_enabled": "1",
        "pihole_url": url,
        "pihole_password": password,
    }


def test_disabled_returns_empty():
    module = load_module()
    assert module.get_pihole_hostnames({}) == {}
    assert module.get_pihole_hostnames({"pihole_enabled": "0"}) == {}

    print("PIHOLE_DISABLED=PASS")


def test_missing_config_returns_empty():
    module = load_module()

    assert module.get_pihole_hostnames({"pihole_enabled": "1"}) == {}
    assert module.get_pihole_hostnames(
        {"pihole_enabled": "1", "pihole_url": "https://pi.hole"}
    ) == {}
    assert module.get_pihole_hostnames(
        {"pihole_enabled": "1", "pihole_password": "x"}
    ) == {}

    print("PIHOLE_MISSING_CONFIG=PASS")


def test_valid_response_returns_normalized_mapping():
    module = load_module()
    patch_urlopen(module)

    mapping = module.get_pihole_hostnames(enabled_config())

    assert mapping == {
        MAC_LOWER: "printer.local",
        "bb:cc:dd:ee:ff:00": "other-host",
    }

    print("PIHOLE_VALID_RESPONSE=PASS")


def test_no_matching_device_and_empty_leases():
    module = load_module()
    resolve = module.resolve_hostname
    Mapping = module.MappingHostnameProvider

    patch_urlopen(module, leases={"leases": []})
    mapping = module.get_pihole_hostnames(enabled_config())
    assert mapping == {}

    providers = [Mapping("pihole", mapping, key="mac", lower=True)]
    hostname, source = resolve(
        {"mac": MAC, "ip": IP, "hostname": ""}, providers
    )
    assert hostname == ""
    assert source == ""

    print("PIHOLE_EMPTY_AND_NO_MATCH=PASS")


def test_precedence_and_source():
    module = load_module()
    build = module.build_hostname_providers
    resolve = module.resolve_hostname

    # Pi-hole is weaker than ISC but stronger than the Hostwatch base.
    providers = build(
        {MAC_LOWER: "isc-name"},
        {},
        {},
        {},
        {MAC_LOWER: "pihole-name"},
    )
    hostname, source = resolve({"mac": MAC, "ip": IP, "hostname": ""}, providers)
    assert hostname == "isc-name"
    assert source == "isc"

    providers = build({}, {}, {}, {}, {MAC_LOWER: "pihole-name"})
    hostname, source = resolve(
        {"mac": MAC, "ip": IP, "hostname": "hostwatch-name"}, providers
    )
    assert hostname == "pihole-name"
    assert source == "pihole"

    print("PIHOLE_PRECEDENCE_AND_SOURCE=PASS")


def test_malformed_and_failure_cases():
    module = load_module()

    # Malformed JSON in the leases response.
    class MalformedResponse(FakeResponse):
        def read(self, limit=None):
            return b"{not-json"

    module.urllib.request.urlopen = (
        lambda request, timeout=None, context=None: MalformedResponse({})
    )
    assert module.get_pihole_hostnames(enabled_config()) == {}

    # Malformed schema (not a dict).
    patch_urlopen(module, leases=["not", "a", "dict"])
    assert module.get_pihole_hostnames(enabled_config()) == {}

    # Network exception.
    patch_urlopen(module, auth=socket.timeout("timed out"))
    assert module.get_pihole_hostnames(enabled_config()) == {}

    # Timeout.
    patch_urlopen(module, leases=TimeoutError("timed out"))
    assert module.get_pihole_hostnames(enabled_config()) == {}

    # HTTP error.
    http_err = urllib.error.HTTPError(
        "https://pi.hole/api/auth", 401, "Unauthorized", {}, io.BytesIO(b"{}")
    )
    patch_urlopen(module, auth=http_err)
    assert module.get_pihole_hostnames(enabled_config()) == {}

    # Authentication failure (no session id in response).
    patch_urlopen(module, auth={"error": "unauthorized"})
    assert module.get_pihole_hostnames(enabled_config()) == {}

    print("PIHOLE_FAILURE_ISOLATION=PASS")


def test_retained_hostname_not_erased():
    module = load_module()
    resolve = module.resolve_hostname
    Mapping = module.MappingHostnameProvider

    providers = [Mapping("pihole", {}, key="mac", lower=True)]
    hostname, source = resolve(
        {"mac": MAC, "ip": IP, "hostname": "retained-host"}, providers
    )
    assert hostname == "retained-host"
    assert source == "hostwatch"

    print("PIHOLE_NO_ERASE=PASS")


def test_friendly_name_untouched():
    module = load_module()
    resolve = module.resolve_hostname
    Mapping = module.MappingHostnameProvider

    device = {"mac": MAC, "ip": IP, "hostname": "", "custom_hostname": "Friend"}
    providers = [Mapping("pihole", {MAC_LOWER: "pihole-name"}, key="mac", lower=True)]

    hostname, source = resolve(device, providers)
    assert hostname == "pihole-name"
    assert source == "pihole"
    assert device["custom_hostname"] == "Friend"

    print("PIHOLE_FRIENDLY_NAME=PASS")


def test_duplicate_idempotent():
    module = load_module()
    resolve = module.resolve_hostname
    Mapping = module.MappingHostnameProvider

    providers = [Mapping("pihole", {MAC_LOWER: "same-name"}, key="mac", lower=True)]
    first = resolve({"mac": MAC, "ip": IP, "hostname": ""}, providers)
    second = resolve({"mac": MAC, "ip": IP, "hostname": ""}, providers)
    assert first == second == ("same-name", "pihole")

    print("PIHOLE_IDEMPOTENT=PASS")


def test_credentials_not_logged():
    logged = []
    module = load_module(log=logged.append)

    patch_urlopen(module, auth=socket.timeout("timed out"))
    module.get_pihole_hostnames(enabled_config(password="super-secret-pw"))

    joined = "\n".join(logged)
    assert "super-secret-pw" not in joined
    assert "app-password" not in joined

    print("PIHOLE_CREDENTIALS_NOT_LOGGED=PASS")


def test_resolve_hostname_has_no_pihole_branch():
    module = load_module()
    source = inspect.getsource(module.resolve_hostname).lower()
    assert "pihole" not in source
    assert "pi-hole" not in source

    print("PIHOLE_GENERIC_RESOLVER=PASS")


def test_apply_wrapper_accepts_pihole():
    module = load_module()

    device = {"mac": MAC, "ip": IP, "hostname": ""}
    module.apply_hostname_provenance(
        device,
        {},
        {},
        {},
        {},
        {MAC_LOWER: "pihole-name"},
    )
    assert device["hostname"] == "pihole-name"
    assert device["hostname_source"] == "pihole"

    print("PIHOLE_APPLY_WRAPPER=PASS")


def main():
    test_disabled_returns_empty()
    test_missing_config_returns_empty()
    test_valid_response_returns_normalized_mapping()
    test_no_matching_device_and_empty_leases()
    test_precedence_and_source()
    test_malformed_and_failure_cases()
    test_retained_hostname_not_erased()
    test_friendly_name_untouched()
    test_duplicate_idempotent()
    test_credentials_not_logged()
    test_resolve_hostname_has_no_pihole_branch()
    test_apply_wrapper_accepts_pihole()

    print("PIHOLE_PROVIDER_REGRESSION=PASS")


if __name__ == "__main__":
    main()
