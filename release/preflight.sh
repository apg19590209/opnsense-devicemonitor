#!/bin/sh
# Run the local checks that have caught release-candidate failures before a push. This is a
# compact aggregator of existing suites; it does not replace or weaken any of them.
#
#   release/preflight.sh
#
# It checks the candidate/archive contract, the installer's pins, the deployment/acceptance
# controls, the Email Log delivery fixture and bundle reproducibility, and finally builds the
# archive from an export of the current committed tree.
set -eu
LC_ALL=C
export LC_ALL
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)
cd "$REPO"
TMP=$(mktemp -d /tmp/dm-preflight.XXXXXX)
trap 'rm -rf "$TMP"' EXIT

run() {
    name=$1
    shift
    printf 'PREFLIGHT %s ...\n' "$name"
    if "$@"; then
        printf 'PREFLIGHT_%s=PASS\n' "$name"
    else
        printf 'PREFLIGHT_%s=FAIL\n' "$name" >&2
        exit 1
    fi
}

php tests/test_email_log_delivery_tracking.php >"$TMP/email.log" || {
    tail -20 "$TMP/email.log" >&2
    printf 'PREFLIGHT_email_delivery=FAIL\n' >&2
    exit 1
}
printf 'PREFLIGHT_email_delivery=PASS\n'
run release_safeguards python3 tests/test_release_safeguards.py
run deployment_safeguards python3 tests/test_deployment_safeguards.py
run execution_ledger python3 tests/test_execution_ledger.py
run release_inputs python3 tests/test_release_inputs.py
run bundle_safety python3 tests/test_bundle_build_safety.py
run bundle_reproducibility python3 tests/test_bundle_reproducibility.py
run bundle_determinism python3 tests/test_bundle_determinism.py
# Build from a clean export of the committed tree. This exercises the same source metadata and
# export path the release archive uses, so a missing packaged input is found before pushing.
WORK=$(mktemp -d /tmp/dm-preflight-build.XXXXXX)
trap 'rm -rf "$WORK"' EXIT
git archive --format=tar HEAD | tar -x -C "$WORK"
(cd "$WORK" && DM_SOURCE_EXPORT=1 DM_CANDIDATE_SOURCE=$(git -C "$REPO" rev-parse HEAD) \
    DM_BUNDLE_STAGE="$WORK/stage" DM_BUNDLE_OUT="$WORK/bundle.tar.gz" \
    DM_BUNDLE_LIST="$WORK/list.txt" sh release/build-bundle.sh >"$WORK/build.log" 2>&1) || {
    tail -20 "$WORK/build.log" >&2
    printf 'PREFLIGHT_export_build=FAIL\n' >&2
    exit 1
}
printf 'PREFLIGHT_export_build=PASS\n'
printf 'PREFLIGHT=PASS\n'
