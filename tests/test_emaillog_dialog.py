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
    start = src.rindex('<div', 0, src.index('id="email-log-message-modal"'))
    block = src[start:src.index('class="modal-footer"') + 400]
    for token in ('class="modal fade"', 'class="modal-dialog modal-lg"', 'class="modal-content"',
                  'class="modal-header"', 'class="modal-title"', 'class="modal-body'):
        assert token in block, token
    assert 'role="dialog"' in block, 'dialog role missing'
    assert 'aria-labelledby="email-log-message-title"' in block, 'dialog must reference its title'
    assert 'class="close"' in block and 'data-dismiss="modal"' in block, 'close control must dismiss'
    assert 'aria-label=' in block, 'close control needs an accessible label'
    print('DIALOG_STRUCTURE=PASS')


def test_core_scrolling_is_reused_not_duplicated():
    src = VIEW.read_text(encoding='utf-8')
    css = src[src.index('<style>'):src.index('</style>')]
    pre = css[css.index('.email-log-dialog-reading pre'):]
    pre = pre[:pre.index('}')]
    assert 'max-height: none' in pre, 'reading area must not fix its height'
    assert 'overflow: visible' in pre, 'reading area must not scroll internally'
    assert 'white-space: pre-wrap' in pre, 'line breaks must be preserved'
    assert 'overflow-wrap: anywhere' in pre or 'word-break: break-word' in pre, 'long lines must wrap'
    if CORE_CSS.is_file():
        css = CORE_CSS.read_text(errors='ignore')
        assert '.modal-body' in css and 'overflow-y: auto' in css, 'core modal scrolling rule missing'
    print('DIALOG_SCROLLING=PASS')


def test_padded_body_and_sections():
    src = VIEW.read_text(encoding='utf-8')
    assert 'email-log-dialog-body' in src, 'padded body class missing'
    css = src[src.index('<style>'):src.index('</style>')]
    assert 'padding: 20px' in css, 'body padding missing'
    assert '#email-log-message-modal' in css, 'styles must be scoped to this dialog'
    # metadata, message and timeline all sit inside the modal body
    body = src[src.index('email-log-dialog-body'):src.index('class="modal-footer"')]
    for part in ('email-log-message-meta', 'email-log-message-body', 'email-log-message-timeline-disclosure'):
        assert part in body, f'{part} must be inside the modal body'
    assert '<hr/>' in body, 'divider between metadata and message'
    assert 'Message content' in body and 'Delivery timeline' in body, 'section headings missing'
    assert '<details' in body and '<summary>' in body, 'timeline must use standard disclosure'
    assert 'class="modal-footer"' in src and 'data-dismiss="modal"' in src, 'footer close button missing'
    print('DIALOG_LAYOUT=PASS')


def test_no_small_custom_typography():
    src = VIEW.read_text(encoding='utf-8')
    css = src[src.index('<style>'):src.index('</style>')]
    assert 'font-size: 12px' not in css, 'no undersized custom font'
    assert 'font-size: inherit' in css, 'reading area inherits theme typography'
    assert 'line-height: 1.5' in css, 'readable line spacing'
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
    test_padded_body_and_sections()
    test_no_small_custom_typography()
    test_plain_text_preserved()
    test_keyboard_and_focus()
    print('EMAIL_LOG_DIALOG_REGRESSION=PASS')


if __name__ == '__main__':
    main()
