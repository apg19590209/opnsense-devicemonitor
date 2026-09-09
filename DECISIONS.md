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
