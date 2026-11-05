#!/bin/sh
# ==============================================================================
# Device Monitor — M5 installer sandbox harness.
#
# Review item M5 (verification/REVIEW-R2-REMEDIATION-20261103.md) is that no test
# ever executed install-unattended.sh: the installer's own wiring was asserted
# textually, and every executable check stopped at release/prune-plan.sh.
#
# This harness executes the real, unmodified installer — the byte-identical
# artifact from release/build-bundle.sh — inside a disposable FreeBSD jail:
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
# `--host` is satisfied by the sandbox hostname; nothing else is stubbed except
# `service configd', which is an OPNsense host service and not part of the
# payload: the stub records the call and doubles as the failure-injection point.
#
# Usage (on the Device Monitor testbed, as root):
#   sh verification/installer-sandbox/run-installer-sandbox.sh all
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
JAIL=dm-m5-sandbox
SB_HOST=dm-m5-sandbox.internal
MARKER=.dm-sandbox-marker
VERSION=2.13.3
PREDECESSOR_TAG=v2.13.2
BUNDLE_DIGEST=7f389248707cf8fa0684760820db85c0fddac4b8b3964e0563318b38b2730fe2
LANGS='en_US cs_CZ de_DE fr_FR es_ES it_IT pt_BR nl_NL ru_RU ja_JP zh_CN'
# Legacy ownership evidence rows used to plant real historical leftovers: the v2.9 flat-layout
# catalogues, which no current release installs and whose digests are published in
# release/legacy-targets.txt (the per-locale LC_MESSAGES layout replaced them).
LEGACY_TAG=v2.9
LEGACY_COUNT=2
LEGACY_SRC_ONE=src/opnsense/mvc/app/languages/cs_CZ_devicemonitor.po
LEGACY_SRC_TWO=src/opnsense/mvc/app/languages/en_US_devicemonitor.po

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
    for t in tar msgfmt python3 sha256; do
        command -v "$t" >/dev/null 2>&1 || fail "$t is required"
    done
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
    for d in bin sbin lib libexec usr etc dev proc tmp var root; do mkdir -p "$ROOT/$d"; done
    for d in etc.rc.d etc.rc.conf.d var tmp root usr.local.etc.inc usr.local.etc.rc.d \
             mvc.app.languages mvc.app.models mvc.app.controllers mvc.app.views \
             scripts.dm service.actions.d www.js.widgets share.locale; do
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
}

sb_mount() {
    for d in bin sbin lib libexec usr etc; do
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
    lines=$(wc -l < "$MNT_LIST" | tr -d ' ')
    while [ "$lines" -gt 0 ]; do
        point=$(sed -n "${lines}p" "$MNT_LIST")
        umount "$point" 2>/dev/null || umount -f "$point" 2>/dev/null || :
        lines=$((lines - 1))
    done
    : > "$MNT_LIST"
}

sb_start() {
    /usr/sbin/jail -c name="$JAIL" path="$ROOT" host.hostname="$SB_HOST" persist \
        || fail 'cannot start the sandbox jail'
    /usr/sbin/jexec "$JAIL" /bin/sh -c \
        "test -f /$MARKER && test \"\$(hostname)\" = \"$SB_HOST\" && test \"\$(id -u)\" = 0" \
        || { sb_stop; fail 'sandbox identity check failed, installer not run'; }
}

sb_stop() {
    /usr/sbin/jail -r "$JAIL" >/dev/null 2>&1 || :
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
    sb_stop
    sb_umount
}

# ------------------------------------------------------------------------------
# Staging: the artifact under test, the predecessor tree, the expected target set
# ------------------------------------------------------------------------------

