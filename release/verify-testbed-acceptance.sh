#!/bin/sh
# Verify sequential promotion evidence for one exact candidate.
#
#   verify-testbed-acceptance.sh --source SHA --identity FILE --through .23|.252|.253
#
# The archive is hashed and the source is read from the identity; no evidence is accepted unless
# it names that same hash and source. The host records are produced by record-acceptance.sh
# after each host's functional checks have passed.
set -eu
LC_ALL=C
export LC_ALL
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)
SOURCE=
IDENTITY=
THROUGH=
while [ "$#" -gt 0 ]; do
    case "$1" in
        --source) [ "$#" -ge 2 ] || exit 2; SOURCE=$2; shift 2 ;;
        --identity) [ "$#" -ge 2 ] || exit 2; IDENTITY=$2; shift 2 ;;
        --through) [ "$#" -ge 2 ] || exit 2; THROUGH=$2; shift 2 ;;
        *) echo "ABORT: unknown argument $1" >&2; exit 2 ;;
    esac
done
[ -n "$SOURCE" ] && [ -n "$IDENTITY" ] && [ -n "$THROUGH" ] || { echo 'usage: --source SHA --identity FILE --through STAGE' >&2; exit 2; }
[ -f "$IDENTITY" ] && [ ! -L "$IDENTITY" ] || { echo 'ABORT: identity missing' >&2; exit 1; }
DIGEST=$(sed -n 's/^sha256=//p' "$IDENTITY" | tail -1)
IDENT_SOURCE=$(sed -n 's/^source=//p' "$IDENTITY" | tail -1)
[ "$DIGEST" = "$(sha256 -q "${IDENTITY%.identity}")" ] || { echo 'ABORT: archive/identity mismatch' >&2; exit 1; }
[ "$SOURCE" = "$IDENT_SOURCE" ] || { echo 'ABORT: identity source mismatch' >&2; exit 1; }
cd "$REPO"
case "$THROUGH" in
    .23) STAGES='.23' ;;
    .252) STAGES='.23 .252' ;;
    .253) STAGES='.23 .252 .253' ;;
    *) echo 'ABORT: --through must be .23, .252 or .253' >&2; exit 2 ;;
esac
for stage in $STAGES; do
    file="release/acceptance/$stage-$DIGEST.passed"
    [ -f "$file" ] || { echo "ABORT: acceptance stage $stage missing" >&2; exit 1; }
    [ "$(sed -n 's/^bundle_sha256=//p' "$file" | tail -1)" = "$DIGEST" ] || { echo "ABORT: stage $stage is another candidate" >&2; exit 1; }
    [ "$(sed -n 's/^source=//p' "$file" | tail -1)" = "$SOURCE" ] || { echo "ABORT: stage $stage source mismatch" >&2; exit 1; }
    [ "$(sed -n 's/^result=//p' "$file" | tail -1)" = PASS ] || { echo "ABORT: stage $stage did not PASS" >&2; exit 1; }
done
printf 'ACCEPTANCE_OK_%s source=%s sha256=%s\n' "$(printf %s "$THROUGH" | tr -d .)" "$SOURCE" "$DIGEST"
