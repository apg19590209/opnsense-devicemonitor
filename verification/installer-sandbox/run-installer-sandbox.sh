#!/bin/sh
# ==============================================================================
# Device Monitor installer sandbox harness.
#
# Review item M5 (verification/REVIEW-R2-REMEDIATION-20261103.md) is that no test
# ever executed install-unattended.sh: the installer's own wiring was asserted
# textually, and every executable check stopped at release/prune-plan.sh.
#
# This harness executes the real, unmodified installer from an explicitly selected
# release bundle — byte-for-byte verified against its published identity — inside a
# disposable FreeBSD jail:
#
#   * read-only nullfs mounts of /bin /sbin /lib /libexec /usr /etc provide the
#     real toolchain (sh, python3, php, msgfmt, msgcat, sha256, stat, install,
#     service, pgrep);
#   * a writable scratch overlay is stacked over every path the installer may
#     write (the plugin's /usr/local trees, /usr/local/share/locale,
#     /usr/local/etc/{inc,rc.d}, /var, /tmp, /root, /etc/rc.d, /etc/rc.conf.d);
#   * the jail carries its own hostname, so the installer's hostname guard is
#     satisfied by the sandbox and never by the real node.
#
# Fail-closed rules (the installer itself has no notion of a sandbox):
#   * the harness refuses to run unless it is root on FreeBSD, outside any jail;
#   * every installer invocation goes through `jexec` into the sandbox jail and is
#     preceded by a marker + hostname + uid check performed *inside* that jail;
#   * if the jail cannot be entered or the checks fail, the installer is not run.
#
# The installer is never modified, and no installer safety check is relaxed.
# `--host` is satisfied by the sandbox hostname. The only host-service stub is
# `service configd`, which is an OPNsense service and not part of the payload: the
# stub records the call and doubles as the failure-injection point. A separate
# pgrep process-visibility shim delegates to the real pgrep with `-j <sandbox>` so
# the host's live daemon cannot satisfy the installer's run-state probe; this is
# not a payload stub and is itself documented in the verification record.
#
# Usage (on the Device Monitor testbed, as root):
#   sh verification/installer-sandbox/run-installer-sandbox.sh all
#   DM_SANDBOX_SAVE=1 sh verification/installer-sandbox/run-installer-sandbox.sh all
#   sh verification/installer-sandbox/run-installer-sandbox.sh scenario check
#   sh verification/installer-sandbox/run-installer-sandbox.sh clean
#
# Exit status: 0 only when every executed scenario passed.
# ==============================================================================
set -eu
export PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin
export LC_ALL=C

SELF=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
REPO=$(CDPATH= cd -- "$SELF/../.." && pwd -P)
WORK=${DM_SANDBOX_WORK:-/var/tmp/dm-installer-sandbox}
JAIL=dm-installer-sandbox
SB_HOST=dm-installer-sandbox.internal
MARKER=.dm-sandbox-marker
VERSION=${DM_SANDBOX_VERSION:-2.14.0}
PREDECESSOR_VERSION=${DM_SANDBOX_PREDECESSOR_VERSION:-2.13.3}
CANDIDATE_COMMIT=${DM_SANDBOX_CANDIDATE_COMMIT:-eac1160557352d45648c4a25310b8daeaad440f6}
CANDIDATE_SOURCE=${DM_SANDBOX_CANDIDATE_SOURCE:-worktree}
PREDECESSOR_COMMIT=${DM_SANDBOX_PREDECESSOR_COMMIT:-eadfc577b9ef184a12edba72780ec548a8486510}
BUNDLE_DIGEST=${DM_SANDBOX_BUNDLE_DIGEST:-5149bfd41e5842a144a9d1280c008511f20f3783932eca9beb1f48fca6173f5f}
BUNDLE_BYTES=${DM_SANDBOX_BUNDLE_BYTES:-1725593}
DEFAULT_CANDIDATE_BUNDLE=${DM_SANDBOX_BUNDLE:-/root/dm-backups/dm-bl009-candidate-rollback-fix-20261106-083105/dm-v2.14.0-runtime.tar.gz}
VERSION_SERIES=v$(printf '%s' "$VERSION" | awk -F. '{print $1 $2}')
STAGE_GLOB=/tmp/dm_install_${VERSION_SERIES}.*
BACKUP_PREFIX=install-${VERSION_SERIES}.
EVIDENCE_ROOT=${DM_SANDBOX_EVIDENCE_DIR:-$SELF/evidence-$VERSION}
LANGS='en_US cs_CZ de_DE fr_FR es_ES it_IT pt_BR nl_NL ru_RU ja_JP zh_CN'
# Legacy ownership evidence rows used to plant real historical leftovers: the v2.9 flat-layout
# catalogues, which no current release installs and whose digests are published in
# release/legacy-targets.txt (the per-locale LC_MESSAGES layout replaced them). There are
# exactly two published, non-current legacy paths. One is planted unchanged (prune); the
# other is modified after planting (retain), so the same run exercises both decisions.
LEGACY_TAG=v2.9
LEGACY_SRC_ONE=src/opnsense/mvc/app/languages/cs_CZ_devicemonitor.po
LEGACY_SRC_TWO=src/opnsense/mvc/app/languages/en_US_devicemonitor.po
LEGACY_PATH_ONE=/usr/local/opnsense/mvc/app/languages/cs_CZ_devicemonitor.po
LEGACY_PATH_TWO=/usr/local/opnsense/mvc/app/languages/en_US_devicemonitor.po

FAILED=0
CURRENT=

say()  { printf '%s\n' "$*"; }
fail() { printf 'SANDBOX_FAIL: %s\n' "$*" >&2; exit 1; }
pass() { printf 'SANDBOX_PASS: %s\n' "$*"; }

require_host() {
    [ "$(uname -s)" = FreeBSD ] || fail 'FreeBSD is required'
    [ "$(id -u)" = 0 ] || fail 'root is required'
    [ "$(sysctl -n security.jail.jailed)" = 0 ] || fail 'refusing to run inside a jail'
    [ -x /usr/sbin/jail ] && [ -x /usr/sbin/jexec ] || fail 'jail(8) and jexec(8) are required'
    [ "$(hostname)" != "$SB_HOST" ] || fail 'refusing: this host is the sandbox hostname'
    [ -d "$REPO/.git" ] || fail "not a repository: $REPO"
    command -v git >/dev/null 2>&1 || fail 'git is required'
    head=$(git -C "$REPO" rev-parse HEAD)
    [ "$head" = "$CANDIDATE_COMMIT" ] ||
        fail "candidate commit mismatch: HEAD $head != $CANDIDATE_COMMIT"
    git -C "$REPO" cat-file -e "$PREDECESSOR_COMMIT^{commit}" 2>/dev/null ||
        fail "predecessor commit not found: $PREDECESSOR_COMMIT"
    for t in tar msgfmt python3 sha256; do
        command -v "$t" >/dev/null 2>&1 || fail "$t is required"
    done
    [ -f /var/db/devicemonitor/installed-manifest.txt ] ||
        fail 'the live 2.13.3 installation record is missing'
    live_first=$(sed -n '1p' /var/db/devicemonitor/installed-manifest.txt)
    printf '%s\n' "$live_first" | grep -Fq "# Device Monitor $PREDECESSOR_VERSION install record" ||
        fail "live record does not identify $PREDECESSOR_VERSION: $live_first"
    live_version=$(python3 - <<'PY'
import json
p='/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'
print(json.load(open(p))['version'])
PY
    ) || fail 'cannot read the live installed version'
    [ "$live_version" = "$PREDECESSOR_VERSION" ] ||
        fail "live installed version $live_version != predecessor $PREDECESSOR_VERSION"
    [ -z "$(find /var/db/devicemonitor -maxdepth 1 -type f \( -name '*-wal' -o -name '*-shm' \) -print)" ] ||
        fail 'live SQLite WAL/SHM files are present; refusing an inconsistent copy'
}

# Read-only fingerprint of the live installation and host services. Every scenario is
# compared against this before it can pass, so a broken isolation layer cannot hide a
# change to the real node. Only hashes and metadata are recorded; file contents are not.
mount_targets() {
    mount 2>/dev/null | sed -n 's/^.* on \(.*\) ([^()]*)$/\1/p'
}

mount_target_exists() {
    mount_targets | grep -Fqx -- "$1"
}