# Builds the release bundle from the current checkout and proves it is the published
# identity before anything is installed. DM_SANDBOX_BUNDLE=<file> reuses an existing
# archive instead of rebuilding it.
sb_stage_bundle() {
    out=$BASE/bundle.tar.gz
    if [ -n "${DM_SANDBOX_BUNDLE:-}" ]; then
        cp "$DM_SANDBOX_BUNDLE" "$out" || fail 'cannot copy DM_SANDBOX_BUNDLE'
        say "SANDBOX_BUNDLE source=$DM_SANDBOX_BUNDLE"
    else
        rm -rf "$BASE/stage"
        DM_BUNDLE_OUT=$out DM_BUNDLE_STAGE=$BASE/stage DM_BUNDLE_LIST=$BASE/bundle-list.txt \
            sh "$REPO/release/build-bundle.sh" > "$EVI/bundle-build.log" 2>&1 ||
            { cat "$EVI/bundle-build.log" >&2; fail 'bundle build failed'; }
        say "SANDBOX_BUNDLE source=release/build-bundle.sh"
    fi
    digest=$(sha256 -q "$out")
    [ "$digest" = "$BUNDLE_DIGEST" ] || fail "bundle digest $digest is not the published $BUNDLE_DIGEST"
    say "SANDBOX_BUNDLE sha256=$digest bytes=$(stat -f %z "$out")"
    mkdir -p "$SCR/root/release"
    tar -xzf "$out" -C "$SCR/root/release" || fail 'cannot extract the bundle'
}

# The exact pre-installation state: the v2.13.2 tree, a real historical leftover that the
# published legacy evidence owns, and the runtime data observed on the testbed.
sb_stage_prestate_inputs() {
    mkdir -p "$SCR/root/predecessor"
    git -C "$REPO" archive --format=tar "$PREDECESSOR_TAG" | tar -xf - -C "$SCR/root/predecessor" ||
        fail "cannot extract $PREDECESSOR_TAG"
    mkdir -p "$SCR/root/predecessor-legacy"
    git -C "$REPO" archive --format=tar "$LEGACY_TAG" "$LEGACY_SRC_ONE" "$LEGACY_SRC_TWO" |
        tar -xf - -C "$SCR/root/predecessor-legacy" || fail "cannot extract $LEGACY_TAG"
    cat > "$SCR/root/legacy.txt" <<'LEGACY'
f0760cb914df2ff38bc8fc207a4468c1877970b8a63f0d46bdb5efa0d8a0fcf0 src/opnsense/mvc/app/languages/cs_CZ_devicemonitor.po /usr/local/opnsense/mvc/app/languages/cs_CZ_devicemonitor.po
2dc80ccd1e297d02722ba4235c1d48a187b0d670c6ae9dd067671cc9e8bf60df src/opnsense/mvc/app/languages/en_US_devicemonitor.po /usr/local/opnsense/mvc/app/languages/en_US_devicemonitor.po
LEGACY
    while read -r want src target; do
        got=$(sha256 -q "$SCR/root/predecessor-legacy/$src")
        [ "$got" = "$want" ] || fail "legacy leftover $target digest $got is not the published $want"
        grep -qx "$want $target" "$REPO/release/legacy-targets.txt" ||
            fail "$want $target is not published ownership evidence"
    done < "$SCR/root/legacy.txt"
    mkdir -p "$SCR/root/prestate"
    # The 2.13.2-era record, database and configuration observed on the testbed, copied in
    # so the sandbox starts from the same shape of state the field node has.
    for f in installed-manifest.txt devices.db config.json; do
        if [ -e "/var/db/devicemonitor/$f" ]; then
            cp -p "/var/db/devicemonitor/$f" "$SCR/root/prestate/$f" || fail "cannot stage $f"
        fi
    done
    say "SANDBOX_PRESTATE record_rows=$(grep -c . "$SCR/root/prestate/installed-manifest.txt")"
}

