"""The published bundle digest must be reproducible from any clean checkout.

The 2.13.3 review found `release/build-bundle.sh` producing different bytes from different
checkouts of the same commit, because `cp -p` carried each checkout's file timestamps into
the archive. Decision 63 normalises mtime, uid/gid and archive format, and pins the member
order to the sorted allow-list.

This suite does what the review asked for: it builds the bundle in **two separate clean
checkouts** of the tested commit, gives each checkout deliberately different file
timestamps, and requires identical bytes. It then compares the result with the digest
recorded in `release/bundle-digest.txt`, so the published identity cannot drift silently.
"""
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / 'release/bundle-digest.txt'
STAMPS = ('202703150101.01', '202401020304.05')


def git(*args, cwd=ROOT):
    return subprocess.run(['git', '-C', str(cwd)] + list(args),
                          capture_output=True, text=True, check=True, timeout=120).stdout.strip()


def make_checkout(destination, sha):
    subprocess.run(['git', 'clone', '--quiet', '--no-hardlinks', str(ROOT), str(destination)],
                   capture_output=True, text=True, check=True, timeout=300)
    subprocess.run(['git', '-C', str(destination), 'checkout', '--quiet', '--detach', sha],
                   capture_output=True, text=True, check=True, timeout=120)
    assert git('rev-parse', 'HEAD', cwd=destination) == sha


def age(tree, stamp):
    """Give every file in the checkout the same, deliberately wrong, timestamp."""
    subprocess.run(['find', str(tree), '-exec', 'touch', '-h', '-t', stamp, '{}', '+'],
                   check=True, timeout=120)


def build(tree, workdir):
    workdir.mkdir(parents=True, exist_ok=True)
    stage = workdir / 'stage'
    out = workdir / 'bundle.tar.gz'
    listing = workdir / 'list.txt'
    env = dict(os.environ,
               DM_BUNDLE_STAGE=str(stage),
               DM_BUNDLE_OUT=str(out),
               DM_BUNDLE_LIST=str(listing))
    done = subprocess.run(['sh', str(tree / 'release/build-bundle.sh')],
                          capture_output=True, text=True, env=env, timeout=600)
    assert done.returncode == 0, (done.stdout, done.stderr)
    match = re.search(r'^bundle sha256: ([0-9a-f]{64})$', done.stdout, re.M)
    assert match, done.stdout
    size = re.search(r'^archive bytes     : (\d+)$', done.stdout, re.M)
    assert size, done.stdout
    assert out.is_file()
    return match.group(1), int(size.group(1))


def canonical():
    values = {}
    for line in CANONICAL.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, _, value = line.partition(' ')
        values[key] = value.strip()
    return values


def test_bundle_is_identical_from_two_checkouts():
    if shutil.which('git') is None:
        raise AssertionError('git is required to prove bundle determinism')
    sha = git('rev-parse', 'HEAD')
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        digests = []
        for index, stamp in enumerate(STAMPS):
            checkout = tmp / ('checkout%d' % index)
            make_checkout(checkout, sha)
            age(checkout, stamp)
            digests.append(build(checkout, tmp / ('build%d' % index)))
        first, second = digests
        assert first == second, (
            'bundle is not reproducible across checkouts: %s != %s' % (first[0], second[0]))
        assert first[1] == second[1], (first[1], second[1])
    print('  two checkouts         %s (%d bytes)' % (first[0], first[1]))


def test_bundle_matches_the_recorded_digest():
    if not CANONICAL.is_file():
        raise AssertionError('release/bundle-digest.txt is missing: run release/build-bundle.sh '
                             'and record its output')
    recorded = canonical()
    sha = git('rev-parse', 'HEAD')
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        checkout = tmp / 'checkout'
        make_checkout(checkout, sha)
        digest, size = build(checkout, tmp / 'build')
    assert recorded.get('sha256') == digest, (
        'release/bundle-digest.txt says %s but the tree builds %s'
        % (recorded.get('sha256'), digest))
    assert recorded.get('bytes') == str(size), (recorded.get('bytes'), size)
    version = re.search(r'^VERSION=([0-9.]+)$',
                        (ROOT / 'install-unattended.sh').read_text(), re.M).group(1)
    assert recorded.get('version') == version, (recorded.get('version'), version)
    print('  canonical digest      %s (%s bytes, v%s)' % (digest, size, version))


CASES = [
    test_bundle_is_identical_from_two_checkouts,
    test_bundle_matches_the_recorded_digest,
]


def main():
    for case in CASES:
        case()
        print('  %-38s PASS' % case.__name__)
    print('BUNDLE_DETERMINISM=PASS cases=%d' % len(CASES))


if __name__ == '__main__':
    main()
