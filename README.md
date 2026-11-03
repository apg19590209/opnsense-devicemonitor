# OPNsense Device Monitor

**[🇨🇿 Czech version](README_CZ.md)** | **[👨‍💻 More projects by the author](https://github.com/hacesoft?tab=repositories)**

---

Plugin for automatic network device monitoring in OPNsense firewall. Detects new devices on the network using the native OPNsense hostwatch database and sends email or webhook notifications.

> **Current release: 2.13.3** — payload `release/v2.13.3-runtime.manifest` (40 targets),
> built as `dm-v2.13.3-runtime.tar.gz` and not yet deployed. 2.13.2 (`74e1f6f`, tag
> `v2.13.2`) stays the release running on the testbed `192.168.20.23` and on the CARP pair
> `192.168.20.253` (master) / `.252` (standby). 2.13.3 carries the pruning remediation of
> Decision 62: verified ownership for pruning, a complete installed-target record, pinned
> install inputs, an idempotent repair install, a hash-verified rollback and append-only
> status output. The Installation section below documents the guarded
> `install-unattended.sh --host <hostname>` flow; `PROJECT_STATE.md` holds the release
> block, the deployment records and the rollback ids.

> **Translations:** the interface is available in English, Czech, German, French, Spanish, Italian, Portuguese (Brazil), Dutch, Russian, Japanese and Simplified Chinese. All translations except English and Czech are machine-generated — native-speaker corrections are welcome.

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

### v2.13.3 (November 2026) — pruning you can prove, and a repair that repeats

- **Pruning requires proof of ownership.** A path is removed only when the previous
  install's own record shows it was installed *and* the file still matches the digest that
  record carries, or when a published historical release manifest shipped that exact digest
  and the path is inside the plugin's namespaces. Everything else is retained and reported
  (`RETAINED modified <path>`), so a hand-edited or third-party file is never deleted.
- **Legacy leftovers are cleaned on the first upgrade.** `release/legacy-targets.txt`
  carries the published digests of every release manifest from v2.9 to v2.13.2, so a node
  coming from an older line loses e.g. the v2.9 `cs_CZ_devicemonitor.po` catalogues that no
  release ships any more — something 2.13.2 could never do, because it had no record yet.
- **The record is the whole target set.** `/var/db/devicemonitor/installed-manifest.txt` now
  records manifest targets *and* the generated catalogues (11 `.mo`, 10 merged core
  catalogues) with their digests, so a release that drops a language can identify and remove
  the catalogue it no longer produces. The current side of the diff is the running install's
  own target plan, so the catalogues a run builds can never be classified as stale.
- **Every executed input is pinned.** `release/release-inputs.sha256` covers the manifest,
  the prune helper, the legacy evidence and the catalogue merge helper;
  `release/verify-release-inputs.sh` enforces it and the installer pins that file inline. A
  tampered helper aborts the run before anything is written.
- **A repair install is genuinely idempotent.** Re-installing the same payload skips every
  byte-identical target — content, mode, owner and mtime are preserved — and reports
  `unchanged=<n>`. The same version is now an accepted predecessor.
- **The rollback verifies itself.** Both halves (replaced targets and pruned files) restore
  from one backup directory, every restore is digest-checked and a damaged backup is a
  reported `ROLLBACK_FAILED` instead of a silent wrong file.
- **Status output is append-only**: `CHECK_OK` gains `legacy_prunable=` and `retained=`,
  `INSTALL_OK` gains `unchanged=`, and the 2.13.2 keys keep their positions.

### v2.13.2 (November 2026) - HA / CARP awareness and restored service-state ageing

- **HA / CARP tab** under Services -> Device Monitor -> Settings: detected role, effective
  mode, whether this node is observing, and the CARP virtual IPs with their state.
- **Standby safety**: a CARP backup does not observe services, so infrastructure-service
  discovery and service alerts are deferred to the master instead of inventing outages.
  `ha_carp_enabled`, `ha_role_override` (auto / master / backup) and
  `ha_notify_failover` control it; the notifier reports role transitions on the existing
  email and webhook channels.
- **A standby ages its own inventory** even while it refuses observation, so a long-lived
  backup does not accumulate stale verdicts until a failover.
- **Service-state ageing restored** on this line: `unavailable` verdicts age to `unknown`
  after 7 days without observation, rows for hosts unseen for 30 days are retired, the
  pass refuses to run when no host looks fresh (a stopped hostwatch), and an address with
  no device row is never retired. Operators can run it with `--age-services [--dry-run]`.

### v2.10 (September 2026) — Nine major UI language translations

- Adds German, Spanish, French, Italian, Japanese, Dutch, Portuguese, Russian and Simplified Chinese translations in addition to the existing English and Czech.
- Adds per-network-identity service email alerts with clearer delivery warnings.

### v2.9 (September 2026) — Fail-closed monitored-interface scoping

- Adds opt-in, single-host full TCP Port Discovery (1–65535) with bounded scans, per-device weekly selection, searchable scan history and service archiving. UDP ports are not scanned.
- Keeps table headers readable and scrollable at narrow widths, and preserves keyboard focus during Devices refresh.

- Adds **Monitored Interfaces**: discovery, priming, status counters, notifications and targeted scans are scoped to the explicitly selected interfaces; an empty selection fails closed (nothing is scanned).
- Supersedes LAN-only Hostwatch priming with selected-interface/subnet priming.
- Prevents targeted-scan starvation: out-of-scope queued scans no longer consume the in-scope batch limit.
- Fixes the Devices-page header counters so **Total Devices** and **Online** match the filtered rows.

### v2.8 (September 2026) — Infrastructure services and device identity improvements

- Adds the dedicated **Infrastructure Services** inventory with verified DHCP, DNS, NTP, SSH, Web/Admin, SMB/NFS, remote-access, SNMP, directory/authentication and VPN service discovery.
- Uses bounded protocol verification, existing targeted Nmap evidence and authoritative local WireGuard runtime state; automatic discovery does not perform broad fresh Nmap sweeps.
- Expands **IP and MAC Conflicts** with Unresolved/Resolved status, filtering and Resolve/Reopen actions while preserving event history.
- Adds Kea DHCP hostname enrichment for detected device hostnames.
- Separates user-assigned **Friendly Name** from detected **Hostname**, preserving detected network identity across edits and scans.
- Adds Friendly Name, Hostname, First Seen and Last Seen presentation/export improvements.
- Standardises project-owned English text to UK English while preserving required technical identifiers and syntax.
- Corrects licence metadata to **BSD 2-Clause License**, matching the repository `LICENSE` file.

### v2.7 (September 2026) — Device identity anomaly detection

- Adds read-only Kea DHCP identity-source detection and normalised IPv4 lease evidence when available.
- Correlates Hostwatch and Kea evidence to detect conflicting device identity without changing device state.
- Detects duplicate ownership of the same non-link-local IPv6 address across different MAC addresses while excluding normal link-local and multiple-address IPv6 behaviour.
- Records identity anomalies as observational SQLite events; no automatic blocking, deletion, firewall changes or remediation is performed.
- Adds a dedicated **Identity Events** API and UI with severity, MAC/IP/interface evidence and expandable event details.
- Refines Settings into Monitoring, Nmap Scanning, Email Notifications, Webhook Notifications and About sections.
- Extends automated CI validation to the `v2.7-development` branch.
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
- Added automated **CI validation** for Python, PHP, shell scripts, translations and database migration behaviour.

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
- Retained the v2.3 configuration merging, SMTP credential protection, deleted-device tombstones, VLAN notification filtering and notification cleanup behaviour.
- Translated remaining source-code comments, runtime log messages and API validation messages to English while preserving the existing translation catalogues.
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
- `<n>DeviceMonitor</n>` → `<name>DeviceMonitor</name>` — OPNsense did not recognise the `<n>` tag
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
✅ **Monitored Interfaces** — fail-closed scoping to selected interfaces/VLANs
✅ **Email notifications** — professional HTML emails with inline CSS
✅ **Webhook notifications** — ntfy.sh, Discord, custom HTTP POST endpoints
✅ **Device history** — first/last detection timestamps
✅ **Vendor lookup** — manufacturer from MAC address (IEEE OUI database)
✅ **Identity anomaly detection** — correlates Hostwatch, Kea and IPv6 evidence without automatic remediation

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
- **Nmap** — used by targeted security scanning; the installer installs it automatically
  (`pkg install -y nmap`) when it is not already present.

> ⚠️ Versions prior to 26.1.5 are not supported. The plugin uses APIs and mechanisms introduced in 26.x.

---

## Installation

Current payload: `dm-v2.13.3-runtime.tar.gz`, built from `release/v2.13.3-runtime.manifest`
(40 hash-verified targets). The bundle carries the runtime files, the 11 gettext
catalogues, `install.sh` / `install-unattended.sh` / `uninstall.sh`, the manifest, the
pinned-inputs file with its verifier, the catalogue merge helper and the prune helper with
its legacy ownership evidence. `install.sh` is a thin wrapper that execs
`install-unattended.sh`, which is the authoritative procedure.

### Method 1: bundle over WinSCP

1. Download `dm-v2.13.3-runtime.tar.gz` from the release assets.
2. Enable SSH in OPNsense: **System → Settings → Administration → Secure Shell → Enable**.
3. Upload the bundle to `/tmp/` with WinSCP.
4. Extract and install:

```sh
cd /tmp
mkdir dm-v2.13.3
tar -xzf dm-v2.13.3-runtime.tar.gz -C dm-v2.13.3
cd dm-v2.13.3
sh install.sh --host "$(/bin/hostname)"
```

### Method 2: direct SSH

```sh
ssh root@your.opnsense.ip
cd /tmp
fetch https://github.com/apg19590209/opnsense-devicemonitor/releases/download/v2.13.3/dm-v2.13.3-runtime.tar.gz
mkdir dm-v2.13.3
tar -xzf dm-v2.13.3-runtime.tar.gz -C dm-v2.13.3
cd dm-v2.13.3
sh install.sh --host "$(/bin/hostname)"
```

`--host` must match the exact output of `/bin/hostname`, otherwise the installer
aborts before touching anything. Add `--check` for a dry run, which validates
everything and prints a report without writing:

```text
CHECK_OK version=2.13.3 predecessor=2.13.2 files=61 core_locales=10 prunable=0 daemon_running=1 host=... legacy_prunable=0 retained=0
INSTALL_OK version=2.13.3 files=61 core_locales=10 pruned=0 backup=/var/backups/devicemonitor/install-v213.XXXXXX daemon_restarted=1 unchanged=0 repaired=0
```

Both lines are a contract, not prose: keys are only ever **appended**, so the 2.13.2 order
is a prefix of the current one and a parser that reads `key=value` pairs keeps working
across releases. When a prune candidate is refused, the plan is listed before the status
line (`PRUNE_PLAN=<RECORD|LEGACY> <path>`) and the refusal is reported on stderr as
`PRUNE_RETAINED <reason> <path>`; the last `CHECK_OK` line on stdout is always the summary.

### What the installer verifies and does

1. Runs as root, on FreeBSD, on OPNsense, with a hostname matching `--host`.
2. Reads the installed version and accepts a predecessor of 2.8 … 2.13.3, including the
   version it is installing (a repair). A payload installed on an unexpected version aborts
   rather than upgrading blind.
3. Verifies `release/release-inputs.sha256` against the digest pinned in the script, then
   every input it lists — the manifest, the prune helper, the legacy evidence and the
   catalogue merge helper — and only then reads the pinned SHA256 of the manifest, its row
   count (40) and the staged target count (61, or 62 on a fresh install), hashing **every**
   source file before a single installed file is replaced.
4. Writes a plan of `old hash → new hash` per target and a timestamped rollback
   backup under `/var/backups/devicemonitor/install-v213.<id>/` (`files/` + `plan`).
5. Installs with the mode recorded in the manifest, compiles the 11 catalogues with
   `msgfmt --check`, merges the plugin keys into the 10 core catalogues that can host
   them (DM-BL-008c, pristine copies recorded for `uninstall.sh`), clears the OPNsense
   menu cache, restarts `configd`, cycles the daemon (stop → wait for exit → start)
   and stops the installation if the daemon does not come back. A target that is already
   byte-identical is left exactly as it is (mode, owner and mtime preserved) and counted in
   `unchanged=<n>`.
6. Re-hashes every installed file and runs `PRAGMA quick_check` on
   `/var/db/devicemonitor/devices.db`.
7. **Prunes** what a previous install owned but this run no longer installs.
   `release/prune-plan.sh` diffs the previous record at
   `/var/db/devicemonitor/installed-manifest.txt` (path + digest per target) and the
   published digests in `release/legacy-targets.txt` against the full target set of this
   run. A path is removed only with proof of ownership — the record's digest still matches,
   or a historical manifest published that digest — and only inside the plugin's four
   namespaces. Everything else is retained and reported; each removal is backed up into the
   rollback directory first. `--check` reports `prunable=<n>`, `legacy_prunable=<n>` and
   `retained=<n>`; a real run reports `pruned=<n>` in `INSTALL_OK`.

Any mismatch rolls the node back — replaced targets first, then pruned files, every restore
digest-verified — and prints `ROLLBACK_ATTEMPTED=/var/backups/devicemonitor/install-v213.<id>`.
Nothing is left half-installed.

### Verifying after install

```sh
/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/daemon_status.sh   # expect: running
grep -m1 version /usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json
```

To prove the node matches the bundle byte for byte, from the extracted bundle:

```sh
cd /tmp/dm-v2.13.3
while read -r h m s t; do
    [ "$(sha256 -q "$t")" = "$h" ] || echo "MISMATCH $t"
done < release/v2.13.3-runtime.manifest
```

### Upgrading an existing installation

### Upgrading from 2.10, 2.11 or 2.12

Install the current bundle **directly** - no staged hop is required. The installer
accepts `2.8`, `2.9`, `2.10`, `2.11`, `2.12`, `2.13` and `2.13.1` as predecessors and
reaches the same final state from any of them:

| Property | Evidence |
|---|---|
| Every schema change is additive (`CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN`), so one `init_db()` migrates in place | `tests/test_upgrade_from_v2_10.py` builds a database with the **v2.10 code**, then upgrades it with the shipped code |
| Added columns are backfilled, never left `NULL` for existing rows | that test asserts `last_checked` is backfilled from the old `last_verified` |
| Device and service rows survive, and re-running the migration changes nothing | same test: 1 device / 2 services before and after, two extra `init_db()` calls are no-ops |
| No file is orphaned | the 2.10 manifest (38 targets) is a subset of the current one (40): nothing was removed, `notify_failover.php` and `actions_devicemonitor_update.conf` are added |
| An old `config.json` gains the new keys instead of losing its values | the model merges `defaults.json` under the saved file: 35 saved keys become 39, `ha_carp_enabled` / `ha_role_override` default in, operator values are kept |

There is no 2.12 **release** to install: the 2.12 line was recovered as
`v2.12-baseline`, which is a source baseline and not an installable payload. A firewall
that reports `2.12` (as the CARP pair did) upgrades to the current bundle in one step.

On a CARP pair, upgrade the master first, verify, then the standby, so the virtual IP
keeps being served. Keep the pre-upgrade data backup and the installer's
`install-v213.<id>/` rollback directory until you have seen a clean scan cycle.

> **Removed files are pruned, but only with proof.** Each install records the full target
> set it owns — manifest files and the catalogues it generates, with a digest each — in
> `/var/db/devicemonitor/installed-manifest.txt`. The next install removes a path only when
> that record still matches the file, or when a published historical manifest
> (`release/legacy-targets.txt`, v2.9 … v2.13.2) shipped that exact digest, and only inside
> the plugin's own namespaces. Anything else — an edited file, a third-party file, a path
> outside those namespaces — is retained and reported. `--check` reports how many would go
> (`prunable=<n>`, split as `legacy_prunable=`) and how many were refused (`retained=<n>`);
> `INSTALL_OK` reports how many did (`pruned=<n>`).

Back up the runtime data first — it is not part of the bundle:

```sh
tar -czf /root/devicemonitor-backup.tgz /var/db/devicemonitor
```

Then install as above. Configuration (`/var/db/devicemonitor/config.json`) and the
device database are preserved; new settings keys appear automatically because the
model merges `defaults.json` under the saved configuration.

To roll back, either re-run the previous bundle, or restore in place:

```sh
service devicemonitor stop
BASE=/var/backups/devicemonitor/install-v213.<id>
while read -r id old new mode src dest; do
    [ "$old" = absent ] || cp -p "$BASE/files/$id" "$dest"
done < "$BASE/plan"
service devicemonitor start
```

A CARP pair is upgraded one node at a time — master first, then standby — so the
VIP keeps being served while the other node restarts its daemon.

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
| Enable Device Monitor | Enable/disable scanning (daemon stays disabled until you enable it) |
| Monitored Interfaces | Interfaces whose devices are scanned; empty selection fails closed |
| Scan Interval | How often to scan (5–30 minutes) |

### Hostname enrichment

Device Monitor fills each device **Hostname** from an ordered precedence of sources:
**AdGuard > Dnsmasq > Kea > ISC > Unbound > Pi-hole > Hostwatch**.

- **Hostwatch**, **ISC**, **Kea** and **Dnsmasq** are native sources used automatically.
- **Unbound** *(Experimental)* — reads local OPNsense Unbound host overrides and host
  aliases from `/conf/config.xml` only. Disabled by default; enable it in Settings.
- **Pi-hole** *(Experimental)* — reads Pi-hole v6 DHCP leases over HTTPS (requires Pi-hole
  v6 and an app password). Disabled by default.

Pi-hole and Unbound enrichment are experimental and disabled by default. No provider is
enabled automatically during install or upgrade.

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

The v2.10 installer upgrades files in place and does not invoke the uninstaller.

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

## Licence

BSD 2-Clause License — see [LICENSE](LICENSE)