# The expected target set, derived from the manifest and the locale list, plus a plan of how
# each target's digest is to be verified independently of the installer's own accounting.
sb_stage_expectations() {
    : > "$SCR/root/targets.txt"
    : > "$SCR/root/expect.tsv"
    while read -r hash mode source target; do
        printf '%s\n' "$target" >> "$SCR/root/targets.txt"
        printf 'manifest\t%s\t%s\n' "$source" "$target" >> "$SCR/root/expect.tsv"
    done < "$REPO/release/v${VERSION}-runtime.manifest"
    for lang in $LANGS; do
        po="src/opnsense/mvc/app/languages/${lang}/LC_MESSAGES/devicemonitor.po"
        mo="/usr/local/opnsense/mvc/app/languages/${lang}/LC_MESSAGES/devicemonitor.mo"
        printf '%s\n' "$mo" >> "$SCR/root/targets.txt"
        printf 'msgfmt\t%s\t%s\n' "$po" "$mo" >> "$SCR/root/expect.tsv"
        [ "$lang" = en_US ] && continue
        core="/usr/local/share/locale/${lang}/LC_MESSAGES/OPNsense.mo"
        printf '%s\n' "$core" >> "$SCR/root/targets.txt"
        printf 'core\t%s\t%s\n' "$po" "$core" >> "$SCR/root/expect.tsv"
    done
    say "SANDBOX_EXPECT targets=$(grep -c . "$SCR/root/targets.txt")"
}

# ------------------------------------------------------------------------------
# Pre-installation state (runs inside the jail, against the real absolute paths)
# ------------------------------------------------------------------------------
sb_prestate() {
    rc=0
    sb_run "$LANGS" > "$EVI/prestate.log" 2>&1 <<'PRESTATE' || rc=$?
langs=$1
# 1. The 40 targets the 2.13.2 manifest declares, at the modes it declares.
while read -r hash mode source target; do
    mkdir -p "$(dirname "$target")"
    install -m "$mode" -o root -g wheel "/root/predecessor/$source" "$target"
    [ "$(sha256 -q "$target")" = "$hash" ] || { echo "PRESTATE_FAIL hash $target" >&2; exit 1; }
done < /root/predecessor/release/v2.13.2-runtime.manifest
# 2. The compiled catalogues and the merged core catalogues, as the 2.13.2 installer builds
#    them. The merge helper is 2.13.2-era code, so the pristine state is era-faithful.
for lang in $langs; do
    po="/root/predecessor/src/opnsense/mvc/app/languages/${lang}/LC_MESSAGES/devicemonitor.po"
    mo="/usr/local/opnsense/mvc/app/languages/${lang}/LC_MESSAGES/devicemonitor.mo"
    mkdir -p "$(dirname "$mo")"
    msgfmt --check -o "$mo" "$po" || { echo "PRESTATE_FAIL msgfmt $lang" >&2; exit 1; }
    [ "$lang" = en_US ] && continue
    core="/usr/local/share/locale/${lang}/LC_MESSAGES/OPNsense.mo"
    mkdir -p "$(dirname "$core")"
    if [ -f "$core" ]; then
        sh /root/predecessor/release/merge-opnsense-catalog.sh "$core" "$po" /root/core.mo ||
            { echo "PRESTATE_FAIL merge $lang" >&2; exit 1; }
        mode=$(stat -f %Lp "$core")
    else
        sh /root/predecessor/release/merge-opnsense-catalog.sh --plugin-only "$po" /root/core.mo ||
            { echo "PRESTATE_FAIL plugin-only $lang" >&2; exit 1; }
        mode=644
    fi
    install -m "$mode" -o root -g wheel /root/core.mo "$core"
    rm -f /root/core.mo
done
# 3. Real historical leftovers: unchanged content from a published release that no current
#    release installs. release/legacy-targets.txt owns these digests, so the plan may prune
#    them, and nothing else in the tree qualifies.
while read -r digest src target; do
    mkdir -p "$(dirname "$target")"
    install -m 644 -o root -g wheel "/root/predecessor-legacy/$src" "$target"
    [ "$(sha256 -q "$target")" = "$digest" ] || { echo "PRESTATE_FAIL legacy $target" >&2; exit 1; }
done < /root/legacy.txt
# 4. Runtime data and the 2.13.2-era record.
mkdir -p /var/db/devicemonitor
for f in installed-manifest.txt devices.db config.json; do
    [ -f "/root/prestate/$f" ] && cp -p "/root/prestate/$f" "/var/db/devicemonitor/$f"
done
mkdir -p /var/backups/devicemonitor/core-locale
echo PRESTATE_OK
PRESTATE
    [ "$rc" = 0 ] || { cat "$EVI/prestate.log" >&2; fail 'cannot build the pre-installation state'; }
    grep -q '^PRESTATE_OK$' "$EVI/prestate.log" || { cat "$EVI/prestate.log" >&2; fail 'prestate incomplete'; }
    pass 'pre-installation state built (2.13.2 payload, catalogues, legacy leftover, record)'
}

