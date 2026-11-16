"""The uninstaller must invalidate the live menu cache without touching unrelated state.

Every case runs the real `uninstall.sh` against a temporary root. Destructive utility
commands are wrapped so a path that escapes that root fails closed before reaching the
host; service, configctl, pkill and sleep are stubs and record what the script requested.
"""
import os
import re
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNINSTALLER = ROOT / 'uninstall.sh'
MAKEFILE = ROOT / 'Makefile'

MENU_CACHE = '/var/lib/php/tmp/opnsense_menu_cache.xml'
ACL_CACHE = '/var/lib/php/tmp/opnsense_acl_cache.json'
DB_CONFIG = '/var/db/devicemonitor/config.json'
DB_FILE = '/var/db/devicemonitor/devices.db'
CONFIG_XML = '/conf/config.xml'
RC_LOCAL = '/etc/rc.conf.local'
LOCALE_INC = '/usr/local/etc/inc/devicemonitor_locale.inc'
ACTION_UPDATE = '/usr/local/opnsense/service/conf/actions.d/actions_devicemonitor_update.conf'
PLUGIN_MANIFEST = ROOT / 'release/v2.14.0-runtime.manifest'


def script(body):
    return '#!/bin/sh\n' + textwrap.dedent(body).lstrip()


class Sandbox:
    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.tmp = Path(self._tmp.name)
        self.root = self.tmp / 'root'
        self.bin = self.tmp / 'bin'
        self.log = self.tmp / 'commands.log'
        self.root.mkdir()
        self.bin.mkdir()
        self.log.write_text('')
        self._install_stubs()

    def close(self):
        self._tmp.cleanup()

    def path(self, absolute):
        return self.root / absolute.lstrip('/')

    def write(self, absolute, body, mode=0o644):
        target = self.path(absolute)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
        os.chmod(target, mode)
        return target

    def _stub(self, name, body):
        target = self.bin / name
        target.write_text(script(body))
        target.chmod(0o755)

    def _guard(self, name, last_only=False):
        real = shutil.which(name)
        assert real, 'missing host utility: %s' % name
        body = r'''import os
import sys

real = __REAL__
args = sys.argv[1:]
paths = args[-1:] if __LAST_ONLY__ else [
    arg for arg in args if arg and not arg.startswith('-')]
root = os.path.realpath(os.environ['DM_UNINSTALL_ROOT'])
for original in paths:
    if not os.path.isabs(original):
        sys.stderr.write('UNSAFE_PATH:%s\n' % original)
        raise SystemExit(97)
    resolved = os.path.realpath(original)
    try:
        within_root = os.path.commonpath((root, resolved)) == root
    except ValueError:
        within_root = False
    if not within_root:
        sys.stderr.write('UNSAFE_ESCAPE:%s\n' % original)
        raise SystemExit(97)
os.execv(real, [real] + args)
'''
        body = body.replace('__REAL__', repr(real)).replace(
            '__LAST_ONLY__', 'True' if last_only else 'False')
        target = self.bin / name
        target.write_text('#!/usr/bin/env python3\n' + body)
        target.chmod(0o755)

    def _install_stubs(self):
        self._guard('rm')
        self._guard('rmdir')
        self._guard('cp')
        self._guard('sed', last_only=True)
        self._stub('service', r'''
            printf 'service:%s\n' "$*" >> "$DM_STUB_LOG"
            [ "${STUB_FAIL_SERVICE:-0}" -eq 0 ] || exit "$STUB_FAIL_SERVICE"
            exit 0
        ''')
        self._stub('configctl', r'''
            printf 'configctl:%s\n' "$*" >> "$DM_STUB_LOG"
            [ "${STUB_FAIL_CONFIGCTL:-0}" -eq 0 ] || exit "$STUB_FAIL_CONFIGCTL"
            exit 0
        ''')
        self._stub('pkill', r'''
            printf 'pkill:%s\n' "$*" >> "$DM_STUB_LOG"
            exit 0
        ''')
        self._stub('sleep', r'''
            printf 'sleep:%s\n' "$*" >> "$DM_STUB_LOG"
            exit 0
        ''')
        self._stub('sha256', r'''
            if [ "${STUB_SHA256_EXIT:-96}" -eq 0 ]; then
                printf '%s\n' "${STUB_SHA256:-UNSAFE}"
                exit 0
            fi
            echo 'UNSAFE_SHA256' >&2
            exit "${STUB_SHA256_EXIT:-96}"
        ''')
        self.write('/usr/local/etc/rc.configure_plugins', r'''#!/bin/sh
printf 'rc.configure_plugins\n' >> "$DM_STUB_LOG"
[ "${STUB_FAIL_RC:-0}" -eq 0 ] || exit "$STUB_FAIL_RC"
exit 0
''', mode=0o755)

    def run(self, *args, **env_extra):
        env = dict(os.environ,
                   PATH='%s:%s' % (self.bin, os.environ.get('PATH', '')),
                   DM_UNINSTALL_ROOT=os.path.realpath(str(self.root)),
                   DM_STUB_LOG=str(self.log))
        env.update(env_extra)
        return subprocess.run(['sh', str(UNINSTALLER)] + list(args), env=env,
                              capture_output=True, text=True, timeout=30)

    def commands(self):
        return self.log.read_text().splitlines()


