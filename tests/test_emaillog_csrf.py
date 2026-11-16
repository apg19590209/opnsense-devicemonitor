"""Email Log page requests must carry the framework CSRF token.

The OPNsense base API controller rejects any POST/PUT/DELETE without a valid
``X-CSRFToken`` (HTTP 403). The layout installs that header through
``$.ajaxSetup`` inside ``$(document).ready``, so a page must not fire an API
request before ready — doing so produced the operator-visible
"Could not load the email log (HTTP 403)".
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / 'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/emaillog.volt'
LAYOUT = Path('/usr/local/opnsense/mvc/app/views/layouts/default.volt')
CONTROLLER = ROOT / 'src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/EmaillogController.php'


def test_layout_installs_the_csrf_hook_before_use():
    if not LAYOUT.is_file():
        print('LAYOUT_CONTRACT=SKIPPED (layout not installed)')
        return
    src = LAYOUT.read_text(encoding='utf-8')
    assert 'xhr.setRequestHeader("X-CSRFToken"' in src, 'layout CSRF header hook changed'
    ready = src.index('$( document ).ready')
    hook = src.index('$.ajaxSetup')
    assert ready < hook, 'CSRF hook is not inside the ready handler'
    print('LAYOUT_CSRF_HOOK=VERIFIED')


def test_no_request_is_fired_outside_ready():
    src = VIEW.read_text(encoding='utf-8')
    ready_at = src.index('$(document).ready(function () {')
    # Every bare statement invoking load() must come after the ready handler.
    for match in re.finditer(r'^\s*load\(\);\s*$', src, re.M):
        assert match.start() > ready_at, 'load() invoked before the CSRF hook exists'
    # The only such invocation is the deferred one.
    bare = re.findall(r'^\s*load\(\);\s*$', src, re.M)
    assert len(bare) == 1, bare
    print('EMAIL_LOG_NO_EARLY_REQUEST=PASS')


def test_all_requests_use_the_shared_helper():
    src = VIEW.read_text(encoding='utf-8')
    calls = re.findall(r"url: '(/api/devicemonitor/emaillog/\w+)'", src)
    assert set(calls) == {'/api/devicemonitor/emaillog/search',
                          '/api/devicemonitor/emaillog/message',
                          '/api/devicemonitor/emaillog/exportcsv'}, calls
    # Both are POSTs, so both need the token installed by the shared hook.
    for url in calls:
        block = src[src.index(url):src.index(url) + 400]
        assert "type: 'POST'" in block, f'{url} is not a POST'
    code = '\n'.join(ln for ln in src.splitlines() if not ln.strip().startswith(('*', '/*', '//')))
    assert 'setRequestHeader' not in code, 'the page must not hand-roll token handling'
    assert 'csrf_token' not in code, 'the page must not read the token directly'
    print('EMAIL_LOG_SHARED_HELPER=PASS')


def test_controller_rejects_protection_by_contract():
    """The controller itself must not provide an unauthenticated escape hatch."""
    src = CONTROLLER.read_text(encoding='utf-8')
    assert 'extends ApiControllerBase' in src, 'controller must use the protected base class'
    assert 'X-CSRF' not in src and 'csrf' not in src.lower(), \
        'the controller must not override CSRF handling'
    assert 'session' not in src.lower(), 'the controller must not manage sessions itself'
    print('EMAIL_LOG_NO_AUTH_BYPASS=PASS')


def main():
    test_layout_installs_the_csrf_hook_before_use()
    test_no_request_is_fired_outside_ready()
    test_all_requests_use_the_shared_helper()
    test_controller_rejects_protection_by_contract()
    print('EMAIL_LOG_CSRF_REGRESSION=PASS')


if __name__ == '__main__':
    main()
