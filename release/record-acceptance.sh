#!/bin/sh
# Record one host's acceptance for one exact candidate archive.
#
#   record-acceptance.sh ARCHIVE IDENTITY --source SHA --host .23|.252|.253 RESULT
#
# The record is created only after the calling verification has passed. It contains the source,
# archive hash, host and the previous host's hash, so the promotion gate cannot reuse a record
# from another candidate or another stage.
set -eu
LC_ALL=C
export LC_ALL
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)
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
        *) [ -z "$RESULT" ] && RESULT=$1 || { echo 'ABORT: too many arguments' >&2; exit 2; }; shift ;;
    esac
done
[ -n "$SOURCE" ] && [ -n "$HOST" ] && [ -n "$RESULT" ] || { echo 'usage: record-acceptance.sh ARCHIVE IDENTITY --source SHA --host STAGE RESULT' >&2; exit 2; }
case "$HOST" in .23|.252|.253) : ;; *) echo 'ABORT: host must be .23, .252 or .253' >&2; exit 2 ;; esac
[ "$RESULT" = PASS ] || { echo 'ABORT: acceptance result must be PASS' >&2; exit 1; }
DIGEST=$(sed -n 's/^sha256=//p' "$IDENTITY" | tail -1)
[ -n "$DIGEST" ] && [ "$(sha256 -q "$ARCHIVE")" = "$DIGEST" ] || { echo 'ABORT: archive/identity mismatch' >&2; exit 1; }
[ "$(sed -n 's/^source=//p' "$IDENTITY" | tail -1)" = "$SOURCE" ] || { echo 'ABORT: identity source mismatch' >&2; exit 1; }
cd "$REPO"
case "$HOST" in
    .252) [ -f "release/acceptance/.23-$DIGEST.passed" ] || { echo 'ABORT: .23 acceptance missing' >&2; exit 1; } ;;
    .253) [ -f "release/acceptance/.252-$DIGEST.passed" ] || { echo 'ABORT: .252 acceptance missing' >&2; exit 1; } ;;
esac
mkdir -p release/acceptance
umask 077
{
    printf 'version=%s\nsource=%s\nbundle_sha256=%s\nhost=%s\nresult=%s\n' \
        "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json)" \
        "$SOURCE" "$DIGEST" "$HOST" "$RESULT"
    [ "$HOST" = .252 ] && printf 'after=.23\n'
    [ "$HOST" = .253 ] && printf 'after=.252\n'
    printf 'accepted_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "release/acceptance/$HOST-$DIGEST.passed"
printf 'ACCEPTANCE_RECORDED=%s-%s\n' "$HOST" "$DIGEST"
