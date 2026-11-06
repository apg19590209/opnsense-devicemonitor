"""The v2.12.1 bundle must be byte-identical across repeated builds."""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'release/build-bundle.sh'
NORMALISER = ROOT / 'release/normalize-bundle-tar.py'
GZIPPER = ROOT / 'release/bundle-gzip.py'
BLOCK = 512
EXPECTED_MEMBERS = 56
GZIP_HEADER = b'\x1f\x8b\x08\x00' + b'\x00\x00\x00\x00' + b'\x00\xff'
CANONICAL_MTIME = b'15125334400 '

_CACHE = {}


def run_build(workdir):
    workdir.mkdir(parents=True, exist_ok=True)
    stage = workdir / 'stage'
    out = workdir / 'bundle.tar.gz'
    listing = workdir / 'list.txt'
    env = dict(os.environ,
               DM_BUNDLE_STAGE=str(stage),
               DM_BUNDLE_OUT=str(out),
               DM_BUNDLE_LIST=str(listing))
    done = subprocess.run(['sh', str(BUILD)], capture_output=True, text=True,
                          env=env, cwd=str(ROOT), timeout=600)
    assert done.returncode == 0, (done.stdout, done.stderr)
    data = out.read_bytes()
    assert ('bundle sha256: %s' % hashlib.sha256(data).hexdigest()) in done.stdout, done.stdout
    return data, done.stdout


def build_once():
    if 'gz' not in _CACHE:
        workdir = Path(tempfile.mkdtemp(prefix='dm-v2121-repro-'))
        gz, output = run_build(workdir / 'first')
        _CACHE.update(dir=workdir, gz=gz, tar=zlib.decompress(gz, 16 + zlib.MAX_WBITS),
                      output=output)
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


def test_repeated_builds_are_byte_identical():
    """A changed build timestamp must not change the published bytes."""
    _, first = build_once()
    time.sleep(1.2)
    with tempfile.TemporaryDirectory() as tmpdir:
        second, output = run_build(Path(tmpdir) / 'second')
    assert first == second, 'repeated builds differ'
    assert hashlib.sha256(first).hexdigest() == hashlib.sha256(second).hexdigest()
    print('  repeated builds        identical (%d bytes)' % len(first))


def test_gzip_header_is_fixed():
    _, gz = build_once()
    assert gz[:10] == GZIP_HEADER, gz[:10]
    assert gz[3] == 0, 'FLG must be 0 (no filename or extra field)'
    assert gz[4:8] == b'\0\0\0\0', 'MTIME must be zero'
    assert gz[9] == 255, 'OS byte must be 255 (unknown)'
    print('  gzip header            mtime 0, OS 255, no filename')


def test_compressor_is_deterministic():
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
    assert outputs[0] == outputs[1] == gz
    print('  compressor             two runs identical')


def test_decompression_and_member_inventory():
    tar, gz = build_once()
    assert zlib.decompress(gz, 16 + zlib.MAX_WBITS) == tar
    parsed = list(members(tar))
    names = [header[0:100].rstrip(b'\0').decode() for header, _size in parsed]
    assert len(names) == EXPECTED_MEMBERS, len(names)
    assert names == sorted(names) and len(names) == len(set(names))
    assert 'release/core-locale-state.sh' in names
    assert 'install-unattended.sh' in names
    assert not any(name.endswith('.pyc') or '__pycache__' in name for name in names)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / 'bundle.tar.gz'
        path.write_bytes(gz)
        system = subprocess.run(['gzip', '-dc', str(path)], capture_output=True, timeout=300)
        assert system.returncode == 0, system.stderr
        assert system.stdout == tar
        listing = subprocess.run(['tar', '-tzf', str(path)], capture_output=True, timeout=300)
        assert listing.returncode == 0, listing.stderr
        assert len(listing.stdout.decode().splitlines()) == EXPECTED_MEMBERS
    print('  inventory              %d members, gzip -dc and tar -tzf agree' % len(names))


def test_tar_headers_are_canonical():
    tar, _ = build_once()
    parsed = list(members(tar))
    assert len(parsed) == EXPECTED_MEMBERS
    for header, _size in parsed:
        assert header[100:108] != b'\0' * 8
        assert header[108:116] == b'000000 \0', ('uid', header[108:116])
        assert header[116:124] == b'000000 \0', ('gid', header[116:124])
        assert header[136:148] == CANONICAL_MTIME, header[136:148]
        assert header[265:297].rstrip(b'\0') == b'root'
        assert header[297:329].rstrip(b'\0') == b'wheel'
        assert header[257:263] == b'ustar\0'
        assert header[263:265] == b'00'
        assert header[156:157] == b'0'
        assert int(header[100:108].strip(b'\0 ') or b'0', 8) in (0o644, 0o755)
        checksum = int((header[148:156].strip(b'\0 ') or b'0'), 8)
        assert checksum == sum(header[:148] + b' ' * 8 + header[156:])
    print('  tar headers            root/wheel, uid/gid 0, fixed mtime')


def test_tar_tail_and_header_encoding_normalise_identically():
    tar, _ = build_once()
    body = tar[:-2 * BLOCK]
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        results = []
        for name, tail in (('bsdtar', 2 * BLOCK), ('gnutar', 7 * BLOCK), ('excess', 20 * BLOCK)):
            source = tmp / ('%s.tar' % name)
            target = tmp / ('%s.canonical' % name)
            source.write_bytes(body + b'\0' * tail)
            done = run_normaliser(source, target)
            assert done.returncode == 0, (done.stdout, done.stderr)
            results.append(target.read_bytes())
        assert results[0] == results[1] == results[2] == tar

        source = tmp / 'short.tar'
        target = tmp / 'short.out'
        source.write_bytes(body + b'\0' * BLOCK)
        done = run_normaliser(source, target)
        assert done.returncode != 0 and not target.exists()
    print('  normaliser             padding variants collapse; malformed tail refused')


def test_gzip_failure_leaves_no_bundle():
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
        done = subprocess.run(['sh', str(BUILD)], capture_output=True, text=True,
                              env=env, cwd=str(ROOT), timeout=600)
        assert done.returncode != 0
        assert 'GZIP_FAILED' in (done.stdout + done.stderr)
        assert not out.exists()
    print('  fail-closed            compressor failure leaves no bundle')


CASES = [
    test_repeated_builds_are_byte_identical,
    test_gzip_header_is_fixed,
    test_compressor_is_deterministic,
    test_decompression_and_member_inventory,
    test_tar_headers_are_canonical,
    test_tar_tail_and_header_encoding_normalise_identically,
    test_gzip_failure_leaves_no_bundle,
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
