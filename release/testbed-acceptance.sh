#!/bin/sh
# Record one verified host's acceptance for an exact candidate archive.
#
#   testbed-acceptance.sh --source SHA --identity FILE --host .23|.252|.253
#
# This replaces earlier whole-pipeline evidence generation. The caller must have completed the
# host's functional checks first; this script records only the identity and the host stage, with
# .252 requiring .23 and .253 requiring .252 for the same bundle.
set -eu
LC_ALL=C
export LC_ALL
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)
SOURCE=
IDENTITY=
HOST=
while [ "$#" -gt 0 ]; do
    case "$1" in
        --source) [ "$#" -ge 2 ] || exit 2; SOURCE=$2; shift 2 ;;
        --identity) [ "$#" -ge 2 ] || exit 2; IDENTITY=$2; shift 2 ;;
        --host) [ "$#" -ge 2 ] || exit 2; HOST=$2; shift 2 ;;
        *) echo "ABORT: unknown argument $1" >&2; exit 2 ;;
    esac
done
[ -n "$SOURCE" ] && [ -n "$IDENTITY" ] && [ -n "$HOST" ] || { echo 'usage: testbed-acceptance.sh --source SHA --identity FILE --host STAGE' >&2; exit 2; }
[ -f "$IDENTITY" ] && [ ! -L "$IDENTITY" ] || { echo 'ABORT: identity missing' >&2; exit 1; }
ARCHIVE=${IDENTITY%.identity}
[ -f "$ARCHIVE" ] || { echo 'ABORT: archive missing beside identity' >&2; exit 1; }
exec /bin/sh "$REPO/release/record-acceptance.sh" "$ARCHIVE" "$IDENTITY" --source "$SOURCE" --host "$HOST" PASS
