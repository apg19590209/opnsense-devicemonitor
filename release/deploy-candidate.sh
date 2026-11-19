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
INSTALLER_SHA=2ebaaec5ab26c75944f3e1f5a4a82fe04e3c59f29ad2841c157ff21a8d15a419
INPUTS_SHA=f02c4a7145dc75e54ccfee1f1eee901574faab2b15d58f9cc753d3e5ea972934
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

# One deployment entry point. The node's management address identifies the actual host and
# stage; acceptance files are checked before any installer write.
case "$HOST" in
    192.168.20.23) DEPLOY_STAGE=.23 ;;
    192.168.20.252) DEPLOY_STAGE=.252 ;;
    192.168.20.253) DEPLOY_STAGE=.253 ;;
    OPNsense.internal) DEPLOY_STAGE=.23 ;;
    local|localhost|127.0.0.1) DEPLOY_STAGE=LOCAL ;;
    OPNsense.home.arpa)
        case "${DM_DEPLOY_STAGE:-}" in
            .252|.253) DEPLOY_STAGE=$DM_DEPLOY_STAGE ;;
            *) echo 'ABORT: hostname deployment requires DM_DEPLOY_STAGE=.252 or .253' >&2; exit 1 ;;
        esac ;;
    *) echo "ABORT: unsupported host $HOST" >&2; exit 1 ;;
esac
# A local target is only valid when this process is the .23 testbed itself: the hostname and the
# management address on a local interface must both agree. SSH to the node from itself was the
# previous failure mode; the installer and its checks run directly here, through the same gate.
LOCAL=0
REMOTE=0
if [ "$DEPLOY_STAGE" = .252 ] || [ "$DEPLOY_STAGE" = .253 ]; then
    REMOTE=1
elif [ "$DEPLOY_STAGE" = LOCAL ]; then
    LOCAL=1
    HERE=$(${DM_HOSTNAME:-/bin/hostname})
    HERE_IP=$(${DM_IFCONFIG:-ifconfig} | awk '$1 == "inet" && $2 == "192.168.20.23" { print $2; exit }')
    [ "$HERE" = OPNsense.internal ] && [ "$HERE_IP" = 192.168.20.23 ] ||
        { echo "ABORT: local target is not the .23 testbed (hostname=$HERE address=${HERE_IP:-none})" >&2; exit 1; }
    DEPLOY_STAGE=.23
fi
# Remote stages run through SSH only. The verified toolchain (this archive's own release/ files,
# the same bytes validate-deploy-archive.py has just checked) is copied to a source-stamped
# directory, and the candidate archive goes alongside it; the remote gate then proves the local
# target before installing. A missing DM_SSH aborts before any remote write.
case "$DEPLOY_STAGE" in
    .252) [ -f "$REPO/release/acceptance/.23-$IDENT_SHA.passed" ] || { echo 'ABORT: .23 acceptance missing for this candidate' >&2; exit 1; } ;;
    .253) [ -f "$REPO/release/acceptance/.252-$IDENT_SHA.passed" ] || { echo 'ABORT: .252 acceptance missing for this candidate' >&2; exit 1; } ;;
