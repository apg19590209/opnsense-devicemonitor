# Locale verification artifacts

Drop point for **genuine** run output from the `it_IT` / `fr_FR` verification passes.

## What belongs here

Real output produced by whatever tool drove the target UI — for example
`result-<locale>.json`, `report-<locale>.html`, `final-<locale>.png`,
`page-<locale>.html`, or the tool's own log file.

## What does not

- Hand-written or pasted summaries dressed up as run output. A file named
  `*_run.log` must be the tool's own output, not a transcription.
- Operator-attested statements with no artifact. Those belong in the
  `REPORT-<locale>-<date>.md` records, under *Supplied log*, where the provenance is
  stated explicitly.

If the only thing available is a pasted transcript, the correct action is to record it
in the report as operator-attested and leave the item `PENDING-EVIDENCE`. Copying that
transcript into this directory under a run-log filename would misrepresent its
provenance and must not be done.

## Why this directory is exempt from the `out` ignore rule

The repository `.gitignore` ignores `out` at every level. Evidence that cannot be
committed is not evidence, so `verification/locales/out/` and its contents are negated
explicitly at the end of the root `.gitignore`. Keep that negation narrow: it exists for
this drop point only.

## Acceptance checklist before an item can be closed

1. Raw tool output present, in the tool's own format.
2. Result artifact (`result-<locale>.json` / `report-<locale>.html`) present.
3. Stream timeline with per-snapshot `t_ms`, `chars`, `sha256`.
4. Screenshot and/or saved page source.
5. Tool name and version.
6. Run timestamp and duration, plus the locale-pinning method.
7. Target identification: OPNsense build/version and the route exercised.
8. Pre-change and post-change locale state for the reported rollback.
9. Confirmation that no firewall configuration other than the UI locale was touched.
