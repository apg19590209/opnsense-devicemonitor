"""Peer aggregation with mocked authenticated peers. No network access."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'src/opnsense/scripts/OPNsense/DeviceMonitor'
CTRL = ROOT / 'src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/EmaillogController.php'
SETTINGS_CTRL = ROOT / 'src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/ConfigController.php'
VIEW = ROOT / 'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/emaillog.volt'
SETTINGS = ROOT / 'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt'

fails = 0
def check(c, m):
    global fails
    print(('  PASS ' if c else '  FAIL ') + m)
    if not c:
        fails += 1

PASS = 0
def php(script):
    """Run a snippet inside PHP so it can use the real classes."""
    r = subprocess.run(['php', '-r', script], capture_output=True, text=True, cwd=str(ROOT))
    if r.returncode != 0:
        raise SystemExit('PHP_FAILED: ' + r.stderr[:400])
    return json.loads(r.stdout)


def peer_module_load():
    return f"require '{SCRIPTS}/PeerClient.php'; require '{SCRIPTS}/EmailLogAggregate.php';"


def test_url_validation():
    out = php(peer_module_load() + """
$cases = [
  'https://192.168.20.252' => 0,
  'http://192.168.20.252' => 1,
  'https://user:pw@host' => 1,
  'https://host/api?x=1' => 1,
  'ftp://host' => 1,
  '' => 1,
  'not a url' => 1,
];
$res = [];
foreach ($cases as $url => $expected) {
  $errs = OPNsense\\DeviceMonitor\\PeerClient::validate(['url' => $url, 'api_key' => 'k', 'api_secret' => 's']);
  $res[$url] = count($errs) > 0 ? 1 : 0;
}
echo json_encode($res);
""")
    check(out['https://192.168.20.252'] == 0, 'https URL accepted')
    for bad in ('http://192.168.20.252', 'https://user:pw@host', 'https://host/api?x=1', 'ftp://host', '', 'not a url'):
        check(out[bad] == 1, f'rejected: {bad or "(empty)"}')


def test_credentials_required():
    out = php(peer_module_load() + """
$res = [];
$res['none'] = count(OPNsense\\DeviceMonitor\\PeerClient::validate(['url' => 'https://h'])) > 0 ? 1 : 0;
$res['blank_secret'] = count(OPNsense\\DeviceMonitor\\PeerClient::validate(['url' => 'https://h', 'api_key' => 'k', 'api_secret' => ' '])) > 0 ? 1 : 0;
$res['bad_ca'] = count(OPNsense\\DeviceMonitor\\PeerClient::validate(['url' => 'https://h', 'api_key' => 'k', 'api_secret' => 's', 'ca_pem' => 'nope'])) > 0 ? 1 : 0;
$res['ok'] = count(OPNsense\\DeviceMonitor\\PeerClient::validate(['url' => 'https://h', 'api_key' => 'k', 'api_secret' => 's'])) > 0 ? 1 : 0;
echo json_encode($res);
""")
    check(out['none'] == 1, 'missing credentials rejected')
    check(out['blank_secret'] == 1, 'blank secret rejected')
    check(out['bad_ca'] == 1, 'non-PEM CA rejected')
    check(out['ok'] == 0, 'complete settings accepted')


def test_aggregate_combines_and_sorts():
    out = php(peer_module_load() + """
