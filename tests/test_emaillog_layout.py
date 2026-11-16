"""Email Log control alignment must stay scoped and consistent.

The type/status dropdowns rendered their text against the box edge next to the
search field and Export button. The fix is a page-scoped rule that gives those
four controls one height and centres the dropdown text, without touching shared
OPNsense styles.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / 'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/emaillog.volt'
SHARED_CSS = [
    '/usr/local/opnsense/www/themes/opnsense/build/css/main.css',
    '/usr/local/opnsense/www/themes/opnsense/build/css/dashboard.css',
]


def rule_block(src):
    return src[src.index('<style>'):src.index('</style>')]


def test_style_is_scoped_to_the_email_log_controls():
    src = VIEW.read_text(encoding='utf-8')
    css = rule_block(src)
    for selector in ('#email-log-search', '#email-log-type', '#email-log-status', '#email-log-export'):
        assert selector in css, f'{selector} missing from the scoped block'
    # No bare element or shared Bootstrap selector may be restyled.
    for bad in ('.form-control', '.input-sm', '.btn-sm', 'select {', 'input {'):
        assert bad not in css, f'shared selector {bad} must not be restyled'
    print('EMAIL_LOG_STYLE_SCOPED=PASS')


def test_controls_share_one_height():
    css = rule_block(VIEW.read_text(encoding='utf-8'))
    block = css[css.index('#email-log-search'):]
    assert re.search(r'height:\s*30px', block), 'one explicit height for all four controls'
    assert 'box-sizing: border-box' in block, 'padding must not change the outer height'
    print('EMAIL_LOG_CONTROL_HEIGHTS=PASS')


def test_dropdown_text_is_vertically_centred():
    css = rule_block(VIEW.read_text(encoding='utf-8'))
    # The second rule is the dropdown-only block (selectors then a brace block).
    rules = re.findall(r'([^{}]+)\{([^}]*)\}', css)
    dropdown = ''
    for selectors, body in rules:
        if '#email-log-type' in selectors and '#email-log-search' not in selectors:
            dropdown = body
    assert dropdown, 'no dropdown-specific rule found'
    # Native selects ignore line-height in some engines; zero symmetric padding
    # plus an explicit height is what actually centres the text.
    assert 'padding-top: 0' in dropdown and 'padding-bottom: 0' in dropdown, dropdown
    assert 'vertical-align: middle' in dropdown, dropdown
    print('EMAIL_LOG_DROPDOWN_CENTRED=PASS')


def test_default_and_selected_labels_present():
    src = VIEW.read_text(encoding='utf-8')
    assert re.search(r"<option value=\"\">\{\{ devicemonitor_t\('All types'\) \}\}</option>", src), \
        'All types default label missing'
    assert re.search(r"<option value=\"failed\">\{\{ devicemonitor_t\('Failed'\) \}\}</option>", src), \
        'Failed status label missing'
    print('EMAIL_LOG_LABELS_PRESENT=PASS')


def test_shared_opnsense_css_untouched():
    for path in SHARED_CSS:
        p = Path(path)
        if not p.is_file():
            continue
        body = p.read_text(encoding='utf-8', errors='ignore')
        assert 'email-log-type' not in body and 'email-log-status' not in body, \
            f'{path} must not reference the Email Log controls'
    print('OPNSENSE_SHARED_CSS_UNTOUCHED=PASS')


def main():
    test_style_is_scoped_to_the_email_log_controls()
    test_controls_share_one_height()
    test_dropdown_text_is_vertically_centred()
    test_default_and_selected_labels_present()
    test_shared_opnsense_css_untouched()
    print('EMAIL_LOG_LAYOUT_REGRESSION=PASS')


if __name__ == '__main__':
    main()
