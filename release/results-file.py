#!/usr/bin/env python3
"""Write one machine-generated result file from actual command outcomes.

    results-file.py --out FILE --check NAME=PASS|FAIL [--check NAME=PASS|FAIL ...]
"""
import argparse
import json
import os
import secrets

p = argparse.ArgumentParser()
p.add_argument('--out', required=True)
p.add_argument('--check', action='append', required=True)
a = p.parse_args()
checks = {}
for item in a.check:
    name, sep, result = item.partition('=')
    if not name or sep != '=' or result not in ('PASS', 'FAIL'):
        raise SystemExit('ABORT: invalid check result')
    checks[name] = result
run = os.environ.get('DM_RUN_ID') or secrets.token_hex(16)
if os.environ.get('DM_RESULTS_REQUIRE_RUNNER') == '1' and not os.environ.get('DM_RUN_ID'):
    raise SystemExit('ABORT: results must be produced by the supported check runner')
payload = {'format': 'dm-check-results-v1', 'run': run, 'checks': checks}
tmp = a.out + '.new.' + str(os.getpid())
with open(tmp, 'w', encoding='utf-8') as stream:
    json.dump(payload, stream, sort_keys=True)
    stream.write('\n')
os.replace(tmp, a.out)
with open(a.out, 'rb') as stream:
    if stream.read(1) != b'{':
        raise SystemExit('ABORT: results file is not the machine format')
print(json.dumps(payload, sort_keys=True))
