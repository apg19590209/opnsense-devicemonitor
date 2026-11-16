"""The OPNsense router derives API controller filenames from the URI segment.

Regression for a real 404: /api/devicemonitor/emaillog/... resolved to
EmaillogController, but the plugin shipped EmailLogController, so the endpoint
never loaded. This test encodes the dispatcher contract itself rather than
relying on structural similarity.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / 'src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api'
ROUTER = Path('/usr/local/opnsense/mvc/app/library/OPNsense/Mvc/Router.php')


def router_controller_name(segment):
    """Mirror Router::parsePath exactly: ucwords on '_', strip '_', add Controller."""
    words = []
    for part in segment.split('_'):
        words.append(part[:1].upper() + part[1:] if part else '')
    return ''.join(words) + 'Controller'


def test_router_contract_matches_the_framework():
    if not ROUTER.is_file():
        print('ROUTER_CONTRACT=SKIPPED (framework not installed)')
        return
    src = ROUTER.read_text(encoding='utf-8')
    assert 'str_replace(\'_\', \'\', ucwords($element, \'_\')) . \'Controller\'' in src, \
        'router controller-name contract changed; revisit this test'
    print('ROUTER_CONTRACT=VERIFIED')


def test_emaillog_controller_name_matches_uri_segment():
    expected = router_controller_name('emaillog')
    assert expected == 'EmaillogController', expected
    candidate = API_DIR / (expected + '.php')
    assert candidate.is_file(), f'missing {candidate.name}; router would 404'
    body = candidate.read_text(encoding='utf-8')
    assert re.search(r'^class %s\b' % expected, body, re.M), 'class name must match filename'
    # The mismatched name must not survive anywhere.
    assert not (API_DIR / 'EmailLogController.php').exists(), 'stale EmailLogController present'
    print('EMAIL_LOG_ROUTE_NAMING=PASS')


def test_every_api_controller_is_router_reachable():
    """Every controller file must be reachable by some URI segment."""
    for path in sorted(API_DIR.glob('*Controller.php')):
        stem = path.stem
        body = path.read_text(encoding='utf-8')
        assert re.search(r'^class %s\b' % stem, body, re.M), f'{stem}: class/file mismatch'
        if stem == 'EmaillogController':
            assert router_controller_name('emaillog') == stem
        else:
            # Convert CamelCase stems back to a URI segment and re-derive.
            segment = re.sub(r'(?<!^)(?=[A-Z])', '_', stem.replace('Controller', '')).lower()
            assert router_controller_name(segment) == stem, (
                f'{stem} unreachable from segment {segment}')
    print('API_CONTROLLER_REACHABILITY=PASS')


def main():
    test_router_contract_matches_the_framework()
    test_emaillog_controller_name_matches_uri_segment()
    test_every_api_controller_is_router_reachable()
    print('EMAIL_LOG_ROUTING_REGRESSION=PASS')


if __name__ == '__main__':
    main()