def test_static_contract():
    text = UNINSTALLER.read_text()
    assert MENU_CACHE in text
    assert LOCALE_INC in text, 'uninstaller must remove the plugin locale bootstrap'
    assert ACTION_UPDATE in text, 'uninstaller must remove the update configd action'
    obsolete_clean = re.compile(
        r'(?m)^\s*(?:@)?rm\s+-f\s+/tmp/opnsense_menu_cache\.xml\s*$')
    assert not obsolete_clean.search(text)
    assert 'php-fpm' not in text
    assert 'configctl webgui restart' in text
    makefile = MAKEFILE.read_text()
    assert MENU_CACHE in makefile
    assert not obsolete_clean.search(makefile)
    assert ACL_CACHE in text
    assert ACL_CACHE in makefile
    obsolete_acl = re.compile(
        r'(?m)^\s*(?:@)?rm\s+-f\s+(?:"?)/tmp/opnsense_acl_cache\.json')
    assert not obsolete_acl.search(text)
    assert not obsolete_acl.search(makefile)
    readme = (ROOT / 'README.md').read_text()
    readme_flat = ' '.join(readme.split())
    assert 'no longer calls the unsupported `service php-fpm restart`' in readme_flat
    assert 'retains the supported' in readme
    assert 'active menu and ACL caches under `/var/lib/php/tmp`' in readme
    readme_cz = (ROOT / 'README_CZ.md').read_text()
    readme_cz_flat = ' '.join(readme_cz.split())
    assert 'aktivní cache menu a ACL v `/var/lib/php/tmp`' in readme_cz
    assert 'již nevolá nepodporovaný příkaz `service php-fpm restart`' in readme_cz_flat
    assert 'zůstává zachována' in readme_cz_flat


def test_cache_invalidation_and_preservation():
    box = Sandbox()
    try:
        box.write(MENU_CACHE, '<menu>stale</menu>\n')
        box.write(ACL_CACHE, '{}\n')
        box.write('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py', 'plugin\n')
        box.write(DB_FILE, 'device data\n')
        box.write(LOCALE_INC, 'plugin locale bootstrap\n')
        box.write(ACTION_UPDATE, '[update]\n')
        preserved = {
            CONFIG_XML: '<opnsense><system/></opnsense>\n',
            RC_LOCAL: 'gateway_enable="YES"\n',
            '/var/db/unrelated/keep.db': 'unrelated data\n',
            '/var/lib/php/tmp/unrelated.xml': 'unrelated cache namespace\n',
            '/usr/local/opnsense/mvc/app/languages/en_US/LC_MESSAGES/other.mo': 'other locale\n',
            '/var/backups/devicemonitor/core-locale/unrelated.txt': 'unrelated backup\n',
            '/usr/local/etc/inc/unrelated.inc': 'unrelated include\n',
            '/usr/local/etc/inc/plugins.inc.d/unrelated.inc': 'unrelated plugin include\n',
            '/usr/local/opnsense/service/conf/actions.d/actions_unrelated.conf': '[unrelated]\n',
            '/usr/local/opnsense/service/conf/actions.d/actions_devicemonitor_extra.conf':
                'not a plugin-owned action\n',
        }
        for path, body in preserved.items():
            box.write(path, body)

        done = box.run()

        assert done.returncode == 0, (done.stdout, done.stderr)
        assert not box.path(MENU_CACHE).exists(), 'active menu cache was not invalidated'
        assert not box.path(ACL_CACHE).exists()
        assert not box.path('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor').exists()
        assert not box.path('/var/db/devicemonitor').exists(), 'normal uninstall removes plugin data'
        assert not box.path(LOCALE_INC).exists(), 'locale bootstrap was left behind'
        assert not box.path(ACTION_UPDATE).exists(), 'update action was left behind'
        for path, body in preserved.items():
            assert box.path(path).read_text() == body, path

        commands = box.commands()
        assert 'rc.configure_plugins' in commands, commands
        assert 'service:configd restart' in commands, commands
        assert 'configctl:webgui restart' in commands, commands
        assert not any('php-fpm' in command for command in commands), commands
        first_sleep = commands.index('sleep:1')
        configd = commands.index('service:configd restart')
        restart_sleep = commands.index('sleep:2')
        webgui = commands.index('configctl:webgui restart')
        assert first_sleep < configd < restart_sleep < webgui, commands
        assert not any(command == 'sleep:2' for command in commands[webgui + 1:]), commands
    finally:
        box.close()


