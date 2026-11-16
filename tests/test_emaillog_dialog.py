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
                  'class="modal-header', 'class="modal-title"', 'class="modal-body'):
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
    assert 'Message content' in body and "devicemonitor_t('Delivery details')" in body, 'section headings missing'
    assert 'email-log-message-timeline-disclosure' in body, 'delivery disclosure missing'
    src_all = src
    assert "$('#email-log-message-title').text(m.subject" in src_all, \
        'the subject must become the dialog heading'
    for label in ("Recipient", "Node", "Time (UTC)", "Type", "Status"):
        assert f"['{label}'" in src_all, f'{label} missing from metadata'
    print('DIALOG_SUBJECT_AND_META=PASS')
    assert 'class="modal-footer"' in src and 'data-dismiss="modal"' in src, 'footer close button missing'
    print('DIALOG_LAYOUT=PASS')


def test_no_small_custom_typography():
    src = VIEW.read_text(encoding='utf-8')
    css = src[src.index('<style>'):src.index('</style>')]
    assert 'font-size: 12px' not in css, 'no undersized custom font'
    assert 'font-size: inherit' in css, 'reading area inherits theme typography'
    assert 'line-height: 1.5' in css, 'readable line spacing'
    print('DIALOG_TYPOGRAPHY=PASS')


def test_spacing_specification():
    src = VIEW.read_text(encoding='utf-8')
    css = src[src.index('<style>'):src.index('</style>')]
    def block(selector):
        i = css.index(selector)
        return css[i:css.index('}', i)]
    header = block('.modal-header {')
    assert 'padding: 20px' in header, 'header needs 20px padding'
    assert 'padding-right: 56px' in header, 'space between subject and close control'
    assert 'padding: 24px' in block('.email-log-dialog-body {'), 'body needs 24px padding'
    meta_dt = block('.email-log-dialog-meta dt {')
    meta_dd = block('.email-log-dialog-meta dd {')
    assert 'margin-bottom: 8px' in meta_dd, '8px between metadata rows'
    assert 'margin-left: 156px' in meta_dd and 'width: 140px' in meta_dt, '16px between label and value'
    assert 'margin-bottom: 24px' in block('.email-log-dialog-reading {'), '24px after the message'
    assert 'padding: 20px' in block('.email-log-dialog-reading {'), 'reading area needs 20px padding'
    i = css.rindex('#email-log-message-modal .modal-footer {')
    footer = css[i:css.index('}', i)]
    assert 'padding: 16px 24px' in footer, 'footer needs 16px/24px padding'
    dialog = block('.modal-dialog {')
    assert 'width: 800px' in dialog and 'calc(100vw - 32px)' in dialog, '800px width with viewport clearance'
    assert 'line-height: 1.5' in block('.email-log-dialog-reading pre'), '1.5 line spacing'
    assert '@media (max-width: 767px)' in css, 'narrow layout must stack labels'
    print('DIALOG_SPACING=PASS')


def test_header_clears_fixed_navigation():
    src = VIEW.read_text(encoding='utf-8')
    css = src[src.index('<style>'):src.index('</style>')]
    def block(selector):
        i = css.index(selector)
        return css[i:css.index('}', i)]
    # The overlay must paint above the fixed page head. Core main.css gives the
    # navbar z-index 1030 and .modal 1050, but the navbar is a document-order list
    # item painted before the transformed .modal, so it wins at equal origin.
    assert re.search(r'#email-log-message-modal \{\s*z-index:\s*1200;', css), \
        'dialog overlay must sit above the fixed navigation'
    if CORE_CSS.is_file():
        core = CORE_CSS.read_text(errors='ignore')
        assert '.navbar-fixed-top' in core and 'z-index: 1030' in core, 'navbar stacking input changed'
        assert 'margin: 62px 10px 10px 10px' in core, 'core dialog margin changed'
    dialog = block('.modal-dialog {')
    margin_top = int(re.search(r'margin: (\d+)px auto', dialog).group(1))
    head_height = 70
    assert margin_top >= head_height + 16, 'dialog must start below the 70px head plus clearance'
    assert 'calc(100vh - 102px)' in dialog, 'dialog height capped to the viewport below the head'
    content = block('.modal-content {')
    assert 'display: flex' in content and 'flex-direction: column' in content, \
        'content must lay out header/body/footer as a column'
    assert 'calc(100vh - 102px)' in content, 'content capped to the remaining viewport'
    body = block('.modal-body {')
    assert 'overflow-y: auto' in body and 'min-height: 0' in body, 'only the body scrolls'
    assert not re.search(r'(^|[;{\s])height:', body), 'body must not fix its height'
    grouping = css[css.index('modal-header,\n    #email-log-message-modal .modal-footer {'):]
    assert 'flex: none' in grouping[:grouping.index('}')], 'header and footer stay fixed while the body scrolls'
    close = block('.modal-header .close {')
    assert 'float: right' in close, 'close control floats clear of a wrapping subject'
    header = block('.modal-header {')
    assert 'padding-right: 56px' in header, 'subject keeps clear of the close control'
    assert 'overflow-wrap: anywhere' in block('.modal-header .modal-title {'), 'long subjects wrap'
    assert 'max-width: calc(100vw - 32px)' in dialog, 'narrow viewport clearance'
    narrow = css[css.index('@media (max-width: 767px)'):]
    assert 'calc(100vh - 86px)' in narrow, 'narrow viewport height cap'
    print('DIALOG_HEADER_VISIBLE=PASS')


