#!/bin/sh
# Verify a release candidate's identity before it may be bundled or promoted.
#
#   verify-candidate.sh [--ancestor REF] [--min-features PATH[:N] ...]
#
# Two checks, both enforceable without a network:
#
# 1. Ancestry. The candidate tree must descend from the intended integration ref
#    (default: the local main), so a branch cut from a stale main cannot become a
#    release candidate by accident. The failure that motivated this script was a
#    candidate built five commits behind main whose manifest silently lost the
#    Email Log files.
#
# 2. Feature presence. Each --min-features "PATH" argument must exist in the
#    versioned runtime manifest, with at least the given count (default 1). The
#    manifest is the installer's allow-list, so a feature missing from it is a
#    feature the payload does not ship.
#
# Usage from the bundler and from CI is the same. Prints CANDIDATE_OK=... or
# ABORT lines on stderr and exits 1.
set -eu
LC_ALL=C
export LC_ALL

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)
cd "$REPO"

ANCESTOR=main
FEATURES=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --ancestor) [ "$#" -ge 2 ] || { echo 'ABORT: --ancestor needs a ref' >&2; exit 2; }; ANCESTOR=$2; shift 2;;
        --min-features) [ "$#" -ge 2 ] || { echo 'ABORT: --min-features needs a path' >&2; exit 2; }; FEATURES="$FEATURES $2"; shift 2;;
        *) echo "ABORT: unknown argument $1" >&2; exit 2;;
    esac
done

if ! git rev-parse --verify --quiet "$ANCESTOR^{commit}" >/dev/null; then
    echo "ABORT: ancestor ref $ANCESTOR not found" >&2
    exit 1
fi
if ! git merge-base --is-ancestor "$ANCESTOR^{commit}" HEAD; then
    BEHIND=$(git rev-list --count "HEAD..$ANCESTOR" 2>/dev/null || echo '?')
    echo "ABORT: candidate is not based on $ANCESTOR (behind by $BEHIND commits)" >&2
    exit 1
fi

VERSION=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' \
    src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json)
MANIFEST=release/v${VERSION}-runtime.manifest
[ -f "$MANIFEST" ] || { echo "ABORT: manifest $MANIFEST missing" >&2; exit 1; }

# Removal guard. The manifest is append-oriented; replacing a row can legitimately be a
# feature change, but silently losing a row is exactly how the stale v2.15.0 candidate
# dropped every Email Log file. A baseline for each released line is kept under
# release/manifests/, and every baseline target must remain. Older baselines are retained so a
# later version cannot quietly drop a previously shipped file.
for baseline in release/manifests/*-runtime.manifest; do
    [ -f "$baseline" ] || continue
    unstable=0
    while read -r hash mode source target; do
        [ -n "$source" ] || { unstable=1; continue; }
        if ! awk -v s="$source" '$3 == s { found = 1 } END { exit !found }' "$MANIFEST"; then
            echo "ABORT: manifest lost a baseline target from ${baseline##*/}: $source" >&2
            unstable=1
        fi
    done < "$baseline"
    [ "$unstable" = 0 ] || exit 1
done

for spec in $FEATURES; do
    path=${spec%%:*}
    minimum=${spec##*:}
    [ "$minimum" = "$spec" ] && minimum=1
    if [ "$(awk -v p="$path" '$3 ~ p {n++} END {print n+0}' "$MANIFEST")" -lt "$minimum" ]; then
        echo "ABORT: $MANIFEST lacks $minimum manifest row(s) matching $path" >&2
        exit 1
    fi
done

echo "CANDIDATE_OK=version=$VERSION ancestor=$(git rev-parse --short "$ANCESTOR^{commit}") features=$(echo $FEATURES | wc -w | tr -d ' ')"
