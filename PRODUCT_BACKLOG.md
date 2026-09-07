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