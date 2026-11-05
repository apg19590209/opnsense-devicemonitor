"""The installer's stdout contract, and the promise that --check never mutates.

`CHECK_OK` and `INSTALL_OK` are machine-read by deployment scripts, so their keys are
append-only: the 2.13.2 order stays a prefix and new fields go on the end. The same file
pins the two behaviours the 2.13.2 review found undocumented or untrue: a repair install
leaves an unchanged target alone, and `--check` exits before anything is written.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = (ROOT / 'install-unattended.sh').read_text()
README = (ROOT / 'README.md').read_text()

# The 2.13.2 contract, which must remain a prefix of the current one.
CHECK_OK_2132 = ['version', 'predecessor', 'files', 'core_locales', 'prunable',
                 'daemon_running', 'host']
INSTALL_OK_2132 = ['version', 'files', 'core_locales', 'pruned', 'backup',
                   'daemon_restarted']


def format_line(marker):
    match = re.search(r"printf '(%s [^']*)'" % marker, INSTALLER)
    assert match, 'no %s status line in install-unattended.sh' % marker
    return match.group(1)


def keys(marker):
    return re.findall(r'([a-z_]+)=%s', format_line(marker))


def readme_keys(marker):
    line = next((l for l in README.splitlines()
                 if l.startswith(marker + ' ') or (' `' + marker + ' ') in l),
                None)
    assert line, 'README does not document the %s line' % marker
    return re.findall(r'([a-z_]+)=\S*', line)


def test_check_ok_is_append_only():
    current = keys('CHECK_OK')
    assert current[:len(CHECK_OK_2132)] == CHECK_OK_2132, current
    assert current[len(CHECK_OK_2132):] == ['legacy_prunable', 'retained'], current
    assert readme_keys('CHECK_OK') == current, readme_keys('CHECK_OK')


def test_install_ok_is_append_only():
    current = keys('INSTALL_OK')
    assert current[:len(INSTALL_OK_2132)] == INSTALL_OK_2132, current
    assert current[len(INSTALL_OK_2132):] == ['unchanged', 'repaired'], current
    assert readme_keys('INSTALL_OK') == current, readme_keys('INSTALL_OK')


def test_check_is_non_mutating():
    """Nothing the script *runs* before the --check exit writes anything.

    The rollback function is defined early but only runs from the EXIT trap, so it is
    scrubbed before the read-only half is inspected.
    """
    start = INSTALLER.index('cleanup() {')
    end = INSTALLER.index('trap cleanup EXIT')
    scrub = INSTALLER[:start] + INSTALLER[end:]
    assert 'trap cleanup EXIT' in scrub

    guard = scrub.index('[ "$CHECK_ONLY" = 0 ] || exit 0')
    head = scrub[:guard]
    mutating = ('install -m ', 'pkg install', 'service ', 'rm -f /', 'mv /', 'ln -s ',
                'chmod ', 'mkdir -p /var', 'MUTATING=1')
    for number, line in enumerate(head.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        # Status and notice text describes commands; drop every quoted string so only the
        # command words of the line are inspected.
        scan = re.sub(r"'[^']*'", "''", stripped)
        scan = re.sub(r'"[^"]*"', '""', scan)
        for token in mutating:
            assert token not in scan, (number, token, stripped)
    # Registering the plugin is a mutation; testing that it is executable is not.
    assert not any(line.strip().startswith('/usr/local/etc/rc.configure_plugins')
                   for line in head.splitlines())
    assert 'MUTATING=1' in scrub[guard:], 'mutation phase missing'
    # The prune plan is computed inside the read-only half, so --check can report it.
    assert head.index('"$SCRIPT_DIR/$PRUNE_HELPER" compute') < guard


def test_unchanged_targets_are_skipped():
    """A repair install does not rewrite a byte-identical target."""
    skip = INSTALLER.index('if [ "$old" = "$new" ]; then')
    install = INSTALLER.index('install -m "$mode" -o "$owner" -g "$group"')
    assert skip < install, (skip, install)
    # The skip path re-verifies the digest instead of trusting the frozen plan.
    between = INSTALLER[skip:install]
    assert 'sha256 -q "$target"' in between
    assert 'UNCHANGED=$((UNCHANGED + 1))' in between


def test_inventory_covers_generated_targets():
    """Both the current side and the record come from the run's own target plan."""
    assert 'awk \'{print $6}\' "$STAGE/plan" > "$STAGE/current-targets"' in INSTALLER
    assert "awk '{print $3, $6}' \"$BACKUP/plan\"" in INSTALLER
    # The record must not be derived from the manifest alone: that omits the 11 .mo files.
    assert "awk '{print $4}' \"$MANIFEST\" | sort -u > \"$INSTALLED_LIST\"" not in INSTALLER


def test_record_has_digests_and_is_written_atomically():
    assert '> "$INSTALLED_LIST.new"' in INSTALLER
    assert 'mv "$INSTALLED_LIST.new" "$INSTALLED_LIST"' in INSTALLER
    assert '<sha256> <absolute installed target>' in INSTALLER


CASES = [
    test_check_ok_is_append_only,
    test_install_ok_is_append_only,
    test_check_is_non_mutating,
    test_unchanged_targets_are_skipped,
    test_inventory_covers_generated_targets,
    test_record_has_digests_and_is_written_atomically,
]


def main():
    for case in CASES:
        case()
        print('  %-42s PASS' % case.__name__)
    print('INSTALLER_STATUS=PASS cases=%d' % len(CASES))


if __name__ == '__main__':
    main()
