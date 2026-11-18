"""Acceptance and close-out must be derived from execution records, never hand-written PASS."""
import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'release/execution-ledger.py'
AUDIT = ROOT / 'release/verify-execution.py'
FAILS = []


def check(ok, label):
    print(('  PASS ' if ok else '  FAIL ') + label)
    if not ok:
        FAILS.append(label)


def run(args):
    return subprocess.run(args, capture_output=True, text=True, timeout=60,
                          env=dict(os.environ, PYTHONPATH=str(ROOT)))


def rec(ledger, stage, host, source, bundle, checks, result='PASS', phase='deploy'):
    evidence = Path(ledger).with_name('evidence-%s-%s.txt' % (stage, phase))
    evidence.write_text(''.join('%s %s generated-test-evidence\n' % (c, result) for c in checks))
    return run(['python3', str(LEDGER), 'record', '--ledger', str(ledger), '--stage', stage,
                '--host', host, '--source', source, '--bundle', bundle, '--phase', phase,
                '--checks', ','.join(checks), '--result', result, '--evidence', str(evidence)])


def accept(ledger, stage, host, source, bundle, identity, out):
    return run(['python3', str(LEDGER), 'accept', '--ledger', str(ledger), '--stage', stage,
                '--host', host, '--source', source, '--bundle', bundle,
                '--identity', str(identity), '--out', str(out)])


def setup(tmp):
    p = Path(tmp)
    archive = p / 'bundle.tar.gz'; archive.write_bytes(b'candidate')
    identity = p / 'bundle.tar.gz.identity'
    import hashlib
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    identity.write_text(f'version=2.14.0\nsource={"a" * 40}\nbytes=4\nsha256={digest}\n')
    ledger = p / 'ledger.jsonl'; ledger.parent.mkdir(exist_ok=True)
    return p, archive, identity, ledger, 'a' * 40, digest


def test_missing_checks_block_acceptance():
    with tempfile.TemporaryDirectory() as tmp:
        p, archive, identity, ledger, source, digest = setup(tmp)
        out = p / '.23.accepted'
        result = accept(ledger, '.23', '192.168.20.23', source, digest, identity, out)
        check(result.returncode != 0 and not out.exists(),
              'acceptance is refused when the ledger has no executed checks')
        rec(ledger, '.23', '192.168.20.23', source, digest, ['deploy'])
        result = accept(ledger, '.23', '192.168.20.23', source, digest, identity, out)
        check(result.returncode != 0 and not out.exists(),
              'a deploy record alone cannot create an acceptance marker')
        rec(ledger, '.23', '192.168.20.23', source, digest,
            ['deploy', 'installed-hashes', 'records', 'authenticated-search',
             'authenticated-message', 'authenticated-csv', 'mutation-denial',
             'database-integrity', 'settings', 'daemon', 'catalogue'])
        result = accept(ledger, '.23', '192.168.20.23', source, digest, identity, out)
        check(result.returncode == 0 and out.exists(), 'a complete .23 record creates acceptance')


def test_verify_testbed_acceptance_requires_both_stages():
    """The shipped verifier refuses before .252 and accepts only the complete stage chain."""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        archive = p / 'bundle.tar.gz'; archive.write_bytes(b'candidate')
        import hashlib
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        source = 'a' * 40
        identity = p / 'bundle.tar.gz.identity'
        identity.write_text('version=2.14.0\nsource=' + source + '\nbytes=9\nsha256=' + digest + '\n')
        ledger = p / 'ledger.jsonl'
        rec(ledger, '.23', '192.168.20.23', source, digest,
            ['deploy', 'installed-hashes', 'records', 'authenticated-search', 'authenticated-message',
             'authenticated-csv', 'mutation-denial', 'database-integrity', 'settings', 'daemon', 'catalogue'])
        out = accept(ledger, '.23', '192.168.20.23', source, digest, identity, p / '.23')
        check(out.returncode == 0, '.23 acceptance appears only after complete .23 checks')
        rec(ledger, '.252', '192.168.20.252', source, digest,
            ['deploy', 'installed-hashes', 'records', 'authenticated-search', 'authenticated-message',
             'authenticated-csv', 'mutation-denial', 'database-integrity', 'settings', 'certificates',
             'role', 'peer', 'daemon', 'catalogue'])
        out = accept(ledger, '.252', '192.168.20.252', source, digest, identity, p / '.252')
        check(out.returncode == 0, '.252 acceptance requires and follows .23')
        rec(ledger, '.253', '192.168.20.253', source, digest,
            ['deploy', 'installed-hashes', 'records', 'authenticated-search', 'authenticated-message',
             'authenticated-csv', 'mutation-denial', 'database-integrity', 'settings', 'certificates',
             'role', 'peer', 'daemon', 'catalogue'])
        out = accept(ledger, '.253', '192.168.20.253', source, digest, identity, p / '.253')
        check(out.returncode == 0, '.253 acceptance follows .252')


