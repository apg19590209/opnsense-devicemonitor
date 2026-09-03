#!/bin/sh

echo "============================================"
echo "  Device Monitor - Installation"
echo "============================================"
echo ""

# ============================================
# [1/9] CHECKS
# ============================================

echo "[1/9] Running pre-installation checks..."

[ "$(id -u)" != "0" ] && {
    echo "  ERROR: This installer must be run as root!"
    exit 1
}
echo "  OK: Root privileges confirmed"

PLUGIN_VER=$(python3 -c "import json; print(json.load(open('src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'))['version'])" 2>/dev/null || echo "?")
echo "  OK: Plugin version: Device Monitor v${PLUGIN_VER}"

OPNSENSE_VER=$(opnsense-version 2>/dev/null | awk '{print $2}')
if [ -n "$OPNSENSE_VER" ]; then
    OPNSENSE_MAJOR=$(echo "$OPNSENSE_VER" | cut -d. -f1)
    OPNSENSE_MINOR=$(echo "$OPNSENSE_VER" | cut -d. -f2)
    OPNSENSE_PATCH=$(echo "$OPNSENSE_VER" | cut -d. -f3)
    if [ "$OPNSENSE_MAJOR" -lt 26 ] || \
       ( [ "$OPNSENSE_MAJOR" -eq 26 ] && [ "$OPNSENSE_MINOR" -lt 1 ] ) || \
       ( [ "$OPNSENSE_MAJOR" -eq 26 ] && [ "$OPNSENSE_MINOR" -eq 1 ] && [ "${OPNSENSE_PATCH:-0}" -lt 5 ] ); then
        echo "  ERROR: OPNsense >= 26.1.5 required; found $OPNSENSE_VER"
        exit 1
    fi
    echo "  OK: OPNsense $OPNSENSE_VER (minimum 26.1.5)"
else
    echo "  WARNING: Unable to determine OPNsense version; continuing..."
fi

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
cd "$SCRIPT_DIR" || exit 1

[ ! -d "src" ] && {
    echo "  ERROR: src/ directory not found!"
    exit 1
}
echo "  OK: Source files found"

if ! command -v msgfmt >/dev/null 2>&1; then
    echo "  -> msgfmt not found; installing gettext-tools..."
    pkg install -y gettext-tools
    if [ $? -ne 0 ] || ! command -v msgfmt >/dev/null 2>&1; then
        echo "  ERROR: gettext-tools installation failed or msgfmt is unavailable"
        exit 1
    fi
    echo "  OK: gettext-tools installed"
else
    echo "  OK: msgfmt available"
fi

# Ensure Nmap is available for targeted new-device security scans.
if ! command -v nmap >/dev/null 2>&1; then
    echo "  -> nmap not found, installing..."
    pkg install -y nmap
    if [ $? -ne 0 ]; then
        echo "  ERROR: nmap installation failed"
        exit 1
    fi
    if ! command -v nmap >/dev/null 2>&1; then
        echo "  ERROR: nmap is still unavailable after installation"
        exit 1
    fi
    echo "  OK: nmap installed"
else
    echo "  OK: nmap available"
fi
# ============================================
# [2/9] REMOVE OLD VERSION
# ============================================

if [ -f "/etc/rc.d/devicemonitor" ] || \
   [ -d "/usr/local/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor" ]; then
    echo ""
    echo "[2/9] Existing installation detected; performing upgrade..."
    if [ -f "$SCRIPT_DIR/uninstall.sh" ]; then
        sh "$SCRIPT_DIR/uninstall.sh" --silent
        echo "  OK: Previous version removed (data preserved)"
    else
        echo "  WARNING: uninstall.sh not found; continuing with overwrite..."
    fi
    sleep 1
else
    echo ""
    echo "[2/9] New installation detected"
fi

# ============================================
# [3/9] DIRECTORIES
# ============================================

echo ""
echo "[3/9] Creating directory structure..."

mkdir -p /usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/Metadata
mkdir -p /usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/Menu
mkdir -p /usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/ACL
mkdir -p /usr/local/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api
mkdir -p /usr/local/opnsense/mvc/app/views/OPNsense/DeviceMonitor
mkdir -p /usr/local/opnsense/mvc/app/languages
mkdir -p /usr/local/opnsense/scripts/OPNsense/DeviceMonitor
mkdir -p /usr/local/opnsense/service/conf/actions.d
mkdir -p /usr/local/opnsense/www/js/widgets/Metadata
mkdir -p /usr/local/etc/inc/plugins.inc.d
mkdir -p /usr/local/etc/rc.d
mkdir -p /etc/rc.d
mkdir -p /var/db/devicemonitor
chmod 755 /var/db/devicemonitor

echo "  OK: Directories created"

# ============================================
# [4/9] RC SCRIPT + SERVICE REGISTRATION
# ============================================

echo ""
echo "[4/9] Installing RC script and service registration..."

if [ -f "src/etc/rc.d/devicemonitor" ]; then
    cp src/etc/rc.d/devicemonitor /usr/local/etc/rc.d/devicemonitor
    chmod +x /usr/local/etc/rc.d/devicemonitor
    ln -sf /usr/local/etc/rc.d/devicemonitor /etc/rc.d/devicemonitor
    echo "  OK: RC script installed (/usr/local/etc/rc.d/)"
else
    echo "  WARNING: RC script not found!"
fi

# Register in Diagnostics -> Services using plugins_services()
if [ -f "src/etc/inc/plugins.inc.d/devicemonitor.inc" ]; then
    cp src/etc/inc/plugins.inc.d/devicemonitor.inc \
       /usr/local/etc/inc/plugins.inc.d/
    chmod 644 /usr/local/etc/inc/plugins.inc.d/devicemonitor.inc
    echo "  OK: Service registered in Diagnostics -> Services"
