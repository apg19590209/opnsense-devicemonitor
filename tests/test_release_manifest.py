"""Validate the v2.9 install payload without touching an OPNsense host."""
from pathlib import Path
import hashlib
import json
import subprocess

root = Path(__file__).resolve().parents[1]
manifest = root / 'release/v2.9-runtime.manifest'
rows = [line.split() for line in manifest.read_text().splitlines()]
assert len(rows) == 37
assert all(len(row) == 4 for row in rows)
sources = [row[2] for row in rows]
targets = [row[3] for row in rows]
assert len(set(sources)) == len(sources)
assert len(set(targets)) == len(targets)
for digest, mode, source, target in rows:
    path = root / source
    assert path.is_file(), source
    released = subprocess.check_output(
        ['git', 'show', 'v2.9:' + source], cwd=root,
    )
    assert hashlib.sha256(released).hexdigest() == digest, source
    assert mode in {'644', '755'}, source
    if source.startswith('src/opnsense/'):
        assert target == '/usr/local/opnsense/' + source.removeprefix('src/opnsense/')
    else:
        assert (source, target) in {
            ('src/etc/rc.d/devicemonitor', '/usr/local/etc/rc.d/devicemonitor'),
            ('src/etc/inc/plugins.inc.d/devicemonitor.inc',
             '/usr/local/etc/inc/plugins.inc.d/devicemonitor.inc'),
        }
    assert '/var/db/' not in target and 'config.json' not in target
defaults = subprocess.check_output(
    ['git', 'show', 'v2.9:src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'],
    cwd=root,
)
assert json.loads(defaults)['version'] == '2.9'
print('V29_RELEASE_MANIFEST=PASS')
