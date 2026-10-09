# Device Monitor — Architectural Decisions

This file records architectural and behavioural decisions that future work must not accidentally reverse.

A recorded decision remains authoritative until it is explicitly superseded by a later decision. Do not silently rewrite an older decision in a way that removes its original rationale.

If architecture changes later, add a new decision that explicitly supersedes the earlier decision rather than silently changing its history.

## 1. Hostwatch newest-record ownership

### Decision

Hostwatch may contain multiple historical rows for the same MAC address.

Device Monitor must derive current device state from the newest relevant Hostwatch record.

Current state includes:

- IP address
- interface
- online/offline state

Older historical Hostwatch records must not overwrite newer state.

### Reason

Hostwatch retains historical observations. Treating historical rows as equally current can allow stale information to overwrite the latest observation.

## 2. Nmap scanning is single-host only

### Decision

Security scans for a discovered device must target one literal IPv4 address belonging to that device.

Never broaden a targeted scan to:

- a subnet
- an address range
- a VLAN
- all discovered hosts

### Reason

Device Monitor runs on the firewall. Broad scans would increase resource usage and change the intended security and operational scope of the feature.

## 3. Security-scan queue is persistent

### Decision

Queued security scans are database-backed and persistent across daemon cycles and restarts.

Failed scans remain queued for retry rather than silently disappearing.

Scan rate limiting must be preserved.

### Reason

Transient scan failures or resource constraints must not cause queued security scans to be lost.

Persistence also avoids making queued work dependent on one daemon process remaining alive.

## 4. Firewall resource usage must remain bounded

### Decision

Device Monitor functionality must be designed with OPNsense CPU, memory and execution-time limits in mind.

Expensive operations should remain targeted and appropriately rate-limited.

### Reason

Device Monitor shares resources with the production firewall and must not compromise firewall operation.

## 5. Notification recipients come from Device Monitor configuration

### Decision

Security-scan result email uses the same configured recipient as ordinary Device Monitor notifications.

Notification recipients must not be hard-coded into application logic when the existing Device Monitor configuration provides the authoritative value.

### Reason

Using one authoritative notification configuration avoids inconsistent recipient behaviour.

## 6. Preserve device history and configuration

### Decision

Normal development and feature work must preserve existing Device Monitor history and configuration unless an explicit migration or cleanup task requires otherwise.

### Reason

Historical device information is operationally useful and should not be destroyed as a side effect of unrelated work.

## 7. Identity anomaly detection is observational

### Decision

Current identity detection records evidence and anomalies but does not automatically:

- block devices
- delete devices
- alter firewall rules
- remediate identity conflicts

### Reason

Identity signals can have legitimate explanations. Evidence should be collected and presented before enforcement or automatic remediation is considered.

## 8. IPv6 identity conflict handling

### Decision

For identity anomaly detection:

- IPv6 link-local addresses are excluded from anomaly scoring.
- One MAC having multiple IPv6 addresses is not anomalous by itself.
- Duplicate ownership of the same non-link-local ULA/global IPv6 address across different MACs is strong identity-conflict evidence.

### Reason

Link-local and multiple-address IPv6 behaviour are normal parts of IPv6 operation. Treating them as suspicious by themselves would create false positives.
## 9. Infrastructure service evidence must be protocol-specific

### Decision

Infrastructure-service discovery must not treat an open port by itself as
proof that a service exists.

Where practical, Device Monitor must verify the actual application protocol.

For services that cannot be reliably verified with a lightweight
unauthenticated probe, structured service-identification evidence may be used.

In particular:

- `open|filtered` Nmap state alone is not proof of a service.
- SNMP, Kerberos and VPN identification require recognised service evidence.
- local OPNsense WireGuard runtime state is authoritative evidence for the
  locally hosted WireGuard service.

### Reason

Port numbers are commonly reused, filtered or exposed without the expected
application protocol. Protocol-specific or authoritative evidence reduces
false positives in the persistent infrastructure-service inventory.

## 10. Automatic infrastructure discovery must not perform broad Nmap sweeps

### Decision

Automatic Infrastructure Services discovery must not launch fresh Nmap scans
across all known Device Monitor hosts.

Automatic Phase 3 discovery may use:

- existing targeted Nmap scan evidence
- bounded lightweight protocol probes
- authoritative local runtime/configuration evidence

Any Nmap invocation performed by service verification must:

- target one literal IPv4 address only
- remain bounded in execution time
- avoid uncontrolled parallel Nmap subprocesses

Nmap-backed SMB verification is serialised.

### Reason

Device Monitor runs on the production firewall. Broad or highly concurrent
Nmap activity would unnecessarily increase firewall CPU, memory and network
load and would conflict with the existing single-host Nmap architecture.

## 11. AdGuard DNS rewrites are the highest-priority automatic hostname source

### Decision

AdGuard Home DNS rewrite hostname enrichment is optional and disabled by
default.

When enabled, automatic hostname precedence is:

`AdGuard rewrite > Dnsmasq > Kea > ISC > Hostwatch`

AdGuard rewrite names must not overwrite `custom_hostname`, which remains the
separate user-controlled Friendly Name.

Only unambiguous literal IPv4 rewrite answers are accepted. CNAME/non-IP and
IPv6 answers are ignored.

AdGuard API access must:

- use HTTPS with normal certificate verification
- reject embedded URL credentials
- disable HTTP redirects
- fail soft if configuration, authentication, transport or response parsing fails

### Reason

AdGuard DNS rewrites are explicit user-authored static mappings and therefore
provide stronger hostname evidence than dynamic DHCP labels or observational
Hostwatch data.

Keeping Friendly Name separate preserves user intent, while HTTPS-only,
no-redirect and fail-soft behaviour prevents an optional enrichment source
from weakening credential handling or normal device monitoring.

## 12. Stale Hostwatch observations require bounded liveness confirmation

### Decision

Decision 1 remains authoritative for current IP address and interface ownership.

For online/offline state only, this decision supersedes the requirement that
Hostwatch recency alone determines liveness.

Device Monitor must:

- treat a Hostwatch observation within 15 minutes as online
- use a bounded ICMP probe when an otherwise relevant Hostwatch observation is stale
- use two ICMP echo requests with a maximum subprocess duration of 3 seconds
- retain a previously-online device for up to 30 minutes when the bounded probe fails
- allow a previously-offline device seen within the last 120 minutes to recover if it responds
- avoid Nmap or broad subnet probing for liveness confirmation

### Reason

Hostwatch is passive. Quiet but reachable infrastructure devices can therefore
have stale Hostwatch timestamps and be falsely marked offline. A bounded
single-host ICMP confirmation preserves Hostwatch ownership semantics while
avoiding false offline state without introducing broad active scanning.

## 13. Full scans may prime Hostwatch visibility for quiet LAN devices

### Decision

A normal Device Monitor full scan may perform a bounded IPv4 ICMP visibility
priming pass before reading Hostwatch.

The priming pass must:

- derive the LAN IPv4 address and prefix from OPNsense configuration
- operate on IPv4 only
- refuse networks larger than `/24`
- probe only usable host addresses and exclude the OPNsense LAN address itself
- use one ICMP echo request per address with bounded concurrency and timeout
- use no Nmap
- create or update no Device Monitor device records directly
- allow Hostwatch to observe responding or otherwise ARP-visible devices before
  Device Monitor reads the Hostwatch database
- fail soft if configuration or probing fails
- run only during a full scan, not `--update-only` or manual targeted scans

Hostwatch remains authoritative for discovered device identity, MAC address,
interface and observation data.

This decision does not change Decision 12: subnet priming is a discovery
mechanism, not a replacement for the bounded single-device liveness rules.

### Reason

Some quiet static LAN devices communicate only with peers on the same subnet
and may never generate traffic through OPNsense. Passive Hostwatch observation
can therefore miss them entirely.

A bounded lightweight ICMP pass causes OPNsense to interact with the LAN hosts
and allows Hostwatch to observe them, while avoiding broad Nmap discovery,
direct database fabrication and unbounded network activity.

## 14. Device identity history uses explicit lifecycle ownership

### Decision

Device history is organised around persistent lifecycle records rather than a
single mutable device record.

Device Monitor must:

- preserve lifecycle records when a device is removed; lifecycles are archived,
  not deleted
- preserve the original lifecycle `first_seen` value
- preserve the earliest-known MAC history independently of lifecycle changes
- mark a previously known MAC that reappears after removal as `return_pending`
- require an explicit user decision before assigning that returning MAC to a
  lifecycle
- allow the user either to start a new lifecycle or relink the device to one of
  its previous archived lifecycles
- never automatically create a new lifecycle solely because a known MAC returns
- retain lifecycle notes as individual timestamped records
- retain note edit history
- archive notes rather than destructively deleting them from user-facing history
- keep archived-lifecycle notes read-only
- expose lifecycle history and notes through the Device Details page rather than
  a separate comments popup
- keep current device ONLINE/OFFLINE state separate from lifecycle
  active/archived state

The Devices page may identify a returning device and link directly to its
lifecycle-resolution section, but lifecycle resolution remains an explicit user
action.

### Reason

A MAC address can disappear and later return for several legitimate reasons.
Automatically creating or overwriting lifecycle history would lose the
distinction between a continuing device identity and a genuinely new period of
ownership or use.

