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

**Resolved (28 September 2026):** `release/v2.10-notes.md` was reviewed against the nine
corrected views (commit `e6443bc`, pushed to `origin/v2.10-development`, CI run `36355695028`
PASS) and now records the JavaScript-encoding correction, the eleven installed catalogues, the
validated nine-language acceptance (10 pages, 448 message ids per language) and the `nl_NL`
GUI-selectability limitation. The file is not one of the 37 guarded files in
`release/v2.10-runtime.manifest`, so the review changed no manifest hash, and
`tests/test_release_manifest.py`, `sh -n install-unattended.sh` and `git diff --check` stayed
PASS.

**Resolved (28 September 2026): French verified as rendered page text, not as a dialog.** An
operator-run remote Selenium script asserted the rendered text stream of the target UI at
`https://192.168.20.23` and found the core French UI strings, including `Résumé des modifications`
(`Change Summary`) and `Surveillance des appareils` (`Device Monitor`). Both match the deployed
`/usr/local/share/locale/fr_FR/LC_MESSAGES/OPNsense.mo` and
`src/opnsense/mvc/app/languages/fr_FR_devicemonitor.po`, so the French translation stream is
verified on the target UI. Evidence status: the Selenium script and its output were not archived
in this repository or on the testbed, so the observation is recorded as operator-reported and is
not reproducible from the checkout.

**Re-scoped (28 September 2026):** the earlier "one browser dialog in French and one in Italian"
wording is withdrawn. There is no dialog to confirm on OPNsense 26.7.4 (see F1), so this item is
verified against observable rendered text instead of a dialog popup. The three French strings that
a `lang._()` regression would have escaped (`Voir l'appareil`, `Voir l'infrastructure`,
`Aucun changement Device Monitor significatif n'a été enregistré pendant cette période.`) all reach
the DOM through `.text()`, where no entity leak is possible.

**F1 (open, new):** the Change Summary toast path is inert. `showToast()` in `changesummary.volt`
guards on `$.fn.notify` and `window.bootbox`, and neither exists on this build: the core
`templateJSIncludes()` list loads no bootbox and no notify plugin, no such file exists under
`/usr/local/opnsense/www` or `/usr/local/www`, `/ui/js/theme.js` is an empty placeholder, and the
plugin calls no dialog API at all. Clicking `Mark reviewed now` therefore renders nothing. The core
dialog API on 26.7.4 is `BootstrapDialog`, wrapped by `stdDialogInform()` in `opnsense_ui.js`.

**Still open (Italian):** the Italian text stream has not been verified. The same assertion must be
run for `it_IT`, whose expected strings are `Riepilogo modifiche` (`Change Summary`) and
`Monitoraggio dispositivi` (`Device Monitor`).

**Resolved (27 September 2026):** the installer pin that `0708239` left stale is corrected by
commit `3eeb78b`, which pins the current `release/v2.10-runtime.manifest` SHA256
`11472b464798344b93ac4be3dc220632cbec62e5a07cdba311f6f77f7161ed76` in
`install-unattended.sh` line 28; `tests/test_release_manifest.py` passes
(`V210_RELEASE_MANIFEST=PASS`) and
`install-unattended.sh --host OPNsense.internal --check` reports
`CHECK_OK version=2.10 predecessor=2.10 files=48 daemon_running=1`.

**Deferred:** the Italian text-stream confirmation and the F1 dialog decision, both of which need a
browser session or a source change and stay outside the local checkout work.

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

**Options (to be decided when the item is taken up):** merge the locale-installer branch after
review, or implement the equivalent merge in the v2.10 installer. Either way the merge must
tolerate a missing core catalogue (`nl_NL`), which the branch currently treats as an abort.

**Validation when implemented:** installer `--check` and a testbed install followed
by `python3 tests/test_language_acceptance.py` (runtime engine) for the nine
languages, plus a negative check on a system without the merge, where the pages
must fall back to English. `tests/test_locale_merge.py` covers the merge mechanics
if the branch is merged. `docs/USER_MANUAL.md` must state which languages are
actually selectable once the delivered set is final.

**Decided (28 September 2026) — deferred; documentation only.** DM-BL-008c stays open and no
installer, manifest, release-note or Makefile change is made now. Reason: the candidate branch is a
v2.9-era change and cannot be adopted unchanged. Its `install-unattended.sh` check still prints
`version=2.9` and stages `install-v29.XXXXXX` backups, and its `--languages` default of `none` would
ship no catalogues at all, taking the default target count from the recorded `files=48` to `37` and
invalidating the "eleven installed catalogues" statements in the release notes and the review
record. Its reusable parts carry no v2.9 coupling and are the starting point when the item is taken
up: `release/merge-opnsense-catalog.sh` (core-first `msgcat --use-first`, then asserts that no core
translation changed and that every plugin string is present), `tests/test_locale_merge.py` (pure
gettext fixtures in a temporary directory) and the two CI steps. The open sub-decision is the
default of `--languages`: `all` to preserve today's 48-file state, `none` for the branch's opt-in
default, or no flag at all. Until it ships, the nine translations remain inert on a firewall
installed from the release asset alone, and the `nl_NL` missing-core-catalogue case must be handled
rather than aborted.

