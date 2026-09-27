"""Compile real catalogues and parse rendered inline JS, without app/network access."""
import gettext
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
VIEWS = ROOT / 'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor'
LANGUAGES = ROOT / 'src/opnsense/mvc/app/languages'
RENDERER = ROOT / 'tests/render_translated_javascript.php'
NODE = os.environ.get('NODE', 'node')
PHP = os.environ.get('PHP', 'php')
parser = argparse.ArgumentParser()
parser.add_argument('--render-dir', type=Path, help='Export rendered scripts for syntax checks on another host')
args = parser.parse_args()
if args.render_dir:
    args.render_dir.mkdir(parents=True, exist_ok=True)
scripts = []
keys = set()
for view in sorted(VIEWS.glob('*.volt')):
    for index, script in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>', view.read_text(), re.S)):
        scripts.append((view.name, index, script))
        for literal in re.findall(r"lang\._\(('(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\")\)", script):
            # Current gettext keys use standard quoted strings; PHP decodes them in the renderer.
            keys.add(literal[1:-1].replace("\\'", "'").replace('\\"', '"').replace('\\\\', '\\'))
assert scripts and keys

def verify(label, translations):
    for name, index, script in scripts:
        result = subprocess.run(
            [PHP, str(RENDERER)], input=json.dumps({'script': script, 'translations': translations}),
            text=True, capture_output=True, encoding='utf-8'
        )
        assert result.returncode == 0, f'{label}/{name}: {result.stdout}{result.stderr}'
        rendered = result.stdout
        assert not re.search(r'</script', rendered, re.I), (label, name, 'script boundary injection')
        if args.render_dir:
            (args.render_dir / f'{label}-{name}-{index}.js').write_text(rendered, encoding='utf-8')
            continue
        result = subprocess.run([NODE, '--check'], input=rendered, text=True,
                                capture_output=True, encoding='utf-8')
        assert result.returncode == 0, f'{label}/{name}/{index}: {result.stderr}'
    print(f'{label}: {len(scripts)} script blocks ' + ('RENDERED' if args.render_dir else 'PASS'))

with tempfile.TemporaryDirectory(prefix='dm-translated-js-') as tmp:
    for po in sorted(LANGUAGES.glob('*_devicemonitor.po')):
        mo = Path(tmp) / 'catalogue.mo'
        subprocess.run(['msgfmt', '--check', '--check-format', str(po), '-o', str(mo)], check=True)
        with mo.open('rb') as stream:
            catalogue = gettext.GNUTranslations(stream)
        verify(po.stem, {key: catalogue.gettext(key) for key in keys})

hostile = "L'identité \"quoted\" \\ path\nnext\rline\t</script><script>throw Error('injected')</script>&\u2028\u2029 日本語"
verify('quotes-backslashes-newlines-script-tags-unicode', {key: hostile for key in keys})
print('TRANSLATED_JAVASCRIPT=' + ('RENDERED (syntax check still required)' if args.render_dir else 'PASS'))
