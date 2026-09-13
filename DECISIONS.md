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

Status: approved; **not yet implemented**. Until it is implemented, the rules
below describe intended behaviour, not current behaviour.

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
