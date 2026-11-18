"""One shared column layout and a scope-accurate banner for the Email Log.

Local, Peer and All nodes must share identical column boundaries at the same
viewport: the markup carries a colgroup and fixed layout, values wrap instead of
being clipped, actions stay inside their column, the table sits in the standard
responsive container, and the All-nodes banner describes both nodes.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / 'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/emaillog.volt'
FAILS = []


def check(cond, label):
    print(('  PASS ' if cond else '  FAIL ') + label)
    if not cond:
        FAILS.append(label)


def css_block(src):
    return src[src.index('<style>'):src.index('</style>')]


def test_shared_layout():
    src = VIEW.read_text(encoding='utf-8')
    check('<colgroup>' in src, 'table declares a colgroup')
    cols = re.findall(r'<col class="(email-log-col-[a-z]+)"/>', src)
    check(cols == ['email-log-col-select', 'email-log-col-time', 'email-log-col-node',
                   'email-log-col-type', 'email-log-col-recipient', 'email-log-col-subject',
                   'email-log-col-status'], f'column order {cols}')
    css_total = css_block(src)
    widths_sum = sum(int(w) for w in re.findall(r'email-log-col-[a-z]+ \{ width: (\d+)%; \}', css_total))
    check(widths_sum == 100, f'selection column does not change the 100% total (got {widths_sum})')
    css = css_block(src)
    check('table-layout: fixed' in css, 'fixed table layout')
    widths = {}
    for name in cols:
        m = re.search(re.escape('.' + name) + r' \{ width: (\d+)%; \}', css)
        check(m is not None, f'{name} has a relative width')
        if m:
            widths[name] = int(m.group(1))
    total = sum(widths.values())
    check(abs(total - 100) <= 1, f'widths total 100% (got {total})')
    check(widths.get('email-log-col-subject', 0) >= widths.get('email-log-col-status', 100),
          'subject column is at least as wide as status')
    check('min-width: 720px' in css, 'narrow viewports keep a readable minimum width')
    check('font-size' not in css.split('#email-log-table.email-log-table')[1].split('@media')[0],
          'no font shrinking to force alignment')


def test_wrapping_and_responsive_container():
    src = VIEW.read_text(encoding='utf-8')
    css = css_block(src)
    table_css = css[css.index('#email-log-table.email-log-table td,'):]
    table_css = table_css[:table_css.index('}')]
    check('overflow-wrap: break-word' in table_css, 'long tokens break instead of clipping')
    check('word-break: normal' in table_css, 'text wraps at word boundaries, not per character')
    check('white-space: normal' in css[css.index('.email-log-subject {'):][:400],
          'the clickable subject wraps naturally')
    check('class="table-responsive"' in src, 'table uses the standard responsive container')
    check('display: none' not in css.split('#email-log-table.email-log-table')[1].split('@media')[0],
          'no content is hidden to force alignment')


def test_actions_are_inline():
    src = VIEW.read_text(encoding='utf-8')
    check("<td>').addClass('email-log-actions" not in src, 'no separate actions cell')
    check('email-log-subject' in src and 'email-log-restore' in src,
          'subject action and inline restore exist')
    row = src[src.index('rows.forEach(function (row)'):src.index('$body.append($tr)')]
    check("if (deleted && $('#email-log-visibility').val() !== 'active')" in row,
          'restore appears only for deleted rows in the Deleted/All views')
    check(".prop('disabled', remote)" in row, 'remote restore stays disabled')
    check("formatTimestamp(row.created_utc, row.created_local)" in src,
          'time keeps its date-aware suffix')


def test_banner_follows_scope():
    src = VIEW.read_text(encoding='utf-8')
    check("allNodes: {{ lang.query('Showing records from this node and the configured peer.')" in src,
          'All nodes banner names both nodes')
    fn = src[src.index('function setScopeNote'):]
    fn = fn[:fn.index('\n        }')]
    all_section = fn[fn.rindex('text.allNodes') - 200:]
    check('text.allNodes' in all_section, 'All nodes sets its own banner')
    check('text.peerOnly' not in all_section, 'All nodes never uses the peer-only wording')
    check(all_section.index("$note.text(text.allNodes)") < all_section.index('data.partial')
          if 'data.partial' in all_section else True,
          'All nodes sets its banner before any partial-results note')


def test_toolbar_and_actions_containment():
    src = VIEW.read_text(encoding='utf-8')
    check('class="email-log-toolbar" role="toolbar"' in src, 'actions live in one toolbar')
    check('flex-wrap: wrap' in css_block(src), 'toolbar wraps')
    check('email-log-filters' in src, 'filters have their own row')
    check('nowrap' not in css_block(src).split('.email-log-subject {')[0][-200:] + css_block(src)[css_block(src).index('.email-log-subject {'):][:400],
          'the subject action itself is not forced onto one line')
    check('overflow: hidden' not in css_block(src), 'nothing is hidden to conceal overflow')
    check("email-log-table td', 'overflow-wrap: anywhere" not in src, 'no placeholder')
    check(len(re.findall(r'<col class=', src)) == 7, 'seven columns: selection plus six data columns')
    check(len(re.findall(r'<th[ >]', src)) == 7, 'seven header cells match the colgroup')
    row = src[src.index('rows.forEach(function (row)'):src.index('$body.append($tr)')]
    check(row.count('$tr.append(') == 7, 'seven body cells per row')


def test_unknown_historical_role_omitted():
    src = VIEW.read_text(encoding='utf-8')
    row = src[src.index('rows.forEach(function (row)'):src.index('$body.append($tr)')]
    check("toLowerCase() !== 'unknown'" in row, 'table omits an unknown historical role')
    dlg = src[src.index('function openMessage'):]
    check("toLowerCase() !== 'unknown'" in dlg, 'dialog omits an unknown historical role')
    check("Role when sent" in src, 'a known role is labelled Role when sent')


def test_confirm_dialog_style():
    css = css_block(VIEW.read_text(encoding='utf-8'))
    block = css[css.index('.email-log-confirm-dialog'):]
    block = block[:block.index('}')]
    check('width: 480px' in block, 'confirmation dialog ~480px')
    check('max-width: calc(100vw - 32px)' in block, 'confirmation dialog is viewport constrained')
    src = VIEW.read_text(encoding='utf-8')
    check('class="modal fade"' in src and 'panel-heading' in src, 'standard OPNsense modal styling kept')
    check('localNodeLabel' in src, 'confirmation names the owning node')
    check('email-log-delete-all-confirm' in src, 'delete all keeps its checkbox')


def test_clickable_subject_contract():
    src = VIEW.read_text(encoding='utf-8')
    row = src[src.index('rows.forEach(function (row)'):src.index('$body.append($tr)')]
    check("<button type=\"button\">" in row and ".addClass('email-log-subject')" in row,
          'the subject is a native button, so keyboard activation is native')
    check(".text(subjectText || text.noSubject)" in row, 'an empty subject shows the translated label')
    check("noSubject: {{ lang.query('No subject')" in src, 'the label is translated')
    check("' \\u2014 ' + text.viewMessage" in row, 'the accessible name says what activation does')
    check('email-log-select' in row and "$tr.on('click'" not in row,
          'checkbox clicks stay independent; the row itself is not clickable')
    check("openMessage(row.event_id, row.scope === 'peer')" in row,
          'the same dialog and peer retrieval path is used')
    check("prop('disabled', remote)" in row, 'remote restore remains disabled')
    check("text.restore" in row, 'restore is reachable for deleted rows')
    for forbidden in ("text.viewMessage)</", ".text(text.delete)"):
        check(forbidden not in row, f'no per-row {forbidden.strip()} button remains')


def test_empty_state_uses_same_table():
    src = VIEW.read_text(encoding='utf-8')
    empty = src[src.index('id="email-log-empty"'):]
    check('<table' not in empty.split('</div>')[0], 'empty state is a message, not a second table')
    check("$('#email-log-empty').toggle(rows.length === 0)" in src,
          'empty state toggles within the one shared table view')


def test_long_content_fixture():
    """Long recipient/subject/node values must land in wrapping cells."""
    html = ('<td>' + 'a' * 60 + '@' + 'b' * 40 + '.invalid</td>'
            '<td>' + 'Subject with a very long unbroken token ' + 'x' * 120 + '</td>')
    check('overflow-wrap: anywhere' in css_block(VIEW.read_text(encoding='utf-8')),
          f'long values have a wrapping rule for {html[:20]}...')


def main():
    test_shared_layout()
    test_wrapping_and_responsive_container()
    test_actions_are_inline()
    test_banner_follows_scope()
    test_toolbar_and_actions_containment()
    test_unknown_historical_role_omitted()
    test_confirm_dialog_style()
    test_clickable_subject_contract()
    test_empty_state_uses_same_table()
    test_long_content_fixture()
    print('EMAIL_LOG_TABLE_LAYOUT=FAIL (%d)' % len(FAILS) if FAILS else 'EMAIL_LOG_TABLE_LAYOUT=PASS')
    return 1 if FAILS else 0


if __name__ == '__main__':
    raise SystemExit(main())
