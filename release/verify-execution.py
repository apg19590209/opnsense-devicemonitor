#!/usr/bin/env python3
"""Independent close-out audit: original requirements versus execution records.

    verify-execution.py --ledger FILE --source SHA --bundle SHA256 --requirements FILE \
        --report FILE

Read-only. Each requirement must name either a check that PASSes on all three stages, or an
explicit exception recorded by id. An unresolved requirement can make the task PARTIAL; it can
never be silently converted to COMPLETE.
"""
import argparse
import json

STAGES = ('.23', '.252', '.253')


def main(argv):
    p = argparse.ArgumentParser()
    for key in ('ledger', 'source', 'bundle', 'requirements', 'report'):
        p.add_argument('--' + key, required=True)
    a = p.parse_args(argv)
    rows = [json.loads(line) for line in open(a.ledger, encoding='utf-8') if line.strip()]
    for r in rows:
        if r.get('source') and r.get('source') != a.source:
            raise SystemExit('ABORT: ledger contains another source')
        if r.get('bundle_sha256') and r.get('bundle_sha256') != a.bundle:
            raise SystemExit('ABORT: ledger contains another candidate')
    results = {}
    for line in open(a.requirements, encoding='utf-8'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, _, spec = line.partition('=')
        if spec.startswith('exception:'):
            ident = spec.split(':', 1)[1]
            ok = any(r.get('phase') == 'exception' and r.get('requirement') == ident
                     for r in rows)
        else:
            ok = all(any(r.get('stage') == stage and r.get('check') == spec
                         and r.get('result') == 'PASS' for r in rows) for stage in STAGES)
        results[key] = ok
    report = open(a.report, encoding='utf-8').read()
    status = next((line for line in report.splitlines() if line.startswith('**Status:')), '')
    if not status:
        raise SystemExit('ABORT: report has no status line')
    if not all(results.values()) and 'Status: COMPLETE' in status:
        raise SystemExit('ABORT: report claims COMPLETE with unresolved requirements')
    for key, ok in results.items():
        print('REQUIREMENT_%s=%s' % (key, 'PASS' if ok else 'OPEN'))
    print('INDEPENDENT_STATUS=' + ('COMPLETE' if all(results.values()) else 'PARTIAL'))
    return 0 if all(results.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main(__import__('sys').argv[1:]))
