# Device Monitor — Product Backlog

This file records explicitly discussed Device Monitor work that has been deferred
or approved for future development.

## Backlog rules

- Add only work explicitly discussed and intentionally deferred or approved.
- Do not invent speculative features merely to populate the backlog.
- Do not duplicate the active task from `PROJECT_STATE.md`.
- Completed work is removed from the open backlog once authoritative project state
  has been updated.
- Architectural constraints remain in `DECISIONS.md`.
- Environment and component facts remain in `SYSTEM_MAP.md`.

## Open backlog

### DM-BL-008a — Dutch (nl_NL) is not selectable in the GUI language list

**Description:** Make the Dutch Device Monitor catalogue usable through the normal
OPNsense language setting, or withdraw Dutch from the delivered language set until
that is possible. The nine DM-BL-008 languages are selected in
System → Settings → General → Language, which is populated by `get_locale_list()`
in `/usr/local/etc/inc/system.inc`; that function is a static list that does not
include `nl_NL`, and OPNsense ships no Dutch core catalogue.

**Benefit:** The Device Monitor pages already render in Dutch (verified
27 September 2026), but an administrator cannot choose Dutch, so the work is
currently unreachable and the DM-BL-008 acceptance step for Dutch cannot be
performed as recorded.

**Evidence (27 September 2026, testbed `192.168.20.23`, OPNsense 26.7.4):**
`get_locale_list()` returns 19 languages (`en_US, zh_CN, zh_TW, cs_CZ, fr_FR,
de_DE, el_GR, it_IT, ja_JP, ko_KR, no_NO, fa_IR, pl_PL, pt_BR, pt_PT, ru_RU,
es_ES, tr_TR, uk_UA`; `vi_VN` only in development builds) — no Dutch, and the list
is not derived from the installed catalogues. A stock OPNsense install has no
`/usr/local/share/locale/nl_NL/LC_MESSAGES/OPNsense.mo`; the deployed file is the
Device Monitor catalogue alone and is byte identical to
`/usr/local/opnsense/mvc/app/languages/nl_NL_devicemonitor.mo` (SHA256
`8bb2a6c7947ecef25f11dbc5648673c050a08f1726a53008264ab276835e1579`). The
`nl_NL.UTF-8` locale exists in FreeBSD base, and
`tests/test_language_acceptance.py` renders all 10 pages in Dutch without
fallbacks.

**Options (decision required):**
1. Core support: request that OPNsense add Dutch to `get_locale_list()` and
   publish a Dutch core catalogue. Outside this repository's control.
2. Withdraw Dutch until core support exists: remove `nl_NL_devicemonitor.po/.mo`
   from the payload, the nine-language acceptance list and the release notes, and
   record Dutch as unsupported.
3. Plugin-side language selection for Device Monitor only. Not preferred: it would
   bypass the OPNsense language setting and duplicate core behaviour.

**Validation when implemented:** `python3 tests/test_language_acceptance.py
--strict` fails while `nl_NL` is absent from `get_locale_list()`, so it is the
regression gate for this item, and passes once Dutch is selectable. Confirm by
hand that Dutch appears in System → Settings → General → Language and that the
pages render Dutch after selection. For option 2, run the acceptance with
`--languages` reduced to the eight remaining languages.

**Deferred:** the GUI language list is core-owned; the correct option depends on
whether OPNsense will support Dutch, which is outside this project.

### DM-BL-008b — JavaScript strings receive HTML entities

**Description:** Stop HTML-escaped text from reaching JavaScript string contexts.
`OPNsense\Base\ViewTranslator::_()` HTML-escapes every translation
(`view_html_safe` → `htmlspecialchars(..., ENT_QUOTES | ENT_HTML401)`, newlines as
`&#10;`), which is correct where the value is HTML. Since `1e98336` the views apply
`json_encode(15)` on top of that escaped value inside inline JavaScript, so an
apostrophe in a translation arrives as `\u0026#039;` and a JavaScript string such
as `Supprimer l&#039;appareil`.

**Benefit:** Removes visibly broken text from the French, Italian and Dutch UI, in
browser dialogs, tooltips and any DOM text assigned with `textContent`. French is
the most affected language.

**Evidence (27 September 2026):** rendering `devices.volt` for `fr_FR` produces
`confirm_delete: "Supprimer l\u0026#039;appareil"`, consumed by
`confirm(translations.confirm_delete + ' ' + mac + '?')` (`devices.volt` line 941).
Affected `lang._(...)|json_encode(15)` call sites: `fr_FR` 72, `it_IT` 7, `nl_NL` 1,
all six other languages 0, out of 241 call sites in the nine views (273 across the
ten pages, because port discovery reuses the infrastructure-services view). Every
affected value contains an apostrophe; no JavaScript-context translation in any
language currently contains `&`, `<`, `>` or `"`. The same values also occur in HTML
context (`fr_FR` 95, `it_IT` 14, `nl_NL` 2), where the escaping is correct and must
be preserved.

**Validated constraints (same day, with the installed Phalcon Volt compiler):**
- `{{ gettext('X') }}` cannot be used: an unregistered function compiles to
  `$this->callMacro('gettext', ['X'])` and fails with `Macro 'gettext' does not
  exist`. Core registers only `theme_file_or_default`, `file_exists` and
  `cache_safe`, plus the `safe` filter, from the private `$volt_functions` array in
  `OPNsense\Base\ControllerBase`.
- `|raw` and `|html_entity_decode` are not Volt filters (`UnknownVoltFilter`).
- `|safe` is `view_html_safe`, which escapes again.
- The Device Monitor views use none of the three core Volt functions (0 occurrences
  in all nine views).

