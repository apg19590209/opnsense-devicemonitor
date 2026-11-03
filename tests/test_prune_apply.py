"""Prune backup, delete and restore behave like a transaction.

The installer deletes pruned targets only after backing them up into its own rollback
directory, and a failed install has to put both the replaced files and the pruned ones back.
These cases drive `release/prune-plan.sh backup|delete|restore` against a staging tree, so
the rollback path is proven without touching a firewall.
"""
import hashlib
import os
import stat
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'release/prune-plan.sh'

REPLACED = '/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py'
KEPT = '/usr/local/opnsense/mvc/app/languages/cs_CZ/LC_MESSAGES/devicemonitor.mo'
PRUNED = '/usr/local/opnsense/mvc/app/languages/cs_CZ_devicemonitor.po'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(*args):
    done = subprocess.run(['sh', str(HELPER)] + list(args),
                          capture_output=True, text=True, timeout=60)
    return done.returncode, done.stdout, done.stderr


class Sandbox:
    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.root = self.tmp / 'root'
        self.root.mkdir()
        self.backup = self.tmp / 'backup'
        self.current = self.tmp / 'current'
        self.legacy = self.tmp / 'legacy'

    def close(self):
        self._tmp.cleanup()

    def file(self, path, body, mode=0o644):
        target = self.root / path.lstrip('/')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
        os.chmod(target, mode)
        return target

    def on_disk(self, path):
        return self.root / path.lstrip('/')

    def plan(self):
        self.current.write_text('%s\n%s\n' % (REPLACED, KEPT))
        self.legacy.write_text('%s %s\n' % (digest(self.on_disk(PRUNED)), PRUNED))
        out = self.tmp / 'plan'
        code, stdout, stderr = run('compute', '--current', str(self.current),
                                   '--legacy', str(self.legacy), '--root', str(self.root))
        assert code == 0, (code, stdout, stderr)
        assert stdout.split() == ['LEGACY', PRUNED], stdout
        out.write_text(stdout)
        return out


def test_backup_records_verified_copy():
    """backup copies, re-hashes and records every target it plans to remove."""
    box = Sandbox()
    try:
        box.file(REPLACED, 'old scanner\n')
        pruned = box.file(PRUNED, 'legacy catalogue\n', mode=0o640)
        box.file(KEPT, 'generated catalogue\n')
        plan = box.plan()
        before = digest(pruned)
        code, stdout, stderr = run('backup', '--plan', str(plan),
                                   '--backup', str(box.backup), '--root', str(box.root))
        assert code == 0, stderr
        assert 'PRUNE_PLANNED=1' in stdout, stdout
        rows = (box.backup / 'prune').read_text().splitlines()
        assert len(rows) == 1, rows
        ident, recorded, path = rows[0].split(' ', 2)
        assert path == PRUNED and recorded == before, rows
        assert digest(box.backup / 'files' / ident) == before
        # Nothing is deleted by backup: it only stages.
        assert pruned.is_file()
    finally:
        box.close()


def test_delete_counts_only_removed_files():
    """Accounting reports what was removed, so a missing target is not counted."""
    box = Sandbox()
    try:
        box.file(REPLACED, 'old scanner\n')
        pruned = box.file(PRUNED, 'legacy catalogue\n')
        box.file(KEPT, 'generated catalogue\n')
        plan = box.plan()
        run('backup', '--plan', str(plan), '--backup', str(box.backup), '--root', str(box.root))
        code, stdout, stderr = run('delete', '--plan', str(box.backup / 'prune'),
                                   '--root', str(box.root))
        assert code == 0, stderr
        assert 'PRUNED=1' in stdout, stdout
        assert not pruned.exists()
        assert box.on_disk(KEPT).is_file()
        # A second delete has nothing left to remove and must not claim a removal.
        code, stdout, stderr = run('delete', '--plan', str(box.backup / 'prune'),
                                   '--root', str(box.root))
        assert code == 0, stderr
        assert 'PRUNED=0' in stdout, stdout
    finally:
        box.close()


