#!/bin/sh
# Guarded Device Monitor v2.11 installation on OPNsense/FreeBSD.
set -eu
export PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin
EXPECTED_HOST=
CHECK_ONLY=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --host) [ "$#" -ge 2 ] || exit 2; EXPECTED_HOST=$2; shift 2;;
        --check) CHECK_ONLY=1; shift;;
        *) echo "ABORT: unknown argument $1" >&2; exit 2;;
    esac
done
[ -n "$EXPECTED_HOST" ] || { echo 'ABORT: --host is required' >&2; exit 2; }
[ "$(id -u)" = 0 ] || { echo 'ABORT: root required' >&2; exit 1; }
[ "$(uname -s)" = FreeBSD ] || { echo 'ABORT: FreeBSD required' >&2; exit 1; }
[ "$(/bin/hostname)" = "$EXPECTED_HOST" ] || { echo 'ABORT: hostname mismatch' >&2; exit 1; }
command -v opnsense-version >/dev/null 2>&1 || { echo 'ABORT: OPNsense missing' >&2; exit 1; }
[ -x /usr/local/etc/rc.configure_plugins ] || { echo 'ABORT: OPNsense plugin registration unavailable' >&2; exit 1; }
ver=$(opnsense-version | awk '{print $2}')
printf '%s\n' "$ver" | awk -F'[.-]' '{if ($1+0>26 || ($1+0==26 && ($2+0>1 || ($2+0==1 && $3+0>=5)))) exit 0; exit 1}' || { echo 'ABORT: OPNsense 26.1.5+ required' >&2; exit 1; }
for executable in sha256 stat install python3 php msgfmt msgcat msgunfmt service; do
    command -v "$executable" >/dev/null 2>&1 || { echo "ABORT: missing dependency $executable" >&2; exit 1; }
done
# Issue #4 ("Missing Dependancy"): nmap is a package dependency (security/nmap), not an
# OPNsense base tool, while scan_network.py invokes /usr/local/bin/nmap directly. The
# installer supplies it instead of failing the installation, as the v2.4 notes already
# document ("The installer now automatically installs Nmap when it is not already
# available"). Detection here is read-only so --check stays non-mutating; the package is
# installed in the write phase, after every read-only guard has passed.
NMAP_MISSING=0
command -v nmap >/dev/null 2>&1 || NMAP_MISSING=1
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
cd "$SCRIPT_DIR"
MANIFEST=release/v2.11-runtime.manifest
[ -f "$MANIFEST" ] && [ "$(sha256 -q "$MANIFEST")" = 56292fb29b66e273d96947e71bd8a4e8a02d7a7e644990f9358ddb91a7a60de5 ] || { echo 'ABORT: release manifest mismatch' >&2; exit 1; }
[ "$(wc -l < "$MANIFEST" | tr -d ' ')" = 38 ] || { echo 'ABORT: release manifest count' >&2; exit 1; }
[ "$(python3 -c 'import json; print(json.load(open("src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json"))["version"])')" = 2.11 ] || { echo 'ABORT: source version' >&2; exit 1; }
LIVE_DEFAULTS=/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json
if [ -f "$LIVE_DEFAULTS" ]; then
    installed=$(python3 - "$LIVE_DEFAULTS" <<'PY'
import json,sys
print(json.load(open(sys.argv[1]))['version'])
PY
) || { echo 'ABORT: installed defaults invalid' >&2; exit 1; }
    case "$installed" in 2.8|2.9|2.10|2.11) :;; *) echo "ABORT: unsupported predecessor $installed" >&2; exit 1;; esac
elif [ -d /usr/local/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor ]; then
    echo 'ABORT: partial existing installation' >&2; exit 1
else
    installed=fresh
