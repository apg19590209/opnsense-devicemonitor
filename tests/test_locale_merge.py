"""DM-BL-008c: the shared core catalogue keeps its translations and gains the plugin's keys.

Pure gettext fixtures in a temporary directory: no installed catalogue, no network and no
target host is touched. Covers both modes of release/merge-opnsense-catalog.sh and checks that
the merge guard fails closed instead of silently dropping a core translation.
"""
import gettext
from pathlib import Path
import os
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
MERGE = ROOT / 'release/merge-opnsense-catalog.sh'
MSGFMT = os.environ.get('MSGFMT', 'msgfmt')
SH = os.environ.get('SH', '/bin/sh')

HEADER = (
    'msgid ""\n'
    'msgstr "Project-Id-Version: test\\n'
    'PO-Revision-Date: 2026-09-26 00:00+0000\\n'
    'Last-Translator: Test\\n'
    'Language-Team: Test\\n'
    'MIME-Version: 1.0\\n'
    'Content-Type: text/plain; charset=UTF-8\\n'
    'Content-Transfer-Encoding: 8bit\\n'
    'Language: es_ES\\n'
    'Plural-Forms: nplurals=2; plural=(n != 1);\\n"\n\n'
)

PLUGIN_PO = (
    HEADER
    + 'msgid "Device"\nmsgstr "Dispositivo del plugin"\n\n'
    + 'msgid "Port Discovery"\nmsgstr "Descubrimiento de puertos"\n\n'
    + 'msgid "Open port"\nmsgid_plural "Open ports"\n'
    + 'msgstr[0] "Puerto abierto"\nmsgstr[1] "Puertos abiertos"\n'
)


def catalogue(path):
    with Path(path).open('rb') as stream:
        return gettext.GNUTranslations(stream)


def compile_po(path, text):
    po = Path(path).with_suffix('.po')
    po.write_text(text, encoding='utf-8')
    subprocess.run([MSGFMT, '-o', str(path), str(po)], check=True)
    return path


def merge(script_arguments, expect_success=True):
    result = subprocess.run(
        [SH, str(MERGE)] + [str(argument) for argument in script_arguments],
        capture_output=True, text=True,
    )
    if expect_success and result.returncode != 0:
        raise AssertionError(f'merge failed: {result.stdout}{result.stderr}')
    if not expect_success and result.returncode == 0:
        raise AssertionError('merge was expected to abort but succeeded')
    return result


with tempfile.TemporaryDirectory() as directory:
    stage = Path(directory)
    core_mo = stage / 'OPNsense.mo'
    plugin_po = stage / 'plugin.po'
    plugin_po.write_text(PLUGIN_PO, encoding='utf-8')

    # 1. Core-first merge: existing OPNsense values win, plugin-only keys are added.
    compile_po(core_mo, (
        HEADER
        + 'msgid "System"\nmsgstr "Sistema"\n\n'
        + 'msgid "Device"\nmsgstr "Dispositivo existente"\n\n'
        + 'msgctxt "menu"\nmsgid "Services"\nmsgstr "Servicios del sistema"\n'
    ))
    merged_mo = stage / 'merged.mo'
    merge([core_mo, plugin_po, merged_mo])
    merged = catalogue(merged_mo)
    assert merged.gettext('System') == 'Sistema'
    assert merged.gettext('Device') == 'Dispositivo existente', 'core value must win'
    assert merged.pgettext('menu', 'Services') == 'Servicios del sistema'
    assert merged.gettext('Port Discovery') == 'Descubrimiento de puertos'
    assert merged.ngettext('Open port', 'Open ports', 2) == 'Puertos abiertos'
    assert catalogue(core_mo).gettext('Device') == 'Dispositivo existente', 'input untouched'

    # 2. Re-merging an already merged catalogue is safe (reinstall over a merged testbed).
    merged_twice = stage / 'merged-twice.mo'
    merge([merged_mo, plugin_po, merged_twice])
    again = catalogue(merged_twice)
    assert again.gettext('Port Discovery') == 'Descubrimiento de puertos'
    assert again.gettext('Device') == 'Dispositivo existente'

    # 3. Plugin-only mode for a locale whose core catalogue is absent (nl_NL): the plugin
    #    catalogue alone, with no core input and no abort.
    plugin_only_mo = stage / 'plugin-only.mo'
    merge(['--plugin-only', plugin_po, plugin_only_mo])
    alone = catalogue(plugin_only_mo)
    assert alone.gettext('Port Discovery') == 'Descubrimiento de puertos'
    assert alone.gettext('Device') == 'Dispositivo del plugin'
    assert alone.ngettext('Open port', 'Open ports', 1) == 'Puerto abierto'
    assert alone.gettext('System') == 'System', 'no core string may leak in'
    assert catalogue(core_mo).gettext('System') == 'Sistema', 'the core input is untouched'

    # 4. The merge guard fails closed: an OPNsense key that would lose its value aborts.
    broken_core = stage / 'OPNsense-broken.mo'
    compile_po(broken_core, HEADER + 'msgid "System"\nmsgstr ""\n\n')
    merge([broken_core, plugin_po, stage / 'must-not-exist.mo'], expect_success=False)
    assert not (stage / 'must-not-exist.mo').exists(), 'a failed merge must leave no output'

    # 5. Both modes refuse to overwrite an existing output file.
    merge([core_mo, plugin_po, merged_mo], expect_success=False)
    merge(['--plugin-only', plugin_po, merged_mo], expect_success=False)

print('LOCALE_MERGE=PASS')
