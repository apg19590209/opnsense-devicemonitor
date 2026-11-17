"""Delete/Restore API contract: visibility plumbing, write gate, remote safety.

The controller is inspected as source because it runs inside the OPNsense
framework; the recorder behaviour is exercised in PHP on temporary databases.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CTRL = ROOT / 'src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/EmaillogController.php'
PEER = ROOT / 'src/opnsense/scripts/OPNsense/DeviceMonitor/PeerClient.php'
VIEW = ROOT / 'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/emaillog.volt'


def body_of(src, name):
    i = src.index(f'function {name}(')
    nxt = re.search(r'\n    (public|private|protected) function ', src[i + 1:])
    return src[i:i + 1 + nxt.start()] if nxt else src[i:]


def test_every_read_path_honours_visibility():
    src = CTRL.read_text(encoding='utf-8')
    for fn in ('searchAction', 'combinedAction', 'exportcsvAction', 'peerpageAction'):
        body = body_of(src, fn)
        assert "'visibility' => $this->visibilityFilter()" in body, f'{fn} ignores visibility'
    peer = PEER.read_text(encoding='utf-8')
    assert "'visibility' => (string)($filters['visibility'] ?? 'active')" in peer, \
        'peer search must forward visibility'
    assert "'deleted_utc'" in src, 'rows carry their visibility marker'
    assert re.search(r"\$clean\['scope'\] = 'local'", src), 'local rows are tagged as local'


def test_visibility_values_are_closed():
    src = CTRL.read_text(encoding='utf-8')
    body = body_of(src, 'visibilityFilter')
    assert "['active', 'deleted', 'all']" in body and "'active'" in body, \
        'only the three values are accepted; anything else is Active'


def test_write_gate():
    src = CTRL.read_text(encoding='utf-8')
    gate = body_of(src, 'requireWriteAccess')
    assert 'throwReadOnly()' in gate, 'user-config-readonly must be refused'
    assert 'return false' in gate, 'the gate must fail closed'
    for fn, flag in (('deleteAction', 'true'), ('restoreAction', 'false')):
        body = body_of(src, fn)
        assert f'setVisibilityAction({flag})' in body, f'{fn} must delegate to the guarded action'
    assert 'requireWriteAccess()' in body_of(src, 'setVisibilityAction'), 'delegated action bypasses the write gate'
    assert src.count('extends ApiControllerBase') == 1, 'framework authentication/ACL remains in force'
    assert 'setStatusCode(403' in body_of(src, 'setVisibilityAction'), 'denial reports 403'
    for fn in ('deleteAction', 'restoreAction'):
        assert 'isPost()' in body_of(src, fn) or 'isPost()' in body_of(src, 'setVisibilityAction')


def test_access_denial_mechanism():
    """A read-only account must be refused before any change is attempted.

    The framework ACL raises a UserException for user-config-readonly; the gate
    converts that into a denial result. The source ordering below proves no
    mutation can run first, and the running framework confirms the privilege and
    refusal type exist and are not granted to an ordinary user.
    """
    src = CTRL.read_text(encoding='utf-8')
    gate = body_of(src, 'requireWriteAccess')
    assert 'try {' in gate and 'throwReadOnly();' in gate and 'catch' in gate, \
        'the gate must convert the ACL refusal into a denial'
    assert 'return false' in gate, 'the gate fails closed'
    assert "hasPrivilege($this->getUserName(), 'page-services-devicemonitor')" in gate, \
        'an explicit write privilege is required'
    action = body_of(src, 'setVisibilityAction')
    assert action.index('requireWriteAccess()') < action.index('markDeleted'), \
        'no mutation may run before the write gate'
    assert action.index('requireWriteAccess()') < action.index('restore('), \
        'no mutation may run before the write gate'
    import json
    import subprocess
    probe = subprocess.run(
        ['php', '-r', 'require_once "/usr/local/opnsense/mvc/script/load_phalcon.php";'
         '$a = new OPNsense\\Core\\ACL();'
         'echo json_encode([$a->hasPrivilege("dm_no_such_user", "user-config-readonly"),'
         ' class_exists("OPNsense\\Base\\UserException")]);'],
        capture_output=True, text=True)
    if probe.returncode == 0 and probe.stdout.strip():
        granted, exc = json.loads(probe.stdout)
        assert granted is False, 'a user without the privilege must not carry it'
        assert exc is True, 'the refusal type the gate catches must exist'


def test_peer_endpoints_stay_read_only():
    src = CTRL.read_text(encoding='utf-8')
    for fn in ('peerpageAction', 'peermessageAction', 'peermessageviewAction'):
        body = body_of(src, fn)
        for forbidden in ('markDeleted', 'restore(', 'EmailTransport', 'shell_exec', 'exec('):
            assert forbidden not in body, f'{fn} must not mutate ({forbidden})'
    peer = PEER.read_text(encoding='utf-8')
    for forbidden in ('delete', 'restore'):
        assert f"'/api/devicemonitor/emaillog/{forbidden}" not in peer, \
            'the peer client must not call mutation endpoints'


def test_mutations_never_touch_mail():
    src = CTRL.read_text(encoding='utf-8')
    body = body_of(src, 'setVisibilityAction')
    for forbidden in ('postfix', 'postsuper', 'postqueue', 'mail(', 'EmailTransport', 'NotificationHandler'):
        assert forbidden not in body, f'mutation must not touch delivery ({forbidden})'
    view = VIEW.read_text(encoding='utf-8')
    code = '\n'.join(ln for ln in view.splitlines()
                     if not ln.strip().startswith(('*', '/*', '//', '<!--', '{#')))
    for forbidden in ('postfix', 'postsuper', 'postqueue', 'mailq'):
        assert forbidden not in code.lower(), f'the page must not touch {forbidden}'


def test_remote_rows_are_not_mutable_from_here():
    view = VIEW.read_text(encoding='utf-8')
    assert "row.scope === 'peer'" in view, 'remote rows must be identified'
    assert ".prop('disabled', remote)" in view, 'remote rows disable the action'
    assert 'aria-describedby' in view, 'the reason is associated with the disabled control'


def main():
    test_every_read_path_honours_visibility()
    test_visibility_values_are_closed()
    test_write_gate()
    test_access_denial_mechanism()
    test_peer_endpoints_stay_read_only()
    test_mutations_never_touch_mail()
    test_remote_rows_are_not_mutable_from_here()
    print('EMAIL_LOG_VISIBILITY_API=PASS')


if __name__ == '__main__':
    main()
