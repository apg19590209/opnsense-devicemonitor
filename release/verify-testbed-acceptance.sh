#!/bin/sh
# Refuse promotion unless this exact candidate hash passed .23, then .252, in that order.
#
#   verify-testbed-acceptance.sh EVIDENCE_FILE
#
# Evidence is the output of release/testbed-acceptance.sh. It names the bundle identity as it
# was fetched and verified, not just a version: version, source SHA and bundle SHA-256 must all
# match release/bundle-digest.txt, and every stage must carry its own bundle digest. A marker
# left by an older candidate cannot authorise a different archive.
#
#   version=2.15.0
#   source=<40 hex>
#   bundle_sha256=<64 hex>
#   feature_files=<n>
#   stage=.23 testbed=192.168.20.23 bundle_sha256=<64 hex> result=PASS feature_files=<n>
#   stage=.252 host=192.168.20.252 bundle_sha256=<64 hex> result=PASS feature_files=<n> after=.23
#   result=PASS
#
# .252 is required before the evidence can pass; .253 is never a substitute for either stage.
# The script deliberately does not contact a host.
set -eu
LC_ALL=C
export LC_ALL

[ "$#" -eq 1 ] || { echo 'usage: verify-testbed-acceptance.sh EVIDENCE_FILE' >&2; exit 2; }
EVIDENCE=$1
[ -f "$EVIDENCE" ] && [ ! -L "$EVIDENCE" ] || { echo "ABORT: evidence file missing: $EVIDENCE" >&2; exit 1; }

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)
cd "$REPO"

scalar() { sed -n "s/^$1=//p" "$EVIDENCE" | tail -1; }
stage_value() {
    # stage_value .23 key
    awk -v want="$1" -v key="$2" '
        $1 == "stage=" want {
            for (i = 2; i <= NF; i++) {
                split($i, kv, "=")
                if (kv[1] == key) { print kv[2]; exit }
            }
        }' "$EVIDENCE"
}

VERSION=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' \
    src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json)
RECORDED=$(sed -n 's/^sha256 \([0-9a-f]\{64\}\)$/\1/p' release/bundle-digest.txt | tail -1)
# A released checkout is a Git worktree. The direct digest comparison below is what binds
# the evidence to the exact candidate bytes; the source SHA is checked only when the caller
# carries a worktree, and is optional for a sealed release mirror.
RECORDED_SOURCE=
if git rev-parse HEAD >/dev/null 2>&1; then
    RECORDED_SOURCE=$(git rev-parse HEAD)
fi
[ -n "$RECORDED" ] || { echo 'ABORT: bundle digest not recorded' >&2; exit 1; }

RESULT=$(scalar result)
VERSION_IN=$(scalar version)
SHA_IN=$(scalar bundle_sha256)
SOURCE_IN=$(scalar source)
FEATURES=$(scalar feature_files)
MARKER_DIR=${DM_ACCEPTANCE_MARKER_DIR:-release/acceptance}
MARKER=$MARKER_DIR/v${VERSION}.accepted
MIN=$(grep -vc '^#' release/feature-set.txt 2>/dev/null || echo 0)

[ "$RESULT" = 'PASS' ] || { echo "ABORT: testbed acceptance result is '${RESULT:-missing}', not PASS" >&2; exit 1; }
[ "$VERSION_IN" = "$VERSION" ] || { echo "ABORT: evidence is for '${VERSION_IN:-nothing}', candidate is $VERSION" >&2; exit 1; }
if [ -n "$RECORDED_SOURCE" ]; then
    [ "$SOURCE_IN" = "$RECORDED_SOURCE" ] || { echo "ABORT: evidence source does not match this candidate" >&2; exit 1; }
fi
[ "$SHA_IN" = "$RECORDED" ] || { echo 'ABORT: acceptance digest does not match the recorded bundle' >&2; exit 1; }
case "$FEATURES" in ''|*[!0-9]*) echo 'ABORT: feature_files count missing' >&2; exit 1;; esac
[ "$FEATURES" -ge "$MIN" ] || { echo "ABORT: only $FEATURES feature file(s) verified, need $MIN" >&2; exit 1; }

for stage in .23 .252; do
    host=$(stage_value "$stage" testbed)
    [ -n "$host" ] || host=$(stage_value "$stage" host)
    result=$(stage_value "$stage" result)
    digest=$(stage_value "$stage" bundle_sha256)
    count=$(stage_value "$stage" feature_files)
    [ -n "$host" ] || { echo "ABORT: acceptance stage $stage has no host" >&2; exit 1; }
    [ "$result" = PASS ] || { echo "ABORT: acceptance stage $stage did not PASS" >&2; exit 1; }
    [ "$digest" = "$RECORDED" ] || { echo "ABORT: acceptance stage $stage is for a different candidate" >&2; exit 1; }
    case "$count" in ''|*[!0-9]*) echo "ABORT: acceptance stage $stage has no feature count" >&2; exit 1;; esac
    [ "$count" -ge "$MIN" ] || { echo "ABORT: acceptance stage $stage verified only $count feature file(s)" >&2; exit 1; }
done
[ "$(stage_value .23 testbed)" = 192.168.20.23 ] || [ "$(stage_value .23 host)" = 192.168.20.23 ] ||
    { echo 'ABORT: .23 acceptance must name the testbed host' >&2; exit 1; }
[ "$(stage_value .252 host)" = 192.168.20.252 ] || { echo 'ABORT: .252 acceptance must name 192.168.20.252' >&2; exit 1; }
[ "$(stage_value .252 after)" = .23 ] || { echo 'ABORT: .252 acceptance must follow .23' >&2; exit 1; }

mkdir -p "$MARKER_DIR"
{
    printf 'version=%s\nsource=%s\nbundle_sha256=%s\nfeature_files=%s\n' \
        "$VERSION" "$RECORDED_SOURCE" "$RECORDED" "$FEATURES"
    printf 'stage=.23 testbed=192.168.20.23 bundle_sha256=%s result=PASS feature_files=%s\n' "$RECORDED" "$FEATURES"
    printf 'stage=.252 host=192.168.20.252 bundle_sha256=%s result=PASS feature_files=%s after=.23\n' "$RECORDED" "$FEATURES"
    printf 'accepted_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$MARKER"
printf 'TESTBED_ACCEPTANCE_OK=version=%s source=%s sha256=%s marker=%s\n' "$VERSION" "$RECORDED_SOURCE" "$RECORDED" "$MARKER"
