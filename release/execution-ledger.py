#!/usr/bin/env python3
"""Append-only execution records, host acceptance, and close-out status for one candidate.

    execution-ledger.py record --ledger FILE --stage .23|.252|.253 --host IP \
        --source SHA --bundle SHA256 --phase deploy|own-check --checks NAME,NAME --result PASS|FAIL
    execution-ledger.py accept --ledger FILE --stage .23|.252|.253 --host IP \
        --source SHA --bundle SHA256 --identity FILE --out PASSED_FILE
    execution-ledger.py status --ledger FILE --source SHA --bundle SHA256 \
        --requirements FILE --report FILE
    execution-ledger.py exception --ledger FILE --requirement ID --reason TEXT
    execution-ledger.py handoff --ledger FILE --file FILE

The same exact check set is required for every host stage. Records name the actual host and
candidate; acceptance is generated only from PASS records, never from a free-form marker.
"""
import argparse
import datetime
import hashlib
import json
import os
import sys

STAGES = ('.23', '.252', '.253')
HOSTS = {'.23': '192.168.20.23', '.252': '192.168.20.252', '.253': '192.168.20.253'}
PREREQUISITE = {'.23': None, '.252': '.23', '.253': '.252'}
REQUIRED = {
    '.23': ('deploy', 'installed-hashes', 'records', 'authenticated-search',
            'authenticated-message', 'authenticated-csv', 'mutation-denial',
            'database-integrity', 'settings', 'daemon', 'catalogue'),
    '.252': ('deploy', 'installed-hashes', 'records', 'authenticated-search',
             'authenticated-message', 'authenticated-csv', 'mutation-denial',
             'database-integrity', 'settings', 'certificates', 'role', 'peer',
             'daemon', 'catalogue'),
    '.253': ('deploy', 'installed-hashes', 'records', 'authenticated-search',
             'authenticated-message', 'authenticated-csv', 'mutation-denial',
             'database-integrity', 'settings', 'certificates', 'role', 'peer',
             'daemon', 'catalogue'),
}


def fail(msg):
    raise SystemExit('ABORT: ' + msg)