fi
[ ! -e /etc/rc.d/devicemonitor ] && [ ! -L /etc/rc.d/devicemonitor ] || [ "$(readlink /etc/rc.d/devicemonitor)" = /usr/local/etc/rc.d/devicemonitor ] || { echo 'ABORT: rc link collision' >&2; exit 1; }
STAGE=$(mktemp -d /tmp/dm_install_v211.XXXXXX)
BACKUP=
MUTATING=0
WAS_RUNNING=0
CONFIGD_CHANGED=0
FRESH=0
RC_LINK_CREATED=0
[ "$installed" = fresh ] && FRESH=1
cleanup() {
    rc=$?
    trap - EXIT
    if [ "$rc" -ne 0 ] && [ "$MUTATING" = 1 ]; then
        echo "ROLLBACK_START=$BACKUP" >&2
        if [ "$WAS_RUNNING" = 1 ] || [ "$FRESH" = 1 ]; then service devicemonitor stop || :; fi
        while read -r id old new mode src dest; do
            if [ "$old" = absent ]; then
                if [ -f "$dest" ] && [ "$(sha256 -q "$dest")" = "$new" ]; then
                    rm -f "$dest" || echo "ROLLBACK_FAILED=$dest" >&2
                elif [ -e "$dest" ]; then
                    echo "ROLLBACK_CONFLICT=$dest" >&2
                fi
            else
                if [ -f "$dest" ] && [ "$(sha256 -q "$dest")" = "$new" ]; then
                    cp -p "$BACKUP/files/$id" "$dest" || echo "ROLLBACK_FAILED=$dest" >&2
                elif [ "$(sha256 -q "$dest" 2>/dev/null || :)" != "$old" ]; then
                    echo "ROLLBACK_CONFLICT=$dest" >&2
                fi
            fi
        done < "$BACKUP/plan"
        if [ "$RC_LINK_CREATED" = 1 ]; then rm -f /etc/rc.d/devicemonitor; fi
        if [ "$CONFIGD_CHANGED" = 1 ]; then service configd restart || echo 'ROLLBACK_CONFIGD_RESTART_FAILED' >&2; fi
        if [ "$WAS_RUNNING" = 1 ]; then service devicemonitor restart || echo 'ROLLBACK_DAEMON_RESTART_FAILED' >&2; fi
        echo "ROLLBACK_ATTEMPTED=$BACKUP" >&2
    fi
    rm -rf "$STAGE"
    exit "$rc"
}
trap cleanup EXIT
# Verify every packaged source before any target is changed.
: > "$STAGE/items"
while read -r hash mode source target; do
    case "$source:$target" in
        src/opnsense/*:/usr/local/opnsense/*|src/etc/rc.d/devicemonitor:/usr/local/etc/rc.d/devicemonitor|src/etc/inc/plugins.inc.d/devicemonitor.inc:/usr/local/etc/inc/plugins.inc.d/devicemonitor.inc|src/etc/inc/devicemonitor_locale.inc:/usr/local/etc/inc/devicemonitor_locale.inc) :;;
        *) echo "ABORT: invalid manifest path $source" >&2; exit 1;;
    esac
    [ -f "$source" ] && [ ! -L "$source" ] && [ "$(sha256 -q "$source")" = "$hash" ] || { echo "ABORT: source hash $source" >&2; exit 1; }
    [ ! -L "$target" ] || { echo "ABORT: target symlink $target" >&2; exit 1; }
    printf '%s %s %s %s\n' "$hash" "$mode" "$source" "$target" >> "$STAGE/items"
done < "$MANIFEST"
# DM-BL-008c: number of core-domain catalogues staged by the loop below (used by the guards
# and by the CHECK_OK/INSTALL_OK report).
CORE_LOCALES=0
for lang in en_US cs_CZ de_DE fr_FR es_ES it_IT pt_BR nl_NL ru_RU ja_JP zh_CN; do
    pofile=src/opnsense/mvc/app/languages/${lang}/LC_MESSAGES/devicemonitor.po
    modir=$STAGE/${lang}/LC_MESSAGES
    mkdir -p "$modir"
    output=$modir/devicemonitor.mo
    msgfmt --check -o "$output" "$pofile" >/dev/null || { echo "ABORT: gettext $lang" >&2; exit 1; }
    printf '%s %s %s %s\n' "$(sha256 -q "$output")" 644 "$output" "/usr/local/opnsense/mvc/app/languages/${lang}/LC_MESSAGES/devicemonitor.mo" >> "$STAGE/items"
    # DM-BL-008c: the inline-script strings resolve through the core domain
    # (ControllerRoot::setLang -> ViewTranslator over /usr/local/share/locale), so the plugin
    # keys are merged into <core>/<locale>/LC_MESSAGES/OPNsense.mo with a core-first msgcat.
    # A locale whose core catalogue is absent (nl_NL on the current release) is not an error:
    # it receives the plugin catalogue alone, which is the state the testbed already renders.
    # en_US is the reference language, so no core catalogue is created for it.
    if [ "$lang" = en_US ]; then continue; fi
    core=/usr/local/share/locale/${lang}/LC_MESSAGES/OPNsense.mo
    coreoutput=$STAGE/OPNsense-${lang}.mo
    if [ -f "$core" ]; then
        /bin/sh "$SCRIPT_DIR/release/merge-opnsense-catalog.sh" "$core" "$pofile" "$coreoutput" || { echo "ABORT: OPNsense catalogue merge $lang" >&2; exit 1; }
        coremode=$(stat -f %Lp "$core")
    else
        /bin/sh "$SCRIPT_DIR/release/merge-opnsense-catalog.sh" --plugin-only "$pofile" "$coreoutput" || { echo "ABORT: plugin-only catalogue $lang" >&2; exit 1; }
        coremode=644
        printf 'NOTICE: no core catalogue for %s; installing the plugin catalogue alone\n' "$lang"
    fi
    printf '%s %s %s %s\n' "$(sha256 -q "$coreoutput")" "$coremode" "$coreoutput" "$core" >> "$STAGE/items"
    CORE_LOCALES=$((CORE_LOCALES + 1))
done
printf 'NOTICE: merged the plugin keys into %s core catalogue(s); uninstall.sh restores the pristine files\n' "$CORE_LOCALES"
python3 - <<'PY'
import ast,glob,json,xml.etree.ElementTree as ET
for p in glob.glob('src/opnsense/scripts/OPNsense/DeviceMonitor/*.py'):
    ast.parse(open(p).read(),filename=p)
json.load(open('src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'))
for p in glob.glob('src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/**/*.xml',recursive=True): ET.parse(p)
PY
for p in src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/*.php src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/*.php src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/*.php src/opnsense/scripts/OPNsense/DeviceMonitor/*.php; do php -l "$p" >/dev/null || exit 1; done
for p in src/opnsense/scripts/OPNsense/DeviceMonitor/*.sh src/etc/rc.d/devicemonitor; do sh -n "$p" || exit 1; done
if [ -f /var/db/devicemonitor/devices.db ]; then
    python3 - <<'PY'
import sqlite3
c=sqlite3.connect('file:/var/db/devicemonitor/devices.db?mode=ro',uri=True)
assert c.execute('PRAGMA quick_check').fetchone()[0]=='ok'
c.close()
PY
fi
if [ -f /var/db/devicemonitor/config.json ]; then python3 -m json.tool /var/db/devicemonitor/config.json >/dev/null || exit 1; fi
if pgrep -f '^/usr/local/bin/python3 /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/monitor_daemon.py$' >/dev/null; then WAS_RUNNING=1; fi
# An existing autostart setting is preserved; fresh installs opt in to service startup.
if [ "$FRESH" = 1 ]; then
    [ ! -e /etc/rc.conf.d/devicemonitor ] || { echo 'ABORT: pre-existing rc configuration' >&2; exit 1; }
    printf 'devicemonitor_enable="YES"\n' > "$STAGE/rc.conf"
    printf '%s %s %s %s\n' "$(sha256 -q "$STAGE/rc.conf")" 644 "$STAGE/rc.conf" /etc/rc.conf.d/devicemonitor >> "$STAGE/items"
fi
# Freeze observed predecessor hashes and metadata before the backup.
: > "$STAGE/plan"
id=0
while read -r hash mode source target; do
    if [ -e "$target" ]; then
        [ -f "$target" ] && [ ! -L "$target" ] || { echo "ABORT: nonregular target $target" >&2; exit 1; }
        old=$(sha256 -q "$target")
    else old=absent; fi
    printf '%s %s %s %s %s %s\n' "$id" "$old" "$hash" "$mode" "$source" "$target" >> "$STAGE/plan"
    id=$((id + 1))
done < "$STAGE/items"
count=$id
# 38 manifest rows + 11 sidecar catalogues + one merged core-domain catalogue per locale that
# can host one (all but en_US); a fresh install adds rc.conf.
expected=59
[ "$FRESH" = 0 ] || expected=60
[ "$count" = "$expected" ] || { echo 'ABORT: target count' >&2; exit 1; }
[ "$NMAP_MISSING" = 0 ] || printf 'NOTICE: nmap is not installed; a real installation runs pkg install -y nmap\n'
printf 'CHECK_OK version=2.11 predecessor=%s files=%s core_locales=%s daemon_running=%s host=%s\n' "$installed" "$count" "$CORE_LOCALES" "$WAS_RUNNING" "$EXPECTED_HOST"
[ "$CHECK_ONLY" = 0 ] || exit 0
mkdir -p /var/backups/devicemonitor
BACKUP=$(mktemp -d /var/backups/devicemonitor/install-v211.XXXXXX)
mkdir "$BACKUP/files"
cp "$STAGE/plan" "$BACKUP/plan"
while read -r id old new mode source target; do
    if [ "$old" != absent ]; then
        cp -p "$target" "$BACKUP/files/$id"
        [ "$(sha256 -q "$BACKUP/files/$id")" = "$old" ] || { echo "ABORT: backup $target" >&2; exit 1; }
    fi
done < "$BACKUP/plan"
if [ -f /var/db/devicemonitor/devices.db ]; then
    python3 - "$BACKUP/devices.db" <<'PY'
import sqlite3,sys
src=sqlite3.connect('file:/var/db/devicemonitor/devices.db?mode=ro',uri=True)
dst=sqlite3.connect(sys.argv[1]);src.backup(dst)
assert dst.execute('PRAGMA quick_check').fetchone()[0]=='ok'
dst.close();src.close()
PY
fi
[ ! -f /var/db/devicemonitor/config.json ] || cp -p /var/db/devicemonitor/config.json "$BACKUP/config.json"
printf 'BACKUP_READY=%s\n' "$BACKUP"
# DM-BL-008c: preserve the pristine core catalogues once, before the first merge, so that
# uninstall.sh can restore them exactly (or delete a file this installer created itself). The
# record is first-write-wins per locale: a later install must never treat its own merged output
# as the pristine state. This runs only on a real install, never during --check.
CORE_LOCALE_STATE=/var/backups/devicemonitor/core-locale
mkdir -p "$CORE_LOCALE_STATE"
while read -r id old new mode source target; do
    case "$target" in
        /usr/local/share/locale/*/LC_MESSAGES/OPNsense.mo) :;;
        *) continue;;
    esac
    lang=$(basename "$(dirname "$(dirname "$target")")")
    state=$CORE_LOCALE_STATE/$lang.state
    if [ ! -f "$state" ]; then
        if [ "$old" = absent ]; then
            pristine=absent
        else
            cp -p "$target" "$CORE_LOCALE_STATE/$lang.OPNsense.mo"
            pristine=$old
            [ "$(sha256 -q "$CORE_LOCALE_STATE/$lang.OPNsense.mo")" = "$pristine" ] || { echo "ABORT: pristine copy $target" >&2; exit 1; }
        fi
    else
        pristine=$(sed -n 's/^pristine=//p' "$state")
        # A catalogue that appeared from outside this installer (a core upgrade, for example) is
        # recorded as pristine rather than mistaken for our own output.
        if [ "$pristine" = absent ] && [ -f "$target" ] && [ "$(sha256 -q "$target")" != "$(sed -n 's/^installed=//p' "$state")" ]; then
            cp -p "$target" "$CORE_LOCALE_STATE/$lang.OPNsense.mo"
            pristine=$(sha256 -q "$target")
        fi
        if [ "$pristine" != absent ] && [ ! -f "$CORE_LOCALE_STATE/$lang.OPNsense.mo" ]; then
            cp -p "$target" "$CORE_LOCALE_STATE/$lang.OPNsense.mo"
            pristine=$(sha256 -q "$target")
        fi
    fi
    printf 'pristine=%s\ntarget=%s\ninstalled=%s\n' "$pristine" "$target" "$new" > "$state"
