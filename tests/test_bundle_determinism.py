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
import gzip
import os
import re
import shutil
import subprocess
import sys
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


def read_members(blob):
    """Parse ustar headers without trusting any tar implementation.

    Returns dicts with the raw field bytes, so a test can assert *encoding*, not just
    content. The checksum is recomputed the way tar does it: with the checksum field read as
    eight spaces.
    """
    position = 0
    while position + 512 <= len(blob):
        header = blob[position:position + 512]
        if header == b'\0' * 512:
            return
        size = int((header[124:136].strip(b'\0 ') or b'0'), 8)
        expected = int((header[148:156].strip(b'\0 ') or b'0'), 8)
        computed = sum(header[:148] + b' ' * 8 + header[156:])
        yield {
            'name': header[0:100].rstrip(b'\0'),
            'mode': int((header[100:108].strip(b'\0 ') or b'0'), 8),
            'uid': header[108:116], 'gid': header[116:124],
            'size': size, 'mtime': header[136:148], 'typeflag': header[156:157],
            'magic': header[257:263], 'version': header[263:265],
            'uname': header[265:297].rstrip(b'\0'), 'gname': header[297:329].rstrip(b'\0'),
            'devmajor': header[329:337], 'devminor': header[337:345],
            'checksum_ok': expected == computed,
        }
        position += 512 + size + (-size % 512)


def gnu_style(blob, mtime=1767186000):
    """Re-encode every header the way GNU tar does: 7-digit octal fields, `ustar  \\0`.

    This is what a GNU-tar-built archive looks like where bsdtar writes `000644 \\0`. If the
    canonicaliser is doing its job, both encodings must end up byte-identical.
    """
    data = bytearray(blob)
    position = 0
    while position + 512 <= len(data):
        header = data[position:position + 512]
        if header == b'\0' * 512:
            break
        size = int((header[124:136].strip(b'\0 ') or b'0'), 8)
        mode = int((header[100:108].strip(b'\0 ') or b'0'), 8)

        def put(start, end, value):
            data[position + start:position + end] = value + b'\0' * (end - start - len(value))

        put(100, 108, ('%07o' % mode).encode())
        put(108, 116, b'0000000')
        put(116, 124, b'0000000')
        put(124, 136, ('%011o' % size).encode())
        put(136, 148, ('%011o' % mtime).encode())
        put(257, 265, b'ustar  \0')
        put(329, 337, b'0000000')
        put(337, 345, b'0000000')
        data[position + 148:position + 156] = b' ' * 8
        total = sum(data[position:position + 512])
        data[position + 148:position + 156] = ('%07o\0' % total).encode()
        position += 512 + size + (-size % 512)
    return bytes(data)


CANONICAL_MTIME = b'15125334400 '   # 1767225600 = 2026-01-01T00:00:00Z, 11 octal digits + space
CANONICAL_ZERO = b'000000 \0'       # mode/uid/gid/devmajor/devminor encoding


def test_archive_metadata_is_canonical():
    """Every header must carry the canonical ownership, mtime and format fields.

    The digest alone cannot tell *why* two archives differ, so this asserts the metadata an
    installer relies on: root/wheel ownership at uid/gid 0, a fixed mtime, POSIX ustar magic
    and a valid checksum — regardless of which tar produced the bytes.
    """
    sha = git('rev-parse', 'HEAD')
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        checkout = tmp / 'checkout'
        make_checkout(checkout, sha)
        build(checkout, tmp / 'build')
        members = list(read_members(gzip.open(tmp / 'build' / 'bundle.tar.gz', 'rb').read()))
    assert members, 'archive has no members'
    names = [member['name'] for member in members]
    assert names == sorted(names), 'member order is not the sorted allow-list'
    assert len(set(names)) == len(names), 'duplicate members in the archive'
    for member in members:
        name = member['name']
        assert member['uid'] == CANONICAL_ZERO, (name, 'uid', member['uid'])
        assert member['gid'] == CANONICAL_ZERO, (name, 'gid', member['gid'])
        assert member['devmajor'] == CANONICAL_ZERO, (name, 'devmajor', member['devmajor'])
        assert member['devminor'] == CANONICAL_ZERO, (name, 'devminor', member['devminor'])
        assert member['uname'] == b'root', (name, 'uname', member['uname'])
        assert member['gname'] == b'wheel', (name, 'gname', member['gname'])
        assert member['mtime'] == CANONICAL_MTIME, (name, 'mtime', member['mtime'])
        assert member['typeflag'] == b'0', (name, 'typeflag', member['typeflag'])
        assert member['magic'] == b'ustar\0', (name, 'magic', member['magic'])
        assert member['version'] == b'00', (name, 'version', member['version'])
        assert member['checksum_ok'], (name, 'checksum')
        assert member['mode'] in (0o644, 0o755), (name, 'mode', oct(member['mode']))
    print('  canonical metadata     %d members, uid/gid 0, root/wheel, mtime %s'
          % (len(members), CANONICAL_MTIME.decode().strip()))


def test_archive_is_independent_of_header_encoding():
    """A GNU-tar-style archive must canonicalise to the same bytes as a bsdtar-style one.

    GNU tar and bsdtar encode the same metadata differently (`000644\\0` vs `000644 \\0`,
    `ustar  \\0` vs `ustar\\0`). The bundle identity may not depend on which one built it, so
    the canonicaliser is fed a GNU-style re-encoding of our own archive and must return the
    original bytes exactly.
    """
    sha = git('rev-parse', 'HEAD')
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        checkout = tmp / 'checkout'
        make_checkout(checkout, sha)
        build(checkout, tmp / 'build')
        original = gzip.open(tmp / 'build' / 'bundle.tar.gz', 'rb').read()
        mutated = gnu_style(original)
        assert mutated != original, 'GNU-style re-encoding changed nothing; the test is inert'
        source = tmp / 'gnu-style.tar'
        source.write_bytes(mutated)
        target = tmp / 'gnu-style-canonical.tar'
        done = subprocess.run(
            [sys.executable, str(ROOT / 'release/normalize-bundle-tar.py'),
             str(source), str(target)],
            capture_output=True, text=True, timeout=120)
        assert done.returncode == 0, (done.stdout, done.stderr)
        assert target.read_bytes() == original, (
            'canonicaliser did not collapse GNU-style headers back to the bsdtar encoding')
    print('  header encoding        GNU-style input collapsed to %d identical bytes'
          % len(original))


CASES = [
    test_bundle_is_identical_from_two_checkouts,
    test_archive_metadata_is_canonical,
    test_archive_is_independent_of_header_encoding,
    test_bundle_matches_the_recorded_digest,
]


def main():
    for case in CASES:
        case()
        print('  %-38s PASS' % case.__name__)
    print('BUNDLE_DETERMINISM=PASS cases=%d' % len(CASES))


if __name__ == '__main__':
    main()
