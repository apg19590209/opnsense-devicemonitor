#!/bin/sh
# Verify every pinned install input before the installer runs any of it (Decision 62).
#
#   verify-release-inputs.sh [ROOT]
#
# ROOT is the unpacked bundle (default: the parent of this script's directory). Every row
# of release/release-inputs.sha256 is a digest the release owner signed off on: the
# runtime manifest, the prune helper, the legacy ownership evidence and the catalogue
# merge helper. A missing, symlinked or modified input fails the whole run, so a tampered
# prune helper can never decide which files get deleted.
set -eu
LC_ALL=C
export LC_ALL

PROG=verify-release-inputs.sh

die() {
    echo "VERIFY_FAILED=$*" >&2
    exit 1
}

digest() {
    if [ -n "${DM_SHA256:-}" ]; then
        $DM_SHA256 "$1"
    elif command -v sha256 >/dev/null 2>&1; then
        sha256 -q "$1"
    elif command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    else
        die 'no sha256 implementation available'
    fi
}

if [ "$#" -gt 1 ]; then
    echo "usage: $PROG [ROOT]" >&2
    exit 2
fi

ROOT=${1:-}
[ -n "$ROOT" ] || ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
[ -d "$ROOT" ] || die "$ROOT (not a directory)"

LIST=$ROOT/release/release-inputs.sha256
[ -f "$LIST" ] || die "release/release-inputs.sha256 (missing)"
[ ! -L "$LIST" ] || die "release/release-inputs.sha256 (symlink)"

n=0
rc=0
while read -r hash path; do
    case "$hash" in
        ''|'#'*) continue ;;
    esac
    [ -n "$path" ] || continue
    case "$path" in
        /*|*..*) echo "VERIFY_FAILED=$path (unsafe path)" >&2; rc=1; continue ;;
    esac
    file=$ROOT/$path
    if [ -L "$file" ] || [ ! -f "$file" ]; then
        echo "VERIFY_FAILED=$path (missing or not a regular file)" >&2
        rc=1
        continue
    fi
    if [ "$(digest "$file")" = "$hash" ]; then
        n=$((n + 1))
    else
        echo "VERIFY_FAILED=$path (digest)" >&2
        rc=1
    fi
done < "$LIST"

[ "$rc" -eq 0 ] || exit 1
printf 'VERIFY_OK=%s\n' "$n"
