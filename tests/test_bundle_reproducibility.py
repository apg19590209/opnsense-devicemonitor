"""The bundle must be byte-identical no matter which tar or compressor produced it.

Run #41627234610 left two platform differences in the identity: GNU tar padded the archive to
its 10 KiB record boundary (3 584 trailing bytes instead of the POSIX 1 024), and GNU gzip
compressed the result differently from BSD gzip (349 052 vs 348 939 bytes for the same input).
Decision 68 fixes both inside our own code — the canonicaliser terminates with exactly two zero
blocks, and `release/bundle-gzip.py` writes a fixed gzip header around stored deflate blocks.

These cases prove each property in an isolated temporary directory, so they hold on FreeBSD and
on the Linux runner alike.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NORMALISER = ROOT / 'release/normalize-bundle-tar.py'
GZIPPER = ROOT / 'release/bundle-gzip.py'
CANONICAL = ROOT / 'release/bundle-digest.txt'
BLOCK = 512
GZIP_HEADER = b'\x1f\x8b\x08\x00' + b'\x00\x00\x00\x00' + b'\x00\xff'

_CACHE = {}


def build_once():
    """Build the bundle once per process; every case reuses the same canonical tar."""
    if 'tar' in _CACHE:
        return _CACHE['tar'], _CACHE['gz']
    workdir = Path(tempfile.mkdtemp(prefix='dm-repro-'))
    env = dict(os.environ,
               DM_BUNDLE_STAGE=str(workdir / 'stage'),
               DM_BUNDLE_LIST=str(workdir / 'list.txt'),
               DM_BUNDLE_OUT=str(workdir / 'bundle.tar.gz'))
    done = subprocess.run(['sh', str(ROOT / 'release/build-bundle.sh')],
                          capture_output=True, text=True, env=env, cwd=str(ROOT), timeout=600)
    assert done.returncode == 0, (done.stdout, done.stderr)
    _CACHE['dir'] = workdir
    _CACHE['gz'] = (workdir / 'bundle.tar.gz').read_bytes()
    _CACHE['tar'] = zlib.decompress(_CACHE['gz'], 16 + zlib.MAX_WBITS)
    return _CACHE['tar'], _CACHE['gz']


def run_normaliser(source, target):
    return subprocess.run([sys.executable, str(NORMALISER), str(source), str(target)],
                          capture_output=True, text=True, timeout=120)


def members(blob):
    position = 0
    while position + BLOCK <= len(blob):
        header = blob[position:position + BLOCK]
        if header == b'\0' * BLOCK:
            return
        size = int((header[124:136].strip(b'\0 ') or b'0'), 8)
        yield header, size
        position += BLOCK + size + (-size % BLOCK)


def test_padding_variants_normalise_identically():
    """bsdtar's 1 024-byte tail and GNU tar's 3 584-byte tail must give the same archive."""
    tar, _ = build_once()
    body = tar[:-2 * BLOCK]
    assert tar[-2 * BLOCK:] == b'\0' * (2 * BLOCK), 'canonical tail is not two zero blocks'
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        results = []
        for name, tail in (('bsdtar', 2 * BLOCK), ('gnutar', 7 * BLOCK), ('excess', 20 * BLOCK)):
            source = tmp / ('%s.tar' % name)
            target = tmp / ('%s.canonical' % name)
            source.write_bytes(body + b'\0' * tail)
            done = run_normaliser(source, target)
            assert done.returncode == 0, (name, done.stdout, done.stderr)
            results.append(target.read_bytes())
    assert results[0] == results[1] == results[2], 'padding length changed the archive'
    assert results[0] == tar, 'canonical archive differs from the built one'
    print('  padding variants      1 024 / 3 584 / 10 240 byte tails identical')


def test_canonicalisation_is_idempotent():
    tar, _ = build_once()
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        first = tmp / 'first.tar'
        second = tmp / 'second.tar'
        third = tmp / 'third.tar'
        first.write_bytes(tar)
        assert run_normaliser(first, second).returncode == 0
        assert run_normaliser(second, third).returncode == 0
        assert second.read_bytes() == tar and third.read_bytes() == tar
    print('  idempotent             second and third passes byte-identical')


def test_malformed_trailing_data_is_rejected():
    tar, _ = build_once()
    body = tar[:-2 * BLOCK]
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        cases = {
            'nonzero-after-final-member': body + b'\0' * (2 * BLOCK) + b'garbage',
            'no-end-marker': body,
            'short-tail': body + b'\0' * BLOCK,
        }
        for name, payload in cases.items():
            source = tmp / ('%s.tar' % name)
            target = tmp / ('%s.out' % name)
            source.write_bytes(payload)
            done = run_normaliser(source, target)
            assert done.returncode != 0, (name, 'malformed archive was accepted')
            assert not target.exists(), name
    print('  malformed tails        nonzero, missing and short tails all rejected')


def test_compression_is_deterministic():
    tar, gz = build_once()
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        source = tmp / 'canonical.tar'
        source.write_bytes(tar)
        outputs = []
        for index in range(2):
            target = tmp / ('out%d.tar.gz' % index)
            done = subprocess.run([sys.executable, str(GZIPPER), str(source), str(target)],
                                  capture_output=True, text=True, timeout=300)
            assert done.returncode == 0, (done.stdout, done.stderr)
            outputs.append(target.read_bytes())
    assert outputs[0] == outputs[1] == gz, 'compression is not deterministic'
    print('  compression            two runs identical (%d bytes)' % len(gz))


def test_gzip_header_metadata_is_stable():
    _, gz = build_once()
    assert gz[:10] == GZIP_HEADER, gz[:10]
    assert gz[3] == 0, 'FLG must be 0 (no name, comment or extra field)'
    assert gz[4:8] == b'\0\0\0\0', 'MTIME must be zero'
    assert gz[9] == 255, 'OS byte must be 255 (unknown), not the host OS id'
    print('  gzip header            fixed: mtime 0, OS 255, no filename')


def test_decompression_returns_the_canonical_tar():
    tar, gz = build_once()
    assert zlib.decompress(gz, 16 + zlib.MAX_WBITS) == tar
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / 'bundle.tar.gz'
        path.write_bytes(gz)
        system = subprocess.run(['gzip', '-dc', str(path)], capture_output=True, timeout=300)
        assert system.returncode == 0, system.stderr
        assert system.stdout == tar, 'system gzip disagrees with the canonical tar'
        listing = subprocess.run(['tar', '-tzf', str(path)], capture_output=True, timeout=300)
        assert listing.returncode == 0, listing.stderr
        assert len(listing.stdout.decode().split()) == 58
    print('  decompression          zlib, gzip -dc and tar -tzf agree (58 members)')


def test_size_and_digest_are_checked_independently():
    _, gz = build_once()
    recorded = {}
    for line in CANONICAL.read_text().splitlines():
        if line and not line.startswith('#') and ' ' in line:
            key, _, value = line.partition(' ')
            recorded[key] = value.strip()
    assert recorded['sha256'] == hashlib.sha256(gz).hexdigest(), recorded['sha256']
    assert recorded['bytes'] == str(len(gz)), (recorded['bytes'], len(gz))
    tar_length = len(zlib.decompress(gz, 16 + zlib.MAX_WBITS))
    assert len(gz) < tar_length + 4096, 'stored-block output cannot exceed the input by much'
    print('  identity               %s / %s bytes' % (recorded['sha256'][:16], recorded['bytes']))


def test_failure_is_fail_closed():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        failing = tmp / 'failing-gzip'
        failing.write_text('#!/bin/sh\nexit 1\n')
        failing.chmod(0o755)
        out = tmp / 'bundle.tar.gz'
        env = dict(os.environ,
                   DM_BUNDLE_STAGE=str(tmp / 'stage'),
                   DM_BUNDLE_LIST=str(tmp / 'list.txt'),
                   DM_BUNDLE_OUT=str(out),
                   DM_BUNDLE_GZIP=str(failing))
        done = subprocess.run(['sh', str(ROOT / 'release/build-bundle.sh')],
                              capture_output=True, text=True, env=env, cwd=str(ROOT), timeout=600)
        assert done.returncode != 0
        assert 'GZIP_FAILED' in (done.stdout + done.stderr)
        assert not out.exists(), 'a failed compression must not leave a bundle'
    print('  fail-closed            compressor failure leaves no bundle')


def test_payload_metadata_is_unchanged():
    tar, _ = build_once()
    parsed = list(members(tar))
    assert len(parsed) == 58, len(parsed)
    names = []
    for header, _size in parsed:
        names.append(header[0:100].rstrip(b'\0'))
        assert header[108:116] == b'000000 \0', ('uid', header[108:116])
        assert header[116:124] == b'000000 \0', ('gid', header[116:124])
        assert header[265:297].rstrip(b'\0') == b'root'
        assert header[297:329].rstrip(b'\0') == b'wheel'
        assert header[136:148] == b'15125334400 ', header[136:148]
        assert header[257:263] == b'ustar\0'
        assert header[263:265] == b'00'
        assert header[156:157] == b'0'
        assert int(header[100:108].strip(b'\0 ') or b'0', 8) in (0o644, 0o755)
        expected = int((header[148:156].strip(b'\0 ') or b'0'), 8)
        assert expected == sum(header[:148] + b' ' * 8 + header[156:]), 'checksum'
    assert names == sorted(names) and len(set(names)) == 58
    print('  payload metadata       58 members, canonical ownership and mtime')


CASES = [
    test_padding_variants_normalise_identically,
    test_canonicalisation_is_idempotent,
    test_malformed_trailing_data_is_rejected,
    test_compression_is_deterministic,
    test_gzip_header_metadata_is_stable,
    test_decompression_returns_the_canonical_tar,
    test_size_and_digest_are_checked_independently,
    test_failure_is_fail_closed,
    test_payload_metadata_is_unchanged,
]


def main():
    try:
        for case in CASES:
            case()
            print('  %-38s PASS' % case.__name__)
        print('BUNDLE_REPRODUCIBILITY=PASS cases=%d' % len(CASES))
    finally:
        if 'dir' in _CACHE:
            shutil.rmtree(_CACHE['dir'], ignore_errors=True)


if __name__ == '__main__':
    main()
