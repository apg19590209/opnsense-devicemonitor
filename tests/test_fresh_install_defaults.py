import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
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


def test_fresh_install_email_is_disabled_without_recipient():
    with DEFAULTS.open("r", encoding="utf-8") as handle:
        config = json.load(handle)["config"]

    assert config["email_enabled"] == "0", config["email_enabled"]
    assert config["email_to"] == "", config["email_to"]

    print("FRESH_INSTALL_EMAIL_DEFAULT=PASS")


def test_experimental_providers_disabled_by_default():
    with DEFAULTS.open("r", encoding="utf-8") as handle:
        config = json.load(handle)["config"]

    assert config["pihole_enabled"] == "0", config["pihole_enabled"]
    assert config["unbound_enabled"] == "0", config["unbound_enabled"]

    print("FRESH_INSTALL_PROVIDERS_DISABLED=PASS")


def main():
    test_fresh_install_email_is_disabled_without_recipient()
    test_experimental_providers_disabled_by_default()
    print("FRESH_INSTALL_DEFAULTS_REGRESSION=PASS")


if __name__ == "__main__":
    main()
