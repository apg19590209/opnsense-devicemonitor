#!/bin/sh
# Build a Device Monitor payload from a git ref and deploy it to the HA nodes.
#
# Usage (on the workstation that holds the checkout):
#
#   ./publish-devicemonitor.sh <ref>
#   NODES="LOCAL root@192.168.20.252" ./publish-devicemonitor.sh <ref>
#
# Environment:
#   REPO  checkout path           (default /usr/local/cline-freebsd/src/cline)
#   JUMP  host the nodes hang off (default opnsense-dm)
#   NODES space separated targets (default "LOCAL"); LOCAL means the jump host
#
# Every file is taken from git, never from a working tree, and the node
# refuses the deploy unless every staged file matches its manifest hash.
set -eu

REF=${1:-}
[ -n "$REF" ] || { echo "usage: $0 <ref>" >&2; exit 2; }

REPO=${REPO:-/usr/local/cline-freebsd/src/cline}
JUMP=${JUMP:-opnsense-dm}
NODES=${NODES:-LOCAL}

command -v git >/dev/null || { echo "git not found" >&2; exit 2; }

commit=$(git -C "$REPO" rev-parse --short "$REF") || exit 2

work=$(mktemp -d /tmp/dm-publish.XXXXXX)
trap 'rm -rf "$work"' EXIT INT TERM

echo "publish: building payload from $REF ($commit)"

files=$(git -C "$REPO" ls-tree -r --name-only "$REF" \
    | grep -E '^src/(opnsense|etc)/' \
    | grep -i 'devicemonitor' \
    | sort)

[ -n "$files" ] || { echo "no plugin files matched in $REF" >&2; exit 2; }

: > "$work/MANIFEST"

count=0
for f in $files; do
    rel=${f#src/}
    dest="$work/payload/usr/local/$rel"

    mkdir -p "$(dirname "$dest")"
    git -C "$REPO" cat-file blob "$REF:$f" > "$dest"

    printf '%s  /usr/local/%s\n' "$(md5 -q "$dest")" "$rel" >> "$work/MANIFEST"
    count=$((count + 1))
done

repo_url=$(git -C "$REPO" config --get remote.origin.url 2>/dev/null || echo unknown)
printf '%s %s %s %s\n' \
    "$REF" "$commit" "$repo_url" "$(date '+%Y-%m-%dT%H:%M:%S%z')" > "$work/SOURCE"

cp "$(dirname "$0")/deploy-devicemonitor.sh" "$work/deploy-devicemonitor.sh"

echo "publish: $count file(s); MANIFEST md5 $(md5 -q "$work/MANIFEST")"

tar -czf "$work/payload.tar.gz" -C "$work" payload MANIFEST SOURCE deploy-devicemonitor.sh

echo "publish: staging on $JUMP"
ssh -o BatchMode=yes "$JUMP" 'rm -rf /tmp/dm-stage && mkdir -p /tmp/dm-stage && cat > /tmp/dm-stage/payload.tar.gz' \
    < "$work/payload.tar.gz"

echo "publish: deploying to [$NODES]"
ssh -o BatchMode=yes "$JUMP" /bin/sh -s <<DRIVER
set -eu
STAGE=/tmp/dm-stage
NODES="$NODES"

cd "\$STAGE"
rm -rf payload MANIFEST SOURCE deploy-devicemonitor.sh
tar xzf payload.tar.gz

for node in \$NODES; do
    echo "=== \$node ==="

    if [ "\$node" = "LOCAL" ]; then
        /bin/sh "\$STAGE/deploy-devicemonitor.sh" "\$STAGE"
        continue
    fi

    ssh -o BatchMode=yes "\$node" 'mkdir -p /tmp/dm-stage && cat > /tmp/dm-stage/payload.tar.gz' \
        < "\$STAGE/payload.tar.gz"

    ssh -o BatchMode=yes "\$node" 'cd /tmp/dm-stage && rm -rf payload MANIFEST SOURCE deploy-devicemonitor.sh && tar xzf payload.tar.gz && /bin/sh deploy-devicemonitor.sh /tmp/dm-stage'
done
DRIVER

echo "publish: done"
