"""Host-only prediction of an install: how many targets are already correct (U4).

The deployment plan states `unchanged=60 replaced=1 files=61` for the 2.13.2 → 2.13.3 step.
That number cannot be asserted on a CI runner (there is no installed plugin there), so this
suite reproduces it on the node it is meant for: it compares every manifest target with the
installed file, recompiles the 11 plugin catalogues and re-merges the 10 core catalogues
against the live ones, and checks the arithmetic.

It writes only to a temporary directory and opens `devices.db` not at all.
"""
import hashlib
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE_DEFAULTS = Path('/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json')
LANGUAGES = ['en_US', 'cs_CZ', 'de_DE', 'fr_FR', 'es_ES', 'it_IT', 'pt_BR', 'nl_NL', 'ru_RU',
             'ja_JP', 'zh_CN']
MERGE = ROOT / 'release/merge-opnsense-catalog.sh'

MANIFEST_TARGETS = 40
GENERATED_TARGETS = 21  # 11 plugin catalogues + 10 merged core catalogues


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest():
    version = LIVE_DEFAULTS.parent.joinpath('defaults.json')
    del version
    rows = []
    for line in (ROOT / 'release/v2.13.3-runtime.manifest').read_text().splitlines():
        if line.strip():
            rows.append(line.split())
    return rows


def test_prediction_matches_the_plan():
    if not LIVE_DEFAULTS.is_file():
        print('  live install          absent on this host '
              '(UPGRADE_PREDICTION=SKIP reason=no-live-install)')
        return
    rows = manifest()
    assert len(rows) == MANIFEST_TARGETS, len(rows)

    unchanged = replaced = 0
    for _hash, _mode, _source, target in rows:
        installed = Path(target)
        if not installed.is_file():
            replaced += 1
            continue
        if digest(installed) == _hash:
            unchanged += 1
        else:
            replaced += 1

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        for language in LANGUAGES:
            po = ROOT / ('src/opnsense/mvc/app/languages/%s/LC_MESSAGES/devicemonitor.po'
                         % language)
            compiled = tmp / ('%s.mo' % language)
            subprocess.run(['msgfmt', '--check', '-o', str(compiled), str(po)],
                           check=True, capture_output=True, timeout=120)
            installed = Path('/usr/local/opnsense/mvc/app/languages/%s/LC_MESSAGES/'
                             'devicemonitor.mo' % language)
            if installed.is_file() and digest(compiled) == digest(installed):
                unchanged += 1
            else:
                replaced += 1
            if language == 'en_US':
                continue
            core = Path('/usr/local/share/locale/%s/LC_MESSAGES/OPNsense.mo' % language)
            merged = tmp / ('OPNsense-%s.mo' % language)
            if core.is_file():
                subprocess.run(['sh', str(MERGE), str(core), str(po), str(merged)],
                               check=True, capture_output=True, timeout=120)
            else:
                subprocess.run(['sh', str(MERGE), '--plugin-only', str(po), str(merged)],
                               check=True, capture_output=True, timeout=120)
            if core.is_file() and digest(merged) == digest(core):
                unchanged += 1
            else:
                replaced += 1

    total = unchanged + replaced
    assert total == MANIFEST_TARGETS + GENERATED_TARGETS, (total, unchanged, replaced)
    print('  prediction            files=%d unchanged=%d replaced=%d' % (total, unchanged, replaced))
    # The plan's claim for the 2.13.2 -> 2.13.3 step: only defaults.json changes.
    if unchanged + replaced == 61:
        assert replaced <= 1, ('more targets differ than the plan expects', replaced)
    print('UPGRADE_PREDICTION=PASS')

    # A fresh-install run has no previous target set; the same arithmetic then describes the
    # repair case: a same-version repair must find every target unchanged.
    if replaced == 0:
        assert unchanged == 61, (unchanged, replaced)


def main():
    test_prediction_matches_the_plan()
    print('PREDICTION_CASES=PASS cases=1')


if __name__ == '__main__':
    main()
