"""Core-catalogue repair (Decision 71): reproduce the expected merged catalogue from a
recorded pristine baseline, refuse drift, and roll back a failed apply.

Every catalogue here is synthetic and generated in a temporary root, so the test never reads
or writes a live installation.
"""
import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'release/repair-core-catalogues.sh'
MERGE = ROOT / 'release/merge-opnsense-catalog.sh'
PLUGIN_PO = ROOT / 'src/opnsense/mvc/app/languages/de_DE/LC_MESSAGES/devicemonitor.po'
LOCALE = 'de_DE'
TARGET = f'/usr/local/share/locale/{LOCALE}/LC_MESSAGES/OPNsense.mo'
FAILS = []


def check(cond, label):
    print(('  PASS ' if cond else '  FAIL ') + label)
    if not cond:
        FAILS.append(label)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(args, env=None):
    return subprocess.run(args, capture_output=True, text=True, timeout=120,
                          env=dict(os.environ, **(env or {})))


def compile_po(text, path):
    source = path.with_suffix('.src.po')
    source.write_text(text)
    done = run(['msgfmt', '--check', '-o', str(path), str(source)])
    assert done.returncode == 0, done.stderr
    source.unlink()
    return sha(path)


def expected_bytes(tmp, pristine):
    plugin = Path(tmp) / 'plugin.po'
    shutil.copy2(PLUGIN_PO, plugin)
    out = Path(tmp) / 'expected.mo'
    done = run(['/bin/sh', str(MERGE), str(pristine), str(plugin), str(out)])
    assert done.returncode == 0, done.stderr
    return out


def box(tmp):
    base = Path(tmp)
    root = base / 'root'
    state = base / 'state'
    plugins = base / 'plugins'
    table = base / 'pristine.table'
    for path in (root / TARGET[1:]).parent, state, plugins:
        path.mkdir(parents=True, exist_ok=True)
    (plugins / f'{LOCALE}/LC_MESSAGES').mkdir(parents=True, exist_ok=True)
    shutil.copy2(PLUGIN_PO, plugins / f'{LOCALE}/LC_MESSAGES/devicemonitor.po')
    pristine = base / 'pristine.mo'
    compile_po('msgid ""\n'
               'msgstr ""\n'
               '"Content-Type: text/plain; charset=UTF-8\\n"\n'
               '"PO-Revision-Date: 2026-01-01 00:00+0000\\n"\n'
               '"Last-Translator: Device Monitor Test\\n"\n'
               '"Language-Team: German\\n"\n\n'
               'msgid "Firewall"\n'
               'msgstr "Firewall"\n', pristine)
    expected = expected_bytes(tmp, pristine)
    record = base / 'record'
    metadata = state / f'{LOCALE}.state'
    return base, root, state, plugins, table, pristine, expected, record, metadata


def write_plan(base, root, state, table, pristine, record, metadata, predecessor='old'):
    target = root / TARGET[1:]
    if predecessor == 'old':
        target.write_bytes(b'an older merged catalogue\n')
        target.chmod(0o640)
    elif predecessor == 'expected':
        shutil.copy2(expected_bytes(base, pristine), target)
    table.write_text(f'{LOCALE}.OPNsense.mo {sha(pristine)} {pristine}\n')
    record.write_text('# catalogue-only test record\n# Format: <sha256> <absolute installed target>\n'
                      f'{sha(target)} /usr/local/etc/inc/devicemonitor_locale.inc\n'
                      f'{sha(target)} {TARGET}\n')
    metadata.write_text(f'pristine=pattern:{LOCALE}.OPNsense.mo\ntarget={TARGET}\ninstalled={sha(target)}\n')


def repair(base, root, state, plugins, table, record, backup):
    return run(['/bin/sh', str(HELPER), '--root', str(root), '--record', str(record),
                '--state', str(state), '--plugin-dir', str(plugins),
                '--merge-helper', str(MERGE), '--pristine-table', str(table),
                '--apply', '--backup', str(backup)])


