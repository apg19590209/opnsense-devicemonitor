# Device Monitor — Product Backlog

This file records explicitly discussed Device Monitor work that has been deferred
or approved for future development.

## Backlog rules

- Add only work explicitly discussed and intentionally deferred or approved.
- Do not invent speculative features merely to populate the backlog.
- Do not duplicate the active task from `PROJECT_STATE.md`.
- Completed work is removed from the open backlog once authoritative project state
  has been updated.
- Architectural constraints remain in `DECISIONS.md`.
- Environment and component facts remain in `SYSTEM_MAP.md`.

## Open backlog

### DM-BL-001 — User-confirmed physical-device identity grouping

Design user-confirmed physical-device identity grouping for cases where one
physical device may legitimately use multiple MAC addresses.

Constraints:

- grouping must be explicitly user-confirmed
- do not automatically merge device identities
- preserve existing device and identity-event history

### DM-BL-002 — Device activity and identity timeline

Add a per-device chronological history of meaningful changes such as first/last
seen, IP changes, hostname/source changes, VLAN/interface changes, discovered
services, identity events and targeted security-scan results.

### DM-BL-003 — Infrastructure-service change alerts

Notify on meaningful verified infrastructure-service transitions, such as a new
service appearing, a previously verified service disappearing, or an
infrastructure role changing.

Constraints:

- use existing protocol-specific evidence rules
- avoid noisy raw port-change alerts
- preserve bounded scanning and existing single-host Nmap constraints

### DM-BL-004 — OPNsense/Unbound hostname enrichment

Investigate high-confidence hostname enrichment from locally configured OPNsense
Unbound host overrides and aliases.

Before implementation, define its precedence relative to AdGuard, Dnsmasq, Kea,
ISC and Hostwatch.

### DM-BL-005 — Generic hostname-provider framework

When enough independent hostname sources justify it, introduce a small provider
abstraction carrying hostname, source and confidence/provenance information.

Do not refactor solely for architectural neatness; implement only when additional
providers make the abstraction worthwhile.

### DM-BL-006 — Device change summary dashboard

Add a concise dashboard summary of meaningful recent changes, such as new
devices, IP changes, newly verified infrastructure services, identity events and
devices not seen for a configured period.

### DM-BL-007 — Optional Pi-hole hostname enrichment

Consider Pi-hole as an optional hostname source if there is user demand or a
deployment available for real validation.

Keep it lower priority than hostname provenance and native OPNsense/Unbound
enrichment.
