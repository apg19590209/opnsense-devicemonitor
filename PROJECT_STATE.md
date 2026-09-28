# Project state

> **Stub file.** Authored 2026-09-28 by the locale-verification workstream. No project
> state file was found in this tree, so this file records **only** the locale
> verification tracks and the `DM-BL-008` items they touch. It is not a full project
> snapshot. Replace or merge it with the authoritative source.

## Repository state

- `verification/locales/` is new in this record set.
- No git repository was present in the tree at the time of writing, so nothing here has
  been committed.
- The `verification/locales/` Selenium harness remains a **proposal**: not written to
  disk, and not runnable on the recording host (no Selenium, no `pip`, no browser or
  WebDriver binary).

## Locale verification tracks

| Locale | Target | Status | Record |
| --- | --- | --- | --- |
| `fr_FR` | OPNsense UI (address not stated in log) | `OPERATOR-REPORTED` | `verification/locales/REPORT-fr_FR-2026-09-28.md` |
| `it_IT` | `192.168.20.23` (OPNsense UI) | `OPERATOR-REPORTED` | `verification/locales/REPORT-it_IT-2026-09-28.md` |

## DM-BL-008 epic

- **`DM-BL-008b`: `PENDING-EVIDENCE`** — not resolved. The 2026-09-28 Italian pass was
  reported by an operator with both check strings passing
  (`[Riepilogo modifiche]`, `[Monitoraggio dispositivi]`) and a reported teardown
  restoring the OPNsense layout parameter to `en_US`, but no artifacts were supplied.
  Closure requires the evidence checklist in `REPORT-it_IT-2026-09-28.md`.
- **`DM-BL-008c`: `DEFERRED`** — unchanged. Not covered by the Italian pass.
- **`F1`: `DEFERRED`** — unchanged. No in-tree description available.

## Open blockers

1. No evidence artifacts for the reported `it_IT` pass (blocking `DM-BL-008b`).
2. No confirmation of the OPNsense locale restore beyond operator attestation
   (infrastructure state, not a documentation fact).
3. No git repository in the working tree; the documentation set cannot be committed or
   pushed from here.
4. Harness not yet implemented, and its host prerequisites are unmet.

## Next actions

- Obtain the artifacts listed in `verification/locales/REPORT-it_IT-2026-09-28.md`.
- Decide whether the locale harness should target a browser UI at all, given that the
  `apps/cli` application in this repository is a terminal TUI.
- Initialise or point at the real repository before any commit/push attempt.
