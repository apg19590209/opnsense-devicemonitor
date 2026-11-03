"""The bundle build must fail loudly instead of publishing a broken archive.

The first GitHub Actions run (#41609297193) published a 20-byte gzip as the runtime bundle:
`tar` rejected bsdtar's `--uid` flag, the `tar | gzip` pipeline reported only gzip's status,
and the script carried on. Decision 67 makes every stage an explicit, checked step and refuses
tar implementations it cannot verify, so this suite fakes each failure mode and requires a
nonzero exit with no archive left behind.

Each case runs the real `release/build-bundle.sh` against a fake tool on `DM_TAR` or `PATH`;
nothing is built from a clone, so the cases are fast and touch only a temporary directory.
"""
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'release/build-bundle.sh'
NORMALIZER = ROOT / 'release/normalize-bundle-tar.py'
REAL_TAR = '/usr/bin/bsdtar' if Path('/usr/bin/bsdtar').exists() else 'tar'


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


def assert_failed(done, out, marker):
    assert done.returncode != 0, ('build succeeded but should have failed:\n%s\n%s'
                                  % (done.stdout, done.stderr))
    assert marker in (done.stdout + done.stderr), (marker, done.stdout, done.stderr)
    assert not out.exists(), 'a failed build must not leave an archive behind'


def test_tar_failure_is_fatal():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        broken = fake(tmp, 'tar', (
            'case " $* " in\n'
            '  *" --version "*) echo "bsdtar 3.8.7 (fake)"; exit 0 ;;\n'
            '  *" -T "*) echo "fake tar: cannot read the file list" >&2; exit 1 ;;\n'
            '  *) exec %s "$@" ;;\n'
            'esac\n') % REAL_TAR)
        done, out = run_build(tmp, {'DM_TAR': broken})
        assert_failed(done, out, 'TAR_FAILED')
    print('  tar failure          rejected, no archive written')


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
        fakedir = tmp / 'bin'
        fakedir.mkdir()
        (fakedir / 'gzip').write_text('#!/bin/sh\necho "fake gzip: out of space" >&2\nexit 1\n')
        (fakedir / 'gzip').chmod(0o755)
        done, out = run_build(tmp, {'PATH': '%s:%s' % (fakedir, os.environ.get('PATH', ''))})
        assert_failed(done, out, 'GZIP_FAILED')
    print('  gzip failure         rejected, no archive written')


def test_empty_tar_is_fatal():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        empty = fake(tmp, 'empty-tar', (
            'case " $* " in\n'
            '  *" --version "*) echo "bsdtar 3.8.7 (fake)"; exit 0 ;;\n'
            '  *" -T "*) for last; do :; done; : > "$last"; exit 0 ;;\n'
            '  *) exec %s "$@" ;;\n'
            'esac\n') % REAL_TAR)
        done, out = run_build(tmp, {'DM_TAR': empty})
        assert_failed(done, out, 'TAR_EMPTY')
    print('  empty tar            rejected, no archive written')


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

    A shim models GNU tar's option grammar — `--version` says GNU tar 1.35, any `--uname`/
    `--gname`/`--uid`/`--gid` is an "unrecognized option" (exit 2), and `--format=ustar` /
    `--owner=NAME:UID` / `--group=NAME:GID` are accepted — then archives with the local
    bsdtar so the resulting bytes can be compared with the recorded identity. This is a
    grammar model, not the GNU binary: the real tool is exercised by the CI runner, which is
    where the original failure appeared.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        shim = tmp / 'gnu-tar-shim'
        shim.write_text(
            '#!/bin/sh\n'
            'case " $* " in\n'
            '  *" --version "*) echo "tar (GNU tar) 1.35"; exit 0 ;;\n'
            'esac\n'
            'for arg in "$@"; do\n'
            '  case "$arg" in\n'
            '    --uname*|--gname*|--uid*|--gid*)\n'
            '      echo "tar: unrecognized option \'$arg\'" >&2; exit 2 ;;\n'
            '  esac\n'
            'done\n'
            'filtered=""\n'
            'for arg in "$@"; do\n'
            '  case "$arg" in\n'
            '    --format=*|--owner=*|--group=*) ;;\n'
            '    *) filtered="$filtered $arg" ;;\n'
            '  esac\n'
            'done\n'
            'exec %s --format ustar --uid 0 --gid 0 --uname root --gname wheel $filtered\n'
            % REAL_TAR)
        shim.chmod(0o755)
        done, out = run_build(tmp, {'DM_TAR': str(shim)})
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
