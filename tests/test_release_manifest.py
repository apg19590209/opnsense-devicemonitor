"""Validate the v2.12.1 release identity and its complete install payload."""
import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = '2.12.1'
MANIFEST_ROWS = 41
HISTORICAL_MANIFEST_SHA = '00698f943b3c3fd79fa9a8dcfa061020df0306ef9952b29b444d725f938a5d3a'
INSTALLER = ROOT / 'install-unattended.sh'
DEFAULTS = ROOT / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'
MANIFEST = ROOT / ('release/v%s-runtime.manifest' % VERSION)
BUILD = ROOT / 'release/build-bundle.sh'
CORE_LOCALE_HELPER = ROOT / 'release/core-locale-state.sh'
NORMALISER = ROOT / 'release/normalize-bundle-tar.py'
GZIPPER = ROOT / 'release/bundle-gzip.py'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


installer = INSTALLER.read_text()
rows = [line.split() for line in MANIFEST.read_text().splitlines() if line.strip()]
assert len(rows) == MANIFEST_ROWS, len(rows)
assert all(len(row) == 4 for row in rows)

# Every payload input is present, hash-pinned, regular and assigned a supported mode.
sources = [row[2] for row in rows]
targets = [row[3] for row in rows]
assert len(set(sources)) == len(sources), 'duplicate manifest source'
assert len(set(targets)) == len(targets), 'duplicate manifest target'
for digest, mode, source, target in rows:
    path = ROOT / source
    assert path.is_file() and not path.is_symlink(), source
    assert sha256(path) == digest, source
    assert mode in {'644', '755'}, source
    assert target.startswith('/') and '/../' not in target, target
    if source.startswith('src/opnsense/'):
        assert target == '/usr/local/opnsense/' + source.removeprefix('src/opnsense/')
    else:
        assert (source, target) in {
            ('src/etc/rc.d/devicemonitor', '/usr/local/etc/rc.d/devicemonitor'),
            ('src/etc/inc/plugins.inc.d/devicemonitor.inc',
             '/usr/local/etc/inc/plugins.inc.d/devicemonitor.inc'),
            ('src/etc/inc/devicemonitor_locale.inc',
             '/usr/local/etc/inc/devicemonitor_locale.inc'),
        }, (source, target)
    assert '/var/db/' not in target and 'config.json' not in target

# One release identity drives the installer, defaults, manifest name and About fallback.
match = re.search(r'^VERSION=([0-9.]+)$', installer, re.M)
assert match and match.group(1) == VERSION, match.group(1) if match else None
assert 'MANIFEST=release/v${VERSION}-runtime.manifest' in installer
assert json.loads(DEFAULTS.read_text())['version'] == VERSION
settings = (ROOT / 'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt').read_text()
assert 'id="about-features-version">v%s</span>' % VERSION in settings

# Rollback and deterministic archive inputs are shipped or executed by the release process.
build = BUILD.read_text()
assert CORE_LOCALE_HELPER.is_file() and os.access(CORE_LOCALE_HELPER, os.X_OK)
assert NORMALISER.is_file() and GZIPPER.is_file()
assert 'release/core-locale-state.sh' in build
assert 'normalize-bundle-tar.py' in build and 'bundle-gzip.py' in build
assert 'CORE_LOCALE_HELPER=release/core-locale-state.sh' in installer

# The digest, row guard and both target guards move with the manifest and locale loop.
match = re.search(r'^MANIFEST_SHA=([0-9a-f]{64})$', installer, re.M)
assert match and match.group(1) == sha256(MANIFEST), match.group(1) if match else None
match = re.search(r'^\[ .*wc -l < "\$MANIFEST".*?= ([0-9]+) \]', installer, re.M)
assert match and int(match.group(1)) == MANIFEST_ROWS, match.group(1) if match else None
match = re.search(r'^for lang in ([^;]+); do$', installer, re.M)
assert match, 'installer has no locale loop'
languages = match.group(1).split()
assert 'en_US' in languages and len(languages) == 11, languages
match = re.search(r'^expected=([0-9]+)$', installer, re.M)
assert match, 'installer has no upgrade target guard'
upgrade_targets = int(match.group(1))
expected = MANIFEST_ROWS + len(languages) + (len(languages) - 1)
assert upgrade_targets == expected == 62, (upgrade_targets, expected)
match = re.search(r'^\[ "\$FRESH" = 0 \] \|\| expected=([0-9]+)$', installer, re.M)
assert match and int(match.group(1)) == 63, match.group(1) if match else None

# Status reporting must use the single VERSION constant rather than a stale literal.
assert not re.search(r'\bversion=2\.\d', installer)
assert 'CHECK_OK version=%s' in installer and 'INSTALL_OK version=%s' in installer

# The immutable v2.12 release input is retained byte-for-byte beside the repaired identity.
historical = ROOT / 'release/v2.12-runtime.manifest'
assert historical.is_file() and sha256(historical) == HISTORICAL_MANIFEST_SHA

print('V2121_RELEASE_MANIFEST=PASS rows=%d payload_hashes=%d upgrade_targets=%d '
      'fresh_targets=%d' % (len(rows), len(rows), upgrade_targets, upgrade_targets + 1))
