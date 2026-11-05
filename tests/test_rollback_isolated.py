"""The documented rollback procedure, executed end to end in an isolated tree.

H2 of the round-2 review: the plan used to offer "reinstall the published 2.13.2 bundle",
which cannot work — that installer accepts only 2.8…2.13.1 and aborts on 2.13.3. The
procedure is now the installer's own preserved assets:

    prune-plan.sh restore-targets --plan <backup>/plan --backup <backup>
    prune-plan.sh restore         --plan <backup>/prune --backup <backup>
    prune-plan.sh restore-record  --record /var/db/devicemonitor/installed-manifest.txt \
                                  --backup <backup>

This suite rehearses a whole install in a staging root — a replaced target, an unchanged
target, a pruned legacy file and the previous install record — then rolls it back with
exactly those commands and requires the pre-install state back, digests and modes included.
"""
import hashlib
import os
import stat
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'release/prune-plan.sh'

SCAN = '/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py'
MO = '/usr/local/opnsense/mvc/app/languages/cs_CZ/LC_MESSAGES/devicemonitor.mo'
LEGACY_PO = '/usr/local/opnsense/mvc/app/languages/cs_CZ_devicemonitor.po'
RECORD = '/var/db/devicemonitor/installed-manifest.txt'
CORE_STATE = '/var/backups/devicemonitor/core-locale'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(*args):
    done = subprocess.run(['sh', str(HELPER)] + [str(a) for a in args],
                          capture_output=True, text=True, timeout=120)
    return done.returncode, done.stdout, done.stderr


class Install:
    """A staging root that behaves like the firewall paths the installer uses."""

    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.root = self.tmp / 'root'
        self.root.mkdir()
        self.backup = self.tmp / 'backup'
        self.plan = self.tmp / 'plan'
        self.prune_plan = self.tmp / 'prune-targets'

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

    # --- the installer's own steps, in its own order -------------------------------

    def stage(self, replaced_old, replaced_new, unchanged):
        self.write(SCAN, replaced_old, mode=0o755)
        self.write(MO, unchanged)
        self.prune_plan.write_text(
            'LEGACY %s\n' % LEGACY_PO
        )
        plan_rows = [
            (0, digest(self.path(SCAN)), hashlib.sha256(replaced_new.encode()).hexdigest(),
             755, 'src/scan_network.py', SCAN),
            (1, digest(self.path(MO)), digest(self.path(MO)),
             644, 'src/devicemonitor.mo', MO),
        ]
        self.plan.write_text(''.join('%d %s %s %s %s %s\n' % row for row in plan_rows))
        self.backup.mkdir(parents=True, exist_ok=True)
        (self.backup / 'files').mkdir(exist_ok=True)
        for row in plan_rows:
            ident, old = row[0], row[1]
            if row[2] != old:  # only a target that will actually change is backed up
                copy = self.backup / 'files' / str(ident)
                copy.write_bytes(self.path(row[5]).read_bytes())
                os.chmod(copy, stat.S_IMODE(os.stat(self.path(row[5])).st_mode))

    def backup_record(self):
        return run('backup-record', '--record', RECORD, '--backup', self.backup,
                   '--root', self.root)

    def backup_prune(self):
        return run('backup', '--plan', self.prune_plan, '--backup', self.backup,
                   '--root', self.root)

    def delete_prune(self):
        return run('delete', '--plan', self.backup / 'prune', '--root', self.root)

    def apply_install(self, replaced_new, new_record):
        self.path(SCAN).write_text(replaced_new)
        self.write(RECORD, new_record)

    # --- the documented manual rollback --------------------------------------------

    def rollback(self):
        steps = []
        steps.append(run('restore-targets', '--plan', self.plan, '--backup', self.backup,
                         '--root', self.root))
        if (self.backup / 'prune').is_file():
            steps.append(run('restore', '--plan', self.backup / 'prune', '--backup',
                             self.backup, '--root', self.root))
        steps.append(run('restore-record', '--record', RECORD, '--backup', self.backup,
                         '--root', self.root))
        return steps


