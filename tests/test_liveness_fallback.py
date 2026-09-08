import importlib.util
import subprocess
from datetime import datetime, timedelta, UTC

p='src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py'
s=importlib.util.spec_from_file_location('dm',p)
m=importlib.util.module_from_spec(s); s.loader.exec_module(m)

recent=datetime.now(UTC).replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S')
recover=(datetime.now(UTC).replace(tzinfo=None)-timedelta(minutes=60)).strftime('%Y-%m-%d %H:%M:%S')
grace=(datetime.now(UTC).replace(tzinfo=None)-timedelta(minutes=20)).strftime('%Y-%m-%d %H:%M:%S')
stale=(datetime.now(UTC).replace(tzinfo=None)-timedelta(minutes=31)).strftime('%Y-%m-%d %H:%M:%S')
old=(datetime.now(UTC).replace(tzinfo=None)-timedelta(minutes=121)).strftime('%Y-%m-%d %H:%M:%S')

class R:
    def __init__(self,rc): self.returncode=rc

orig=m.subprocess.run
try:
    m.subprocess.run=lambda *a,**k: (_ for _ in ()).throw(Exception('ping should not run'))
    assert m.is_device_active(recent,'192.168.20.210',True)
    assert not m.is_device_active(old,'192.168.20.210',False)

    m.subprocess.run=lambda *a,**k:R(0)
    assert m.is_device_active(stale,'192.168.20.210',True)
    assert m.is_device_active(recover,'192.168.20.211',False)

    m.subprocess.run=lambda *a,**k:R(1)
    assert m.is_device_active(grace,'192.168.20.210',True)
    assert not m.is_device_active(grace,'192.168.20.210',False)
    assert not m.is_device_active(stale,'192.168.20.210',True)

    def timeout(*a,**k): raise subprocess.TimeoutExpired('ping',2)
    m.subprocess.run=timeout
    assert not m.is_device_active(stale,'192.168.20.210',True)
finally:
    m.subprocess.run=orig

print('LIVENESS_FALLBACK_REGRESSION=PASS')
