"""Every input the installer executes or trusts is pinned, and the pins are enforced.

The 2.13.2 review found `release/compute-prune.sh` being executed without verification while
the manifest and every payload source were pinned. Decision 62 moves all executed inputs
behind `release/release-inputs.sha256`, pins that file inline in `install-unattended.sh`, and
runs `release/verify-release-inputs.sh` before anything else happens. These cases keep the
three layers consistent and prove that a tampered helper is refused.
"""
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / 'release'
INSTALLER = ROOT / 'install-unattended.sh'
DEFAULTS = ROOT / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'

REQUIRED_INPUTS = {
    'release/prune-plan.sh',
    'release/legacy-targets.txt',
    'release/merge-opnsense-catalog.sh',
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def installer_text():
    return INSTALLER.read_text()


def pin(name):
    match = re.search(r'^%s=([0-9a-f]{64})$' % re.escape(name), installer_text(), re.M)
    assert match, 'missing pin %s in install-unattended.sh' % name
    return match.group(1)


def inputs_rows():
    rows = {}
    for line in (RELEASE / 'release-inputs.sha256').read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        digest, path = line.split()
        rows[path] = digest
    return rows


def installed_version():
    match = re.search(r'^VERSION=([0-9.]+)$', installer_text(), re.M)
    assert match, 'installer has no VERSION'
    return match.group(1)


def assert_manifest_guards(text, manifest_rows):
    """The installer's row and target guards follow the manifest and locale loop."""
    count = re.search(r'^\[ .*wc -l < "\$MANIFEST".*?= ([0-9]+) \]', text, re.M)
    assert count, 'installer has no manifest row-count guard'
    assert int(count.group(1)) == manifest_rows, (count.group(1), manifest_rows)

    languages_match = re.search(r'^for lang in ([^;]+); do$', text, re.M)
    assert languages_match, 'installer has no sidecar language loop'
    languages = languages_match.group(1).split()
    assert 'en_US' in languages, languages

    expected = re.search(r'^expected=([0-9]+)$', text, re.M)
    expected_fresh = re.search(r'^\[ "\$FRESH" = 0 \] \|\| expected=([0-9]+)$', text, re.M)
    assert expected and expected_fresh, 'installer has no target-count guards'

    # Every language gets a sidecar .mo; every language except en_US also gets a
    # merged core-domain catalogue. A fresh install adds one rc.conf target.
    upgrade_targets = manifest_rows + len(languages) + (len(languages) - 1)
    assert int(expected.group(1)) == upgrade_targets, (expected.group(1), upgrade_targets, languages)
    assert int(expected_fresh.group(1)) == upgrade_targets + 1, (
        expected_fresh.group(1), upgrade_targets + 1, languages)


def verify(root):
    return subprocess.run(['sh', str(Path(root) / 'release/verify-release-inputs.sh'), str(root)],
                          capture_output=True, text=True, timeout=120)


def test_pins_are_consistent():
    """The inline pins, the inputs file and the files on disk all agree."""
    version = installed_version()
    manifest = 'release/v%s-runtime.manifest' % version
    rows = inputs_rows()

    assert REQUIRED_INPUTS <= set(rows), sorted(REQUIRED_INPUTS - set(rows))
    assert manifest in rows, manifest
    for path, digest in rows.items():
        assert (ROOT / path).is_file(), path
        assert sha256(ROOT / path) == digest, path

    assert pin('MANIFEST_SHA') == sha256(ROOT / manifest)
    assert pin('MANIFEST_SHA') == rows[manifest]
    assert pin('RELEASE_INPUTS_SHA') == sha256(RELEASE / 'release-inputs.sha256')
    assert pin('VERIFIER_SHA') == sha256(RELEASE / 'verify-release-inputs.sh')


def test_manifest_guards_match_target_derivation():
    """A manifest row change must move every coupled installer guard."""
    version = installed_version()
    manifest = RELEASE / ('v%s-runtime.manifest' % version)
    manifest_rows = len(manifest.read_text().splitlines())
    assert_manifest_guards(installer_text(), manifest_rows)


def test_version_is_single_sourced():
    """One version string: defaults.json, the installer constant and the manifest name."""
    version = json.loads(DEFAULTS.read_text())['version']
    assert installed_version() == version, (installed_version(), version)
    assert (RELEASE / ('v%s-runtime.manifest' % version)).is_file()
    text = installer_text()
    assert 'MANIFEST=release/v${VERSION}-runtime.manifest' in text
    # No status line may hardcode the version: parsers key on the field name.
    assert not re.search(r'version=2\.\d', text), 'hardcoded version in a status line'
    assert 'version=%s' in text


def test_verifier_accepts_the_checkout():
    """The shipped tree passes its own verification."""
    done = verify(ROOT)
    assert done.returncode == 0, (done.stdout, done.stderr)
    assert 'VERIFY_OK=' in done.stdout, done.stdout


def test_corrupted_helper_is_refused():
    """A modified helper, a missing input and a symlinked input all abort."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bundle = Path(tmpdir) / 'bundle'
        shutil.copytree(RELEASE, bundle / 'release')

        done = verify(bundle)
        assert done.returncode == 0, (done.stdout, done.stderr)

        helper = bundle / 'release/prune-plan.sh'
        original = helper.read_text()
        helper.write_text(original + '\n# tampered\n')
        done = verify(bundle)
        assert done.returncode != 0, done.stdout
        assert 'VERIFY_FAILED=release/prune-plan.sh' in done.stderr, done.stderr
        assert 'VERIFY_OK=' not in done.stdout, done.stdout

        helper.write_text(original)
        done = verify(bundle)
        assert done.returncode == 0, (done.stdout, done.stderr)

        # A missing input is a failure, not a skip.
        evidence = bundle / 'release/legacy-targets.txt'
        moved = bundle / 'legacy-targets.bak'
        evidence.rename(moved)
        done = verify(bundle)
        assert done.returncode != 0, done.stdout
        assert 'VERIFY_FAILED=release/legacy-targets.txt' in done.stderr, done.stderr

        # A symlink is refused even when it points at identical content.
        moved.rename(evidence)
        decoy = bundle / 'decoy.txt'
        shutil.copy2(evidence, decoy)
        evidence.unlink()
        evidence.symlink_to(decoy)
        done = verify(bundle)
        assert done.returncode != 0, done.stdout
        assert 'VERIFY_FAILED=release/legacy-targets.txt' in done.stderr, done.stderr


def test_verification_precedes_execution():
    """The installer verifies its inputs before it runs the prune helper."""
    text = installer_text()
    pin_line = text.index('RELEASE_INPUTS_SHA=')
    verify_line = text.index('/bin/sh "$VERIFIER"')
    first_helper = text.index('"$SCRIPT_DIR/$PRUNE_HELPER"')
    assert pin_line < verify_line < first_helper, (pin_line, verify_line, first_helper)
    assert 'ABORT: release inputs' in text


def test_generator_is_atomic():
    """A failed regeneration must not leave a partial or altered checksum file (L8)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tree = Path(tmpdir) / 'tree'
        tree.mkdir()
        archive = subprocess.run(['git', '-C', str(ROOT), 'archive', '--format=tar', 'HEAD'],
                                 capture_output=True, check=True, timeout=180)
        subprocess.run(['tar', '-x', '-C', str(tree)], input=archive.stdout,
                       check=True, timeout=180)

        generator = tree / 'release/build-release-inputs.sh'
        target = tree / 'release/release-inputs.sha256'
        done = subprocess.run(['sh', str(generator)], capture_output=True, text=True,
                              timeout=180)
        assert done.returncode == 0, (done.stdout, done.stderr)
        assert not (tree / 'release/release-inputs.sha256.new').exists()
        before = target.read_text()

        (tree / 'release/legacy-targets.txt').unlink()
        done = subprocess.run(['sh', str(generator)], capture_output=True, text=True,
                              timeout=180)
        assert done.returncode != 0, (done.stdout, done.stderr)
        assert 'missing release/legacy-targets.txt' in done.stderr, done.stderr
        assert target.read_text() == before, 'a failed run must not touch the checksum file'
        assert not (tree / 'release/release-inputs.sha256.new').exists()


CASES = [
    test_pins_are_consistent,
    test_manifest_guards_match_target_derivation,
    test_version_is_single_sourced,
    test_verifier_accepts_the_checkout,
    test_corrupted_helper_is_refused,
    test_verification_precedes_execution,
    test_generator_is_atomic,
]


def main():
    for case in CASES:
        case()
        print('  %-34s PASS' % case.__name__)
    print('RELEASE_INPUTS=PASS cases=%d' % len(CASES))


if __name__ == '__main__':
    main()
