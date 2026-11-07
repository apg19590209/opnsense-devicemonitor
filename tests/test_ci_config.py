"""The workflow must select the suites it claims to run, on the branches it claims to cover.

Round-2 review H1: the remediation branch could not be tested at all, and the predecessor
step did not require the exact pass/skip outcome by name. This suite pins the triggers,
the preserved release-line entries and the selection itself — every `tests/*.py` named in
the workflow must exist, so a renamed or mistyped suite cannot silently drop out of CI.

The workflow is checked as text on purpose: PyYAML is not part of a stock GitHub runner, and
a YAML library dependency would make this check fail for the wrong reason.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / '.github/workflows/ci.yml').read_text()
TESTS = ROOT / 'tests'

# Branches whose existing behaviour must not regress when triggers are edited.
PRESERVED = [
    'v2.5-development',
    'v2.6-development',
    'v2.7-development',
    'v2.8-development',
    'v2.9-development',
    'v2.10-development',
    'feature/async-db-v2.11',
    'release/2.13',
]
REMEDIATION = 'fix/pruning-remediation-20261103'
INTEGRATION = 'integration/dm-bl-009-reconcile-20261105'


def trigger_block(name):
    match = re.search(r'^%s:\n(.*?)(?=^\S)' % name, WORKFLOW, re.M | re.S)
    assert match, 'no %s trigger' % name
    return match.group(1)


def test_remediation_branch_can_be_tested():
    assert re.search(r'^  workflow_dispatch:\s*$', WORKFLOW, re.M), \
        'no workflow_dispatch trigger'
    branches = trigger_block('  push')
    assert ('- %s' % REMEDIATION) in branches, branches
    # push triggers are evaluated against the pushed commit, so this alone is enough.
    assert 'push:' in WORKFLOW
    print('  trigger               push + workflow_dispatch, %s' % REMEDIATION)


def test_integration_branch_can_be_tested():
    branches = trigger_block('  push')
    assert ('- %s' % INTEGRATION) in branches, branches
    assert INTEGRATION not in trigger_block('  pull_request')
    print('  integration trigger   push-only, %s' % INTEGRATION)


def test_existing_branches_are_preserved():
    push = trigger_block('  push')
    pull = trigger_block('  pull_request')
    for branch in PRESERVED:
        assert ('- %s' % branch) in push, (branch, 'push')
    for branch in PRESERVED[:6]:
        assert ('- %s' % branch) in pull, (branch, 'pull_request')
    # The remediation branch is a push-only addition: pull_request filters on the PR *base*.
    assert REMEDIATION not in pull, 'the remediation branch must not be a PR base filter'
    print('  preserved             %d push branches, %d pull_request branches'
          % (len(PRESERVED), len(PRESERVED[:6])))


def test_every_named_suite_exists():
    names = sorted(set(re.findall(r'python3 tests/([A-Za-z0-9_]+\.py)', WORKFLOW)))
    assert names, 'the workflow names no test suites'
    missing = [name for name in names if not (TESTS / name).is_file()]
    assert not missing, 'workflow names missing suites: %s' % missing
    for required in ('test_upgrade_predecessors.py', 'test_bundle_determinism.py',
                     'test_rollback_isolated.py', 'test_prune_plan.py',
                     'test_locale_merge.py',
                     'test_integration_reconciliation.py'):
        assert required in names, '%s is not wired into CI' % required
    print('  suites referenced     %d (all present)' % len(names))


def test_predecessor_step_requires_ten_passes():
    step = re.search(r'name: Validate every accepted predecessor upgrade\n(.*?)(?=^      - name:)',
                     WORKFLOW, re.M | re.S)
    assert step, 'no predecessor step'
    body = step.group(1)
    assert "grep -q '^UPGRADE_PREDECESSORS=PASS passed=10 skipped=0$'" in body, body
    assert 'DM_ALLOW_SKIPPED_PREDECESSORS' not in body, body
    print('  predecessor step      asserts passed=10 skipped=0')


def test_determinism_step_is_wired():
    assert 'run: python3 tests/test_bundle_determinism.py' in WORKFLOW
    print('  determinism step      wired')


CASES = [
    test_remediation_branch_can_be_tested,
    test_integration_branch_can_be_tested,
    test_existing_branches_are_preserved,
    test_every_named_suite_exists,
    test_predecessor_step_requires_ten_passes,
    test_determinism_step_is_wired,
]


def main():
    for case in CASES:
        case()
        print('  %-42s PASS' % case.__name__)
    print('CI_CONFIG=PASS cases=%d' % len(CASES))


if __name__ == '__main__':
    main()
