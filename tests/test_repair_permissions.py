"""Repair behaviour for modes and ownership (M6).

Decision 64 defines the repair contract: a byte-identical target is not rewritten, but its
mode and ownership are enforced against the manifest mode and `root:wheel`. Unsafe drift —
a world-writable plugin file, a foreign owner — therefore never survives a repair, while an
already correct target is left completely alone (no mtime change, no chown).
"""
import os
import stat
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'release/prune-plan.sh'
TARGET = '/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py'


def run(*args):
    done = subprocess.run(['sh', str(HELPER)] + [str(a) for a in args],
                          capture_output=True, text=True, timeout=60)
    return done.returncode, done.stdout, done.stderr


class Tree:
    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / 'root'
        self.root.mkdir(parents=True)

    def close(self):
        self._tmp.cleanup()

    def file(self, mode):
        target = self.root / TARGET.lstrip('/')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('body\n')
        os.chmod(target, mode)
        return target

    def enforce(self, mode, owner=None, group=None):
        args = ['enforce-target', '--target', TARGET, '--mode', mode, '--root', self.root]
        if owner:
            args += ['--owner', owner, '--group', group]
        return run(*args)


def test_world_writable_file_is_repaired():
    """0777 on a plugin file is unsafe drift: a repair restores the manifest mode."""
    tree = Tree()
    try:
        target = tree.file(0o777)
        code, out, err = tree.enforce('644')
        assert code == 0, err
        assert out.startswith('REPAIRED=%s 644' % TARGET), out
        assert stat.S_IMODE(os.stat(target).st_mode) == 0o644
    finally:
        tree.close()


def test_script_mode_is_repaired_to_executable():
    """A 644 script is drift too: the manifest says 755."""
    tree = Tree()
    try:
        target = tree.file(0o644)
        code, out, err = tree.enforce('755')
        assert code == 0, err
        assert out.startswith('REPAIRED='), out
        assert stat.S_IMODE(os.stat(target).st_mode) == 0o755
    finally:
        tree.close()


def test_correct_target_is_untouched():
    """An already correct file is not rewritten, re-chmodded or re-chowned."""
    tree = Tree()
    try:
        target = tree.file(0o644)
        os.utime(target, (1000000000, 1000000000))
        before = target.stat()
        code, out, err = tree.enforce('644')
        assert code == 0, err
        assert out.startswith('ENFORCED=%s' % TARGET), out
        after = target.stat()
        assert stat.S_IMODE(after.st_mode) == 0o644
        assert after.st_mtime == before.st_mtime, 'mtime must be preserved'
        assert after.st_uid == before.st_uid and after.st_gid == before.st_gid
    finally:
        tree.close()


def test_ownership_is_enforced_and_failure_aborts():
    """Ownership is part of the contract; an impossible chown is a hard failure."""
    tree = Tree()
    try:
        target = tree.file(0o644)
        owner = subprocess.run(['stat', '-c', '%U'], capture_output=True, text=True)
        if owner.returncode != 0:
            owner = subprocess.run(['stat', '-f', '%Su'], capture_output=True, text=True)
        group = subprocess.run(['stat', '-c', '%G'], capture_output=True, text=True)
        if group.returncode != 0:
            group = subprocess.run(['stat', '-f', '%Sg'], capture_output=True, text=True)
        current_owner, current_group = owner.stdout.strip(), group.stdout.strip()

        # Enforcing the ownership it already has is a no-op, not a rewrite.
        code, out, err = tree.enforce('644', current_owner, current_group)
        assert code == 0, err
        assert out.startswith('ENFORCED='), out

        # An impossible ownership must not be silently skipped.
        code, out, err = tree.enforce('644', 'no-such-user-dm', 'no-such-group-dm')
        assert code != 0, (code, out, err)
        assert 'cannot set' in err, err
        assert stat.S_IMODE(os.stat(target).st_mode) == 0o644
    finally:
        tree.close()


CASES = [
    test_world_writable_file_is_repaired,
    test_script_mode_is_repaired_to_executable,
    test_correct_target_is_untouched,
    test_ownership_is_enforced_and_failure_aborts,
]


def main():
    for case in CASES:
        case()
        print('  %-44s PASS' % case.__name__)
    print('REPAIR_PERMISSIONS=PASS cases=%d' % len(CASES))


if __name__ == '__main__':
    main()