live_fingerprint() {
    out=$1
    record=/var/db/devicemonitor/installed-manifest.txt
    {
        printf 'HOST %s\n' "$(hostname)"
        printf 'DEFAULTS %s\n' "$(sha256 -q /usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json)"
        printf 'SETTINGS %s\n' "$(sha256 -q /usr/local/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt)"
        printf 'RECORD %s\n' "$(sha256 -q "$record")"
        printf 'DB %s\n' "$(sha256 -q /var/db/devicemonitor/devices.db)"
        printf 'CONFIG %s\n' "$(sha256 -q /var/db/devicemonitor/config.json)"
        printf 'RCLINK %s\n' "$(readlink /etc/rc.d/devicemonitor 2>/dev/null || echo absent)"
        while read -r digest path; do
            [ -n "${path:-}" ] || continue
            case "$digest" in '#'*) continue ;; esac
            [ -f "$path" ] && [ ! -L "$path" ] || fail "live target is not a regular file: $path"
            actual=$(sha256 -q "$path")
            [ "$actual" = "$digest" ] || fail "live target digest drift: $path"
            printf 'TARGET %s %s %s %s %s\n' "$path" "$actual" \
                "$(stat -f %Lp "$path")" "$(stat -f %Su:%Sg "$path")" "$(stat -f %m "$path")"
        done < "$record"
        find /var/backups/devicemonitor -mindepth 1 -maxdepth 1 -print 2>/dev/null |
            sort | while read -r p; do printf 'BACKUP %s\n' "${p#/var/backups/devicemonitor/}"; done
        find /var/backups/devicemonitor/core-locale -maxdepth 1 -type f -print 2>/dev/null |
            sort | while read -r p; do
                printf 'CORELOCALEFILE %s %s %s %s\n' "${p#/var/backups/devicemonitor/core-locale/}" \
                    "$(sha256 -q "$p")" "$(stat -f %Lp "$p")" "$(stat -f %Su:%Sg "$p")"
            done
        printf 'DAEMONPID %s\n' "$(ps -axo pid,jail,command |
            awk 'NR > 1 && $2 == "-" && /\/usr\/local\/opnsense\/scripts\/OPNsense\/DeviceMonitor\/monitor_daemon\.py/ {print $1; exit}')"
        printf 'CONFIGDPID %s\n' "$(ps -axo pid,jail,command |
            awk 'NR > 1 && $2 == "-" && /\/usr\/local\/opnsense\/service\/configd\.py/ {print $1; exit}')"
        printf 'HOSTSTAGES %s\n' "$(find /tmp -maxdepth 1 -name "$(basename "$STAGE_GLOB")" -print 2>/dev/null | wc -l | tr -d ' ')"
        printf 'SANDBOXJAILS %s\n' "$(jls 2>/dev/null | awk 'NR > 1 && $4 == "'"$JAIL"'" {n++} END {print n+0}')"
        printf 'SANDBOXMOUNTS %s\n' "$(mount_targets | awk -v w="$WORK/" 'index($0, w) == 1 {n++} END {print n+0}')"
    } > "$out"
}

assert_live_unchanged() {
    live_fingerprint "$EVI/live-after.fingerprint"
    if cmp -s "$WORK/live-before.fingerprint" "$EVI/live-after.fingerprint"; then
        pass 'live .23 installation, daemon, configd, backups and host stage area are unchanged'
        return 0
    fi
    printf 'SANDBOX_FAIL: live host state changed\n' >&2
    diff -u "$WORK/live-before.fingerprint" "$EVI/live-after.fingerprint" >&2 || :
    : > "$WORK/abort"
    return 1
}

# ------------------------------------------------------------------------------
# Sandbox layout
# ------------------------------------------------------------------------------
# BASE/root      jail root (nullfs read-only base + writable overlays)
# BASE/scratch   host-side source of every writable overlay
# BASE/mounts    mount points in mount order, for teardown
# BASE/evidence  captured transcripts for this scenario
# The jail sees the bundle under /root/release and nothing else from the repository.

sb_build() {
    CURRENT=$1
    BASE=$WORK/$CURRENT
    ROOT=$BASE/root
    SCR=$BASE/scratch
    MNT_LIST=$BASE/mounts
    EVI=$BASE/evidence
    rm -rf "$BASE"
    mkdir -p "$ROOT" "$SCR" "$EVI"
    : > "$MNT_LIST"
    for d in bin sbin lib libexec usr etc dev proc tmp var root .host-bin; do
        mkdir -p "$ROOT/$d"
    done
    for d in etc.rc.d etc.rc.conf.d var tmp root usr.local.etc.inc usr.local.etc.rc.d \
             mvc.app.languages mvc.app.models mvc.app.controllers mvc.app.views \
             scripts.dm service.actions.d www.js.widgets share.locale tooling.bin; do
        mkdir -p "$SCR/$d"
    done
    sb_seed
}

# Copies the host's read-only state into the writable overlays. The plugin trees the
# payload writes to start empty; everything else is the host's real content, so the
# installer compiles its catalogues against real core catalogues and merges into real
# plugins.inc.d/actions.d/widget directories.
sb_seed() {
    cp -a /etc/rc.d/. "$SCR/etc.rc.d/"
    cp -a /usr/local/etc/inc/. "$SCR/usr.local.etc.inc/"
    cp -a /usr/local/etc/rc.d/. "$SCR/usr.local.etc.rc.d/"
    cp -a /usr/local/opnsense/mvc/app/languages/. "$SCR/mvc.app.languages/"
    cp -a /usr/local/opnsense/service/conf/actions.d/. "$SCR/service.actions.d/"
    cp -a /usr/local/opnsense/www/js/widgets/. "$SCR/www.js.widgets/"
    cp -a /usr/local/share/locale/. "$SCR/share.locale/"
    rm -f "$SCR/etc.rc.conf.d/devicemonitor"
    mkdir -p "$SCR/var/db/devicemonitor" "$SCR/var/backups/devicemonitor" \
             "$SCR/var/lib/php/tmp" "$SCR/var/log" "$SCR/var/run" "$SCR/var/tmp" \
             "$SCR/var/cache" "$SCR/var/spool"
    # The one stub. configd is an OPNsense host service, not part of the payload, and the
    # installer calls `service configd restart' unconditionally. The stub records the call
    # and fails on demand, which is how the rollback scenario injects a failure *after* the
    # prune step without touching the installer.
    cat > "$SCR/usr.local.etc.rc.d/configd" <<'STUB'
#!/bin/sh
# SANDBOX STUB (verification/installer-sandbox/run-installer-sandbox.sh): configd is an
# OPNsense host service and is not part of the Device Monitor payload under test.
echo "SANDBOX_SERVICE configd $*" >> /var/log/sandbox-services.log
if [ -e /.dm-fail-configd ]; then
    echo "SANDBOX: injected failure in service configd $*" >&2
    exit 1
fi
exit 0
STUB
    chmod 755 "$SCR/usr.local.etc.rc.d/configd"
    # The host has security.bsd.see_jail_proc=1 and a live Device Monitor daemon. The jail's
    # /bin is a directory overlay whose entries link back to a read-only host /bin mount;
    # only pgrep is replaced. It delegates to that same real binary with the sandbox jail id,
    # so the installer's process pattern is unchanged while host processes stay invisible.
    for source in /bin/*; do
        bin_name=${source##*/}
        [ "$bin_name" = pgrep ] && continue
        ln -s "/.host-bin/$bin_name" "$SCR/tooling.bin/$bin_name"
    done
    cat > "$SCR/tooling.bin/pgrep" <<EOF
#!/bin/sh
exec /.host-bin/pgrep -j $JAIL "\$@"
EOF
    chmod 555 "$SCR/tooling.bin/pgrep"
}

sb_mount() {
    mkdir -p "$ROOT/.host-bin"
    mount -t nullfs -o ro /bin "$ROOT/.host-bin" || fail 'nullfs /.host-bin'
    printf '%s\n' "$ROOT/.host-bin" >> "$MNT_LIST"
    mount -t nullfs -o ro "$SCR/tooling.bin" "$ROOT/bin" || fail 'nullfs /bin shim'
    printf '%s\n' "$ROOT/bin" >> "$MNT_LIST"
    for d in sbin lib libexec usr etc; do
        mount -t nullfs -o ro "/$d" "$ROOT/$d" || fail "nullfs /$d"
        printf '%s\n' "$ROOT/$d" >> "$MNT_LIST"
    done
    mount -t devfs devfs "$ROOT/dev" || fail 'devfs mount'
    printf '%s\n' "$ROOT/dev" >> "$MNT_LIST"
    while read -r src target; do
        [ -n "$src" ] || continue
        mount -t nullfs "$SCR/$src" "$ROOT$target" || fail "nullfs $target"
        printf '%s\n' "$ROOT$target" >> "$MNT_LIST"
    done <<'OVERLAYS'
etc.rc.d /etc/rc.d
etc.rc.conf.d /etc/rc.conf.d
var /var
tmp /tmp
root /root
usr.local.etc.inc /usr/local/etc/inc
usr.local.etc.rc.d /usr/local/etc/rc.d
mvc.app.languages /usr/local/opnsense/mvc/app/languages
mvc.app.models /usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor
mvc.app.controllers /usr/local/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor
mvc.app.views /usr/local/opnsense/mvc/app/views/OPNsense/DeviceMonitor
scripts.dm /usr/local/opnsense/scripts/OPNsense/DeviceMonitor
service.actions.d /usr/local/opnsense/service/conf/actions.d
www.js.widgets /usr/local/opnsense/www/js/widgets
share.locale /usr/local/share/locale
OVERLAYS
    printf 'sandbox=%s host=%s created=%s\n' "$CURRENT" "$SB_HOST" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        > "$ROOT/$MARKER"
}