Explicit lifecycle selection preserves historical evidence, user intent,
timestamps and notes while preventing scanner observations from silently
rewriting device history.

Separating current ONLINE/OFFLINE state from lifecycle state also avoids
treating an active historical lifecycle as proof that a device is currently
reachable.

## 15. Device activity timeline preserves authoritative history and only persists otherwise-lost meaningful transitions

### Decision

The per-device Activity Timeline is a read model assembled from authoritative
historical sources plus a small append-only activity table.

Existing authoritative history remains authoritative for:

- device lifecycle start records and current archive state
- lifecycle notes and note-version history
- identity anomaly detection and resolution records
- targeted Nmap scan history
- initial infrastructure-service discovery through `first_detected`

`device_activity_events` is used only for meaningful transitions that would
otherwise be lost when mutable current-state rows are updated, including:

- IP address changes
- detected hostname changes
- hostname-source changes
- Interface/VLAN changes
- infrastructure-service availability/status changes
- Friendly Name changes
- lifecycle relink actions and preservation of the prior archive timestamp
- identity reopen actions and preservation of the prior resolution timestamp

When an operation would clear or replace an authoritative historical timestamp,
the prior transition must be persisted before that value is cleared, within the
same transaction where practical.

The timeline must not fabricate retroactive transitions from current snapshots.
Routine polling noise such as every `last_seen` update is not activity history.
ONLINE/OFFLINE transitions remain excluded unless a later explicitly designed
feature establishes meaningful, non-noisy semantics for them.

### Reason

Device Monitor stores some information as durable history and other information
as mutable current state. Aggregating the durable sources while recording only
otherwise-lost meaningful transitions preserves operational evidence without
duplicating authoritative records or flooding the timeline with scan noise.

Preserving archive and resolution timestamps before relink/reopen operations also
prevents user actions from erasing the chronology that the timeline is intended
to explain.

## 16. SSH service probes terminate cleanly after banner verification

### Decision

SSH infrastructure-service verification remains based on receiving a valid SSH
server identification banner.

After successfully receiving an SSH 2.0-compatible banner, Device Monitor must:

- send its own SSH client identification string
- send `SSH_MSG_DISCONNECT` with reason `SSH_DISCONNECT_BY_APPLICATION`
- allow the peer a brief opportunity to process the disconnect before closing
  the TCP socket
- treat clean-disconnect transmission as best-effort; a send failure must not
  invalidate service verification that already succeeded from the server banner
- retain the existing `ssh_banner` detection method and service identity

CrowdSec must not be globally weakened or the OPNsense address whitelisted merely
to suppress legitimate Device Monitor SSH service probes.

### Reason

Abruptly closing an SSH connection immediately after reading the server banner
causes OpenSSH to log `Connection closed ... [preauth]`.

CrowdSec classifies that form as `ssh_failed-auth`; repeated scheduled Device
Monitor probes can therefore accumulate into a false
`crowdsecurity/ssh-time-based-bf` alert.

A protocol-level SSH disconnect produces the normal `Received disconnect ...`
log form instead, preventing the false authentication-failure evidence while
preserving SSH discovery, CrowdSec protection, existing service identity and
history semantics.

## 17. Physical-device grouping is an additive user-confirmed identity layer

### Decision

Physical-device grouping must exist as a separate layer above the existing
MAC-based device and lifecycle model.

Device Monitor must:

- create grouping relationships only through an explicit user action
- never automatically merge MAC identities
- preserve each existing MAC identity, lifecycle, identity event and activity
  history unchanged
- allow a MAC to belong to at most one active physical-device group
- retain previous membership records when a MAC is removed from a group rather
  than destructively deleting that relationship
- keep grouping reversible without rewriting historical device records
- continue existing identity-conflict detection against the actual observed
  MAC/IP evidence
- continue requiring the existing `return_pending` lifecycle decision when a
  previously known MAC returns
- leave Hostwatch, scanning, Nmap and infrastructure-service discovery semantics
  unchanged

### Reason

A single physical device may legitimately present multiple MAC addresses, such
as separate wired and wireless interfaces or privacy-addressed interfaces.

Representing that user-confirmed relationship is useful, but merging the
underlying identities would destroy evidence and interfere with lifecycle and
identity-conflict semantics. An additive, auditable grouping layer provides the
association while preserving the existing authoritative history.

## 18. Physical-device grouping lifecycle: removal, empty groups and device deletion

### Decision

This decision extends Decision 17. It does not supersede it.

Status: approved; **implemented**.

#### Membership removal

- Removing a physical-device membership is always permitted, including removal
  of the final active membership.
- Removal soft-closes the membership by recording its removal time; membership
  records are never erased.
- No behavioural last-active-member removal guard is introduced.

#### Empty-group lifecycle

- An active physical-device group must have at least one active membership.
- When a group reaches zero active memberships it is archived automatically by
  recording an archive time.
- Archived groups are historical and read-only: they are not returned as active
  groupings and cannot accept members.
- Archived groups are never restored or reactivated. If the same physical
  relationship becomes relevant again, the user creates a new active group.
- Archived group rows and their membership records are retained for audit and
  history.

#### Device deletion

- Deleting a grouped device soft-closes that MAC's active physical-device
  memberships within the same logical transaction as the deletion.
- The same rule applies to single-device deletion and to clear-all or any
  equivalent deletion flow.
- After memberships are closed, any affected group with zero active memberships
  is archived automatically.
- Device deletion must not erase physical-device group or membership history.

#### Liveness

- Online/offline state must never create, close, remove, archive or restore
  grouping membership or group state.
- Grouping changes remain driven by explicit user or lifecycle operations only.

#### Returning MAC

- Existing `return_pending` lifecycle handling remains authoritative and
  unchanged; a returning MAC is resolved through the existing lifecycle
  workflow first.
- After resolution it may be linked to an existing non-archived group or used to
  create a new group, subject to the existing grouping eligibility rules.
- An archived group is not reopened for the returning identity.

#### User interface

- Any later confirmation shown when the last active member is removed is
  advisory only and must not prevent the removal.

### Reason

Grouping represents a user-confirmed physical relationship without merging
identities or destroying evidence. Permitting removal preserves operator control
and matches the existing membership model, in which removed memberships are
retained rather than deleted.

A group with no active memberships cannot be used or discovered as an active
grouping, so archiving it makes that state explicit and auditable instead of
leaving unreachable rows, and keeps one coherent rule: no active memberships
means archived. Not restoring archived groups keeps the layer a record of
user-confirmed relationships rather than mutable convenience state.

Device deletion removes the current identity that an active membership depends
on, so closing that membership at the same moment keeps memberships consistent
with the current device set, avoids stale active memberships blocking a later
returning MAC, and preserves all membership history. Applying one identical rule
to every deletion path avoids contradictory semantics between deletion flows.

Leaving `return_pending` resolution untouched preserves Decision 14's lifecycle
ownership semantics.

## 19. Change Summary aggregates existing authoritative history

### Decision

The Device Change Summary dashboard is a read-only aggregation of existing
authoritative Device Monitor history. It does not introduce a parallel
event-summary or event-store table, and it does not persist new rows.

The Change Summary API is read-only (GET) and returns merged, sorted, paginated
events derived from existing sources; it performs no database writes.

### Reason

Device Monitor already records authoritative history in dedicated tables. A
separate parallel event store would duplicate that history, risk divergence and
require additional write paths and schema surface for no added benefit.

## 20. "Since last review" is explicit browser-local state

### Decision

The Change Summary "Since last review" time window is resolved from an explicit
browser-local marker stored under the localStorage key
`devicemonitor.changeSummary.lastReviewed`. It does not write to the server or
the Device Monitor database.

Marking reviewed updates only that browser-local marker; it never creates,
updates or deletes server-side state.

### Reason

A per-administrator "since I last looked" reference is inherently
browser/session-local and must not be persisted as shared server state, which
would be wrong for multiple administrators and would introduce a write path
into an otherwise read-only feature.

## 21. Change Summary renders time in the user's browser-local timezone

### Decision

Timestamps are stored and sorted in UTC (`occurred_at_utc`) and remain UTC
internally for storage, filtering and sorting. The Change Summary UI converts
event time for display in the user's browser-local timezone and DST rules using
native browser Date/Intl formatting; no timezone or abbreviation is hardcoded.

### Reason

UTC is the only unambiguous internal representation for sorting and filtering.
Presenting values in the viewing administrator's local timezone (with automatic
DST handling by the browser) makes the read-only summary intuitive without
changing the authoritative stored values.

## 22. Hostname enrichment uses a generic provider abstraction

### Decision

Device Monitor hostname enrichment is centralized behind a small generic
provider abstraction. Each provider exposes a stable `name` (the recorded
`hostname_source`) and a `lookup(device)` that returns a candidate or no result.

- Precedence is centralized and deterministic, strongest-first:
  AdGuard > Dnsmasq > Kea > ISC, with Hostwatch as the observational base value.
- Provider failures are isolated: a failing provider is logged and skipped and
  cannot break the device scan.
- An empty provider result is not an error and never erases an already-resolved
  hostname.
- Provider candidates pass through one shared normalization path (strip
  surrounding whitespace and a trailing dot).