# A reproducible fingerprint of everything the installer is allowed to touch. Used to prove
# that --check does not mutate, and that a failed install restores the node exactly.
sb_snapshot() {
    sb_run > "$1" 2>&1 <<'SNAPSHOT'
while read -r path; do
    [ -n "$path" ] || continue
    if [ -e "$path" ]; then printf '%s %s\n' "$path" "$(sha256 -q "$path")"
    else printf '%s ABSENT\n' "$path"; fi
done < /root/targets.txt
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
printf 'ETCINC %s\n' "$(cd /usr/local/etc/inc && find . -type f | sort | while read -r f; do sha256 -q "$f"; done | sha256 -q)"
printf 'STAGE %s\n' "$(ls -d /tmp/dm_install_v213.* 2>/dev/null | wc -l | tr -d ' ')"
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
    sb_run "release/v${VERSION}-runtime.manifest" > "$EVI/$label.log" 2>&1 <<'VERIFY' || rc=$?
manifest=$1
bad=0
report() { echo "VERIFY_FAIL $*"; bad=1; }
# 1. Content of every expected target, recomputed from the bundle.
while IFS="$(printf '\t')" read -r kind source target; do
    [ -n "$target" ] || continue
    [ -f "$target" ] || { report "missing $target"; continue; }
    [ "$(stat -f %Su:%Sg "$target")" = root:wheel ] || report "owner $target $(stat -f %Su:%Sg "$target")"
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
# 2. Modes the manifest declares.
while read -r hash mode source target; do
    [ -f "$target" ] || { report "missing $target"; continue; }
    have=$(stat -f %Lp "$target")
    [ "$have" = "$mode" ] || report "mode $target $have != $mode"
done < "/root/release/$manifest"
# 3. The record describes exactly this target set, with digests.
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
# 4. Nothing left behind, and the rc.d link is in place.
left=$(ls -d /tmp/dm_install_v213.* 2>/dev/null | wc -l | tr -d ' ')
[ "$left" = 0 ] || report "staged temp directory left: $left"
[ "$(readlink /etc/rc.d/devicemonitor)" = /usr/local/etc/rc.d/devicemonitor ] || report 'rc.d link'
echo "VERIFY_TARGETS=$want_rows"
[ "$bad" = 0 ]
VERIFY
    if [ "$rc" = 0 ]; then
        sed -n 's/^VERIFY_/  /p' "$EVI/$label.log"
        pass "$label"
    else
        grep '^VERIFY_FAIL' "$EVI/$label.log" >&2 || cat "$EVI/$label.log" >&2
        printf 'SANDBOX_FAIL: %s\n' "$label" >&2
        FAILED=$((FAILED + 1))
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
    diff "$1" "$2" | grep '^[<>]' | grep -v '^[<>] BACKUPS' | grep -v '^[<>] CORELOCALE' || true
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
    recorded "$EVI/install-check.log" \
        '^CHECK_OK version=2.13.3 predecessor=2.13.2 files=61 core_locales=10 prunable=2 daemon_running=0 host=dm-m5-sandbox.internal legacy_prunable=2 retained=0$' ||
        { cat "$EVI/install-check.log" >&2; fail 'CHECK_OK line unexpected'; }
    pass '--check reported CHECK_OK version=2.13.3 predecessor=2.13.2 files=61 core_locales=10 prunable=2 legacy_prunable=2 retained=0'
    plans=$(grep -c '^PRUNE_PLAN=LEGACY ' "$EVI/install-check.log" || true)
    [ "$plans" = "$LEGACY_COUNT" ] ||
        { cat "$EVI/install-check.log" >&2; fail "the plan named $plans legacy leftovers, expected $LEGACY_COUNT"; }
    pass "the plan named exactly the $LEGACY_COUNT published legacy leftovers"
    sb_snapshot "$EVI/after.snapshot"
    changed=$(sb_diff_snapshots "$EVI/before.snapshot" "$EVI/after.snapshot")
    [ -z "$changed" ] || { printf '%s\n' "$changed" >&2; fail '--check mutated the sandbox'; }
    pass '--check left every target, the record, the database and the backup area untouched'
    if grep -q '^BACKUPS .*install-v213\.' "$EVI/after.snapshot"; then
        grep '^BACKUPS ' "$EVI/after.snapshot" >&2
        fail 'a backup directory was created'
    fi
    pass 'no /var/backups/devicemonitor/install-v213.* created'
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
    printf '%s\n' "$line" | grep -q '^INSTALL_OK version=2.13.3 files=61 core_locales=10 pruned=2 ' ||
        fail 'INSTALL_OK does not report the 2.13.3 payload with both leftovers pruned'
    printf '%s\n' "$line" | grep -q 'daemon_restarted=0 unchanged=[0-9]* repaired=0$' ||
        fail 'INSTALL_OK reports a daemon restart, a repair, or no unchanged accounting'
    pass 'INSTALL_OK version=2.13.3 files=61 core_locales=10 pruned=2 daemon_restarted=0 repaired=0'
    recorded "$EVI/install.log" '^PRUNED=2$' || fail 'the prune step did not report PRUNED=2'
    pass 'the prune step reported PRUNED=2'
    recorded "$EVI/install.log" '^BACKUP_READY=/var/backups/devicemonitor/install-v213\.' ||
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
    done < "$SCR/root/legacy.txt"
    pass "both pruned leftovers are preserved digest-verified in $(basename "$bfiles")/files/prune-*"
    while read -r want src target; do
        [ -e "$SCR/mvc.app.languages/$(basename "$target")" ] && fail "the legacy leftover $target still exists" || :
    done < "$SCR/root/legacy.txt"
    pass 'both legacy leftovers were removed from the installed tree'
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
    [ "$states" = 10 ] || fail "core-locale state files $states != 10"
    pass 'the pristine core catalogues were preserved (10 locales)'
}

