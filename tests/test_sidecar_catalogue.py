"""Prove the sidecar chain resolves through the <locale>/LC_MESSAGES layout, locally.

Compiles the real plugin catalogues into the layout devicemonitor_locale.inc binds, adds a
stand-in core OPNsense domain with deliberately hostile content, and asserts precedence,
the toggle, the msgid fallback and HTML escaping. No browser, no network, no target host.
"""
import gettext
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / 'tests/sidecar_translate_probe.php'
LANGUAGES = ROOT / 'src/opnsense/mvc/app/languages'
PHP = os.environ.get('PHP', 'php')
MSGFMT = os.environ.get('MSGFMT', 'msgfmt')
SIDECAR_LOCALE = 'fr_FR'
CORE_ONLY_LOCALE = 'de_DE'
KEY = 'Total Devices'
UNKNOWN_KEY = 'This string is not in any Device Monitor catalogue'
HOSTILE = 'L\'équipement "cité" & <script>alert(1)</script>\nfin'

failures = []


def fail(message):
    print(f'FAIL: {message}')
    failures.append(message)


def php_escape(text):
    """PHP htmlspecialchars(ENT_QUOTES | ENT_HTML401) with newlines as &#10;."""
    escaped = (text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
               .replace('"', '&quot;').replace("'", '&#039;'))
    return escaped.replace('\n', '&#10;')


def compile_po(po, mo):
    mo.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([MSGFMT, '--check', '--check-format', str(po), '-o', str(mo)], check=True)


def po_quote(text):
    """C-string escaping for a generated .po entry."""
    return '"' + text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


def catalogue_value(po, key):
    with tempfile.TemporaryDirectory(prefix='dm-sidecar-value-') as tmp:
        mo = Path(tmp) / 'catalogue.mo'
        compile_po(po, mo)
        with mo.open('rb') as stream:
            return gettext.GNUTranslations(stream).gettext(key)


def probe(locale, sidecar_dir, core_dir, enabled):
    result = subprocess.run(
        [PHP, str(PROBE)],
        input=json.dumps({
            'locale': locale,
            'sidecar_dir': str(sidecar_dir),
            'core_dir': str(core_dir),
            'enabled': enabled,
            'keys': [KEY, UNKNOWN_KEY, HOSTILE],
        }),
        text=True, capture_output=True, encoding='utf-8',
        env={**os.environ, 'DM_PROBE_TOGGLE': '1' if enabled else '0'},
    )
    if result.returncode != 0:
        raise RuntimeError(f'{locale}: {result.stdout}{result.stderr}')
    return json.loads(result.stdout)


sidecar_po = LANGUAGES / SIDECAR_LOCALE / 'LC_MESSAGES' / 'devicemonitor.po'
assert sidecar_po.is_file(), sidecar_po
flat_layout = sorted(LANGUAGES.glob('*_devicemonitor.po'))
if flat_layout:
    fail(f'flat catalogue layout still present in the source tree: {[p.name for p in flat_layout]}')
sidecar_expected = catalogue_value(sidecar_po, KEY)
assert sidecar_expected != KEY, 'the fixture catalogue does not translate the probe key'

with tempfile.TemporaryDirectory(prefix='dm-sidecar-') as tmp:
    tmp = Path(tmp)
    sidecar_dir = tmp / 'sidecar'
    core_dir = tmp / 'core'

    # The plugin catalogue exists for one locale only: the other must fall through.
    compile_po(sidecar_po, sidecar_dir / SIDECAR_LOCALE / 'LC_MESSAGES' / 'devicemonitor.mo')

    core_po = tmp / f'{CORE_ONLY_LOCALE}.po'
    core_po.write_text(
        'msgid ""\n'
        'msgstr ""\n'
        '"Content-Type: text/plain; charset=UTF-8\\n"\n'
        '\n'
        f'msgid {po_quote(KEY)}\n'
        f'msgstr {po_quote(HOSTILE)}\n',
        encoding='utf-8',
    )
    for locale in (SIDECAR_LOCALE, CORE_ONLY_LOCALE):
        compile_po(core_po, core_dir / locale / 'LC_MESSAGES' / 'OPNsense.mo')

    print(f'fixture: sidecar {SIDECAR_LOCALE}={sidecar_expected!r}  core={HOSTILE!r}')

    enabled = probe(SIDECAR_LOCALE, sidecar_dir, core_dir, enabled=True)
    if not enabled['sidecar_enabled']:
        fail('the binder reported the sidecar disabled while the toggle is "1"')
    if not enabled['bound']:
        fail('devicemonitor_bind_sidecar() did not bind the domain')
    if enabled['locale'] not in (f'{SIDECAR_LOCALE}.UTF-8', 'C'):
        print(f'note: active locale is {enabled["locale"]!r}')

    value = enabled['values'][KEY]
    if value['t'] != php_escape(sidecar_expected):
        fail(f'{SIDECAR_LOCALE} enabled: expected the sidecar catalogue '
             f'{php_escape(sidecar_expected)!r}, got {value["t"]!r}')
    if value['raw'] != sidecar_expected:
        fail(f'{SIDECAR_LOCALE} enabled: raw value should be {sidecar_expected!r}, got {value["raw"]!r}')

    core_only = probe(CORE_ONLY_LOCALE, sidecar_dir, core_dir, enabled=True)
    core_only_value = core_only['values'][KEY]
    if core_only_value['t'] != php_escape(HOSTILE):
        fail(f'{CORE_ONLY_LOCALE} enabled: no plugin catalogue, expected the core domain value '
             f'{php_escape(HOSTILE)!r}, got {core_only_value["t"]!r}')
    if core_only_value['raw'] != HOSTILE:
        fail(f'{CORE_ONLY_LOCALE} enabled: the raw value must stay unescaped for script '
             f'contexts, got {core_only_value["raw"]!r}')

    disabled = probe(SIDECAR_LOCALE, sidecar_dir, core_dir, enabled=False)
    if disabled['sidecar_enabled']:
        fail('the binder ignored sidecar_translation_enabled = "0"')
    if disabled['bound']:
        fail('devicemonitor_bind_sidecar() bound the domain while disabled')
    disabled_value = disabled['values'][KEY]
    if disabled_value['t'] != php_escape(HOSTILE):
        fail(f'{SIDECAR_LOCALE} disabled: expected the core domain value '
             f'{php_escape(HOSTILE)!r}, got {disabled_value["t"]!r}')

    for label, payload in (('enabled', enabled), ('disabled', disabled), ('core-only', core_only)):
        unknown = payload['values'][UNKNOWN_KEY]
        if unknown['t'] != UNKNOWN_KEY or unknown['raw'] != UNKNOWN_KEY:
            fail(f'{label}: an unknown msgid must fall back to the msgid itself, got {unknown!r}')
        hostile = payload['values'][HOSTILE]
        if hostile['t'] != php_escape(HOSTILE) or hostile['raw'] != HOSTILE:
            fail(f'{label}: a msgid with markup must be escaped only in the HTML path, got {hostile!r}')

if failures:
    print(f'SIDECAR_CATALOGUE=FAIL failures={len(failures)}')
    sys.exit(1)
print('SIDECAR_CATALOGUE=PASS locales=2 toggle=both fallback=core msgid-fallback=ok escaping=matched')