def test_delivery_disclosure_pattern():
    src = VIEW.read_text(encoding='utf-8')
    start = src.index('id="email-log-message-timeline-disclosure"')
    block = src[start:src.index('id="email-log-message-timeline"', start)]
    tag_start = src.rindex('<button', 0, start)
    tag = src[tag_start:src.index('>', start) + 1]
    assert 'type="button"' in tag, 'disclosure must be a real button'
    assert 'aria-expanded="false"' in tag, 'collapsed state exposed'
    assert 'aria-controls="email-log-message-timeline-panel"' in tag, 'button names what it expands'
    assert 'glyphicon-chevron-right' in block, 'chevron indicator present'
    assert '<details' not in block and '<summary' not in block, 'summary is not the established pattern'
    panel = src[src.index('id="email-log-message-timeline-panel"') - 30:]
    panel_tag = src[src.rindex('<div', 0, src.index('id="email-log-message-timeline-panel"')):]
    panel_tag = panel_tag[:panel_tag.index('>') + 1]
    assert 'hidden' in panel_tag, 'expanded content starts hidden'
    css = src[src.index('<style>'):src.index('</style>')]
    disc = css[css.index('.email-log-dialog-disclosure {'):]
    disc = disc[:disc.index('}')]
    assert 'font-size: inherit' in disc, 'normal-size text, not a small label'
    assert 'cursor: pointer' in disc, 'the whole heading is clickable'
    assert 'width: 100%' in disc, 'the whole heading row is the target'
    assert not re.search(r'font-size:\s*1[0-2]px', disc), 'no undersized label'
    assert 'transform: rotate(90deg)' in css, 'chevron reflects expanded state'
    js = src[src.index('function setTimelineExpanded'):src.index('function openMessage')]
    assert "attr('aria-expanded'" in js, 'activated state is reflected in aria-expanded'
    assert ".prop('hidden', !on)" in js, 'panel visibility follows the state'
    # The label and chevron are driven from the same state, never set independently.
    assert "text(on ?" not in js and "hideDelivery" not in js, \
        'the heading text is stable; only the state drives the chevron'
    assert 'aria-expanded="true"] .glyphicon' in css and 'rotate(90deg)' in css, \
        'the chevron follows aria-expanded in CSS'
    assert "$('#email-log-message-timeline-disclosure').on('click'" in src, 'click activates'
    assert 'setTimelineExpanded(false)' in src, 'each open starts collapsed'
    assert 'id="email-log-message-timeline-count"' in src, 'event count placeholder present'
    assert "'(' + count + ' ' + label + ')'" in js, 'the count is rendered in the heading, e.g. (3 events)'
    assert "count === 1 ? text.eventSingular : text.eventPlural" in js, \
        'one event is singular, several are plural'
    assert "lang.query('event')" in src and "lang.query('events')" in src, 'both labels are translated'
    assert "devicemonitor_t('Delivery details')" in src, 'heading text is the translated Delivery details'
    assert 'noDelivery' in src and 'No delivery details recorded' in src, 'empty wording translated'
    assert 'id="email-log-message-no-delivery"' in src and 'hidden' in \
        src[src.index('id="email-log-message-no-delivery"'):src.index('id="email-log-message-no-delivery"') + 160], \
        'the no-events statement starts hidden'
    assert "$('#email-log-message-delivery').prop('hidden', steps.length === 0)" in src, \
        'no expansion control when there are no events'
    assert "$('#email-log-message-no-delivery').prop('hidden', steps.length > 0)" in src, \
        'the empty statement replaces the control'
    assert 'steps.forEach' in src, 'one row per event'
    for part in ('email-log-event-time', 'step.stage', 'step.status', 'step.detail', 'step.source'):
        assert part in src, f'event row misses {part}'
    assert 'steps.forEach' in src and 'forEach' in src, 'events keep the recorded order'
    print('DIALOG_DISCLOSURE=PASS')