**Resolution adopted (27 September 2026): the raw translator through the inherited
`query()` method.** `ViewTranslator` extends `Phalcon\Translate\Adapter\Gettext`,
which already provides `query($messageId)` returning the untransformed catalogue
string, so the raw value is reachable without a core change and without a new
plugin file. Every call site whose value is JSON-encoded for a script context now
reads `{{ lang.query('...')|json_encode(15) }}` — 241 call sites in the nine views
— and the HTML-context `lang._(...)` call sites were left unchanged, because that
escaping is required there. Measured on the testbed with the installed translator:
`_('View Device')` returns `Voir l&#039;appareil` while `query('View Device')`
returns `Voir l'appareil`, which `json_encode(15)` renders as
`"Voir l\u0027appareil"`.

**Alternatives rejected:** the validated constraints above rule out a Volt function
or filter; a plugin-registered Volt function would duplicate core engine
configuration (cache `path`/`separator`); replacing the affected apostrophes with
U+2019 is data only and does not cover `&`, `<`, `>` or `"`; decoding entities in
each view risks decoding literal text that is not a translation; and a `rawlang`
view variable would need a new PHP file plus release-manifest, installer-count and
`tests/test_release_manifest.py` changes for what the inherited method already
provides.

**Validation (27 September 2026):** the nine views were deployed to the testbed
(`/usr/local/opnsense/mvc/app/views/OPNsense/DeviceMonitor`, 21:17:12 AEST, backup
`/root/devicemonitor_backup/dm-language-js-query-views-20260927-211712`, with a
rollback script) and all nine files match the source by SHA256.
`python3 tests/test_language_acceptance.py --engine runtime` then passes for all
nine languages over 10 pages and 448 strings with zero failures and, unlike the
20:32 run, no JavaScript-entity finding at all: that check is now scoped to script
bodies and measured on the values that actually reach them, so it fails only for
the languages whose values are escaped (reverting `changesummary.volt` to
`lang._()` fails `fr_FR` alone, with 3 such strings).
`python3 tests/test_translated_javascript.py` passes for the eleven catalogues, the
hostile-string control and the isolated translated-string probe, and
`node tests/test_change_summary_ui.js` passes.

**Still open:** `release/v2.10-runtime.manifest` was regenerated for the corrected views by
`0708239` and `tests/test_release_manifest.py` passes against it
(`V210_RELEASE_MANIFEST=PASS`, re-verified 27 September 2026). That commit did not update
the manifest SHA256 pinned in `install-unattended.sh` line 28, which still holds the
pre-refresh hash (`29ac9a16…`; the manifest is now `11472b46…`), so the guarded installer
aborts with `ABORT: release manifest mismatch` and the pin needs its own change.
`release/v2.10-notes.md` has not been reviewed against the corrected views. One
browser dialog in French and one in Italian still need visual confirmation, because
the defect is only visible in the browser.

**Deferred:** the installer-pin correction, the release-notes review and the browser
confirmation, all outside the testbed view deployment performed here.

### DM-BL-008c — Installed plugin catalogues are invisible to the GUI without the shared merge

**Description:** Deliver the Device Monitor translations into the domain the GUI
actually reads. The installer compiles each `<locale>_devicemonitor.po` into
`/usr/local/opnsense/mvc/app/languages/<locale>_devicemonitor.mo`, but no installed
OPNsense code reads that directory: the MVC view translator is configured by
`OPNsense\Base\ControllerRoot::setLang()` with `directory = /usr/local/share/locale`
and `defaultDomain = OPNsense`, so a language renders only when
`/usr/local/share/locale/<locale>/LC_MESSAGES/OPNsense.mo` contains the Device
Monitor strings.

**Benefit:** Without this, the nine languages (and Czech) are installed but inert
on any firewall that used the released installer alone, and the DM-BL-008 language
work would look broken in the field.

**Evidence (27 September 2026):** the released installer
(`install-unattended.sh`, lines 94–98) installs the eleven `.mo` files into
`/usr/local/opnsense/mvc/app/languages/`, and searching `/usr/local/etc`,
`/usr/local/opnsense` and `/usr/local/www` for `mvc/app/languages` finds no reader.
The testbed renders the nine languages because the shared catalogues were merged
out of band on 26 September 2026 (pre-merge originals under
`/root/devicemonitor_backup/pre-merge-opnsense-mo-20260926-131554`); for `nl_NL`,
where no core catalogue exists, the shared file is the plugin catalogue alone. A
candidate fix exists on the unmerged but pushed branch
`feature/optional-locale-installer-20260927` (commit `c1fa466`:
`release/merge-opnsense-catalog.sh`, `tests/test_locale_merge.py`,
`install-unattended.sh --languages`, README/Makefile changes).

**Options (decision required):** merge the locale-installer branch after review, or
implement the equivalent merge in the v2.10 installer. Either way the merge must
tolerate a missing core catalogue (`nl_NL`), which the branch currently treats as
an abort.

**Validation when implemented:** installer `--check` and a testbed install followed
by `python3 tests/test_language_acceptance.py` (runtime engine) for the nine
languages, plus a negative check on a system without the merge, where the pages
must fall back to English. `tests/test_locale_merge.py` covers the merge mechanics
if the branch is merged. `docs/USER_MANUAL.md` must state which languages are
actually selectable once the delivered set is final.

**Deferred:** the merge was deliberately made opt-in, and adopting it changes the
installer, manifest and release notes, so it needs its own change and decision.