def test_manual_rollback_restores_the_pre_install_state():
    """Rehearse install → documented manual rollback and compare against the pre-state."""
    install = Install()
    try:
        old_scan, new_scan = 'old scanner\n', 'new scanner\n'
        unchanged = 'catalogue\n'
        install.stage(old_scan, new_scan, unchanged)
        install.write(LEGACY_PO, 'legacy catalogue\n', mode=0o640)

        # The previous install's record: the target set it declared, with digests.
        old_record = (
            '# Device Monitor 2.13.2 install record (Decision 62).\n'
            '# Format: <sha256> <absolute installed target>\n'
            '%s %s\n%s %s\n' % (digest(install.path(SCAN)), SCAN,
                                digest(install.path(MO)), MO)
        )
        install.write(RECORD, old_record)
        before = {
            'scan': digest(install.path(SCAN)),
            'scan_mode': stat.S_IMODE(os.stat(install.path(SCAN)).st_mode),
            'mo': digest(install.path(MO)),
            'po': digest(install.path(LEGACY_PO)),
            'po_mode': stat.S_IMODE(os.stat(install.path(LEGACY_PO)).st_mode),
            'record': digest(install.path(RECORD)),
        }

        # Pre-install: back up the record and the pruned target, then prune.
        code, out, err = install.backup_record()
        assert code == 0, err
        assert 'RECORD_BACKED_UP=%s' % RECORD in out, out
        code, out, err = install.backup_prune()
        assert code == 0, err
        assert 'PRUNE_PLANNED=1' in out, out
        code, out, err = install.delete_prune()
        assert code == 0, err
        assert 'PRUNED=1' in out, out
        assert not install.path(LEGACY_PO).exists()

        # The install itself: one target replaced, and a new record written.
        new_record = ('# Device Monitor 2.13.3 install record (Decision 62).\n'
                      '# Format: <sha256> <absolute installed target>\n'
                      '%s %s\n' % (hashlib.sha256(new_scan.encode()).hexdigest(), SCAN))
        install.apply_install(new_scan, new_record)
        assert digest(install.path(RECORD)) != before['record']

        # The documented rollback, exactly as the plan states it.
        for code, out, err in install.rollback():
            assert code == 0, err
            assert 'ROLLBACK_FAILED' not in err, err
            assert 'ROLLBACK_CONFLICT' not in err, err

        assert digest(install.path(SCAN)) == before['scan']
        assert stat.S_IMODE(os.stat(install.path(SCAN)).st_mode) == before['scan_mode']
        assert digest(install.path(MO)) == before['mo']
        assert digest(install.path(LEGACY_PO)) == before['po']
        assert stat.S_IMODE(os.stat(install.path(LEGACY_PO)).st_mode) == before['po_mode']
        assert digest(install.path(RECORD)) == before['record'], 'record not restored'
        assert install.path(RECORD).read_text() == old_record
    finally:
        install.close()


def test_fresh_install_rollback_removes_the_new_record():
    """A run that created the record removes it again when it is rolled back."""
    install = Install()
    try:
        install.stage('old scanner\n', 'new scanner\n', 'catalogue\n')
        code, out, err = install.backup_record()
        assert code == 0, err
        assert 'RECORD_BACKED_UP=absent' in out, out

        install.write(RECORD, '# Device Monitor 2.13.3 install record\n')
        code, out, err = run('restore-record', '--record', RECORD, '--backup', install.backup,
                             '--root', install.root)
        assert code == 0, err
        assert 'RECORD_REMOVED=%s' % RECORD in out, out
        assert not install.path(RECORD).exists()
    finally:
        install.close()


def test_restore_record_reports_a_damaged_backup():
    """A corrupted record backup must fail loudly instead of restoring wrong content."""
    install = Install()
    try:
        install.stage('old scanner\n', 'new scanner\n', 'catalogue\n')
        install.write(RECORD, '%s %s\n' % (digest(install.path(SCAN)), SCAN))
        code, out, err = install.backup_record()
        assert code == 0, err
        install.path(RECORD).unlink()
        (install.backup / 'installed-manifest.txt').write_text('tampered\n')
        code, out, err = run('restore-record', '--record', RECORD, '--backup', install.backup,
                             '--root', install.root)
        assert code != 0, (code, out, err)
        assert 'ROLLBACK_FAILED=%s (backup digest)' % RECORD in err, err
        assert not install.path(RECORD).exists(), 'nothing may be written from a bad backup'
    finally:
        install.close()


