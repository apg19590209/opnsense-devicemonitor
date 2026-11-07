"""DM-BL-008c/DM-BL-010: core-first catalogue merging repairs only missing header metadata.

Pure gettext fixtures in a temporary directory: no installed catalogue, no network and no
target host is touched. Covers both modes of release/merge-opnsense-catalog.sh and checks that
the merge guard fails closed instead of silently dropping a core translation. The DM-BL-010
cases reproduce a sparse core header, require a warning-free merge, preserve real core metadata,
and reject an incomplete plugin header or a malformed catalogue.
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

HEADER_FIELDS = [
    'Project-Id-Version: test',
    'PO-Revision-Date: 2026-09-26 00:00+0000',
    'Last-Translator: Test',
    'Language-Team: Test',
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=UTF-8',
    'Content-Transfer-Encoding: 8bit',
    'Language: es_ES',
    'Plural-Forms: nplurals=2; plural=(n != 1);',
]


def po_header(fields):
    return 'msgid ""\nmsgstr ""\n' + ''.join('"%s\\n"\n' % field for field in fields) + '\n'


HEADER = po_header(HEADER_FIELDS)
SPARSE_HEADER = po_header([
    field for field in HEADER_FIELDS
    if not field.startswith(('PO-Revision-Date:', 'Last-Translator:', 'Language-Team:'))
])

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


def assert_warning_free(result):
    assert 'warning:' not in result.stderr.lower(), result.stderr


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
    result = merge([core_mo, plugin_po, merged_mo])
    assert_warning_free(result)
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

    # 6. DM-BL-010: a sparse core header gains only the missing metadata from the complete
    #    plugin header. It must merge without the reporter's missing-field warnings, while
    #    every core translation and every plugin key remains unchanged.
    sparse_core_mo = stage / 'OPNsense-sparse.mo'
    compile_po(sparse_core_mo, (
        SPARSE_HEADER
        + 'msgid "System"\nmsgstr "Sistema"\n\n'
        + 'msgid "Device"\nmsgstr "Dispositivo existente"\n\n'
        + 'msgctxt "menu"\nmsgid "Services"\nmsgstr "Servicios del sistema"\n'
    ))
    sparse_merged_mo = stage / 'merged-sparse.mo'
    sparse_result = merge([sparse_core_mo, plugin_po, sparse_merged_mo])
    assert_warning_free(sparse_result)
    sparse = catalogue(sparse_merged_mo)
    sparse_info = sparse.info()
    assert sparse_info['po-revision-date'] == '2026-09-26 00:00+0000'
    assert sparse_info['last-translator'] == 'Test'
    assert sparse_info['language-team'] == 'Test'
    assert sparse.gettext('System') == 'Sistema'
    assert sparse.gettext('Device') == 'Dispositivo existente'
    assert sparse.pgettext('menu', 'Services') == 'Servicios del sistema'
    assert sparse.gettext('Port Discovery') == 'Descubrimiento de puertos'

    # 7. Metadata already present in the core catalogue is authoritative. The plugin has real,
    #    complete values but they differ, so a correct merge must preserve the core values.
    core_metadata_mo = stage / 'OPNsense-metadata.mo'
    compile_po(core_metadata_mo, (
        po_header([
            'Project-Id-Version: core',
            'PO-Revision-Date: 2025-01-02 03:04+0000',
            'Last-Translator: Original Core Translator',
            'Language-Team: Original Core Team',
            'MIME-Version: 1.0',
            'Content-Type: text/plain; charset=UTF-8',
            'Content-Transfer-Encoding: 8bit',
            'Language: es_ES',
            'Plural-Forms: nplurals=2; plural=(n != 1);',
        ])
        + 'msgid "System"\nmsgstr "Sistema original"\n'
    ))
    metadata_merged_mo = stage / 'merged-metadata.mo'
    metadata_result = merge([core_metadata_mo, plugin_po, metadata_merged_mo])
    assert_warning_free(metadata_result)
    metadata = catalogue(metadata_merged_mo).info()
    assert metadata['po-revision-date'] == '2025-01-02 03:04+0000'
    assert metadata['last-translator'] == 'Original Core Translator'
    assert metadata['language-team'] == 'Original Core Team'
    assert catalogue(metadata_merged_mo).gettext('System') == 'Sistema original'

    # 8. The repair never invents metadata: a plugin missing any of the three fields aborts.
    incomplete_plugin = stage / 'incomplete-plugin.po'
    incomplete_plugin.write_text(
        SPARSE_HEADER + 'msgid "Device"\nmsgstr "Dispositivo del plugin"\n',
        encoding='utf-8',
    )
    incomplete_output = stage / 'incomplete.mo'
    incomplete_result = merge(
        [sparse_core_mo, incomplete_plugin, incomplete_output], expect_success=False
    )
    assert 'plugin metadata field' in incomplete_result.stderr
    assert not incomplete_output.exists(), 'an incomplete header must leave no output'

    # 9. Genuinely invalid catalogues are rejected by the existing gettext validation.
    invalid_plugin = stage / 'invalid-plugin.po'
    invalid_plugin.write_text(HEADER + 'msgid "broken"\nmsgstr "unterminated\n', encoding='utf-8')
    invalid_plugin_output = stage / 'invalid-plugin.mo'
    merge([core_mo, invalid_plugin, invalid_plugin_output], expect_success=False)
    assert not invalid_plugin_output.exists(), 'an invalid plugin must leave no output'

    invalid_core = stage / 'invalid-core.mo'
    invalid_core.write_bytes(b'not a gettext catalogue\n')
    invalid_core_output = stage / 'invalid-core-output.mo'
    merge([invalid_core, plugin_po, invalid_core_output], expect_success=False)
    assert not invalid_core_output.exists(), 'an invalid core must leave no output'

print('LOCALE_MERGE=PASS')