- The user-controlled `custom_hostname` (Friendly Name) remains independent of
  provider enrichment (see Decision 11).
- Future providers (for example Pi-hole) integrate by exposing the same
  `name` + `lookup` interface and being placed in the ordered provider list,
  without modifying core selection logic.

### Reason

Device Monitor already has multiple independent hostname sources, so a common
abstraction avoids scattering provider-specific logic across the codebase and
gives future integrations a stable, tested extension point, while keeping
precedence, normalization and failure behaviour deterministic and auditable.

## 23. Pi-hole hostname enrichment is optional and uses the generic provider framework

### Decision

Pi-hole hostname enrichment is implemented as a provider on top of the generic
DM-BL-005 framework and is disabled by default.

- Data source: the Pi-hole v6 REST API `GET /api/dhcp/leases` (session auth via
  `POST /api/auth` with an app password, then the `X-FTL-SID` header), mapping
  DHCP-lease MAC (`hwaddr`) to hostname (`name`).
- Precedence is AdGuard > Dnsmasq > Kea > ISC > Pi-hole > Hostwatch: Pi-hole is
  weaker than the native OPNsense DHCP sources but stronger than the Hostwatch
  observational base (consistent with the DM-BL-007 backlog wording "lower
  priority than hostname provenance and native OPNsense/Unbound enrichment").
- Access is HTTPS-only with TLS verification enabled, a bounded timeout, and no
  credential values in logs or error messages.
- Provider failure or an empty result never erases an already-resolved hostname.

### Reason

Pi-hole is an external, optional DNS/DHCP source, so it must not be enabled by
default or outrank the authoritative native OPNsense sources. Reusing the generic
provider framework keeps Pi-hole-specific parsing and networking isolated from
core selection logic, matching the DM-BL-005 design.

## 24. Unbound hostname enrichment is native and uses the generic provider framework

### Decision

OPNsense/Unbound hostname enrichment reads local OPNsense configuration
(`/conf/config.xml` host overrides A records and host aliases) with no network
access and no per-device DNS query.

- Precedence: AdGuard > Dnsmasq > Kea > ISC > Unbound > Pi-hole > Hostwatch
  (Unbound is a native OPNsense source, stronger than external Pi-hole and
  weaker than the native DHCP lease sources).
- It requires no enable/disable setting and no provider-specific configuration;
  it is always available when the local Unbound host configuration exists.
- Provider failure or an empty result never erases an already-resolved hostname.

### Reason

Unbound host overrides are user-authored static DNS mappings already maintained
locally in OPNsense, so they are a trustworthy native source. Reading them
directly avoids network queries and keeps enrichment deterministic, while the
generic provider framework isolates parsing from core selection logic.

## 25. Discovery priming and scope follow the selected monitored interfaces

### Decision

This decision supersedes Decision 13 (Full scans may prime Hostwatch visibility
for quiet LAN devices).

A full scan may still perform a bounded IPv4 ICMP visibility priming pass before
reading Hostwatch, but the priming target set is derived from the explicitly
selected **Monitored Interfaces** (their configured IPv4 subnets), not the LAN.

Monitored-interface scoping is fail-closed:

- Discovery, priming, status counters, identity events, notification cleanup and
  the targeted Nmap queue are all restricted to the selected interfaces' subnets.
- An empty selection is refused: a full scan exits with an error and no LAN
  fallback is performed.
- Selected subnets must not overlap.

Hostwatch remains authoritative for discovered device identity; `interface_name`
is metadata only and is never an admission condition (a VLAN observation may be
attributed to a parent physical interface such as `re0`).

### Reason

Device Monitor may observe arbitrary OPNsense interfaces and VLANs, not just the
LAN. Deriving priming and admission scope from the explicitly selected interfaces
keeps discovery deterministic and prevents observation, priming or scanning
outside the intended scope.

## 26. Pi-hole and Unbound hostname enrichment are experimental and opt-in

### Decision

This decision supersedes the "always available / no enable-disable setting"
statement in Decision 24 (Unbound hostname enrichment is native and uses the
generic provider framework).

Pi-hole and Unbound hostname enrichment are both marked **Experimental** and are
**disabled by default**.

- Unbound enrichment is gated behind a new `unbound_enabled` setting (default
  `"0"`). When disabled, `get_unbound_hostnames()` is not called and no Unbound
  provider is constructed. A missing key after an upgrade means disabled.
- Pi-hole enrichment remains gated behind `pihole_enabled` (default `"0"`),
  exactly as recorded in Decision 23.
- Only `"0"` and `"1"` are accepted for the `unbound_enabled` setting.
- When either provider is enabled, the existing provider precedence
  (`AdGuard > Dnsmasq > Kea > ISC > Unbound > Pi-hole > Hostwatch`) and existing
  fail-soft behaviour are unchanged.
- Disabling a provider never erases or downgrades an already-resolved hostname.
- No provider is enabled automatically during install or upgrade.
- No Unbound network query is introduced; Unbound continues to read local
  `/conf/config.xml` only.

### Reason

Pi-hole and Unbound enrichment are optional, low-precedence sources whose value
depends on administrator-maintained external or local data. Marking them
experimental and disabled-by-default prevents a previously absent Unbound source
from silently changing resolved hostnames after an upgrade, keeps the native
always-on sources (Hostwatch/ISC/Kea/Dnsmasq) as the safe default, and makes the
opt-in explicit and reversible.

## 27. Device navigation and terminology: Network Identities and Device Profiles

### Decision

This decision supersedes the user-facing terminology introduced by Decision 17
("Physical-device grouping") and the wording recorded in `PROJECT_STATE.md`
("the user-facing term **Physical Device** is retained").

The Device Monitor submenu exposes a single **Devices** entry with two
tab-style views that link between the existing routes:

- **Network Identities** — the MAC-level discovered-device table (formerly the
  "Devices" view). Explanatory text: "Automatically discovered network
  identities. Each row represents one MAC address."
- **Device Profiles** — the user-confirmed real-world device grouping (formerly
  "Physical Devices"). Explanatory text: "Real-world devices linked to one or
  more network identities, such as wired and Wi-Fi adapters."

User-facing terminology changes:

- "Physical Devices" → "Device Profiles"
- "Physical Device" (column/field) → "Device Profile"
- "Create Device" → "Create Profile"
- "Device Summary" (profile summary) → "Profile Summary"
- "All Devices / Current Devices / Archived Devices" → "All Profiles / Current
  Profiles / Archived Profiles"
- "Current Identities", "Previous Identities", "Add Identity" and "Unlink
  Identity" are retained.
- The term "Device Groups" must not be used for profiles.

### Non-negotiable compatibility

All internal routes, URLs, controller actions, API endpoints, model methods,
JSON fields and database identifiers remain unchanged, including
`index/physicaldevices`, `physicaldevices`, `listphysicaldevices`,
`createphysicaldevice`, `linkphysicaldeviceidentity`,
`removephysicaldeviceidentity`, `physical_devices` and
`physical_device_memberships`. Existing bookmarks, API clients and stored data
continue to work; no database migration is performed.

### Reason

"Devices" versus "Physical Devices" overloaded the word "device" at two
different abstraction levels and implied the discovered view was somehow
non-physical. The new labels map each view to its data model (a MAC identity
versus a user-confirmed real-world profile) while keeping the internal
identifiers stable so that the rename is purely presentational.

## 28. Network Identities view: natural layout, no custom sticky header

### Decision

The Network Identities (`devices.volt`) view must not use custom sticky
positioning, `scroll-snap`, runtime `getBoundingClientRect()` offset
measurement, or pseudo-element "shield" extensions to pin the summary,
toolbar or column header while rows scroll. The page renders in natural DOM
order — page title, Network Identities / Device Profiles tabs, explanatory
text, summary, filter toolbar, column header, device rows — and relies only
on the OPNsense fixed global header for chrome.

Filtering (VLAN Apply/Clear and status) preserves vertical and horizontal
scroll position via `captureScrollPosition()`/`restoreScrollPosition()`, and
must never call `scrollIntoView()`, `focus()`, or follow an anchor jump.

### Reason

A measured-gap sticky stack plus global `scroll-snap` proved fragile: body
rows could appear above the column header, the summary/toolbar/thead stack
reordered during scrolling, and a stale measured gap left blank space below
the page title and could cover the tabs. Correct, stable natural layout is
more important than a sticky header, so the fragile custom implementation was
removed outright rather than patched with further measured offsets.

## 29. Network Identities view: stable sticky complete identities header

### Decision

This decision supersedes Decision 28's prohibition on custom sticky
positioning in `devices.volt`.

The Network Identities view pins the complete plugin header beneath the fixed
OPNsense top navigation while device rows scroll, in this exact vertical order:
the OPNsense page title, the navigation tabs, the explanatory text, the summary
counters, the VLAN/status toolbar and the table column headings. The design:

- makes the OPNsense page title (`header.page-content-head`) sticky (z-index
  30) just beneath the fixed top navigation;
- uses one sticky wrapper (`#devices-sticky-header`) containing the navigation
  tabs, the explanatory text, the summary counters and the filter toolbar
  (z-index 20), pinned flush beneath the sticky title;
- makes the table column headings (`#grid-devices thead th`) stick immediately
  below that wrapper (z-index 10);
- expresses the three offsets as CSS custom properties (`--devices-title-top`,
  `--devices-sticky-top`, `--devices-sticky-thead-top`) recalculated from live
  measurements of the fixed navigation height, the page-title height and the
  header-block height on initial load, window resize, and genuine
  toolbar/header-height changes (via `ResizeObserver`); measuring never
  triggers a table render;
- gives the title, the wrapper and the headings an opaque background and
  z-index so scrolling rows cannot show through or paint beside the header;
- switches the device table (`#grid-devices`) to the separated border model
  (`border-collapse: separate; border-spacing: 0`) so each sticky heading owns
  an opaque, contiguous box and the first body row keeps a single heading
  separator. Bootstrap's default `border-collapse: collapse` lets scrolled
  `tbody` row content paint through the sticky `th` band. The table's
  redundant `border-top` is removed so the toolbar's single bottom border is
  the only separator above the sticky column headings, avoiding a 1px
  double-line seam that only appeared at the top of the page;
- keeps the table on natural (auto) column widths and hides lower-priority
  columns (Services, Device Profile, Scan Status, First Seen, Last Seen)
  progressively - only as many as needed - when the table would otherwise
  exceed its content-box owner's actual width. `syncResponsiveColumns()` is
  driven by a `ResizeObserver` on the table (plus a post-render call) and
  toggles `devices-hide-N` classes, so the break point tracks the real content
  width rather than a hard-coded viewport width. The essential
  identity/status/action columns remain usable without document-level
  horizontal overflow. A fixed-percentage `table-layout: fixed` layout was
  tried and rejected: it squeezed the 13 columns into unusable widths, causing
  Services badges to overlap VLAN/Status and dates to wrap and concatenate.

Natural DOM order is preserved (page title -> tabs -> explanatory text ->
counters -> toolbar -> headings -> rows). The VLAN **Apply VLAN Filter** button
commits the pending checkbox selection once and preserves scroll position via
`captureScrollPosition()`/`restoreScrollPosition()`; there is no standalone
VLAN Clear button (selecting all VLANs and applying restores the unfiltered
view).

The fragile techniques recorded as the reason for Decision 28 remain
prohibited: global `scroll-snap`, pseudo-element "shield" masking, and cached
one-shot `getBoundingClientRect()` gap geometry.

### Reason

Removing the measured-gap sticky stack (Decision 28) fixed the overlap,
jumping and tab coverage, but it also let the complete page header and the
column headings scroll away with a long device list, and the wide table bled
row content past the right edge of the sticky region. A minimal CSS
`position: sticky` design — a sticky title, one sticky wrapper plus sticky
table headings, with lower-priority columns hidden at narrower widths —
restores the complete header without reintroducing the scroll-snap, shield or
one-shot-geometry defects.

## 30. Port discovery is opt-in and single-host

### Decision

The Infrastructure Services Port Discovery tab may run a bounded full TCP
port scan only for one explicitly selected, currently in-scope device.
Weekly scheduling is disabled by default and enabled separately for each
device. At most one due device is scanned after a monitoring cycle, and a
process lock prevents overlapping manual and scheduled port discovery.
Timed-out scans are recorded as incomplete and do not replace prior results.

The port scan does not identify UDP services. An Nmap port or service name
is identification evidence; WireGuard identification still requires
authoritative runtime or configuration evidence under Decisions 9 and 10.

### Reason

The normal top-ports scan can miss nonstandard TCP ports. A separately
opted-in, single-host scan provides wider coverage without turning automatic
infrastructure discovery into a network-wide Nmap sweep.

## 31. Per-device service email preferences

### Decision

Device Details may save `inherit`, `on`, or `off` for each service email event
type, keyed to the normalized MAC address. Existing devices inherit the
global service category and event settings. Explicit `on` overrides the
service category default, but never the global monitoring/email master
switches or missing recipient. Explicit `off` suppresses that MAC's event.
Events with no MAC use global defaults. Suppressed events still advance the
service alert cursor, while selected events remain pending after failed
delivery. Preferences survive lifecycle archival and are never inferred from
Device Profile membership.

### Reason

An administrator can tune alerts for a known identity without changing
alerts for every device. Global delivery and scoping remain authoritative,
and suppressed history cannot unexpectedly replay when preferences change.

## 32. Notification dispatch: configd is authoritative, HTTP API cutover is gated

### Decision

Daemon notification dispatch is authoritative through configd.
`scan_network.py` marks the in-scope filtered set with `notification_pending`
and then invokes the configd actions `devicemonitor sendEmailNotification` and
`devicemonitor sendWebhookNotification`, which run `notify_email.php` and
`notify_webhook.php` as root and call `NotificationHandler::sendEmail(false)`
and `sendWebhook(false, ...)`.

`ConfigController::sendEmailAction` and `sendWebhookAction`
(`POST /api/devicemonitor/config/sendEmail`, `POST /api/devicemonitor/config/sendWebhook`)
exist for authenticated external and automation use. They are not a daemon
transport and must not replace the configd path unless every cutover gate below
is satisfied in a separately authorised task. Until then the `apiEmailUrl` and
`apiWebhookUrl` entries in `defaults.json` remain informational, and
`scan_network.py` must keep the configd path as its working behaviour.

### Reason

The HTTP endpoints invoke the same real-mode `NotificationHandler` calls as the
configd scripts, so a cutover changes transport, authentication and privileges
only — not behaviour — while risking working delivery. Measured on the testbed
(27 September 2026):

- Authentication is mandatory. The installed
  `OPNsense\Base\ApiControllerBase` treats any request carrying an
  `Authorization` header as an external API call requiring an API key and
  secret validated against the `Local API` authenticator plus ACL page access;
  a request without that header requires a session and, for POST, a CSRF token.
  There is no localhost or internal bypass, and the plugin stores no API
  credentials.
- The documented default URL fails TLS hostname verification:
  `https://localhost/api/devicemonitor/config/getversion` returns
  `SSL: no alternative certificate subject name matches target hostname 'localhost'`,
  because the testbed web GUI certificate carries the `192.168.20.23` IP SAN.
- The API path executes inside php-fpm as `www`, while
  `NotificationHandler::fLog()` appends to `/var/log/devicemonitor.log`
  (0640 root:wheel) and direct-SMTP mode reads
  `/var/db/devicemonitor/config.json` (0600 root:wheel). Both would fail for
  `www`, whereas the configd path runs as root today.

### Cutover gates

The following must all hold before `scan_network.py` may send notifications
through `apiEmailUrl` or `apiWebhookUrl`:

1. Credentials source: a root-only credential store owned by the plugin
   (`/var/db/devicemonitor/config.json` is web-readable-configurable and must not
   hold secrets for this purpose), holding the API key and secret of a dedicated
   user granted only `page-services-devicemonitor` (`ui/devicemonitor/*` and
   `api/devicemonitor/*`). Secrets must never be written to the device database,
   the device-monitor log, a command line or the repository, and must be
   replaceable and revocable without touching device data.
2. TLS identity: the request URL must use a host name covered by the web GUI
   certificate SAN, with the issuing CA present in the Python trust store.
   Certificate verification must never be disabled and redirects must not be
   followed to an unverified host.
3. Privilege model: notification code must keep the privileges it needs. Either
   the notifying process retains root equivalence, or the log file and
   config-file permissions are deliberately re-scoped for the web user as an
   explicit, audited change limited to those files.
4. Failure handling: per-channel timeout, no retry storm, authenticated and TLS
   failures logged with distinguishable reasons, and pending notifications left
   intact so no new-device alert is lost. The configd path stays available as an
   explicit fallback until live delivery through the API is proven.
5. Validation: live testbed proof for both channels covering success,
   authentication failure, TLS failure and an unreachable web GUI, plus
   regression proof that the configd path still delivers.

### Non-negotiable compatibility

`notification_pending` semantics, interface-scoped filtering, per-identity
service preferences (Decision 31) and global monitoring/email master switches
remain unchanged by any cutover. `apiEmailUrl` and `apiWebhookUrl` are transport
locations and must not be repurposed to carry credentials. A cutover must not
change the observable behaviour of the Settings delivery tests.

**Superseded (27 September 2026):** the cutover gates in this decision are
withdrawn by Decision 33. The authoritative part of this decision is retained —
configd is the notification transport, and the recorded authentication, TLS
identity and privilege blockers remain the documented reason the HTTP route is
not taken. No cutover is planned. The php-fpm/`www` privilege bullet in the
Reason section is factually corrected by Decision 34.

## 33. Notification HTTP API integration is not implemented

### Decision

Device Monitor does not integrate the HTTP API for notification dispatch.
Daemon notifications continue to use the configd actions
`devicemonitor sendEmailNotification` and `devicemonitor sendWebhookNotification`,
which run `notify_email.php` and `notify_webhook.php` as root and call
`NotificationHandler::sendEmail(false)` and `sendWebhook(false, ...)`. This is
the documented, supported and permanent mechanism for this plugin.

This decision supersedes the cutover gates in Decision 32. The authoritative
part of Decision 32 is retained: configd remains the notification transport and
the recorded blockers (authentication, TLS identity, privileges) stay on record
as the reason the HTTP route is not taken. The `apiEmailUrl` and `apiWebhookUrl`
settings remain informational; they must not be used for dispatch unless a new
recorded decision replaces this one.

The `ConfigController` `sendEmail` and `sendWebhook` endpoints added for the
documented API URLs remain available for authenticated external or automation
use with an OPNsense API key. They are not part of the daemon delivery path, and
this decision requires no change to or removal of them.

### Reason

The plugin already delivers notifications correctly through configctl without
API authentication, and the HTTP route would add complexity without adding any
notification capability:

- It would require provisioning and storing an OPNsense API key and secret for a
  least-privilege user, creating a credential lifecycle (creation, rotation,
  revocation, leak handling) that the plugin otherwise does not need.
- It would require the local web GUI certificate to cover the request host name
  and its issuing CA to be trusted by Python. The shipped default
  (`https://localhost/...`) fails host name verification, and disabling
  verification would weaken security.
- It would move delivery into php-fpm as `www`, which cannot write
  `/var/log/devicemonitor.log` (0640 root:wheel) or read
  `/var/db/devicemonitor/config.json` (0600 root:wheel), so notification logging
  and direct SMTP would need permission changes to working files.
- It would make notification delivery depend on the web GUI and php-fpm being
  available, whereas the current path keeps working without them.
- The endpoints call the same handler methods as the configctl scripts, so the
  switch would change transport, authentication and privileges only, not any
  notification behaviour.

**Corrected (27 September 2026):** the php-fpm/`www` privilege bullet above is
withdrawn — the web GUI executes PHP as root on the testbed. Decision 34 records
the correction. The remaining grounds (API credential lifecycle, TLS host-name
and CA trust, dependency on the web GUI being up, and no capability gain) stand,
and this decision is unchanged.

### Non-negotiable compatibility

`notification_pending` semantics, interface-scoped filtering, per-identity
service preferences (Decision 31), the global monitoring/email master switches
and the observable behaviour of the Settings delivery tests are unchanged.
Future work must not move daemon dispatch to `apiEmailUrl` or `apiWebhookUrl`
without a new recorded decision that explicitly replaces this one.

## 34. Correction: the web GUI executes PHP as root on OPNsense

### Decision

The privilege argument recorded in Decisions 32 and 33 against the HTTP API
route is withdrawn. On the testbed (OPNsense 26.7.4, measured 27 September 2026)
the web GUI is served by lighttpd with PHP executed by `/usr/local/bin/php-cgi`
FastCGI workers running as **root**. `php-fpm` is not installed or running, so
`/usr/local/etc/php-fpm.d/www.conf` (`user = www`) is not the active
configuration. Requests handled through `/api/devicemonitor/...` therefore run
with the same access to `/var/log/devicemonitor.log` (0640 root:wheel) and
`/var/db/devicemonitor/config.json` (0600 root:wheel) as the configd actions.

Decision 33 still stands: the notification HTTP API integration is not
implemented and configd remains the daemon transport. The remaining grounds are
the ones that stay verified — mandatory API key and secret authentication with
ACL page access and no localhost bypass, TLS host-name and CA trust for the API
URL, the credential lifecycle the plugin otherwise does not need, delivery
depending on the web GUI being up, and no notification capability being gained.

### Reason

Decisions 32 and 33 derived the acting user from
`/usr/local/etc/php-fpm.d/www.conf` instead of from the running system, which is
not authoritative. Live measurement showed root-owned `php-cgi` workers on the
`/var/lib/php/tmp/php-fastcgi.socket` listeners, `www` cannot write the
device-monitor log or read `config.json` (verified with `su -m www`), and an API
request through `/api/devicemonitor/config/testemail` did write its result to
that root-only log. The correction keeps the authority order in
`PROJECT_RULES.md`: source code and system evidence outrank documentation.

### Non-negotiable compatibility

This correction changes no decision outcome, no daemon transport and no
notification behaviour. Decision 33's ban on moving dispatch to `apiEmailUrl`
or `apiWebhookUrl` without a new recorded decision remains in force.

## 35. Core catalogue ownership: the installer merges into OPNsense-owned language files

### Decision

`DM-BL-008c` is implemented by merging the plugin's message ids into the OPNsense core
catalogues that the GUI actually reads — `/usr/local/share/locale/<locale>/LC_MESSAGES/
OPNsense.mo` — for the ten plugin locales other than `en_US` (`en_US` is the reference set and
OPNsense ships no catalogue for it). The merge is core-first (`msgcat --use-first`, with
assertions that no existing OPNsense translation changed and that every plugin string is
present, `release/merge-opnsense-catalog.sh`); a locale without a core catalogue (`nl_NL` on
this release) receives the plugin catalogue alone instead of aborting. The staged results go
through the installer's existing guard, backup, rollback and final-hash machinery, and the
update target count is therefore 59 files (`60` fresh) with `core_locales=10`.

**Ownership and the restore boundary are part of the decision.** Those catalogues are owned by
the OPNsense core package, not by this plugin:

- The installer records a pristine copy and a state record per locale under
  `/var/backups/devicemonitor/core-locale/<locale>.state` (with `<locale>.OPNsense.mo` beside
  it), first-write-wins, so a later install never records its own merged output as pristine.
- `uninstall.sh` restores exactly that recorded pre-install catalogue, or deletes the file the
  installer created when no core catalogue existed, and refuses to touch a catalogue that no
  longer matches what it injected.
- On the testbed those recorded copies are the **26 September 2026 hand-merged catalogues**, not
  vendor-clean OPNsense originals: the boundary `uninstall.sh` restores to is "whatever was
  installed before this plugin's install", which on this host already contained plugin strings
  for the keys merged by hand at that time. The only route back to vendor-clean files is a
  package-level reinstall or `pkg upgrade` of the core language files.
- A core `pkg upgrade` can likewise replace the merged catalogues afterwards; the inline-script
  strings then fall back to English until the installer is re-run. The plugin degrades, it does
  not break.

### Reason

The inline-script call sites in the nine views use `lang.query()` → `ControllerRoot::setLang()`
→ `ViewTranslator` over the core domain, so no plugin-side change can translate them: only the
core catalogue can. Merging core-first preserves every existing OPNsense translation (asserted,
and verified live: fr_FR grew from 13,398 to 13,400 keys with no core entry altered), while the
plugin's own "sidecar" domain continues to serve page text. Recording the pre-install files is
what makes the ownership trade-off reversible; treating "no core catalogue" as a supported case
is what lets `nl_NL` work without a core catalogue to preserve. Evidence for the whole change
is in `.cline-reports/REPORT-20260929-152545.md` (engineering), `REPORT-20260929-160427.md`
(testbed install, nine-language runtime acceptance with exit code 0, English-fallback check) and
the deployment record in `PROJECT_STATE.md`.

### Inert legacy message ids: accepted structural overhead

The core-first merge is additive, so a message id that the plugin catalogue once carried and no longer carries
stays in the merged catalogue. Measured on the testbed on 29 September 2026, after the second install replaced the
sidecar help string: each of the ten merged catalogues holds **exactly one** such orphan — the retired
`Translate Device Monitor strings … never modified in either case.` help id — that is ten dead keys, roughly
1.5 KB in total, inside catalogues that hold between 457 (`nl_NL`, plugin-only) and 13,404 entries. Nothing
renders them (the views reference the current ids only) and the acceptance harness ignores them because they are
not page strings.

**Decision: keep the additive merge; no subtractive pass.** The entries are accepted as structural overhead until
the next upstream core-package replacement, which rewrites each catalogue vendor-clean and therefore clears them
without any plugin action; the following install re-merges only the current plugin keys. The overhead is bounded
by the number of retired ids per locale and is self-healing rather than cumulative.

**Reason: a prune cannot be made safe from what the host can prove.** After a merge, the non-plugin keys of a
catalogue are roughly 12,900 upstream strings that must survive untouched, and "keys that are not in the current
plugin catalogue" is not a valid discriminator for them: it also matches upstream strings that a core
`pkg upgrade` added *after* the merge. The recorded pristine copies are the pre-*install* state — on this testbed
already hand-merged, as described above — not vendor-clean originals, so they cannot serve as the baseline either.
A wrong prune would damage the whole core GUI in that language, and the merge's existing guard ("no upstream
translation changed") was not designed to detect removals, so it would not catch it. Against that risk the gain is
deleting ten invisible entries.

### If a subtractive prune is ever revisited (requirements, not implemented)

The route documented for a future decision, in preference to an installer/engine flag:

1. **Provenance first.** The merge records the message ids it injects per locale (a `<locale>.injected` list
   beside the existing state record), so "ours" is recorded data rather than inferred.
2. **Vendor baseline required.** A prune runs only with an operator-supplied vendor-clean catalogue
   (`--vendor <OPNsense.mo>`, available from the core package) and refuses to proceed when any non-injected key
   differs from that baseline.
3. **Separate script, not an engine flag.** `release/prune-opnsense-catalog.sh`, following the same discipline as
   `merge-opnsense-catalog.sh`: stage-only output, rollback copy, per-key assertions that only injected ids were
   removed and every other entry is byte-identical.
4. **Gates.** A dedicated gettext-fixture test (upstream keys preserved, injected keys removed, missing vendor
   file refused) with its own CI step; the installer and uninstaller stay additive unless a further decision says
   otherwise.
5. **Trigger.** Only when the overhead becomes material — for example many retired ids after repeated renames —
   or when an operator needs vendor-identical catalogues for an audit.

### Non-negotiable compatibility

The sidecar translation path still reads and writes nothing under `/usr/local/share/locale`, so
the Settings toggle `sidecar_translation_enabled` keeps its documented fallback chain
(sidecar → core → msgid). Changing the merge target set, the merge semantics, the pristine-record
scheme or the restore boundary requires a new recorded decision, and any change to a manifest
row must update `install-unattended.sh:28` in the same commit because the guarded installer
validates the manifest digest before it does anything. Additive-only merging is the current policy: a subtractive
prune requires a new recorded decision and the provenance plus vendor-baseline preconditions listed above.

## 36. Identity-conflict alerts are gated by their own webhook subcategory switch

### Decision

Identity-conflict alerts (`identity_conflict` frames produced by `notify_identity_email.php`) are gated by a
dedicated configuration switch of their own, `identity_webhook_enabled`, not by the generic webhook master switch
and not by the email settings. The switch belongs to the Webhook Notifications option tree as an isolated
subcategory checkbox, alongside the existing per-category precedent (`identity_email_enabled`,
`service_email_enabled` plus `service_email_new`/`service_email_unavailable`/`service_email_recovered`).

The effective gate for producing an identity frame is, in this order:

1. `enabled` (monitoring master switch),
2. `identity_webhook_enabled` (the new subcategory switch, default `"0"`),
3. `webhook_enabled` **and** a non-empty `webhook_url` (the transport precondition that
   `ConfigController::save` and `NotificationHandler::sendWebhook()` already enforce).

The default is fail-closed: an installation that upgrades gains no identity webhook traffic by itself.

`identity_email_enabled` is no longer consulted by the identity leg, because that leg no longer sends email
(28/29 September 2026 re-route). Its key and stored value stay in place for backward compatibility and the
Settings control keeps working as a stored preference, but it must not be described as delivering email while
the identity leg dispatches to the webhook: retiring or repurposing it is a separate change that requires its own
recorded decision once an email channel exists again.

### Reason

**Reusing the generic webhook gate was rejected (`Option A`).** `webhook_enabled` is the documented master switch
for *new-device* webhook notifications, and it is the only switch an operator consents to when that category is
enabled. Mapping identity alerts onto it would widen the permission set as a side effect of an unrelated action
(risk: broadcasting conflict alerts to an endpoint whose operator only opted into new-device alerts). It would
also ignore the only existing webhook scope control: `webhook_vlans` filters the new-device leg
(`scan_network.py`, notification section) and identity events carry an `interface`, not a VLAN, so the identity
category would be delivered with no scope filter at all. Finally, the two categories could not be separated: a
site wanting new-device alerts but not conflict alerts (or the reverse) has no way to express it, and turning the
endpoint off silences both.

**A dedicated switch is consistent with the established pattern and with the fail-closed defaults.** Identity
and service notification categories already have their own switches with a `"0"` default, and the identity leg's
current activation state on a fresh installation is effectively `"0"`. A dedicated key keeps the administrative
permission discrete, keeps identity alerts independent of the email recipient and method (which this testbed does
not have), and leaves the generic webhook switch meaning exactly what it says.

**Reusing `identity_email_enabled` as the identity gate was also rejected (`Option C`).** An email-named key
governing webhook delivery is misleading in the GUI, contradicts the terminology rule, and would have to be split
again when an email channel returns; a dedicated key costs one setting and one label instead.

**Consequences accepted:**

- The implementation step must add the key (`defaults.json`, `ConfigController::save` read plus `"0"`/`"1"`
  validation plus assignment), the checkbox row in the Webhook Notifications tab, the JS load/save wiring, the
  label in every shipped catalogue, and the manual entry; and it must correct the Settings wording that still
  promises email delivery for conflict alerts.
- Until that implementation lands, the identity leg stays dark on any installation whose email settings are not
  satisfied — which is the current, accepted state, not a regression.
- VLAN/interface scoping of identity frames is not solved by this decision. If identity alerts need to respect a
  scope, that is a new decision, because identity events are keyed by interface rather than VLAN.
- Adding one label does not change the language acceptance threshold: that test derives the expected translated
  string set from the shipped catalogues rather than from a fixed count.

### Amendment (29 September 2026)

The implementation step removed the Email-tab control for `identity_email_enabled` instead of leaving an inert
switch in place, because a control that no longer delivers anything misleads the operator. The stored key remains
in `defaults.json` with its `"0"` default and `ConfigController::save` keeps accepting, validating and writing it,
but no view posts it any more, so the stored value settles to `"0"` on the next save. The names that still carry
"email" — `should_send_identity_email()` and `notify_identity_email.php` — were retained because the helper's path
is part of the installer manifest; they are naming residuals, not behaviour.

## 37. Nmap scan-history writes are deferred to a single asynchronous writer thread

### Decision

`scan_network.py` no longer performs the completion write for a targeted Nmap scan on the scan
thread. `run_targeted_scan_with_history()` builds a plain payload dictionary and hands it to
`enqueue_db_write()`, which places it on a `queue.Queue` consumed by one process-wide daemon
thread (`dm-db-writer`).

- One writer thread owns one long-lived `sqlite3` connection and commits one transaction per job
  (`with conn:`), so a job either commits completely or rolls back completely.
- `_db_write_apply(conn, job)` is the only implementation of the completion write and is shared
  verbatim by the writer thread and by the synchronous fallback, so the two paths cannot drift.
- A `threading.Condition` counter (`_DB_WRITER_PENDING`) makes the queue drainable:
  `flush_db_writes()` blocks until every accepted job has been committed.
- Queued work is drained before the process may exit via `atexit.register` (registered when the
  writer starts) and via an explicit `flush_db_writes()` in `full_scan()`, after the automatic
  targeted-scan loop.
- `stop_db_writer()` drains and stops the thread deterministically; the tests use it so no
  connection is leaked between test modules.

Two writes are deliberately **not** deferred:

- the pre-scan `INSERT INTO nmap_scan_history`, whose `lastrowid` is required by the port rows
  and by the abort path;
- the abort/failure `UPDATE`, because the process is unwinding and the record must not depend on
  a background thread.

### Fallback

`enqueue_db_write()` returns `False` when the writer thread cannot be started or the `put()`
fails. On `False` the caller performs the original synchronous write inside
`with sqlite3.connect(DB_FILE)`. Deferred writing is therefore an optimisation and never a
precondition for recording history: a failure to defer degrades to the previous behaviour
instead of dropping the row.

### Accepted risk — the SIGKILL drain boundary

**Accepted by architectural decision, 30 September 2026.** A history completion is durable only
once the writer thread has committed it, so a drain boundary exists between
`enqueue_db_write()` returning and that commit. If the process is killed without running
`atexit` — `SIGKILL`, an OOM kill, or a supervisor timeout that escalates to `SIGKILL` — a job
that was queued but not yet committed is lost, whereas the inline v2.10 code had already
committed it by that point.

This boundary is accepted for v2.11 because:

- targeted Nmap history is periodic audit data, not transactional state; a lost row is a gap in
  an audit trail, and the next scan rewrites the port set for that host;
- every orderly exit path drains, and that is covered by test;
- the exposure window is the write of a single job, not the whole scan;
- only `nmap_scan_history` and `nmap_scan_ports` are deferred — no device, configuration or
  notification state is affected.

If the daemon is ever changed to enforce a hard `SIGKILL` timeout on scan subprocesses, this
decision must be revisited: either drain in-process before the deadline, or make the writer
synchronous under a configuration flag. A bounded pre-exit drain in `main()` is the preferred
remedy.

**Update, 30 September 2026 — the preferred remedy is implemented.** `main()` in `scan_network.py` is
now a thin wrapper whose `finally` calls `flush_db_writes(5.0)`, and the former body is
`_main_dispatch()`. Every exit path drains, including the early `--discover-services` and
`--list-targets` returns and the SIGINT/error handlers. The 5.0 s bound is half the 10.0 s default the
`atexit` backstop uses, and `flush_db_writes()` logs and returns `False` rather than raising when the
queue has not drained, so a stuck writer cannot hang the exit.

The precondition above is no longer hypothetical: `monitor_daemon.py` has always run the scan as
`subprocess.run(..., timeout=300)`, and Python escalates that timeout to SIGKILL, which no in-process
hook — `atexit`, this drain or a signal handler — can intercept. That window is therefore still open
and unchanged by this drain.

Two further boundary facts were measured while implementing it, and they are recorded here so nobody
reads the drain as broader than it is. **SIGTERM is not covered**: Python's default disposition for
SIGTERM terminates the process without unwinding, so no `finally`, no `atexit` handler and no signal
callback runs — and `service devicemonitor stop` sends SIGTERM. Measured in isolation on this host:
`SIGINT -> finally ran`, `SIGTERM -> returncode -15, finally never reached`. **SIGINT is covered**,
because `_main_dispatch()` catches the resulting `KeyboardInterrupt` and the wrapper's `finally` then
runs. Closing the SIGTERM window needs an explicit `signal.signal(signal.SIGTERM, ...)` handler that
drains and then re-raises the signal; that is a separate change and was deliberately not made here.

### Reason

The completion write previously ran on the scan thread and acquired the SQLite write lock and
its fsync there, once per scan, while the surrounding scan loop opened its own connections for
queue bookkeeping. Moving the write behind a queue removes the lock acquisition and the disk IO
from the scan path and consolidates the writes onto a single connection.

### Verified

`python3 tests/test_deferred_db_writes.py` -> `DEFERRED_DB_WRITES=PASS`, six checks:
commit-and-drain; rescan replaces ports rather than duplicating them; a failed scan records its
error and writes no ports; the asynchronous and synchronous paths produce identical rows; four
threads x sixteen concurrent enqueues are all recorded; and an empty flush returns immediately.

## 38. The optional shared-locale installer branch is retired, superseded by the v2.10 catalogue layout

### Decision

Pull request **#2** (`Device Monitor: optional shared locale installation`,
`feature/optional-locale-installer-20260927` -> `v2.10-development`) was **closed as superseded on
30 September 2026** via `gh pr close 2`
(`✓ Closed pull request apg19590209/opnsense-devicemonitor#2`; closed at `2026-09-30T12:58:15Z`,
head `06a256c69eaa967c953455a4864ce35a2097116e`). No rebase, no merge and no history rewrite were
performed, and no `--force` push was made: the branch is left in place on `origin` at `06a256c`,
because closing a pull request does not delete its branch.

