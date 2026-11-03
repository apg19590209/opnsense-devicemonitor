"""The bundle build must fail loudly instead of publishing a broken archive.

The first GitHub Actions run (#41609297193) published a 20-byte gzip as the runtime bundle:
`tar` rejected bsdtar's `--uid` flag, the `tar | gzip` pipeline reported only gzip's status,
and the script carried on. Decision 67 makes every stage an explicit, checked step and refuses
tar implementations it cannot verify, so this suite fakes each failure mode and requires a
nonzero exit with no archive left behind.

Each case runs the real `release/build-bundle.sh` with `DM_TAR` or `DM_BUNDLE_GZIP` pointing at a
fixture; nothing is built from a clone, so the cases are fast and touch only a temporary directory.
The tar fixtures implement the interface themselves instead of forwarding flags to the host tar —
run #41629115055 showed that "advertise bsdtar, then exec the local tar" breaks on a GNU-tar host.
"""
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'release/build-bundle.sh'
NORMALIZER = ROOT / 'release/normalize-bundle-tar.py'


def run_build(tmp, env_extra):
    stage = tmp / 'stage'
    out = tmp / 'bundle.tar.gz'
    listing = tmp / 'list.txt'
    env = dict(os.environ,
               DM_BUNDLE_STAGE=str(stage),
               DM_BUNDLE_OUT=str(out),
               DM_BUNDLE_LIST=str(listing))
    env.update(env_extra)
    done = subprocess.run(['sh', str(BUILD)], capture_output=True, text=True, env=env,
                          cwd=str(ROOT), timeout=300)
    return done, out


def fake(tmp, name, body):
    path = tmp / name
    path.write_text('#!/bin/sh\n' + body)
    path.chmod(0o755)
    return str(path)


# A platform-neutral fake tar (Decision 69). Run #41629115055 failed in this suite because the
# previous fakes advertised bsdtar and forwarded its options to whatever `tar` the host had: on
# the Linux runner that is GNU tar, which rejects `--uid`, so the archive stage was never
# reached. This fixture implements the small interface release/build-bundle.sh uses — --version,
# -cf OUT, -T LIST, positional members and both ownership spellings — and writes a real ustar
# archive itself. It never shells out, so the same script behaves identically on FreeBSD and
# Linux and the cases reach the failure they intend to exercise.
FAKE_TAR = r'''#!/usr/bin/env python3
import os
import sys

FLAVOUR = "__FLAVOUR__"
MODE = "__MODE__"
REJECT = __REJECT__
BLOCK = 512


def octal(value, digits):
    return ("%0*o" % (digits, value)).encode()


def header(name, size, mode):
    block = bytearray(b"\0" * BLOCK)
    block[0:len(name)] = name
    block[100:108] = octal(mode, 7) + b"\0"
    block[108:116] = octal(0, 7) + b"\0"
    block[116:124] = octal(0, 7) + b"\0"
    block[124:136] = octal(size, 11) + b"\0"
    block[136:148] = octal(1767225600, 11) + b"\0"
    block[148:156] = b" " * 8
    block[156:157] = b"0"
    block[257:263] = b"ustar\0"
    block[263:265] = b"00"
    block[265:269] = b"root"
    block[297:302] = b"wheel"
    block[148:156] = ("%06o" % sum(block)).encode() + b"\0 "
    return bytes(block)


def main(argv):
    if "--version" in argv:
        print(FLAVOUR)
        return 0
    for arg in argv:
        for prefix in REJECT:
            if arg.startswith(prefix):
                sys.stderr.write("tar: unrecognized option '%s'\n" % arg)
                return 2
    out = None
    listing = None
    files = []
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "-cf":
            out = argv[index + 1]
            index += 2
        elif arg in ("--format", "--uid", "--gid", "--uname", "--gname"):
            index += 2
        elif arg == "-T":
            listing = argv[index + 1]
            index += 2
        elif arg.startswith("-"):
            index += 1
        else:
            files.append(arg)
            index += 1
    if MODE == "fail-any":
        sys.stderr.write("fake tar: refusing to create an archive\n")
        return 1
    if out is None:
        sys.stderr.write("fake tar: no -cf output\n")
        return 2
    if listing is not None:
        if MODE == "fail-archive":
            sys.stderr.write("fake tar: cannot read the file list\n")
            return 1
        if MODE == "empty-archive":
            open(out, "wb").close()
            return 0
    names = files if listing is None else [line.strip() for line in open(listing) if line.strip()]
    with open(out, "wb") as handle:
        for name in names:
            body = open(name, "rb").read()
            mode = os.stat(name).st_mode & 0o777
            handle.write(header(name.encode(), len(body), mode))
            handle.write(body + b"\0" * (-len(body) % BLOCK))
        handle.write(b"\0" * (2 * BLOCK))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
'''