def test_core_locale_state_rollback_restores_existing_state_and_archives():
    """A failed install restores .state files and pristine catalogues exactly."""
    install = Install()
    try:
        state_dir = install.path(CORE_STATE)
        state_dir.mkdir(parents=True)
        os.chmod(state_dir, 0o750)
        old_state = ('pristine=old-pristine\n'
                     'target=/usr/local/share/locale/cs_CZ/LC_MESSAGES/OPNsense.mo\n'
                     'installed=old-installed\n')
        install.write(CORE_STATE + '/cs_CZ.state', old_state, mode=0o640)
        install.write(CORE_STATE + '/cs_CZ.OPNsense.mo', 'old archive\n', mode=0o600)
        before = {}
        for path in (state_dir, state_dir / 'cs_CZ.state', state_dir / 'cs_CZ.OPNsense.mo'):
            info = os.stat(path)
            before[str(path)] = (path.read_bytes() if path.is_file() else None,
                                 stat.S_IMODE(info.st_mode), info.st_uid, info.st_gid)

        code, out, err = run('backup-core-locale-state', '--state', CORE_STATE,
                             '--backup', install.backup, '--root', install.root)
        assert code == 0, err
        assert 'CORE_LOCALE_STATE_BACKED_UP=present files=2' in out, out

        install.write(CORE_STATE + '/cs_CZ.state',
                      old_state.replace('old-installed', 'new-installed'), mode=0o600)
        install.write(CORE_STATE + '/cs_CZ.OPNsense.mo', 'new archive\n', mode=0o644)
        install.write(CORE_STATE + '/fr_FR.state', 'new state\n')
        install.write(CORE_STATE + '/fr_FR.OPNsense.mo', 'new archive\n')
        os.chmod(state_dir, 0o700)

        code, out, err = run('restore-core-locale-state', '--state', CORE_STATE,
                             '--backup', install.backup, '--root', install.root)
        assert code == 0, err
        assert 'CORE_LOCALE_ROLLBACK_SUMMARY=restored=2 removed=2 conflicts=0 failed=0' in out, out
        for path in (state_dir, state_dir / 'cs_CZ.state', state_dir / 'cs_CZ.OPNsense.mo'):
            info = os.stat(path)
            body = path.read_bytes() if path.is_file() else None
            assert (body, stat.S_IMODE(info.st_mode), info.st_uid, info.st_gid) == before[str(path)]
        assert not (state_dir / 'fr_FR.state').exists()
        assert not (state_dir / 'fr_FR.OPNsense.mo').exists()
    finally:
        install.close()


def test_core_locale_state_rollback_removes_a_directory_created_by_the_failed_run():
    """When no state directory existed before, rollback removes it and its created files."""
    install = Install()
    try:
        code, out, err = run('backup-core-locale-state', '--state', CORE_STATE,
                             '--backup', install.backup, '--root', install.root)
        assert code == 0, err
        assert 'CORE_LOCALE_STATE_BACKED_UP=absent files=0' in out, out

        install.write(CORE_STATE + '/nl_NL.state', 'new state\n')
        install.write(CORE_STATE + '/nl_NL.OPNsense.mo', 'new archive\n')
        code, out, err = run('restore-core-locale-state', '--state', CORE_STATE,
                             '--backup', install.backup, '--root', install.root)
        assert code == 0, err
        assert 'CORE_LOCALE_ROLLBACK_SUMMARY=restored=0 removed=2 conflicts=0 failed=0' in out, out
        assert not install.path(CORE_STATE).exists()
    finally:
        install.close()


def test_core_locale_state_rollback_rejects_a_damaged_backup_before_mutation():
    """A damaged state backup leaves the post-failure state untouched."""
    install = Install()
    try:
        install.write(CORE_STATE + '/cs_CZ.state', 'old state\n')
        code, out, err = run('backup-core-locale-state', '--state', CORE_STATE,
                             '--backup', install.backup, '--root', install.root)
        assert code == 0, err
        (install.backup / 'core-locale-state/files/cs_CZ.state').write_text('tampered\n')
        install.write(CORE_STATE + '/cs_CZ.state', 'new state\n')
        code, out, err = run('restore-core-locale-state', '--state', CORE_STATE,
                             '--backup', install.backup, '--root', install.root)
        assert code != 0, (code, out, err)
        assert 'ROLLBACK_FAILED=%s/cs_CZ.state (backup digest)' % CORE_STATE in err, err
        assert install.path(CORE_STATE + '/cs_CZ.state').read_text() == 'new state\n'
    finally:
        install.close()


CASES = [
    test_manual_rollback_restores_the_pre_install_state,
    test_fresh_install_rollback_removes_the_new_record,
    test_restore_record_reports_a_damaged_backup,
    test_core_locale_state_rollback_restores_existing_state_and_archives,
    test_core_locale_state_rollback_removes_a_directory_created_by_the_failed_run,
    test_core_locale_state_rollback_rejects_a_damaged_backup_before_mutation,
]


def main():
    for case in CASES:
        case()
        print('  %-48s PASS' % case.__name__)
    print('ROLLBACK_ISOLATED=PASS cases=%d' % len(CASES))


if __name__ == '__main__':
    main()
