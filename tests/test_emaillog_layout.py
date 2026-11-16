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


def test_no_custom_control_styling():
    """The page must not compensate for markup with fixed heights or padding."""
    src = VIEW.read_text(encoding='utf-8')
    css = src[src.index('<style>'):src.index('</style>')] if '<style>' in src else ''
    # Dialog reading-area rules may set max-height:none, but the page must never
    # impose fixed control sizing (e.g. height:30px) on standard controls.
    assert not re.search(r'(^|[;{\s])height:\s*\d', css), \
        'the page must not carry fixed control-height CSS'
    for bad in ('style="height', 'style="line-height', 'padding-top: 5px'):
        assert bad not in src, f'custom control sizing present: {bad}'
    print('EMAIL_LOG_NO_CUSTOM_CONTROL_CSS=PASS')


def test_selects_use_the_framework_widget():
    src = VIEW.read_text(encoding='utf-8')
    for ident in ('email-log-type', 'email-log-status'):
        block = src[src.index(f'id="{ident}"'):src.index('</select>', src.index(f'id="{ident}"'))]
        assert 'class="selectpicker"' in block, f'{ident} must use the standard selectpicker widget'
        assert 'form-control' not in block, f'{ident} must not mix raw form-control styling'
        assert 'data-style="btn-default btn-sm"' in block, f'{ident} must use the shared small-button style'
    print('EMAIL_LOG_SELECTPICKER_MARKUP=PASS')


def test_initialisation_follows_the_lifecycle():
    """bootstrap-select auto-initialises .selectpicker on window load; a page must
    neither double-initialise nor refresh static options per request."""
    src = VIEW.read_text(encoding='utf-8')
    assert ".selectpicker();" not in src, 'explicit initialisation would duplicate the plugin hook'
    assert ".selectpicker('refresh')" not in src, 'options are static; no per-request refresh'
    ready_at = src.index('$(document).ready(function () {')
    load_at = src.index('load();', ready_at)
    assert load_at > ready_at, 'the first request must still wait for ready (CSRF hook)'
    print('EMAIL_LOG_WIDGET_LIFECYCLE=PASS')


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


def test_control_inventory_has_one_shared_cause():
    """Every page's selects follow the framework widget, except deliberate
    page-specific width rules under container classes."""
    views = ROOT / 'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor'
    offenders = []
    for path in sorted(views.glob('*.volt')):
        src = path.read_text(encoding='utf-8')
        for m in re.finditer(r'<select[^>]*>', src):
            tag = m.group(0)
            if 'selectpicker' in tag or 'data-role' in tag:
                continue
            offenders.append((path.name, tag))
    assert not offenders, offenders
    print('CONTROL_INVENTORY_CONSISTENT=PASS')


def main():
    test_no_custom_control_styling()
    test_selects_use_the_framework_widget()
    test_initialisation_follows_the_lifecycle()
    test_default_and_selected_labels_present()
    test_shared_opnsense_css_untouched()
    test_control_inventory_has_one_shared_cause()
    print('EMAIL_LOG_LAYOUT_REGRESSION=PASS')


if __name__ == '__main__':
    main()
