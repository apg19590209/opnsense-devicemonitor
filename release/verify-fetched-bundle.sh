#!/bin/sh
# Verify a bundle that was actually fetched, not one in the working tree.
#
#   verify-fetched-bundle.sh ARCHIVE --source SHA --identity FILE --list FILE
#
# The source must be a full commit SHA. The archive's declared identity must name that SHA, its
# member set must equal the list produced by build-bundle.sh, and the bytes of every member must
# match the files in the verified checkout. A mismatched SHA is a hard stop.
set -eu
LC_ALL=C
export LC_ALL

usage() {
    echo 'usage: verify-fetched-bundle.sh ARCHIVE --source SHA --identity FILE --list FILE' >&2
    exit 2
}
[ "$#" -ge 2 ] || usage
ARCHIVE=$1
shift
SOURCE=
IDENTITY=
LIST=
while [ "$#" -gt 0 ]; do
    case "$1" in
        --source) [ "$#" -ge 2 ] || usage; SOURCE=$2; shift 2;;
        --identity) [ "$#" -ge 2 ] || usage; IDENTITY=$2; shift 2;;
        --list) [ "$#" -ge 2 ] || usage; LIST=$2; shift 2;;
        *) usage;;
    esac
done
[ -n "$SOURCE" ] && [ -n "$IDENTITY" ] && [ -n "$LIST" ] || usage
case "$SOURCE" in *[!0-9a-f]*|'') echo 'ABORT: --source must be a lowercase commit SHA' >&2; exit 1;; esac
[ "${#SOURCE}" -eq 40 ] || { echo 'ABORT: --source must be a full 40-character commit SHA' >&2; exit 1; }
[ -f "$ARCHIVE" ] && [ ! -L "$ARCHIVE" ] || { echo "ABORT: archive missing: $ARCHIVE" >&2; exit 1; }

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
python3 "$SCRIPT_DIR/verify-bundle.py" --archive "$ARCHIVE" --list "$LIST" --identity "$IDENTITY" --source "$SOURCE"