def fake_tar(tmp, mode='normal', flavour='bsdtar 3.8.7 (fake)', reject=()):
    script = (FAKE_TAR.replace('__FLAVOUR__', flavour)
                      .replace('__MODE__', mode)
                      .replace('__REJECT__', repr(tuple(reject))))
    path = tmp / 'fake-tar'
    path.write_text(script)
    path.chmod(0o755)
    return str(path)


def assert_failed(done, out, marker):
    assert done.returncode != 0, ('build succeeded but should have failed:\n%s\n%s'
                                  % (done.stdout, done.stderr))
    assert marker in (done.stdout + done.stderr), (marker, done.stdout, done.stderr)
    assert not out.exists(), 'a failed build must not leave an archive behind'


def test_tar_failure_is_fatal():
    """The archive stage itself fails: the probe must still pass so the case reaches TAR_FAILED."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        broken = fake_tar(tmp, mode='fail-archive')
        done, out = run_build(tmp, {'DM_TAR': broken})
        assert 'TAR_FORMAT=canonical-ustar members=1' in done.stdout, (
            'the probe must succeed before the archive stage is exercised', done.stdout)
        assert_failed(done, out, 'TAR_FAILED')
    print('  tar failure          probe passed, archive stage rejected, no archive written')


def test_probe_failure_is_reported():
    """A tar that cannot produce a parseable archive fails at the probe, by name."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        unusable = fake_tar(tmp, mode='fail-any')
        done, out = run_build(tmp, {'DM_TAR': unusable})
        assert_failed(done, out, 'TAR_PROBE_FAILED')
        assert 'TAR_FAILED' not in (done.stdout + done.stderr), 'wrong stage reported'
    print('  probe failure        reported as TAR_PROBE_FAILED, not as a later stage')


def test_unknown_tar_implementation_is_refused():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        mystery = fake(tmp, 'mystery-tar', 'echo "mystery-tar 1.0"; exit 0\n')
        done, out = run_build(tmp, {'DM_TAR': mystery})
        assert_failed(done, out, 'UNSUPPORTED_TAR')
    print('  unknown tar          refused by name')