$local = [
  ['event_id' => 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'created_utc' => '2026-11-17 10:00:00', 'node_ip' => '192.168.20.23', 'notification_type' => 'test'],
  ['event_id' => 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb', 'created_utc' => '2026-11-17 12:00:00', 'node_ip' => '192.168.20.23', 'notification_type' => 'test'],
];
$peerRows = ['available' => true, 'rows' => [
  ['event_id' => 'cccccccccccccccccccccccccccccccc', 'created_utc' => '2026-11-17 11:00:00', 'node_ip' => '192.168.20.252', 'notification_type' => 'test'],
]];
$tag = ['scope' => 'local', 'node_id' => 'n1', 'node_ip' => '192.168.20.23', 'role' => 'master'];
$ptag = ['scope' => 'peer', 'node_id' => 'n2', 'node_ip' => '192.168.20.252', 'role' => 'backup'];
$r = OPNsense\\DeviceMonitor\\EmailLogAggregate::combine($local, $peerRows, $tag, $ptag, 10, 0);
echo json_encode(['order' => array_map(fn($x) => substr($x['created_utc'], 11, 5), $r['rows']),
                  'total' => $r['total'], 'partial' => $r['partial'], 'peer' => $r['peer']['status']]);
""")
    check(out['order'] == ['12:00', '11:00', '10:00'], 'combined set sorted newest first across nodes')
    check(out['total'] == 3, 'total counts both nodes')
    check(out['partial'] is False, 'no partial flag when peer is healthy')
    check(out['peer'] == 'available', 'peer reported available')


def test_aggregate_partial_and_pagination():
    out = php(peer_module_load() + """
$local = [];
for ($i = 0; $i < 5; $i++) {
  $local[] = ['event_id' => str_repeat('a', 32), 'created_utc' => '2026-11-17 1' . $i . ':00:00', 'node_ip' => 'h'];
}
$tag = ['scope' => 'local', 'node_id' => 'n1', 'node_ip' => 'h', 'role' => 'master'];
$ptag = ['scope' => 'peer', 'node_id' => 'n2', 'node_ip' => 'p', 'role' => 'backup'];
$down = ['available' => false, 'reason' => 'Peer request failed'];
$r = OPNsense\\DeviceMonitor\\EmailLogAggregate::combine($local, $down, $tag, $ptag, 2, 2);
echo json_encode(['partial' => $r['partial'], 'peer' => $r['peer']['status'], 'reason' => $r['peer']['reason'],
                  'returned' => count($r['rows']), 'total' => $r['total'], 'offset' => $r['offset']]);
""")
    check(out['partial'] is True, 'peer failure sets partial=true')
    check(out['peer'] == 'unavailable', 'peer reported unavailable')
    check('Peer request failed' in out['reason'], 'reason surfaced')
    check(out['returned'] == 2 and out['total'] == 5 and out['offset'] == 2, 'pagination applies to combined set')


def test_peer_disabled_state():
    out = php(peer_module_load() + """
$tag = ['scope' => 'local', 'node_id' => 'n1', 'node_ip' => 'h', 'role' => 'master'];
$ptag = ['scope' => 'peer', 'node_id' => '', 'node_ip' => '', 'role' => ''];
$r = OPNsense\\DeviceMonitor\\EmailLogAggregate::combine([], null, $tag, $ptag, 10, 0);
echo json_encode(['peer' => $r['peer']['status'], 'partial' => $r['partial']]);
""")
    check(out['peer'] == 'disabled', 'unconfigured peer reported disabled, not error')
    check(out['partial'] is False, 'disabled peer is not a partial failure')


def test_mock_peer_over_tls_is_not_attempted_without_trust():
    out = php(peer_module_load() + """
$client = new OPNsense\\DeviceMonitor\\PeerClient(['url' => '', 'api_key' => 'k', 'api_secret' => 's']);
$r = $client->search([], 10, 0);
$msg = $client->message(str_repeat('a', 32));
echo json_encode(['search_available' => $r['available'], 'msg_available' => $msg['available'],
                  'bad_id' => (new OPNsense\\DeviceMonitor\\PeerClient(['url' => 'https://h', 'api_key' => 'k', 'api_secret' => 's']))->message('nope')['available']]);
""")
    check(out['search_available'] is False, 'no URL means no request and no rows')
    check(out['msg_available'] is False, 'no URL means no message fetch')
    check(out['bad_id'] is False, 'invalid message reference refused before any request')


def test_controller_and_client_wiring():
    ctrl = CTRL.read_text(encoding='utf-8')
    for name in ('combinedAction', 'peerpageAction', 'peermessageAction', 'peermessageviewAction', 'peerSettings'):
        check(f'function {name}' in ctrl, f'controller defines {name}')
    check("'partial' => $combined['partial']" in ctrl, 'combined response exposes partial state')
    check("implode(' ', $errors)" in ctrl, 'invalid peer settings reported, not attempted')
    client = (SCRIPTS / 'PeerClient.php').read_text(encoding='utf-8')
    check('CURLOPT_SSL_VERIFYPEER => true' in client, 'TLS peer verification enabled')
    check('CURLOPT_SSL_VERIFYHOST => 2' in client, 'hostname verification enforced')
    check('CURLOPT_FOLLOWLOCATION => false' in client, 'redirects not followed')
    check('CURLOPT_CONNECTTIMEOUT' in client and 'CURLOPT_TIMEOUT' in client, 'requests bounded')
    check('MAX_RESPONSE_BYTES' in client, 'response size bounded')
    check("'transport error'" in client, 'transport errors do not leak URL or credentials')


def test_secret_never_returned():
    ctrl = SETTINGS_CTRL.read_text(encoding='utf-8')
    check("unset($config['email_log_peer_api_secret'])" in ctrl, 'config API strips the peer secret')
    check("email_log_peer_secret_set" in ctrl, 'config API reports only whether a secret is stored')
    check("if ($peer_api_secret !== '')" in ctrl, 'blank secret keeps the stored value')
    view = SETTINGS.read_text(encoding='utf-8')
    check('#email_log_peer_api_secret' in view and 'type="password"' in view, 'secret field is a password input')
    check("email_log_peer_secret_set" in view, 'settings loads only the stored-secret flag')
    check("data.email_log_peer_api_secret = secret" in view, 'secret sent only when typed')


def test_ui_tabs_and_partial_state():
    view = VIEW.read_text(encoding='utf-8')
    check('data-scope="peer"' in view and 'data-scope="all"' in view, 'peer and all tabs wired')
    check('email-log-partial' in view, 'partial-failure banner present')
    check('peerNotConfigured' in view and 'peerUnavailable' in view, 'explicit peer states worded')
    check('peermessageview' in view, 'peer messages fetched on demand')


def main():
    test_url_validation()
    test_credentials_required()
    test_aggregate_combines_and_sorts()
    test_aggregate_partial_and_pagination()
    test_peer_disabled_state()
    test_mock_peer_over_tls_is_not_attempted_without_trust()
    test_controller_and_client_wiring()
    test_secret_never_returned()
    test_ui_tabs_and_partial_state()
    print('EMAIL_LOG_PEER_TESTS=' + ('PASS' if fails == 0 else f'FAIL ({fails})'))
    return 0 if fails == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