# Plants the state a later upgrade produces when a language is dropped: a compiled catalogue
# for a locale the current release no longer ships, named by the digest-bearing record that
# the 2.13.3 installer wrote. This is finding #2 of the pruning review in executable form.
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

# The pristine-catalogue archive is deliberately not rolled back: it is the pre-install copy
# that uninstall.sh restores, and it is first-write-wins, so a failed run leaving it behind
# cannot change what a later run considers pristine. This check proves the archive really
# matches the catalogues that the rollback restored.
sb_verify_core_locale_archive() {
    label=$1
    rc=0
    sb_run > "$EVI/core-locale.log" 2>&1 <<'CORELOCALE' || rc=$?
bad=0
for state in /var/backups/devicemonitor/core-locale/*.state; do
    [ -f "$state" ] || continue
    lang=$(basename "$state" .state)
    pristine=$(sed -n 's/^pristine=//p' "$state")
    target=$(sed -n 's/^target=//p' "$state")
    [ -n "$target" ] || { echo "VERIFY_FAIL state $lang"; bad=1; continue; }
    if [ "$pristine" = absent ]; then
        [ ! -e "$target" ] || { echo "VERIFY_FAIL pristine-absent $target"; bad=1; }
    elif [ ! -f "$target" ]; then
        echo "VERIFY_FAIL missing $target"; bad=1
    elif [ "$(sha256 -q "$target")" != "$pristine" ]; then
        echo "VERIFY_FAIL pristine $target"; bad=1
    fi
done
count=$(ls /var/backups/devicemonitor/core-locale/*.state 2>/dev/null | wc -l | tr -d ' ')
[ "$count" = 10 ] || { echo "VERIFY_FAIL state count $count"; bad=1; }
echo "VERIFY_CORE_LOCALE=$count"
[ "$bad" = 0 ]
CORELOCALE
    if [ "$rc" = 0 ]; then
        sed -n 's/^VERIFY_/  /p' "$EVI/core-locale.log"
        pass "$label"
    else
        grep '^VERIFY_FAIL' "$EVI/core-locale.log" >&2 || cat "$EVI/core-locale.log" >&2
        printf 'SANDBOX_FAIL: %s\n' "$label" >&2
        FAILED=$((FAILED + 1))
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
        printf 'SANDBOX_FAIL: %s\n' "$label" >&2
        FAILED=$((FAILED + 1))
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
    printf '%s\n' "$line" | grep -q '^INSTALL_OK version=2.13.3 files=61 core_locales=10 pruned=1 ' ||
        fail 'the repair did not report the payload with one pruned file'
    printf '%s\n' "$line" | grep -q 'daemon_restarted=0 unchanged=61 repaired=0$' ||
        fail 'the repair did not report unchanged=61 repaired=0'
    pass 'the repair reported unchanged=61 repaired=0 with pruned=1'
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
# This is the deployment-shaped case: a 2.13.2 node with both published leftovers present
# runs the real upgrade, the prune is applied, the next step fails, and the installer's own
# abort path has to restore the replaced target, the two pruned files and the record.
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
    recorded "$EVI/failing.log" '^ROLLBACK_ATTEMPTED=/var/backups/devicemonitor/install-v213\.' ||
        { cat "$EVI/failing.log" >&2; fail 'no ROLLBACK_ATTEMPTED line'; }
    recorded "$EVI/failing.log" '^ROLLBACK_STATUS=COMPLETE$' ||
        { cat "$EVI/failing.log" >&2; fail 'the rollback did not report COMPLETE'; }
    pass 'the installer reported ROLLBACK_STATUS=COMPLETE'
    recorded "$EVI/failing.log" '^PRUNED=2$' || fail 'the prune step did not run before the failure'
    pass 'both leftovers had already been pruned when the failure was injected'
    recorded "$EVI/failing.log" '^ROLLBACK_SUMMARY=restored=1 skipped=[0-9]* conflicts=0 failed=0$' ||
        fail 'the replaced target was not restored by restore-targets'
    pass 'the replaced target was restored by the digest-verified restore-targets step'
    recorded "$EVI/failing.log" '^ROLLBACK_SUMMARY=restored=2 skipped=0 conflicts=0 failed=0$' ||
        fail 'the pruned files were not restored by the prune rollback'
    pass 'both pruned leftovers were restored by the digest-verified prune rollback'
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
    done < "$SCR/root/legacy.txt"
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
  DM_SANDBOX_BUNDLE    use an existing dm-v2.13.3-runtime.tar.gz instead of rebuilding it
  DM_SANDBOX_SAVE      set to 1 to copy the transcripts into verification/installer-sandbox/evidence
USAGE
    exit 2
}

save_evidence() {
    [ "${DM_SANDBOX_SAVE:-0}" = 1 ] || return 0
    dest=$SELF/evidence/$CURRENT
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
    (
        trap 'save_evidence; sb_teardown' EXIT INT TERM
        "scenario_$name"
        printf '%s\n' "$name" > "$WORK/status-$name"
    ) 2>&1 | tee "$WORK/transcript-$name.log" || rc=$?
    if [ -f "$WORK/status-$name" ]; then
        say "SANDBOX_SCENARIO $name PASS"
    else
        say "SANDBOX_SCENARIO $name FAIL"
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
    rm -f "$WORK"/status-*
    if [ "$cmd" = all ]; then
        for s in check install repair rollback failclosed; do run_one "$s"; done
    else
        [ "$#" = 2 ] || usage
        run_one "$2"
    fi
    say "SANDBOX_SUMMARY failures=$FAILED work=$WORK"
    [ "$FAILED" = 0 ] || exit 1
    say 'SANDBOX_RESULT=PASS'
}

main "$@"
