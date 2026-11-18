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

# 0. Candidate identity: the tree must descend from the integration branch and its
#    manifest must carry the Email Log feature set. A candidate cut from a stale main
#    once reached a testbed with a manifest that had silently lost the whole feature.
FEATURE_ARGS=""
if [ -f "$REPO/release/feature-set.txt" ]; then
    set -f
    for feature in $(grep -v '^#' "$REPO/release/feature-set.txt" | awk 'NF {print $1}'); do
        FEATURE_ARGS="$FEATURE_ARGS --min-features $feature"
    done
    set +f
fi
if [ "${DM_SOURCE_EXPORT:-0}" != 1 ] && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    # shellcheck disable=SC2086
    # A CI PR checkout has no local main, but the integration ref is still authoritative.
    if [ -z "${DM_CANDIDATE_ANCESTOR:-}" ] && ! git rev-parse --verify --quiet 'main^{commit}' >/dev/null; then
        DM_CANDIDATE_ANCESTOR=origin/main
    fi
    /bin/sh "$REPO/release/verify-candidate.sh" --ancestor "${DM_CANDIDATE_ANCESTOR:-main}" $FEATURE_ARGS >/dev/null || {
        echo 'ABORT: candidate identity check failed' >&2
        exit 1
    }
    SOURCE=$(git rev-parse HEAD)
else
    # An exported source has no Git ancestry metadata. It must state its exact source and
    # carry the exporter's mode map; a .git directory here would make the two metadata
    # sources ambiguous.
    [ ! -e "$REPO/.git" ] || { echo 'ABORT: DM_SOURCE_EXPORT inside a Git checkout is ambiguous' >&2; exit 1; }
    SOURCE=${DM_CANDIDATE_SOURCE:-}
    case "$SOURCE" in *[!0-9a-f]*|'') echo 'ABORT: exported source needs DM_CANDIDATE_SOURCE as a commit SHA' >&2; exit 1;; esac
    [ "${#SOURCE}" -eq 40 ] || { echo 'ABORT: DM_CANDIDATE_SOURCE must be a full commit SHA' >&2; exit 1; }
    for baseline in release/manifests/*-runtime.manifest; do
        [ -f "$baseline" ] || continue
        while read -r hash mode feature target; do
            [ -n "$feature" ] || { echo 'ABORT: malformed baseline row' >&2; exit 1; }
            awk -v s="$feature" '$3 == s {found=1} END {exit !found}' "$REPO/release/v${VERSION}-runtime.manifest" ||
                { echo "ABORT: manifest lost a baseline target: $feature" >&2; exit 1; }
        done < "$baseline"
    done
    while read -r feature; do
        case "$feature" in ''|'#'*) continue ;; esac
        awk -v p="$feature" 'index($3,p)>0 {found=1} END {exit !found}' "$REPO/release/v${VERSION}-runtime.manifest" ||
            { echo "ABORT: manifest lacks feature $feature" >&2; exit 1; }
    done < "$REPO/release/feature-set.txt"
fi

# 1. Manifest payload: the hash-verified install targets.
awk '{print $3}' "$MANIFEST" > "$LIST"

# 2. The .po catalogues the installer compiles, taken from the single supported-locale policy
#    (release/supported-locales.sh) rather than a broad find: a retained-but-deferred translation
#    source (nl_NL, DM-BL-008a) must never re-enter the payload by file discovery.
. "$REPO/release/supported-locales.sh"
for lang in $SUPPORTED_LOCALES; do
    printf '%s\n' "src/opnsense/mvc/app/languages/${lang}/LC_MESSAGES/devicemonitor.po" >> "$LIST"
done
# The policy file itself is shipped so the installer and the bundle cannot diverge.
printf '%s\n' release/supported-locales.sh >> "$LIST"

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
    release/repair-core-catalogues.sh \
    release/pristine-catalogues.sha256 \
    release/manifests/v${VERSION}-runtime.manifest \
    release/verify-candidate.sh \
    release/feature-set.txt \
    release/verify-bundle.py \
    release/verify-fetched-bundle.sh \
    release/verify-testbed-acceptance.sh \
    release/testbed-acceptance.sh \
    release/record-acceptance.sh \
    release/execution-ledger.py \
    release/verify-execution.py \
    release/run-host-checks.sh \
    release/acceptance-check.php \
    release/results-file.py \
    release/current-task-requirements.txt \
    release/export-modes.txt \
    release/validate-deploy-archive.py \
    release/prune-plan.sh \
    release/legacy-targets.txt >> "$LIST"
# The packed pristine baselines are a repair input, not a runtime target. They are shipped one
# file per supported locale (nine in total) and are neither installed nor listed in the record.
for lang in $SUPPORTED_LOCALES; do
    [ "$lang" = en_US ] && continue
    printf '%s\n' "release/core-catalogues/${lang}.OPNsense.mo" >> "$LIST"
done

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
    if [ "${DM_SOURCE_EXPORT:-0}" != 1 ] && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        mode=$(git ls-files --stage -- "$f" | awk 'NR == 1 { print $1 } END { if (NR != 1) exit 1 }')
    elif [ "${DM_SOURCE_EXPORT:-0}" = 1 ]; then
        # Exported sources use the checked-in mode map made from the Git index. A path-based
        # guess would change archive modes and therefore the published identity.
        mode=$(awk -F' ' -v p="$f" '$2 == p {print $1; found=1} END {if (!found) exit 1}' "$REPO/release/export-modes.txt") ||
            { echo "UNSUPPORTED_SOURCE=$f (not in release/export-modes.txt)" >&2; exit 1; }
    else
        echo "UNSUPPORTED_SOURCE=$f (no Git metadata; set DM_SOURCE_EXPORT=1)" >&2
        exit 1
    fi
    case $mode in
        100644) chmod 644 "$BUILD/$f" ;;
        100755) chmod 755 "$BUILD/$f" ;;
        *)
            echo "UNSUPPORTED_GIT_MODE=$mode $f (expected 100644 or 100755)" >&2
            exit 1
            ;;
    esac
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
# BSD gzip or GNU gzip is installed (Decision 68). File modes are normalised from the Git index:
# 100644 becomes 0644 and 100755 becomes 0755. This keeps the executable bits recorded in Git
# while making the archive independent of checkout umask and transient local permissions.
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
printf 'version=%s\nsource=%s\nbytes=%s\nsha256=%s\n' "$VERSION" "$SOURCE" \
    "$(wc -c < "$OUT" | tr -d ' ')" "$(digest "$OUT")" > "$OUT.identity"
chmod 644 "$OUT.identity"
# The built archive is verified against the list it was built from and the files in the
# fetched checkout; an incomplete or altered archive never gets a success line.
python3 "$SCRIPT_DIR/verify-bundle.py" --archive "$OUT" --list "$LIST" \
    --identity "$OUT.identity" --source "$SOURCE" || {
    echo "BUNDLE_VERIFY_FAILED=$OUT" >&2
    exit 1
}
echo "archive bytes     : $(wc -c < "$OUT" | tr -d ' ')"
printf 'bundle sha256: %s\n' "$(digest "$OUT")"
printf 'bundle identity: %s\n' "$OUT.identity"
