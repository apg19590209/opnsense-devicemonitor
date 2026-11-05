"""The prune plan deletes only files the plugin can prove it owns.

`release/prune-plan.sh compute` is the single decider behind pruning. It is given the full
target set of the run that is about to install (`--current`), the previous install's own
record (`--record`) and the published digests of historical releases (`--legacy`). It prints
`<SOURCE> <path>` for every target it will delete and `RETAINED <reason> <path>` on stderr
for everything it refuses to touch.

Every case below runs root-free against a staging tree (`--root`), so the plan and its
guards are exercised without a firewall.
"""
import hashlib
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'release/prune-plan.sh'

SCAN = '/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py'
MO = '/usr/local/opnsense/mvc/app/languages/cs_CZ/LC_MESSAGES/devicemonitor.mo'
DROPPED_MO = '/usr/local/opnsense/mvc/app/languages/zh_CN/LC_MESSAGES/devicemonitor.mo'
STALE = '/usr/local/opnsense/mvc/app/languages/cs_CZ_devicemonitor.po'
NOTIFY = '/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/notify_failover_v1.php'
RC = '/etc/rc.conf.d/devicemonitor'
SHARE_MO = '/usr/local/share/locale/de_DE/LC_MESSAGES/OPNsense.mo'


class Tree:
    """A staging root with the files each scenario needs."""

    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.root = self.tmp / 'root'
        self.root.mkdir()
        self.current = self.tmp / 'current'
        self.record = self.tmp / 'record'
        self.legacy = self.tmp / 'legacy'
        self.current.write_text('')
        self.record.write_text('')
        self.legacy.write_text('')

    def close(self):
        self._tmp.cleanup()

    def file(self, path, body):
        target = self.on_disk(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
        return target

    def on_disk(self, path):
        return self.root / path.lstrip('/')

    def run(self, current=None, record=None, legacy=None):
        args = ['sh', str(HELPER), 'compute',
                '--current', str(current or self.current),
                '--root', str(self.root)]
        if record is not False:
            args += ['--record', str(record or self.record)]
        if legacy is not False:
            args += ['--legacy', str(legacy or self.legacy)]
        done = subprocess.run(args, capture_output=True, text=True, timeout=60)
        assert done.returncode == 0, (done.returncode, done.stdout, done.stderr)
        plan = [line.split(' ', 1) for line in done.stdout.splitlines() if line.strip()]
        retained = [line.split(' ', 2) for line in done.stderr.splitlines() if line.strip()]
        return plan, retained


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_current(tree, *paths):
    tree.current.write_text(''.join(p + '\n' for p in paths))


def write_record(tree, mapping=None, bare=()):
    lines = ['%s %s\n' % (value, path) for path, value in (mapping or {}).items()]
    lines += ['%s\n' % path for path in bare]
    tree.record.write_text(''.join(lines))


def write_legacy(tree, mapping):
    tree.legacy.write_text(''.join('%s %s\n' % (value, path) for path, value in mapping.items()))


def test_current_targets_never_pruned():
    """A path this run installs is never a candidate, whatever the record says."""
    tree = Tree()
    try:
        tree.file(SCAN, 'current body\n')
        tree.file(MO, 'generated body\n')
        write_current(tree, SCAN, MO)
        write_record(tree, bare=[SCAN, MO])
        plan, retained = tree.run()
        assert plan == [], plan
        assert retained == [], retained
    finally:
        tree.close()


def test_current_generated_retained():
    """The .mo files built by this run stay, even though no manifest row lists them.

    This is the trap the 2.13.2 review found: with the manifest alone as the current side,
    the eleven freshly compiled catalogues look stale and are deleted right after install.
    """
    tree = Tree()
    try:
        generated = ['/usr/local/opnsense/mvc/app/languages/%s/LC_MESSAGES/devicemonitor.mo'
                     % lang for lang in ('cs_CZ', 'de_DE', 'zh_CN')]
        for path in generated:
            tree.file(path, 'catalogue for ' + path)
        write_current(tree, SCAN, *generated)
        # The record carries an older release's digests for the same catalogue paths.
        write_record(tree, {path: 'f' * 64 for path in generated})
        plan, retained = tree.run()
        assert plan == [], plan
        assert retained == [], retained
    finally:
        tree.close()


def test_namespace_guard():
    """A recorded or evidenced path outside the approved namespaces is never a candidate."""
    tree = Tree()
    try:
        tree.file(RC, 'devicemonitor_enable="YES"\n')
        tree.file(SHARE_MO, 'core catalogue\n')
        write_current(tree, SCAN)
        write_record(tree, bare=[RC, SHARE_MO])
        write_legacy(tree, {RC: 'a' * 64})
        plan, retained = tree.run()
        assert plan == [], plan
        # Not even reported as retained: it was never a candidate.
        assert retained == [], retained
    finally:
        tree.close()


def test_legacy_requires_evidence():
    """Without trusted evidence a leftover file is never pruned."""
    tree = Tree()
    try:
        tree.file(STALE, 'legacy catalogue\n')
        write_current(tree, SCAN)
        plan, retained = tree.run(legacy=False)
        assert plan == [], plan
        assert retained == [], retained
        tree.legacy.write_text('# no rows\n')
        plan, retained = tree.run()
        assert plan == [], plan
        assert retained == [], retained
    finally:
        tree.close()


def test_legacy_prunes_verified_file():
    """An unchanged historical file that a published manifest shipped is pruned."""
    tree = Tree()
    try:
        stale = tree.file(STALE, 'legacy catalogue\n')
        write_current(tree, SCAN)
        write_legacy(tree, {STALE: digest(stale)})
        plan, retained = tree.run()
        assert plan == [['LEGACY', STALE]], plan
        assert retained == [], retained
    finally:
        tree.close()

def test_modified_legacy_retained():
    """A historical file whose content changed is retained and reported, never deleted."""
    tree = Tree()
    try:
        tree.file(STALE, 'legacy catalogue, edited by an operator\n')
        write_current(tree, SCAN)
        write_legacy(tree, {STALE: 'b' * 64})
        plan, retained = tree.run()
        assert plan == [], plan
        assert retained == [['RETAINED', 'modified', STALE]], retained
    finally:
        tree.close()


def test_modified_recorded_retained():
    """Same for a path the previous install recorded with a digest."""
    tree = Tree()
    try:
        tree.file(NOTIFY, 'edited after install\n')
        write_current(tree, SCAN)
        write_record(tree, {NOTIFY: 'c' * 64})
        plan, retained = tree.run()
        assert plan == [], plan
        assert retained == [['RETAINED', 'modified', NOTIFY]], retained
    finally:
        tree.close()


def test_dropped_generated_identified():
    """A generated catalogue the new release no longer produces is identified safely."""
    tree = Tree()
    try:
        dropped = tree.file(DROPPED_MO, 'catalogue of a dropped language\n')
        write_current(tree, SCAN, MO)
        write_record(tree, {DROPPED_MO: digest(dropped)})
        plan, retained = tree.run()
        assert plan == [['RECORD', DROPPED_MO]], plan
        assert retained == [], retained
    finally:
        tree.close()


def test_empty_and_identical():
    """An empty record and a record identical to the current set both plan nothing."""
    tree = Tree()
    try:
        tree.file(SCAN, 'current body\n')
        write_current(tree, SCAN)
        plan, retained = tree.run()
        assert plan == [] and retained == [], (plan, retained)
        write_record(tree, {SCAN: digest(tree.on_disk(SCAN))})
        plan, retained = tree.run()
        assert plan == [] and retained == [], (plan, retained)
    finally:
        tree.close()


def test_unsafe_paths_ignored():
    """Traversal and whitespace are corruption, not targets."""
    tree = Tree()
    try:
        tree.file(SCAN, 'current body\n')
        write_current(tree, SCAN, '/usr/local/opnsense/../etc/passwd')
        tree.record.write_text('/usr/local/opnsense/../../etc/passwd\n'
                               '/usr/local/opnsense/scripts with space/x.py\n')
        tree.legacy.write_text('%s /usr/local/opnsense/../etc/passwd\n' % ('d' * 64))
        plan, retained = tree.run()
        assert plan == [] and retained == [], (plan, retained)
    finally:
        tree.close()


def test_bare_record_requires_evidence():
    """A bare-path record entry prunes only with a published digest match (M1, U1).

    The 2.13.2 installer wrote paths without digests. Naming a path proves we once installed
    it, not what is there now, so the record alone can never authorise a deletion.
    """
    tree = Tree()
    try:
        stale = tree.file(STALE, 'legacy catalogue\n')
        write_current(tree, SCAN)
        write_record(tree, bare=[STALE])
        plan, retained = tree.run(legacy=False)
        assert plan == [], plan
        assert retained == [['RETAINED', 'unverified', STALE]], retained

        write_legacy(tree, {STALE: digest(stale)})
        plan, retained = tree.run()
        assert plan == [['LEGACY', STALE]], plan
        assert retained == [], retained
    finally:
        tree.close()


def test_bare_record_modified_retained():
    """A bare-path recorded file that no published digest matches is retained (M1, U1)."""
    tree = Tree()
    try:
        tree.file(STALE, 'edited after install\n')
        write_current(tree, SCAN)
        write_record(tree, bare=[STALE])
        write_legacy(tree, {STALE: 'b' * 64})
        plan, retained = tree.run()
        assert plan == [], plan
        assert retained == [['RETAINED', 'unverified', STALE]], retained
    finally:
        tree.close()


CASES = [
    test_current_targets_never_pruned,
    test_current_generated_retained,
    test_namespace_guard,
    test_legacy_requires_evidence,
    test_legacy_prunes_verified_file,
    test_modified_legacy_retained,
    test_modified_recorded_retained,
    test_dropped_generated_identified,
    test_empty_and_identical,
    test_unsafe_paths_ignored,
    test_bare_record_requires_evidence,
    test_bare_record_modified_retained,
]


def main():
    for case in CASES:
        case()
        print('  %-34s PASS' % case.__name__)
    print('PRUNE_PLAN=PASS cases=%d' % len(CASES))


if __name__ == '__main__':
    main()
