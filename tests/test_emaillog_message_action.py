"""The View message action must be offered for every row.

The action was conditionally rendered only when row.has_content was true, so on a
log whose rows predate content capture the operator saw Timeline buttons alone.
Older rows must still open the modal, which then reports that the content is
unavailable.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / 'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/emaillog.volt'
CONTROLLER = ROOT / 'src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/EmaillogController.php'


def test_action_is_not_conditionally_hidden():
    src = VIEW.read_text(encoding='utf-8')
    assert 'if (row.has_content)' not in src, \
        'View message must not be gated on captured content'
    start = src.index("/* The single row action.")
    block = src[start:src.index('appendTo($detail)', start)]
    assert 'text.viewMessage' in block, 'button label missing'
    assert 'openMessage(row.event_id' in block, 'button must open the message modal'


def test_every_row_gets_the_button():
    src = VIEW.read_text(encoding='utf-8')
    # The row rendering loop builds one action cell per row; the button is added
    # unconditionally inside it, before the cell is appended.
    rows_loop = src[src.index('rows.forEach(function (row) {'):src.index('$body.append($tr)')]
    assert "data-event-id" in rows_loop, 'no per-row action identifier'
    assert 'openMessage' in rows_loop, 'no per-row open handler'


def test_one_row_action():
    """View message is the only row action; the delivery timeline opens with it."""
    src = VIEW.read_text(encoding='utf-8')
    row_at = src.index('rows.forEach(function (row) {')
    end_at = src.index("$('#email-log-empty')", row_at)
    loop = src[row_at:end_at]
    assert loop.count("<button>')") == 1, 'a second row button would duplicate the view'
    assert 'text.diagnostics' not in src, 'the separate Timeline action must be gone'
    assert "closest('tr').next()" not in src, 'no inline timeline row remains'
    assert 'text.viewMessage' in loop and 'openMessage(row.event_id' in loop


def test_unavailable_state_is_reachable():
    src = VIEW.read_text(encoding='utf-8')
    assert 'email-log-message-unavailable' in src, 'unavailable notice missing from the modal'
    assert 'text.unavailable' in src, 'unavailable wording not applied'
    ctrl = CONTROLLER.read_text(encoding='utf-8')
    assert "'content_available'" in ctrl, 'endpoint does not report content availability'
    assert "'content' => $hasContent" in ctrl, 'endpoint must not invent content'


def test_endpoint_answers_for_legacy_rows():
    """A legacy row returns ok with content_available false, not an error."""
    ctrl = CONTROLLER.read_text(encoding='utf-8')
    block = ctrl[ctrl.index('$hasContent ='):]
    block = block[:block.index("'timeline' => $timeline") + 20]
    assert 'content_available' in block and 'hasContent' in block


def main():
    test_action_is_not_conditionally_hidden()
    test_every_row_gets_the_button()
    test_one_row_action()
    test_unavailable_state_is_reachable()
    test_endpoint_answers_for_legacy_rows()
    print('EMAIL_LOG_MESSAGE_ACTION_REGRESSION=PASS')


if __name__ == '__main__':
    main()
