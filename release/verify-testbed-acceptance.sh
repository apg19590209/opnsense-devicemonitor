#!/bin/sh
# Refuse promotion unless the candidate was accepted on the testbed.
#
#   verify-testbed-acceptance.sh EVIDENCE_FILE
#
# The evidence file is written by the testbed validation step (or by the operator
# running it) and must name the exact candidate bundle digest and version, the
# host it was accepted on, and the feature files that were verified present.
# Promotion -- creating a tag or attaching release assets -- must run this first.
#
# Format (one key=value per line, '#' comments allowed):
#   version=2.15.0
#   bundle_sha256=<64 hex>
#   testbed=192.168.20.23
#   feature_files=<n>        number of Email Log files verified present+hash-matched
#   result=PASS
#
# A result other than PASS, a missing file, a digest mismatch with
# release/bundle-digest.txt, or a different version is a hard stop.
set -eu
LC_ALL=C
export LC_ALL

[ "$#" -eq 1 ] || { echo 'usage: verify-testbed-acceptance.sh EVIDENCE_FILE' >&2; exit 2; }
EVIDENCE=$1
[ -f "$EVIDENCE" ] && [ ! -L "$EVIDENCE" ] || { echo "ABORT: evidence file missing: $EVIDENCE" >&2; exit 1; }

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)
cd "$REPO"

value() { sed -n "s/^$1=//p" "$EVIDENCE" | tail -1; }

VERSION=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' \
    src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json)
RESULT=$(value result)
VERSION_IN=$(value version)
SHA_IN=$(value bundle_sha256)
FEATURES=$(value feature_files)
MARKER_DIR=${DM_ACCEPTANCE_MARKER_DIR:-release/acceptance}
MARKER=$MARKER_DIR/v${VERSION}.accepted

[ "$RESULT" = 'PASS' ] || { echo "ABORT: testbed acceptance result is '${RESULT:-missing}', not PASS" >&2; exit 1; }
[ "$VERSION_IN" = "$VERSION" ] || { echo "ABORT: evidence is for '${VERSION_IN:-nothing}', candidate is $VERSION" >&2; exit 1; }
case "$FEATURES" in ''|*[!0-9]*) echo 'ABORT: feature_files count missing' >&2; exit 1;; esac
MIN=$(grep -vc '^#' release/feature-set.txt 2>/dev/null || echo 0)
[ "$FEATURES" -ge "$MIN" ] || { echo "ABORT: only $FEATURES feature file(s) verified, need $MIN" >&2; exit 1; }
RECORDED=$(sed -n 's/^sha256 \([0-9a-f]\{64\}\)$/\1/p' release/bundle-digest.txt | tail -1)
[ -n "$RECORDED" ] || { echo 'ABORT: bundle digest not recorded' >&2; exit 1; }
[ "$SHA_IN" = "$RECORDED" ] || { echo "ABORT: acceptance digest does not match the recorded bundle" >&2; exit 1; }

mkdir -p "$MARKER_DIR"
{
    echo "version=$VERSION"
    echo "bundle_sha256=$RECORDED"
    echo "testbed=$(value testbed)"
    echo "feature_files=$FEATURES"
    echo "accepted_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$MARKER"
echo "TESTBED_ACCEPTANCE_OK=version=$VERSION marker=$MARKER"