sb_umount() {
    [ -f "${MNT_LIST:-}" ] || return 0
    rc=0
    lines=$(wc -l < "$MNT_LIST" | tr -d ' ')
    while [ "$lines" -gt 0 ]; do
        point=$(sed -n "${lines}p" "$MNT_LIST")
        if mount_target_exists "$point"; then
            umount "$point" 2>/dev/null || umount -f "$point" 2>/dev/null || :
            if mount_target_exists "$point"; then
                printf 'SANDBOX_FAIL: mount still present: %s\n' "$point" >&2
                rc=1
            fi
        fi
        lines=$((lines - 1))
    done
    : > "$MNT_LIST"
    return "$rc"
}

sb_start() {
    /usr/sbin/jail -c name="$JAIL" path="$ROOT" host.hostname="$SB_HOST" persist \
        || fail 'cannot start the sandbox jail'
    /usr/sbin/jexec "$JAIL" /bin/sh -c \
        "test -f /$MARKER && test \"\$(hostname)\" = \"$SB_HOST\" && test \"\$(id -u)\" = 0" \
        || { sb_stop; fail 'sandbox identity check failed, installer not run'; }
}

sandbox_jail_exists() {
    /usr/sbin/jls -j "$JAIL" jid >/dev/null 2>&1
}

sb_stop() {
    /usr/sbin/jail -r "$JAIL" >/dev/null 2>&1 || :
    if sandbox_jail_exists; then
        printf 'SANDBOX_FAIL: jail still present: %s\n' "$JAIL" >&2
        return 1
    fi
    return 0
}

# Runs a script inside the sandbox jail. Every installer invocation goes through this
# function, and the script it runs starts with an identity check, so a broken jail can
# only ever produce a refusal - never an install against the host.
sb_run() {
    {
        printf 'set -eu\n'
        printf 'test -f /%s || { echo "SANDBOX_FAIL: not inside the sandbox" >&2; exit 99; }\n' "$MARKER"
        printf 'test "$(hostname)" = "%s" || { echo "SANDBOX_FAIL: sandbox hostname mismatch" >&2; exit 99; }\n' "$SB_HOST"
        printf 'test "$(id -u)" = 0 || { echo "SANDBOX_FAIL: not root in the sandbox" >&2; exit 99; }\n'
        cat
    } | /usr/sbin/jexec "$JAIL" /bin/sh -s "$@"
}

sb_teardown() {
    rc=0
    sb_stop || rc=1
    sb_umount || rc=1
    return "$rc"
}

assert_sandbox_clean() {
    rc=0
    if sandbox_jail_exists; then
        printf 'SANDBOX_FAIL: sandbox jail remains after teardown\n' >&2
        rc=1
    fi
    mounts=$(mount_targets | awk -v w="$WORK/" 'index($0, w) == 1 {print}')
    if [ -n "$mounts" ]; then
        printf 'SANDBOX_FAIL: sandbox mounts remain after teardown:\n%s\n' "$mounts" >&2
        rc=1
    fi
    stages=$(find /tmp -maxdepth 1 -name "$(basename "$STAGE_GLOB")" -print 2>/dev/null)
    if [ -n "$stages" ]; then
        printf 'SANDBOX_FAIL: host installer stage directories remain:\n%s\n' "$stages" >&2
        rc=1
    fi
    stages=$(find "$WORK" -path '*/scratch/tmp/dm_install_*' -print 2>/dev/null)
    if [ -n "$stages" ]; then
        printf 'SANDBOX_FAIL: sandbox installer stage directories remain:\n%s\n' "$stages" >&2
        rc=1
    fi
    if [ "$rc" = 0 ]; then
        pass 'sandbox jail, mounts and host stage directories were removed'
    else
        : > "$WORK/abort"
    fi
    return "$rc"
}

# ------------------------------------------------------------------------------
# Staging: the artifact under test, the predecessor tree, the expected target set
# ------------------------------------------------------------------------------

