"""Node identity presentation for the Email Log.

Rules: one header format "hostname — management IP — role"; This node and Peer
labelled distinctly; the management address comes from the configured interface
(never the first NIC with an address); historical roles in rows and message
metadata are never replaced by the live role; the timezone legend and global
remote banner are gone while local times and UTC CSV remain.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / 'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/emaillog.volt'
CTRL = ROOT / 'src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/EmaillogController.php'
IDENT = ROOT / 'src/opnsense/scripts/OPNsense/DeviceMonitor/NodeIdentity.php'
AGG = ROOT / 'src/opnsense/scripts/OPNsense/DeviceMonitor/EmailLogAggregate.php'
FAILS = []


def check(cond, label):
    print(('  PASS ' if cond else '  FAIL ') + label)
    if not cond:
        FAILS.append(label)


def test_management_identity():
    src = IDENT.read_text(encoding='utf-8')
    check("const INTERFACE_ORDER" in src, 'management interface order is declared')
    check("$config->interfaces->{$name}" in src, 'address comes from configuration')
    check('net_get_interfaces' not in src, 'no interface scan picks the address')
    check('foreach ([\'re0\'' not in src and "'igc0'" not in src, 'no hard-coded NIC list')
    ctrl = CTRL.read_text(encoding='utf-8')
    check('NodeIdentity::local()' in ctrl, 'controller uses the identity helper')
    check('shell_exec' not in ctrl.split('function nodeFacts')[1].split('\n    }')[0],
          'nodeFacts no longer shells out itself')


def test_label_format():
    src = IDENT.read_text(encoding='utf-8')
    check("\u2014" in src or "\\u{2014}" in src, 'label uses an em dash separator')
    agg = AGG.read_text(encoding='utf-8')
    check("'label' => $label" in agg, 'node tags carry the label')
    view = VIEW.read_text(encoding='utf-8')
    check("text.thisNode + ': '" in view, 'local node is labelled "This node"')
    check("text.peerPrefix + ': '" in view, 'remote node is labelled "Peer"')


def test_historical_roles_preserved():
    view = VIEW.read_text(encoding='utf-8')
    check("if (row.node_role) { nodeText += ' (' + row.node_role + ')'" in view,
          'rows show the recorded role from the row itself')
    check("[text.recordedRole, (m.node_ip || '')" in view,
          'message metadata labels the recorded role')
    check("row.node_role || " not in view.replace("if (row.node_role) {", ""),
          'the live role never substitutes a missing recorded role')
    ctrl = CTRL.read_text(encoding='utf-8')
    check("'node_role' => (string)$row['node_role']" in ctrl, 'API keeps the stored node_role')


def test_notices_removed():
    view = VIEW.read_text(encoding='utf-8')
    check('Time shown in your local timezone' not in view, 'timezone legend wording removed')
    check('email-log-timezone-legend' not in view, 'timezone legend element removed')
    check('renderTimezoneLegend' not in view, 'legend renderer removed')
    check("suffix = '' " not in view and 'formatTimestamp(' in view, 'date-aware suffixes retained')
    check('{{ lang.query(\'Time (local)\')' in view or "devicemonitor_t('Time (local)')" in view,
          'Time (local) heading retained')
    ctrl = CTRL.read_text(encoding='utf-8')
    check("'created_utc', 'node_ip'" in ctrl, 'CSV export stays UTC-labelled')
    check('class="sr-only" id="email-log-remote-note"' in view,
          'remote explanation is an accessible description, not page text')


def test_management_address_selection():
    """The rule, proven against fixtures rather than this host's own addresses."""
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    cfg = tmp / 'config.xml'
    cfg.write_text(
        "<?xml version='1.0'?><opnsense><interfaces>"
        "<wan><if>pppoe0</if><ipaddr>pppoe</ipaddr></wan>"
        "<opt1><if>em0</if><ipaddr>10.0.99.9</ipaddr></opt1>"
        "<lan><if>igc1</if><ipaddr>192.0.2.10</ipaddr></lan>"
        "</interfaces></opnsense>", encoding='utf-8')
    php = ("require '%s'; $c=simplexml_load_file('%s');"
           "echo OPNsense\\DeviceMonitor\\NodeIdentity::managementAddress($c);" % (IDENT, cfg))
    out = subprocess.run(['php', '-r', php], capture_output=True, text=True, timeout=20).stdout.strip()
    check(out == '192.0.2.10', f'LAN address wins over another interface (got {out!r})')
    for f in cfg.parent.iterdir():
        f.unlink()
    cfg.parent.rmdir()


def main():
    test_management_identity()
    test_label_format()
    test_historical_roles_preserved()
    test_notices_removed()
    test_management_address_selection()
    print('EMAIL_LOG_IDENTITY_PRESENTATION=FAIL (%d)' % len(FAILS) if FAILS
          else 'EMAIL_LOG_IDENTITY_PRESENTATION=PASS')
    return 1 if FAILS else 0


if __name__ == '__main__':
    raise SystemExit(main())
