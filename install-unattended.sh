#!/bin/sh
# Guarded Device Monitor v2.9 installation on OPNsense/FreeBSD.
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
for executable in sha256 stat install python3 php msgfmt nmap service; do
    command -v "$executable" >/dev/null 2>&1 || { echo "ABORT: missing dependency $executable" >&2; exit 1; }
done
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
cd "$SCRIPT_DIR"
MANIFEST=release/v2.9-runtime.manifest
[ -f "$MANIFEST" ] && [ "$(sha256 -q "$MANIFEST")" = 57f167b3c3db3eae87190593c27311e6bd45d79ae0372c5c03625cfc82b5958d ] || { echo 'ABORT: release manifest mismatch' >&2; exit 1; }
[ "$(wc -l < "$MANIFEST" | tr -d ' ')" = 37 ] || { echo 'ABORT: release manifest count' >&2; exit 1; }
[ "$(python3 -c 'import json; print(json.load(open("src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json"))["version"])')" = 2.9 ] || { echo 'ABORT: source version' >&2; exit 1; }
LIVE_DEFAULTS=/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json
if [ -f "$LIVE_DEFAULTS" ]; then
    installed=$(python3 - "$LIVE_DEFAULTS" <<'PY'
import json,sys
print(json.load(open(sys.argv[1]))['version'])
PY
) || { echo 'ABORT: installed defaults invalid' >&2; exit 1; }
    case "$installed" in 2.8|2.9) :;; *) echo "ABORT: unsupported predecessor $installed" >&2; exit 1;; esac
elif [ -d /usr/local/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor ]; then
    echo 'ABORT: partial existing installation' >&2; exit 1
else
    installed=fresh
fi
[ ! -e /etc/rc.d/devicemonitor ] && [ ! -L /etc/rc.d/devicemonitor ] || [ "$(readlink /etc/rc.d/devicemonitor)" = /usr/local/etc/rc.d/devicemonitor ] || { echo 'ABORT: rc link collision' >&2; exit 1; }
STAGE=$(mktemp -d /tmp/dm_install_v29.XXXXXX)
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
        src/opnsense/*:/usr/local/opnsense/*|src/etc/rc.d/devicemonitor:/usr/local/etc/rc.d/devicemonitor|src/etc/inc/plugins.inc.d/devicemonitor.inc:/usr/local/etc/inc/plugins.inc.d/devicemonitor.inc) :;;
        *) echo "ABORT: invalid manifest path $source" >&2; exit 1;;
    esac
    [ -f "$source" ] && [ ! -L "$source" ] && [ "$(sha256 -q "$source")" = "$hash" ] || { echo "ABORT: source hash $source" >&2; exit 1; }
    [ ! -L "$target" ] || { echo "ABORT: target symlink $target" >&2; exit 1; }
    printf '%s %s %s %s\n' "$hash" "$mode" "$source" "$target" >> "$STAGE/items"
done < "$MANIFEST"
for lang in en_US cs_CZ; do
    source=src/opnsense/mvc/app/languages/${lang}_devicemonitor.po
    output=$STAGE/${lang}_devicemonitor.mo
    msgfmt --check -o "$output" "$source" >/dev/null || { echo "ABORT: gettext $lang" >&2; exit 1; }
    printf '%s %s %s %s\n' "$(sha256 -q "$output")" 644 "$output" "/usr/local/opnsense/mvc/app/languages/${lang}_devicemonitor.mo" >> "$STAGE/items"
done
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
expected=39
[ "$FRESH" = 0 ] || expected=40
[ "$count" = "$expected" ] || { echo 'ABORT: target count' >&2; exit 1; }
printf 'CHECK_OK version=2.9 predecessor=%s files=%s daemon_running=%s host=%s\n' "$installed" "$count" "$WAS_RUNNING" "$EXPECTED_HOST"
[ "$CHECK_ONLY" = 0 ] || exit 0
mkdir -p /var/backups/devicemonitor
BACKUP=$(mktemp -d /var/backups/devicemonitor/install-v29.XXXXXX)
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
# Recheck all predecessors immediately before first replacement.
while read -r id old new mode source target; do
    if [ "$old" = absent ]; then [ ! -e "$target" ] || { echo "ABORT: target appeared $target" >&2; exit 1; }
    else [ "$(sha256 -q "$target")" = "$old" ] || { echo "ABORT: target changed $target" >&2; exit 1; }; fi
done < "$BACKUP/plan"
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
    pgrep -f '^/usr/local/bin/python3 /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/monitor_daemon.py$' >/dev/null || { echo 'ABORT: daemon not running' >&2; exit 1; }
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
printf 'INSTALL_OK version=2.9 files=%s backup=%s daemon_restarted=%s\n' "$count" "$BACKUP" "$WAS_RUNNING"