# Selects the explicit candidate bundle, proves its size and published digest, then proves
# every extracted member is byte-identical to its declared source. The source is either the
# current working tree (for an uncommitted candidate) or the named candidate commit.
# DM_SANDBOX_BUNDLE may override the archive; when it is absent the known candidate copy is
# used, and only when neither exists is the bundle rebuilt from the checkout.
sb_stage_bundle() {
    out=$BASE/bundle.tar.gz
    if [ -n "${DM_SANDBOX_BUNDLE:-}" ] || [ -f "$DEFAULT_CANDIDATE_BUNDLE" ]; then
        source=${DM_SANDBOX_BUNDLE:-$DEFAULT_CANDIDATE_BUNDLE}
        cp "$source" "$out" || fail "cannot copy candidate bundle: $source"
        printf 'SANDBOX_BUNDLE source=%s\n' "$source" > "$EVI/bundle-build.log"
    else
        rm -rf "$BASE/stage"
        DM_BUNDLE_OUT=$out DM_BUNDLE_STAGE=$BASE/stage DM_BUNDLE_LIST=$BASE/bundle-list.txt \
            sh "$REPO/release/build-bundle.sh" > "$EVI/bundle-build.log" 2>&1 ||
            { cat "$EVI/bundle-build.log" >&2; fail 'bundle build failed'; }
    fi
    digest=$(sha256 -q "$out")
    [ "$digest" = "$BUNDLE_DIGEST" ] || fail "bundle digest $digest is not the published $BUNDLE_DIGEST"
    bytes=$(stat -f %z "$out")
    [ "$bytes" = "$BUNDLE_BYTES" ] || fail "bundle size $bytes is not the published $BUNDLE_BYTES"
    printf 'SANDBOX_BUNDLE sha256=%s bytes=%s version=%s commit=%s source=%s\n' \
        "$digest" "$bytes" "$VERSION" "$CANDIDATE_COMMIT" "$CANDIDATE_SOURCE" |
        tee -a "$EVI/bundle-build.log"
    mkdir -p "$SCR/root/release"
    tar -xzf "$out" -C "$SCR/root/release" || fail 'cannot extract the bundle'
    case "$CANDIDATE_SOURCE" in
        worktree)
            candidate_root=$REPO
            git -C "$REPO" status --porcelain=v1 > "$EVI/candidate-worktree.status" ||
                fail 'cannot record the candidate working-tree status'
            ;;
        commit)
            mkdir -p "$BASE/candidate-git"
            git -C "$REPO" archive --format=tar "$CANDIDATE_COMMIT" |
                tar -xf - -C "$BASE/candidate-git" || fail 'cannot extract the candidate commit'
            candidate_root=$BASE/candidate-git
            ;;
        *)
            fail "unknown candidate source: $CANDIDATE_SOURCE"
            ;;
    esac
    tar -tzf "$out" > "$EVI/bundle-members.txt" || fail 'cannot list the candidate bundle'
    while IFS= read -r member; do
        [ -n "$member" ] || continue
        case "$member" in
            /*|*..*) fail "unsafe bundle member: $member" ;;
        esac
        [ -f "$SCR/root/release/$member" ] || fail "bundle member is not a regular file: $member"
        [ -f "$candidate_root/$member" ] || fail "candidate source lacks bundle member: $member"
        cmp -s "$SCR/root/release/$member" "$candidate_root/$member" ||
            fail "bundle member differs from candidate source: $member"
    done < "$EVI/bundle-members.txt"
    pass "candidate bundle and all $(grep -c . "$EVI/bundle-members.txt") members match $CANDIDATE_SOURCE $CANDIDATE_COMMIT"
}

# The exact pre-installation state: every live 2.13.3 installed target, the live record,
# database, configuration and pristine-catalogue archive, plus two published non-current
# legacy paths (one unchanged for pruning, one deliberately modified for retention).
sb_stage_prestate_inputs() {
    record=/var/db/devicemonitor/installed-manifest.txt
    mkdir -p "$SCR/root/predecessor-live" "$SCR/root/prestate"
    : > "$SCR/root/predecessor-paths.txt"
    rows=0
    while read -r want target; do
        [ -n "${target:-}" ] || continue
        case "$want" in '#'*) continue ;; esac
        printf '%s' "$want" | grep -Eq '^[0-9a-f]{64}$' || fail "bad live record digest: $want"
        case "$target" in /usr/local/*) : ;; *) fail "live record target outside /usr/local: $target" ;; esac
        [ -f "$target" ] && [ ! -L "$target" ] || fail "live predecessor target is not regular: $target"
        got=$(sha256 -q "$target")
        [ "$got" = "$want" ] || fail "live predecessor digest drift: $target"
        dest="$SCR/root/predecessor-live$target"
        mkdir -p "$(dirname "$dest")"
        cp -p "$target" "$dest" || fail "cannot stage live predecessor target: $target"
        printf '%s %s\n' "$want" "$target" >> "$SCR/root/predecessor-paths.txt"
        rows=$((rows + 1))
    done < "$record"
    record_rows=$(awk '/^[0-9a-f]{64} \// {n++} END {print n+0}' "$record")
    [ "$rows" = "$record_rows" ] || fail "staged predecessor rows $rows != recorded $record_rows"
    [ "$rows" -gt 0 ] || fail 'live installation record has no targets'
    [ -f /usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json ] ||
        fail 'live predecessor defaults.json is missing'
    live_conf=$(python3 - <<'PY'
import json
print(json.load(open('/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'))['version'])
PY
    ) || fail 'cannot read live predecessor version'
    [ "$live_conf" = "$PREDECESSOR_VERSION" ] || fail "live predecessor version $live_conf"
    for f in installed-manifest.txt devices.db config.json; do
        cp -p "/var/db/devicemonitor/$f" "$SCR/root/prestate/$f" || fail "cannot stage $f"
    done
    mkdir -p "$SCR/root/prestate/core-locale"
    if [ -d /var/backups/devicemonitor/core-locale ]; then
        cp -Rp /var/backups/devicemonitor/core-locale/. "$SCR/root/prestate/core-locale/" ||
            fail 'cannot stage the pristine core-locale archive'
    fi
    rc_target=$(readlink /etc/rc.d/devicemonitor 2>/dev/null || true)
    [ "$rc_target" = /usr/local/etc/rc.d/devicemonitor ] || fail "unexpected rc link: ${rc_target:-absent}"
    printf '%s\n' "$rc_target" > "$SCR/root/prestate/rc-link"

    mkdir -p "$SCR/root/predecessor-legacy"
    git -C "$REPO" archive --format=tar "$LEGACY_TAG" "$LEGACY_SRC_ONE" "$LEGACY_SRC_TWO" |
        tar -xf - -C "$SCR/root/predecessor-legacy" || fail "cannot extract $LEGACY_TAG"
    prune_digest=$(awk -v p="$LEGACY_PATH_ONE" '$2 == p {print $1; exit}' "$REPO/release/legacy-targets.txt")
    retain_original=$(awk -v p="$LEGACY_PATH_TWO" '$2 == p {print $1; exit}' "$REPO/release/legacy-targets.txt")
    [ -n "$prune_digest" ] && [ -n "$retain_original" ] || fail 'cannot read published legacy fixture digests'
    for entry in "$prune_digest $LEGACY_SRC_ONE" "$retain_original $LEGACY_SRC_TWO"; do
        want=${entry%% *}; src=${entry#* }
        got=$(sha256 -q "$SCR/root/predecessor-legacy/$src")
        [ "$got" = "$want" ] || fail "$LEGACY_TAG source $src digest $got != published $want"
    done
    printf '\n# sandbox retained fixture: published content deliberately modified\n' \
        >> "$SCR/root/predecessor-legacy/$LEGACY_SRC_TWO"
    retain_digest=$(sha256 -q "$SCR/root/predecessor-legacy/$LEGACY_SRC_TWO")
    [ "$retain_digest" != "$retain_original" ] || fail 'retained legacy fixture was not modified'
    grep -q "^$retain_digest $LEGACY_PATH_TWO$" "$REPO/release/legacy-targets.txt" &&
        fail 'modified legacy fixture accidentally matches published ownership evidence' || :
    printf '%s %s %s\n' "$prune_digest" "$LEGACY_SRC_ONE" "$LEGACY_PATH_ONE" > "$SCR/root/legacy-prune.txt"
    printf '%s %s %s\n' "$retain_digest" "$LEGACY_SRC_TWO" "$LEGACY_PATH_TWO" > "$SCR/root/legacy-retain.txt"
    say "SANDBOX_PRESTATE record_rows=$rows predecessor=$live_conf legacy_prune=1 legacy_retain=1"
}

# The expected target set, derived from the manifest and the locale list, plus a plan of how
# each target's digest is to be verified independently of the installer's own accounting.
sb_stage_expectations() {
    manifest=$REPO/release/v${VERSION}-runtime.manifest
    [ -f "$manifest" ] || fail "candidate manifest missing: $manifest"
    manifest_rows=$(grep -c . "$manifest")
    lang_count=$(printf '%s\n' $LANGS | grep -c .)
    core_count=$((lang_count - 1))
    EXPECTED_TARGETS=$((manifest_rows + lang_count + core_count))
    EXPECTED_CORE_LOCALES=$core_count
    [ "$EXPECTED_TARGETS" -gt 0 ] || fail 'derived target count is zero'
    : > "$SCR/root/targets.txt"
    : > "$SCR/root/expect.tsv"
    while read -r hash mode source target; do
        printf '%s\n' "$target" >> "$SCR/root/targets.txt"
        printf 'manifest\t%s\t%s\t%s\n' "$source" "$target" "$mode" >> "$SCR/root/expect.tsv"
    done < "$manifest"
    for lang in $LANGS; do
        po="src/opnsense/mvc/app/languages/${lang}/LC_MESSAGES/devicemonitor.po"
        mo="/usr/local/opnsense/mvc/app/languages/${lang}/LC_MESSAGES/devicemonitor.mo"
        printf '%s\n' "$mo" >> "$SCR/root/targets.txt"
        printf 'msgfmt\t%s\t%s\t644\n' "$po" "$mo" >> "$SCR/root/expect.tsv"
        [ "$lang" = en_US ] && continue
        core="/usr/local/share/locale/${lang}/LC_MESSAGES/OPNsense.mo"
        if [ -f "$core" ]; then core_mode=$(stat -f %Lp "$core"); else core_mode=644; fi
        printf '%s\n' "$core" >> "$SCR/root/targets.txt"
        printf 'core\t%s\t%s\t%s\n' "$po" "$core" "$core_mode" >> "$SCR/root/expect.tsv"
    done
    actual_targets=$(grep -c . "$SCR/root/targets.txt")
    [ "$actual_targets" = "$EXPECTED_TARGETS" ] ||
        fail "derived target file has $actual_targets rows, expected $EXPECTED_TARGETS"
    cat "$SCR/root/targets.txt" > "$SCR/root/state-paths.txt"
    awk '{print $3}' "$SCR/root/legacy-prune.txt" "$SCR/root/legacy-retain.txt" \
        >> "$SCR/root/state-paths.txt"
    duplicate_targets=$(sort "$SCR/root/targets.txt" | uniq -d | wc -l | tr -d ' ')
    [ "$duplicate_targets" = 0 ] || fail "candidate target list has $duplicate_targets duplicate path(s)"
    cat > "$SCR/root/candidate.env" <<ENV
VERSION=$VERSION
PREDECESSOR_VERSION=$PREDECESSOR_VERSION
CANDIDATE_COMMIT=$CANDIDATE_COMMIT
CANDIDATE_SOURCE=$CANDIDATE_SOURCE
PREDECESSOR_COMMIT=$PREDECESSOR_COMMIT
BUNDLE_DIGEST=$BUNDLE_DIGEST
EXPECTED_TARGETS=$EXPECTED_TARGETS
EXPECTED_CORE_LOCALES=$EXPECTED_CORE_LOCALES
ENV
    cp "$SCR/root/candidate.env" "$EVI/candidate.env"

    cat > "$SCR/root/verify-about-endpoint.py" <<'PY'
import json
import re
import sys
from pathlib import Path

expected = sys.argv[1]
settings_path = Path('/usr/local/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt')
controller_path = Path('/usr/local/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/ConfigController.php')
defaults_path = Path('/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json')
settings = settings_path.read_text()
controller = controller_path.read_text()
defaults = json.loads(defaults_path.read_text())
errors = []

if re.search(r'v2\.10 Features and Enhancements', settings):
    errors.append('stale v2.10 heading remains in settings.volt')
if not re.search(r'<span id="about-version"[^>]*>\s*</span>', settings):
    errors.append('About version badge is not an empty endpoint-fed span')
features_span = re.search(r'<span id="about-features-version"[^>]*>(.*?)</span>', settings, re.S)
if not features_span or 'devicemonitor_t' in features_span.group(1):
    errors.append('Features version span is missing or contains an unexpected expression')
features_fallback = features_span.group(1).strip() if features_span else ''

callback = re.search(
    r"// Version\s*\$\.getJSON\('/api/devicemonitor/config/getversion', function\(d\) \{(?P<body>.*?)\n\s*\}\);",
    settings, re.S)
if not callback:
    errors.append('single getversion callback was not found')
else:
    body = callback.group('body')
    if not re.search(r"var v = 'v'\+\(d\.version\|\|'\?'\);", body):
        errors.append('neither display value is derived from the endpoint version field')
    if not re.search(r"\$\('#about-version'\)\.text\(v\);", body):
        errors.append('About badge is not populated from the getversion response')
    if not re.search(r"\$\('#about-features-version'\)\.text\(v\);", body):
        errors.append('Features heading is not populated from the getversion response')
if settings.count("/api/devicemonitor/config/getversion") != 1:
    errors.append('settings.volt does not have exactly one version endpoint call')
if len(re.findall(r"\$\('#about-version'\)\.text\(", settings)) != 1:
    errors.append('About badge has more than one display assignment')
if len(re.findall(r"\$\('#about-features-version'\)\.text\(", settings)) != 1:
    errors.append('Features heading has more than one display assignment')

method = re.search(
    r"public function getversionAction\(\)\s*\{(?P<body>.*?)\n\s{4}\}",
    controller, re.S)
if not method:
    errors.append('getversionAction method was not found')
else:
    body = method.group('body')
    if "'/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'" not in body:
        errors.append('getversionAction does not read the installed defaults.json')
    if "['version']" not in body:
        errors.append('getversionAction does not return the defaults version field')
if str(defaults.get('version', '')) != expected:
    errors.append(f"defaults version {defaults.get('version')!r} != expected {expected!r}")

if errors:
    for error in errors:
        print('VERIFY_FAIL about_endpoint:', error)
    raise SystemExit(1)
print(f'VERIFY_ABOUT_ENDPOINT={defaults["version"]}')
print('VERIFY_ABOUT_BINDINGS=about-version,about-features-version')
print(f'VERIFY_FEATURES_STATIC_FALLBACK={features_fallback or "none"}')
print('VERIFY_ABOUT_MODE=source-endpoint-binding; authenticated-browser=not-performed')
PY
    pass "manifest and locale plan derive $EXPECTED_TARGETS targets ($manifest_rows manifest, $lang_count sidecars, $core_count core)"
}

# ------------------------------------------------------------------------------
# Pre-installation state (runs inside the jail, against the real absolute paths)
# ------------------------------------------------------------------------------
sb_prestate() {
    rc=0
    sb_run "$LANGS" > "$EVI/prestate.log" 2>&1 <<'PRESTATE' || rc=$?
langs=$1
# 1. Every target named by the live 2.13.3 installation record, copied from the host by
#    the harness and re-verified here before it reaches its installed path.
while read -r hash target; do
    source="/root/predecessor-live$target"
    [ -f "$source" ] || { echo "PRESTATE_FAIL missing source $source" >&2; exit 1; }
    mkdir -p "$(dirname "$target")"
    mode=$(stat -f %Lp "$source")
    install -m "$mode" -o root -g wheel "$source" "$target"
    [ "$(sha256 -q "$target")" = "$hash" ] || { echo "PRESTATE_FAIL hash $target" >&2; exit 1; }
done < /root/predecessor-paths.txt
# 2. The live pristine-catalogue archive, unchanged.
mkdir -p /var/backups/devicemonitor/core-locale
if [ -d /root/prestate/core-locale ]; then
    cp -Rp /root/prestate/core-locale/. /var/backups/devicemonitor/core-locale/ ||
        { echo 'PRESTATE_FAIL core-locale archive' >&2; exit 1; }
fi
# 3. Real historical leftovers. The first is unchanged and therefore prunable. The second
#    is a deliberately modified copy of published content and must be retained.
while read -r digest src target; do
    mkdir -p "$(dirname "$target")"
    install -m 644 -o root -g wheel "/root/predecessor-legacy/$src" "$target"
    [ "$(sha256 -q "$target")" = "$digest" ] || { echo "PRESTATE_FAIL legacy $target" >&2; exit 1; }
done < /root/legacy-prune.txt
while read -r digest src target; do
    mkdir -p "$(dirname "$target")"
    install -m 644 -o root -g wheel "/root/predecessor-legacy/$src" "$target"
    [ "$(sha256 -q "$target")" = "$digest" ] || { echo "PRESTATE_FAIL retained $target" >&2; exit 1; }
done < /root/legacy-retain.txt
# 4. Runtime data, the live record and the rc.d link.
mkdir -p /var/db/devicemonitor
for f in installed-manifest.txt devices.db config.json; do
    cp -p "/root/prestate/$f" "/var/db/devicemonitor/$f" ||
        { echo "PRESTATE_FAIL runtime $f" >&2; exit 1; }
done
rm -f /etc/rc.d/devicemonitor
ln -s "$(cat /root/prestate/rc-link)" /etc/rc.d/devicemonitor
echo PRESTATE_OK
PRESTATE
    [ "$rc" = 0 ] || { cat "$EVI/prestate.log" >&2; fail 'cannot build the pre-installation state'; }
    grep -q '^PRESTATE_OK$' "$EVI/prestate.log" || { cat "$EVI/prestate.log" >&2; fail 'prestate incomplete'; }
    pass "pre-installation state built from live $PREDECESSOR_VERSION targets, record and catalogue archive"
}

# A reproducible fingerprint of everything the installer is allowed to touch. Used to prove
# that --check does not mutate, and that a failed install restores the node exactly.
sb_snapshot() {
    sb_run "$STAGE_GLOB" > "$1" 2>&1 <<'SNAPSHOT'
stage_glob=$1
while read -r path; do
    [ -n "$path" ] || continue
    if [ -e "$path" ]; then printf '%s %s\n' "$path" "$(sha256 -q "$path")"
    else printf '%s ABSENT\n' "$path"; fi
done < /root/state-paths.txt
for p in /var/db/devicemonitor/installed-manifest.txt /var/db/devicemonitor/devices.db \
         /var/db/devicemonitor/config.json; do
    if [ -e "$p" ]; then printf '%s %s\n' "$p" "$(sha256 -q "$p")"
    else printf '%s ABSENT\n' "$p"; fi
done
printf 'RCLINK %s\n' "$(readlink /etc/rc.d/devicemonitor 2>/dev/null || echo absent)"
# One leading space per entry and nothing when the list is empty: the recorded snapshot must
# never carry trailing whitespace, so the evidence stays clean under `git diff --check`.
listing() {
    [ -d "$1" ] || return 0
    out=
    for entry in $(ls -1 "$1" 2>/dev/null | sort); do out="$out $entry"; done
    printf '%s' "$out"
}
printf 'BACKUPS%s\n' "$(listing /var/backups/devicemonitor)"
printf 'CORELOCALE%s\n' "$(listing /var/backups/devicemonitor/core-locale)"
find /var/backups/devicemonitor/core-locale -maxdepth 1 -type f -print 2>/dev/null | sort |
    while read -r p; do
        printf 'CORELOCALEFILE %s %s %s %s\n' "${p##*/}" "$(sha256 -q "$p")" \
            "$(stat -f %Lp "$p")" "$(stat -f %Su:%Sg "$p")"
    done
