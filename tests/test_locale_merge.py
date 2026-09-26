"""The shared catalogue keeps core translations and gains plugin-only strings."""
import gettext
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
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


def catalogue(path):
    with path.open('rb') as stream:
        return gettext.GNUTranslations(stream)


with tempfile.TemporaryDirectory() as directory:
    stage = Path(directory)
    core_po = stage / 'core.po'
    plugin_po = stage / 'plugin.po'
    core_mo = stage / 'OPNsense.mo'
    merged_mo = stage / 'merged.mo'
    core_po.write_text(
        HEADER
        + 'msgid "System"\nmsgstr "Sistema"\n\n'
        + 'msgid "Device"\nmsgstr "Dispositivo existente"\n\n'
        + 'msgctxt "menu"\nmsgid "Services"\nmsgstr "Servicios del sistema"\n',
        encoding='utf-8',
    )
    plugin_po.write_text(
        HEADER
        + 'msgid "Device"\nmsgstr "Dispositivo del plugin"\n\n'
        + 'msgid "Port Discovery"\nmsgstr "Descubrimiento de puertos"\n\n'
        + 'msgid "Open port"\nmsgid_plural "Open ports"\n'
        + 'msgstr[0] "Puerto abierto"\nmsgstr[1] "Puertos abiertos"\n',
        encoding='utf-8',
    )
    subprocess.run(['msgfmt', '-o', str(core_mo), str(core_po)], check=True)
    subprocess.run(
        ['/bin/sh', str(ROOT / 'release/merge-opnsense-catalog.sh'),
         str(core_mo), str(plugin_po), str(merged_mo)],
        check=True,
    )
    merged = catalogue(merged_mo)
    assert merged.gettext('System') == 'Sistema'
    assert merged.gettext('Device') == 'Dispositivo existente'
    assert merged.pgettext('menu', 'Services') == 'Servicios del sistema'
    assert merged.gettext('Port Discovery') == 'Descubrimiento de puertos'
    assert merged.ngettext('Open port', 'Open ports', 2) == 'Puertos abiertos'
    assert catalogue(core_mo).gettext('Device') == 'Dispositivo existente'

    # A second merge is safe when a testbed already has the plugin messages.
    merged_twice = stage / 'merged-twice.mo'
    subprocess.run(
        ['/bin/sh', str(ROOT / 'release/merge-opnsense-catalog.sh'),
         str(merged_mo), str(plugin_po), str(merged_twice)],
        check=True,
    )
    assert catalogue(merged_twice).gettext('Port Discovery') == 'Descubrimiento de puertos'

print('LOCALE_MERGE=PASS')
