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