printf 'ETCINC %s\n' "$(cd /usr/local/etc/inc && find . -type f | sort | while read -r f; do sha256 -q "$f"; done | sha256 -q)"
printf 'STAGE %s\n' "$(find /tmp -maxdepth 1 -name "$(basename "$stage_glob")" -print 2>/dev/null | wc -l | tr -d ' ')"
printf 'NEWRECORD %s\n' "$(ls /var/db/devicemonitor/installed-manifest.txt.new 2>/dev/null | wc -l | tr -d ' ')"
SNAPSHOT
}

# Verifies the installed result the way a reviewer would: every expected target exists with
# the manifest mode and root:wheel ownership, and its content matches an independently
# recomputed digest (bundled source, freshly compiled catalogue, or a core catalogue that
# really carries the plugin strings) - not the installer's own accounting. The record, the
# rc.d link and the absence of staged leftovers are checked as well.
sb_verify_installed() {
    label=$1
    rc=0
    sb_run "release/v${VERSION}-runtime.manifest" "$VERSION" "$STAGE_GLOB" \
        > "$EVI/$label.log" 2>&1 <<'VERIFY' || rc=$?
manifest=$1
version=$2
stage_glob=$3
bad=0
report() { echo "VERIFY_FAIL $*"; bad=1; }
# 1. Content, mode and ownership of every expected target, recomputed from the bundle and
#    the independently derived locale plan.
while IFS="$(printf '\t')" read -r kind source target expected_mode; do
    [ -n "$target" ] || continue
    [ -f "$target" ] || { report "missing $target"; continue; }
    [ "$(stat -f %Su:%Sg "$target")" = root:wheel ] || report "owner $target $(stat -f %Su:%Sg "$target")"
    have_mode=$(stat -f %Lp "$target")
    [ "$have_mode" = "$expected_mode" ] || report "mode $target $have_mode != $expected_mode"
    case "$kind" in
        manifest)
            want=$(sha256 -q "/root/release/$source")
            [ "$(sha256 -q "$target")" = "$want" ] || report "content $target"
            ;;
        msgfmt)
            msgfmt -o /root/verify.mo "/root/release/$source" || { report "msgfmt $source"; continue; }
            want=$(sha256 -q /root/verify.mo); rm -f /root/verify.mo
            [ "$(sha256 -q "$target")" = "$want" ] || report "catalogue $target"
            ;;
        core)
            msgid=$(sed -n 's/^msgid "\(.*\)"$/\1/p' "/root/release/$source" | sed -n '2p')
            [ -n "$msgid" ] || { report "no msgid $source"; continue; }
            msgunfmt "$target" 2>/dev/null | grep -Fq -- "$msgid" || report "core merge $target"
            ;;
    esac
done < /root/expect.tsv
# 2. The record describes exactly this target set, with digests and the candidate version.
head -n 1 /var/db/devicemonitor/installed-manifest.txt |
    grep -Fq "# Device Monitor $version install record" || report 'record version header'