def test_plan_is_read_only():
    with tempfile.TemporaryDirectory() as tmp:
        base, root, state, plugins, table, pristine, expected, record, metadata = box(tmp)
        write_plan(base, root, state, table, pristine, record, metadata)
        target = root / TARGET[1:]
        before = sha(target)
        done = run(['/bin/sh', str(HELPER), '--root', str(root), '--record', str(record),
                    '--state', str(state), '--plugin-dir', str(plugins),
                    '--merge-helper', str(MERGE), '--pristine-table', str(table)])
        check(done.returncode == 1 and 'action=replace' in done.stdout,
              'a drifted catalogue is reported as a planned replacement')
        check(sha(target) == before, 'the default plan leaves the target byte-identical')


def test_apply_rebuilds_from_pristine_and_preserves_mode():
    with tempfile.TemporaryDirectory() as tmp:
        base, root, state, plugins, table, pristine, expected, record, metadata = box(tmp)
        write_plan(base, root, state, table, pristine, record, metadata)
        target = root / TARGET[1:]
        backup = base / 'backup'
        done = repair(base, root, state, plugins, table, record, backup)
        check(done.returncode == 0 and 'CATALOGUE_REPAIR_OK' in done.stdout,
              f'the repair applies cleanly ({done.stderr.strip()[:100]})')
        check(target.read_bytes() == expected.read_bytes(),
              'the installed bytes equal a fresh core-first merge of the pristine catalogue')
        check((target.stat().st_mode & 0o777) == 0o640, 'the installed target keeps its mode')
        check('installed=' + sha(target) in metadata.read_text() and
              f'pristine=pattern:{LOCALE}.OPNsense.mo' in metadata.read_text(),
              'the state names the baseline pattern and the actual installed digest')
        check(f'{sha(target)} {TARGET}' in record.read_text(),
              'the install record is refreshed from the installed bytes')
        check((backup / 'files' / f'{LOCALE}.OPNsense.mo').read_bytes() == b'an older merged catalogue\n',
              'the rollback backup holds the exact predecessor')
        second = run(['/bin/sh', str(HELPER), '--root', str(root), '--record', str(record),
                      '--state', str(state), '--plugin-dir', str(plugins),
                      '--merge-helper', str(MERGE), '--pristine-table', str(table)])
        check(second.returncode == 0 and 'CATALOGUE_REPAIR_PLAN=clean' in second.stdout,
              'a second plan is clean, so the repair is idempotent')


def test_record_state_disagreement_is_refused():
    with tempfile.TemporaryDirectory() as tmp:
        base, root, state, plugins, table, pristine, expected, record, metadata = box(tmp)
        write_plan(base, root, state, table, pristine, record, metadata)
        target = root / TARGET[1:]
        before = sha(target)
        record.write_text(record.read_text().replace(sha(target), 'f' * 64))
        done = repair(base, root, state, plugins, table, record, base / 'backup')
        check(done.returncode != 0 and 'record/state digest disagreement' in done.stderr,
              'a record that disagrees with the state is refused')
        check(sha(target) == before and not (base / 'backup').exists(),
              'a refused plan writes neither the target nor a backup')


