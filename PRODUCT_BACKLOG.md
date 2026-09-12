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


### DM-BL-004 — OPNsense/Unbound hostname enrichment

**Description:** Investigate and, where the data is sufficiently authoritative
and unambiguous, add hostname enrichment from locally configured OPNsense Unbound
host overrides and aliases. Define Unbound's precedence relative to AdGuard,
Dnsmasq, Kea, ISC and Hostwatch before implementation. Preserve
`custom_hostname` as the independent user-controlled Friendly Name and retain
hostname-source provenance.

**Benefit:** Reuses trusted names already maintained in OPNsense, particularly
for static and infrastructure devices that may have poor or missing DHCP or
Hostwatch names. It can improve recognition without duplicate manual naming,
while retaining explicit source provenance.

**Deferred:** Unbound is not currently used in this environment, so there is no
immediate local benefit or real deployment data available for validation.

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
