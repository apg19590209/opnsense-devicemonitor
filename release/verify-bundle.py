#!/usr/bin/env python3
"""Verify a Device Monitor bundle's exact member set and digests before it is used.

    verify-bundle.py --archive TAR.GZ --list LIST --identity FILE [--source SHA]

LIST is the bundler's one-path-per-line allow-list. Every member must be listed, every listed
member must be present, and each member's bytes must match the files in the current checkout
(the caller runs this after checking out the declared source). The archive must have no
directories, symlinks or duplicate members. The identity line is the one printed by
build-bundle.sh; no digest is inferred from a version number or a local checkout.
"""
import gzip
import hashlib
import sys
import tarfile


def parse_args(argv):
    opts = {'--archive': None, '--list': None, '--identity': None, '--source': None}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in opts and i + 1 < len(argv):
            opts[a] = argv[i + 1]
            i += 2
        else:
            raise SystemExit('usage: verify-bundle.py --archive FILE --list FILE --identity FILE [--source SHA]')
    for key in ('--archive', '--list', '--identity'):
        if not opts[key]:
            raise SystemExit('usage: verify-bundle.py --archive FILE --list FILE --identity FILE [--source SHA]')
    if opts['--source'] is not None and len(opts['--source']) != 40:
        raise SystemExit('ABORT: source identity must be a 40-character commit SHA')
    return opts


def read_list(path):
    with open(path, encoding='utf-8') as stream:
        items = [line.rstrip('\n') for line in stream if line.rstrip('\n')]
    if not items or len(items) != len(set(items)):
        raise SystemExit('ABORT: bundle list is empty or contains duplicates')
    for item in items:
        if item.startswith('/') or '..' in item.split('/') or not item:
            raise SystemExit('ABORT: unsafe member in bundle list: %r' % item)
    return items


def read_identity(path):
    values = {}
    with open(path, encoding='utf-8') as stream:
        for line in stream:
            if '=' in line:
                key, value = line.rstrip('\n').split('=', 1)
                values[key] = value
    for key in ('version', 'source', 'bytes', 'sha256'):
        if not values.get(key):
            raise SystemExit('ABORT: bundle identity is missing %s' % key)
    if len(values['sha256']) != 64 or any(c not in '0123456789abcdef' for c in values['sha256']):
        raise SystemExit('ABORT: bundle identity sha256 is not lowercase hexadecimal')
    if len(values['source']) != 40 or any(c not in '0123456789abcdef' for c in values['source']):
        raise SystemExit('ABORT: bundle identity source is not a 40-character commit SHA')
    return values


def main(argv):
    opts = parse_args(argv)
    listed = read_list(opts['--list'])
    identity = read_identity(opts['--identity'])
    data = open(opts['--archive'], 'rb').read()
    if str(len(data)) != identity['bytes']:
        raise SystemExit('ABORT: archive size %d does not match identity %s' % (len(data), identity['bytes']))
    if hashlib.sha256(data).hexdigest() != identity['sha256']:
        raise SystemExit('ABORT: archive sha256 does not match identity %s' % identity['sha256'])
    if opts['--source'] and opts['--source'] != identity['source']:
        raise SystemExit('ABORT: fetched source %s differs from bundle source %s'
                         % (opts['--source'], identity['source']))

    import io
    members = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz', format=tarfile.USTAR_FORMAT) as archive:
        for member in archive.getmembers():
            if not member.isfile():
                raise SystemExit('ABORT: non-regular archive member %s' % member.name)
            if member.name in members:
                raise SystemExit('ABORT: duplicate archive member %s' % member.name)
            members[member.name] = member
        expected = set(listed)
        actual = set(members)
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        if missing or extra:
            raise SystemExit('ABORT: archive membership missing=%s extra=%s' % (missing[:5], extra[:5]))
        for name in listed:
            stream = archive.extractfile(members[name])
            digest = hashlib.sha256(stream.read()).hexdigest()
            source = open(name, 'rb').read()
            if digest != hashlib.sha256(source).hexdigest():
                raise SystemExit('ABORT: archived bytes differ from source: %s' % name)
    print('BUNDLE_VERIFIED version=%s source=%s members=%d sha256=%s'
          % (identity['version'], identity['source'], len(listed), identity['sha256']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