rows=$(grep -vc '^#' /var/db/devicemonitor/installed-manifest.txt || true)
want_rows=$(grep -c . /root/targets.txt)
[ "$rows" = "$want_rows" ] || report "record rows $rows != $want_rows"
while read -r path; do
    [ -n "$path" ] || continue
    grep -q "^[0-9a-f][0-9a-f]* $path$" /var/db/devicemonitor/installed-manifest.txt ||
        report "record path $path"
done < /root/targets.txt
while read -r digest path; do
    case "$digest" in '#'*) continue ;; esac
    [ -e "$path" ] || { report "record names absent $path"; continue; }
    [ "$(sha256 -q "$path")" = "$digest" ] || report "record digest $path"
done < /var/db/devicemonitor/installed-manifest.txt
# 3. Nothing left behind, the rc.d link is in place, and both About labels are wired to the
#    candidate's single version endpoint. This is a source/data-flow check, not a browser run.
left=$(find /tmp -maxdepth 1 -name "$(basename "$stage_glob")" -print 2>/dev/null | wc -l | tr -d ' ')
[ "$left" = 0 ] || report "staged temp directory left: $left"
[ "$(readlink /etc/rc.d/devicemonitor)" = /usr/local/etc/rc.d/devicemonitor ] || report 'rc.d link'
python3 /root/verify-about-endpoint.py "$version" || report 'About/Features endpoint binding'
echo "VERIFY_TARGETS=$want_rows"
[ "$bad" = 0 ]
VERIFY
    if [ "$rc" = 0 ]; then
        sed -n 's/^VERIFY_/  /p' "$EVI/$label.log"
        pass "$label"
    else
        grep '^VERIFY_FAIL' "$EVI/$label.log" >&2 || cat "$EVI/$label.log" >&2
        fail "$label"
    fi
}

# ------------------------------------------------------------------------------
# Scenario plumbing
# ------------------------------------------------------------------------------
sb_setup() {
    sb_build "$1"
    sb_stage_bundle
    sb_stage_prestate_inputs
    sb_stage_expectations
    sb_mount
    sb_start
    sb_prestate
}

# Runs the real installer inside the jail. Extra arguments are passed through, so the
# --check scenario uses the same entry point as a real run.
sb_install() {
    label=$1; shift
    rc=0
    sb_run "$SB_HOST" "$@" > "$EVI/$label.log" 2>&1 <<'INSTALL' || rc=$?
host=$1; shift
sh /root/release/install-unattended.sh --host "$host" "$@"
INSTALL
    return "$rc"
}

# Snapshot comparison: prints the paths whose digest differs between two snapshots.
# The backup-area listing is excluded on purpose: a failed install keeps its rollback
# directory (that is the evidence a rollback needs), so the comparison is about the
# installed state, and the caller checks the added directory separately.
sb_diff_snapshots() {
    diff "$1" "$2" | grep '^[<>]' | grep -Ev '^[<>] (BACKUPS|CORELOCALE)( |$)' || true
}

recorded() { # recorded <file> <pattern>
    grep -q -- "$2" "$1"
}

# ------------------------------------------------------------------------------
# Scenario: --check must not mutate anything (U3)
# ------------------------------------------------------------------------------
scenario_check() {
    sb_setup check
    sb_snapshot "$EVI/before.snapshot"
    rc=0
    sb_install install-check --check || rc=$?
    [ "$rc" = 0 ] || { cat "$EVI/install-check.log" >&2; fail "--check exited $rc"; }
    expected="CHECK_OK version=$VERSION predecessor=$PREDECESSOR_VERSION files=$EXPECTED_TARGETS core_locales=$EXPECTED_CORE_LOCALES prunable=1 daemon_running=0 host=$SB_HOST legacy_prunable=1 retained=1"
    grep -Fxq "$expected" "$EVI/install-check.log" ||
        { cat "$EVI/install-check.log" >&2; fail "CHECK_OK line unexpected; wanted: $expected"; }
    pass "--check reported the derived $EXPECTED_TARGETS-target candidate with prune=1 retain=1 and daemon_running=0"
    plans=$(grep -c '^PRUNE_PLAN=LEGACY ' "$EVI/install-check.log" || true)
    [ "$plans" = 1 ] ||
        { cat "$EVI/install-check.log" >&2; fail "the plan named $plans legacy leftovers, expected 1"; }
    recorded "$EVI/install-check.log" "^PRUNE_PLAN=LEGACY $LEGACY_PATH_ONE$" ||
        fail 'the unchanged published legacy path was not selected for pruning'
    recorded "$EVI/install-check.log" "^PRUNE_RETAINED modified $LEGACY_PATH_TWO$" ||
        fail 'the modified published legacy path was not reported as retained'
    pass 'the plan prunes the unchanged published leftover and retains the modified one'
    sb_snapshot "$EVI/after.snapshot"
    changed=$(sb_diff_snapshots "$EVI/before.snapshot" "$EVI/after.snapshot")
    [ -z "$changed" ] || { printf '%s\n' "$changed" >&2; fail '--check mutated the sandbox'; }
    pass '--check left every target, the record, the database and the backup area untouched'
    if grep '^BACKUPS ' "$EVI/after.snapshot" | grep -Fq "$BACKUP_PREFIX"; then
        grep '^BACKUPS ' "$EVI/after.snapshot" >&2
        fail 'a backup directory was created'
    fi
    pass "no /var/backups/devicemonitor/${BACKUP_PREFIX}* directory was created"
}

