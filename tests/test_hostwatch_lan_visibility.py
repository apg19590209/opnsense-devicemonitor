import importlib.util
import inspect
import subprocess

p='src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py'
s=importlib.util.spec_from_file_location('dm',p)
m=importlib.util.module_from_spec(s); s.loader.exec_module(m)


class Root:
    def __init__(self, ip='192.168.20.254', subnet='24'):
        self.values = {
            './interfaces/lan/ipaddr': ip,
            './interfaces/lan/subnet': subnet,
        }

    def findtext(self, path):
        return self.values.get(path)


class Tree:
    def __init__(self, root):
        self.root = root

    def getroot(self):
        return self.root


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


orig_parse = m.ET.parse
orig_run = m.subprocess.run
orig_executor = m.ThreadPoolExecutor
orig_sleep = m.time.sleep
orig_log = m.log

try:
    m.ThreadPoolExecutor = Executor
    m.time.sleep = lambda seconds: None
    m.log = lambda message: None

    # Valid /24: all usable hosts except OPNsense itself are probed.
    calls = []
    m.ET.parse = lambda path: Tree(Root(subnet='24'))
    m.subprocess.run = lambda args, **kwargs: (
        calls.append((args, kwargs)) or Result(0)
    )

    m.prime_hostwatch_lan_visibility()

    addresses = [call[0][4] for call in calls]
    assert len(addresses) == 253
    assert '192.168.20.254' not in addresses
    assert '192.168.20.1' in addresses
    assert '192.168.20.253' in addresses
    assert Executor.workers == 32

    for args, kwargs in calls:
        assert args[:3] == ['/sbin/ping', '-n', '-c']
        assert args[4]
        assert kwargs['timeout'] == 2
        assert kwargs['check'] is False
        assert kwargs['stdout'] is subprocess.DEVNULL
        assert kwargs['stderr'] is subprocess.DEVNULL

    # Smaller network such as /25 is allowed.
    calls = []
    m.ET.parse = lambda path: Tree(Root(subnet='25'))
    m.subprocess.run = lambda args, **kwargs: (
        calls.append(args[4]) or Result(0)
    )

    m.prime_hostwatch_lan_visibility()

    assert len(calls) == 125
    assert '192.168.20.254' not in calls
    assert '192.168.20.129' in calls
    assert '192.168.20.253' in calls

    # Networks larger than /24 are rejected.
    calls = []
    m.ET.parse = lambda path: Tree(Root(subnet='23'))
    m.subprocess.run = lambda *args, **kwargs: (
        calls.append(True) or Result(0)
    )

    m.prime_hostwatch_lan_visibility()
    assert calls == []

    # Malformed LAN configuration fails soft.
    m.ET.parse = lambda path: Tree(Root(ip='not-an-ip', subnet='24'))
    m.subprocess.run = lambda *args, **kwargs: (
        (_ for _ in ()).throw(Exception('ping should not run'))
    )

    m.prime_hostwatch_lan_visibility()

    # Missing/unreadable config fails soft.
    def missing_config(path):
        raise OSError('missing config')

    m.ET.parse = missing_config
    m.prime_hostwatch_lan_visibility()

    # Individual ping timeout/failure must not abort the pass.
    seen = []

    def mixed_ping(args, **kwargs):
        address = args[4]
        seen.append(address)

        if address == '192.168.20.1':
            raise subprocess.TimeoutExpired('ping', 2)

        if address == '192.168.20.2':
            return Result(1)

        return Result(0)

    m.ET.parse = lambda path: Tree(Root(subnet='25'))
    m.subprocess.run = mixed_ping

    m.prime_hostwatch_lan_visibility()

    assert '192.168.20.1' not in seen
    assert len(seen) == 125

    # Use a /24 containing .1/.2 for timeout/failure coverage.
    seen = []
    m.ET.parse = lambda path: Tree(
        Root(ip='192.168.20.254', subnet='24')
    )
    m.subprocess.run = mixed_ping

    m.prime_hostwatch_lan_visibility()

    assert '192.168.20.1' in seen
    assert '192.168.20.2' in seen
    assert len(seen) == 253

    # Full scan must prime Hostwatch before reading Hostwatch.
    full_source = inspect.getsource(m.full_scan)
    assert (
        full_source.index('prime_hostwatch_lan_visibility()')
        <
        full_source.index('devices = get_hostwatch_devices()')
    )

    # Quick update mode must remain passive and not run LAN priming.
    update_source = inspect.getsource(m.update_status_only)
    assert 'prime_hostwatch_lan_visibility' not in update_source

finally:
    m.ET.parse = orig_parse
    m.subprocess.run = orig_run
    m.ThreadPoolExecutor = orig_executor
    m.time.sleep = orig_sleep
    m.log = orig_log


print('HOSTWATCH_LAN_VISIBILITY_REGRESSION=PASS')
