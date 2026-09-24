# Device Monitor — User Manual

This manual describes every user-facing function in the Device Monitor plugin for OPNsense.
It is written for an OPNsense administrator and describes only functionality that is
actually implemented in the current release (`v2.9-development`). Internal details are
included only where they help explain observable behaviour.

> **Conventions.** Actions that only *view* data are marked **Read-only**. Actions that
> *change* stored data, run a network scan, or control a service are marked **Changes
> state** (and noted as consequential where appropriate).

---

## 1. Introduction

Device Monitor is an OPNsense plugin that automatically discovers and tracks the devices
on your LAN. It combines observations from the OPNsense Hostwatch service with several
optional hostname sources, and provides pages for reviewing devices, their history,
detected identity conflicts, discovered network services, security-scan results, and a
chronological change summary.

Device Monitor does **not** block, disconnect, or remediate devices on its own. It is an
observational and administrative tool: it records what it sees and helps you organise and
review that information. Where it can change state (for example, deleting a device or
running an Nmap scan), it always does so as an explicit, user-initiated action.

---

## 2. Getting started

### 2.1 Where to find Device Monitor

After the plugin is installed, open **Services → Device Monitor**. The submenu contains:

- **Devices**
- **Change Summary**
- **Infrastructure Services**
- **IP and MAC Conflicts**
- **Nmap Scan History**
- **Settings**

### 2.2 Enabling Device Monitor

1. Go to **Services → Device Monitor → Settings**.
2. On the **Monitoring** tab, tick **Enable Device Monitor**.
3. Select one or more **Monitored Interfaces**. With no interface selected, discovery is
   refused (fail-closed) — nothing is scanned.
4. Optionally adjust the **Scan interval** (how often discovery runs, in seconds; allowed
   range 60–3600).
5. Save the settings.

