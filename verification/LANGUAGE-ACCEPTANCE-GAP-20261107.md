# Language acceptance `gaps=1` — `nl_NL` selector gap

**Status: explained; no product change made. Runtime rendering passes for all nine bundled
languages. The single gap is the core-owned GUI selector omission documented and closed as
DM-BL-008a.**

## Observed result

The production-engine run on the installed 2.14.0 tree reported:

```text
LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0
```

The underlying report is
`/root/dm-validation-2140/language-runtime-2.14.0-20261107.md`: 10 pages and 490 keys per language,
with `nl_NL` rendering all 10 pages through the production Phalcon/Volt/ViewTranslator path.

## What `gaps=1` means

`tests/test_language_acceptance.py` counts two non-fatal conditions as gaps: a language absent from
`get_locale_list()` and a missing host locale. The run's only gap is:

```text
WARNING: nl_NL: absent from System > Settings > General > Language
```

The OPNsense core function `get_locale_list()` is a static list and does not contain `nl_NL`;
OPNsense also ships no Dutch core catalogue. The Device Monitor `nl_NL` catalogue is a plugin-only
sidecar. The installed core language list was readable and contained 19 languages, not including
Dutch. This is the same limitation recorded and closed as **DM-BL-008a** on 28 September 2026.

## User-visible effect

- An administrator cannot select Dutch from the normal OPNsense language selector.
- The Device Monitor Dutch catalogue is installed and renders correctly when the locale is selected
  through the plugin path, but normal GUI selection cannot reach it.
- This is a selector/reachability limitation, not a missing translation, incomplete catalogue or
  runtime rendering failure.

## Acceptance treatment

- The native Phalcon/Volt/ViewTranslator acceptance criterion is **satisfied**: every one of the
  nine bundled languages renders 10/10 pages with 490/490 keys and zero failures.
- The `--strict` selector criterion is **not satisfied** for `nl_NL`; that is why `gaps=1` is
  reported rather than `gaps=0`.
- This is not a demonstrated defect in the Device Monitor repository. The selector is owned by
  OPNsense core and cannot be changed from the plugin without a non-upstream Device Monitor-only
  language picker, which DM-BL-008a explicitly rejected. The gap remains a documented upstream
  limitation and is not treated as a native-runtime failure.

No source, catalogue, installer, manifest, release pin or archive change is required for this
explanation. No browser layout, JavaScript execution or human translation-quality claim is made.
