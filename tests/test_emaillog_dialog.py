"""The View message dialog must use the standard OPNsense modal structure.

Reference: the installed core dialog in OPNsense/Firewall/alias.volt
(`#DialogAlias`): `modal fade` > `modal-dialog modal-lg` > `modal-content` with
`modal-header` (close button + `h4.modal-title`), `modal-body`, and scrolling
provided by the core `.modal-body` rule rather than page-local styles.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / 'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/emaillog.volt'
CORE = Path('/usr/local/opnsense/mvc/app/views/OPNsense/Firewall/alias.volt')
CORE_CSS = Path('/usr/local/opnsense/www/themes/opnsense/build/css/main.css')


def dialog(src):
    start = src.index('id="email-log-message-modal"')
    return src[src.rindex('<div', 0, start):src.index('{# ', start) if '{# ' in src[start:] else len(src)]


def test_structure_matches_core():
    src = VIEW.read_text(encoding='utf-8')
    block = src[src.index('id="email-log-message-modal"') - 40:src.index('</div>', src.index('id="email-log-message-timeline"')) + 400]
    for token in ('class="modal fade"', 'class="modal-dialog modal-lg"', 'class="modal-content"',
                  'class="modal-header"', 'class="modal-title"', 'class="modal-body"'):
        assert token in block, token
    assert 'role="dialog"' in block, 'dialog role missing'
    assert 'aria-labelledby="email-log-message-title"' in block, 'dialog must reference its title'
    assert 'class="close"' in block and 'data-dismiss="modal"' in block, 'close control must dismiss'
    assert 'aria-label=' in block, 'close control needs an accessible label'
    print('DIALOG_STRUCTURE=PASS')


def test_core_scrolling_is_reused_not_duplicated():
    src = VIEW.read_text(encoding='utf-8')
    body = src[src.index('id="email-log-message-body"'):]
    body = body[:body.index('</pre>')]
    assert 'max-height' not in body, 'body must not impose its own scroll height'
    assert 'overflow' not in body, 'body must not impose its own overflow'
    assert 'white-space:pre-wrap' in body, 'line breaks must be preserved'
    assert 'word-break:break-word' in body, 'long lines must wrap on narrow screens'
    if CORE_CSS.is_file():
        css = CORE_CSS.read_text(errors='ignore')
        assert '.modal-body' in css and 'overflow-y: auto' in css, 'core modal scrolling rule missing'
    print('DIALOG_SCROLLING=PASS')


def test_no_small_custom_typography():
    src = VIEW.read_text(encoding='utf-8')
    start = src.index('id="email-log-message-modal"')
    block = src[start:start + 3000]
    assert 'font-size:12px' not in block, 'no undersized custom font in the dialog'
    assert 'font-family:inherit' in block, 'body text inherits the theme font, not monospace'
    print('DIALOG_TYPOGRAPHY=PASS')


def test_plain_text_preserved():
    src = VIEW.read_text(encoding='utf-8')
    assert "$('#email-log-message-body').text(" in src, 'body must be rendered as text'
    assert "$('#email-log-message-body').html(" not in src, 'body must never be rendered as HTML'
    print('DIALOG_PLAINTEXT=PASS')


def test_keyboard_and_focus():
    src = VIEW.read_text(encoding='utf-8')
    assert 'tabindex="-1"' in src, 'dialog must be focusable for keyboard dismissal'
    assert "hidden.bs.modal" in src, 'focus must be restored when the dialog closes'
    print('DIALOG_FOCUS=PASS')


def test_core_reference_present():
    if not CORE.is_file():
        print('CORE_REFERENCE=SKIPPED')
        return
    core = CORE.read_text(encoding='utf-8', errors='ignore')
    assert 'modal fade' in core and 'modal-dialog modal-lg' in core
    print('CORE_REFERENCE=VERIFIED')


def main():
    test_core_reference_present()
    test_structure_matches_core()
    test_core_scrolling_is_reused_not_duplicated()
    test_no_small_custom_typography()
    test_plain_text_preserved()
    test_keyboard_and_focus()
    print('EMAIL_LOG_DIALOG_REGRESSION=PASS')


if __name__ == '__main__':
    main()
