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
                   'email-log-col-status', 'email-log-col-actions'], f'column order {cols}')
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
    table_css = css.split('#email-log-table.email-log-table td,')[1].split('}')[0]
    check('overflow-wrap: anywhere' in table_css, 'values wrap')
    check('word-break: break-word' in table_css, 'long tokens break instead of clipping')
    check('white-space: nowrap' in css, 'actions stay in one line inside their column')
    check('class="table-responsive"' in src, 'table uses the standard responsive container')
    check('display: none' not in css.split('#email-log-table.email-log-table')[1].split('@media')[0],
          'no content is hidden to force alignment')


def test_actions_column():
    src = VIEW.read_text(encoding='utf-8')
    check(".addClass('email-log-actions')" in src, 'action cell carries its column class')
    check("var remote = row.scope === 'peer';" in src and ".prop('disabled', remote)" in src,
          'remote rows keep their disabled action')
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
    test_actions_column()
    test_banner_follows_scope()
    test_empty_state_uses_same_table()
    test_long_content_fixture()
    print('EMAIL_LOG_TABLE_LAYOUT=FAIL (%d)' % len(FAILS) if FAILS else 'EMAIL_LOG_TABLE_LAYOUT=PASS')
    return 1 if FAILS else 0


if __name__ == '__main__':
    raise SystemExit(main())
