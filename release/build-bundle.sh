#!/bin/sh
# Build dm-v<VERSION>-runtime.tar.gz from an explicit allow-list.
#
# The bundle is NOT just the manifest: install-unattended.sh compiles all 11 locale .po
# files (hardcoded list, unconditional ABORT on a missing one) and the non-en_US branches
# invoke release/merge-opnsense-catalog.sh. It also executes release/prune-plan.sh and
# reads release/legacy-targets.txt, and verifies both against release/release-inputs.sha256
# through release/verify-release-inputs.sh. A glob of src/ would additionally ship stale
# __pycache__/*.pyc, so the set is built explicitly.
set -eu
LC_ALL=C
export LC_ALL

# Repo root is the parent of this script's own directory (release/), so the bundler is
# location-independent instead of hardcoding one developer's absolute checkout path.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)
VERSION=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' \
    "$REPO/src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json")
MANIFEST=release/v${VERSION}-runtime.manifest

digest() {
    if [ -n "${DM_SHA256:-}" ]; then
        $DM_SHA256 "$1"
    elif command -v sha256 >/dev/null 2>&1; then
        sha256 -q "$1"
    else
        sha256sum "$1" | awk '{print $1}'
    fi
}

BUILD=${DM_BUNDLE_STAGE:-/tmp/dm-bundle-stage}
OUT=${DM_BUNDLE_OUT:-/tmp/dm-v${VERSION}-runtime.tar.gz}
LIST=${DM_BUNDLE_LIST:-/tmp/dm-bundle-list.txt}

cd "$REPO"

# 1. Manifest payload: the 40 hash-verified install targets.
awk '{print $3}' "$MANIFEST" > "$LIST"

# 2. The .po catalogues the installer compiles (includes the 9 the manifest omits).
find src -name '*.po' >> "$LIST"

# 3. Installer scripts, the manifest itself, the pinned-inputs file and its verifier, the
#    catalogue merge helper, the prune helper with its legacy ownership evidence, and the
#    uninstaller that install-unattended.sh advertises for restoring pristine files.
printf '%s\n' \
    install.sh \
    uninstall.sh \
    install-unattended.sh \
    "$MANIFEST" \
    release/release-inputs.sha256 \
    release/verify-release-inputs.sh \
    release/merge-opnsense-catalog.sh \
    release/prune-plan.sh \
    release/legacy-targets.txt >> "$LIST"

sort -u "$LIST" -o "$LIST"
echo "allow-list entries: $(wc -l < "$LIST" | tr -d ' ')"

rm -rf "$BUILD"
mkdir -p "$BUILD"
while IFS= read -r f; do
    if [ ! -f "$f" ]; then
        echo "MISSING SOURCE: $f" >&2
        exit 1
    fi
    mkdir -p "$BUILD/$(dirname "$f")"
    cp -p "$f" "$BUILD/$f"
done < "$LIST"

echo "staged files      : $(find "$BUILD" -type f | wc -l | tr -d ' ')"
echo "staged .pyc       : $(find "$BUILD" -name '*.pyc' | wc -l | tr -d ' ') (must be 0)"
echo "staged __pycache__: $(find "$BUILD" -type d -name '__pycache__' | wc -l | tr -d ' ') (must be 0)"

rm -f "$OUT"
# Determinism (Decision 63): the published digest is an artifact identity, so identical
# inputs must give identical bytes from any checkout. Four things are normalised —
#   * member mtimes, which `cp -p` would otherwise inherit from the working copy (and a
#     fresh clone has different ones);
#   * uid/gid and their symbolic names, which depend on who built the archive;
#   * the member-order source, which is the sorted allow-list, never a directory scan;
#   * the archive format, pinned to ustar so no pax extended header (with sub-second
#     mtimes or path hints) can leak in.
# gzip -n removes the timestamp gzip would otherwise write into its header. File modes are
# NOT normalised: the executable bits recorded in git must survive.
find "$BUILD" -exec touch -h -t 202601010000.00 {} +
( cd "$BUILD" && tar --format ustar -cf - \
        --uid 0 --gid 0 --uname root --gname wheel \
        -T "$LIST" | gzip -n > "$OUT" )
echo "archive bytes     : $(wc -c < "$OUT" | tr -d ' ')"
printf 'bundle sha256: %s\n' "$(digest "$OUT")"