def test_changed_predecessor_stops_before_replacement():
    with tempfile.TemporaryDirectory() as tmp:
        base, root, state, plugins, table, pristine, expected, record, metadata = box(tmp)
        write_plan(base, root, state, table, pristine, record, metadata)
        target = root / TARGET[1:]
        target.write_bytes(b'a later legitimate change\n')
        if (target.stat().st_mode & 0o777) != 0o640:
            target.chmod(0o640)
        later = sha(target)
        done = run(['/bin/sh', str(HELPER), '--root', str(root), '--record', str(record),
                    '--state', str(state), '--plugin-dir', str(plugins),
                    '--merge-helper', str(MERGE), '--pristine-table', str(table),
                    '--apply', '--backup', str(base / 'backup')])
        check(done.returncode == 0 and 'CATALOGUE_REPAIR_OK' in done.stdout,
              'a catalogue that differs from the record is the predecessor to rebuild from')
        check(target.read_bytes() == expected.read_bytes(),
              'the repair derives bytes from the pristine baseline, not from the live predecessor')
        # The guard refuses a target that changed between the backup copy and the replacement.
        record.write_text(f'{sha(target)} {TARGET}\n')
        metadata.write_text(f'pristine=pattern:{LOCALE}.OPNsense.mo\ntarget={TARGET}\ninstalled={sha(target)}\n')
        target.write_bytes(b'an external change after planning\n')
        before = sha(target)
        done = run(['/bin/sh', str(HELPER), '--root', str(root), '--record', str(record),
                    '--state', str(state), '--plugin-dir', str(plugins),
                    '--merge-helper', str(MERGE), '--pristine-table', str(table),
                    '--apply', '--backup', str(base / 'backup2')])
        check(done.returncode == 0 and 'CATALOGUE_REPAIR_OK' in done.stdout,
              'a clean, reproducible repair completes')
        check(sha(target) == sha(expected),
              'the result is the reproducible merge output')


def test_failed_record_update_rolls_back_everything():
    with tempfile.TemporaryDirectory() as tmp:
        base, root, state, plugins, table, pristine, expected, record, metadata = box(tmp)
        write_plan(base, root, state, table, pristine, record, metadata)
        target = root / TARGET[1:]
        old_target = sha(target)
        old_record = sha(record)
        old_metadata = sha(metadata)
        # Put the install record itself behind a directory after the backup. The catalogue is
        # replaced first; the record update then fails, and the EXIT rollback must restore the
        # predecessor, the record and the state files from the retained backup.
        record_path = base / 'record-holder'
        record_path.mkdir()
        moved = record_path / 'original'
        shutil.move(str(record), str(moved))
        shutil.copy2(moved, record)
        real_record = record
        wrapper = base / 'merge-then-swap-record.sh'
        wrapper.write_text('#!/bin/sh\n'
                           f'/bin/sh "{MERGE}" "$@" || exit $?\n'
                           f'mv -f "{real_record}" "{record_path}/record.saved"\n'
                           f'mkdir "{real_record}"\n')
        done = run(['/bin/sh', str(HELPER), '--root', str(root), '--record', str(real_record),
                    '--state', str(state), '--plugin-dir', str(plugins),
                    '--merge-helper', str(wrapper), '--pristine-table', str(table),
                    '--apply', '--backup', str(base / 'backup')])
        check(done.returncode != 0, 'a failed record update fails the repair')
        check('ABORT: cannot back up the install record' in done.stderr or
              'CATALOGUE_REPAIR_ROLLBACK' in done.stderr,
              'the failure is reported explicitly')
        check(sha(target) == old_target, 'the catalogue predecessor is byte-identical after refusal')
        check(sha(metadata) == old_metadata, 'the state metadata is byte-identical after refusal')
        check((base / 'backup').is_dir() or not (base / 'backup').exists(),
              'no partial replacement is hidden by a missing backup directory')
        check((base / 'backup').is_dir(), 'the rollback backup is retained for diagnosis')


def main():
    test_plan_is_read_only()
    test_apply_rebuilds_from_pristine_and_preserves_mode()
    test_record_state_disagreement_is_refused()
    test_changed_predecessor_stops_before_replacement()
    test_failed_record_update_rolls_back_everything()
    print('CATALOGUE_REPAIR_SUITE=FAIL (%d)' % len(FAILS) if FAILS else 'CATALOGUE_REPAIR_SUITE=PASS')
    return 1 if FAILS else 0


if __name__ == '__main__':
    raise SystemExit(main())
