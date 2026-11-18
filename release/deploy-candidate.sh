#!/bin/sh
# Deployment entry point: bind an archive to its explicit source before any installation write.
#
#   deploy-candidate.sh ARCHIVE IDENTITY --host HOST --source SHA [--check]
#
# The installer retains its own input pins and transaction. This separate gate checks the
# installer digest, the archive identity/source, every archive member's bytes in an unpacked
# copy, required feature files in both manifest and archive, and the host's prior-stage
# acceptance. A production Git checkout is not required: the identity names the source and the
# unpacked archive carries the manifest/feature contract.
set -eu
LC_ALL=C
export LC_ALL
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)
cd "$REPO"
INSTALLER_SHA=229419a29e956c0f1273f3596915058f817d1cb8182226bc56474deb69053582
INPUTS_SHA=8ab307aaca4951724d8095c942fb92d7b391b1e66b43f174032522f0cdb36bc6
[ "$#" -ge 2 ] || { echo 'usage: deploy-candidate.sh ARCHIVE IDENTITY --host HOST --source SHA [--check]' >&2; exit 2; }
ARCHIVE=$1
IDENTITY=$2
shift 2
HOST=
SOURCE=
CHECK=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --host) [ "$#" -ge 2 ] || exit 2; HOST=$2; shift 2 ;;
        --source) [ "$#" -ge 2 ] || exit 2; SOURCE=$2; shift 2 ;;
        --check) CHECK=1; shift ;;
        *) echo "ABORT: unknown argument $1" >&2; exit 2 ;;
    esac
done
[ -n "$HOST" ] && [ -n "$SOURCE" ] || { echo 'ABORT: --host and --source are required' >&2; exit 2; }
[ -f "$ARCHIVE" ] && [ ! -L "$ARCHIVE" ] || { echo "ABORT: archive missing: $ARCHIVE" >&2; exit 1; }
[ -f "$IDENTITY" ] && [ ! -L "$IDENTITY" ] || { echo "ABORT: identity missing: $IDENTITY" >&2; exit 1; }
[ "$(sha256 -q install-unattended.sh)" = "$INSTALLER_SHA" ] || { echo 'ABORT: installer digest' >&2; exit 1; }
IDENT_SOURCE=$(sed -n 's/^source=//p' "$IDENTITY" | tail -1)
IDENT_SHA=$(sed -n 's/^sha256=//p' "$IDENTITY" | tail -1)
[ "$IDENT_SOURCE" = "$SOURCE" ] || { echo 'ABORT: archive identity source differs from --source' >&2; exit 1; }
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    [ "$(git rev-parse HEAD)" = "$SOURCE" ] || { echo 'ABORT: worktree is not the declared source' >&2; exit 1; }
    [ -z "$(git status --porcelain)" ] || { echo 'ABORT: worktree is dirty' >&2; exit 1; }
fi
STAGE=$(mktemp -d /tmp/dm_deploy_candidate.XXXXXX)
trap 'rm -rf "$STAGE"' EXIT
tar -xzf "$ARCHIVE" -C "$STAGE"
python3 "$SCRIPT_DIR/validate-deploy-archive.py" --archive "$ARCHIVE" --identity "$IDENTITY" \
    --source "$SOURCE" --root "$STAGE"

case "$HOST" in OPNsense.internal|OPNsense.home.arpa|192.168.20.23|192.168.20.252|192.168.20.253) : ;; *) echo "ABORT: unsupported host $HOST" >&2; exit 1 ;; esac
ACCEPTANCE_DIR=$REPO/release/acceptance
if [ "$HOST" = 192.168.20.252 ]; then
    [ -f "$ACCEPTANCE_DIR/.23-$IDENT_SHA.passed" ] || { echo 'ABORT: .23 acceptance missing for this candidate' >&2; exit 1; }
fi
if [ "$HOST" = 192.168.20.253 ]; then
    [ -f "$ACCEPTANCE_DIR/.252-$IDENT_SHA.passed" ] || { echo 'ABORT: .252 acceptance missing for this candidate' >&2; exit 1; }
fi
if [ "$CHECK" = 1 ]; then
    echo "DEPLOYMENT_CHECK_OK source=$SOURCE bundle_sha256=$IDENT_SHA host=$HOST"
    exit 0
fi
cd "$STAGE"
/bin/sh install-unattended.sh --host "$HOST"