def test_silent_mode_preserves_plugin_data_and_skips_services():
    box = Sandbox()
    try:
        box.write(MENU_CACHE, '<menu>stale</menu>\n')
        box.write(DB_FILE, 'device data\n')
        box.write(DB_CONFIG, '{"enabled": 0}\n')
        box.write(LOCALE_INC, 'plugin locale bootstrap\n')
        box.write(ACTION_UPDATE, '[update]\n')

        done = box.run('--silent')

        assert done.returncode == 0, (done.stdout, done.stderr)
        assert box.path(DB_FILE).read_text() == 'device data\n'
        assert box.path(DB_CONFIG).read_text() == '{"enabled": 0}\n'
        assert not box.path(MENU_CACHE).exists()
        assert not box.path(LOCALE_INC).exists()
        assert not box.path(ACTION_UPDATE).exists()
        commands = box.commands()
        assert 'rc.configure_plugins' not in commands, commands
        assert not any(command.startswith('service:') for command in commands), commands
        assert not any(command.startswith('configctl:') for command in commands), commands
    finally:
        box.close()


def test_locale_bootstrap_and_update_action_are_removed_only():
    """The two 12 November residuals are plugin-owned files, not directory-wide globs."""
    box = Sandbox()
    try:
        box.write(LOCALE_INC, 'plugin locale bootstrap\n')
        box.write(ACTION_UPDATE, '[update]\n')
        preserved = {
            '/usr/local/etc/inc/unrelated.inc': 'unrelated include\n',
            '/usr/local/opnsense/service/conf/actions.d/actions_unrelated.conf': '[unrelated]\n',
            '/usr/local/opnsense/service/conf/actions.d/actions_devicemonitor_extra.conf':
                'not a plugin-owned action\n',
        }
        for path, body in preserved.items():
            box.write(path, body)

        done = box.run()

        assert done.returncode == 0, (done.stdout, done.stderr)
        assert not box.path(LOCALE_INC).exists()
        assert not box.path(ACTION_UPDATE).exists()
        for path, body in preserved.items():
            assert box.path(path).read_text() == body, path
    finally:
        box.close()


def test_every_manifest_target_is_removed():
    """A normal uninstall must leave no installed payload target behind."""
    box = Sandbox()
    try:
        targets = []
        for digest, mode, source, target in (
                line.split() for line in PLUGIN_MANIFEST.read_text().splitlines() if line.strip()):
            assert re.fullmatch(r'[0-9a-f]{64}', digest), digest
            box.write(target, 'payload for %s\n' % source, mode=int(mode, 8))
            targets.append(target)
        assert len(targets) == len(PLUGIN_MANIFEST.read_text().splitlines()), targets

        done = box.run()

        assert done.returncode == 0, (done.stdout, done.stderr)
        leftovers = [target for target in targets if box.path(target).exists()]
        assert not leftovers, 'uninstaller left manifest targets: %r' % leftovers
    finally:
        box.close()


def test_required_command_failures_propagate():
    cases = [
        ({'STUB_FAIL_RC': '17'}, 17, 'ERROR: rc.configure_plugins failed (status 17)',
         'service:configd restart', False),
        ({'STUB_FAIL_SERVICE': '22'}, 22,
         'ERROR: service configd restart failed (status 22)',
         'configctl:webgui restart', False),
        ({'STUB_FAIL_CONFIGCTL': '23'}, 23,
         'ERROR: configctl webgui restart failed (status 23)',
         'configctl:webgui restart', True),
    ]
    for env_extra, expected, message, marker, marker_expected in cases:
        box = Sandbox()
        try:
            done = box.run(**env_extra)
            assert done.returncode == expected, (env_extra, done.returncode, done.stderr)
            assert message in done.stderr, done.stderr
            assert 'Uninstall complete!' not in done.stdout, done.stdout
            assert (marker in box.commands()) is marker_expected, box.commands()
        finally:
            box.close()