When enabled, the background daemon runs discovery on a schedule and populates the Devices
list. You can also trigger discovery manually from the Devices page (see [Section 4](#4-devices)).

### 2.3 What you will see first

- The **Devices** page lists every discovered device with its IP address, detected hostname,
  Friendly Name, vendor, VLAN, status, and more.
- The **Settings** page controls monitoring, notifications and security scanning.

> **Prerequisite.** Device Monitor reads device observations from the OPNsense Hostwatch
> service. Each selected Monitored Interface must be observed by Hostwatch. For a VLAN
> interface, select that VLAN in **Interfaces → Neighbors → Automatic Discovery** and
> restart Hostwatch, otherwise few or no devices on that VLAN will appear.
> See [Section 17](#17-troubleshooting).

---

## 3. Device Monitor navigation

| Menu item | Purpose |
|-----------|---------|
| **Devices** | Device inventory with two tabs: **Network Identities** and **Device Profiles**. |
| **Change Summary** | Chronological review of device, lifecycle, identity and service changes. |
| **Infrastructure Services** | Network services discovered on your devices (DHCP, DNS, SSH, …). |
| **IP and MAC Conflicts** | Detected identity anomalies (an IP/MAC seen with conflicting devices). |
| **Nmap Scan History** | History of targeted Nmap security scans and their results. |
| **Settings** | Monitoring, notification and Nmap scanning configuration. |

The **Devices** menu item opens two tab-style views:

- **Network Identities** — automatically discovered network identities; each row is one MAC address.
- **Device Profiles** — real-world devices linked to one or more network identities (for example wired and Wi-Fi adapters).

Two additional pages are reached from the Devices list rather than the menu:

- **Device Details** — a single device's summary, notes, lifecycle history and device-profile
  association. Open it with the note/comment icon (or **History**) in a device's **Actions** column.
- **Device Activity** — the chronological activity log for a single device. Open it
  with the **Device Activity** button on the Device Details page.

Device Monitor also provides a small dashboard widget (OPNsense Lobby) showing the daemon
status (**Running**/**Stopped** with its PID), total devices, and how many are **Online**.

---

## 4. Devices

**Path:** Services → Device Monitor → Devices → **Network Identities**

This is the primary view of everything Device Monitor has discovered. Each row is one
automatically discovered network identity (a MAC address).

### 4.1 Purpose

List all known devices and allow you to review and act on them: edit a Friendly Name, check
whether a device is online, run a targeted Nmap scan, open its history, or remove it.

### 4.2 Page header

- **Total Devices** — the number of devices currently shown, matching the active
  VLAN/status filter.
- **Online** — how many of those (filtered) devices are currently online.

The page title is provided by the OPNsense breadcrumb (**Services → Device Monitor →
Devices**). The installed plugin version is shown under **Settings → About**.

### 4.3 Toolbar controls

- **All VLANs (drop-down)** — a multi-select VLAN filter. Tick one or more VLANs, then
  press **Apply VLAN Filter** to show only devices on those VLANs. Tick **All VLANs**
  and press **Apply VLAN Filter** to return to the unfiltered all-VLAN view. Clearing
  every tick leaves an incomplete selection: the drop-down shows **Select a VLAN**,
  **Apply VLAN Filter** is disabled, and the table keeps its last applied filter until
  you tick a VLAN or **All VLANs**. Checkbox changes are not applied to the table until
  you press the button, which stays muted/disabled until your selection differs from what
  is applied. **Read-only.**
- **All statuses (drop-down)** — filter by **All statuses**, **Online** or **Offline**.
  **Read-only.**
- **Refresh** — reload the list and statistics immediately. **Read-only.**
- **Run scan now** (magnifier icon) — trigger a Device Monitor discovery/scan immediately.
  **Changes state** (runs the background scan).
- **Export to CSV** (download icon) — download the current filtered list as a CSV file
  (with a UTF-8 BOM so it opens cleanly in Excel). The filename includes the date and the
  active VLAN filter. **Read-only.**
- **Clear Database** (red button) — deletes the entire Device Monitor device database.
  This is **consequential and destructive**: it removes all devices and related history. A
  confirmation prompt is shown first. **Changes state.**

### 4.4 Table columns

- **MAC Address** — the device's MAC address (its primary identity).
- **IP Address** — the current IPv4 address.
- **Friendly Name** — a name *you* assign. Editable inline (pencil icon). See 4.6.
- **Hostname** — the hostname Device Monitor detected, together with its source (for
  example `kea`, `unbound`, `adguard`, `pihole`, or `hostwatch`). See [Section 13](#13-hostname-enrichment-and-hostname-sources).
- **Vendor** — the NIC vendor derived from the MAC address (OUI lookup).
- **Services** — badges/summary of infrastructure services discovered on the device. See
  [Section 9](#9-infrastructure-services).
- **VLAN** — the VLAN/interface the device was observed on.
- **Status** — **ONLINE** (green), **OFFLINE** (grey), or **RETURNING** (orange). See
  [Section 5](#5-device-lifecycle-and-returning-devices).
- **Device Profile** — the device profile this identity is linked to (if any), with its
  identity count. See [Section 7](#7-device-profiles).
- **Scan Status** — status of the device's most recent targeted Nmap scan: e.g. **Pending**,
  a completed status, or **Failed n/5** (attempt count out of 5). See [Section 12](#12-networknmapsecurity-scanning).
- **First Seen** — when the device was first observed.
- **Last Seen** — when the device was last observed.
- **Actions** — per-row buttons (below).

### 4.5 Per-row actions

- **Details/Notes** (comment icon) — opens the Device Details page. For a **RETURNING**
  device this becomes a **History** button (history icon) to resolve the returning device.
  **Read-only** (opens a page).
- **Check online** (plug icon) — pings the device and reports success/failure as a toast
  message. **Read-only** (does not change stored data).
- **Run targeted Nmap scan** (search icon) — starts a targeted Nmap scan against this one
  device. **Changes state.** See [Section 12](#12-networknmapsecurity-scanning).
- **Delete** (trash icon) — removes this device. A confirmation is shown first. This is
  **consequential**; its lifecycle history is preserved as an archive (see Section 5).
  **Changes state.**

### 4.6 Editing a Friendly Name

Click the pencil icon next to **Friendly Name**, enter a name and save, or clear it. The
Friendly Name is your own label (`custom_hostname`); it is independent of the detected
Hostname, and editing it never overwrites the detected hostname. The change is recorded in
the device's Device Activity.

### 4.7 Important notes

- The list and statistics auto-refresh every 30 seconds.
- The page title, navigation tabs, explanatory text, summary counters, filter
  toolbar and table column headings remain "sticky" while scrolling a long
  list.
- At narrower window/content widths, lower-priority columns (Services, Device
  Profile, Scan Status, First Seen, Last Seen) are hidden progressively - only
  as many as needed - so the essential identity, status and action columns
  remain usable without horizontal scrolling; that information remains
  available on the Device Details page.
- **Clear Database** and per-row **Delete** are the only destructive actions on this page.

---

## 5. Device lifecycle and returning devices

Device Monitor organises a device's identity into **lifecycles**. A lifecycle is a period
of continuous ownership/use for a given MAC address.

### 5.1 Normal lifecycle

- When a new MAC is first observed, Device Monitor creates an **active** lifecycle.
- While the device keeps being seen, that lifecycle remains active and its snapshot
  (Friendly Name, hostname, IP, VLAN, first/last seen) is kept up to date.

### 5.2 Returning devices

If a device is deleted (or archived) and the same MAC address reappears later, Device
Monitor does **not** silently re-create it. Instead the device is shown as **RETURNING**
(orange badge) on the Devices page.

For a returning device you must make an explicit choice in its **Device Details →
Lifecycle History**:

- **Start New Lifecycle** — treat the returning device as a new identity/ownership period.
  A fresh active lifecycle is created.
- **Relink** (per archived lifecycle row) — link the returning device back to one of its
  previous archived lifecycles, preserving the original history and `First Seen` date.

This is deliberate: it preserves the distinction between a continuing device identity and
a genuinely new period of ownership, and prevents scanner observations from silently
rewriting device history.

### 5.3 Lifecycle statuses

- **Active** — the current, live lifecycle for a device.
- **Archived** — a previous lifecycle, preserved for history when the device was removed.
- **RETURNING** (device status) — a known MAC has reappeared after removal and awaits your
  lifecycle decision.

### 5.4 What is preserved

- Removing a device archives (rather than deletes) its lifecycle records.
- The original lifecycle `First Seen` value is preserved.
- The earliest-known MAC history is preserved independently of lifecycle changes.
- Lifecycle notes are retained as timestamped, versioned records (see Section 6).

> **Note.** ONLINE/OFFLINE state is separate from lifecycle active/archived state: an
> archived lifecycle does **not** imply the device is currently offline, and vice versa.

---

## 6. Device history and comments (notes)

**Path:** Devices → a device's **Actions → comment icon** (or **History** for returning
devices) → **Device Details**

### 6.1 Purpose

Give a concise operational summary of one device's current identity and lifecycle, with
clear navigation to its full activity history and to grouping management.

### 6.2 Device Summary panel

Shows the device's current identity in two columns. **IP Address** is the first field,
followed by **Friendly Name**, **Hostname** (with its source, when known), **MAC Address**,
and **Vendor**. The second column shows **Status**, **VLAN**, **First Seen**, **Last Seen**,
and **Current Lifecycle**. **Read-only.**

### 6.3 Lifecycle History panel

Lists the device's lifecycles as a table. A short explanation at the top describes what a
lifecycle is: one continuous period during which a MAC address is treated as the same known
device; earlier lifecycles are archived (not deleted) and remain available below.

Columns: **Lifecycle**, **Status**, **IP Address**, **Friendly Name**, **Hostname**,
**Vendor**, **VLAN**, **First Seen**, **Last Seen**, **Notes**, and **Actions**.

- For a **RETURNING** device, this panel shows the resolution controls: **Start New
  Lifecycle** and per-row **Relink**.
- Each lifecycle row lets you view its notes.

### 6.4 Notes panel

- **Add Note** — add a free-text note to the device's *active* lifecycle. **Changes state.**
- Each note is numbered, shows its text and timestamp, and supports:
  - **Edit** — change the note text (creates a new version). **Changes state.**
  - **Archive** — archive the note (soft-delete; it is retained, not erased). **Changes state.**
- Note history is preserved: edits create versions and the note's creation/edit history is
  shown. Archived notes are retained but no longer shown as current.

> **Prerequisite.** Notes belong to an active lifecycle. If a device is **RETURNING** and
> has no active lifecycle, you must first resolve it in Lifecycle History (Start New
> Lifecycle or Relink) before adding notes.

### 6.5 Device Activity link

The **Device Activity** button on Device Details opens the **Device Activity** page
for the device (see below).

### 6.6 Device Activity page

**Path:** Device Details → **Device Activity**

Shows the device's activity history in a table with columns: **Date / time**, **Activity**
(colour-coded label), **Details**, and **Lifecycle** (the lifecycle number).

Activity labels include (among others): **Lifecycle started**, **Lifecycle archived**,
**Lifecycle relinked**, **Friendly name changed**, **Note created**, **Note edited**,
and identity changes (IP/hostname/source changes). **Read-only.**

---

## 7. Device Profiles

**Path:** Services → Device Monitor → Devices → **Device Profiles**

### 7.1 Purpose

A **device profile** is one real-world piece of equipment that you recognise and name
(for example "Reception PC" or "Lab printer"). Because one machine can appear on the
network under several MAC addresses (wired + Wi-Fi, for instance), you can associate
several network identities with the same device profile.

- **Current Identities** are the MAC/network identities currently associated with the
  device.
- **Previous Identities** are identities that were associated in the past and are kept
  as history.

Associating identities is **explicit and user-confirmed**: it never merges or rewrites
device, lifecycle or identity history.

### 7.2 What you can do

On the **Device Profiles** page:

- **Create Profile** — enter a name and a starting MAC address; the new profile is created
  with that MAC as its first current identity. The starting MAC must be a currently online
  network identity. **Changes state.**
- Expand a profile to see its identities, then use **Add Identity** to add another MAC, or
  **Unlink Identity** to remove a current identity. **Changes state.**
- Filter the list with **All Profiles / Current Profiles / Archived Profiles** and search by
  name or MAC. **Read-only.**
- **View Device Details** for any identity to open its **Device Details** page. **Read-only.**

On a device's **Device Details** page, a read-only **Device Profile** summary shows the
profile's name and current identity count and links to the **Device Profiles** page.

### 7.3 What is displayed

The page lists every device profile (current and archived) with its current identity
count, online/offline status and last-seen time. Each profile expands to show its
**Profile Summary**, **Current Identities** and **Previous Identities**. Archived profiles
are read-only; removed identities are retained as history. The Devices page **Device
Profile** column shows the profile name plus the identity count.

> Device profiles are purely organisational. They do not change how devices are scanned,
> monitored or notified, and they do not alter device or lifecycle history.

---

## 8. Identity Events (IP and MAC Conflicts)

**Path:** Services → Device Monitor → IP and MAC Conflicts

### 8.1 Purpose

Show detected identity anomalies — situations where an IP address or MAC address was seen
associated with conflicting devices. These are **observations**, not automatic actions:
Device Monitor never blocks or remediates a device.

### 8.2 Controls

- **Status filter** — **All**, **Unresolved** or **Resolved**.
- **Rows** — how many events to show per view (10 / 25 / 50 / 100).
- **Refresh** — reload the list.
- **Unresolved** / **Resolved** summary links (with counts) — jump to that filtered view.

### 8.3 Table columns

- **Severity** — a colour-coded severity label.
- **Resolution** — **Unresolved** / **Resolved**.
- **Event type** — the anomaly type (for example an IP or MAC identity change/conflict).
- **MAC** — the primary MAC involved.
- **IP** — the primary IP involved.
- **Other MAC** / **Other IP** — the conflicting counterpart.
- **Interface** — the interface where the event was observed.
- **Details / Actions** — a details expand button and a resolve/reopen button.

The controls heading and table column headers stay pinned while the list scrolls (normal
page scrolling).

### 8.4 Actions

- **Details** — expand the row to reveal the full recorded details.
- **Resolve** — mark an unresolved event as resolved. **Changes state.**
- **Reopen** — return a resolved event to unresolved. **Changes state.**

Marking an event resolved/reopened is purely administrative book-keeping; it does not
change device records or network state.

---

## 9. Infrastructure Services

**Path:** Services → Device Monitor → Infrastructure Services

### Port Discovery

The **Port Discovery** tab lists monitored devices in a searchable table.
Use **Run Now** on a device row to scan that device's TCP ports (1–65535).
Use the weekly checkboxes and **Save weekly selections** to schedule several
devices in one pass. Filters show all devices, those selected for weekly scans,
or those never scanned. Weekly scans run while Device Monitor monitoring is
enabled. At most one due device is
processed after each normal monitoring cycle; scans for different devices
never run concurrently through this feature. Each scan has a 120-second
process limit and records identified open ports and errors separately from
the existing Nmap Scan History. A timed-out or incomplete scan is reported
as a failure, rather than a complete list of ports.
The **Last Scan** and **Scan Time** columns display the browser's local time
and timezone label. Devices without a hostname show their IP once, alongside
their MAC address.

Port names are Nmap identification evidence, not proof of the application
protocol. UDP ports are outside this TCP scan; in particular, WireGuard
requires authoritative configuration or host runtime evidence.

### 9.1 Purpose

Show the network services discovered on your devices, organised into tabs by service
category, plus a feed of recent service changes.

### 9.2 Header statistics

**Total**, **Available**, **Unavailable**, and **Stale** counts for the currently shown
services.

### 9.3 Toolbar controls

- **Refresh View** — reload the service data. **Read-only.**
- **Discover Now** — trigger an immediate infrastructure-service discovery pass.
  **Changes state** (runs discovery).
- **All Services** (type filter) — filter by service type.
- **All Statuses** (status filter) — filter by **Available** / **Unavailable** / **Stale**.
- **Search services** — free-text filter.
- **Show archived** — include services hidden with **Archive**.
- **Showing n** — number of services currently displayed.

Each service row has **Archive** (or **Restore** when archived). Archive hides
the endpoint from the normal tabs without deleting its discovery or activity
history. A later successful verification returns an archived endpoint to the
normal list. Restore returns it immediately.

### 9.4 Tabs and table columns

Services are organised into tabs, one per service category:

- **Recent Service Changes** — the latest service events feed (see 9.5).
- **DHCP Servers**, **DNS Servers**, **NTP Servers**, **SSH Servers**,
  **Web / Admin Services**, **File / NAS Services** (SMB/NFS), **Remote Access**
  (RDP/VNC/WinRM), **Directory / Authentication** (LDAP/LDAPS/Kerberos),
  **SNMP / Management**, and **VPN Endpoints**.

Only the categories that actually contain services are shown as tabs, in the order
above. Click a tab to view that category; switching tabs is instant and does not
reload data. Each tab shows a badge with its current service count.

The page heading, common controls and the tab strip remain visible while you scroll,
and the active table's column headings stay pinned beneath them.

Each service row shows:

- **IP Address** — the device IP.
- **Hostname** — the device hostname.
- **Status** — **Available** / **Unavailable** / **Stale**.
- **Port / Protocol** — e.g. `22/TCP`.
- **Interface / VLAN** — where the service was detected.
- **Detection** — how the service was detected (probe / Nmap / authoritative config).
- **Confidence** — detection confidence.
- **Product / Version** — service product/version when known.
- **Last Verified** — when the service was last verified.

> **"Stale"** means the service has not been re-verified recently (rather than being
> confirmed down). "Unavailable" means it was confirmed unreachable.

### 9.5 Recent Service Changes tab

The first tab shows a feed of the latest service events with columns: **Date / Time**,
**Change** (discovered / unavailable / recovered / changed), **Service**, **Device**,
**Endpoint**, **Evidence**, and **History**. **Read-only.**

---

## 10. Scan History (Nmap)

**Path:** Services → Device Monitor → Nmap Scan History

### 10.1 Purpose

Show the history of targeted Nmap security scans that Device Monitor has run, together with
their results.

### 10.2 Controls

- **Rows** — number of history rows to show (10 / 25 / 50 / 100).
- **Refresh** — reload the list.

### 10.3 Table columns

- **Started** — when the scan started.
- **MAC Address** — the target device.
- **IP Address** — the target IP.
- **Type** — the scan type (e.g. targeted / top-ports).
- **Scan** — scan status.
- **Open Ports** — a summary of open ports found.
- **Email** — whether a scan-result email was sent for this scan.
- **Details** — expand to see the full result.

The controls heading and table column headers stay pinned while the list scrolls (normal
page scrolling).

### 10.4 Notes

- Scans are **targeted** at one literal IPv4 address per device; Device Monitor never
  performs broad subnet sweeps for security scanning.
- See [Section 12](#12-networknmapsecurity-scanning) for how scanning is configured.

---

## 11. Change Summary

**Path:** Services → Device Monitor → Change Summary

### 11.1 Purpose

Provide a chronological, filterable review of recent changes across devices, lifecycles,
identities, device profiles, notes/history, and infrastructure services.

### 11.2 Controls

- **Period** — **Since last review**, **Last 24 hours**, **Last 7 days**, **Last 30 days**,
  or **Custom range** (start/end, UTC).
- **Category** — **All categories**, **Device**, **Lifecycle**, **Identity**,
  **Device Profile**, **Notes / History**, or **Infrastructure**.
- **Refresh** — reload.
- **Mark reviewed now** — sets the "last reviewed" marker to now (stored in your browser).
  This anchors the **Since last review** period. **Read-only effect on data** (local only).

### 11.3 Summary counters

**Total Changes**, **New Devices**, **Returned Devices**, **Identity Changes**,
**Infrastructure Changes**, **Lifecycle Changes**.

### 11.4 Table columns

- **#** — row number.
- **Time** — when the change occurred.
- **Category** — the change category.
- **Device / Subject** — the affected device or subject.
- **Change** — what changed.
- **Previous** / **Current** — before and after values.
- **Action** — the action that caused the change (where applicable).

The table is paginated with **Previous** / **Next**.

> **"Since last review"** uses a browser-local marker (`localStorage`), so it is per-browser
> and per-machine, not a shared server setting. "Mark reviewed now" only affects that
> browser's marker.

---

## 12. Network / Nmap / security scanning

### 12.1 What scanning does

Device Monitor can run **targeted Nmap scans** against individual devices to discover open
ports and detect services. Scanning is separate from ordinary device discovery.

### 12.2 Important safety rules

- Every security scan targets **one literal IPv4 address** belonging to the device.
- Device Monitor **never** scans a subnet, an address range, a VLAN, or all hosts at once.
- Failed scans remain queued for retry, with rate limiting preserved.

### 12.3 Triggering scans

- **Devices page → a device's "Run targeted Nmap scan" button** — scan that one device.
  **Changes state.**
- The background daemon can also process queued scan work automatically (subject to the
  **Nmap scans per cycle** limit).

### 12.4 Configuring scans

See the **Nmap Scanning** tab under [Section 14](#14-settings). Key options:

- **Enable targeted Nmap scanning** — master switch.
- **Top ports** — number of top ports to scan (1–1000; default 100).
- **Timing template** — Nmap timing T0–T5 (default 4).
- **Host timeout** — per-host timeout in seconds (10–300; default 45).
- **Version detection** — enable service/version detection.
- **Nmap scans per cycle** — max scans per daemon cycle (1–10; default 2).

### 12.5 Where results appear

- **Nmap Scan History** page — the scan log (see [Section 10](#10-scan-history-nmap)).
- **Devices page → Scan Status** column — per-device scan status (Pending / completed /
  Failed n/5).

> **Warning.** Targeted Nmap scanning is a consequential action: it sends packets to a
> device and consumes firewall resources. Keep the per-cycle limit and host timeout bounded,
> and only scan devices you are authorised to test.

---

## 13. Hostname enrichment and hostname sources

### 13.1 Overview

Device Monitor obtains each device's **Hostname** from one of several sources. These are
combined through a single ordered precedence, and the winning source is shown next to the
hostname on the Devices page (e.g. `hostname (kea)`).

Precedence (strongest first):

1. **AdGuard** DNS rewrites (`adguard`)
2. **Dnsmasq** DHCP leases (`dnsmasq`)
3. **Kea** DHCP leases (`kea`)
4. **ISC** DHCP leases (`isc`)
5. **Unbound** host overrides/aliases (`unbound`)
6. **Pi-hole** DHCP leases (`pihole`)
7. **Hostwatch** (observational base) (`hostwatch`)

### 13.2 The sources

- **Hostwatch** — the observational base. This is the hostname OPNsense itself observes.
- **ISC / Kea / Dnsmasq** — native OPNsense DHCP lease sources (when those services provide
  leases with hostnames).
- **Unbound** *(Experimental)* — reads local OPNsense Unbound host overrides (A records)
  and host aliases from `/conf/config.xml`. It reads local configuration only, performs no
  network queries, is disabled by default and must be enabled in Settings.
- **AdGuard** — optional external DNS-rewrite source. Configured in Settings.
- **Pi-hole** *(Experimental)* — optional external DHCP-lease source (Pi-hole v6 REST
  API). Configured in Settings and disabled by default.

### 13.3 Behaviour and guarantees

- The **Friendly Name** (your own label) is completely independent of the Hostname and is
  never overwritten by enrichment.
- If a source returns no result or fails, the next source is used; a failed source never
  breaks discovery.
- An empty result **never erases** an already-resolved hostname.
- Hostnames are normalised (surrounding whitespace and a trailing dot are removed).

### 13.4 Configuration

Configure AdGuard, Pi-hole and Unbound on the **Settings → Monitoring** tab (see
Section 14). ISC, Kea, Dnsmasq and Hostwatch require no Device Monitor configuration; they
are used when the underlying data is present on OPNsense. Pi-hole and Unbound are
experimental and disabled by default.

---

## 14. Settings

**Path:** Services → Device Monitor → Settings

Settings are organised into five tabs: **Monitoring**, **Nmap Scanning**,
**Email Notifications**, **Webhook Notifications**, and **About**. Use the **Apply/save**
button on each tab to persist changes. Saving is validated server-side; invalid values are
rejected with an error message.

### 14.1 Monitoring tab

- **Enable Device Monitor** — master switch for the background monitoring daemon
  (default: off). The daemon stays disabled until you deliberately enable it.
  **Changes state.**
- **Monitored Interfaces** — select the interfaces whose devices are scanned. Empty
  selection fails closed: discovery is refused and nothing is scanned. Selected
  subnets must not overlap.
- **Scan interval** — seconds between discovery runs. Allowed 60–3600 (default 300).
- **Email VLANs** — restrict email notifications to selected VLANs/interfaces. Empty means
  all.
- **Webhook VLANs** — restrict webhook notifications to selected VLANs/interfaces. Empty
  means all.
- **Identity email** — enable email notifications for identity-conflict events.
- **Service email** — enable email notifications for infrastructure-service changes, with
  three sub-options:
  - **New** — notify when a service is first discovered.
  - **Unavailable** — notify when a service becomes unavailable.
  - **Recovered** — notify when a service becomes available again.

#### AdGuard DNS rewrites

- **Enable AdGuard rewrites** — enable hostname enrichment from AdGuard Home DNS rewrites.
- **AdGuard URL** — the AdGuard Home base URL (HTTPS).
- **AdGuard username / password** — credentials for the AdGuard API.

#### Pi-hole (Experimental)

- **Enable Pi-hole** — enable hostname enrichment from Pi-hole v6 DHCP leases (disabled by
  default).
- **Pi-hole URL** — the Pi-hole base URL (HTTPS).
- **Pi-hole password** — the Pi-hole v6 app password (used for session auth).

Pi-hole requires Pi-hole v6, HTTPS and an app password.

#### Unbound (Experimental)

- **Enable Unbound hostname enrichment** — enable hostname enrichment from local Unbound
  host overrides and host aliases (disabled by default). This reads `/conf/config.xml`
  only and performs no network queries.

> AdGuard is an optional external source. Pi-hole and Unbound are experimental and disabled
> by default. AdGuard and Pi-hole use HTTPS with certificate verification enabled, and
> credentials are never written to logs or error messages.

### 14.2 Email Notifications tab

- **Enable Email** — master switch for email notifications (default: off).
- **Email Recipient** — where notifications are sent.
- **Email Sender** — the From address (default `devicemonitor@opnsense.local`).
- **Email delivery method** — **sendmail** (local MTA) or **SMTP**.
- When **SMTP** is selected:
  - **SMTP host** — the relay hostname/IP.
  - **SMTP port** — 1–65535 (default 587).
  - **Encryption** — none / STARTTLS / SSL.
  - **Username / Password** — SMTP authentication (optional).
- **Test Email** — save the current form, then send a test message to the configured
  recipient. The result (success/failure, and transport) is shown. **Changes state** (sends
  a real email).

### 14.3 Webhook Notifications tab

- **Enable Webhook** — master switch for webhook notifications (default: off).
- **Webhook URL** — the HTTP(S) endpoint that receives JSON notifications.
- **Test webhook** — send a test payload to the configured URL and show the result.
  **Changes state** (sends a real request).

### 14.4 Nmap Scanning tab

- **Enable targeted Nmap scanning** — master switch for the targeted Nmap scan feature
  (default: on).
- **Top ports** — number of top ports scanned per device. Allowed 1–1000 (default 100).
- **Timing template** — Nmap timing T0–T5 (0–5; default 4 = T4).
- **Host timeout** — per-host timeout in seconds. Allowed 10–300 (default 45).
- **Version detection** — enable service/version detection during scans (default: on).
- **Nmap scans per cycle** — maximum scans the daemon runs per cycle. Allowed 1–10
  (default 2).

### 14.5 About tab

Displays the installed Device Monitor version and descriptive information. **Read-only.**

---

## 15. Status indicators, badges and terminology

- **ONLINE** (green circle) — the device was recently observed online.
- **OFFLINE** (grey circle) — the device is not currently online.
- **RETURNING** (orange) — a known MAC reappeared after removal and needs a lifecycle
  decision.
- **Active / Archived** (lifecycle) — the current vs. historical lifecycle for a device.
- **Unresolved / Resolved** (identity event) — whether an identity anomaly has been
  acknowledged (resolved) by an administrator.
- **Available / Unavailable / Stale** (service) — confirmed reachable / confirmed
  unreachable / not re-verified recently.
- **Pending / Failed n/5** (scan status) — a scan is queued or has failed after *n* of 5
  attempts.
- **Running (PID: n) / Stopped** (widget) — the Device Monitor daemon state.

---

## 16. Common workflows

### 16.1 Enable monitoring and see devices

1. Settings → Monitoring → tick **Enable Device Monitor** → save.
2. Open **Devices** and click **Run scan now**, or wait for the next interval.
3. Review the device list.

### 16.2 Give a device a memorable name

1. On **Devices**, find the device.
2. Click the pencil icon in **Friendly Name**, type a name, save.

### 16.3 Handle a returning device

1. On **Devices**, find the **RETURNING** device.
2. Click **History**.
3. In **Lifecycle History**, choose **Start New Lifecycle** (new identity) or **Relink**
   (restore a previous lifecycle).

### 16.4 Associate several MAC addresses with one device profile

1. Open **Services → Device Monitor → Devices → Device Profiles**.
2. Click **Create Profile**, enter a name and one of the machine's MAC addresses, then confirm.
3. Expand the new profile and use **Add Identity** to add the machine's other MACs.

### 16.5 Review what changed recently

1. Open **Change Summary**.
2. Choose a **Period** (e.g. **Since last review** or **Last 7 days**) and optionally a
   **Category**.
3. Review the changes; click **Mark reviewed now** when done.

### 16.6 Investigate an IP/MAC conflict

1. Open **IP and MAC Conflicts**.
2. Filter by **Unresolved**.
3. Expand a row's **Details** to see the full evidence.
4. Click **Resolve** after investigating (or **Reopen** to undo).

### 16.7 Scan a single device for open ports

1. On **Devices**, click the **Run targeted Nmap scan** (search icon) for the device.
2. Watch the **Scan Status** column, then review results in **Nmap Scan History**.

### 16.8 Test notification delivery

1. Settings → **Email Notifications** → configure recipient/transport → **Test Email**.
2. Settings → **Webhook Notifications** → configure URL → **Test webhook**.

---

## 17. Troubleshooting

- **No devices appear.**
  Confirm Device Monitor is enabled, at least one **Monitored Interface** is selected, the
  interface has a usable IPv4 address/prefix, and Hostwatch is observing that interface. For
  a VLAN interface, select it in **Interfaces → Neighbors → Automatic Discovery** and restart
  Hostwatch. Then click **Run scan now**.
- **A device shows "RETURNING".**
  This is expected when a previously removed MAC reappears. Resolve it in Device Details →
  Lifecycle History.
- **A service shows "Stale".**
  The service has not been re-verified recently. Run **Discover Now** on Infrastructure
  Services and re-check.
- **Email/webhook test fails.**
  Check the recipient, the SMTP relay/credentials/port/encryption (for email), or the webhook
  URL and reachability (for webhooks). The test reports a failure reason where available.
- **A scan is "Failed n/5".**
  The target may be offline, firewalled, or timing out. Adjust the host timeout, or re-run
  the scan later.
- **Saving settings is rejected.**
  Values are validated. Check that scan interval (60–3600), SMTP port (1–65535), top ports
  (1–1000), timing (0–5), host timeout (10–300) and scans-per-cycle (1–10) are within range.

---

## 18. Safety and operational limitations

- Device Monitor is **observational**; it does not block, disconnect, delete, or remediate
  devices on its own, and it never changes firewall rules.
- Security scanning is **single-host only**: one literal IPv4 address per scan. Broad
  subnet/range/VLAN sweeps are never performed.
- **Clear Database** and per-device **Delete** are destructive; they are always confirmed.
  Deleting a device archives (does not erase) its lifecycle history.
- External hostname sources (AdGuard, Pi-hole) are optional and use HTTPS with certificate
  verification enabled. Credentials are never logged. Pi-hole and Unbound hostname
  enrichment are experimental and disabled by default.
- Resource use is bounded: the daemon rate-limits discovery and scan work. Keep the
  scan-interval and scans-per-cycle values conservative on a busy firewall.
- The Change Summary "Since last review" marker is browser-local, not a shared server
  setting.
- Automatic monitoring is scoped to the selected Monitored Interfaces; an empty selection is
  refused (fail-closed), so no subnet is observed unless you explicitly select it.

---

## 19. Glossary

- **Network Identity** — a discovered network device, keyed by MAC address (shown on the
  Network Identities tab).
- **Hostwatch** — the OPNsense service that observes hosts on firewall interfaces.
- **Lifecycle** — a period of continuous ownership/use for a MAC address.
- **Returning device** — a known MAC that reappeared after removal and awaits a decision.
- **Friendly Name** — your own label for a device (`custom_hostname`), independent of the
  detected hostname.
- **Hostname** — the hostname Device Monitor detected (with a source tag).
- **Device Profile** — one real-world piece of equipment, recognised by you, with one or
  more current or previous network identities.
- **Identity event** — a detected IP/MAC anomaly or conflict.
- **Infrastructure service** — a network service (DHCP, DNS, SSH, SMB, …) found on a device.
- **Targeted Nmap scan** — a single-host port/security scan.
- **Daemon** — the background Device Monitor process that performs scheduled discovery and
  scan work.

---

## Appendix A — Coverage map (page/control/function → source file)

| User-visible surface | Source file(s) |
|----------------------|----------------|
| Navigation menu | `src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/Menu/Menu.xml` |
| ACL / permissions | `src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/ACL/ACL.xml` |
| Devices page (list, filters, CSV, actions) | `views/.../devices.volt`, `Api/DevicesController.php`, `models/.../DeviceMonitor.php` |
| Device Profiles | `views/.../physicaldevices.volt`, `Api/DevicesController.php`, `models/.../DeviceMonitor.php` |
| Device Details (summary, notes, lifecycle, device profile) | `views/.../devicehistory.volt`, `Api/DevicesController.php`, `models/.../DeviceMonitor.php` |
| Device Activity | `views/.../activitytimeline.volt`, `Api/DevicesController.php`, `models/.../DeviceMonitor.php` |
| IP and MAC Conflicts | `views/.../identityevents.volt`, `Api/DevicesController.php`, `models/.../DeviceMonitor.php` |
| Infrastructure Services | `views/.../infrastructureservices.volt`, `Api/DevicesController.php`, `scan_network.py` |
| Nmap Scan History | `views/.../scanhistory.volt`, `Api/DevicesController.php` |
| Change Summary | `views/.../changesummary.volt`, `Api/DevicesController.php`, `models/.../DeviceMonitor.php` |
| Settings (all tabs) | `views/.../settings.volt`, `Api/ConfigController.php`, `defaults.json` |
| Dashboard widget | `views/.../service_widget.volt`, `Api/ServiceController.php`, `Api/DevicesController.php` |
| Daemon start/stop/restart/status | `Api/ServiceController.php`, `DeviceMonitor.xml`, `monitor_daemon.py`, `daemon_status.sh` |
| Device discovery / scan / providers | `scripts/.../scan_network.py` (`get_unbound_hostnames`, `get_adguard_rewrite_hostnames`, `get_pihole_hostnames`, `build_hostname_providers`) |
| Notifications (email/webhook) | `scripts/.../NotificationHandler.php`, `notify_*.php`, `smtp_send.py` |
| Defaults and schema | `models/.../defaults.json`, `models/.../DeviceMonitor.xml` |

All paths above are under `src/opnsense/mvc/app/` (for MVC/views/controllers/models) or
`src/opnsense/scripts/OPNsense/DeviceMonitor/` (for runtime scripts).