### Reason

The pull request adds an opt-in `--languages none|all|LOCALE[,LOCALE...]` selection to the
unattended installer. The patch was written against the **v2.9** installer, and the v2.10 catalogue
work replaced the entire locale-staging path that the patch edits:

| Installer facet | PR #2 (`c1fa466`) | `v2.10-development` |
|---|---|---|
| release manifest | `release/v2.9-runtime.manifest`, 37 rows | `release/v2.10-runtime.manifest`, 38 rows, sha-pinned to `5d8101ba…` |
| source pin | `defaults.json version == 2.9` | `defaults.json version == 2.10` |
| catalogue layout | flat `src/opnsense/mvc/app/languages/${lang}_devicemonitor.po` | per-locale tree `.../languages/${lang}/LC_MESSAGES/devicemonitor.po` |
| core-domain merge | `ABORT` when the shared core catalogue is absent | `release/merge-opnsense-catalog.sh`, with a `--plugin-only` fallback for locales whose core catalogue is absent (`nl_NL`) |
| staged target count | `expected=37`, widened per selected language | `expected=59` (38 manifest rows + 11 sidecar catalogues + 10 merged core catalogues), `60` on a fresh install |

`release/v2.9-runtime.manifest` does not exist in `v2.10-development`. Rebasing the branch therefore
does not yield a merge conflict to adjudicate but a **rewrite of the locale-staging path**: the
staging loop, the `CORE_LOCALES` accounting, the `expected=59/60` guard and the `CORE_LOCALE_STATE`
reporting all have to be re-derived under a selected-language set. Two of the five rebase conflicts
are add/add duplicates of files `v2.10-development` already owns
(`release/merge-opnsense-catalog.sh` and `tests/test_locale_merge.py`, both introduced by `a9c56b2`,
DM-BL-008c), so the pull request re-adds work that has already landed.

