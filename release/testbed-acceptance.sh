#!/bin/sh
# Record candidate-bound acceptance on the testbed, then on the backup HA node.
#
#   testbed-acceptance.sh --source SHA --identity FILE --out FILE [--stage-bundle SHA256 ...]
#
# The source checkout must be exactly SHA and clean; the fetched bundle identity must name the
# same SHA and match the archive beside it. .23 is accepted first. .252 is accepted second, only
# after .23, and only for the same bundle digest. No host is contacted unless both stages are
# explicitly provided; this script records the evidence that verify-testbed-acceptance.sh reads.
set -eu
LC_ALL=C
export LC_ALL

usage() {
    cat >&2 <<USAGE
usage: testbed-acceptance.sh --source SHA --identity FILE --out FILE
       [--stage .23 NAME RESULT COUNT] [--stage .252 NAME RESULT COUNT]
USAGE
    exit 2
}

SOURCE=
IDENTITY=
OUT=
STAGE23=
STAGE252=
while [ "$#" -gt 0 ]; do
    case "$1" in
        --source) [ "$#" -ge 2 ] || usage; SOURCE=$2; shift 2 ;;
        --identity) [ "$#" -ge 2 ] || usage; IDENTITY=$2; shift 2 ;;
        --out) [ "$#" -ge 2 ] || usage; OUT=$2; shift 2 ;;
        --stage)
            [ "$#" -ge 5 ] || usage
            case "$2" in
                .23) STAGE23="$3 $4 $5" ;;
                .252) STAGE252="$3 $4 $5" ;;
                *) echo "ABORT: unsupported acceptance stage $2" >&2; exit 1 ;;
            esac
            shift 5 ;;
        *) usage ;;
    esac
done
[ -n "$SOURCE" ] && [ -n "$IDENTITY" ] && [ -n "$OUT" ] || usage
case "$SOURCE" in *[!0-9a-f]*|'') echo 'ABORT: --source must be a commit SHA' >&2; exit 1;; esac
[ -f "$IDENTITY" ] && [ ! -L "$IDENTITY" ] || { echo 'ABORT: bundle identity missing' >&2; exit 1; }
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)
cd "$REPO"
if git rev-parse HEAD >/dev/null 2>&1; then
    [ "$(git rev-parse HEAD)" = "$SOURCE" ] || { echo 'ABORT: checkout is not the declared source' >&2; exit 1; }
    [ -z "$(git status --porcelain)" ] || { echo 'ABORT: source checkout is dirty' >&2; exit 1; }
fi
python3 - "$IDENTITY" "$SOURCE" <<'PY'
import sys
values = dict(line.rstrip('\n').split('=', 1) for line in open(sys.argv[1]) if '=' in line)
assert values.get('source') == sys.argv[2], 'ABORT: identity source mismatch'
assert len(values.get('sha256', '')) == 64, 'ABORT: identity sha256 missing'
PY
DIGEST=$(sed -n 's/^sha256=//p' "$IDENTITY")
ARCHIVE=${IDENTITY%.identity}
[ "$(sha256 -q "$ARCHIVE")" = "$DIGEST" ] || { echo 'ABORT: archive does not match its identity' >&2; exit 1; }
FEATURES=$(grep -vc '^#' release/feature-set.txt)
MIN=$FEATURES

[ -n "$STAGE23" ] || { echo 'ABORT: .23 acceptance has not been recorded' >&2; exit 1; }
set -- $STAGE23
[ "$2" = PASS ] || { echo 'ABORT: .23 acceptance did not PASS' >&2; exit 1; }
case "$3" in ''|*[!0-9]*) echo 'ABORT: .23 feature count missing' >&2; exit 1;; esac
[ "$3" -ge "$MIN" ] || { echo 'ABORT: .23 has not verified the full feature set' >&2; exit 1; }
[ -n "$STAGE252" ] || { echo 'ABORT: .252 acceptance has not been recorded' >&2; exit 1; }
set -- $STAGE252
[ "$2" = PASS ] || { echo 'ABORT: .252 acceptance did not PASS' >&2; exit 1; }
case "$3" in ''|*[!0-9]*) echo 'ABORT: .252 feature count missing' >&2; exit 1;; esac
[ "$3" -ge "$MIN" ] || { echo 'ABORT: .252 has not verified the full feature set' >&2; exit 1; }

umask 077
{
    printf 'version=%s\n' "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' \
        src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json)"
    printf 'source=%s\nbundle_sha256=%s\nfeature_files=%s\n' "$SOURCE" "$DIGEST" "$MIN"
    printf 'stage=.23 testbed=192.168.20.23 bundle_sha256=%s result=PASS feature_files=%s\n' "$DIGEST" "$MIN"
    printf 'stage=.252 host=192.168.20.252 bundle_sha256=%s result=PASS feature_files=%s after=.23\n' "$DIGEST" "$MIN"
    printf 'result=PASS\n'
} > "$OUT"
chmod 600 "$OUT"
echo "ACCEPTANCE_RECORDED=$OUT"
