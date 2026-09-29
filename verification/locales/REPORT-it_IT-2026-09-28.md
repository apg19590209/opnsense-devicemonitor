# Locale text-stream verification — `it_IT`

- Locale: `it_IT` (Italian)
- Recorded: 2026-09-28
- Target: `192.168.20.23` (OPNsense firewall admin UI — outside this repository)
- Status: **OPERATOR-REPORTED**
- Harness executed by this workstream: **NO**
- Evidence artifacts attached: **NONE**

## Provenance

This record is an **operator attestation**, not a harness result sheet. The verification
pass it describes was reported by the operator after a remote run against
`192.168.20.23`. The recording agent did not execute the pass, did not observe the
target host, and did not receive any output file from it.

The `verification/locales/` harness (`verify_locale_stream.py`) described in
`README.md` was **still a proposal at the time of writing**: it had not been written to
disk, and it cannot run on the recording host, which has no Selenium installation
(`import selenium` fails), no `pip`, and no browser or WebDriver binary available.

Nothing in this file asserts more than the operator reported. See
[Evidence gap](#evidence-gap) for exactly what is missing.

## Harness status (updated 2026-09-29)

The paragraphs above describe 2026-09-28 and stay as written. As of **2026-09-29** the
harness exists: `verification/locales/verify_locale_stream.py`, version 0.1.0, with an
offline self-test at `verification/locales/tests/test_verify_locale_stream.py`. Its
`--check-env` and `--dry-run` operations refuse to proceed on this host (`selenium` is not
importable, `pip` is absent, no browser or WebDriver binary is installed), and
`locale_cases/it_IT.json` carries `null` for `target.base_url` and `target.route`, so a run
cannot be started for `it_IT` either.

None of this changes the record: the harness **has not been run for `it_IT`**, no check in
the table below was produced by it, and `DM-BL-008b` remains `PENDING-EVIDENCE`.

## Reported results

Quoted verbatim as supplied by the operator:

| Reported check | Reported status |
| --- | --- |
| Check String `[Riepilogo modifiche]` | PASS |
| Check String `[Monitoraggio dispositivi]` | PASS |

Both strings are OPNsense UI labels, so these read as assertions that the two labels
render correctly in Italian. Note that **neither maps to a check name in the
`verification/locales/` harness**, whose checks are: `stream_progressed`,
`stream_lossless`, `no_replacement_char`, `no_mojibake`, `no_control_chars`,
`localized_markers_present`, `no_untranslated_fallback`, `document_lang`,
`diacritics_roundtrip`. Whatever produced these two PASS results was therefore not the
harness in this directory.

## Reported teardown

The operator reports that a teardown loop ran and confirmed the OPNsense **layout
parameter was restored to English (`en_US`)**.

Recorded as reported. Two caveats, stated plainly:

1. The proposed harness has no teardown loop and no firewall integration. Its only
   cleanup step is a browser session close (`driver.quit()`). It cannot read or write a
   parameter on a remote OPNsense device, so this teardown cannot be attributed to it.
2. A locale change on a firewall is an **infrastructure state change**, not a
   documentation fact. Confirming the restore requires the device's own state, which is
   not captured in this repository and was not observed here.

## Evidence gap

The following are absent. Until they exist, the reported PASS results are unverified
and no downstream defect or backlog item may be closed on their strength:

- [ ] Raw harness/tool output (JSON, log, or console transcript) from the machine that ran the pass
- [ ] Result artifact from the target run — `result-it_IT.json`, `report-it_IT.html`, or equivalent
- [ ] Stream timeline (per-snapshot `t_ms`, `chars`, `sha256`) proving progressive streaming and lossless assembly
- [ ] Final screenshot (`final-it_IT.png`) and/or saved page source (`page-it_IT.html`)
- [ ] Which tool or script was actually used, and at which version/commit
- [ ] Timestamp and duration of the run, and the exact locale-pinning method used
- [ ] Target identification: OPNsense version/build, and the base URL or route exercised
- [ ] Pre-change and post-change locale state proving the layout parameter really is `en_US`
  again (the reported teardown assertion)
- [ ] Confirmation of whether any firewall configuration other than the UI locale was
  touched, and by whom

## What this record does and does not assert

**Does assert:** the operator reports two Italian labels rendering correctly on
`192.168.20.23`, and reports a layout-parameter restore to `en_US`.

**Does not assert:** that the `verification/locales/` harness ran or passed; that
streaming, encoding, fallback, or `document.lang` checks were exercised; that an
artifact trail exists; that `DM-BL-008b` is resolved.

## Related records

- `verification/locales/README.md` — index and status legend
- `verification/locales/deferrals.md` — F1, `DM-BL-008b`, `DM-BL-008c` state
- `PRODUCT_BACKLOG.md`, `PROJECT_STATE.md` — `DM-BL-008b` currently `PENDING-EVIDENCE`
