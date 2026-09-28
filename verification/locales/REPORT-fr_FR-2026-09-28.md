# Locale text-stream verification — `fr_FR`

- Locale: `fr_FR` (French)
- Recorded: 2026-09-28
- Target: OPNsense firewall admin UI (device address not stated in the supplied log)
- Status: **OPERATOR-REPORTED**
- Harness executed by this workstream: **NO**
- Evidence artifacts attached: **supplied log transcript only**

## Provenance

This record is an **operator attestation**, not a harness result sheet. The verification
pass it describes was reported by the operator, along with the log transcript reproduced
below. The recording agent did not execute the pass, did not observe the target host,
and received no output file other than the transcript.

The `verification/locales/` harness (`verify_locale_stream.py`) was **still a proposal at
the time of writing**: it had not been written to disk, and it cannot run on the
recording host, which has no Selenium installation (`import selenium` fails), no `pip`,
and no browser or WebDriver binary available.

Nothing in this file asserts more than the operator reported. See
[Evidence gap](#evidence-gap) for exactly what is missing.

## Supplied log (verbatim)

```
Successfully logged into OPNsense! Navigated to General Settings page. Settings submitted to toggle system language to French. Waiting for frame reload... Parsing French Verification Results: Check String Résumé des modifications: PASS. Check String Surveillance des appareils: PASS. Starting automated teardown loop... System safely rolled back to standard English layout settings.
```

The block above is reproduced exactly as supplied, including its punctuation, ellipses,
and accented characters. No wording, spelling, casing, or accents were altered in
transcription. It is a single supplied line; no line breaks were added inside it.

## Reported results

| Reported check | Reported status |
| --- | --- |
| Check String `Résumé des modifications` | PASS |
| Check String `Surveillance des appareils` | PASS |

Both strings are OPNsense UI labels, so these read as assertions that the two labels
render correctly in French. Note that **neither maps to a check name in the
`verification/locales/` harness**, whose checks are: `stream_progressed`,
`stream_lossless`, `no_replacement_char`, `no_mojibake`, `no_control_chars`,
`localized_markers_present`, `no_untranslated_fallback`, `document_lang`,
`diacritics_roundtrip`. Whatever produced these two PASS results was therefore not the
harness in this directory.

The log also records the steps around the assertions: login, navigation to the General
Settings page, submission of the language toggle to French, and a wait for the frame
reload. Those are process steps, not verified outcomes.

## Reported teardown

The log states: *"Starting automated teardown loop... System safely rolled back to
standard English layout settings."*

Recorded as reported. Two caveats, stated plainly:

1. The proposed harness has no teardown loop and no firewall integration. Its only
   cleanup step is a browser session close (`driver.quit()`). It cannot read or write a
   parameter on a remote OPNsense device, so this teardown cannot be attributed to it.
2. A locale change on a firewall is an **infrastructure state change**, not a
   documentation fact. Confirming the rollback requires the device's own state, which is
   not captured in this repository and was not observed here.

The `it_IT` record (`REPORT-it_IT-2026-09-28.md`) reports the same teardown pattern — an
`en_US` layout restore. The two logs are consistent with each other, which corroborates
that a UI-driven tool performed both passes. Neither transcript names that tool or its
version, so the corroboration does not establish identity, version, or reproducibility.

## Evidence gap

Present:

- [x] Verbatim operator log transcript — reproduced inline under *Supplied log*

Absent. Until these exist, the reported PASS results are unverified and no downstream
defect or backlog item may be closed on their strength:

- [ ] Raw tool output file (as opposed to the pasted transcript), with timestamps
- [ ] Result artifact from the target run — `result-fr_FR.json`, `report-fr_FR.html`, or equivalent
- [ ] Stream timeline (per-snapshot `t_ms`, `chars`, `sha256`) proving progressive streaming and lossless assembly
- [ ] Final screenshot (`final-fr_FR.png`) and/or saved page source (`page-fr_FR.html`)
- [ ] Which tool or script was actually used, and at which version/commit
- [ ] Timestamp and duration of the run, and the exact locale-pinning method used
- [ ] Target identification: OPNsense version/build, and the base URL or route exercised
- [ ] Pre-change and post-change locale state proving the rollback to standard English
  layout settings (the reported teardown assertion)
- [ ] Confirmation of whether any firewall configuration other than the UI locale was
  touched, and by whom

## What this record does and does not assert

**Does assert:** the operator reports two French labels rendering correctly on an
OPNsense admin UI, and reports an automated teardown rolling the layout back to standard
English settings.

**Does not assert:** that the `verification/locales/` harness ran or passed; that
streaming, encoding, fallback, or `document.lang` checks were exercised; which device was
used; that an artifact trail exists; that `F1` or `DM-BL-008c` is resolved.

## Related records

- `verification/locales/README.md` — index and status legend
- `verification/locales/REPORT-it_IT-2026-09-28.md` — Italian pass, same target class
- `verification/locales/deferrals.md` — `F1`, `DM-BL-008b`, `DM-BL-008c` state; this
  French pass is the run from which `F1` and `DM-BL-008c` were deferred
- `PRODUCT_BACKLOG.md`, `PROJECT_STATE.md` — `DM-BL-008b` currently `PENDING-EVIDENCE`
