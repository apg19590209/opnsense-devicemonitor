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
# mtime normalisation below uses `touch -t`, which reads the *local* timezone. Without this
# the same commit produced 451a03f4… on an AEDT host and e6596665… under TZ=UTC0 — the
# published identity must not depend on where it was built (Decision 67).
TZ=UTC0
export TZ

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

# 1. Manifest payload: the 42 hash-verified install targets.
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
# inputs must give identical bytes from any checkout. Normalised here or by the
# canonicaliser that follows —
#   * member mtimes (`cp -p` would otherwise inherit each checkout's timestamps, and
#     `touch -t` would otherwise read the local timezone);
#   * uid/gid and their symbolic names, which depend on who built the archive;
#   * the member-order source, which is the sorted allow-list, never a directory scan;
#   * the archive format, pinned to ustar so no pax extended header can leak in;
#   * the *header encoding*, which differs between bsdtar and GNU tar (Decision 67).
# gzip is no longer the host tool: release/bundle-gzip.py writes a fixed header (mtime 0,
# OS 255) and a stored-block deflate stream, so the compressed bytes do not depend on whether
# BSD gzip or GNU gzip is installed (Decision 68). File modes are
# NOT normalised: the executable bits recorded in git must survive.
find "$BUILD" -exec touch -h -t 202601010000.00 {} +

# ---------------------------------------------------------------------------
# Tar implementation detection (Decision 67). The first GitHub run failed here: the script
# passed bsdtar-only --uid/--gid to GNU tar, the failure was swallowed by the `tar | gzip`
# pipeline, and a 20-byte gzip was published as the bundle. The implementation is probed
# from the binary itself (an OS check would be wrong: FreeBSD can run GNU tar and a Linux
# runner can carry bsdtar). Unknown implementations are refused, not guessed at.
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
        # GNU tar 1.35 has no --uname/--gname (those are bsdtar); ownership is spelled
        # --owner=NAME:UID and --group=NAME:GID, which set both the symbolic name and the
        # numeric id. Run #41611564118 proved the previous --uname=/--gname= spelling is
        # rejected outright: "tar: unrecognized option '--uname=root'".
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

# Functional probe: accept the flags and the format, not just the version string. A tar
# that claims to be ustar but writes GNU/pax headers is rejected here instead of shipping a
# different bundle later.
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

# ---------------------------------------------------------------------------
# Fail-safe construction (Decision 67): every stage writes an explicit file and its status
# is checked, so no pipeline can mask a failure and no partial archive is ever published.
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
# Unquoted on purpose: DM_BUNDLE_GZIP exists so a test can substitute a failing compressor and
# prove the build stops. The default is our own deterministic writer.
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
