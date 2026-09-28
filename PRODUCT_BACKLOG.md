# Product backlog

> **Stub file.** Authored 2026-09-28 by the locale-verification workstream. It contains
> **only** the items referenced by `verification/locales/REPORT-it_IT-2026-09-28.md`. It
> is **not** a complete backlog: no existing backlog file was found in this tree, and no
> source material for other items was available. Migrate the real items in from the
> tracking system, or replace this file wholesale.

Status legend: `OPEN`, `DEFERRED`, `PENDING-EVIDENCE`, `RESOLVED`, `WONTFIX`.

## DM-BL-008b

- Status: **`PENDING-EVIDENCE`** — *not* resolved
- Epic: DM-BL-008
- Reported: 2026-09-28 — operator-reported Italian (`it_IT`) text-stream pass against
  `192.168.20.23`, with both reported check strings passing
  (`[Riepilogo modifiche]`, `[Monitoraggio dispositivi]`) and a reported teardown
  restoring the OPNsense layout parameter to `en_US`.
- Acceptance criteria: not present in this repository.
- Why this is not `RESOLVED`: the report is an operator attestation with no attached
  artifacts. Missing: raw harness/tool output, result JSON/HTML, stream timeline,
  screenshot or page source, tool name and version, run timestamp, OPNsense build, and
  pre/post locale state for the reported `en_US` restore. Full list in
  `verification/locales/REPORT-it_IT-2026-09-28.md` → *Evidence gap*.
- Closes when: those artifacts are attached and the acceptance criteria are checked
  against them.

## DM-BL-008c

- Status: **`DEFERRED`** — unchanged
- Recorded as deferred in the French text-stream verification commit. The Italian pass
  does not cover this item and supplied no closure evidence, so the deferral stands.
- See `verification/locales/deferrals.md`.

## F1

- Status: **`DEFERRED`** — unchanged
- Description unknown to this repository; the identifier appears in the French
  verification commit message and in `verification/locales/REPORT-fr_FR-2026-09-28.md`,
  with no in-tree definition. Supply the tracking-system description, owner, and revisit
  trigger to make this entry actionable.
