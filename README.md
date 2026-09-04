# OPNsense Device Monitor

**[🇨🇿 Czech version](README_CZ.md)** | **[👨‍💻 More projects by the author](https://github.com/hacesoft?tab=repositories)**

---

Plugin for automatic network device monitoring in OPNsense firewall. Detects new devices on the network using the native OPNsense hostwatch database and sends email or webhook notifications.

---

## 📋 Table of Contents

- [What the plugin does](#what-the-plugin-does)
- [Version history](#version-history)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Plugin structure](#plugin-structure)
- [How the daemon works](#how-the-daemon-works)
- [Troubleshooting](#troubleshooting)
- [Uninstallation](#uninstallation)

---

## What the plugin does

The plugin automatically monitors the network and alerts you about:

- 🆕 **New devices** connecting to the network
- 📊 **Device history** with first/last detection timestamps
- 📧 **Email notifications** with professional HTML design
- 🔔 **Webhook notifications** (ntfy.sh, Discord, custom)
- 🖥️ **Dashboard widget** on the OPNsense Lobby page

---

## Version history

### v2.6 (September 2026) — Detailed targeted Nmap scan history

- Records targeted scan settings, Nmap version, elapsed time, OS hint and email outcome.
- Stores discovered open ports with protocol, service, product, version and extra information.
- Adds expandable scan-history details while keeping the main history table compact.
- Separates Nmap scan success from notification email success.
- Adds backward-compatible database migration for existing v2.5 installations.
- Preserves valid zero-valued Nmap settings.
- Adds translated scan-history detail labels.
- Extends CI validation to the v2.6 development branch.

### v2.5 (September 2026) — Nmap management, history and reliability

- Added configurable **targeted Nmap settings** for enable/disable, top-port count, timing template, host timeout, service/version detection and scans per monitoring cycle.
- Added **retry and backoff** for failed automatic targeted scans: 15 minutes, 1 hour, 6 hours and 24 hours, with automatic retry stopping after five failed attempts.
- Added visible **Nmap queue/retry status** to the Devices table, including Pending, Retry and Failed states.
- Added a per-device **manual targeted Nmap scan** action using the same controlled scan settings without modifying the automatic retry queue.
- Added persistent **Nmap scan history** for manual and automatic scans, including successful, failed and interrupted/incomplete runs.
- Added a dedicated **Nmap Scan History** page with selectable 10, 25, 50 or 100-row views, refresh control and scrollable results.
- Added permanent **known MAC history** so a previously seen device does not become a new-device event merely because its active device record was deleted and later rediscovered.
- Hardened the scan-history API with bounded queries, read-only SQLite access and safer error reporting.
- Hardened the installer with source validation, dependency checks, temporary upgrade backups and syntax validation.
- Added automated **CI validation** for Python, PHP, shell scripts, translations and database migration behavior.

### v2.4 (September 2026) — Targeted security scanning and reliability improvements

- Added optional **targeted Nmap security scans** for newly detected devices that qualify for email notification.
- Targeted scans inspect the top 100 TCP ports using lightweight service/version detection and send a separate formatted security report by email.
- Scan targets are restricted to a single literal IPv4 address; hostnames, ranges and CIDR targets are rejected.
- Added a persistent **database-backed Nmap scan queue** so bursts of new devices are processed safely across multiple Device Monitor cycles instead of being dropped.
- Targeted scans are deliberately rate-limited to **two devices per monitoring cycle** to preserve headroom below the Device Monitor daemon timeout.
- Failed targeted scans remain queued for retry; the queue flag is cleared only after the scan report is successfully sent.
- Targeted scan reports now support both **Local Sendmail / Postfix** and the v2.3 **Direct SMTP** transport.
- The installer now automatically installs **Nmap** when it is not already available.
- Improved Hostwatch de-duplication by selecting the newest IPv4 record for each MAC address directly in SQL.
- Retained the v2.3 configuration merging, SMTP credential protection, deleted-device tombstones, VLAN notification filtering and notification cleanup behavior.
- Translated remaining source-code comments, runtime log messages and API validation messages to English while preserving the existing translation catalogs.
### v2.3 (August 2026) — Direct SMTP and notification improvements

- Added selectable **Email delivery method** in Device Monitor settings.
- **Local Sendmail / Postfix** remains the default and preserves existing installations.
- Added built-in **Direct SMTP** delivery using Python `smtplib`; no additional Python package is required.
- Direct SMTP supports **STARTTLS**, **SSL/TLS**, and unencrypted SMTP.
- Added SMTP server, port, username and password configuration to the UI.
- **Test Email** now uses the currently selected delivery method.
- Existing configuration files are merged with new defaults automatically, so upgrading does not require a configuration reset.
- SMTP credentials are read from the protected Device Monitor configuration instead of being passed on the process command line.
- Configuration containing SMTP credentials is stored with restrictive file permissions.
- Includes the v2.2 Hostwatch fixes: newest Hostwatch record is selected per MAC, deleted devices no longer return from historical records, VLAN notification filtering was corrected, and real Hostwatch `last_seen` values are preserved during quick status updates.

v2.1 (April 2026) — Dnsmasq hostname support
What changed and why
1. Dnsmasq hostname resolution — `get_dnsmasq_descriptions()`
OPNsense users who migrated from the deprecated ISC DHCPv4 to Dnsmasq DNS & DHCP (the recommended replacement as of OPNsense 25.7+) had empty hostnames in Device Monitor. The previous code only read hostnames from `config.xml → dhcpd` (ISC DHCP static mappings).
A new function reads hostname data from the Dnsmasq Host Overrides section of `config.xml`. The correct XML structure for Dnsmasq entries is:
```xml
<hosts uuid="...">
  <host>MyDevice</host>          ← hostname field
  <hwaddr>aa:bb:cc:dd:ee:ff</hwaddr>  ← MAC address (note: hwaddr, NOT hw)
  <ip>192.168.1.100</ip>
  <descr>My Device Description</descr>
</hosts>
```
> ⚠️ The MAC address field is `<hwaddr>` — not `<hw>` as one might expect. This was confirmed by inspecting a live `config.xml`.
2. ISC DHCP disabled interfaces are now skipped
When an ISC DHCP interface is disabled (checkbox unchecked in the UI), OPNsense sets no `<enable>` child element inside that interface's config block. The updated `get_dhcp_descriptions()` function skips any ISC interface that lacks the `<enable>` tag, preventing stale data from disabled interfaces from appearing as hostnames.
3. Hostname source priority
Hostname resolution now follows a clear priority chain:
```
1. custom_hostname  (manually set in Device Monitor UI — highest priority)
2. Dnsmasq          (Host Overrides with MAC → hostname mapping)
3. ISC DHCP         (static mappings, hostname field preferred over descr)
```
Dnsmasq overwrites ISC data for the same MAC address via `dict.update()`:
```python
dhcp_descriptions = get_dhcp_descriptions()     # ISC DHCP (enabled interfaces only)
dnsmasq_descriptions = get_dnsmasq_descriptions()  # Dnsmasq Host Overrides
dhcp_descriptions.update(dnsmasq_descriptions)  # Dnsmasq wins on conflict
```
4. Hostname field preference within ISC DHCP
Previously, the ISC DHCP reader used only `<descr>` (the description/note field). It now prefers `<hostname>` and falls back to `<descr>` only when `<hostname>` is absent or empty. This matches how hostnames actually appear in DNS and DHCP lease tables.


### v2.0 (April 2026) — Major overhaul

This version is a complete architectural rewrite focused on deep integration with OPNsense 26.x. Many components that were previously custom-built are now replaced by native OPNsense mechanisms.

#### What changed and why

**1. Service registration — `plugins.inc.d/devicemonitor.inc`**

In previous versions, the daemon was completely invisible to OPNsense. It did not appear in *System → Diagnostics → Services*, so there was no way to start/stop/restart it from the GUI.

The fix is a new file `src/etc/inc/plugins.inc.d/devicemonitor.inc` which registers the service using OPNsense's native `plugins_services()` mechanism.

```php
function devicemonitor_services()
{
    $services = [];
    $services[] = [
        'description' => gettext('Device Monitor - network device tracking'),
        'configd' => [
            'restart' => ['devicemonitor restart'],
            'start'   => ['devicemonitor start'],
            'stop'    => ['devicemonitor stop'],
        ],
        'name'    => 'devicemonitor',
        'pidfile' => '/var/run/devicemonitor.pid',
    ];
    return $services;
}
```

**2. Daemon status check — `daemon_status.sh`**

The previous approach used `service devicemonitor status` in the configd `[status]` action. On FreeBSD, this command returns exit code 1 even when the service is running normally (it returns 1 = "not managed by rc.d in the traditional sense"). Because configd type `script_output` treats any non-zero exit as an error, every status check produced `Execute error`.

The fix is a dedicated shell script that checks the pidfile directly:

```sh
#!/bin/sh
PIDFILE="/var/run/devicemonitor.pid"
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "running"
        exit 0
    fi
    rm -f "$PIDFILE"   # stale pidfile cleanup
fi
echo "stopped"
exit 0
```

**3. `actions_devicemonitor.conf` — `|| true` on start/stop/restart**

Without `|| true`, if the daemon was already running and configd tried to start it again, `service devicemonitor start` returned a non-zero exit code (daemon already running), which configd interpreted as an error and showed `Error (1)`. Adding `|| true` ensures configd always sees success.

The `[status]` action now calls `daemon_status.sh` instead of `service devicemonitor status`.

**4. `rc.d/devicemonitor` — added `procname`, fixed default**

Two fixes:
- Default changed from `"YES"` to `"NO"` — FreeBSD convention: the script itself must default to disabled; activation is done by `/etc/rc.conf.d/devicemonitor`
- Added `procname="/usr/local/bin/python3"` — without this, `rc.d` cannot find the running process and every `start` creates a new zombie process. 

**5. `service.xml` — fixed tag name, added `<pidfile>`, fixed `<commands>`**

Three bugs in one file:
- `<n>DeviceMonitor</n>` → `<name>DeviceMonitor</name>` — OPNsense did not recognize the `<n>` tag
- Added `<pidfile>/var/run/devicemonitor.pid</pidfile>` — needed for the green/red status dot
- `<commands>` changed from shell commands (`service devicemonitor start`) to configd action names (`devicemonitor start`)

**6. `ServiceController.php` — start/stop/restart via `configdRun()`**

Previously, the PHP API controller called `exec('service devicemonitor start')` directly. This bypasses OPNsense's privilege model. All service control now goes through `$backend->configdRun('devicemonitor start')`.

**7. Dashboard widget — fixed detached DOM issue**

The widget's `onWidgetTick()` method was updating `this.$container.find('.dm-total')`. However, OPNsense's widget framework copies the markup into the DOM rather than inserting the original jQuery object, so `this.$container` pointed to a detached element — `.find()` worked silently but changes were never visible on screen.

Fixed by giving each element a unique `id` and selecting directly from the document:

```javascript
// Before (broken — updates detached element)
this.$container.find('.dm-total').text(stats.total);

// After (correct — selects from live DOM)
$('#dm-total').text(stats.total);
```

Also fixed: the widget was calling `/api/devicemonitor/service/status` for device counts (which returns daemon status, not stats). It now correctly calls `/api/devicemonitor/devices/stats`.

**8. `install.sh` — complete rewrite**

Key changes:
- Zombie process cleanup before daemon start (`pkill -f monitor_daemon.py`)
- Daemon started via `configctl devicemonitor start` instead of `service devicemonitor start`
- Daemon verified via pidfile + `kill -0` instead of `service devicemonitor status`
- Removed broken `service php-fpm restart` and `configctl webgui restart` calls
- Added `plugins.inc.d/devicemonitor.inc` installation step
- Fixed step numbering (was `[6/11]` followed by `[6/10]`)

**9. `uninstall.sh` — fixed daemon stop**

Previously used `service devicemonitor status` which returned exit 1, causing the stop to fail. Now uses `pkill -f monitor_daemon.py` which always works regardless of pidfile state.

Also removed broken `configctl webgui restart` and `service php-fpm restart` calls — these are either not available or unnecessary on OPNsense 26.x.

---

### v1.x (January 2026)

- **OPNsense 26.x compatibility fix:** Removed `$this->sessionClose()` calls from controllers. This function was removed in OPNsense 26.0 and caused crashes when called. Added automatic version detection to maintain backward compatibility with 25.x.

---

## Features

### 🎯 Core features

✅ **Device discovery** via OPNsense hostwatch SQLite database (`/var/db/hostwatch/hosts.db`)
✅ **Email notifications** — professional HTML emails with inline CSS
✅ **Webhook notifications** — ntfy.sh, Discord, custom HTTP POST endpoints
✅ **Device history** — first/last detection timestamps
✅ **Vendor lookup** — manufacturer from MAC address (IEEE OUI database)

### 🖥️ Web interface

✅ **Dashboard widget** — shows total/online device count and daemon status on Lobby page
✅ **Device list** — searchable, sortable table with delete actions
✅ **Settings page** — all configuration in one place with test buttons
✅ **Service control** — visible in *System → Diagnostics → Services* with start/stop/restart buttons

### 📊 Technical

✅ **SQLite database** — fast storage, no external database needed
✅ **Background daemon** — Python process managed by FreeBSD rc.d
✅ **configd integration** — all service actions go through OPNsense configd
✅ **Logging** — `/var/log/devicemonitor.log`

---

## Requirements

- **OPNsense 26.1.5 or newer**
- **SSH access** (System → Settings → Administration → Secure Shell)
- **Root account** or admin with CLI access

> ⚠️ Versions prior to 26.1.5 are not supported. The plugin uses APIs and mechanisms introduced in 26.x.

---

## Installation

### Method 1: Download release ZIP + WinSCP

1. Download the **v2.6 Source code (zip)** from:
   https://github.com/apg19590209/opnsense-devicemonitor/releases/tag/v2.6
2. Enable SSH in OPNsense: **System -> Settings -> Administration -> Secure Shell -> Enable**.
3. Upload the ZIP to `/tmp/` using WinSCP.
4. Connect by SSH and install:

```sh
cd /tmp
unzip opnsense-devicemonitor-2.6.zip
cd opnsense-devicemonitor-2.6
sh install.sh
```

No reboot is normally required.

### Method 2: Direct SSH

```sh
ssh root@your.opnsense.ip
cd /tmp
fetch https://github.com/apg19590209/opnsense-devicemonitor/archive/refs/tags/v2.6.zip
unzip v2.6.zip
cd opnsense-devicemonitor-2.6
sh install.sh
```

### Upgrading an existing installation

Before upgrading, back up the runtime data:

```sh
tar -czf /root/devicemonitor-backup.tgz /var/db/devicemonitor
```

Then install v2.6 using either method above.

Existing configuration and device data are preserved during the upgrade.

After installation, verify the daemon:

```sh
/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/daemon_status.sh
```

Expected result:

```text
running
```

### Targeted Nmap scanning in v2.6

For newly detected devices that qualify for an email notification, v2.6 can:

- run targeted scans automatically, with the feature independently enabled or disabled;
- scan a configurable number of top TCP ports (default: 100);
- use a configurable Nmap timing template and host timeout;
- optionally perform lightweight service/version detection;
- queue scans persistently in SQLite;
- process a configurable number of queued devices per monitoring cycle (default: 2);
- retry failed automatic scans using bounded backoff and stop after five failed attempts;
- run an on-demand targeted scan manually from the Devices page;
- record manual and automatic scan outcomes in persistent scan history;
- send a separate formatted scan report by email.

Existing devices are not automatically added to the automatic Nmap queue during an upgrade.

---

## Configuration

Go to: **Services → DeviceMonitor → Settings**

### Basic

| Setting | Description |
|---------|-------------|
| Enable Device Monitor | Enable/disable scanning |
| Scan Interval | How often to scan (5–30 minutes) |

### Email notifications

Device Monitor offers two independent email delivery methods:

- **Local Sendmail / Postfix** — the default and backward-compatible method. It uses `/usr/local/sbin/sendmail`, so a working local mail transport such as the OPNsense `os-postfix` plugin must be configured.
- **Direct SMTP (built into Device Monitor)** — connects directly to the configured SMTP server using Python `smtplib`, without requiring Postfix or Monit for message delivery.

| Setting | Description |
|---------|-------------|
| Enable Email | Enable email notifications |
| Email (To) | Recipient address |
| Email (From) | Sender address |
| Email delivery method | Select Local Sendmail/Postfix or Direct SMTP |
| SMTP Server | SMTP hostname or IP address (Direct SMTP only) |
| SMTP Port | SMTP port, typically 587 for STARTTLS or 465 for SSL/TLS |
| Encryption | STARTTLS, SSL/TLS, or None |
| SMTP Username | Optional SMTP authentication username |
| SMTP Password | Optional SMTP authentication password |
| Test Email | Save the current settings and test the selected delivery method |

Existing installations continue to use **Local Sendmail / Postfix** after upgrading unless Direct SMTP is explicitly selected.

### Webhook notifications

| Setting | Description |
|---------|-------------|
| Enable Webhook | Enable webhook notifications |
| Webhook URL | Target URL |
| Test Webhook | Send a test payload |

**Supported webhook types:**

- **ntfy.sh** — `https://ntfy.sh/yourSecretTopic`
- **Discord** — `https://discord.com/api/webhooks/...`
- **Generic** — any HTTP POST endpoint receiving JSON

---

## Usage

### Lobby dashboard widget

After installation, add the **Device Monitor** widget to the Lobby dashboard. It shows:
- Daemon status (Running / Stopped)
- Total device count
- Online device count

### Device list

**Services → DeviceMonitor → Devices**

Columns: MAC, Vendor, IP, Hostname, First Seen, Last Seen, Actions

### Service control

**System → Diagnostics → Services → devicemonitor**

Start, stop, restart the daemon directly from the GUI. The green/red status dot reflects the actual process state via pidfile.

### Logs

```bash
# Live log
tail -f /var/log/devicemonitor.log

# Filter by type
grep EMAIL /var/log/devicemonitor.log
grep WEBHOOK /var/log/devicemonitor.log
grep SCAN /var/log/devicemonitor.log
```

---

## Plugin structure

```
src/
├── etc/
│   ├── rc.d/
│   │   └── devicemonitor              # FreeBSD rc.d service script
│   └── inc/
│       └── plugins.inc.d/
│           └── devicemonitor.inc      # Service registration for Diagnostics → Services
├── opnsense/
│   ├── mvc/app/
│   │   ├── controllers/OPNsense/DeviceMonitor/
│   │   │   ├── IndexController.php
│   │   │   └── Api/
│   │   │       ├── ConfigController.php
│   │   │       ├── DevicesController.php
│   │   │       └── ServiceController.php
│   │   ├── models/OPNsense/DeviceMonitor/
│   │   │   ├── DeviceMonitor.php
│   │   │   ├── DeviceMonitor.xml
│   │   │   ├── defaults.json
│   │   │   ├── Metadata/
│   │   │   │   └── service.xml        # MVC service metadata
│   │   │   ├── Menu/Menu.xml
│   │   │   └── ACL/ACL.xml
│   │   └── views/OPNsense/DeviceMonitor/
│   │       ├── devices.volt
│   │       ├── settings.volt
│   │       └── service_widget.volt
│   ├── scripts/OPNsense/DeviceMonitor/
│   │   ├── monitor_daemon.py          # Background daemon
│   │   ├── scan_network.py            # Network scan script
│   │   ├── daemon_status.sh           # Reliable status check via pidfile
│   │   ├── NotificationHandler.php
│   │   ├── notify_email.php
│   │   └── notify_webhook.php
│   ├── service/conf/actions.d/
│   │   └── actions_devicemonitor.conf # configd action definitions
│   └── www/js/widgets/
│       ├── DeviceMonitor.js           # Lobby dashboard widget
│       └── Metadata/
│           └── DeviceMonitor.xml      # Widget metadata and endpoints
```

### Runtime files

```
/var/run/devicemonitor.pid             # Daemon PID
/var/log/devicemonitor.log             # Log file
/var/db/devicemonitor/
├── devices.db                         # SQLite device database
└── config.json                        # Runtime configuration
/etc/rc.conf.d/devicemonitor           # Autostart flag
```

### API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/devicemonitor/devices/stats` | Total and online device count |
| GET | `/api/devicemonitor/service/status` | Daemon status (running/stopped) |
| POST | `/api/devicemonitor/service/start` | Start daemon |
| POST | `/api/devicemonitor/service/stop` | Stop daemon |
| POST | `/api/devicemonitor/service/restart` | Restart daemon |
| POST | `/api/devicemonitor/service/scan` | Trigger manual scan |
| GET | `/api/devicemonitor/config/get` | Get configuration |
| POST | `/api/devicemonitor/config/set` | Save configuration |
| POST | `/api/devicemonitor/config/testemail` | Send test email |
| POST | `/api/devicemonitor/config/testwebhook` | Send test webhook |

---

## How the daemon works

```
monitor_daemon.py (background process)
    │
    ├── reads /var/db/devicemonitor/config.json  (scan interval, enabled flag)
    ├── reads /var/db/hostwatch/hosts.db          (OPNsense native discovery)
    ├── writes /var/db/devicemonitor/devices.db   (known devices, notification queue)
    └── writes /var/log/devicemonitor.log

configd (OPNsense configuration daemon)
    │
    ├── devicemonitor start   → service devicemonitor start || true
    ├── devicemonitor stop    → service devicemonitor stop || true
    ├── devicemonitor restart → service devicemonitor restart || true
    └── devicemonitor status  → daemon_status.sh (pidfile check, always exit 0)

rc.d/devicemonitor
    │
    ├── uses /usr/sbin/daemon -f -p /var/run/devicemonitor.pid python3 monitor_daemon.py
    ├── procname="/usr/local/bin/python3"   (needed for stop to find the process)
    └── default: devicemonitor_enable="NO"  (activated by /etc/rc.conf.d/devicemonitor)
```

---

## Troubleshooting

### Plugin does not appear in Services

```bash
# Verify the .inc file exists (NOT .php!)
ls /usr/local/etc/inc/plugins.inc.d/devicemonitor.inc

# Verify PHP can load the function
php -r "require_once('/usr/local/etc/inc/plugins.inc.d/devicemonitor.inc'); var_dump(devicemonitor_services());"

# Reload plugin registry
/usr/local/etc/rc.configure_plugins
```

### Daemon control shows "Execute error"

```bash
# Check that daemon_status.sh exists and is executable
ls -la /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/daemon_status.sh

# Test it manually (must print "running" or "stopped", never an error)
sh /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/daemon_status.sh

# Check configd actions are loaded
configctl configd actions | grep devicemonitor
```

### Multiple zombie daemon processes

```bash
# Check how many are running
ps aux | grep monitor_daemon | grep -v grep

# Kill all instances
pkill -f monitor_daemon.py
rm -f /var/run/devicemonitor.pid

# Start fresh
configctl devicemonitor start
```

Root cause: the RC script was missing `procname`, so `rc.d` could not detect the running process and started a new one every time. Fixed in v2.0 by adding `procname="/usr/local/bin/python3"` to the RC script.

### Widget shows dashes, no data

```bash
# Verify the stats endpoint works
curl -k -u "APIKEY:APISECRET" https://localhost/api/devicemonitor/devices/stats
# Should return: {"total": N, "online": N}

# Verify the status endpoint works
curl -k -u "APIKEY:APISECRET" https://localhost/api/devicemonitor/service/status
# Should return: {"result": "running", ...}
```

If the endpoints return data but the widget still shows dashes, clear browser cache (Ctrl+Shift+R) and check the browser console for JavaScript errors.

### Email notifications not working

```bash
# Test from command line
php /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/notify_email.php

# Check logs
grep EMAIL /var/log/devicemonitor.log
```

### Daemon won't start

```bash
# Check log for startup errors
tail -30 /var/log/devicemonitor.log

# Run daemon manually to see errors
/usr/local/bin/python3 /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/monitor_daemon.py

# Check that defaults.json is readable
cat /usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json
```

### Corrupted database

```bash
cp /var/db/devicemonitor/devices.db /var/db/devicemonitor/devices.db.backup
rm /var/db/devicemonitor/devices.db
configctl devicemonitor restart
```

---

## Uninstallation

### Method 1: uninstall.sh (recommended)

```bash
cd /path/to/opnsense-devicemonitor
sh uninstall.sh
```

This removes all files, stops the daemon, disables autostart, and clears caches. The database `/var/db/devicemonitor/devices.db` is deleted.

### Method 2: Silent uninstall (preserves database)

```bash
sh uninstall.sh --silent
```

Used internally by `install.sh` during upgrades. Removes all files but keeps the database.

### Method 3: Manual

```bash
pkill -f monitor_daemon.py
rm -f /var/run/devicemonitor.pid
rm -f /etc/rc.conf.d/devicemonitor
rm -f /usr/local/etc/rc.d/devicemonitor
rm -f /etc/rc.d/devicemonitor
rm -f /usr/local/etc/inc/plugins.inc.d/devicemonitor.inc
rm -rf /usr/local/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor
rm -rf /usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor
rm -rf /usr/local/opnsense/mvc/app/views/OPNsense/DeviceMonitor
rm -rf /usr/local/opnsense/scripts/OPNsense/DeviceMonitor
rm -f /usr/local/opnsense/service/conf/actions.d/actions_devicemonitor.conf
rm -f /usr/local/opnsense/www/js/widgets/DeviceMonitor.js
rm -f /usr/local/opnsense/www/js/widgets/Metadata/DeviceMonitor.xml
rm -rf /var/db/devicemonitor        # WARNING: deletes device database
rm -f /var/log/devicemonitor.log
/usr/local/etc/rc.configure_plugins
service configd restart
```

---

## Support

**GitHub Issues:** https://github.com/hacesoft/opnsense-devicemonitor/issues

**Author:**
- GitHub: [@hacesoft](https://github.com/hacesoft)
- Web: [hacesoft.cz](https://hacesoft.cz)

---

## License

MIT License — see [LICENSE](LICENSE)

# ============================================
# [scanhistory.volt] Nmap scan history page
# ============================================

msgid "Nmap Scan History"
msgstr "Nmap Scan History"

msgid "Refresh scan history"
msgstr "Refresh scan history"

msgid "Rows"
msgstr "Rows"

msgid "Started"
msgstr "Started"

msgid "Finished"
msgstr "Finished"

msgid "Error"
msgstr "Error"