done < "$BACKUP/plan"
printf 'CORE_LOCALE_STATE=%s\n' "$CORE_LOCALE_STATE"
# Recheck all predecessors immediately before first replacement.
while read -r id old new mode source target; do
    if [ "$old" = absent ]; then [ ! -e "$target" ] || { echo "ABORT: target appeared $target" >&2; exit 1; }
    else [ "$(sha256 -q "$target")" = "$old" ] || { echo "ABORT: target changed $target" >&2; exit 1; }; fi
done < "$BACKUP/plan"
# Issue #4: satisfy the nmap package dependency after every read-only guard has passed and
# before the first installed target is replaced, so the plugin is never installed onto a
# firewall that lacks the scanner its targeted scans invoke.
if [ "$NMAP_MISSING" = 1 ]; then
    command -v pkg >/dev/null 2>&1 || { echo 'ABORT: missing dependency nmap and pkg is unavailable to install it' >&2; exit 1; }
    printf 'NOTICE: nmap is not installed; installing the security/nmap package\n'
    pkg install -y nmap >&2 || { echo 'ABORT: missing dependency nmap; pkg install failed' >&2; exit 1; }
    command -v nmap >/dev/null 2>&1 || { echo 'ABORT: missing dependency nmap; pkg install did not provide nmap' >&2; exit 1; }
