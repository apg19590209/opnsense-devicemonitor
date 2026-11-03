"""The shipped legacy ownership evidence is exactly what the releases published.

`release/legacy-targets.txt` is the only thing that lets a node coming from an older line
lose the files those releases shipped and this one does not. It has to be reproducible from
the git history: regenerate it and compare. A missing tag is a failure unless
`DM_ALLOW_MISSING_HISTORY=1` is set deliberately, so a shallow clone cannot quietly shrink
the evidence to nothing.
"""
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / 'release/build-legacy-evidence.sh'
SHIPPED = ROOT / 'release/legacy-targets.txt'

# Must match DEFAULT_TAGS in the generator; asserted below so the two cannot drift.
TAGS = ['v2.9', 'v2.10', 'v2.11-patch1', 'v2.13', 'v2.13.1', 'v2.13.2']

NAMESPACE = re.compile(
    r'^(/usr/local/opnsense/'
    r'|/usr/local/etc/rc\.d/devicemonitor$'
    r'|/usr/local/etc/inc/plugins\.inc\.d/devicemonitor\.inc$'
    r'|/usr/local/etc/inc/devicemonitor_locale\.inc$)'
)


def allow_missing():
    return os.environ.get('DM_ALLOW_MISSING_HISTORY') == '1'


def rows(text):
    return [line.split() for line in text.splitlines()
            if line.strip() and not line.startswith('#')]


def test_tag_list_matches_generator():
    script = GENERATOR.read_text()
    match = re.search(r'^DEFAULT_TAGS="([^"]+)"$', script, re.M)
    assert match, 'generator has no DEFAULT_TAGS'
    assert match.group(1).split() == TAGS, match.group(1).split()


def test_evidence_is_reproducible():
    missing = [tag for tag in TAGS
               if subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '-q', '--verify',
                                  'refs/tags/%s' % tag],
                                 capture_output=True).returncode != 0]
    if missing:
        assert allow_missing(), (
            'missing tags %s: fetch the history (fetch-depth: 0) or set '
            'DM_ALLOW_MISSING_HISTORY=1 for a deliberate local run' % missing)
        print('  SKIPPED reproducibility: missing tags %s' % missing)
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / 'legacy-targets.txt'
        done = subprocess.run(['sh', str(GENERATOR), str(out)],
                              capture_output=True, text=True, timeout=120)
        assert done.returncode == 0, (done.stdout, done.stderr)
        regenerated = out.read_text()

    assert regenerated == SHIPPED.read_text(), (
        'release/legacy-targets.txt is stale: re-run release/build-legacy-evidence.sh')


def test_evidence_rows_are_shaped_and_owned():
    """Every row is a digest plus an absolute path this plugin may own."""
    parsed = rows(SHIPPED.read_text())
    assert parsed, 'no evidence rows'
    seen = set()
    for digest, path in parsed:
        assert re.fullmatch(r'[0-9a-f]{64}', digest), digest
        assert path.startswith('/'), path
        assert NAMESPACE.match(path), path
        assert (digest, path) not in seen, (digest, path)
        seen.add((digest, path))
    # The headers must name every manifest the rows came from.
    text = SHIPPED.read_text()
    for tag in TAGS:
        assert ('#   %s@release/' % tag) in text, tag


def test_evidence_covers_the_known_legacy_leftovers():
    """The v2.9 catalogues that no current release ships are in the evidence."""
    text = SHIPPED.read_text()
    for legacy in ('/usr/local/opnsense/mvc/app/languages/cs_CZ_devicemonitor.po',
                   '/usr/local/opnsense/mvc/app/languages/en_US_devicemonitor.po'):
        assert legacy in text, legacy


def test_evidence_does_not_claim_foreign_paths():
    """Nothing outside the plugin's namespaces leaks into the evidence."""
    for _digest, path in rows(SHIPPED.read_text()):
        assert '/etc/rc.conf' not in path, path
        assert '/usr/local/share/locale/' not in path, path
        assert '/usr/local/www/' not in path, path


CASES = [
    test_tag_list_matches_generator,
    test_evidence_is_reproducible,
    test_evidence_rows_are_shaped_and_owned,
    test_evidence_covers_the_known_legacy_leftovers,
    test_evidence_does_not_claim_foreign_paths,
]


def main():
    for case in CASES:
        case()
        print('  %-46s PASS' % case.__name__)
    print('LEGACY_EVIDENCE=PASS cases=%d' % len(CASES))


if __name__ == '__main__':
    main()
