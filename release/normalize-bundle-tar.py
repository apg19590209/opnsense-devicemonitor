#!/usr/bin/env python3
"""Canonicalise a Device Monitor bundle tar so any tar producer gives the same bytes.

`release/build-bundle.sh` pins member order, mtimes and ownership, but the *textual*
encoding of a ustar header is producer-specific: bsdtar writes `000644 \\0` while GNU tar
writes `000644\\0`, GNU may write the old `ustar  \\0` magic, and each tool chooses its own
padding for devmajor/devminor. The first GitHub run proved the consequence: the same tree
built an archive with a different identity on Linux.

This helper rewrites every header field that a tar implementation may encode differently
into one canonical form, then recomputes the checksum. Anything it does not understand is a
hard failure, so an unsupported producer can never silently ship a different archive.

    normalize-bundle-tar.py IN.tar OUT.tar     rewrite into canonical ustar
    normalize-bundle-tar.py --check IN.tar     parse and reject unsupported producers

Canonical values (Decision 67): uid 0 / gid 0, uname `root`, gname `wheel`,
mtime 1767225600 (2026-01-01T00:00:00Z), magic `ustar`+`00`, empty devmajor/devminor and
prefix, mode and size preserved. Encoding: 6 octal digits + space + NUL for mode/uid/gid/
devmajor/devminor, 11 octal digits + space for size/mtime, 6 octal digits + NUL + space for
the checksum.
"""
import sys

BLOCK = 512
CANONICAL_MTIME = 1767225600
CANONICAL_OWNER = (b'root', b'wheel')
ZERO_FIELD_LIMIT = 8 ** 6 - 1

FIELDS = (
    ('name', 0, 100), ('mode', 100, 108), ('uid', 108, 116), ('gid', 116, 124),
    ('size', 124, 136), ('mtime', 136, 148), ('chksum', 148, 156), ('typeflag', 156, 157),
    ('linkname', 157, 257), ('magic', 257, 263), ('version', 263, 265), ('uname', 265, 297),
    ('gname', 297, 329), ('devmajor', 329, 337), ('devminor', 337, 345), ('prefix', 345, 500),
)
OFFSETS = dict((name, (start, end)) for name, start, end in FIELDS)


def field(header, name):
    start, end = OFFSETS[name]
    return header[start:end]


def put(header, name, value):
    start, end = OFFSETS[name]
    if len(value) > end - start:
        raise SystemExit('normalize-bundle-tar: %s does not fit its ustar field' % name)
    header[start:end] = value + b'\0' * (end - start - len(value))


def number(header, name):
    raw = field(header, name).strip(b'\0 ').strip()
    if not raw:
        return 0
    try:
        return int(raw, 8)
    except ValueError:
        raise SystemExit('normalize-bundle-tar: %s is not octal: %r' % (name, raw))


def small(value, what):
    if value < 0 or value > ZERO_FIELD_LIMIT:
        raise SystemExit('normalize-bundle-tar: %s does not fit 6 octal digits: %d'
                         % (what, value))
    return ('%06o ' % value).encode() + b'\0'


def wide(value, what):
    if value < 0 or value > 8 ** 11 - 1:
        raise SystemExit('normalize-bundle-tar: %s does not fit 11 octal digits: %d'
                         % (what, value))
    return ('%011o ' % value).encode()


def checksum(header):
    saved = bytes(field(header, 'chksum'))
    header[OFFSETS['chksum'][0]:OFFSETS['chksum'][1]] = b' ' * 8
    total = sum(header)
    header[OFFSETS['chksum'][0]:OFFSETS['chksum'][1]] = saved
    return total


def parse(header):
    magic = field(header, 'magic')
    if magic not in (b'ustar\0', b'ustar '):
        raise SystemExit('normalize-bundle-tar: unsupported header magic %r (pax and GNU '
                         'extended formats are refused)' % magic)
    typeflag = field(header, 'typeflag')
    if typeflag not in (b'0', b'\0'):
        raise SystemExit('normalize-bundle-tar: unsupported member type %r (only regular '
                         'files belong in the runtime bundle)' % typeflag)
    if field(header, 'prefix').strip(b'\0'):
        raise SystemExit('normalize-bundle-tar: ustar name prefix present; a canonical '
                         'bundle keeps every member name under 100 bytes with no prefix')
    return number(header, 'size'), number(header, 'mode'), field(header, 'name').rstrip(b'\0')


def rewrite(header, mode, size):
    put(header, 'mode', small(mode, 'mode'))
    put(header, 'uid', small(0, 'uid'))
    put(header, 'gid', small(0, 'gid'))
    put(header, 'size', wide(size, 'size'))
    put(header, 'mtime', wide(CANONICAL_MTIME, 'mtime'))
    put(header, 'typeflag', b'0')
    put(header, 'magic', b'ustar\0')
    put(header, 'version', b'00')
    put(header, 'uname', CANONICAL_OWNER[0])
    put(header, 'gname', CANONICAL_OWNER[1])
    put(header, 'devmajor', small(0, 'devmajor'))
    put(header, 'devminor', small(0, 'devminor'))
    put(header, 'chksum', ('%06o' % checksum(header)).encode() + b'\0 ')


def walk(data, transform=None):
    """Canonicalise members and terminate the archive with exactly two zero blocks.

    The tail after the final member is producer-dependent: bsdtar writes the two POSIX
    end-of-archive blocks, GNU tar writes those plus padding to its 10 KiB record boundary
    (run #41627234610 showed 1 024 bytes locally versus 3 584 on the runner). Everything
    after the last member must be zero, and the canonical archive keeps exactly two blocks,
    so the result no longer depends on which tar produced the input.
    """
    out = bytearray()
    position = 0
    members = 0
    while position + BLOCK <= len(data):
        header = bytearray(data[position:position + BLOCK])
        if header == bytearray(BLOCK):
            break
        size, mode, name = parse(header)
        pad = -size % BLOCK
        body = data[position + BLOCK:position + BLOCK + size]
        if len(body) != size:
            raise SystemExit('normalize-bundle-tar: truncated member %r' % name)
        padding = data[position + BLOCK + size:position + BLOCK + size + pad]
        if len(padding) != pad:
            raise SystemExit('normalize-bundle-tar: truncated padding after %r' % name)
        if transform:
            rewrite(header, mode, size)
        out += header + body + padding
        position += BLOCK + size + pad
        members += 1

    tail = data[position:]
    if len(tail) < 2 * BLOCK:
        raise SystemExit('normalize-bundle-tar: missing end-of-archive marker after %d '
                         'member(s) (%d trailing byte(s))' % (members, len(tail)))
    excess = tail.strip(b'\0')
    if excess:
        raise SystemExit('normalize-bundle-tar: nonzero data after the final member '
                         '(%d byte(s); only zero padding may follow the last member)'
                         % len(excess))
    out += b'\0' * (2 * BLOCK)
    return bytes(out), members


def main(argv):
    if len(argv) == 3 and argv[1] == '--check':
        with open(argv[2], 'rb') as handle:
            _, members = walk(handle.read())
        print('TAR_FORMAT=canonical-ustar members=%d' % members)
        return 0
    if len(argv) == 3:
        with open(argv[1], 'rb') as handle:
            data, members = walk(handle.read(), transform=True)
        with open(argv[2], 'wb') as handle:
            handle.write(data)
        print('TAR_CANONICALISED members=%d bytes=%d' % (members, len(data)))
        return 0
    print('usage: normalize-bundle-tar.py IN.tar OUT.tar | --check IN.tar', file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv))