The branch also has no green baseline worth preserving. On its own unmodified head the installer
pre-flight aborts, because its v2.9 pin cannot validate the v2.10 `defaults.json` in its own tree:

```
sh install-unattended.sh --host OPNsense.internal --check
  ABORT: source version          (exit 1)
```

The v2.9 staging layout is therefore superseded. The option-parsing intent is not, but it can only
be delivered as new work on top of the v2.10 installer.

### Verified

- `gh pr view 2` -> `state CLOSED`, `closed true`, `closedAt 2026-09-30T12:58:15Z`,
  `headRefOid 06a256c69eaa967c953455a4864ce35a2097116e`, `baseRefName v2.10-development`.
- Scratch rebase of the true head (`06a256c`) onto `v2.10-development`:
  `CONFLICT (content)` in `.github/workflows/ci.yml`, `PROJECT_STATE.md` and
  `install-unattended.sh`; `CONFLICT (add/add)` in `release/merge-opnsense-catalog.sh` and
  `tests/test_locale_merge.py`. No `release/*.manifest` file conflicts.
- `git show v2.10-development:release/v2.9-runtime.manifest` -> path does not exist.
- `git show c1fa466:install-unattended.sh` -> `Guarded Device Monitor v2.9 installation`,
  `MANIFEST=release/v2.9-runtime.manifest`, `version == 2.9`, `expected=37`.
