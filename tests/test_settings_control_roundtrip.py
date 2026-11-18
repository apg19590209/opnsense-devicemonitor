"""Settings selects must keep their field names, values and round-trip.

The three selects converted to the framework widget (nmap_timing, email_method,
smtp_encryption) must still be read with .val() for loading and for the save
payload, and must still drive their change handlers. This is checked statically
against the template; no production setting is written.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / 'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt'
CONTROLS = {
    'nmap_timing': ['0', '1', '2', '3', '4', '5'],
    'email_method': ['sendmail', 'smtp'],
    'smtp_encryption': ['starttls', 'ssl', 'none'],
}


def select_block(src, ident):
    start = src.index(f'id="{ident}"')
    end = src.index('</select>', start)
    return src[start:end]


def test_widget_markup_and_option_values_preserved():
    src = VIEW.read_text(encoding='utf-8')
    for ident, values in CONTROLS.items():
        block = select_block(src, ident)
        assert 'class="selectpicker"' in block, f'{ident} must use the framework widget'
        assert 'form-control' not in block, f'{ident} must not mix raw form-control styling'
        found = re.findall(r'<option value="([^"]*)"', block)
        assert found == values, (ident, found, values)
    print('SETTINGS_CONTROL_VALUES=PASS')


def test_load_path_reads_and_refreshes():
    src = VIEW.read_text(encoding='utf-8')
    for ident in CONTROLS:
        assert re.search(rf"\$\('#{ident}'\)\.val\(", src), f'{ident} load path missing'
        assert re.search(rf"\$\('#{ident}'\)\.selectpicker\('refresh'\)", src), \
            f'{ident} needs a refresh after programmatic val()'
    print('SETTINGS_LOAD_ROUNDTRIP=PASS')


def test_save_payload_keys_unchanged():
    src = VIEW.read_text(encoding='utf-8')
    for ident in CONTROLS:
        assert re.search(rf"^\s*{ident}:\s+\$\('#{ident}'\)\.val\(\),", src, re.M), \
            f'{ident} missing from the save payload'
    print('SETTINGS_SAVE_PAYLOAD=PASS')


def test_change_handler_preserved():
    src = VIEW.read_text(encoding='utf-8')
    assert re.search(r"\$\('#email_method'\)\.change\(toggleEmailMethod\)", src), \
        'email_method change handler removed'
    assert 'function toggleEmailMethod' in src, 'toggleEmailMethod definition missing'
    print('SETTINGS_CHANGE_HANDLER=PASS')


def main():
    test_widget_markup_and_option_values_preserved()
    test_load_path_reads_and_refreshes()
    test_save_payload_keys_unchanged()
    test_change_handler_preserved()
    print('SETTINGS_CONTROL_ROUNDTRIP=PASS')


if __name__ == '__main__':
    main()
