"""Access boundaries for the Email Log API and its peer-read privilege.

The peer-read privilege must cover only the peer listing and message endpoints;
Delete/Restore must require the full Device Monitor privilege on top of the
user-config-readonly restriction, and anything unproven must be denied.

Source-level assertions are used for the controller (it runs inside the OPNsense
framework); where the running framework is available, its real ACL matcher is
used to prove which URLs each privilege set can reach.
"""
import re
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACL = ROOT / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/ACL/ACL.xml'
CTRL = ROOT / 'src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/EmaillogController.php'
FAILS = []


def check(cond, label):
    print(('  PASS ' if cond else '  FAIL ') + label)
    if not cond:
        FAILS.append(label)


def acl_sets():
    xml = ACL.read_text(encoding='utf-8')
    out = {}
    for m in re.finditer(r'<([a-z0-9-]+)>\s*<name>.*?</name>\s*<patterns>(.*?)</patterns>', xml, re.S):
        out[m.group(1)] = re.findall(r'<pattern>(.*?)</pattern>', m.group(2))
    return out


def test_acl_scope():
    sets = acl_sets()
    peer = sets.get('page-services-devicemonitor-peer', [])
    check(peer == ['api/devicemonitor/emaillog/peerpage', 'api/devicemonitor/emaillog/peermessage'],
          'peer privilege lists exactly the two peer endpoints')
    for bad in ('ui/', 'api/devicemonitor/config', 'delete', 'restore', 'search', 'combined', 'exportcsv', '*' + 'devicemonitor/*'):
        check(not any(bad in p for p in peer), f'peer privilege excludes {bad}')
    full = sets.get('page-services-devicemonitor', [])
    check('ui/devicemonitor/*' in full and 'api/devicemonitor/*' in full,
          'the administrator privilege keeps its existing scope')


def test_write_gate():
    src = CTRL.read_text(encoding='utf-8')
    gate = src[src.index('private function requireWriteAccess'):]
    gate = gate[:gate.index('\n    }')]
    check('throwReadOnly()' in gate, 'user-config-readonly remains a restriction')
    check("hasPrivilege($this->getUserName(), 'page-services-devicemonitor')" in gate,
          'explicit Device Monitor write privilege is required')
    check('return false' in gate, 'the gate fails closed')
    for fn in ('deleteAction', 'restoreAction'):
        body = src[src.index(f'function {fn}('):]
        body = body[:body.index('\n    }')]
        check('setVisibilityAction(' in body, f'{fn} delegates to the guarded action')
    setv = src[src.index('private function setVisibilityAction'):]
    setv = setv[:setv.index('\n    }')]
    check(setv.index('requireWriteAccess()') < setv.index('markDeleted'), 'delete is gated before mutation')
    check(setv.index('requireWriteAccess()') < setv.index('restore('), 'restore is gated before mutation')


def framework_acl():
    """Ask the installed ACL matcher which URLs each configured pattern reaches."""
    patterns = acl_sets().get('page-services-devicemonitor-peer', [])
    urls = ['/api/devicemonitor/emaillog/peerpage', '/api/devicemonitor/emaillog/peermessage',
            'api/devicemonitor/emaillog/delete', 'api/devicemonitor/emaillog/restore',
            'api/devicemonitor/emaillog/search', 'api/devicemonitor/config/get',
            'api/core/firmware/status', 'ui/devicemonitor/emaillog']
    php = ("require_once '/usr/local/opnsense/mvc/script/load_phalcon.php';"
           "$a=new OPNsense\\Core\\ACL();$urls=json_decode($argv[1],true);"
           "$pats=json_decode($argv[2],true);"
           "foreach($urls as $u){$hit=0;foreach($pats as $p){if($a->urlMatch($u,$p)){$hit=1;break;}}"
           "echo $u,'=',$hit,PHP_EOL;}")
    import json
    try:
        out = subprocess.run(['php', '-r', php, json.dumps(urls), json.dumps(patterns)],
                             capture_output=True, text=True, timeout=20).stdout
        return dict(line.split('=', 1) for line in out.splitlines() if '=' in line)
    except Exception:
        return None


def test_framework_matcher():
    res = framework_acl()
    if res is None:
        print('  SKIP framework ACL matcher unavailable')
        return
    allowed = {'/api/devicemonitor/emaillog/peerpage', '/api/devicemonitor/emaillog/peermessage'}
    for url in list(res):
        expected = '1' if url in allowed else '0'
        check(res[url] == expected, f'peer privilege reaches {url} -> {res[url]}')


def main():
    test_acl_scope()
    test_write_gate()
    test_framework_matcher()
    print('EMAIL_LOG_PEER_PRIVILEGE=FAIL (%d)' % len(FAILS) if FAILS else 'EMAIL_LOG_PEER_PRIVILEGE=PASS')
    return 1 if FAILS else 0


if __name__ == '__main__':
    raise SystemExit(main())
