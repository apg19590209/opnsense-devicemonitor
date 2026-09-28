# Locale text-stream verification — `fr_FR`

- Locale: `fr_FR` (French)
- Recorded: 2026-09-28
- Target: OPNsense firewall admin UI (device address not stated in the supplied log)
- Target address, operator-attested: `192.168.20.23` — the same host as the `it_IT`
  testbed. Attested by the operator on 2026-09-28. See [Target attribution](#target-attribution).
  Not present in the supplied log, and corroborated by no artifact.
- Case data: `verification/locales/locale_cases/fr_FR.json` — case boundaries and
  provenance only; it holds no run output and closes nothing
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

## Target attribution

The line above the fold states a fact about the transcript: the supplied log does not name
a device. That statement is still true and is not withdrawn here.

Separately, the operator has attested that this French pass ran against the **same target
host as the Italian pass, `192.168.20.23`**. That is recorded as an operator statement,
with its provenance, and not as a verified fact:

- **Source.** Operator attestation, 2026-09-28, through this repository's tracking channel.
- **Corroboration.** None. The supplied log names no address, no route, and no build, and
  no artifact from the target has been supplied. `REPORT-it_IT-2026-09-28.md` records the
  same address for the Italian pass, but two attestations of one address are not an
  artifact trail — they are the same class of evidence, and the Italian address is itself
  unverified.
- **Standing.** This is a working assumption about scheduling and scope. It may not close
  anything, it does not satisfy the *Target identification* item in the evidence gap, and
  it must be corrected if an artifact shows a different host.

`locale_cases/fr_FR.json` carries the same address and the same caveat in its `target`
block (`address_provenance`, `address_in_supplied_log: false`,
`address_corroborated_by_artifact: false`).

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
- [x] Case-boundary file `verification/locales/locale_cases/fr_FR.json` — case data only;
  it contains no run output and closes nothing

Absent. Until these exist, the reported PASS results are unverified and no downstream
defect or backlog item may be closed on their strength. **Nothing supplied since this
record was written is a run artifact**, so every box below stays unchecked and the record
stays `OPERATOR-REPORTED` — an operator statement, however precise, does not satisfy any
item here (see `out/README.md` → *Acceptance checklist before an item can be closed*).

- [ ] Corroboration that this run targeted `192.168.20.23` — the address is
  operator-attested only, and the supplied log names no device ([Target attribution](#target-attribution))
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
used (the address above is operator-attested, not evidenced, and the supplied log does not
name one); that the shared-host attribution is correct; that an artifact trail exists; that
`F1` or `DM-BL-008c` is resolved; that `DM-BL-008b` is resolved.

**Status of the tracked items:** unchanged. `F1` `DEFERRED`, `DM-BL-008c` `DEFERRED`,
`DM-BL-008b` `PENDING-EVIDENCE`. No evidence flag on this record was cleared by the target
attribution.

## Related records

- `verification/locales/README.md` — index and status legend
- `verification/locales/locale_cases/fr_FR.json` — case boundaries, target attribution,
  and the tracking rules this record obeys (no run output)
- `verification/locales/REPORT-it_IT-2026-09-28.md` — Italian pass, same target class,
  and the origin of the `192.168.20.23` address
- `verification/locales/deferrals.md` — `F1`, `DM-BL-008b`, `DM-BL-008c` state; this
  French pass is the run from which `F1` and `DM-BL-008c` were deferred
- `PRODUCT_BACKLOG.md`, `PROJECT_STATE.md` — `DM-BL-008b` currently `PENDING-EVIDENCE`