- `sh install-unattended.sh --host OPNsense.internal --check` on `v2.10-development` ->
  `CHECK_OK version=2.10 predecessor=2.10 files=59 core_locales=10 daemon_running=1 host=OPNsense.internal`.
- The two commits that exist only on `origin/feature/optional-locale-installer-20260927`
  (`26c27a5`, which adds `remove-locales.sh`, and `06a256c`, which restores locales before the
  guarded uninstall) are **not** deleted by this closure; they remain on the branch.

## 39. v2.11 carries its own release manifest, and the v2.10 manifest is retained unchanged

### Decision

The v2.11 tree is cut as a **separate** release artifact instead of repinning the v2.10 one:

- `release/v2.11-runtime.manifest` — 38 rows, SHA256 `df10e9e0…`, generated from this tree.
- `release/v2.10-runtime.manifest` — retained **byte-unchanged** (`5d8101ba…`, 38 rows) as the
  v2.10 release artifact, so a v2.10 deployment remains independently verifiable.
- `install-unattended.sh` points at the v2.11 manifest, pins its digest, and its source-version and
  predecessor guards become `2.11` and `2.8|2.9|2.10|2.11`.
- `defaults.json` `version` becomes `2.11`, so the installer, the manifest and the installed payload
  agree on a single identity. A "v2.11" manifest over a `version == 2.10` tree would be a
  mislabelled artifact, which is why the version bump is part of the cut rather than a later step.