def test_rollback_restores_pruned_and_replaced():
    """A failed install puts back both the replaced file and the pruned one, verified."""
    box = Sandbox()
    try:
        replaced = box.file(REPLACED, 'old scanner\n', mode=0o755)
        pruned = box.file(PRUNED, 'legacy catalogue\n', mode=0o640)
        kept = box.file(KEPT, 'generated catalogue\n')
        old_replaced, old_pruned, old_kept = digest(replaced), digest(pruned), digest(kept)
        new_replaced = 'new scanner\n'

        # The installer's own plan: "<id> <old> <new> <mode> <source> <target>".
        plan = box.tmp / 'install-plan'
        plan.write_text(
            '0 %s %s 755 src/scan_network.py %s\n'
            '1 %s %s 644 src/devicemonitor.mo %s\n' % (
                old_replaced, hashlib.sha256(new_replaced.encode()).hexdigest(), REPLACED,
                old_kept, old_kept, KEPT,
            )
        )
        (box.backup / 'files').mkdir(parents=True)
        # The installer copies with `cp -p`, so the backup carries the original mode.
        copy = box.backup / 'files' / '0'
        copy.write_text('old scanner\n')
        os.chmod(copy, 0o755)

        # Install: one target replaced, then the legacy catalogue pruned.
        prune_plan = box.plan()
        run('backup', '--plan', str(prune_plan), '--backup', str(box.backup),
            '--root', str(box.root))
        run('delete', '--plan', str(box.backup / 'prune'), '--root', str(box.root))
        replaced.write_text(new_replaced)
        assert not pruned.exists()

        # Failure: roll both halves back.
        code, stdout, stderr = run('restore-targets', '--plan', str(plan),
                                   '--backup', str(box.backup), '--root', str(box.root))
        assert code == 0, stderr
        assert 'ROLLBACK_RESTORED=%s' % REPLACED in stdout, stdout
        code, stdout, stderr = run('restore', '--plan', str(box.backup / 'prune'),
                                   '--backup', str(box.backup), '--root', str(box.root))
        assert code == 0, stderr
        assert 'ROLLBACK_RESTORED=%s' % PRUNED in stdout, stdout

        assert digest(replaced) == old_replaced
        assert stat.S_IMODE(os.stat(replaced).st_mode) == 0o755
        assert digest(pruned) == old_pruned
        assert stat.S_IMODE(os.stat(pruned).st_mode) == 0o640
        # The untouched target is neither restored nor reported.
        assert digest(kept) == old_kept
        assert 'ROLLBACK_RESTORED=%s' % KEPT not in stdout
    finally:
        box.close()


def test_restore_reports_conflict_and_failure():
    """A target that reappeared is a reported conflict; an unverifiable restore fails."""
    box = Sandbox()
    try:
        box.file(REPLACED, 'old scanner\n')
        pruned = box.file(PRUNED, 'legacy catalogue\n')
        box.file(KEPT, 'generated catalogue\n')
        plan = box.plan()
        run('backup', '--plan', str(plan), '--backup', str(box.backup), '--root', str(box.root))
        run('delete', '--plan', str(box.backup / 'prune'), '--root', str(box.root))
        pruned.write_text('recreated by something else\n')
        code, stdout, stderr = run('restore', '--plan', str(box.backup / 'prune'),
                                   '--backup', str(box.backup), '--root', str(box.root))
        assert code == 0, stderr
        assert 'ROLLBACK_CONFLICT=%s' % PRUNED in stderr, stderr
        assert pruned.read_text() == 'recreated by something else\n'

        # Corrupt the backed-up copy: the restore must not silently accept it.
        pruned.unlink()
        copy = sorted((box.backup / 'files').iterdir())[0]
        copy.write_text('corrupted backup\n')
        code, stdout, stderr = run('restore', '--plan', str(box.backup / 'prune'),
                                   '--backup', str(box.backup), '--root', str(box.root))
        assert code != 0, (stdout, stderr)
        assert 'ROLLBACK_FAILED=%s' % PRUNED in stderr, stderr
        assert not pruned.exists()
    finally:
        box.close()


CASES = [
    test_backup_records_verified_copy,
    test_delete_counts_only_removed_files,
    test_rollback_restores_pruned_and_replaced,
    test_restore_reports_conflict_and_failure,
]


def main():
    for case in CASES:
        case()
        print('  %-40s PASS' % case.__name__)
    print('PRUNE_APPLY=PASS cases=%d' % len(CASES))


if __name__ == '__main__':
    main()
