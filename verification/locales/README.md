# Locale text-stream verification

Records for localized text-stream verification runs, and the harness used to produce
them.

## Status legend

| Status | Meaning |
| --- | --- |
| `PASS` / `FAIL` / `WARN` / `SKIP` | Harness-reported check outcome. |
| `OPERATOR-REPORTED` | Asserted by an operator, no artifact attached. Unverified. |
| `PENDING-EVIDENCE` | Claimed done, no artifact to close it. Not resolved. |
| `DEFERRED` | Consciously not actioned yet. |

## Records

| Record | Locale | Target | Status |
| --- | --- | --- | --- |
| `REPORT-fr_FR-2026-09-28.md` | `fr_FR` | `192.168.20.23` (OPNsense UI — operator-attested, not in the supplied log; see the report's *Target attribution*) | `OPERATOR-REPORTED` |
| `REPORT-it_IT-2026-09-28.md` | `it_IT` | `192.168.20.23` (OPNsense UI) | `OPERATOR-REPORTED` |

See `deferrals.md` for F1, `DM-BL-008b`, `DM-BL-008c`.

## Harness

`verify_locale_stream.py` — **written 2026-09-29, committed, and not yet run against any
target.** Protocol: standard library plus `selenium` only; case data in
`locale_cases/<locale>.json`; offline self-test in `tests/test_verify_locale_stream.py`
(`python3 tests/test_verify_locale_stream.py` — no selenium, no browser, no network).

Case data exists for `fr_FR` (2026-09-28) and `it_IT` (2026-09-29). Both are marked
`draft-unratified` and every field a run would fill is `null`. A non-`null` value in either
is never a PASS. Keys are limited to what this file and the harness name explicitly, plus
one optional key: `untranslated_probe`, a list of English label strings that must not
render. While that list is empty — the current state of both files —
`no_untranslated_fallback` is a `SKIP`, never a `PASS`.

Checks emitted: `stream_progressed`, `stream_lossless`, `no_replacement_char`,
`no_mojibake`, `no_control_chars`, `localized_markers_present`,
`no_untranslated_fallback`, `document_lang`, `diacritics_roundtrip`.

### What each check does and does not cover

| Check | PASS requires | A PASS does not cover |
| --- | --- | --- |
| `stream_progressed` | at least two samples, and the rendered text grew; a shrink is `FAIL`, no growth is `WARN` | that a single-shot render is wrong |
| `stream_lossless` | captured `fetch`/`XHR` bodies reassemble into the rendered text (`captured-response-assembly`); with nothing captured, every earlier sample must be a prefix of the final text (`dom-prefix`) | transport bytes, compression, HTTP framing |
| `no_replacement_char` | no `U+FFFD` in the rendered text | text the browser never received |
| `no_mojibake` | none of a fixed cp1252-decoded-as-utf-8 sequence list appears | mojibake shapes outside that list |
| `no_control_chars` | no control character other than tab, newline or carriage return | normalisation the browser already performed |
| `localized_markers_present` | every marker text from the case file appears in the rendered text | translation quality. Marker *text* is read from the case file; its `reported_status` is an attestation and is never consumed |
| `no_untranslated_fallback` | no `untranslated_probe` string appears | an empty probe list yields `SKIP`; an English fallback absent from the list is not detected |
| `document_lang` | `document.documentElement.lang` equals `expected_document_lang` (`_`/`-` and case insensitive) | text direction, spelling, or the attribute as served |
| `diacritics_roundtrip` | the rendered text round trips through UTF-8, the declared charset is utf-8, and marker diacritics survive; `WARN` if diacritics are missing or none were exercised | that a `WARN` is a pass — it is not |

A `SKIP` means the check was not exercised, and is never a pass. A run in which no check
reaches `PASS` reports `NO-RESULT` and exits `2`.

The harness reads no OPNsense configuration, performs no teardown, and does not compare a
page against another installed locale's catalogue. Those stay operator duties, and the
acceptance checklist in `out/README.md` still governs closure.

```sh
python3 verify_locale_stream.py --case locale_cases/it_IT.json --check-env
python3 verify_locale_stream.py --case locale_cases/it_IT.json --dry-run
python3 verify_locale_stream.py --case locale_cases/it_IT.json --headless \
  --out-dir out/it_IT --write-markdown --save-page-source
```

Exit codes: `0` all checks passed, `1` at least one `FAIL`/`ERROR`, `2` configuration or
environment error — which includes `NO-RESULT`, a run that exercised nothing. `--check-env`
and `--dry-run` write nothing and touch no target. A run writes only under `--out-dir`, and
refuses to start when `target.base_url` or `target.route` is `null` in the case file.

### Host requirements

The recording host currently meets none of these. `--check-env` reports exactly this and
exits `2`. Selenium is not importable, `pip` is absent, and no browser or WebDriver binary
is installed. On FreeBSD:

```sh
pkg install chromium firefox
python3 -m ensurepip && python3 -m pip install selenium
# or: pkg install py313-selenium
```

Selenium Manager is unlikely to resolve a driver for FreeBSD; pass `--driver-path`
pointing at a locally installed `chromedriver` or `geckodriver`.

## Note on scope

The `fr_FR` and `it_IT` records both target an OPNsense firewall UI, which lives outside
this repository. Verification that touches a remote device must record the device build
and its before/after state, because restored locale settings are infrastructure state
rather than documentation.
