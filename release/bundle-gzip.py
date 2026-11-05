#!/usr/bin/env python3
"""Deterministic gzip writer for the Device Monitor bundle (Decision 68).

The bundle identity must not depend on the host compressor. Run #41627234610 proved it did:
for the same 1 658 880-byte canonical tar, FreeBSD's BSD gzip produced 348 939 bytes while the
GitHub runner's GNU gzip produced 349 052 — different deflate implementations, different bytes.
Pinning zlib parameters would move the same problem to the zlib *version* on each platform.

So the bundle is compressed here, in Python, with a controlled deflate stream:

  * every block is a stored (BTYPE=00) block, which is pure framing — no algorithm version to
    drift, no tuning parameter to disagree about;
  * the gzip header is fixed: ID1/ID2 `\\x1f\\x8b`, CM=8, FLG=0, MTIME=0, XFL=0, OS=255
    (unknown), so there is no timestamp, no filename and no OS byte to vary;
  * the CRC-32 comes from `binascii` and the ISIZE from the input length, both fixed by
    RFC 1952;
  * the stream is verified by inflating it again before it is written, and any failure exits
    non-zero and deletes the output.

Cost: the archive is no longer compressed (≈1.66 MB instead of ≈349 KB). That is a deliberate
trade — determinism and a version-free implementation over payload size. Standard gzip and
`tar -xzf` read stored blocks, so installers are unaffected.

    bundle-gzip.py IN OUT
"""
import binascii
import hashlib
import sys
import zlib

HEADER = b'\x1f\x8b\x08\x00' + b'\x00\x00\x00\x00' + b'\x00\xff'
MAX_STORED = 65535


def store_blocks(data):
    """Wrap data in a stored-block gzip member. Output depends only on the input bytes."""
    out = bytearray(HEADER)
    if not data:
        out += b'\x01\x00\x00\xff\xff'
    else:
        position = 0
        while position < len(data):
            chunk = data[position:position + MAX_STORED]
            position += len(chunk)
            final = 1 if position >= len(data) else 0
            out.append(final)                      # BFINAL + BTYPE 00, byte-aligned start
            out += len(chunk).to_bytes(2, 'little')
            out += (len(chunk) ^ 0xFFFF).to_bytes(2, 'little')
            out += chunk
    out += binascii.crc32(data).to_bytes(4, 'little')
    out += (len(data) & 0xFFFFFFFF).to_bytes(4, 'little')
    return bytes(out)


def main(argv):
    if len(argv) != 3:
        print('usage: bundle-gzip.py IN OUT', file=sys.stderr)
        return 2
    source, target = argv[1], argv[2]
    with open(source, 'rb') as handle:
        data = handle.read()
    compressed = store_blocks(data)
    try:
        restored = zlib.decompress(compressed, 16 + zlib.MAX_WBITS)
    except zlib.error as error:
        print('GZIP_INFLATE_FAILED=%s' % error, file=sys.stderr)
        return 1
    if restored != data:
        print('GZIP_ROUNDTRIP_MISMATCH=restored:%d expected:%d'
              % (len(restored), len(data)), file=sys.stderr)
        return 1
    with open(target, 'wb') as handle:
        handle.write(compressed)
    print('gzip deterministic: stored blocks, mtime 0, os 255')
    print('GZIP_OK bytes=%d sha256=%s' % (len(compressed), hashlib.sha256(compressed).hexdigest()))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
