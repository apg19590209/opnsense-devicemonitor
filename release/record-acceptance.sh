#!/bin/sh
# Generate a host acceptance marker only from complete execution-ledger records.
#
#   record-acceptance.sh ARCHIVE IDENTITY --source SHA --host .23|.252|.253 RESULT
#
# The only accepted RESULT is PASS; even then, release/execution-ledger.py accept refuses unless
# every required check has a PASS record for this exact candidate and actual host.
set -eu
LC_ALL=C
export LC_ALL
[ "$#" -ge 2 ] || { echo 'usage: record-acceptance.sh ARCHIVE IDENTITY --source SHA --host STAGE RESULT' >&2; exit 2; }
ARCHIVE=$1
IDENTITY=$2
shift 2
SOURCE=
HOST=
RESULT=
while [ "$#" -gt 0 ]; do
    case "$1" in
        --source) [ "$#" -ge 2 ] || exit 2; SOURCE=$2; shift 2 ;;
        --host) [ "$#" -ge 2 ] || exit 2; HOST=$2; shift 2 ;;
        *) RESULT=$1; shift ;;
    esac
done
[ -n "$SOURCE" ] && [ -n "$HOST" ] && [ "$RESULT" = PASS ] || { echo 'ABORT: --source, --host and PASS are required' >&2; exit 1; }
case "$HOST" in .23|.252|.253) : ;; *) echo 'ABORT: invalid stage' >&2; exit 1 ;; esac
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)
DIGEST=$(sed -n 's/^sha256=//p' "$IDENTITY" | tail -1)
python3 "$SCRIPT_DIR/execution-ledger.py" accept --ledger "$REPO/release/execution-ledger.jsonl" \
    --stage "$HOST" --host "$(case "$HOST" in .23) echo 192.168.20.23;; .252) echo 192.168.20.252;; .253) echo 192.168.20.253;; esac)" \
    --source "$SOURCE" --bundle "$DIGEST" --identity "$IDENTITY" \
    --out "$REPO/release/acceptance/$HOST-$DIGEST.passed"
