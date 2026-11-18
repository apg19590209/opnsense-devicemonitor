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
    out = run(['sh', str(ROOT / 'release/verify-candidate.sh'), '--ancestor', 'main']
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
    script = ROOT / 'release/verify-testbed-acceptance.sh'
    text = script.read_text()
    check('release/bundle-digest.txt' in text and 'feature_files' in text,
          'the promotion gate reads the recorded digest and the verified feature count')
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / 'repo'
        shutil.copytree(ROOT / 'release', repo / 'release')
        shutil.copytree(ROOT / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor',
                        repo / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor')
        version = __import__('json').loads((ROOT / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json')
                                           .read_text())['version']
        digest = re.search(r'^sha256 ([0-9a-f]{64})$', (repo / 'release/bundle-digest.txt').read_text(), re.M).group(1)
        env = dict(os.environ, DM_ACCEPTANCE_MARKER_DIR=str(Path(tmp) / 'markers'))
        missing = run(['sh', str(repo / 'release/verify-testbed-acceptance.sh')], env=env)
        check(missing.returncode != 0, 'promotion is refused with no evidence file')
        ev = Path(tmp) / 'ev.txt'
        ev.write_text(f'version={version}\nbundle_sha256={digest}\ntestbed=192.0.20.1\nfeature_files=0\nresult=PASS\n')
        out = run(['sh', str(repo / 'release/verify-testbed-acceptance.sh'), str(ev)], env=env)
        check(out.returncode != 0, 'promotion is refused when the feature set was not verified')
        ev.write_text(f'version={version}\nbundle_sha256={digest}\ntestbed=192.0.20.1\nfeature_files=10\nresult=FAIL\n')
        out = run(['sh', str(repo / 'release/verify-testbed-acceptance.sh'), str(ev)], env=env)
        check(out.returncode != 0, 'promotion is refused when the testbed result is not PASS')
        ev.write_text(f'version={version}\nbundle_sha256={"1" * 64}\ntestbed=192.0.20.1\nfeature_files=10\nresult=PASS\n')
        out = run(['sh', str(repo / 'release/verify-testbed-acceptance.sh'), str(ev)], env=env)
        check(out.returncode != 0, 'promotion is refused when the digest differs from the record')
        ev.write_text(f'version={version}\nbundle_sha256={digest}\ntestbed=192.0.20.1\nfeature_files=10\nresult=PASS\n')
        out = run(['sh', str(repo / 'release/verify-testbed-acceptance.sh'), str(ev)], env=env)
        check(out.returncode == 0 and 'TESTBED_ACCEPTANCE_OK' in out.stdout,
              'a complete, matching, passing evidence file allows promotion')


def main():
    test_current_tree_passes()
    test_stale_source_is_rejected()
    test_missing_feature_is_rejected()
    test_bundler_runs_the_guard()
    test_promotion_needs_acceptance()
    print('RELEASE_SAFEGUARDS=FAIL (%d)' % len(FAILS) if FAILS else 'RELEASE_SAFEGUARDS=PASS')
    return 1 if FAILS else 0


if __name__ == '__main__':
    raise SystemExit(main())
