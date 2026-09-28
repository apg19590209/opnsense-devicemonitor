# Locale verification deferrals

Status of items raised by the locale verification tracks. Updated 2026-09-28.

## Status legend

| Status | Meaning |
| --- | --- |
| `DEFERRED` | Consciously not actioned yet; owner and revisit trigger recorded. |
| `PENDING-EVIDENCE` | Claimed or reported done, but no artifact exists to close it. Not resolved. |
| `RESOLVED` | Closed, with an artifact trail referenced. Not used in this file yet. |

## Items

### F1

- Status: `DEFERRED` (unchanged)
- Note: description not present in this repository. The identifier `F1` appears in the
  French verification commit message only, with no in-tree definition. Owned content
  must be supplied from the tracking system before this entry can carry a description,
  owner, or revisit trigger.

### DM-BL-008b

- Status: `PENDING-EVIDENCE` — **not resolved**
- Reported: 2026-09-28, operator-reported Italian pass against `192.168.20.23`; both
  reported check strings passed (`[Riepilogo modifiche]`, `[Monitoraggio dispositivi]`).
- Blocker still open because: no harness output, no result artifact, no stream timeline,
  no screenshot or page source, no OPNsense build/version, and no pre/post locale state
  were provided. See `REPORT-it_IT-2026-09-28.md` → *Evidence gap*.
- Cleared when: the evidence checklist on `REPORT-it_IT-2026-09-28.md` is satisfied and
  the acceptance criteria for `DM-BL-008b` are checked against it.

### DM-BL-008c

- Status: `DEFERRED` (unchanged)
- Note: recorded as deferred in the French text-stream verification commit. No evidence
  of closure was supplied with the Italian pass, and the Italian pass does not cover
  this item, so its deferral stands.

## Blockers cleared by this update

**None.** No deferral track was unblocked. The operator-reported Italian pass is a
useful signal, but two quoted label strings without artifacts cannot close any of the
three items above.

## What would clear each item

Only artifacts, not further attestation. For `DM-BL-008b`, the minimum is: the run's
raw output plus result JSON/HTML, a stream timeline, one screenshot or page source, the
tool/version used, and the OPNsense build plus before/after locale state for the
reported `en_US` restore.
