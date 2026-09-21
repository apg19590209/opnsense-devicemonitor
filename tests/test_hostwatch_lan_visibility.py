import builtins
import importlib.util
import inspect
import ipaddress
import subprocess
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

    spec = importlib.util.spec_from_file_location("dm_visibility_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    builtins.open = test_open
    try:
        spec.loader.exec_module(module)
    finally:
        builtins.open = real_open
    module.log = lambda message: None
    return module


def net(ip, prefix):
    return {
        "name": "opt1",
        "description": "DMTEST",
        "device": "vlan0.50",
        "ip": ip,
        "subnet": str(prefix),
        "network": ipaddress.ip_network(f"{ip}/{prefix}", strict=False),
    }


class Result:
    def __init__(self, returncode=0):
        self.returncode = returncode


class Executor:
    workers = None

    def __init__(self, max_workers=None):
        Executor.workers = max_workers

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def map(self, func, values):
        return [func(value) for value in values]


m = load_module()

orig_run = m.subprocess.run
orig_executor = m.ThreadPoolExecutor
orig_sleep = m.time.sleep

try:
    m.ThreadPoolExecutor = Executor
    m.time.sleep = lambda seconds: None

    # Selected /24 (opt1): every usable host except the interface IP is probed.
    calls = []
    m.subprocess.run = lambda args, **kwargs: (calls.append((args, kwargs)) or Result(0))
    m.prime_selected_interface_visibility([net("192.168.50.1", 24)])

    addresses = [call[0][4] for call in calls]
    assert len(addresses) == 253
    assert "192.168.50.1" not in addresses
    assert "192.168.50.2" in addresses
    assert "192.168.50.254" in addresses
    assert not any(a.startswith("192.168.20.") for a in addresses)
    assert Executor.workers == 32

    for args, kwargs in calls:
        assert args[:3] == ["/sbin/ping", "-n", "-c"]
        assert args[4]
        assert kwargs["timeout"] == 2
        assert kwargs["check"] is False
        assert kwargs["stdout"] is subprocess.DEVNULL
        assert kwargs["stderr"] is subprocess.DEVNULL

    # Smaller network such as /25 is allowed (interface ip .254 -> .129..253).
    calls = []
    m.subprocess.run = lambda args, **kwargs: (calls.append(args[4]) or Result(0))
    m.prime_selected_interface_visibility([net("192.168.50.254", 25)])

    assert len(calls) == 125
    assert "192.168.50.129" in calls
    assert "192.168.50.253" in calls
    assert "192.168.50.254" not in calls
    assert not any(a.startswith("192.168.20.") for a in calls)

    # Networks larger than /24 are rejected (no probe).
    calls = []
    m.subprocess.run = lambda *args, **kwargs: (calls.append(True) or Result(0))
    m.prime_selected_interface_visibility([net("192.168.50.1", 23)])
    assert calls == []

    # Malformed interface IP fails soft (no probe).
    bad_ip = dict(net("192.168.50.1", 24), ip="not-an-ip")
    m.subprocess.run = lambda *args, **kwargs: (_ for _ in ()).throw(Exception("ping should not run"))
    m.prime_selected_interface_visibility([bad_ip])

    # Empty selection is a no-op.
    m.prime_selected_interface_visibility([])

    # Individual ping timeout/failure must not abort the pass.
    seen = []

    def mixed_ping(args, **kwargs):
        address = args[4]
        seen.append(address)
        if address == "192.168.50.1":
            raise subprocess.TimeoutExpired("ping", 2)
        if address == "192.168.50.2":
            return Result(1)
        return Result(0)

    # /25 target set excludes .1/.2.
    m.subprocess.run = mixed_ping
    m.prime_selected_interface_visibility([net("192.168.50.254", 25)])
    assert "192.168.50.1" not in seen
    assert len(seen) == 125

    # /24 target set includes .1/.2.
    seen = []
    m.subprocess.run = mixed_ping
    m.prime_selected_interface_visibility([net("192.168.50.254", 24)])
    assert "192.168.50.1" in seen
    assert "192.168.50.2" in seen
    assert len(seen) == 253

    # Full scan must prime Hostwatch before reading Hostwatch.
    full_source = inspect.getsource(m.full_scan)
    assert (
        full_source.index("prime_selected_interface_visibility(networks)")
        <
        full_source.index("devices = get_hostwatch_devices(networks)")
    )

    # Quick update mode must remain passive and not run visibility priming.
    update_source = inspect.getsource(m.update_status_only)
    assert "prime_selected_interface_visibility" not in update_source

finally:
    m.subprocess.run = orig_run
    m.ThreadPoolExecutor = orig_executor
    m.time.sleep = orig_sleep


print("HOSTWATCH_LAN_VISIBILITY_REGRESSION=PASS")