fi
MUTATING=1
while read -r id old new mode source target; do
    mkdir -p "$(dirname "$target")"
    if [ "$old" = absent ]; then owner=root; group=wheel
    else
        mode=$(stat -f %Lp "$target")
        owner=$(stat -f %Su "$target")
        group=$(stat -f %Sg "$target")
    fi
    install -m "$mode" -o "$owner" -g "$group" "$source" "$target"
    [ "$(sha256 -q "$target")" = "$new" ] || { echo "ABORT: poststate $target" >&2; exit 1; }
done < "$BACKUP/plan"
if [ ! -e /etc/rc.d/devicemonitor ]; then
    ln -s /usr/local/etc/rc.d/devicemonitor /etc/rc.d/devicemonitor
    RC_LINK_CREATED=1
fi
mkdir -p /var/db/devicemonitor
if [ "$FRESH" = 1 ]; then chmod 755 /var/db/devicemonitor; fi
rm -f /var/lib/php/tmp/opnsense_menu_cache.xml
if [ -d /var/lib/php/tmp ]; then find /var/lib/php/tmp -type f \( -name '*devicemonitor*' -o -name '*DeviceMonitor*' \) -delete; fi
if [ "$FRESH" = 1 ]; then /usr/local/etc/rc.configure_plugins; fi
CONFIGD_CHANGED=1
service configd restart
if [ "$WAS_RUNNING" = 1 ]; then
    service devicemonitor restart