def test_pax_archive_is_refused():
    """A producer that emits pax extended headers must be rejected, not silently shipped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        source = tmp / 'pax.tar'
        header = bytearray(512)
        header[0:4] = b'pax\0'
        header[100:108] = b'000644 \0'
        header[108:116] = b'000000 \0'
        header[116:124] = b'000000 \0'
        header[124:136] = b'00000000000 '
        header[136:148] = b'00000000000 '
        header[156:157] = b'x'
        header[257:265] = b'ustar\0' + b'00'
        header[265:269] = b'root'
        header[297:302] = b'wheel'
        header[148:156] = b' ' * 8
        header[148:156] = ('%06o' % sum(header)).encode() + b'\0 '
        source.write_bytes(bytes(header) + b'\0' * 1024)
        done = subprocess.run(['python3', str(NORMALIZER), '--check', str(source)],
                              capture_output=True, text=True, timeout=120)
        assert done.returncode != 0, done.stdout
        assert 'unsupported member type' in done.stderr, done.stderr
    print('  pax producer         refused by the canonicaliser')


def test_gzip_failure_is_fatal():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        failing = fake(tmp, 'failing-gzip',
                       'echo "deterministic compressor exploded" >&2\nexit 1\n')
        done, out = run_build(tmp, {'DM_BUNDLE_GZIP': failing})
        assert_failed(done, out, 'GZIP_FAILED')
    print('  gzip failure         rejected, no archive written')


def test_empty_tar_is_fatal():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        empty = fake_tar(tmp, mode='empty-archive')
        done, out = run_build(tmp, {'DM_TAR': empty})
        assert 'TAR_FORMAT=canonical-ustar members=1' in done.stdout, done.stdout
        assert_failed(done, out, 'TAR_EMPTY')
    print('  empty tar            probe passed, empty archive rejected, no archive written')


def build_script():
    return (ROOT / 'release/build-bundle.sh').read_text()


def flag_strings():
    """Extract the per-implementation TAR_OPTS assignment from the build script."""
    found = {}
    for flavour in ('bsdtar', 'gnu'):
        match = re.search(r'^\s{4}%s\)\n(?:.*\n)*?\s+TAR_OPTS="([^"]+)"' % flavour,
                          build_script(), re.M)
        assert match, 'no TAR_OPTS for %s' % flavour
        found[flavour] = match.group(1)
    return found


def test_gnu_flag_string_is_valid_for_gnu_tar():
    """Guard the exact defect from run #41611564118: GNU tar has no --uname/--gname.

    GNU tar 1.35 answers `tar: unrecognized option '--uname=root'`, which aborted the build
    at the functional probe. This asserts the spelling statically, so the regression is caught
    even on a host where only bsdtar is installed.
    """
    flags = flag_strings()
    gnu = flags['gnu']
    for forbidden in ('--uname', '--gname', '--uid', '--gid'):
        assert forbidden not in gnu, (forbidden, gnu)
    for required in ('--format=ustar', '--owner=root:0', '--group=wheel:0'):
        assert required in gnu, (required, gnu)
    bsdtar = flags['bsdtar']
    for required in ('--format ustar', '--uid 0', '--gid 0', '--uname root', '--gname wheel'):
        assert required in bsdtar, (required, bsdtar)
    print('  gnu flags             %s' % gnu)
    print('  bsdtar flags          %s' % bsdtar)


def test_gnu_option_grammar_accepts_the_build():
    """Run the real build through a tar that rejects what GNU tar 1.35 rejects.

    The fixture announces GNU tar 1.35, treats `--uname`/`--gname`/`--uid`/`--gid` as
    "unrecognized option" (exit 2) and accepts `--format=ustar` / `--owner=NAME:UID` /
    `--group=NAME:GID`, then writes a ustar archive itself. Nothing is delegated to the host
    tar, so the case runs identically on FreeBSD and Linux and the identity can be compared
    with the recorded digest. It is a grammar model, not the GNU binary: the real tool is
    exercised by the runner, which is where the original failure appeared.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        shim = fake_tar(tmp, flavour='tar (GNU tar) 1.35',
                        reject=('--uname', '--gname', '--uid', '--gid'))
        done, out = run_build(tmp, {'DM_TAR': shim})
        assert done.returncode == 0, (done.stdout, done.stderr)
        assert 'tar implementation: gnu' in done.stdout, done.stdout
        assert 'TAR_FORMAT=canonical-ustar members=1' in done.stdout, done.stdout
        assert 'TAR_CANONICALISED members=58' in done.stdout, done.stdout
        digest = re.search(r'^bundle sha256: ([0-9a-f]{64})$', done.stdout, re.M)
        assert digest, done.stdout
        recorded = re.search(r'^sha256 ([0-9a-f]{64})$',
                             (ROOT / 'release/bundle-digest.txt').read_text(), re.M)
        assert recorded, 'release/bundle-digest.txt has no sha256 line'
        assert digest.group(1) == recorded.group(1), (digest.group(1), recorded.group(1))
    print('  gnu grammar path      accepted, identity %s' % digest.group(1)[:16])


CASES = [
    test_tar_failure_is_fatal,
    test_probe_failure_is_reported,
    test_unknown_tar_implementation_is_refused,
    test_pax_archive_is_refused,
    test_gzip_failure_is_fatal,
    test_empty_tar_is_fatal,
    test_gnu_flag_string_is_valid_for_gnu_tar,
    test_gnu_option_grammar_accepts_the_build,
]


def main():
    for case in CASES:
        case()
        print('  %-38s PASS' % case.__name__)
    print('BUNDLE_BUILD_SAFETY=PASS cases=%d' % len(CASES))


if __name__ == '__main__':
    main()
