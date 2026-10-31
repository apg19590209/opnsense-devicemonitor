"""Device Monitor must never monitor the WAN/uplink segment.

v2.11 HA safety (Decision 51). After the production HA reconfiguration `opt1`
disappeared and the uplink became `wan`. Interface selection is by logical name,
so a re-selection can point the scanner at the internet-facing segment: nmap and
the service probes would then run across the uplink, which is both noisy and
inappropriate for a LAN-observability plugin.

`resolve_monitored_networks()` therefore refuses:

  * an interface named `wan`, and
  * any interface carrying a `<gateway>` child, which is what marks an uplink
    regardless of what the assignment is called.

Everything else keeps the existing fail-closed behaviour (missing, disabled,
no device, no static IPv4, loopback, bad subnet, overlapping subnets).

The checks drive the real resolver through a fixture configuration tree, so no
`/conf/config.xml` edit is required.
"""
import builtins
import importlib.util
import ipaddress
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

CONFIG_XML = """<opnsense>
  <interfaces>
    <lan>
      <enable>1</enable>
      <if>re0</if>
      <ipaddr>192.168.20.23</ipaddr>
      <subnet>24</subnet>
      <descr>LAN</descr>
    </lan>
    <opt1>
      <enable>1</enable>
      <if>vlan0.50</if>
      <ipaddr>192.168.50.1</ipaddr>
      <subnet>24</subnet>
      <descr>DMTEST</descr>
    </opt1>
    <wan>
      <enable>1</enable>
      <if>em0</if>
      <ipaddr>203.0.113.10</ipaddr>
      <subnet>24</subnet>
      <descr>WAN</descr>
    </wan>
    <opt3>
      <enable>1</enable>
      <if>em1</if>
      <ipaddr>198.51.100.2</ipaddr>
      <subnet>24</subnet>
      <descr>UPLINK2</descr>
      <gateway>WAN2_GW</gateway>
    </opt3>
    <opt4>
      <enable>1</enable>
      <if>em2</if>
      <ipaddr>10.10.10.1</ipaddr>
      <subnet>24</subnet>
      <descr>POLICYROUTE</descr>
      <gateway>LAN_GW</gateway>
    </opt4>
    <opt5>
      <enable>1</enable>
      <if>em3</if>
      <ipaddr>192.0.2.50</ipaddr>
      <subnet>24</subnet>
      <descr>DMZ</descr>
    </opt5>
  </interfaces>
</opnsense>
"""


def load_module():
    """Load scan_network.py with defaults.json redirected to the checkout."""
    original_open = builtins.open

    def test_open(path, *args, **kwargs):
        if str(path).endswith('/models/OPNsense/DeviceMonitor/defaults.json'):
            path = DEFAULTS
        return original_open(path, *args, **kwargs)

    spec = importlib.util.spec_from_file_location(
        "devicemonitor_monitored_interfaces_test",
        SOURCE,
    )
    module = importlib.util.module_from_spec(spec)
    builtins.open = test_open
    try:
        spec.loader.exec_module(module)
    finally:
        builtins.open = original_open

    module.log = lambda message: None

    root = ET.fromstring(CONFIG_XML)
    tree = ET.ElementTree(root)
    module.ET = type(
        "FixtureET",
        (),
        {
            "parse": staticmethod(lambda path: tree),
            "ParseError": ET.ParseError,
        },
    )

    return module


def select(module, names):
    return module.resolve_monitored_networks(
        {"monitored_interfaces": names}
    )



def test_internal_interfaces_accepted():
    module = load_module()

    networks, error = select(module, "lan,opt1")

    assert error is None, error
    assert [n["name"] for n in networks] == ["lan", "opt1"], networks
    assert networks[0]["device"] == "re0", networks
    assert networks[1]["network"] == ipaddress.ip_network("192.168.50.0/24")

    print("MONITORED_INTERNAL_ACCEPTED=PASS")


def test_wan_by_name_refused():
    module = load_module()

    networks, error = select(module, "lan,wan")

    assert networks is None, networks
    assert error and "WAN" in error.upper(), error

    print("MONITORED_WAN_REFUSED=PASS")


def test_uplink_by_gateway_refused():
    module = load_module()

    networks, error = select(module, "opt3")

    assert networks is None, networks
    assert error and "OPT3" in error.upper(), error

    print("MONITORED_GATEWAY_REFUSED=PASS")


def test_internal_segment_with_gateway_allowed():
    """Policy routing on an internal segment must not disable monitoring."""
    module = load_module()

    networks, error = select(module, "opt4")

    assert error is None, error
    assert [n["name"] for n in networks] == ["opt4"], networks

    print("MONITORED_INTERNAL_GATEWAY_ALLOWED=PASS")


def test_public_segment_without_gateway_allowed():
    """A DMZ on public space is a legitimate target when nothing marks it uplink."""
    module = load_module()

    networks, error = select(module, "opt5")

    assert error is None, error
    assert [n["name"] for n in networks] == ["opt5"], networks

    print("MONITORED_DMZ_ALLOWED=PASS")


def test_missing_interface_still_refused():
    module = load_module()

    networks, error = select(module, "opt9")

    assert networks is None, networks
    assert error and "does not exist" in error, error

    print("MONITORED_MISSING_STILL_REFUSED=PASS")


def test_empty_selection_still_refused():
    module = load_module()

    networks, error = select(module, "")

    assert networks is None, networks
    assert error and "No monitored interfaces" in error, error

    print("MONITORED_EMPTY_STILL_REFUSED=PASS")


def main():
    test_internal_interfaces_accepted()
    test_wan_by_name_refused()
    test_uplink_by_gateway_refused()
    test_internal_segment_with_gateway_allowed()
    test_public_segment_without_gateway_allowed()
    test_missing_interface_still_refused()
    test_empty_selection_still_refused()

    print("MONITORED_INTERFACES=PASS")


if __name__ == "__main__":
    main()