def test_one_row_action_opens_everything():
    src = VIEW.read_text(encoding='utf-8')
    start = src.index('rows.forEach(function (row) {')
    loop = src[start:src.index("$('#email-log-empty')", start)]
    assert loop.count("$('<button>')") == 2, \
        'View message plus exactly one Delete/Restore control per row'
    assert loop.count("openMessage(") == 1, 'only View message opens the dialog'
    assert "data-action" in loop and 'confirmVisibility' in loop, 'Delete/Restore is its own action'
    assert 'text.diagnostics' not in loop and "'Timeline'" not in loop, 'no separate Timeline action'
    assert "<tr>').hide()" not in loop and 'closest(\'tr\').next()' not in loop, \
        'no inline table timeline expansion'
    assert 'openMessage(row.event_id, row.scope === \'peer\')' in loop, \
        'peer rows must retrieve from the peer'
    assert 'text.viewMessage' in loop, 'the single action is View message'
    # metadata, content and the full timeline all come from one lookup in the dialog
    dlg = src[src.index('function openMessage'):]
    for part in ('email-log-message-meta', 'email-log-message-body', 'email-log-message-timeline', 'm.timeline'):
        assert part in dlg, f'{part} missing from the dialog'
    print('DIALOG_ONE_MESSAGE_VIEW=PASS')


def test_clear_filters_and_visibility():
    src = VIEW.read_text(encoding='utf-8')
    assert 'id="email-log-clear"' in src, 'Clear filters button missing'
    clear_at = src.index("$('#email-log-clear').on('click'")
    body = src[clear_at:src.index('});', clear_at) + 3]
    for control in ('#email-log-search', '#email-log-type', '#email-log-status'):
        assert control in body and ".val('')" in body, f'{control} must be reset'
    assert 'page = 1' in body, 'pagination returns to page one'
    assert body.count('load()') == 1, 'exactly one refresh'
    assert 'email-log-visibility' not in body, 'the visibility choice is not a search filter'
    assert "scope =" not in body, 'the Local/Peer/All scope is preserved'
    vis = src[src.index('id="email-log-visibility"'):]
    vis = vis[:vis.index('</select>')]
    assert 'value="active" selected' in vis and 'value="deleted"' in vis and 'value="all"' in vis, \
        'Active/Deleted/All visibility with Active as the default'
    assert "visibility: $('#email-log-visibility').val()" in src, 'filters carry the visibility'
    print('DIALOG_CLEAR_AND_VISIBILITY=PASS')


def test_soft_delete_controls():
    src = VIEW.read_text(encoding='utf-8')
    confirm = ("Remove this entry from the active log? Its message and delivery history will be "
               "retained under the existing retention policy.")
    assert confirm in src, 'the approved confirmation wording must be shown verbatim'
    assert 'email-log-delete-modal' in src and 'modal fade' in src, 'standard confirmation dialog'
    assert "data-dismiss=\"modal\"" in src[src.index('email-log-delete-modal'):], 'confirmation can be cancelled'
    assert ".prop('disabled', remote)" in src, 'remote rows disable delete/restore'
    assert 'remoteLocked' in src and 'aria-describedby' in src, 'remote explanation reaches assistive tech'
    assert "'/api/devicemonitor/emaillog/delete'" in src and "'/api/devicemonitor/emaillog/restore'" in src
    assert 'changeVisibility' in src and 'confirmVisibility' in src
    code = '\n'.join(ln for ln in src.splitlines()
                     if not ln.strip().startswith(('*', '/*', '//', '<!--', '{#')))
    for forbidden in ('postfix', 'postsuper', 'postqueue', '/mail', 'mailq'):
        assert forbidden not in code.lower(), f'the page must not touch {forbidden}'
    print('DIALOG_SOFT_DELETE=PASS')