esac
SSH_CMD=${DM_SSH:-}
# Remote reachability is checked only after the local prior-stage gate above has passed.
if [ "$REMOTE" = 1 ]; then
    [ -n "$SSH_CMD" ] || { echo 'ABORT: remote deployment requires DM_SSH (an ssh command with its identity and host-key options)' >&2; exit 1; }
    [ -n "${DM_REMOTE_LEDGER:-}" ] || { echo 'ABORT: DM_REMOTE_LEDGER (remote ledger path) is required' >&2; exit 1; }
    REMOTE_ROOT=/var/tmp/dm-release-tools
    REMOTE_DIR=$REMOTE_ROOT/$SOURCE
    # The verified toolchain (this archive's own release/ files, the bytes
    # validate-deploy-archive.py has just checked) is unpacked atomically at a source-stamped
    # directory; the archive itself goes with it so the remote gate re-checks everything.
    # shellcheck disable=SC2086
    $SSH_CMD "$HOST" "mkdir -p '$REMOTE_ROOT' && rm -rf '$REMOTE_DIR.new' && mkdir -p '$REMOTE_DIR.new' && tar -xzf - -C '$REMOTE_DIR.new' && mv '$REMOTE_DIR.new' '$REMOTE_DIR' && echo REMOTE_TOOLS_READY=$REMOTE_DIR" < "$ARCHIVE" || {
        echo 'ABORT: remote toolchain staging failed' >&2; exit 1; }
    # The role is a prerequisite, not just a post-install result: run the staged packaged check
    # on the host before the remote gate writes anything.
    # shellcheck disable=SC2086
    $SSH_CMD "$HOST" "TMPDIR=/var/tmp /usr/local/bin/python3 - '$REMOTE_DIR/release/run-host-checks.sh' '$DEPLOY_STAGE'" <<'ROLE_CHECK' || {
import os, re, subprocess, sys, tempfile
src = open(sys.argv[1], encoding='utf-8').read()
start = src.index('role_check() {')
end = src.index('\n}\n', start) + 3
fd, path = tempfile.mkstemp(prefix='dm-role-prereq.', suffix='.sh')
with os.fdopen(fd, 'w') as stream:
    stream.write('STAGE=%s\nDM_IFCONFIG=ifconfig\n' % sys.argv[2] + src[start:end] + '\nrole_check\n')
raise SystemExit(subprocess.run(['/bin/sh', path]).returncode)
ROLE_CHECK
        echo 'ABORT: role prerequisite failed before installation' >&2; exit 1; }
    echo "ROLE_PREREQUISITE_OK stage=$DEPLOY_STAGE"
    if [ "$DEPLOY_STAGE" = .253 ]; then
        # shellcheck disable=SC2086
        $SSH_CMD "$HOST" "python3 - '$DM_REMOTE_LEDGER' '$SOURCE'" <<'REMOTE_CHECK' || {
import json, sys
rows = [json.loads(line) for line in open(sys.argv[1], encoding='utf-8') if line.strip()]
ok = any(r.get('stage') == '.252' and r.get('phase') == 'acceptance' and r.get('result') == 'PASS'
         and r.get('source') == sys.argv[2] for r in rows)
raise SystemExit(0 if ok else 1)
REMOTE_CHECK
            echo 'ABORT: remote .253 requires a passing .252 acceptance record for this source' >&2; exit 1; }
    fi
fi
LEDGER=$REPO/release/execution-ledger.jsonl
DEPLOY_HOST=$(case "$DEPLOY_STAGE" in .23) echo 192.168.20.23;; .252) echo 192.168.20.252;; .253) echo 192.168.20.253;; esac)
record_deploy() {
    result=$1
    log=$2
    # This record is generated by the installer invocation above; the log is its evidence.
    if grep -q '^INSTALL_OK ' "$log"; then result=PASS; else result=FAIL; fi
    evidence=$(mktemp /tmp/dm-deploy-evidence.XXXXXX)
    install_result=$([ "$result" = PASS ] && echo PASS || echo FAIL)
    python3 "$SCRIPT_DIR/results-file.py" --out "$evidence" \
        --check deploy="$install_result" --check installed-hashes="$install_result" >/dev/null
    python3 "$SCRIPT_DIR/execution-ledger.py" record --ledger "$LEDGER" --stage "$DEPLOY_STAGE" \
        --host "$DEPLOY_HOST" --source "$SOURCE" --bundle "$IDENT_SHA" --phase deploy \
        --checks deploy,installed-hashes --result "$result" --evidence "$evidence"
    rm -f "$evidence"
    [ "$result" = PASS ]
}
if [ "$CHECK" = 1 ]; then
    echo "DEPLOYMENT_CHECK_OK source=$SOURCE bundle_sha256=$IDENT_SHA host=$HOST stage=$DEPLOY_STAGE local=$LOCAL"
    exit 0
fi

