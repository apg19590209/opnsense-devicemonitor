#!/usr/bin/env python3
"""Verify an unpacked candidate archive, its required features, and its explicit source identity.

    validate-deploy-archive.py --archive FILE --identity FILE --source SHA --root DIR
"""
import hashlib
import json
import os
import sys
import tarfile


def opts(argv):
    out = {}
    i = 0
    while i < len(argv):
        if argv[i] in ('--archive', '--identity', '--source', '--root') and i + 1 < len(argv):
            out[argv[i]] = argv[i + 1]
            i += 2
        else:
            raise SystemExit('usage: validate-deploy-archive.py --archive FILE --identity FILE --source SHA --root DIR')
    for key in ('--archive', '--identity', '--source', '--root'):
        if not out.get(key):
            raise SystemExit('ABORT: missing %s' % key)
    if len(out['--source']) != 40 or any(c not in '0123456789abcdef' for c in out['--source']):
        raise SystemExit('ABORT: --source must be a lowercase 40-character commit SHA')
    return out


def identity(path):
    values = {}
    for line in open(path, encoding='utf-8'):
        if '=' in line:
            key, value = line.rstrip('\n').split('=', 1)
            values[key] = value
    return values


def main(argv):
    o = opts(argv)
    values = identity(o['--identity'])
    data = open(o['--archive'], 'rb').read()
    if values.get('source') != o['--source']:
        raise SystemExit('ABORT: archive identity source differs from requested source')
    if values.get('sha256') != hashlib.sha256(data).hexdigest():
        raise SystemExit('ABORT: archive bytes differ from identity sha256')
    if str(len(data)) != values.get('bytes'):
        raise SystemExit('ABORT: archive bytes differ from identity bytes')
    root = o['--root']
    with tarfile.open(o['--archive'], 'r:gz') as tar:
        members = tar.getmembers()
        names = [m.name for m in members]
        if not names or len(names) != len(set(names)):
            raise SystemExit('ABORT: archive membership is empty or duplicated')
        expected = sorted(names)
        regular = [n for n in names if os.path.isfile(os.path.join(root, n)) and not os.path.islink(os.path.join(root, n))]
        if expected != sorted(regular):
            raise SystemExit('ABORT: archive contains a non-regular member')
        for member in members:
            stream = tar.extractfile(member)
            unpacked = os.path.join(root, member.name)
            if stream is None or not os.path.isfile(unpacked):
                raise SystemExit('ABORT: unpacked member missing: ' + member.name)
            if hashlib.sha256(stream.read()).hexdigest() != hashlib.sha256(open(unpacked, 'rb').read()).hexdigest():
                raise SystemExit('ABORT: unpacked member differs: ' + member.name)
    version = json.load(open(os.path.join(root, 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json')))['version']
    feature_path = os.path.join(root, 'release/feature-set.txt')
    manifest_path = os.path.join(root, 'release/v%s-runtime.manifest' % version)
    if not os.path.isfile(feature_path) or not os.path.isfile(manifest_path):
        raise SystemExit('ABORT: required feature set or manifest missing')
    features = [line.strip() for line in open(feature_path, encoding='utf-8')
                if line.strip() and not line.startswith('#')]
    manifest = open(manifest_path, encoding='utf-8').read()
    archived = set(names)
    for feature in features:
        rows = [row.split() for row in manifest.splitlines()]
        if not any(len(row) >= 4 and row[2] == feature for row in rows):
            raise SystemExit('ABORT: manifest lacks feature ' + feature)
        if feature not in archived:
            raise SystemExit('ABORT: archive lacks feature ' + feature)
    if values.get('version') != version:
        raise SystemExit('ABORT: identity version differs from packaged version')
    print('DEPLOY_ARCHIVE_OK members=%d features=%d source=%s sha256=%s'
          % (len(names), len(features), o['--source'], values['sha256']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
