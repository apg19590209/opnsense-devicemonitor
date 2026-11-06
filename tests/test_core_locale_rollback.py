"""Focused regressions for the core-locale state snapshot and rollback helper."""
import hashlib
import os
import stat
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'release/core-locale-state.sh'
STATE = '/var/backups/devicemonitor/core-locale'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(*args):
    done = subprocess.run(['sh', str(HELPER)] + [str(arg) for arg in args],
                          capture_output=True, text=True, timeout=120)
    return done.returncode, done.stdout, done.stderr


def snapshot(directory):
    if not directory.exists():
        return {'directory': 'absent'}
    info = directory.stat()
    result = {
        'directory': {
            'mode': stat.S_IMODE(info.st_mode),
            'uid': info.st_uid,
            'gid': info.st_gid,
        },
        'files': {},
    }
    for path in sorted(directory.iterdir()):
        file_info = path.stat()
        result['files'][path.name] = {
            'sha256': digest(path),
            'mode': stat.S_IMODE(file_info.st_mode),
            'uid': file_info.st_uid,
            'gid': file_info.st_gid,
            'mtime': int(file_info.st_mtime),
        }
    return result


class Install:
    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.root = self.tmp / 'root'
        self.root.mkdir()
        self.backup = self.tmp / 'backup'

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


def test_preexisting_state_and_metadata_are_restored_exactly():
    """Restore original bytes, modes and ownership; remove files the failed run created."""
    install = Install()
    try:
        state_dir = install.path(STATE)
        state_dir.mkdir(parents=True)
        os.chmod(state_dir, 0o750)
        install.write(STATE + '/cs_CZ.state',
                      'pristine=old-pristine\n'
                      'target=/usr/local/share/locale/cs_CZ/LC_MESSAGES/OPNsense.mo\n'
                      'installed=old-installed\n', mode=0o640)
        install.write(STATE + '/cs_CZ.OPNsense.mo', 'old archive\n', mode=0o600)
        install.write(STATE + '/operator-note.txt', 'not owned by the installer\n', mode=0o644)
        before = snapshot(state_dir)

        code, out, err = run('backup-core-locale-state', '--state', STATE,
                             '--backup', install.backup, '--root', install.root)
        assert code == 0, err
        assert 'CORE_LOCALE_STATE_BACKED_UP=present files=2' in out, out

        install.write(STATE + '/cs_CZ.state',
                      'pristine=old-pristine\n'
                      'target=/usr/local/share/locale/cs_CZ/LC_MESSAGES/OPNsense.mo\n'
                      'installed=new-installed\n', mode=0o600)
        install.write(STATE + '/cs_CZ.OPNsense.mo', 'new archive\n', mode=0o644)
        install.write(STATE + '/fr_FR.state', 'new state\n')
        install.write(STATE + '/fr_FR.OPNsense.mo', 'new archive\n')
        os.chmod(state_dir, 0o700)

        code, out, err = run('restore-core-locale-state', '--state', STATE,
                             '--backup', install.backup, '--root', install.root)
        assert code == 0, err
        assert 'CORE_LOCALE_ROLLBACK_SUMMARY=restored=2 removed=2 conflicts=0 failed=0' in out, out
        assert snapshot(state_dir) == before
        assert (state_dir / 'operator-note.txt').read_text() == 'not owned by the installer\n'
    finally:
        install.close()


def test_originally_absent_directory_and_files_are_removed():
    """A fresh install's rollback removes the state directory it created."""
    install = Install()
    try:
        code, out, err = run('backup-core-locale-state', '--state', STATE,
                             '--backup', install.backup, '--root', install.root)
        assert code == 0, err
        assert 'CORE_LOCALE_STATE_BACKED_UP=absent files=0' in out, out

        install.write(STATE + '/nl_NL.state', 'new state\n')
        install.write(STATE + '/nl_NL.OPNsense.mo', 'new archive\n')
        code, out, err = run('restore-core-locale-state', '--state', STATE,
                             '--backup', install.backup, '--root', install.root)
        assert code == 0, err
        assert 'CORE_LOCALE_ROLLBACK_SUMMARY=restored=0 removed=2 conflicts=0 failed=0' in out, out
        assert not install.path(STATE).exists()
    finally:
        install.close()


def test_damaged_backup_is_refused_before_mutation():
    """A damaged snapshot cannot overwrite the post-failure state."""
    install = Install()
    try:
        install.write(STATE + '/cs_CZ.state', 'old state\n')
        code, out, err = run('backup-core-locale-state', '--state', STATE,
                             '--backup', install.backup, '--root', install.root)
        assert code == 0, err
        (install.backup / 'core-locale-state/files/cs_CZ.state').write_text('tampered\n')
        install.write(STATE + '/cs_CZ.state', 'new state\n')
        before = snapshot(install.path(STATE))

        code, out, err = run('restore-core-locale-state', '--state', STATE,
                             '--backup', install.backup, '--root', install.root)
        assert code != 0, (code, out, err)
        assert 'ROLLBACK_FAILED=%s/cs_CZ.state (backup digest)' % STATE in err, err
        assert snapshot(install.path(STATE)) == before
    finally:
        install.close()


CASES = [
    test_preexisting_state_and_metadata_are_restored_exactly,
    test_originally_absent_directory_and_files_are_removed,
    test_damaged_backup_is_refused_before_mutation,
]


def main():
    for case in CASES:
        case()
        print('  %-56s PASS' % case.__name__)
    print('CORE_LOCALE_ROLLBACK=PASS cases=%d' % len(CASES))


if __name__ == '__main__':
    main()
