"""Catalogue compilation and merging are deterministic (U5).

A repair install only reports `unchanged=` when recompiling the 11 plugin catalogues and
merging the plugin keys into the 10 core catalogues reproduces the installed bytes. This
suite proves the property directly: the same inputs are processed twice and the outputs must
be byte-identical.
"""
import hashlib
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MERGE = ROOT / 'release/merge-opnsense-catalog.sh'
LANGUAGES = ['en_US', 'cs_CZ', 'de_DE', 'fr_FR', 'es_ES', 'it_IT', 'pt_BR', 'nl_NL', 'ru_RU',
             'ja_JP', 'zh_CN']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def po(language):
    return ROOT / ('src/opnsense/mvc/app/languages/%s/LC_MESSAGES/devicemonitor.po' % language)


def test_msgfmt_is_deterministic():
    """Compiling the same catalogue twice gives the same bytes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        for language in LANGUAGES:
            outputs = []
            for attempt in ('a', 'b'):
                out = tmp / ('%s-%s.mo' % (language, attempt))
                subprocess.run(['msgfmt', '--check', '-o', str(out), str(po(language))],
                               check=True, capture_output=True, timeout=120)
                outputs.append(digest(out))
            assert outputs[0] == outputs[1], (language, outputs)
    print('  msgfmt                %d catalogues, identical bytes' % len(LANGUAGES))


def test_core_merge_is_deterministic():
    """Merging the same core catalogue and plugin catalogue twice gives the same bytes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        core_po = po('nl_NL')
        outputs = []
        for attempt in ('a', 'b'):
            core_mo = tmp / ('core-%s.mo' % attempt)
            subprocess.run(['msgfmt', '--check', '-o', str(core_mo), str(core_po)],
                           check=True, capture_output=True, timeout=120)
            merged = tmp / ('merged-%s.mo' % attempt)
            subprocess.run(['sh', str(MERGE), str(core_mo), str(po('cs_CZ')), str(merged)],
                           check=True, capture_output=True, timeout=120)
            outputs.append(digest(merged))
        assert outputs[0] == outputs[1], outputs

        # And the plugin-only branch, used where a locale has no core catalogue.
        outputs = []
        for attempt in ('a', 'b'):
            merged = tmp / ('plugin-only-%s.mo' % attempt)
            subprocess.run(['sh', str(MERGE), '--plugin-only', str(po('cs_CZ')), str(merged)],
                           check=True, capture_output=True, timeout=120)
            outputs.append(digest(merged))
        assert outputs[0] == outputs[1], outputs
    print('  merge                 core-first and plugin-only branches, identical bytes')


CASES = [test_msgfmt_is_deterministic, test_core_merge_is_deterministic]


def main():
    for case in CASES:
        case()
        print('  %-38s PASS' % case.__name__)
    print('CATALOGUE_DETERMINISM=PASS cases=%d' % len(CASES))


if __name__ == '__main__':
    main()