def test_isolated_root_must_be_canonical_and_not_live_root():
    box = Sandbox()
    try:
        link = box.tmp / 'root-link'
        link.symlink_to(box.root, target_is_directory=True)
        cases = [
            ('/', 'ERROR: DM_UNINSTALL_ROOT must not be the live root'),
            ('relative/root', 'ERROR: DM_UNINSTALL_ROOT must be an absolute path'),
            (str(box.root) + '/..',
             'ERROR: DM_UNINSTALL_ROOT must be a canonical, non-root directory path'),
            (str(link),
             'ERROR: DM_UNINSTALL_ROOT must be a canonical, non-root directory path'),
        ]
        for value, message in cases:
            done = box.run(DM_UNINSTALL_ROOT=value)
            assert done.returncode == 1, (value, done.returncode, done.stderr)
            assert message in done.stderr, (value, done.stderr)
        assert box.commands() == [], box.commands()
    finally:
        box.close()


def test_recorded_core_target_cannot_escape_the_root():
    box = Sandbox()
    try:
        outside = box.tmp / 'outside.mo'
        outside.write_text('must not be removed\n')
        box.write('/var/backups/devicemonitor/core-locale/en_US.state',
                  'pristine=absent\ntarget=/../outside.mo\ninstalled=anything\n')

        done = box.run()

        assert done.returncode == 0, (done.stdout, done.stderr)
        assert outside.read_text() == 'must not be removed\n'
        assert 'recorded target escapes its root; left unchanged' in done.stdout
        assert 'UNSAFE_SHA256' not in done.stderr, done.stderr
    finally:
        box.close()


def test_destructive_guards_reject_symlink_escapes():
    box = Sandbox()
    try:
        outside_scripts = box.tmp / 'outside-scripts'
        plugin_dir = outside_scripts / 'OPNsense' / 'DeviceMonitor'
        plugin_dir.mkdir(parents=True)
        marker = plugin_dir / 'must-survive.txt'
        marker.write_text('outside plugin data\n')

        outside_rc = box.tmp / 'outside-rc.conf.local'
        outside_rc.write_text('devicemonitor_enable="YES"\n')
        rc_link = box.path(RC_LOCAL)
        rc_link.parent.mkdir(parents=True, exist_ok=True)
        rc_link.symlink_to(outside_rc)

        scripts_link = box.path('/usr/local/opnsense/scripts')
        scripts_link.parent.mkdir(parents=True, exist_ok=True)
        scripts_link.symlink_to(outside_scripts, target_is_directory=True)

        outside_locale = box.tmp / 'outside-locale'
        target = outside_locale / 'en_US' / 'LC_MESSAGES' / 'OPNsense.mo'
        target.parent.mkdir(parents=True)
        target.write_text('outside catalogue\n')
        locale_link = box.path('/usr/local/share/locale')
        locale_link.parent.mkdir(parents=True, exist_ok=True)
        locale_link.symlink_to(outside_locale, target_is_directory=True)
        box.write('/var/backups/devicemonitor/core-locale/en_US.state',
                  'pristine=abc123\ntarget=/usr/local/share/locale/en_US/LC_MESSAGES/OPNsense.mo\n'
                  'installed=abc123\n')
        box.write('/var/backups/devicemonitor/core-locale/en_US.OPNsense.mo', 'pristine\n')

        done = box.run(STUB_SHA256='abc123', STUB_SHA256_EXIT='0')

        assert done.returncode == 0, (done.stdout, done.stderr)
        assert marker.read_text() == 'outside plugin data\n'
        assert outside_rc.read_text() == 'devicemonitor_enable="YES"\n'
        assert target.read_text() == 'outside catalogue\n'
        assert done.stderr.count('UNSAFE_ESCAPE:') >= 3, done.stderr
    finally:
        box.close()


CASES = [
    test_static_contract,
    test_cache_invalidation_and_preservation,
    test_silent_mode_preserves_plugin_data_and_skips_services,
    test_locale_bootstrap_and_update_action_are_removed_only,
    test_every_manifest_target_is_removed,
    test_required_command_failures_propagate,
    test_isolated_root_must_be_canonical_and_not_live_root,
    test_recorded_core_target_cannot_escape_the_root,
    test_destructive_guards_reject_symlink_escapes,
]


def main():
    for case in CASES:
        case()
        print('  %-58s PASS' % case.__name__)
    print('UNINSTALLER_TEST=PASS cases=%d' % len(CASES))


if __name__ == '__main__':
    main()