### Reason

Three rows no longer matched the tree — `scan_network.py` (deferred writes, `DECISIONS.md` 37),
`defaults.json` (version) and `devicemonitor_locale.inc` (a comment naming the guarded manifest) —
so the v2.10 manifest had stopped being a truthful description of the tree, and **both** integrity
gates were failing:

```
python3 tests/test_release_manifest.py   -> AssertionError: .../scan_network.py   (rc=1)
sh install-unattended.sh --host OPNsense.internal --check
                                         -> ABORT: source hash .../scan_network.py   (exit 1)
```

Two alternatives were rejected. Rewriting `release/v2.10-runtime.manifest` in place would contradict
the position recorded in `PROJECT_STATE.md` Task 1 ("the v2.10 manifest is the v2.10 release artifact
and must not be rewritten for v2.11 work") and would retroactively change what the published v2.10
asset verifies. Leaving the branch red until release time was the other option, and it was rejected
because it left the branch unable to demonstrate a coherent payload.

The cut follows the coupling rule already recorded in this file under decision 35: a manifest row
change and the installer's digest pin move in the same commit. That rule's
`install-unattended.sh:28` line reference is stale — the pin is line 36 as of this change.

### Verified

- `python3 tests/test_release_manifest.py` -> `V211_RELEASE_MANIFEST=PASS` (rc=0).
- `sh install-unattended.sh --host OPNsense.internal --check` ->
  `CHECK_OK version=2.11 predecessor=2.10 files=59 core_locales=10 daemon_running=1 host=OPNsense.internal`, `EXIT=0`.
- `sha256 -q release/v2.10-runtime.manifest` -> `5d8101ba…`, and the file has no diff.
- `sh -n` on `install-unattended.sh`, `install.sh`, `uninstall.sh` and `release/build-bundle.sh` -> PASS.
- `git diff --check` -> clean.

### Scope note

The check is self-consistent by construction: it was cut from the tree it validates, so it cannot
fail for that tree. It verifies release-artifact integrity only and says nothing about the
correctness of the deferred-write refactor — that evidence is `tests/test_deferred_db_writes.py`.
The gate is expected to go red again the next time a manifest row changes without the manifest and
the pin being refreshed in the same commit, which is the intended behaviour.

## 40. A corrupt devices.db is quarantined and rebuilt empty at initialisation

### Decision

`init_db()` in `src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py` probes the database for
structural corruption before any schema work, and self-heals it:

- **Probe.** `_db_health_problem()` opens the file read-only and immutable
  (`file:<path>?mode=ro&immutable=1`) and runs `PRAGMA quick_check`. A missing file is *not*
  corruption — that is a first run, and the schema creates it. `sqlite3.DatabaseError`, and any
  `quick_check` result other than `ok`, are corruption.
- **Quarantine.** `_db_quarantine()` moves the database, its `-wal` and its `-shm` aside with
  `os.replace` to `<path>.corrupt-<UTC stamp>`; a counter disambiguates a second quarantine in the
  same second. Nothing is deleted.
- **Rebuild.** The pristine schema is rebuilt at `DB_FILE` from the DDL that `_apply_db_schema()`
  already carries. No external asset is used.
- **Alert.** A `CRITICAL DB RECOVERY:` notice goes to `/var/log/devicemonitor.log` and, following
  `monitor_daemon.py`'s precedent, to syslog via `logger -t devicemonitor`. The syslog call is best
  effort and can never fail the recovery.
- The probe runs once per process per path (`_db_health_checked_path`), because a single scan calls
  `init_db()` about a dozen times.

### Accepted risk — the recovered database is empty

**Accepted by architectural decision, 30 September 2026.** Rebuilding restores service but not data:
the device inventory, identities, lifecycles, activity events and Nmap history held in the corrupt
file are absent from the rebuilt database and are **not** restored automatically. Recovery is
therefore availability-preserving, not data-preserving.

Accepted because:

- the alternative is a plugin that fails every scan until an operator intervenes, logging a failed
  scan every cycle;
- the corrupt file is preserved under a `.corrupt-<stamp>` name, so the data stays recoverable by
  hand with `sqlite3 .recover` or a `dump`/`restore`;
- the alert states, in the log line itself, that the history is not restored;
- only `devices.db` is affected — OPNsense configuration and `config.json` are not in the database.

If the operator-visible cost of a silent empty rebuild is ever judged too high, the remedy is to gate
the rebuild behind an explicit configuration flag, or to attempt salvage first and rebuild only when
salvage fails. Both are larger changes and need their own decision.

### Reason

`init_db()` is the single database initialisation hook and had no integrity guard. A malformed
`devices.db` therefore raised `sqlite3.DatabaseError` at every one of its 13 call sites, so the
scanner aborted and the plugin stayed dead until an operator acted.

### Verified

- `tests/test_db_corruption_recovery.py` -> `DB_CORRUPTION_RECOVERY=PASS`, five checks: a missing
  database is a first run; a malformed database is quarantined byte-for-byte and replaced by a valid
  schema; the `-wal` and `-shm` sidecars are quarantined with it; a healthy database keeps its rows
  across repeated `init_db()` calls; and the probe runs once per process per path.
- The read-only immutable URI is required, not stylistic. Measured on this host: a plain
  `sqlite3.connect(path)` **deletes** `-wal` and `-shm` while it fails to open a malformed database,
  destroying the quarantine's own evidence — the new test caught this on its first run.
  `mode=ro`, `immutable=1` and `mode=ro&immutable=1` all raise `DatabaseError` on garbage, all
  report `ok` on a healthy WAL-mode database, and none deletes a sidecar. The live database is in
  `journal_mode=delete`, so the sidecar path is defensive rather than routine.
- `tests/test_deferred_db_writes.py` -> `DEFERRED_DB_WRITES=PASS`; `test_device_activity_events.py`
  and `test_device_lifecycle_return.py`, the other `init_db()` callers, still pass.
- `tests/test_release_manifest.py` -> `V211_RELEASE_MANIFEST=PASS`, and
  `sh install-unattended.sh --host OPNsense.internal --check` -> `EXIT=0`, after the same-change-set
  manifest re-cut that decision 35 requires.

## 41. SIGTERM drains the deferred writer queue and then re-raises

### Decision

`scan_network.py` installs a SIGTERM handler from `main()` — deliberately not at import time — that
drains the deferred writer queue with the same `SHUTDOWN_DRAIN_TIMEOUT` (5.0 s) the normal exit path
uses, then restores the default disposition and re-raises the signal:

- `_sigterm_drain_handler()` accepts one drain per process (`_SIGTERM_DRAIN_DONE`). A second SIGTERM
  arriving during the drain exits immediately instead of draining again, because a repeated SIGTERM
  means "stop now".
- `_reraise_sigterm()` does `signal.signal(SIGTERM, SIG_DFL)` followed by
  `os.kill(os.getpid(), SIGTERM)`, so the process still reports death-by-SIGTERM (`returncode -15`)
  to `rc.d` and to supervisors. It is a separate function so the handler can be exercised without
  killing the process running the test.
- `_install_sigterm_drain()` swallows `ValueError` and `OSError`: a non-main thread, or a platform
  that refuses the handler, degrades to the exit-path drain instead of failing the scan.
- Installing from `main()` rather than at import time matters because the test harness imports this
  module; an import-time handler would hijack the caller's SIGTERM handling.
- `SHUTDOWN_DRAIN_TIMEOUT` is now one constant, used by both the exit path and the handler.

### Reason

Decision 37's remedy — a bounded pre-exit drain in `main()` — was implemented as the v2.11 Task 6
wrapper, and it covers every normal and early return, the error handler and SIGINT. It does **not**
cover SIGTERM, because Python's default disposition terminates the process without unwinding: no
`finally`, no `atexit`, no callback. Measured before this change: `SIGINT -> finally ran`,
`SIGTERM -> returncode -15, finally never reached`. Since `service devicemonitor stop` sends SIGTERM,
that was the one shutdown path on a firewall where a queued history completion could still be lost.

### Verified

Out of process, with the real handler and a real SIGTERM, against a job deliberately held in flight by
a slow `_db_write_apply`:

```
WITHOUT handler  returncode=-15   finished_at=None                 -> job committed: False
WITH handler     returncode=-15   finished_at=2026-10-01 00:00:03  -> job committed: True
```

The exit status is identical both ways, which is the point: the handler buys the commit without
changing what a supervisor or `rc.d` observes.

`tests/test_shutdown_drain.py` -> `SHUTDOWN_DRAIN=PASS`, four checks: `main()` installs the handler
and keeps the matching exit-path drain (a wiring pin read from the source); the handler commits a job
that is still in flight and then re-raises; a second SIGTERM does not drain twice; and a platform that
refuses the handler logs and continues. `tests/test_deferred_db_writes.py`,
`tests/test_db_corruption_recovery.py`, `tests/test_device_activity_events.py` and
`tests/test_device_lifecycle_return.py` all still pass, and `test_release_manifest.py` reports
`V211_RELEASE_MANIFEST=PASS` after the same-change-set re-cut that decision 35 requires.

### Residual risk, unchanged

SIGKILL cannot be intercepted by any in-process hook, and `monitor_daemon.py` runs this script with
`subprocess.run(timeout=300)`, which Python escalates to SIGKILL. That window remains the accepted
risk recorded in decision 37 and is not affected by this change.

### Behavioural note

While the handler drains, the main thread may be inside a `subprocess.run()` waiting on an nmap scan.
The drain waits for the writer queue only; it does not signal or reap that child, so a scan killed by
SIGTERM can leave its nmap child to be reaped by init. That is the same outcome as the previous
default disposition, so nothing regressed — but any future "stop the scanner cleanly on SIGTERM"
change has to signal the child as well.

## 42. `tests/price_gate.py` carries its own Apache-2.0 record, separate from the repository licence

### Decision

`tests/price_gate.py` is a standalone test-harness utility distributed with its own licensing
record rather than under the repository's BSD-2-Clause terms:

- Its copyright notice names the individual holder
  (`Copyright 2026 Anthony Gonzalez (apg19590209)`), per the operator's ownership attestation
  recorded in `.cline-reports/REPORT-20261009-142252.md` and the follow-up instruction that set
  the individual name.
- It declares `SPDX-License-Identifier: Apache-2.0` and is accompanied by the full Apache-2.0
  terms in `tests/price_gate.LICENSE`, satisfying Apache-2.0 section 4(a) for source
  distribution.
- The position is deliberately mixed-licence: the plugin payload stays BSD-2-Clause (`LICENSE`,
  `Copyright (c) 2024, Hacesoft`); this test asset stays Apache-2.0, so the repository's BSD-2
  terms are not asserted over third-party code.

### Provenance

The utility is a port, not original composition. It was copied verbatim from the Cline monorepo
(`apps/cli/tests/price_gate.py`, Apache-2.0; that project's `LICENSE` appendix names
`Copyright 2026 Cline Bot Inc.`). The ported revision was byte-identical, sha256
`3fea2443f2bbc644ca30ddfa7ec3c4109579933019e4e78b3bf1e9ad9678a03c`, and the only later change is
the header comment block added on 9 October 2026. The header therefore keeps upstream authorship
(`Author: Cline Bot Inc.`) alongside the local copyright notice; Apache-2.0 section 4(c) is met
because the upstream attribution travels both in the file and in `tests/price_gate.LICENSE`.

### Reason

The gate is developer/CI tooling rather than plugin payload: nothing under `src/` imports it, it is
absent from `release/v2.11-runtime.manifest` (0 of 38 rows mention `tests/`), and no `ci.yml` step
executes it. Keeping its licence self-contained isolates the copyright record and keeps the
Apache-2.0 obligations with the file.

### Verified

`python3 -m py_compile tests/price_gate.py` passes; `python3 tests/price_gate.py --status` reports
`peak=false off-peak` on 9 October 2026 with the window boundaries (11:00 and 16:00 inside, 14:00
and 20:00 outside, weekends never) unchanged from the pre-header revision.
`tests/price_gate.LICENSE` is a byte-copy of the upstream Apache-2.0 text (sha256
`f704446a5f1271608805598b557e4288cf8580477ea038c9c3d8b361f693f6b8`, 201 lines).

### Residual risk

The individual ownership notice rests on the operator's instruction; no assignment document is held
in the repository, and the same file previously carried a Hacesoft notice (commit `75d3ad3`,
superseded by `e038933`) and before that the upstream Cline Bot Inc. notice. If the rights position
changes again, this decision and the file header must be updated together.
