"""Validate the v2.11 install payload against the working tree."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[1]
manifest = root / 'release/v2.11-runtime.manifest'
rows = [line.split() for line in manifest.read_text().splitlines()]
assert len(rows) == 39
assert all(len(row) == 4 for row in rows)
sources = [row[2] for row in rows]
targets = [row[3] for row in rows]
assert len(set(sources)) == len(sources)
assert len(set(targets)) == len(targets)
for digest, mode, source, target in rows:
    path = root / source
    assert path.is_file(), source
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, source
    assert mode in {'644', '755'}, source
    if source.startswith('src/opnsense/'):
        assert target == '/usr/local/opnsense/' + source.removeprefix('src/opnsense/')
    else:
        assert (source, target) in {
            ('src/etc/rc.d/devicemonitor', '/usr/local/etc/rc.d/devicemonitor'),
            ('src/etc/inc/plugins.inc.d/devicemonitor.inc',
             '/usr/local/etc/inc/plugins.inc.d/devicemonitor.inc'),
            ('src/etc/inc/devicemonitor_locale.inc',
             '/usr/local/etc/inc/devicemonitor_locale.inc'),
        }
    assert '/var/db/' not in target and 'config.json' not in target
defaults = json.loads(
    (root / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json').read_text()
)
assert defaults['version'] == '2.11'
print('V211_RELEASE_MANIFEST=PASS')
