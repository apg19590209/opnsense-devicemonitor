#!/bin/sh
# Verify the installed Device Monitor files against the deploy manifest.
#
# The manifest is written by deploy-devicemonitor.sh and records the md5 of
# every file that deployment installed, together with the git ref it came
# from. Any local edit, hand-patched file or stray code file is reported as
# drift, so an appliance can never silently run code that is not in git.
#
# Exit codes: 0 = clean, 1 = drift detected, 2 = no manifest (never deployed
# with this tool).
set -u

MANIFEST=/var/db/devicemonitor/deployed.manifest
DRIFT_LOG=/var/log/devicemonitor-drift.log
ROOT=/usr/local
TAG=devicemonitor-drift

PLUGIN_DIRS="$ROOT/opnsense/scripts/OPNsense/DeviceMonitor \
$ROOT/opnsense/mvc/app/models/OPNsense/DeviceMonitor \
$ROOT/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor \
$ROOT/opnsense/mvc/app/views/OPNsense/DeviceMonitor"

if [ ! -f "$MANIFEST" ]; then
    msg="no deploy manifest at $MANIFEST: this appliance was not deployed by deploy/deploy-devicemonitor.sh"
    echo "DRIFT: $msg" >&2
    logger -t "$TAG" -p daemon.warning "$msg" 2>/dev/null
    exit 2
fi

now=$(date '+%Y-%m-%dT%H:%M:%S%z')
deployed=$(sed -n '1s/^# *//p' "$MANIFEST" 2>/dev/null)
checked=0
drift=0

report() {
    drift=$((drift + 1))
    echo "DRIFT: $*"
    printf '%s DRIFT %s\n' "$now" "$*" >> "$DRIFT_LOG"
}

while read -r hash path; do
    case "$hash" in
        ''|'#'*) continue ;;
    esac

    checked=$((checked + 1))

    if [ ! -f "$path" ]; then
        report "missing file: $path"
        continue
    fi

    actual=$(md5 -q "$path" 2>/dev/null)
    if [ "$actual" != "$hash" ]; then
        report "modified file: $path (expected $hash, found ${actual:-unreadable})"
    fi
done < "$MANIFEST"

# Any code file in the plugin tree that the manifest does not know about is
# unversioned code: the exact failure mode that let production run a
# scan_network.py that existed in no commit.
known=$(awk '!/^#/ {print $2}' "$MANIFEST")

for dir in $PLUGIN_DIRS; do
    [ -d "$dir" ] || continue

    for file in "$dir"/*; do
        [ -f "$file" ] || continue

        case "$file" in
            *.bak*|*.orig|*.pre-*|*.pre_*|*'~'|*.pyc|*.mo|*.swp) continue ;;
        esac

        case "$file" in
            *.py|*.php|*.sh|*.inc|*.volt|*.conf|*.json|*.xml|*.js) ;;
            *) continue ;;
        esac

        if ! printf '%s\n' "$known" | grep -Fxq "$file"; then
            report "unversioned file: $file (not in the deploy manifest)"
        fi
    done
done

if [ "$drift" -ne 0 ]; then
    summary="$drift drift item(s) across $checked tracked files; see $DRIFT_LOG"
    echo "$summary" >&2
    logger -t "$TAG" -p daemon.warning "$summary" 2>/dev/null
    exit 1
fi

echo "clean: $checked tracked files match the manifest ($deployed)"
exit 0
