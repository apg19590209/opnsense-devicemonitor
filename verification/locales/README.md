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
| `REPORT-fr_FR-2026-09-28.md` | `fr_FR` | OPNsense UI (address not stated in the supplied log) | `OPERATOR-REPORTED` |
| `REPORT-it_IT-2026-09-28.md` | `it_IT` | `192.168.20.23` (OPNsense UI) | `OPERATOR-REPORTED` |

See `deferrals.md` for F1, `DM-BL-008b`, `DM-BL-008c`.

## Harness

`verify_locale_stream.py` (proposed, **not yet committed**). Protocol: standard library
plus `selenium` only; case data in `locale_cases/<locale>.json`.

Checks emitted: `stream_progressed`, `stream_lossless`, `no_replacement_char`,
`no_mojibake`, `no_control_chars`, `localized_markers_present`,
`no_untranslated_fallback`, `document_lang`, `diacritics_roundtrip`.

```sh
python3 verify_locale_stream.py --case locale_cases/it_IT.json --check-env
python3 verify_locale_stream.py --case locale_cases/it_IT.json --dry-run
python3 verify_locale_stream.py --case locale_cases/it_IT.json --headless \
  --out-dir out/it_IT --write-markdown --save-page-source
```

Exit codes: `0` all checks passed, `1` at least one `FAIL`/`ERROR`, `2` configuration or
environment error.

### Host requirements

The recording host currently meets none of these: Selenium is not importable, `pip` is
absent, and no browser or WebDriver binary is installed. On FreeBSD:

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
