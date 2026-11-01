#!/bin/sh
# Install a staged Device Monitor payload onto this appliance (run as root).
#
# Usage: deploy-devicemonitor.sh <staging-dir>
#
# The staging directory must contain:
#   payload/  file tree rooted at usr/local/...
#   MANIFEST  "<md5>  <absolute path>" per file
#   SOURCE    one line of provenance: ref, commit, built-by, timestamp
#
# Nothing is written unless every staged file matches its manifest hash, so a
# partial or corrupted transfer cannot half-update an appliance.
set -eu

STAGE=${1:-}
MANIFEST_SRC="$STAGE/MANIFEST"
MANIFEST_DST=/var/db/devicemonitor/deployed.manifest
STATE_DST=/var/db/devicemonitor/deployed.json
SERVICE=/usr/sbin/service
LOG=/var/log/devicemonitor.log
DRIFT_CRON=/etc/cron.d/devicemonitor-drift

die() {
    echo "deploy: $*" >&2
    exit 1
}

[ -n "$STAGE" ] || die "usage: $0 <staging-dir>"
[ -f "$MANIFEST_SRC" ] || die "missing $MANIFEST_SRC"
[ -d "$STAGE/payload" ] || die "missing $STAGE/payload"

echo "deploy: verifying staged payload"
while read -r hash path; do
    case "$hash" in
        ''|'#'*) continue ;;
    esac

    rel=${path#/}
    file="$STAGE/payload/$rel"

    [ -f "$file" ] || die "staged file missing: $rel"

    actual=$(md5 -q "$file")
    [ "$actual" = "$hash" ] || die "staged hash mismatch for $rel (want $hash, got $actual)"
done < "$MANIFEST_SRC"

stamp=$(date '+%Y%m%d-%H%M%S')
backup="/root/devicemonitor-deploy-backup-$stamp"
mkdir -p "$backup"

echo "deploy: backing up replaced files to $backup"

# 1. backup everything that is about to be replaced
while read -r hash path; do
    case "$hash" in
        ''|'#'*) continue ;;
    esac

    [ -f "$path" ] || continue

    dest="$backup/${path#/}"
    mkdir -p "$(dirname "$dest")"
    cp -p "$path" "$dest"
done < "$MANIFEST_SRC"

# 2. install atomically, one file at a time
installed=0
while read -r hash path; do
    case "$hash" in
        ''|'#'*) continue ;;
    esac

    rel=${path#/}
    src="$STAGE/payload/$rel"
    dir=$(dirname "$path")

    [ -d "$dir" ] || mkdir -p "$dir"

    case "$path" in
        */scripts/*|*/rc.d/*|*.sh)
            mode=755
            ;;
        *)
            mode=644
            ;;
    esac

    tmp="$path.deploy-$$"
    cp "$src" "$tmp"
    chown root:wheel "$tmp"
    chmod "$mode" "$tmp"
    mv -f "$tmp" "$path"
    installed=$((installed + 1))
done < "$MANIFEST_SRC"

echo "deploy: installed $installed file(s)"

# 3. record provenance so the appliance knows exactly what it is running
{
    printf '# %s\n' "$(cat "$STAGE/SOURCE" 2>/dev/null || echo 'unknown source')"
    cat "$MANIFEST_SRC"
} > "$MANIFEST_DST.tmp"
mv -f "$MANIFEST_DST.tmp" "$MANIFEST_DST"

ref=$(sed -n '1s/^# *//p' "$MANIFEST_DST" | awk '{print $1}')
commit=$(sed -n '1s/^# *//p' "$MANIFEST_DST" | awk '{print $2}')

cat > "$STATE_DST" <<EOF
{
  "ref": "${ref:-unknown}",
  "commit": "${commit:-unknown}",
  "installed_at": "$(date '+%Y-%m-%dT%H:%M:%S%z')",
  "files": $installed,
  "backup": "$backup"
}
EOF

# 4. keep the drift check scheduled (idempotent)
if [ ! -f "$DRIFT_CRON" ]; then
    cat > "$DRIFT_CRON" <<EOF
SHELL=/bin/sh
PATH=/etc:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin
17 4 * * * root /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/verify-devicemonitor.sh >/dev/null 2>&1
EOF
    chmod 644 "$DRIFT_CRON"
    echo "deploy: scheduled drift check in $DRIFT_CRON"
fi

# 5. restart and smoke-test one scan cycle
if [ -f /usr/local/etc/rc.d/devicemonitor ]; then
    before=$(wc -l < "$LOG" 2>/dev/null || echo 0)

    $SERVICE devicemonitor restart >/dev/null 2>&1 || die "service devicemonitor failed to restart"

    echo "deploy: waiting for a clean scan cycle"
    waited=0
    ok=0
    while [ "$waited" -lt 120 ]; do
        sleep 5
        waited=$((waited + 5))

        if tail -n +"$((before + 1))" "$LOG" 2>/dev/null | grep -q 'Scan completed successfully'; then
            ok=1
            break
        fi

        if tail -n +"$((before + 1))" "$LOG" 2>/dev/null | grep -q 'Scan failed with code'; then
            die "post-deploy scan failed; see $LOG (rollback from $backup)"
        fi
    done

    [ "$ok" -eq 1 ] || die "no successful scan within 120s; see $LOG (rollback from $backup)"
fi

# 6. verify what we just installed
/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/verify-devicemonitor.sh || true

echo "deploy: done ($installed files from ${ref:-unknown})"
