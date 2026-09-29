#!/bin/sh

# Device Monitor - Uninstall Script
# Supports silent mode for reinstall: ./uninstall.sh --silent

SILENT_MODE=0

# Check the --silent parameter
if [ "$1" = "--silent" ]; then
    SILENT_MODE=1
fi

if [ "$SILENT_MODE" -eq 0 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Device Monitor - Uninstall"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
fi

# Root check
[ "$(id -u)" != "0" ] && {
    echo "ERROR: You must be root!"
    exit 1
}

# ============================================
# 1. STOP SERVICES
# ============================================

echo "[1/6] Stopping daemon..."
# Stop through configd (not service status, which returns exit 1)
pkill -f monitor_daemon.py 2>/dev/null || true
sleep 1
rm -f /var/run/devicemonitor.pid
echo "  Daemon stopped"


# ============================================
# 3. AUTOSTART
# ============================================

echo "[3/6] Disabling autostart..."
rm -f /etc/rc.conf.d/devicemonitor

if grep -q "devicemonitor_enable" /etc/rc.conf.local 2>/dev/null; then
    sed -i '' '/devicemonitor_enable/d' /etc/rc.conf.local
fi

echo "  Autostart disabled"

# ============================================
# 4. PLUGIN FILES
# ============================================

echo "[4/6] Removing plugin files..."

# RC script
rm -f /usr/local/etc/rc.d/devicemonitor
rm -f /etc/rc.d/devicemonitor

# Also remove the new script
rm -f /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/daemon_status.sh

# 
rm -f /usr/local/etc/inc/plugins.inc.d/devicemonitor.inc

# Models
rm -rf /usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor

# Controllers
rm -rf /usr/local/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor

# Views
rm -rf /usr/local/opnsense/mvc/app/views/OPNsense/DeviceMonitor

# Scripts
rm -rf /usr/local/opnsense/scripts/OPNsense/DeviceMonitor

# Configd actions
rm -f /usr/local/opnsense/service/conf/actions.d/actions_devicemonitor.conf

# Config files
rm -f /tmp/devicemonitor_config.json

# New JS widget (OPNsense 26.x)
rm -f /usr/local/opnsense/www/js/widgets/DeviceMonitor.js
rm -f /usr/local/opnsense/www/js/widgets/Metadata/DeviceMonitor.xml

echo "  Plugin files removed"

# ============================================
# 5. TRANSLATIONS
# ============================================

echo "[5/6] Removing translations..."
for lang in en_US cs_CZ de_DE fr_FR es_ES it_IT pt_BR nl_NL ru_RU ja_JP zh_CN; do
    rm -f "/usr/local/opnsense/mvc/app/languages/${lang}/LC_MESSAGES/devicemonitor.po"
    rm -f "/usr/local/opnsense/mvc/app/languages/${lang}/LC_MESSAGES/devicemonitor.mo"
    rmdir "/usr/local/opnsense/mvc/app/languages/${lang}/LC_MESSAGES" 2>/dev/null || true
    rmdir "/usr/local/opnsense/mvc/app/languages/${lang}" 2>/dev/null || true
    # Legacy flat layout from v2.9/v2.10 release-asset installs; unreadable by
    # bindtextdomain() and superseded by the <locale>/LC_MESSAGES/ layout above.
    rm -f "/usr/local/opnsense/mvc/app/languages/${lang}_devicemonitor.po"
    rm -f "/usr/local/opnsense/mvc/app/languages/${lang}_devicemonitor.mo"
done
echo "  Translations removed"

# ============================================
# 5b. CORE DOMAIN CATALOGUES (DM-BL-008c)
# ============================================

echo "[5b/6] Restoring core domain catalogues..."
# --- DM-BL-008c core catalogue restore: begin ---
# The installer merges the plugin's keys into /usr/local/share/locale/<locale>/LC_MESSAGES/
# OPNsense.mo, because the views' inline-script strings resolve through the core domain. Put the
# pristine core catalogue back from the copy the installer recorded, or delete a file the
# installer created itself; a catalogue that no longer matches what was injected is never removed.
CORE_LOCALE_STATE=/var/backups/devicemonitor/core-locale
SHA256=$(command -v sha256 2>/dev/null || :)
core_restored=0
core_removed=0
if [ -z "$SHA256" ]; then
    echo "  WARNING: sha256 unavailable; core domain catalogues left unchanged"
elif [ -d "$CORE_LOCALE_STATE" ]; then
    for state in "$CORE_LOCALE_STATE"/*.state; do
        [ -f "$state" ] || continue
        pristine=$(sed -n 's/^pristine=//p' "$state")
        target=$(sed -n 's/^target=//p' "$state")
        installed=$(sed -n 's/^installed=//p' "$state")
        [ -n "$target" ] || continue
        copy="$CORE_LOCALE_STATE/$(basename "$state" .state).OPNsense.mo"
        if [ "$pristine" = absent ]; then
            if [ -f "$target" ] && [ "$("$SHA256" -q "$target")" = "$installed" ]; then
                rm -f "$target"
                rmdir "$(dirname "$target")" 2>/dev/null || true
                rmdir "$(dirname "$(dirname "$target")")" 2>/dev/null || true
                core_removed=$((core_removed + 1))
            else
                echo "  WARNING: $target is not the catalogue this installer created; left in place"
            fi
        elif [ -f "$copy" ]; then
            if [ "$("$SHA256" -q "$copy")" = "$pristine" ]; then
                cp -p "$copy" "$target"
                core_restored=$((core_restored + 1))
            else
                echo "  WARNING: pristine copy for $target does not match its recorded hash; kept at $copy"
            fi
        else
            echo "  WARNING: no pristine copy recorded for $target; left unchanged"
        fi
    done
fi
echo "  Core catalogues: restored=$core_restored removed=$core_removed"
# --- DM-BL-008c core catalogue restore: end ---

# ============================================
# 6. DATABASE AND DATA
# ============================================

if [ "$SILENT_MODE" -eq 1 ]; then
    # Silent mode (reinstall) - DO NOT DELETE DATA!
    echo "[6/6] Preserving database (reinstall)..."
    echo "  /var/db/devicemonitor/devices.db"
else
    # Normal uninstall - remove everything
    echo "[6/6] Removing database..."
    
    if [ -d "/var/db/devicemonitor" ]; then
        rm -rf /var/db/devicemonitor
        echo "  Database removed"
    else
        echo "  Database not found"
    fi
fi

# ============================================
# CLEAR CACHE
# ============================================

if [ "$SILENT_MODE" -eq 0 ]; then
    echo ""
    echo "Clearing cache..."
fi

rm -f /tmp/opnsense_menu_cache.xml
rm -f /tmp/opnsense_acl_cache.json
rm -rf /var/cache/opnsense/templates/* 2>/dev/null || true

# ============================================
# RESTART SERVICES (normal uninstall only)
# ============================================

if [ "$SILENT_MODE" -eq 0 ]; then
    echo ""
    echo "Updating menu and restarting services..."
    
    /usr/local/etc/rc.configure_plugins
    service configd restart
    sleep 2
    configctl webgui restart
    sleep 2
    service php-fpm restart
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Uninstall complete!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "The plugin has been removed from the GUI."
    echo "For a complete refresh, reload the browser with Ctrl+Shift+R."
    echo ""
fi

exit 0