## O3/O4 sidecar translation — 28 September 2026

Recorded by the O4 view-migration workstream (branch `feature/o4-sidecar-views-20260928`, branch
commit `43891db` plus the installer-layout change and this record). Appended, not merged into the
sections above.

### `O3` — installer catalogue layout: **`RESOLVED`**

- The eleven catalogues moved from the flat `src/opnsense/mvc/app/languages/<locale>_devicemonitor.po`
  layout, which `bindtextdomain()` cannot resolve, to
  `src/opnsense/mvc/app/languages/<locale>/LC_MESSAGES/devicemonitor.po`.
- `install-unattended.sh` compiles each catalogue into
  `/usr/local/opnsense/mvc/app/languages/<locale>/LC_MESSAGES/devicemonitor.mo`, the path
  `devicemonitor_locale.inc` binds; `uninstall.sh` removes the nested catalogue and the legacy flat
  pair of files from v2.9/v2.10 release-asset installs; the CI catalogue step mirrors the layout.
- The `en_US` and `cs_CZ` manifest rows were repathed to the nested sources. The manifest stays at 38
  rows; its new SHA256 is
  `ee688415eb586abec361b84cd54ac75d5fe45a4fddb136f89bfcda610894ce69`, pinned in
  `install-unattended.sh`.
- Standing consequence: on a firewall installed from the release asset the sidecar catalogue now
  resolves, so `devicemonitor_t()` is behaviour-changing rather than a pass-through to the core
  domain. `DM-BL-008c`'s whole-payload condition remains unaffected: the nine languages become
  readable through the plugin's own domain instead of a merged core catalogue, so no core language
  file is read or written.

### `O4` — route the GUI through the sidecar text domain: **`CODE-COMPLETE`** (not closed)

- All 372 HTML-context `lang._()` call sites in the nine views call `devicemonitor_t()`; the 241
  `lang.query()` call sites inside inline script bodies are unchanged, because those need the raw
  value. Every call site's argument text is byte-identical, so no message id changed.
- `src/etc/inc/devicemonitor_locale.inc` is now a guarded payload row: `IndexController::initialize()`
  requires it and binds the domain before a view renders, with a sidecar -> core `OPNsense` -> msgid
  fallback and the `sidecar_translation_enabled` toggle (default `"1"`, Settings -> About checkbox).
- Remaining dependency before this item can close: **human browser confirmation** that the rendered
  pages are correct with the sidecar toggle both on and off. It cannot be produced from the
  development checkout (no Selenium/WebDriver there and the change is not deployed).
- New gate: `tests/test_sidecar_catalogue.py` with `tests/sidecar_translate_probe.php` and a CI step.
  It proves sidecar precedence, the core fallback, the toggle, the msgid fallback and HTML escaping
  without a browser or a network.

### Webhook guard bypass: **`CLOSED`** (fixed, commit `43891db`)

- `ConfigController::sendWebhookAction()` passed `''` when the caller omitted `webhook_url`; the
  handler only short-circuits on `null`, so the "Webhook disabled" guard was skipped and delivery was
  attempted to an empty URL. Absent, null, empty and whitespace-only values are now detected in the
  controller, normalised again inside `NotificationHandler::sendWebhook()`, and a whitespace-only
  configured URL is treated as absent. `testWebhookAction()` rejects an empty URL instead of
  attempting delivery.
- The observation first recorded in `PROJECT_STATE.md` on 27 September 2026 under *Limits* is
  therefore closed. The instruction's `isset($backendConfig->webhook_url)` shape does not exist in
  this checkout; the equivalent strict check is implemented against the request parameter and the
  `DeviceMonitor::getConfig()` array, and the response keeps the established `result` key.


### Deployment — 28 September 2026

The v2.10 payload was deployed to `OPNsense.internal` with the guarded unattended installer
(`INSTALL_OK version=2.10 files=49`, backup `/var/backups/devicemonitor/install-v210.UmZ7ze`,
configd and the Device Monitor daemon restarted). That clears the deployment lag recorded above
for `O3`: the nested catalogues, the committed sidecar binder and the migrated views are now the
installed ones, all 38 manifest targets verify on disk, and the eleven catalogues match the
source. Monitoring remains disabled, so no scan ran. `O4` stays open for human browser
confirmation only.