elif [ "$FRESH" = 1 ]; then
    service devicemonitor start
fi
if [ "$WAS_RUNNING" = 1 ] || [ "$FRESH" = 1 ]; then
    # rc starts the daemon in the background and it can take a moment to appear, so poll
    # instead of testing once: an immediate pgrep can fail on a healthy restart and abort an
    # otherwise complete installation. That happened on 2026-09-28 and rolled back a good
    # deployment even though the daemon came up moments later.
    waited=0
    while [ "$waited" -lt 30 ]; do
        pgrep -f '^/usr/local/bin/python3 /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/monitor_daemon.py$' >/dev/null && break
        sleep 1
        waited=$((waited + 1))
    done
    pgrep -f '^/usr/local/bin/python3 /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/monitor_daemon.py$' >/dev/null || { echo 'ABORT: daemon not running after 30s' >&2; exit 1; }
fi
while read -r id old new mode source target; do
    [ "$(sha256 -q "$target")" = "$new" ] || { echo "ABORT: final hash $target" >&2; exit 1; }
done < "$BACKUP/plan"
if [ -f /var/db/devicemonitor/devices.db ]; then
    python3 - <<'PY'
import sqlite3
c=sqlite3.connect('file:/var/db/devicemonitor/devices.db?mode=ro',uri=True)
assert c.execute('PRAGMA quick_check').fetchone()[0]=='ok'
c.close()
PY
fi
MUTATING=0
printf 'INSTALL_OK version=2.11 files=%s core_locales=%s backup=%s daemon_restarted=%s\n' "$count" "$CORE_LOCALES" "$BACKUP" "$WAS_RUNNING"
