import importlib.util
import json
import tempfile
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


def load_module():
    spec = importlib.util.spec_from_file_location(
        "devicemonitor_adguard_test",
        SOURCE,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.log = lambda message: None
    return module


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        if isinstance(self.payload, bytes):
            return self.payload
        return json.dumps(self.payload).encode("utf-8")


class FakeOpener:
    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error
        self.request = None
        self.timeout = None

    def open(self, request, timeout=None):
        self.request = request
        self.timeout = timeout

        if self.error is not None:
            raise self.error

        return FakeResponse(self.payload)


def enabled_config():
    return {
        "adguard_rewrite_enabled": True,
        "adguard_url": "https://192.0.2.53/",
        "adguard_username": "test-user",
        "adguard_password": "test-password",
    }


def install_fake_opener(module, payload=None, error=None):
    seen = {}
    opener = FakeOpener(payload=payload, error=error)
    tls_context = object()

    module.ssl.create_default_context = lambda: tls_context

    original_https_handler = module.urllib.request.HTTPSHandler

    def fake_https_handler(context=None):
        seen["https_context"] = context
        return original_https_handler(context=context)

    module.urllib.request.HTTPSHandler = fake_https_handler

    def fake_build_opener(*handlers):
        seen["handlers"] = handlers
        return opener

    module.urllib.request.build_opener = fake_build_opener

    return opener, tls_context, seen


def test_disabled_no_request():
    module = load_module()

    def forbidden_build_opener(*args, **kwargs):
        raise AssertionError("Disabled AdGuard integration made a request")

    module.urllib.request.build_opener = forbidden_build_opener

    result = module.get_adguard_rewrite_hostnames(
        {"adguard_rewrite_enabled": False}
    )

    assert result == {}
    print("ADGUARD_DISABLED_NO_REQUEST=PASS")


def test_non_https_url_rejected_without_request():
    module = load_module()

    def forbidden_build_opener(*args, **kwargs):
        raise AssertionError("Non-HTTPS AdGuard URL made a request")

    module.urllib.request.build_opener = forbidden_build_opener

    config = enabled_config()
    config["adguard_url"] = "http://192.0.2.53"

    result = module.get_adguard_rewrite_hostnames(config)

    assert result == {}
    print("ADGUARD_NON_HTTPS_REJECTED=PASS")


def test_valid_ipv4_rewrites_tls_and_no_redirects():
    module = load_module()

    opener, tls_context, seen = install_fake_opener(
        module,
        payload=[
            {
                "domain": "vault.example.internal",
                "answer": "192.0.2.16",
            },
            {
                "domain": "router.example.internal.",
                "answer": "192.0.2.1",
            },
            {
                "domain": "alias.example.internal",
                "answer": "target.example.internal",
            },
            {
                "domain": "ipv6.example.internal",
                "answer": "2001:db8::1",
            },
        ],
    )

    result = module.get_adguard_rewrite_hostnames(
        enabled_config()
    )

    assert result == {
        "192.0.2.16": "vault.example.internal",
        "192.0.2.1": "router.example.internal",
    }, result

    assert opener.timeout == 4
    assert seen["https_context"] is tls_context

    request = opener.request
    assert request.full_url == (
        "https://192.0.2.53/control/rewrite/list"
    )

    authorization = request.get_header("Authorization")
    assert authorization is not None
    assert authorization.startswith("Basic ")

    redirect_handlers = [
        handler
        for handler in seen["handlers"]
        if isinstance(
            handler,
            module.urllib.request.HTTPRedirectHandler,
        )
    ]

    assert len(redirect_handlers) == 1
    assert (
        redirect_handlers[0].redirect_request(
            request,
            None,
            302,
            "Found",
            {},
            "https://redirect.example.invalid/",
        )
        is None
    )

    print("ADGUARD_IPV4_MAPPING=PASS")
    print("ADGUARD_NON_IPV4_FILTER=PASS")
    print("ADGUARD_TLS_VERIFICATION=PASS")
    print("ADGUARD_REDIRECTS_DISABLED=PASS")


def test_ambiguous_ipv4_rewrite_is_skipped():
    module = load_module()

    install_fake_opener(
        module,
        payload=[
            {
                "domain": "first.example.internal",
                "answer": "192.0.2.20",
            },
            {
                "domain": "second.example.internal",
                "answer": "192.0.2.20",
            },
        ],
    )

    result = module.get_adguard_rewrite_hostnames(
        enabled_config()
    )

    assert result == {}, result
    print("ADGUARD_AMBIGUOUS_REWRITE_SKIPPED=PASS")


def test_malformed_json_fails_soft():
    module = load_module()

    install_fake_opener(
        module,
        payload=b"{not-json",
    )

    result = module.get_adguard_rewrite_hostnames(
        enabled_config()
    )

    assert result == {}
    print("ADGUARD_MALFORMED_JSON_FAILSOFT=PASS")


def test_http_failure_fails_soft():
    module = load_module()

    error = urllib.error.HTTPError(
        url="https://192.0.2.53/control/rewrite/list",
        code=401,
        msg="Unauthorized",
        hdrs=None,
        fp=None,
    )

    install_fake_opener(module, error=error)

    result = module.get_adguard_rewrite_hostnames(
        enabled_config()
    )

    assert result == {}
    print("ADGUARD_HTTP_FAILSOFT=PASS")


def test_invalid_url_fails_soft():
    module = load_module()

    def forbidden_build_opener(*args, **kwargs):
        raise AssertionError("Invalid AdGuard URL made a request")

    module.urllib.request.build_opener = forbidden_build_opener

    config = enabled_config()
    config["adguard_url"] = "https://user:pass@192.0.2.53"

    result = module.get_adguard_rewrite_hostnames(config)

    assert result == {}
    print("ADGUARD_EMBEDDED_CREDENTIALS_REJECTED=PASS")


def test_load_config_exposes_adguard_settings():
    module = load_module()

    with tempfile.TemporaryDirectory() as tmp:
        config_file = Path(tmp) / "config.json"

        config_file.write_text(
            json.dumps(
                {
                    "adguard_rewrite_enabled": "1",
                    "adguard_url": "https://192.0.2.53",
                    "adguard_username": "configured-user",
                    "adguard_password": "configured-password",
                }
            ),
            encoding="utf-8",
        )

        module.CONFIG_FILE = str(config_file)

        config = module.load_config()

        assert config["adguard_rewrite_enabled"] is True
        assert config["adguard_url"] == "https://192.0.2.53"
        assert config["adguard_username"] == "configured-user"
        assert config["adguard_password"] == "configured-password"

    print("ADGUARD_LOAD_CONFIG=PASS")


def main():
    test_disabled_no_request()
    test_non_https_url_rejected_without_request()
    test_valid_ipv4_rewrites_tls_and_no_redirects()
    test_ambiguous_ipv4_rewrite_is_skipped()
    test_malformed_json_fails_soft()
    test_http_failure_fails_soft()
    test_invalid_url_fails_soft()
    test_load_config_exposes_adguard_settings()

    print("ADGUARD_REWRITE_REGRESSION=PASS")


if __name__ == "__main__":
    main()
