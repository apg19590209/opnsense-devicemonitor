"""Validate the v2.13.3 install payload against the working tree.

Also proves that the published 2.13.2 payload was not rewritten: the tag still carries the
manifest it shipped, byte for byte, so `dm-v2.13.2-runtime.tar.gz` keeps its identity.
"""
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
installer = (root / 'install-unattended.sh').read_text()
version = re.search(r'^VERSION=([0-9.]+)$', installer, re.M).group(1)
manifest = root / ('release/v%s-runtime.manifest' % version)
rows = [line.split() for line in manifest.read_text().splitlines()]
assert len(rows) == 40, len(rows)
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
assert defaults['version'] == version, (defaults['version'], version)


def published_manifest_is_intact():
    """The v2.13.2 tag still ships the manifest that was released under that tag."""
    tag = 'v2.13.2'
    path = 'release/v2.13.2-runtime.manifest'
    try:
        published = subprocess.run(['git', '-C', str(root), 'show', '%s:%s' % (tag, path)],
                                   capture_output=True, text=True, check=True, timeout=30).stdout
    except (subprocess.SubprocessError, OSError):
        if os.environ.get('DM_ALLOW_MISSING_HISTORY') == '1':
            print('  SKIPPED v2.13.2 identity: tag not fetched')
            return
        raise AssertionError('tag %s is missing: fetch the history (fetch-depth: 0) or set '
                             'DM_ALLOW_MISSING_HISTORY=1 for a deliberate local run' % tag)
    assert published == (root / path).read_text(), 'release/%s was modified in place' % path


published_manifest_is_intact()
print('V%s_RELEASE_MANIFEST=PASS' % version.replace('.', ''))