def test_retrieval_errors_and_no_send():
    src = VIEW.read_text(encoding='utf-8')
    open_at = src.index('function openMessage')
    err_at = src.index('function showMessageError')
    dlg = src[min(open_at, err_at):]
    assert 'id="email-log-message-error"' in src and 'role="alert"' in src, 'dialog error surface missing'
    assert 'showMessageError' in dlg and "' (HTTP '" in dlg, \
        'HTTP failures are reported in the dialog'
    assert "data && data.message ? ': ' + data.message" in dlg, \
        'the API reason is shown, not only a generic failure'
    for forbidden in ('/notify', 'sendemail', 'testemail', 'sendmail'):
        assert forbidden not in dlg.lower(), f'opening the dialog must not invoke {forbidden}'
    ctrl = (ROOT / 'src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/EmaillogController.php').read_text()
    for action in ('messageAction', 'peermessageAction', 'peermessageviewAction'):
        block = ctrl[ctrl.index(f'function {action}('):]
        block = block[:block.index('\n    }\n')]
        for forbidden in ('EmailTransport', 'mail(', 'NotificationHandler', 'sendCustomEmail'):
            assert forbidden not in block, f'{action} must be read-only'
    print('DIALOG_NO_SEND=PASS')


def test_legacy_rows_keep_delivery():
    src = VIEW.read_text(encoding='utf-8')
    dlg = src[src.index('function openMessage'):]
    started = dlg.index("$('#email-log-message-unavailable')")
    block = dlg[started:started + 400]
    assert "prop('hidden', !!m.content_available)" in block, 'legacy rows show the explanation'
    assert 'is-unavailable' in block and 'is-unavailable' in src[:src.index('function emailLogText')], \
        'the empty reading area is hidden rather than left as an empty box'
    assert "m.timeline" in dlg, 'the delivery record is read for legacy rows too'
    assert "'.email-log-dialog-reading'" in block, 'reading area toggled, not removed'
    print('DIALOG_LEGACY_CONTENT=PASS')


def test_header_reuses_the_panel_header_style():
    """The subject header takes the theme's panel-header background, not a colour."""
    src = VIEW.read_text(encoding='utf-8')
    start = src.index('id="email-log-message-modal"')
    dialog = src[src.rindex('<div', 0, start):]
    header = dialog[dialog.index('class="modal-header'):]
    header = header[:header.index('>')]
    assert 'panel-heading' in header, 'header must reuse the framework panel-header class'
    css = src[src.index('<style>'):src.index('</style>')]
    assert 'background' not in css[css.index('.modal-header {'):css.index('}', css.index('.modal-header {'))], \
        'no page-local header background'
    assert 'linear-gradient' not in css and 'rgba(0, 0, 0, 0.0' not in css, 'no gradients or hand-mixed colours'
    if CORE_CSS.is_file():
        light = CORE_CSS.read_text(errors='ignore')
        assert '.panel-default > .panel-heading {' in light and 'background-color: #f5f5f5' in light, \
            'light theme panel-header rule missing'
        dark = Path('/usr/local/opnsense/www/themes/opnsense-dark/build/css/main.css')
        if dark.is_file():
            d = dark.read_text(errors='ignore')
            block = d[d.index('.panel-default > .panel-heading {'):]
            block = block[:block.index('}')]
            assert 'background-color: rgb(' in block and 'color:' in block, \
                'dark theme must supply its own header background and paired text colour'
    print('DIALOG_HEADER_THEME=PASS')


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
    test_header_reuses_the_panel_header_style()
    test_header_clears_fixed_navigation()
    test_delivery_disclosure_pattern()
    test_one_row_action_opens_everything()
    test_clear_filters_and_visibility()
    test_soft_delete_controls()
    test_retrieval_errors_and_no_send()
    test_legacy_rows_keep_delivery()
    test_no_small_custom_typography()
    test_spacing_specification()
    test_plain_text_preserved()
    test_keyboard_and_focus()
    print('EMAIL_LOG_DIALOG_REGRESSION=PASS')


if __name__ == '__main__':
    main()
