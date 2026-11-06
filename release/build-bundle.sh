#!/bin/sh
# Build dm-v<VERSION>-runtime.tar.gz from an explicit allow-list.
#
# The bundle is NOT just the manifest: install-unattended.sh compiles all 11 locale .po
# files (hardcoded list, unconditional ABORT on a missing one) and the non-en_US branches
# invoke release/merge-opnsense-catalog.sh. The installer also needs the core-locale rollback
# helper. A glob of src/ would additionally ship stale __pycache__/*.pyc, so the set is built
# explicitly.
set -eu
LC_ALL=C
TZ=UTC0
export LC_ALL TZ

# Repo root is the parent of this script's own directory (release/), so the bundler is
# location-independent instead of hardcoding one developer's absolute checkout path.
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)
VERSION=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' \
    "$REPO/src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json")
MANIFEST=release/v${VERSION}-runtime.manifest

digest() {
    if command -v sha256 >/dev/null 2>&1; then
        sha256 -q "$1"
    else
        sha256sum "$1" | awk '{print $1}'
    fi
}

BUILD=${DM_BUNDLE_STAGE:-/tmp/dm-bundle-stage}
OUT=${DM_BUNDLE_OUT:-/tmp/dm-v${VERSION}-runtime.tar.gz}
LIST=${DM_BUNDLE_LIST:-/tmp/dm-bundle-list.txt}

cd "$REPO"

# 1. Manifest payload: the hash-verified install targets.
awk '{print $3}' "$MANIFEST" > "$LIST"

# 2. The .po catalogues the installer compiles (includes the sidecars the manifest omits).
find src -name '*.po' >> "$LIST"

# 3. Installer scripts, the manifest itself, the catalogue merge helper, the core-locale
#    rollback helper, and the uninstaller that install-unattended.sh advertises.
printf '%s\n' \
    install.sh \
    uninstall.sh \
    install-unattended.sh \
    "$MANIFEST" \
    release/merge-opnsense-catalog.sh \
    release/core-locale-state.sh >> "$LIST"

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

# Determinism: archive modes come from the executable bit, not the checkout umask. Git tracks
# only that bit, so two otherwise identical checkouts must not publish 644/755 or 664/775
# depending on the user who built them.
while IFS= read -r f; do
    if [ -x "$BUILD/$f" ]; then
        chmod 755 "$BUILD/$f"
    else
        chmod 644 "$BUILD/$f"
    fi
done < "$LIST"

# Member mtimes are fixed before archiving and canonicalised again below.
find "$BUILD" -exec touch -h -t 202601010000.00 {} +

# Tar implementation detection. A producer that cannot be identified is refused rather than
# guessed at, because a different implementation can emit a different archive identity.
TAR=${DM_TAR:-tar}
tar_version=$("$TAR" --version 2>&1 | head -n 1 || true)
case $tar_version in
    *bsdtar*) TAR_FLAVOUR=bsdtar ;;
    *"GNU tar"*) TAR_FLAVOUR=gnu ;;
    *) TAR_FLAVOUR=unknown ;;
esac
echo "tar implementation: $TAR_FLAVOUR ($TAR - ${tar_version:-no --version output})"

# Unquoted expansion on purpose: these are flag lists with no embedded spaces.
case $TAR_FLAVOUR in
    bsdtar)
        TAR_OPTS="--format ustar --uid 0 --gid 0 --uname root --gname wheel"
        ;;
    gnu)
        TAR_OPTS="--format=ustar --owner=root:0 --group=wheel:0"
        ;;
    *)
        printf '%s\n' \
            "UNSUPPORTED_TAR=$TAR" \
            "  '$TAR --version' identified neither GNU tar nor bsdtar." \
            "  Refusing to build: a different implementation can produce a different" \
            "  archive identity. Point DM_TAR at a supported tar." >&2
        exit 1
        ;;
esac

# Functional probe: accept the flags and the canonical format, not just a version string.
PROBE=$(mktemp -d "${TMPDIR:-/tmp}/dm-tar-probe.XXXXXX")
mkdir -p "$PROBE/tree"
: > "$PROBE/tree/probe"
if ! ( cd "$PROBE/tree" && "$TAR" $TAR_OPTS -cf "$PROBE/probe.tar" probe ); then
    rm -rf "$PROBE"
    echo "TAR_PROBE_FAILED=$TAR (flags rejected: $TAR_OPTS)" >&2
    exit 1
fi
if ! python3 "$SCRIPT_DIR/normalize-bundle-tar.py" --check "$PROBE/probe.tar"; then
    rm -rf "$PROBE"
    echo "TAR_PROBE_UNSUPPORTED=$TAR (archive is not canonical ustar)" >&2
    exit 1
fi
rm -rf "$PROBE"

# Every construction stage writes an explicit file and its status is checked, so no pipeline
# can mask a failure and no partial archive is left behind.
TARBALL=$OUT.tar
CANONICAL=$OUT.tar.canonical
rm -f "$OUT" "$TARBALL" "$CANONICAL"
( cd "$BUILD" && "$TAR" $TAR_OPTS -cf "$TARBALL" -T "$LIST" ) || {
    echo "TAR_FAILED=$TAR (no archive produced)" >&2
    rm -f "$TARBALL"
    exit 1
}
if [ ! -s "$TARBALL" ]; then
    echo "TAR_EMPTY=$TARBALL (0 bytes)" >&2
    rm -f "$TARBALL"
    exit 1
fi
if ! canonical_out=$(python3 "$SCRIPT_DIR/normalize-bundle-tar.py" "$TARBALL" "$CANONICAL"); then
    echo "TAR_CANONICALISE_FAILED=$TARBALL" >&2
    rm -f "$TARBALL" "$CANONICAL"
    exit 1
fi
echo "$canonical_out"
members=$(printf '%s\n' "$canonical_out" | sed -n 's/.*members=\([0-9][0-9]*\).*/\1/p')
expected=$(wc -l < "$LIST" | tr -d ' ')
if [ "$members" != "$expected" ]; then
    echo "MEMBER_COUNT_MISMATCH=archived:$members expected:$expected" >&2
    rm -f "$TARBALL" "$CANONICAL"
    exit 1
fi

# The default compressor writes fixed gzip metadata and a stored-block deflate stream, so the
# compressed bytes depend only on the canonical tar rather than on the host gzip.
GZIPPER=${DM_BUNDLE_GZIP:-python3 $SCRIPT_DIR/bundle-gzip.py}
if ! gzip_out=$($GZIPPER "$CANONICAL" "$OUT"); then
    echo "GZIP_FAILED=$CANONICAL (deterministic compressor refused)" >&2
    rm -f "$OUT" "$TARBALL" "$CANONICAL"
    exit 1
fi
echo "$gzip_out"
rm -f "$TARBALL" "$CANONICAL"
if [ ! -s "$OUT" ]; then
    echo "BUNDLE_EMPTY=$OUT (0 bytes)" >&2
    exit 1
fi
echo "archive bytes     : $(wc -c < "$OUT" | tr -d ' ')"
printf 'bundle sha256: %s\n' "$(digest "$OUT")"
