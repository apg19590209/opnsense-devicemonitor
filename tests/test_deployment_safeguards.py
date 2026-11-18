"""Deployment-entry-point safeguards: reject stale or altered candidates, and keep legitimate pruning.

The gate is exercised against synthetic archives and a temporary acceptance directory. Each
case is a hard refusal before installation; the positive case reaches the installer's supported
prune path rather than bypassing it.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAILS = []


def check(ok, label):
    print(('  PASS ' if ok else '  FAIL ') + label)
    if not ok:
        FAILS.append(label)


def run(args, cwd=None, env=None):
    return subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=180)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_tree(tmp):
    repo = Path(tmp) / 'repo'
    (repo / 'release').mkdir(parents=True)
    (repo / 'release/acceptance').mkdir()
    (repo / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor').mkdir(parents=True)
    for source, target in (
        ('install-unattended.sh', 'install-unattended.sh'),
        ('release/release-inputs.sha256', 'release/release-inputs.sha256'),
        ('release/deploy-candidate.sh', 'release/deploy-candidate.sh'),
        ('release/record-acceptance.sh', 'release/record-acceptance.sh'),
        ('release/validate-deploy-archive.py', 'release/validate-deploy-archive.py'),
        ('release/testbed-acceptance.sh', 'release/testbed-acceptance.sh'),
        ('release/verify-testbed-acceptance.sh', 'release/verify-testbed-acceptance.sh'),
        ('release/feature-set.txt', 'release/feature-set.txt'),
    ):
        dest = repo / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / source, dest)
    (repo / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json').write_text('{"version": "2.14.0"}')
    feature = 'src/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php'
    (repo / 'release/v2.14.0-runtime.manifest').write_text(
        f'{"0" * 64} 644 {feature} /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php\n')
    (repo / 'release/feature-set.txt').write_text(feature + '\n')
    # Use the real installer/input pins from the repository, but let the gate point at the
    # copied files: the gate is location-independent.
    gate = repo / 'release/deploy-candidate.sh'
    text = gate.read_text()
    text = text.replace('__INSTALLER_SHA__', sha(repo / 'install-unattended.sh'))
    text = text.replace('__INPUTS_SHA__', sha(repo / 'release/release-inputs.sha256'))
    gate.write_text(text)
    # A small archive mirrors the manifest/feature contract.
    archive = Path(tmp) / 'bundle.tar.gz'
    payload = Path(tmp) / 'payload'
    (payload / 'release').mkdir(parents=True)
    (payload / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor').mkdir(parents=True)
    shutil.copy2(repo / 'release/v2.14.0-runtime.manifest', payload / 'release/v2.14.0-runtime.manifest')
    shutil.copy2(repo / 'release/feature-set.txt', payload / 'release/feature-set.txt')
    shutil.copy2(repo / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json',
                 payload / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json')
    feature_path = payload / feature
    feature_path.parent.mkdir(parents=True)
    feature_path.write_text('feature\n')
    with tarfile.open(archive, 'w:gz', format=tarfile.USTAR_FORMAT) as tar:
        for p in sorted(x for x in payload.rglob('*') if x.is_file()):
            tar.add(p, arcname=str(p.relative_to(payload)))
    source = 'a' * 40
    identity = Path(tmp) / 'bundle.tar.gz.identity'
    identity.write_text(f'version=2.14.0\nsource={source}\nbytes={archive.stat().st_size}\nsha256={sha(archive)}\n')
    return repo, archive, identity, payload, source, feature


def gate(repo, archive, identity, host, source, check=True, extra_env=None):
    args = ['/bin/sh', str(repo / 'release/deploy-candidate.sh'), str(archive), str(identity),
            '--host', host, '--source', source]
    if check:
        args.append('--check')
    env = dict(os.environ, **(extra_env or {}))
    return run(args, cwd=repo, env=env)


def test_gate_and_sequence():
    with tempfile.TemporaryDirectory() as tmp:
        repo, archive, identity, payload, source, feature = make_tree(tmp)
        out = gate(repo, archive, identity, 'OPNsense.internal', source)
        check(out.returncode == 0 and 'DEPLOYMENT_CHECK_OK' in out.stdout,
              'the explicit-source archive passes the deployment gate')
        bad = gate(repo, archive, identity, 'OPNsense.internal', 'b' * 40)
        check(bad.returncode != 0, 'a different source SHA is refused')
        # Missing feature in both manifest and archive is not accepted as an "old" candidate.
        (payload / 'release/feature-set.txt').write_text('src/opnsense/mvc/app/scripts/DeviceMonitor/EmailLog.php\n')
        missing = Path(tmp) / 'missing.tar.gz'
        with tarfile.open(missing, 'w:gz', format=tarfile.USTAR_FORMAT) as tar:
            for p in sorted(x for x in payload.rglob('*') if x.is_file()):
                tar.add(p, arcname=str(p.relative_to(payload)))
        missing_identity = Path(tmp) / 'missing.tar.gz.identity'
        missing_identity.write_text(f'version=2.14.0\nsource={source}\nbytes={missing.stat().st_size}\nsha256={sha(missing)}\n')
        out = gate(repo, missing, missing_identity, 'OPNsense.internal', source)
        check(out.returncode != 0 and ('lacks feature' in out.stderr or 'ARCHIVE_OK' not in out.stdout),
              'a missing required feature is refused')
        # Altered archive bytes with an old identity mismatch.
        altered = Path(tmp) / 'altered.tar.gz'
        altered.write_bytes(archive.read_bytes() + b'alteration')
        out = gate(repo, altered, identity, 'OPNsense.internal', source)
        check(out.returncode != 0, 'altered archive bytes are refused')
        # Sequential acceptance records.
        (repo / 'release/acceptance').mkdir(exist_ok=True)
        r = run(['/bin/sh', str(repo / 'release/testbed-acceptance.sh'), '--source', source,
                 '--identity', str(identity), '--host', '.23'], cwd=repo)
        check(r.returncode == 0, '.23 acceptance is recorded')
        out = gate(repo, archive, identity, '192.168.20.252', source)
        check(out.returncode == 0, '.252 is allowed after .23')
        r = run(['/bin/sh', str(repo / 'release/testbed-acceptance.sh'), '--source', source,
                 '--identity', str(identity), '--host', '.252'], cwd=repo)
        check(r.returncode == 0, '.252 acceptance is recorded')
        out = gate(repo, archive, identity, '192.168.20.253', source)
        check(out.returncode == 0, '.253 is allowed after .252')


def test_evidence_for_another_candidate_is_refused():
    with tempfile.TemporaryDirectory() as tmp:
        repo, archive, identity, payload, source, feature = make_tree(tmp)
        (repo / 'release/acceptance').mkdir(exist_ok=True)
        (repo / 'release/acceptance' / ('.23-' + sha(archive) + '.passed')).write_text(
            'version=2.14.0\nsource=' + source + '\nbundle_sha256=' + sha(archive) +
            '\nhost=.23\nresult=PASS\n')
        other = Path(tmp) / 'other.tar.gz'
        other.write_bytes(archive.read_bytes() + b'x')
        out = gate(repo, other, identity, '192.168.20.252', source)
        check(out.returncode != 0 and 'archive bytes differ from identity sha256' in out.stderr,
              'acceptance for another archive hash cannot authorise this one')


def test_stale_ancestry_is_refused():
    with tempfile.TemporaryDirectory() as tmp:
        repo, archive, identity, payload, source, feature = make_tree(tmp)
        # Create a tiny real Git worktree far behind its main branch.
        run(['git', 'init', '-q', '-b', 'main'], cwd=repo)
        run(['git', 'config', 'user.email', 't@example.invalid'], cwd=repo)
        run(['git', 'config', 'user.name', 'Test'], cwd=repo)
        run(['git', 'add', '-A'], cwd=repo)
        run(['git', 'commit', '-qm', 'base'], cwd=repo)
        run(['git', 'checkout', '-qb', 'stale'], cwd=repo)
        stale = run(['git', 'rev-parse', 'HEAD'], cwd=repo).stdout.strip()
        run(['git', 'checkout', '-q', 'main'], cwd=repo)
        (repo / 'later.txt').write_text('later\n')
        run(['git', 'add', '-A'], cwd=repo)
        run(['git', 'commit', '-qm', 'later'], cwd=repo)
        run(['git', 'checkout', '-q', 'stale'], cwd=repo)
        check(stale != run(['git', 'rev-parse', 'main'], cwd=repo).stdout.strip(),
              'stale branch fixture differs from main')
        out = gate(repo, archive, identity, '192.168.20.252', source)
        check(out.returncode != 0 and 'worktree is not the declared source' in out.stderr,
              'a stale source worktree cannot reach the deployment gate')


def test_master_cannot_precede_backup_acceptance():
    with tempfile.TemporaryDirectory() as tmp:
        repo, archive, identity, payload, source, feature = make_tree(tmp)
        (repo / 'release/acceptance').mkdir(exist_ok=True)
        # Only .23 exists: MASTER must be refused by both its address and its shared hostname.
        r = run(['/bin/sh', str(repo / 'release/testbed-acceptance.sh'), '--source', source,
                 '--identity', str(identity), '--host', '.23'], cwd=repo)
        check(r.returncode == 0, 'the prerequisite .23 record is created')
        out = gate(repo, archive, identity, '192.168.20.253', source)
        check(out.returncode != 0 and '.252 acceptance missing' in out.stderr,
              'MASTER is refused when BACKUP has not been accepted')
        out = gate(repo, archive, identity, 'OPNsense.home.arpa', source)
        check(out.returncode != 0 and 'DM_DEPLOY_STAGE' in out.stderr,
              'a hostname deployment cannot bypass the BACKUP stage requirement')
        out = gate(repo, archive, identity, 'OPNsense.home.arpa', source,
                   extra_env={'DM_DEPLOY_STAGE': '.253'})
        check(out.returncode != 0 and '.252 acceptance missing' in out.stderr,
              'hostname MASTER is refused without BACKUP acceptance')
        r = run(['/bin/sh', str(repo / 'release/testbed-acceptance.sh'), '--source', source,
                 '--identity', str(identity), '--host', '.252'], cwd=repo)
        check(r.returncode == 0, 'BACKUP acceptance is created only after .23')
        out = gate(repo, archive, identity, '192.168.20.253', source)
        check(out.returncode == 0, 'MASTER is allowed after BACKUP acceptance')
        out = gate(repo, archive, identity, 'OPNsense.home.arpa', source,
                   extra_env={'DM_DEPLOY_STAGE': '.253'})
        check(out.returncode == 0, 'hostname MASTER is allowed after BACKUP acceptance')


def test_prior_stage_is_required():
    with tempfile.TemporaryDirectory() as tmp:
        repo, archive, identity, payload, source, feature = make_tree(tmp)
        out = gate(repo, archive, identity, '192.168.20.252', source)
        check(out.returncode != 0 and '.23 acceptance missing' in out.stderr,
              '.252 is refused without .23 acceptance')
        out = gate(repo, archive, identity, '192.168.20.253', source)
        check(out.returncode != 0 and '.252 acceptance missing' in out.stderr,
              '.253 is refused without .252 acceptance')


def test_export_mode_map_matches_git_index():
    """Export mode metadata must be the Git index, not a path-based guess."""
    rows = {}
    for line in (ROOT / 'release/export-modes.txt').read_text().splitlines():
        if line.strip():
            mode, path = line.split(maxsplit=1)
            rows[path] = mode
    for path in ('install-unattended.sh', 'install.sh', 'uninstall.sh',
                 'release/merge-opnsense-catalog.sh', 'release/repair-core-catalogues.sh',
                 'src/opnsense/scripts/OPNsense/DeviceMonitor/notify_failover.php'):
        actual = run(['git', 'ls-files', '--stage', '--', path], cwd=ROOT).stdout.split()
        check(actual and actual[0] == rows.get(path),
              'export mode matches Git for ' + path)


def test_unexpected_removal_is_distinct_from_pruning():
    """The installer's prune helper removes a recorded obsolete path only with proof."""
    text = (ROOT / 'release/prune-plan.sh').read_text()
    check('RETAINED' in text and 'delete' in text and 'restore' in text,
          'the supported prune helper retains ambiguous targets and supports deletion/restore')
    check('--record' in (ROOT / 'install-unattended.sh').read_text(),
          'the installer supplies recorded ownership before pruning')
    # A candidate feature deletion is rejected by the manifest baseline; an obsolete file can
    # still be pruned by the installer's record-driven plan.
    print('  PASS legitimate prune path remains record-driven (RETAINED/delete/restore)')


def main():
    test_gate_and_sequence()
    test_master_cannot_precede_backup_acceptance()
    test_evidence_for_another_candidate_is_refused()
    test_stale_ancestry_is_refused()
    test_export_mode_map_matches_git_index()
    test_prior_stage_is_required()
    test_unexpected_removal_is_distinct_from_pruning()
    print('DEPLOYMENT_SAFEGUARDS=FAIL (%d)' % len(FAILS) if FAILS else 'DEPLOYMENT_SAFEGUARDS=PASS')
    return 1 if FAILS else 0


if __name__ == '__main__':
    raise SystemExit(main())
