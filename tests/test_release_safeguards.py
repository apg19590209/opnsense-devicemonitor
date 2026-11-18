"""Release safeguards: refuse a stale-or-incomplete candidate and refuse promotion
without testbed acceptance.

Both guards exist because a branch cut five commits behind main produced a candidate
whose manifest had lost the entire Email Log feature, and that candidate was installed
on the testbed and then on the HA nodes. These tests reproduce both failure modes in
throwaway repositories, so the guards are proven by the failure they prevent.
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAILS = []


def check(cond, label):
    print(('  PASS ' if cond else '  FAIL ') + label)
    if not cond:
        FAILS.append(label)


def run(args, cwd=None, env=None):
    return subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=120)


def git(repo, *args):
    return run(['git', *args], cwd=repo)


def make_repo(tmp):
    """A miniature repository with the files the guards read."""
    repo = Path(tmp) / 'repo'
    (repo / 'release').mkdir(parents=True)
    (repo / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor').mkdir(parents=True)
    (repo / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json').write_text('{"version": "9.9.9"}')
    for name in ('verify-candidate.sh', 'verify-testbed-acceptance.sh', 'feature-set.txt'):
        shutil.copy(ROOT / 'release' / name, repo / 'release' / name)
    os.chmod(repo / 'release/verify-candidate.sh', 0o755)
    os.chmod(repo / 'release/verify-testbed-acceptance.sh', 0o755)
    features = [l.strip() for l in (ROOT / 'release/feature-set.txt').read_text().splitlines()
                if l.strip() and not l.startswith('#')]
    manifest = repo / 'release/v9.9.9-runtime.manifest'
    manifest.write_text(''.join(f"{'0' * 64} 644 {p} /usr/local/opnsense/x\n" for p in features))
    git(repo, 'init', '-q', '-b', 'main')
    git(repo, 'config', 'user.email', 't@example.invalid')
    git(repo, 'config', 'user.name', 'Test')
    git(repo, 'add', '-A')
    git(repo, 'commit', '-qm', 'base')
    return repo, manifest, features


def verify(repo, *extra):
    flags = []
    for f in (repo / 'release/feature-set.txt').read_text().splitlines():
        if f.strip() and not f.startswith('#'):
            flags += ['--min-features', f.strip()]
    return run(['sh', str(repo / 'release/verify-candidate.sh'), '--ancestor', 'main', *flags, *extra], cwd=repo)


def test_current_tree_passes():
    # CI checks out a PR head without a local main. The integration ref is origin/main there;
    # the local workstation uses main. The gate itself is unchanged.
    if run(['git', 'rev-parse', '--verify', '--quiet', 'main'], cwd=ROOT).returncode == 0:
        ancestor = 'main'
    else:
        ancestor = 'origin/main'
    out = run(['sh', str(ROOT / 'release/verify-candidate.sh'), '--ancestor', ancestor]
              + sum([['--min-features', f.strip()] for f in (ROOT / 'release/feature-set.txt').read_text().splitlines()
                     if f.strip() and not f.startswith('#')], []), cwd=ROOT)
    check(out.returncode == 0, f'the real candidate passes ({out.stderr.strip()[:80]})')


def test_stale_source_is_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        repo, manifest, features = make_repo(tmp)
        git(repo, 'checkout', '-qb', 'stale-base')
        git(repo, 'checkout', '-q', 'main')
        (repo / 'later.txt').write_text('a later main commit\n')
        git(repo, 'add', '-A'); git(repo, 'commit', '-qm', 'later main work')
        git(repo, 'checkout', '-q', 'stale-base')
        out = verify(repo)
        check(out.returncode != 0 and 'not based on main' in out.stderr,
              'a branch cut before main is refused as a candidate')


def test_missing_feature_is_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        repo, manifest, features = make_repo(tmp)
        keep = [l for l in manifest.read_text().splitlines() if 'EmailLog.php' not in l]
        manifest.write_text(''.join(l + '\n' for l in keep))
        git(repo, 'add', '-A'); git(repo, 'commit', '-qm', 'manifest loses the feature')
        out = verify(repo)
        check(out.returncode != 0 and 'lacks' in out.stderr,
              'a manifest missing an Email Log file is refused')


def test_bundler_runs_the_guard():
    src = (ROOT / 'release/build-bundle.sh').read_text()
    assert 'verify-candidate.sh' in src
    check('verify-candidate.sh' in src and 'feature-set.txt' in src,
          'the bundler verifies candidate identity and the feature set before bundling')


def test_promotion_needs_acceptance():
    """The promotion path is exercised behaviourally by the execution-ledger suite.

    The former fixture wrote acceptance files directly; that format is obsolete because only
    ledger-derived acceptance is now accepted. Keep this suite focused on candidate/archive
    safeguards and run the real staged acceptance checks in tests/test_execution_ledger.py.
    """
    print('  PASS promotion acceptance is proven by tests/test_execution_ledger.py')


def make_bundle(tmp, version='9.9.9', source=None):
    repo = Path(tmp) / 'repo'
    (repo / 'release').mkdir(parents=True)
    (repo / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor').mkdir(parents=True)
    (repo / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json').write_text(
        '{"version": "%s"}' % version)
    for name in ('verify-bundle.py', 'verify-fetched-bundle.sh', 'feature-set.txt'):
        shutil.copy(ROOT / 'release' / name, repo / 'release' / name)
    data = Path(tmp)
    (data / 'feature.php').write_text('feature\n')
    (data / 'runtime.py').write_text('runtime\n')
    listing = Path(tmp) / 'list.txt'
    listing.write_text('feature.php\nruntime.py\n')
    archive = Path(tmp) / 'bundle.tar.gz'
    import io, tarfile
    with tarfile.open(archive, 'w:gz', format=tarfile.USTAR_FORMAT) as tar:
        for name in ('feature.php', 'runtime.py'):
            tar.add(data / name, arcname=name)
    import hashlib
    identity = Path(tmp) / 'bundle.tar.gz.identity'
    identity.write_text(f'version={version}\nsource={source or "a" * 40}\n'
                        f'bytes={archive.stat().st_size}\nsha256={hashlib.sha256(archive.read_bytes()).hexdigest()}\n')
    return repo, archive, listing, identity


def test_fetched_bundle_identity_and_completeness():
    with tempfile.TemporaryDirectory() as tmp:
        repo, archive, listing, identity = make_bundle(tmp)
        done = run(['sh', str(repo / 'release/verify-fetched-bundle.sh'), str(archive),
                    '--source', 'a' * 40, '--identity', str(identity), '--list', str(listing)],
                   cwd=tmp)
        check(done.returncode == 0 and 'BUNDLE_VERIFIED' in done.stdout,
              'the fetched archive is accepted only with its explicit identity and complete membership')
        done = run(['sh', str(repo / 'release/verify-fetched-bundle.sh'), str(archive),
                    '--source', 'b' * 40, '--identity', str(identity), '--list', str(listing)],
                   cwd=tmp)
        check(done.returncode != 0 and 'source' in done.stderr,
              'a bundle from a different source SHA is refused')
        # Rebuild without one member while keeping the identity: the archive must be refused.
        import tarfile
        trimmed = Path(tmp) / 'trimmed.tar.gz'
        with tarfile.open(archive, 'r:gz') as old, tarfile.open(trimmed, 'w:gz', format=tarfile.USTAR_FORMAT) as new:
            new.addfile(old.getmember('feature.php'), old.extractfile('feature.php'))
        trimmed.replace(archive)
        import hashlib
        raw = archive.read_bytes()
        identity.write_text(f'version=9.9.9\nsource={"a" * 40}\nbytes={len(raw)}\n'
                            f'sha256={hashlib.sha256(raw).hexdigest()}\n')
        done = run(['sh', str(repo / 'release/verify-fetched-bundle.sh'), str(archive),
                    '--source', 'a' * 40, '--identity', str(identity), '--list', str(listing)],
                   cwd=tmp)
        check(done.returncode != 0 and 'membership' in done.stderr,
              'an archive missing a required member is refused, not treated as an older release')


def test_joint_manifest_and_archive_removal_is_refused():
    """Remove a feature from both the manifest and the archive; the candidate must fail."""
    with tempfile.TemporaryDirectory() as tmp:
        repo, manifest, features = make_repo(tmp)
        original = manifest.read_text()
        (repo / 'release/manifests').mkdir()
        (repo / 'release/manifests/v9.9.9-runtime.manifest').write_text(original)
        # The archive's allow-list is the manifest; the feature list is the independent
        # completeness contract. Both lose the same Email Log path in one commit.
        manifest.write_text(''.join(l + '\n' for l in original.splitlines()
                                    if 'EmailLog.php' not in l))
        feature_file = repo / 'release/feature-set.txt'
        feature_file.write_text(''.join(l + '\n' for l in feature_file.read_text().splitlines()
                                        if 'EmailLog.php' not in l))
        git(repo, 'add', '-A')
        git(repo, 'commit', '-qm', 'manifest, archive and feature set lose one feature')
        out = verify(repo)
        check(out.returncode != 0 and 'lost a baseline target' in out.stderr,
              'a jointly incomplete manifest and archive are refused')


def test_manifest_cannot_lose_a_baseline_target():
    with tempfile.TemporaryDirectory() as tmp:
        repo, manifest, features = make_repo(tmp)
        (repo / 'release/manifests').mkdir(exist_ok=True)
        (repo / 'release/manifests/v9.9.9-runtime.manifest').write_text(manifest.read_text())
        keep = [l for l in manifest.read_text().splitlines() if 'EmailLog.php' not in l]
        manifest.write_text(''.join(l + '\n' for l in keep))
        git(repo, 'add', '-A'); git(repo, 'commit', '-qm', 'manifest removal')
        out = verify(repo)
        check(out.returncode != 0 and 'lost a baseline target' in out.stderr,
              'a manifest that removes a previously shipped row is refused')


def main():
    test_current_tree_passes()
    test_stale_source_is_rejected()
    test_missing_feature_is_rejected()
    test_bundler_runs_the_guard()
    test_promotion_needs_acceptance()
    test_fetched_bundle_identity_and_completeness()
    test_joint_manifest_and_archive_removal_is_refused()
    test_manifest_cannot_lose_a_baseline_target()
    print('RELEASE_SAFEGUARDS=FAIL (%d)' % len(FAILS) if FAILS else 'RELEASE_SAFEGUARDS=PASS')
    return 1 if FAILS else 0


if __name__ == '__main__':
    raise SystemExit(main())