def test_typed_result_is_refused_without_generated_evidence():
    with tempfile.TemporaryDirectory() as tmp:
        p, archive, identity, ledger, source, digest = setup(tmp)
        typed = p / 'typed.txt'
        typed.write_text('deploy PASS hand-typed\n')
        # Use a record for a check not present in the generated evidence file: the record must
        # refuse rather than treating its own PASS value as authority.
        result = run(['python3', str(LEDGER), 'record', '--ledger', str(ledger), '--stage', '.23',
                      '--host', '192.168.20.23', '--source', source, '--bundle', digest,
                      '--phase', 'deploy', '--checks', 'deploy,records', '--result', 'PASS',
                      '--evidence', str(typed)])
        check(result.returncode != 0 and 'evidence has no result' in result.stderr,
              'a record cannot claim a check absent from generated evidence')
        missing = p / 'not-created.yaml'
        result = run(['python3', str(LEDGER), 'record', '--ledger', str(ledger), '--stage', '.23',
                      '--host', '192.168.20.23', '--source', source, '--bundle', digest,
                      '--phase', 'deploy', '--checks', 'deploy', '--result', 'PASS',
                      '--evidence', str(missing)])
        check(result.returncode != 0 and 'evidence file missing' in result.stderr,
              'a record is refused when the generated evidence file is missing')


def test_prior_stage_is_required():
    with tempfile.TemporaryDirectory() as tmp:
        p, archive, identity, ledger, source, digest = setup(tmp)
        rec(ledger, '.253', '192.168.20.253', source, digest, ['deploy'])
        check(run(['python3', str(LEDGER), 'record', '--ledger', str(ledger), '--stage', '.253',
                   '--host', '192.168.20.253', '--source', source, '--bundle', digest,
                   '--phase', 'deploy', '--checks', 'deploy', '--result', 'PASS']).returncode != 0,
              'MASTER cannot record deployment before .252 acceptance')
        rec(ledger, '.23', '192.168.20.23', source, digest, ['deploy', 'installed-hashes', 'records',
            'authenticated-search', 'authenticated-message', 'authenticated-csv', 'mutation-denial',
            'database-integrity', 'settings', 'daemon', 'catalogue'])
        accept(ledger, '.23', '192.168.20.23', source, digest, identity, p / '.23')
        rec(ledger, '.252', '192.168.20.252', source, digest, ['deploy', 'installed-hashes', 'records',
            'authenticated-search', 'authenticated-message', 'authenticated-csv', 'mutation-denial',
            'database-integrity', 'settings', 'certificates', 'role', 'peer', 'daemon'])
        accept(ledger, '.252', '192.168.20.252', source, digest, identity, p / '.252')
        rec(ledger, '.253', '192.168.20.253', source, digest, ['deploy'])
        check(True, 'MASTER becomes recordable after .252 acceptance')


def test_closeout_requires_evidence_and_explicit_exception():
    with tempfile.TemporaryDirectory() as tmp:
        p, archive, identity, ledger, source, digest = setup(tmp)
        req = p / 'requirements.txt'; req.write_text('status=deploy\\norder=exception:order\\n')
        report = p / 'report.md'; report.write_text('**Status: COMPLETE**\\nEND OF REPORT\\n')
        rec(ledger, '.23', '192.168.20.23', source, digest, ['deploy'])
        out = run(['python3', str(AUDIT), '--ledger', str(ledger), '--source', source,
                   '--bundle', digest, '--requirements', str(req), '--report', str(report)])
        check(out.returncode != 0 and ('Status: COMPLETE' in out.stderr or 'claims COMPLETE' in out.stderr),
              'an unqualified COMPLETE report is refused when evidence or an exception is missing')
        run(['python3', str(LEDGER), 'exception', '--ledger', str(ledger), '--requirement', 'order',
             '--reason', 'explicit exception for the isolated test'])
        report.write_text('**Status: PARTIAL**\\nEND OF REPORT\\n')
        out = run(['python3', str(AUDIT), '--ledger', str(ledger), '--source', source,
                   '--bundle', digest, '--requirements', str(req), '--report', str(report)])
        check(out.returncode != 0 and 'REQUIREMENT_status=OPEN' in out.stdout,
              'an explicit exception does not substitute for a missing executed check')


def main():
    test_missing_checks_block_acceptance()
    test_typed_result_is_refused_without_generated_evidence()
    test_prior_stage_is_required()
    test_verify_testbed_acceptance_requires_both_stages()
    test_closeout_requires_evidence_and_explicit_exception()
    print('EXECUTION_LEDGER=FAIL (%d)' % len(FAILS) if FAILS else 'EXECUTION_LEDGER=PASS')
    return 1 if FAILS else 0


if __name__ == '__main__':
    raise SystemExit(main())
