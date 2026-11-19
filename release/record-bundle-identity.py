#!/usr/bin/env python3
"""Record a measured archive identity together with the source commit it was built from.

    record-bundle-identity.py SHA256 BYTES [NOTE_FILE]

Run from the checked-out content commit after building ``dm-v<version>-runtime.tar.gz`` from a
clean export of that same commit. It refuses a dirty worktree and writes ``version``, ``bytes``,
``sha256`` and ``# source = <HEAD>`` to ``release/bundle-digest.txt``. The source line is part of
the record because identical digest lines are not a git change: without it a later re-pin of an
unchanged identity cannot be told apart from the commit that first recorded it.
"""
import json
import re
import subprocess
import sys


def git(*args):
    return subprocess.run(['git'] + list(args), capture_output=True, text=True,
                          check=True, timeout=60).stdout.strip()


def main(argv):
    if not 2 <= len(argv) <= 3:
        raise SystemExit('usage: record-bundle-identity.py SHA256 BYTES [NOTE_FILE]')
    digest, size = argv[0], argv[1]
    if not re.fullmatch(r'[0-9a-f]{64}', digest) or not size.isdigit():
        raise SystemExit('ABORT: malformed identity')
    if git('status', '--porcelain'):
        raise SystemExit('ABORT: worktree is dirty')
    source = git('rev-parse', 'HEAD')
    version = json.load(open('src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json',
                             encoding='utf-8'))['version']
    path = 'release/bundle-digest.txt'
    text = open(path, encoding='utf-8').read()
    block = re.search(r'^version .*\nbytes .*\nsha256 .*\n(?:# source = .*\n)?', text, re.M)
    if not block:
        raise SystemExit('ABORT: digest record has no identity block')
    notes = open(argv[2], encoding='utf-8').read() if len(argv) == 3 else ''
    record = 'version %s\nbytes %s\nsha256 %s\n# source = %s\n%s' % (version, size, digest, source, notes)
    open(path, 'w', encoding='utf-8').write(text[:block.start()] + record + text[block.end():])
    print('DIGEST_RECORDED source=%s sha256=%s bytes=%s' % (source, digest, size))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
