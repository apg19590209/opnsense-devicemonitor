import builtins
import importlib.util
import ipaddress
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py"
DEFAULTS = ROOT / "src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json"


def load_module():
    real_open = builtins.open

    def test_open(path, *args, **kwargs):
        if str(path) == "/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json":
            path = DEFAULTS
        return real_open(path, *args, **kwargs)

    spec = importlib.util.spec_from_file_location("dm_loopback_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    builtins.open = test_open
    try:
        spec.loader.exec_module(module)
    finally:
        builtins.open = real_open
    module.log = lambda message: None
    return module


m = load_module()

FAKE_CONFIG = """<opnsense>
  <interfaces>
    <lo0>
      <enable>1</enable><if>lo0</if><ipaddr>127.0.0.1</ipaddr><subnet>8</subnet><descr>Loopback</descr>
    </lo0>
    <loopback_test>
      <enable>1</enable><if>lo1</if><ipaddr>127.0.0.1</ipaddr><subnet>8</subnet><descr>Loopback test</descr>
    </loopback_test>
    <opt1>
      <enable>1</enable><if>vlan0.50</if><ipaddr>192.168.50.1</ipaddr><subnet>24</subnet><descr>DMTEST</descr>
    </opt1>
    <lan>
      <enable>1</enable><if>re0</if><ipaddr>192.168.20.23</ipaddr><subnet>24</subnet><descr>LAN</descr>
    </lan>
  </interfaces>
</opnsense>"""

fake_tree = ET.ElementTree(ET.fromstring(FAKE_CONFIG))
orig_parse = m.ET.parse
m.ET.parse = lambda path: fake_tree

try:
    # Loopback by logical name (lo0) must be rejected.
    networks, error = m.resolve_monitored_networks({'monitored_interfaces': 'lo0'})
    assert networks is None, 'lo0 must be rejected'
    assert error and 'loopback' in error, 'lo0 rejection must mention loopback'

    # Loopback by address under a non-lo0 name must also be rejected.
    networks, error = m.resolve_monitored_networks(
        {'monitored_interfaces': 'loopback_test'}
    )
    assert networks is None, 'loopback by address must be rejected regardless of name'
    assert error and 'loopback' in error, 'loopback-by-address rejection must mention loopback'

    # Valid VLAN (opt1) must remain valid.
    networks, error = m.resolve_monitored_networks({'monitored_interfaces': 'opt1'})
    assert error is None, f'opt1 must be valid, got error: {error}'
    assert len(networks) == 1 and networks[0]['name'] == 'opt1'
    assert networks[0]['network'] == ipaddress.ip_network('192.168.50.0/24')

    # LAN and opt1 together must remain valid.
    networks, error = m.resolve_monitored_networks(
        {'monitored_interfaces': 'lan,opt1'}
    )
    assert error is None, f'lan,opt1 must be valid, got error: {error}'
    assert sorted(n['name'] for n in networks) == ['lan', 'opt1']

    # Empty selection still fails closed.
    networks, error = m.resolve_monitored_networks({'monitored_interfaces': ''})
    assert networks is None and error is not None, 'empty selection must fail closed'

    # Nonexistent selection still fails closed.
    networks, error = m.resolve_monitored_networks(
        {'monitored_interfaces': 'nonexistent'}
    )
    assert networks is None and error is not None, 'invalid selection must fail closed'

finally:
    m.ET.parse = orig_parse

print("LOOPBACK_PY_RESOLVER_REJECTS=PASS")
print("LOOPBACK_PY_LAN_OPT1_VALID=PASS")
print("LOOPBACK_PY_EMPTY_INVALID_FAIL_CLOSED=PASS")
print("LOOPBACK_MONITORING_PY=PASS")
