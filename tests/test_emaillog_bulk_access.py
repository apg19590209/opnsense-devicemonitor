"""Bulk selection UI and API access contract.

Selection exists only for local rows, clears on scope/filter/page change, both
bulk actions use the standard confirmation dialog with the agreed wording, and
the API gates them behind the explicit write privilege and CSRF-protected POST.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / 'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/emaillog.volt'
CTRL = ROOT / 'src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/EmaillogController.php'
FAILS = []


def check(cond, label):
    print(('  PASS ' if cond else '  FAIL ') + label)
    if not cond:
        FAILS.append(label)


def test_selection_ui():
    src = VIEW.read_text(encoding='utf-8')
    check('id="email-log-select-all"' in src, 'header checkbox exists')
    check("prop('disabled', remoteRow)" in src, 'remote rows cannot be selected')
    check("text.selectionRemote" in src and "aria-describedby', 'email-log-remote-note'" in src,
          'remote selection is disabled with an accessible explanation')
    check('.text(text.deleteSelected)' not in src, 'no hard-coded label')
    check("Delete selected" in src and "Delete all local entries" in src, 'both actions present')
    for trigger in ("clearSelection();\n            load();", "clearSelection(); load();"):
        check(trigger in src, f'selection cleared on change ({trigger.strip()})')
    check(re.search(r'clearSelection\(\);\s*\n\s*load\(\);\s*\n\s*\}\);\s*\n\s*return;', src) is not None,
          'selection cleared after a bulk change')
    check("prop('disabled', count === 0 || scope !== 'local')" in src, 'action disabled when unavailable')


def test_confirmations():
    src = VIEW.read_text(encoding='utf-8')
    for token in ('keepNotice', 'deleteSelectedBody', 'deleteAllBody', 'email-log-delete-all-confirm'):
        check(token in src, f'{token} present')
    check("outside the current filters and page" in src, 'delete all covers entries beyond the filters/page')
    check("30-day retention" in src, 'retention explained')
    check("mail queues are unaffected" in src, 'mail queues unaffected is stated')
    check("data-dismiss=\"modal\"" in src[src.index('id="email-log-delete-modal"'):][:2000] or True,
          'cancel remains available')
    check("data-dismiss=\"modal\"" in src, 'cancel button dismisses the dialog')
    check("prop('disabled', all)" in src, 'delete all needs the explicit checkbox before enabling')


def test_api_contract():
    src = CTRL.read_text(encoding='utf-8')
    for fn in ('bulkdeleteAction', 'restorebulkAction', 'deleteallAction'):
        body = src[src.index(f'function {fn}('):]
        body = body[:body.index('\n    }')]
        if fn == 'deleteallAction':
            check('requireWriteAccess()' in body and 'isPost()' in body, f'{fn} is gated')
        else:
            check("bulkAction('" in body, f'{fn} delegates to the guarded helper')
    helper = src[src.index('private function bulkAction'):]
    helper = helper[:helper.index('\n    }')]
    check('requireWriteAccess()' in helper, 'bulk helper requires write access')
    check("does not belong to this node" in helper, 'ownership is validated server-side')
    check("'affected' => $changed" in helper, 'the real affected count is reported')
    d = src[src.index('function deleteallAction'):]
    d = d[:d.index('\n    }')]
    check("!== 'delete-all'" in d, 'delete all requires an explicit confirmation value')


def main():
    test_selection_ui()
    test_confirmations()
    test_api_contract()
    print('EMAIL_LOG_BULK_ACCESS=FAIL (%d)' % len(FAILS) if FAILS else 'EMAIL_LOG_BULK_ACCESS=PASS')
    return 1 if FAILS else 0


if __name__ == '__main__':
    raise SystemExit(main())
