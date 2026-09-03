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
rm -f /usr/local/opnsense/mvc/app/languages/cs_CZ_devicemonitor.po
rm -f /usr/local/opnsense/mvc/app/languages/cs_CZ_devicemonitor.mo
rm -f /usr/local/opnsense/mvc/app/languages/en_US_devicemonitor.po
rm -f /usr/local/opnsense/mvc/app/languages/en_US_devicemonitor.mo
echo "  Translations removed"

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