def sha256(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def load(path):
    if not os.path.exists(path):
        return []
    return [json.loads(line) for line in open(path, encoding='utf-8') if line.strip()]


def append(path, row):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'a', encoding='utf-8') as stream:
        stream.write(json.dumps(row, sort_keys=True) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def stage_rows(rows, source, bundle, stage):
    return [r for r in rows if r.get('source') == source and r.get('bundle_sha256') == bundle
            and r.get('stage') == stage]


def passed(rows, source, bundle, stage, check):
    return any(r.get('host') == HOSTS[stage] and r.get('check') == check and
               r.get('result') == 'PASS' for r in stage_rows(rows, source, bundle, stage))


def missing(rows, source, bundle, stage):
    return [c for c in REQUIRED[stage] if not passed(rows, source, bundle, stage, c)]


def record(args):
    if args.stage not in STAGES or args.host != HOSTS[args.stage]:
        fail('stage and host must match')
    checks = [c for c in args.checks.split(',') if c]
    if not checks or any(c not in REQUIRED[args.stage] for c in checks):
        fail('unknown or empty check set')
    if args.phase not in ('deploy', 'own-check') or args.result not in ('PASS', 'FAIL'):
        fail('invalid phase or result')
    rows = load(args.ledger)

    if args.stage == '.252' and not any(r.get('stage') == '.23' and r.get('phase') == 'acceptance'
                                         and r.get('result') == 'PASS' for r in rows):
        fail('BACKUP has no passing .23 acceptance record')
    if args.stage == '.253' and not any(r.get('stage') == '.252' and r.get('phase') == 'acceptance'
                                         and r.get('result') == 'PASS' for r in rows):
        fail('MASTER has no passing .252 acceptance record')
    for check in checks:
        append(args.ledger, {'time': now(), 'stage': args.stage, 'host': args.host,
                             'source': args.source, 'bundle_sha256': args.bundle,
                             'phase': args.phase, 'check': check, 'result': args.result})


def accept(args):
    if args.stage not in STAGES or args.host != HOSTS[args.stage]:
        fail('stage and host must match')
    rows = load(args.ledger)
    left = missing(rows, args.source, args.bundle, args.stage)
    if left:
        fail('missing checks: ' + ','.join(left))
    prereq = PREREQUISITE[args.stage]
    if prereq and not os.path.isfile(args.out.replace(args.stage, prereq)):
        fail('prior acceptance missing for ' + prereq)
    if not os.path.isfile(args.identity) or sha256(args.identity[:-9]) != args.bundle:
        fail('identity does not match archive')
    marker = {'version': json.load(open(os.path.join(os.path.dirname(__file__), '..', 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json')))['version'],
              'source': args.source, 'bundle_sha256': args.bundle, 'host': args.host,
              'stage': args.stage, 'result': 'PASS', 'after': prereq,
              'evidence': 'execution-ledger:' + os.path.abspath(args.ledger),
              'accepted_at': now()}
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, 'x', encoding='utf-8') as stream:
        for key, value in marker.items():
            stream.write('%s=%s\n' % (key, value if value is not None else ''))
    append(args.ledger, {'time': now(), 'stage': args.stage, 'host': args.host,
                         'source': args.source, 'bundle_sha256': args.bundle,
                         'phase': 'acceptance', 'result': 'PASS'})
    print('ACCEPTANCE_RECORDED=' + args.out)


def requirements(path):
    out = []
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if line and not line.startswith('#'):
            key, _, value = line.partition('=')
            out.append((key, value))
    return out


def status(args):
    rows = load(args.ledger)
    open_stage = []
    for stage in STAGES:
        left = missing(rows, args.source, args.bundle, stage)
        accepted = any(r.get('stage') == stage and r.get('phase') == 'acceptance' and r.get('result') == 'PASS' for r in rows)
        print('STAGE_%s=%s acceptance=%s' % (stage, 'PASS' if not left else 'OPEN:' + ','.join(left), 'RECORDED' if accepted else 'OPEN'))
        open_stage.extend('%s:%s' % (stage, x) for x in left)
    req_results = []
    for key, value in requirements(args.requirements):
        if value.startswith('exception:'):
            ok = any(r.get('phase') == 'exception' and r.get('requirement') == value.split(':', 1)[1] for r in rows)
        else:
            ok = all(passed(rows, args.source, args.bundle, stage, value) for stage in STAGES)
        req_results.append((key, ok))
        print('REQUIREMENT_%s=%s' % (key, 'PASS' if ok else 'OPEN'))
    report_status = next((x for x in open(args.report, encoding='utf-8') if x.startswith('**Status:')), '')
    overall = 'COMPLETE' if not open_stage and all(ok for _, ok in req_results) else 'PARTIAL'
    if overall != 'COMPLETE' and 'Status: COMPLETE' in report_status:
        fail('report claims COMPLETE while required evidence is open')
    print('OVERALL_STATUS=' + overall)
    if overall != 'COMPLETE':
        for item in open_stage:
            print('OPEN=' + item)


def exception(args):
    append(args.ledger, {'time': now(), 'phase': 'exception', 'requirement': args.requirement,
                         'reason': args.reason})


def handoff(args):
    rows = load(args.ledger)
    with open(args.file, 'w', encoding='utf-8') as stream:
        stream.write('# Current task handoff\n\n')
        stream.write('Objective: complete Email Log recovery and release safeguards.\n\n')
        stream.write('Authority: local commits only; no push, merge, tag or publication; deploy only to the authorised stage.\n\n')
        bundles = sorted(set(r.get('bundle_sha256') for r in rows if r.get('bundle_sha256')))
        sources = sorted(set(r.get('source') for r in rows if r.get('source')))
        stream.write('Pinned candidate: %s\n' % (bundles[-1] if bundles else 'not yet pinned'))
        stream.write('Source: %s\n\n' % (sources[-1] if sources else 'not yet pinned'))
        for stage in STAGES:
            accepted = any(r.get('stage') == stage and r.get('phase') == 'acceptance' and r.get('result') == 'PASS' for r in rows)
            missing_checks = [] if accepted else [c for c in REQUIRED[stage] if not passed(rows, sources[-1] if sources else '', bundles[-1] if bundles else '', stage, c)]
            stream.write('- %s: %s\n' % (stage, 'accepted' if accepted else ('accepted (evidence ledger)' if not missing_checks else 'outstanding: ' + ','.join(missing_checks))))
        stream.write('\nOutstanding checks: `python3 release/execution-ledger.py status`.\n\n')
        stream.write('Stop conditions: price gate premium without approval; missing access; unsafe verification failure; action outside authority.\n')


def main(argv):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    fields = {
        'record': ('ledger', 'stage', 'host', 'source', 'bundle', 'phase', 'checks', 'result'),
        'accept': ('ledger', 'stage', 'host', 'source', 'bundle', 'identity', 'out'),
        'status': ('ledger', 'source', 'bundle', 'requirements', 'report'),
        'exception': ('ledger', 'requirement', 'reason'),
        'handoff': ('ledger', 'file'),
    }
    for name, names in fields.items():
        p = sub.add_parser(name)
        for field in names:
            p.add_argument('--' + field, required=True)
    args = parser.parse_args(argv)
    return {'record': record, 'accept': accept, 'status': status,
            'exception': exception, 'handoff': handoff}[args.command](args) or 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