else
    echo "  WARNING: plugins.inc.d/devicemonitor.inc not found!"
fi

# ============================================
# [5/9] WIDGET
# ============================================

echo ""
echo "[5/9] Installing dashboard widget..."

if [ -f "src/opnsense/www/js/widgets/DeviceMonitor.js" ]; then
    cp src/opnsense/www/js/widgets/DeviceMonitor.js \
       /usr/local/opnsense/www/js/widgets/
    chmod 644 /usr/local/opnsense/www/js/widgets/DeviceMonitor.js
    echo "  OK: Widget JavaScript installed"
else
    echo "  WARNING: DeviceMonitor.js not found!"
fi

if [ -f "src/opnsense/www/js/widgets/Metadata/DeviceMonitor.xml" ]; then
    cp src/opnsense/www/js/widgets/Metadata/DeviceMonitor.xml \
       /usr/local/opnsense/www/js/widgets/Metadata/
    chmod 644 /usr/local/opnsense/www/js/widgets/Metadata/DeviceMonitor.xml
    echo "  OK: Widget metadata installed"
else
    echo "  WARNING: DeviceMonitor.xml not found!"
fi

if [ -f "src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/Metadata/service.xml" ]; then
    cp src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/Metadata/service.xml \
       /usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/Metadata/
    chmod 644 /usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/Metadata/service.xml
    echo "  OK: Service metadata installed"
else
    echo "  WARNING: service.xml not found!"
fi

# ============================================
# [6/9] TRANSLATIONS
# ============================================

echo ""
echo "[6/9] Installing translations..."

if [ -f "src/opnsense/mvc/app/languages/cs_CZ_devicemonitor.po" ]; then
    if command -v msgfmt >/dev/null 2>&1; then
        msgfmt -o /usr/local/opnsense/mvc/app/languages/cs_CZ_devicemonitor.mo \
                  src/opnsense/mvc/app/languages/cs_CZ_devicemonitor.po \
            && echo "  OK: cs_CZ translation compiled" \
            || echo "  ERROR: cs_CZ translation compilation failed"
        msgfmt -o /usr/local/opnsense/mvc/app/languages/en_US_devicemonitor.mo \
                  src/opnsense/mvc/app/languages/en_US_devicemonitor.po \
            && echo "  OK: en_US translation compiled" \
            || echo "  ERROR: en_US translation compilation failed"
    else
        echo "  WARNING: msgfmt is unavailable - translations will not work"
    fi
else
    echo "  WARNING: Translation source files not found"
fi

# ============================================
# [7/9] MVC (Models, Controllers, Views)
# ============================================

echo ""
echo "[7/9] Copying MVC files..."

cp src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/DeviceMonitor.xml \
   /usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/
cp src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/DeviceMonitor.php \
   /usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/
cp src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/Menu/Menu.xml \
   /usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/Menu/
cp src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/ACL/ACL.xml \
   /usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/ACL/
cp src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json \
   /usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/
echo "  OK: Models installed"

cp src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/IndexController.php \
   /usr/local/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/
cp src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/*.php \
   /usr/local/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/
echo "  OK: Controllers installed"

cp src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/*.volt \
   /usr/local/opnsense/mvc/app/views/OPNsense/DeviceMonitor/
echo "  OK: Views installed"

# ============================================
# [8/9] SCRIPTS AND CONFIGURATION
# ============================================

echo ""
echo "[8/9] Installing scripts and configuration..."

cp src/opnsense/scripts/OPNsense/DeviceMonitor/*.py \
   /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/
chmod +x /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/*.py
echo "  OK: Python scripts installed"

cp src/opnsense/scripts/OPNsense/DeviceMonitor/*.sh \
   /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/
chmod +x /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/*.sh
echo "  OK: Shell scripts installed"

cp src/opnsense/scripts/OPNsense/DeviceMonitor/*.php \
   /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/
chmod +x /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/*.php
echo "  OK: PHP scripts installed"

cp src/opnsense/service/conf/actions.d/actions_devicemonitor.conf \
   /usr/local/opnsense/service/conf/actions.d/
echo "  OK: Configd actions installed"

echo 'devicemonitor_enable="YES"' > /etc/rc.conf.d/devicemonitor
chmod 644 /etc/rc.conf.d/devicemonitor
echo "  OK: Autostart enabled"

[ -f "/var/db/known_devices.db" ] && rm -f /var/db/known_devices.db

# ============================================
# [9/9] FINALIZATION AND STARTUP
# ============================================

echo ""
echo "[9/9] Finalizing installation..."

echo "  -> Clearing caches..."
rm -f /tmp/opnsense_menu_cache.xml
rm -f /tmp/opnsense_acl_cache.json
rm -rf /var/cache/opnsense/templates/* 2>/dev/null || true

echo "  -> Updating menus and plugins..."
/usr/local/etc/rc.configure_plugins

echo "  -> Restarting configd..."
service configd restart
sleep 3

echo "  -> Starting Device Monitor daemon..."
pkill -f monitor_daemon.py 2>/dev/null
sleep 1
rm -f /var/run/devicemonitor.pid
configctl devicemonitor start
sleep 2

PID=$(cat /var/run/devicemonitor.pid 2>/dev/null)
if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
    echo "  OK: Daemon running (PID: $PID)"
else
    echo "  WARNING: Daemon failed to start"
    echo "  -> Start manually with: configctl devicemonitor start"
    echo "  -> Log: tail -f /var/log/devicemonitor.log"
fi

echo ""
echo "============================================"
echo "  Device Monitor v${PLUGIN_VER} installed successfully!"
echo "============================================"
echo ""

exit 0