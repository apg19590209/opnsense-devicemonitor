#!/bin/sh
# Build dm-v2.11-runtime.tar.gz from an explicit allow-list.
#
# The bundle is NOT just the manifest: install-unattended.sh:97-123 compiles all 11
# locale .po files (hardcoded list, unconditional ABORT on a missing one) and the
# non-en_US branches invoke release/merge-opnsense-catalog.sh. A glob of src/ would
# additionally ship stale __pycache__/*.pyc, so the set is built explicitly.
set -eu

# Repo root is the parent of this script's own directory (release/), so the bundler is
# location-independent instead of hardcoding one developer's absolute checkout path.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)
BUILD=/tmp/dm-bundle-stage
OUT=/tmp/dm-v2.11-runtime.tar.gz
LIST=/tmp/dm-bundle-list.txt

cd "$REPO"

# 1. Manifest payload: the 38 hash-verified install targets.
awk '{print $3}' release/v2.11-runtime.manifest > "$LIST"

# 2. The .po catalogues the installer compiles (includes the 9 the manifest omits).
find src -name '*.po' >> "$LIST"

# 3. Installer scripts, the manifest itself, the catalogue merge helper, and the
#    uninstaller that install-unattended.sh advertises for restoring pristine files.
printf '%s\n' \
    install.sh \
    uninstall.sh \
    install-unattended.sh \
    release/v2.11-runtime.manifest \
    release/merge-opnsense-catalog.sh >> "$LIST"

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
( cd "$BUILD" && tar -czf "$OUT" -T "$LIST" )
echo "archive bytes     : $(wc -c < "$OUT" | tr -d ' ')"
sha256 "$OUT"