# ------------------------------------------------------------------------------
# Scenario: the real upgrade install, including the prune (M5 core acceptance)
# ------------------------------------------------------------------------------
scenario_install() {
    sb_setup install
    sb_snapshot "$EVI/before.snapshot"
    rc=0
    sb_install install || rc=$?
    [ "$rc" = 0 ] || { cat "$EVI/install.log" >&2; fail "installer exited $rc"; }
    line=$(grep '^INSTALL_OK ' "$EVI/install.log" || true)
    [ -n "$line" ] || { cat "$EVI/install.log" >&2; fail 'no INSTALL_OK line'; }
    say "  $line"
    printf '%s\n' "$line" | grep -Eq \
        '^INSTALL_OK version=2\.14\.0 files=63 core_locales=10 pruned=1 backup=/var/backups/devicemonitor/install-v214\.[^ ]+ daemon_restarted=0 unchanged=[0-9]+ repaired=0$' ||
        fail 'INSTALL_OK does not report the 2.14.0 payload, one prune and no daemon restart'
    pass 'INSTALL_OK version=2.14.0 files=63 core_locales=10 pruned=1 daemon_restarted=0 repaired=0'
    recorded "$EVI/install.log" '^PRUNED=1$' || fail 'the prune step did not report PRUNED=1'
    pass 'the prune step reported PRUNED=1'
    recorded "$EVI/install.log" '^BACKUP_READY=/var/backups/devicemonitor/install-v214\.' ||
        fail 'no rollback directory was reported'
    bdir=$(sed -n 's/^BACKUP_READY=//p' "$EVI/install.log")
    [ -n "$bdir" ] || fail 'cannot read BACKUP_READY'
    bfiles=$SCR/var/backups/devicemonitor/${bdir#/var/backups/devicemonitor/}
    preserved=$(cat "$bfiles"/files/prune-* 2>/dev/null | wc -c | tr -d ' ')
    [ "$preserved" -gt 0 ] || fail 'the pruned files were not preserved in the rollback directory'
    while read -r want src target; do
        found=0
        for f in "$bfiles"/files/prune-*; do
            [ -f "$f" ] || continue
            [ "$(sha256 -q "$f")" = "$want" ] && found=1 || :
        done
        [ "$found" = 1 ] || fail "the rollback directory does not preserve $target"
    done < "$SCR/root/legacy-prune.txt"
    pass "the pruned leftover is preserved digest-verified in $(basename "$bfiles")/files/prune-*"
    prune_target=$(awk '{print $3}' "$SCR/root/legacy-prune.txt")
    [ ! -e "$SCR/mvc.app.languages/$(basename "$prune_target")" ] ||
        fail "the unchanged legacy leftover $prune_target still exists"
    pass 'the unchanged legacy leftover was removed from the installed tree'
    while read -r want src target; do
        retained="$SCR/mvc.app.languages/$(basename "$target")"
        [ -f "$retained" ] || fail "the modified legacy leftover $target was removed"
        [ "$(sha256 -q "$retained")" = "$want" ] ||
            fail "the modified legacy leftover $target changed during the install"
    done < "$SCR/root/legacy-retain.txt"
    pass 'the modified legacy leftover was retained byte-identically'
    sb_verify_installed install-verify
    sb_snapshot "$EVI/after.snapshot"
    for p in devices.db config.json; do
        a=$(grep "^/var/db/devicemonitor/$p " "$EVI/before.snapshot" || true)
        b=$(grep "^/var/db/devicemonitor/$p " "$EVI/after.snapshot" || true)
        [ -n "$a" ] && [ "$a" = "$b" ] || fail "/var/db/devicemonitor/$p changed: [$a] -> [$b]"
    done
    pass 'devices.db and config.json are byte-identical after the install'
    awk 'NR==FNR { want[$0]=1; next } ($1 in want) { print }' \
        "$SCR/root/targets.txt" "$EVI/before.snapshot" | sort > "$EVI/before.targets"
    awk 'NR==FNR { want[$0]=1; next } ($1 in want) { print }' \
        "$SCR/root/targets.txt" "$EVI/after.snapshot" | sort > "$EVI/after.targets"
    same=$(comm -12 "$EVI/before.targets" "$EVI/after.targets" | wc -l | tr -d ' ')
    reported=$(printf '%s\n' "$line" | sed -n 's/.*unchanged=\([0-9]*\).*/\1/p')
    [ "$reported" = "$same" ] ||
        fail "unchanged=$reported does not match the $same targets whose content is identical"
    pass "unchanged=$reported matches the $same byte-identical targets of $(grep -c . "$SCR/root/targets.txt")"
    states=$(ls "$SCR/var/backups/devicemonitor/core-locale" | grep -c '\.state$' || true)
    [ "$states" = "$EXPECTED_CORE_LOCALES" ] ||
        fail "core-locale state files $states != $EXPECTED_CORE_LOCALES"
    pass "the pristine core catalogues were preserved ($EXPECTED_CORE_LOCALES locales)"
}

# Plants the state a later upgrade produces when a language is dropped: a compiled catalogue
# for a locale the current release no longer ships, named by the digest-bearing record that
# the first 2.14.0 install wrote. This is finding #2 of the pruning review in executable form.
sb_plant_dropped_language() {
    sb_run > "$EVI/plant.log" 2>&1 <<'PLANT' || { cat "$EVI/plant.log" >&2; fail 'cannot plant the dropped-language state'; }
dir=/usr/local/opnsense/mvc/app/languages/xx_XX/LC_MESSAGES
mkdir -p "$dir"
cp /usr/local/opnsense/mvc/app/languages/cs_CZ/LC_MESSAGES/devicemonitor.mo "$dir/devicemonitor.mo"
chmod 644 "$dir/devicemonitor.mo"
printf '%s %s\n' "$(sha256 -q "$dir/devicemonitor.mo")" "$dir/devicemonitor.mo" \
    >> /var/db/devicemonitor/installed-manifest.txt
echo "PLANTED $dir/devicemonitor.mo"
PLANT
    pass 'planted a compiled catalogue for a dropped locale, named by digest in the record'
}

# The pristine-catalogue archive is deliberately first-write-wins. This check proves each
# stored pristine copy still matches the digest recorded in its state file; the rollback
# scenario separately compares the complete archive against its pre-install snapshot.
sb_verify_core_locale_archive() {
    label=$1
    rc=0
    sb_run "$EXPECTED_CORE_LOCALES" > "$EVI/core-locale.log" 2>&1 <<'CORELOCALE' || rc=$?
expected=$1
bad=0
archive=/var/backups/devicemonitor/core-locale
for state in /var/backups/devicemonitor/core-locale/*.state; do
    [ -f "$state" ] || continue
    lang=$(basename "$state" .state)
    pristine=$(sed -n 's/^pristine=//p' "$state")
    target=$(sed -n 's/^target=//p' "$state")
    [ -n "$target" ] || { echo "VERIFY_FAIL state $lang"; bad=1; continue; }
    copy="$archive/$lang.OPNsense.mo"
    if [ "$pristine" = absent ]; then
        [ ! -e "$copy" ] || { echo "VERIFY_FAIL unexpected pristine copy $copy"; bad=1; }
    elif [ ! -f "$copy" ]; then
        echo "VERIFY_FAIL missing pristine copy $copy"; bad=1
    elif [ "$(sha256 -q "$copy")" != "$pristine" ]; then
        echo "VERIFY_FAIL pristine copy $copy"; bad=1
    fi
done
count=$(ls /var/backups/devicemonitor/core-locale/*.state 2>/dev/null | wc -l | tr -d ' ')
[ "$count" = "$expected" ] || { echo "VERIFY_FAIL state count $count != $expected"; bad=1; }
echo "VERIFY_CORE_LOCALE=$count"
[ "$bad" = 0 ]
CORELOCALE
    if [ "$rc" = 0 ]; then
        sed -n 's/^VERIFY_/  /p' "$EVI/core-locale.log"
        pass "$label"
    else
        grep '^VERIFY_FAIL' "$EVI/core-locale.log" >&2 || cat "$EVI/core-locale.log" >&2
        fail "$label"
    fi
}

# Verifies that a pruned path has been put back exactly: present, correct content.
sb_verify_restored_path() {
    label=$1; path=$2; digest=$3
    rc=0
    sb_run "$path" "$digest" > "$EVI/restored.log" 2>&1 <<'RESTORED' || rc=$?
path=$1
digest=$2
[ -f "$path" ] || { echo "VERIFY_FAIL absent $path"; exit 1; }
[ "$(sha256 -q "$path")" = "$digest" ] || { echo "VERIFY_FAIL digest $path"; exit 1; }
echo "VERIFY_RESTORED=$path"
RESTORED
    if [ "$rc" = 0 ]; then
        sed -n 's/^VERIFY_/  /p' "$EVI/restored.log"
        pass "$label"
    else
        grep '^VERIFY_FAIL' "$EVI/restored.log" >&2 || cat "$EVI/restored.log" >&2
        fail "$label"
    fi
}

# ------------------------------------------------------------------------------
# Scenario: same-version repair with a record-driven prune (U5 arithmetic, finding #2)
# ------------------------------------------------------------------------------
scenario_repair() {
    sb_setup repair
    rc=0
    sb_install first || rc=$?
    [ "$rc" = 0 ] || { cat "$EVI/first.log" >&2; fail "first install exited $rc"; }
    grep -q '^INSTALL_OK ' "$EVI/first.log" || fail 'the first install did not report INSTALL_OK'
    sb_plant_dropped_language
    sb_snapshot "$EVI/before.snapshot"
    rc=0
    sb_install repair || rc=$?
    [ "$rc" = 0 ] || { cat "$EVI/repair.log" >&2; fail "repair install exited $rc"; }
    line=$(grep '^INSTALL_OK ' "$EVI/repair.log" || true)
    say "  $line"
    printf '%s\n' "$line" | grep -Eq \
        '^INSTALL_OK version=2\.14\.0 files=63 core_locales=10 pruned=1 backup=/var/backups/devicemonitor/install-v214\.[^ ]+ daemon_restarted=0 unchanged=63 repaired=0$' ||
        fail 'the repair did not report the 2.14.0 payload with one prune and unchanged=63'
    pass 'the repair reported unchanged=63 repaired=0 with pruned=1'
    recorded "$EVI/repair.log" \
        '^PRUNE_PLAN=RECORD /usr/local/opnsense/mvc/app/languages/xx_XX/LC_MESSAGES/devicemonitor.mo$' ||
        { cat "$EVI/repair.log" >&2; fail 'the dropped catalogue was not planned from the record'; }
    pass 'the dropped catalogue was planned from the install record, not from a manifest diff'
    [ -e "$SCR/mvc.app.languages/xx_XX/LC_MESSAGES/devicemonitor.mo" ] &&
        fail 'the dropped catalogue still exists'
    pass 'the dropped catalogue was removed'
    sb_verify_installed repair-verify
}

# ------------------------------------------------------------------------------
# Scenario: an injected failure after the prune must roll the node back exactly (U2, U6)
#
# This is the deployment-shaped case: a 2.13.3 node with one unchanged and one modified
# published leftover runs the real upgrade, the unchanged leftover is pruned, the next step
# fails, and the installer's own abort path has to restore every target and the record.
# ------------------------------------------------------------------------------
scenario_rollback() {
    sb_setup rollback
    sb_snapshot "$EVI/before.snapshot"
    # The failure is injected at `service configd restart', the first step after the prune,
    # through the sandbox's configd stub: the installer's own abort path then runs.
    sb_run > /dev/null 2>&1 <<'ARM'
: > /.dm-fail-configd
ARM
    rc=0
    sb_install failing || rc=$?
    [ "$rc" -ne 0 ] || { cat "$EVI/failing.log" >&2; fail 'the injected failure did not abort the install'; }
    pass "the install aborted with exit $rc after the failure injection"
    recorded "$EVI/failing.log" '^ROLLBACK_ATTEMPTED=/var/backups/devicemonitor/install-v214\.' ||
        { cat "$EVI/failing.log" >&2; fail 'no ROLLBACK_ATTEMPTED line'; }
    recorded "$EVI/failing.log" '^ROLLBACK_STATUS=COMPLETE$' ||
        { cat "$EVI/failing.log" >&2; fail 'the rollback did not report COMPLETE'; }
    pass 'the installer reported ROLLBACK_STATUS=COMPLETE'
    recorded "$EVI/failing.log" '^PRUNED=1$' || fail 'the prune step did not run before the failure'
    pass 'the unchanged leftover had already been pruned when the failure was injected'
    summaries=$(sed -n 's/^ROLLBACK_SUMMARY=//p' "$EVI/failing.log")
    summary_count=$(printf '%s\n' "$summaries" | grep -c .)
    [ "$summary_count" = 2 ] || fail "expected two rollback summaries, got $summary_count"
    targets_summary=$(printf '%s\n' "$summaries" | sed -n '1p')
    prune_summary=$(printf '%s\n' "$summaries" | sed -n '2p')
    printf '%s\n' "$targets_summary" | grep -Eq '^restored=[0-9]+ skipped=[0-9]+ conflicts=0 failed=0$' ||
        fail "restore-targets did not complete cleanly: $targets_summary"
    restored=$(printf '%s\n' "$targets_summary" | sed -n 's/^restored=\([0-9]*\).*/\1/p')
    skipped=$(printf '%s\n' "$targets_summary" | sed -n 's/.*skipped=\([0-9]*\).*/\1/p')
    [ "$((restored + skipped))" = "$EXPECTED_TARGETS" ] ||
        fail "restore-targets accounted for $((restored + skipped)) of $EXPECTED_TARGETS targets"
    pass "all $EXPECTED_TARGETS targets were restored or already identical"
    [ "$prune_summary" = 'restored=1 skipped=0 conflicts=0 failed=0' ] ||
        fail "the prune rollback did not complete cleanly: $prune_summary"
    pass 'the pruned leftover was restored by the digest-verified prune rollback'
    core_files=$(grep -c '^CORELOCALEFILE ' "$EVI/before.snapshot" || true)
    recorded "$EVI/failing.log" \
        "^CORE_LOCALE_ROLLBACK_SUMMARY=restored=$core_files removed=0 conflicts=0 failed=0$" ||
        fail 'the core-locale state rollback did not complete cleanly'
    pass "all $core_files core-locale state and pristine files were restored exactly"
    sb_snapshot "$EVI/after.snapshot"
    changed=$(sb_diff_snapshots "$EVI/before.snapshot" "$EVI/after.snapshot")
    [ -z "$changed" ] || { printf '%s\n' "$changed" >&2; fail 'the rollback did not restore the pre-install state'; }
    pass 'every target, the record, the database and the backup area match the pre-install state'
    before_dirs=$(printf '%s' "$(sed -n 's/^BACKUPS //p' "$EVI/before.snapshot")" | wc -w | tr -d ' ')
    after_dirs=$(printf '%s' "$(sed -n 's/^BACKUPS //p' "$EVI/after.snapshot")" | wc -w | tr -d ' ')
    [ "$after_dirs" = "$((before_dirs + 1))" ] ||
        fail "the failed run left $((after_dirs - before_dirs)) rollback directories, expected 1"
    pass 'exactly one rollback directory remains, holding the pre-install copies'
    recorded "$EVI/after.snapshot" '^NEWRECORD 0$' || fail 'a half-written record was left behind'
    pass 'no installed-manifest.txt.new was left behind by the failed run'
    sb_verify_core_locale_archive 'the pristine catalogue archive matches the restored catalogues'
    replaced=/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json
    replaced_digest=$(awk -v p="$replaced" '$1 == p { print $2 }' "$EVI/before.snapshot")
    [ -n "$replaced_digest" ] || fail 'cannot read the pre-install digest of defaults.json'
    sb_verify_restored_path 'the replaced target was restored byte-identically' "$replaced" "$replaced_digest"
    while read -r digest src target; do
        sb_verify_restored_path "the pruned leftover $target was restored digest-verified" "$target" "$digest"
    done < "$SCR/root/legacy-prune.txt"
    sb_run > /dev/null 2>&1 <<'DISARM'
rm -f /.dm-fail-configd
DISARM
}

# ------------------------------------------------------------------------------
# Scenario: a tampered helper must abort before any mutation (U7, L8)
# ------------------------------------------------------------------------------
scenario_failclosed() {
    sb_setup failclosed
    sb_snapshot "$EVI/before.snapshot"
    sb_run > "$EVI/tamper.log" 2>&1 <<'TAMPER' || { cat "$EVI/tamper.log" >&2; fail 'cannot tamper with the helper'; }
printf '\n# tampered by the sandbox harness\n' >> /root/release/release/prune-plan.sh
echo TAMPERED
TAMPER
    rc=0
    sb_install tampered || rc=$?
    [ "$rc" -ne 0 ] || { cat "$EVI/tampered.log" >&2; fail 'the installer accepted a tampered helper'; }
    recorded "$EVI/tampered.log" '^ABORT: release inputs$' ||
        { cat "$EVI/tampered.log" >&2; fail 'the abort was not the pinned-input refusal'; }
    pass 'a tampered prune helper was refused by the pinned-input check'
    recorded "$EVI/tampered.log" '^INSTALL_OK' && fail 'the installer reported success' || :
    sb_snapshot "$EVI/after.snapshot"
    changed=$(sb_diff_snapshots "$EVI/before.snapshot" "$EVI/after.snapshot")
    [ -z "$changed" ] || { printf '%s\n' "$changed" >&2; fail 'the refused run still mutated the sandbox'; }
    pass 'the refused run mutated nothing (no replacement, no prune, no record)'
}

# ------------------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------------------
usage() {
    cat <<'USAGE'
usage: run-installer-sandbox.sh <command>

  all                  run every scenario (check, install, repair, rollback, failclosed)
  scenario <name>      run one scenario
  keep                 run nothing; report the sandbox work directory
  clean                remove the work directory and any leftover mounts/jails

Environment:
  DM_SANDBOX_WORK      work directory (default /var/tmp/dm-installer-sandbox)
  DM_SANDBOX_BUNDLE    explicit candidate bundle (default is the v2.14.0 candidate copy)
  DM_SANDBOX_SAVE      set to 1 to copy transcripts into evidence-<version>/
USAGE
    exit 2
}

save_evidence() {
    [ "${DM_SANDBOX_SAVE:-0}" = 1 ] || return 0
    dest=$EVIDENCE_ROOT/$CURRENT
    # The destination is replaced, never merged: evidence from an earlier version of a
    # scenario must not survive alongside the current run's transcripts.
    rm -rf "$dest"
    mkdir -p "$dest"
    for f in "$EVI"/*; do
        [ -f "$f" ] && cp "$f" "$dest/" || :
    done
    say "SANDBOX_EVIDENCE $dest"
}

run_one() {
    name=$1
    say "=== scenario $name ==="
    rc=0
    pipeline_rc=0
    (
        trap '_trap_rc=$?; sb_teardown || { [ "$_trap_rc" -ne 0 ] || _trap_rc=1; : > "$WORK/abort"; }; assert_sandbox_clean || { [ "$_trap_rc" -ne 0 ] || _trap_rc=1; : > "$WORK/abort"; }; assert_live_unchanged || { [ "$_trap_rc" -ne 0 ] || _trap_rc=1; : > "$WORK/abort"; }; save_evidence || { [ "$_trap_rc" -ne 0 ] || _trap_rc=1; }; printf "%s\n" "$_trap_rc" > "$WORK/exit-$name"; exit "$_trap_rc"' EXIT INT TERM
        "scenario_$name"
        printf '%s\n' "$name" > "$WORK/status-$name"
    ) 2>&1 | tee "$WORK/transcript-$name.log" || pipeline_rc=$?
    if [ -f "$WORK/exit-$name" ]; then
        rc=$(cat "$WORK/exit-$name")
    else
        rc=1
    fi
    [ "$pipeline_rc" = 0 ] || rc=1
    if [ "$rc" = 0 ] && [ -f "$WORK/status-$name" ]; then
        say "SANDBOX_SCENARIO $name PASS"
    else
        say "SANDBOX_SCENARIO $name FAIL exit=$rc"
        FAILED=$((FAILED + 1))
    fi
}

clean_all() {
    sb_stop
    # Remove every sandbox that a previous run left behind, unmounting in reverse order.
    for base in "$WORK"/*; do
        [ -d "$base" ] || continue
        MNT_LIST=$base/mounts
        sb_umount
    done
    rm -rf "$WORK"
    say "SANDBOX_CLEAN removed $WORK"
}

main() {
    cmd=${1:-}
    [ -n "$cmd" ] || usage
    case "$cmd" in
        all|scenario|clean) : ;;
        keep) say "SANDBOX_WORK $WORK"; exit 0 ;;
        *) usage ;;
    esac
    require_host
    if [ "$cmd" = clean ]; then clean_all; exit 0; fi
    mkdir -p "$WORK"
    rm -f "$WORK"/status-* "$WORK"/exit-*
    rm -f "$WORK/abort"
    live_fingerprint "$WORK/live-before.fingerprint"
    if [ "$cmd" = all ]; then
        for s in check install repair rollback failclosed; do
            run_one "$s"
            [ ! -f "$WORK/abort" ] || break
        done
    else
        [ "$#" = 2 ] || usage
        run_one "$2"
    fi
    say "SANDBOX_SUMMARY failures=$FAILED work=$WORK"
    [ "$FAILED" = 0 ] || exit 1
    say 'SANDBOX_RESULT=PASS'
}

main "$@"