cd "$STAGE"
# The host-check runner reads its pinned helpers from /var/tmp/dm-release-tools (scoped by source)
# and falls back to its own directory. Stage only those pinned files from the verified archive
# extraction, at the fixed path the runner names, so the helper's own 0600/root-owner credential
# rule and the API checks behave identically on every host.
HELPER_DIR=/var/tmp/dm-release-tools
if [ ! -f "$HELPER_DIR/results-file.py" ]; then
    mkdir -p "$HELPER_DIR"
    for helper in run-host-checks.sh acceptance-check.php results-file.py; do
        cp "$STAGE/release/$helper" "$HELPER_DIR/$helper"
        chmod 755 "$HELPER_DIR/$helper"
        [ "$(sha256 -q "$STAGE/release/$helper")" = "$(sha256 -q "$HELPER_DIR/$helper")" ] ||
            { echo "ABORT: helper copy differs: $helper" >&2; exit 1; }
    done
fi
INSTALL_RESULT=0
if [ "$REMOTE" = 1 ]; then
    # shellcheck disable=SC2086
    $SSH_CMD "$HOST" "cd '$REMOTE_DIR' && ./release/deploy-candidate.sh '$REMOTE_DIR/dm-v2.15.0-runtime.tar.gz' '$REMOTE_DIR/dm-v2.15.0-runtime.tar.gz.identity' --host local --source '$SOURCE'" > "$STAGE/install.log" 2>&1 || INSTALL_RESULT=$?
else
    cp "$ARCHIVE" "$STAGE/dm-v2.15.0-runtime.tar.gz"
    cp "$IDENTITY" "$STAGE/dm-v2.15.0-runtime.tar.gz.identity"
    /bin/sh install-unattended.sh --host "$HOST" > "$STAGE/install.log" 2>&1 || INSTALL_RESULT=$?
fi
if ! record_deploy "$([ "$INSTALL_RESULT" = 0 ] && echo PASS || echo FAIL)" "$STAGE/install.log"; then
    cat "$STAGE/install.log" >&2
    exit 1
fi
[ "$INSTALL_RESULT" = 0 ] || {
    cat "$STAGE/install.log" >&2
    # The installer has already performed its own guarded rollback and verification.
    exit "$INSTALL_RESULT"
}
cat "$STAGE/install.log"
if [ "$LOCAL" = 1 ]; then
    # Local execution must be provable after the write, not merely intended before it.
    INSTALLED_AT=$(stat -f '%Su' /var/db/devicemonitor/installed-manifest.txt 2>/dev/null || echo unknown)
    echo "LOCAL_EXECUTION host=$HERE address=$HERE_IP stage=$DEPLOY_STAGE manifest_owner=$INSTALLED_AT"
    [ "$(stat -f '%Su' /var/db/devicemonitor/installed-manifest.txt)" = root ] ||
        { echo 'ABORT: local manifest is not root-owned' >&2; exit 1; }
fi
# Every required functional, database and settings check runs after the installer under the
# supported entry point. A failure aborts; acceptance remains a separate ledger-derived step.
HOST_EVIDENCE=$(mktemp /tmp/dm-host-evidence.XXXXXX)
if ! /bin/sh "$SCRIPT_DIR/run-host-checks.sh" --stage "$DEPLOY_STAGE" --source "$SOURCE" \
        --bundle "$IDENT_SHA" --out "$HOST_EVIDENCE"; then
    cp "$HOST_EVIDENCE" "$LEDGER.failed-$(date -u +%Y%m%dT%H%M%SZ)-$DEPLOY_STAGE"
    echo 'ABORT: host checks failed; no acceptance is possible' >&2
    rm -f "$HOST_EVIDENCE"
    exit 1
fi
HOST_CHECKS=$(python3 - "$HOST_EVIDENCE" <<'PY2'
import json,sys
c=json.load(open(sys.argv[1],encoding='utf-8'))['checks']
print(','.join(k for k in c if k != 'deploy'))
PY2
)
python3 "$SCRIPT_DIR/execution-ledger.py" record --ledger "$LEDGER" --stage "$DEPLOY_STAGE" \
    --host "$DEPLOY_HOST" --source "$SOURCE" --bundle "$IDENT_SHA" --phase own-check \
    --checks "$HOST_CHECKS" --result PASS --evidence "$HOST_EVIDENCE"
rm -f "$HOST_EVIDENCE"
