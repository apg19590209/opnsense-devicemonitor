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

### DM-BL-008a — Dutch (nl_NL) is not selectable in the GUI language list: **`CLOSED`**

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

**Closed (28 September 2026) — dropped: upstream limitation.** Closed for the same reason the
parallel locale-verification track recorded its `O2` decision: the GUI language list is core-owned
and Dutch selectability cannot be delivered from this repository. Evidence (live testbed, 28
September 2026): `/usr/local/etc/inc/system.inc` is SHA256
`3347f8761fd70498d0a4cb32b7b06b4eeda6647a076853eaf5a9ede0d972041f`, byte identical to upstream
`opnsense/core` master and `stable/26.7`, and contains no `nl_NL` entry — nothing is commented out
— so there is no menu entry to restore; `/usr/local/share/locale/nl_NL` does not exist, so there is
no shipped Dutch core catalogue to attach one to. Option 1 (core support) remains outside this
repository's control. Option 3 (plugin-side language selection) was considered and not adopted: a
Device Monitor-only language picker would bypass the OPNsense language setting and duplicate core
behaviour. The binder that O3/O4 shipped is a text-*domain* binder, not a selector —
`src/etc/inc/devicemonitor_locale.inc` binds `devicemonitor` and resolves the active locale through
the core setting, so it renders Dutch once Dutch can be selected and cannot make it selectable.
Scope boundary: what ships is the rendering path — the `nl_NL` catalogue stays in the
eleven-catalogue payload and all 372 HTML-context view call sites route through
`devicemonitor_t()` — not the selector. Re-open only if upstream adds `nl_NL` to
`get_locale_list()` and publishes a Dutch core catalogue, or if a Dutch GUI is commissioned as a
non-upstream change; `python3 tests/test_language_acceptance.py --strict` is the gate for that
case. This closure changes no installer, manifest, catalogue, release-note or Makefile content.

### DM-BL-008b — JavaScript strings receive HTML entities: **`CLOSED`**

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

**`F1` — `CLOSED` / `RESOLVED` (29 September 2026): the Change Summary confirmation banner is
implemented and verified live.** The `$.fn.notify` shape cannot be the remedy on this build: the core
page loads no notify plugin and no `bootbox` (neither asset exists under `/usr/local/opnsense/www` or
`/usr/local/www`, and `/ui/js/theme.js` is an empty placeholder), so the 28 September wording that
proposed `$.fn.notify(message, { type: 'success' })` is withdrawn for the same reason the original
guard chain was inert. The committed implementation is `changesummary.volt:581-593` — the
self-contained jQuery banner already proven in `devices.volt:435-444`, with two deliberate
differences: the icon and the message are appended as DOM nodes (`$('<i>').addClass('fa ' + ic)` plus
`document.createTextNode(' ' + message)`) instead of being interpolated into `.html('<i …></i> ' +
msg)`, so a translation is never parsed as markup; and the auto-dismiss timeout is `4000` ms rather
than `3000` ms (`fadeIn(300)` → `setTimeout(4000)` → `fadeOut(300, remove)`). The banner keeps the
`devices.volt` geometry and palette (`position: fixed`, `top/right: 20px`, `z-index: 9999`,
`min-width: 280px`, success background `#4CAF50`, `fa-check-circle` icon).

Operator live verification (29 September 2026) on
`https://192.168.20.23/ui/devicemonitor/index/changesummary`: clicking **Mark reviewed now** renders
the success banner with a clean, unclipped icon layout, the message appended as a text node (no
entity or markup leakage), and the banner auto-dismisses after exactly four seconds; no new entry
appeared in the PHP error log for the request. Evidence status: operator attestation recorded in this
session — no screenshot, DOM capture, browser version or log transcript was attached to this
checkout, so the entry states the operator's reported result, exactly as the `O4` sign-off, the 28
September French Selenium note and the `DM-BL-008b` dialog closure do. The view digest moved from
`0503e488b0caff4dbe7727b9820ca1d58bc63f92850b748c403214c6bc94f527` to
`b7aa5631344ea410326d18f6fc07a52e0a43ddf0a1e160c6c91f2f5326003d0c`, so
`release/v2.10-runtime.manifest` row 17 and the `install-unattended.sh` line 28 manifest pin (now
`fc2669413c86c70b6bf4c72f0d1a014361cbe179e64ae50a7147d3d690b50ac2`) were refreshed in the same change
set; `python3 tests/test_release_manifest.py` passes (`V210_RELEASE_MANIFEST=PASS`, 38 rows).

**Resolved (29 September 2026): live confirmation dialog verified in French and Italian —
item `CLOSED`.** The row-1 confirmation dialog was checked by the operator on the live interface:
`https://192.168.20.23/ui/devicemonitor/index/devices` (menu route
`/ui/devicemonitor/index/devices`, `Menu.xml` line 4; per-row Delete, `devices.volt:895` button →
handler `:939` → `confirm(translations.confirm_delete + ' ' + mac + '?')` at `:941`, payload
`lang.query('Delete device')|json_encode(15)` at `:419`). French rendered exactly
`Supprimer l'appareil <MAC>?` and Italian exactly `Elimina dispositivo <MAC>?` — no HTML-entity
leakage (`&#039;`, `&amp;`, `\u0026#039;` all absent) and no layout or button-container clipping.
Catalogue cross-check for the same message id: the source `.po` (`fr_FR`/`it_IT` lines 116-117), the
deployed plugin catalogue
(`/usr/local/opnsense/mvc/app/languages/<lang>/LC_MESSAGES/devicemonitor.mo`) and the shared core
`OPNsense.mo` all agree, and the French apostrophe is the ASCII character U+0027 (`…6c2761…`). So the
Italian text stream is verified as well, which closes the item left open by the 28 September entry
above; the Italian core page text expected by that earlier note remains
`Riepilogo modifiche` (`Change Summary`) and `Monitoraggio dispositivi` (`Device Monitor`).

**Runtime-engine gate also satisfied (29 September 2026):** the harness previously could not certify
any language on the production Volt path, because its own compiler was built without the sidecar
binding and every page aborted with `Using $this when not in object context` (`failures=10`). Commit
`7b4bb46` — pushed to `origin/v2.10-development`, CI run `36516155279` PASS — registers
`devicemonitor_t` on that compiler (`tests/render_device_monitor_page.php:105`, mirroring
`IndexController.php:44`). `python3 tests/test_language_acceptance.py --engine runtime` then reports
`it_IT PASS pages=10 keys=451 translated=442 identical-to-english=9 selectable=True locale=True
identity=it_IT engine=runtime`, `failures=0`, and `PASS languages=8 gaps=0 failures=0` for the eight
languages whose shared catalogues exist; `--engine interpolate` stays `PASS languages=9 gaps=1
failures=0`. No installer, manifest, catalogue or release-note content changed for this closure.

**CI gate expanded to the guarded runtime matrix (29 September 2026):** the interpolate-only CI statement
above is superseded. The `Validate language acceptance (DM-BL-008)` step (`.github/workflows/ci.yml:74-105`)
now runs the interpolate baseline and then the production-parity runtime matrix: `--engine runtime` is
invoked with `--languages <languages whose shared OPNsense.mo the runner carries>`, each host-blocked
language is printed as `SKIPPED <lang>: shared OPNsense.mo catalogue absent on this runner (host-blocked
language)`, and the matrix exits cleanly with a stated reason when the runner has no Phalcon Volt compiler
or no `OPNsense\Base\ViewTranslator`. `nl_NL` (`DM-BL-008a`) therefore no longer removes the runtime path
from continuous integration; it is reported as a skip. This is a workflow-and-record change only: no
installer, manifest, catalogue, view, Makefile or release-note content changed, so no guarded digest and no
installer pin moved.

**Evidence status:** the dialog observation is an operator attestation recorded in this session;
screenshots, DOM captures or browser/version details were not attached to this checkout, so the entry
states the operator's reported result rather than an artifact-backed verification, matching the `O4`
sign-off and the 28 September French Selenium note. `F1` (the inert Change Summary toast) was a
separate open decision at the time of this closure and was not affected by it; it was closed the same
day — see the `F1` entry above and the `F1` closure section in `PROJECT_STATE.md`. `DM-BL-008c` was resolved on
29 September 2026 (see its entry below).

**Resolved (27 September 2026):** the installer pin that `0708239` left stale is corrected by
commit `3eeb78b`, which pins the current `release/v2.10-runtime.manifest` SHA256
`11472b464798344b93ac4be3dc220632cbec62e5a07cdba311f6f77f7161ed76` in
`install-unattended.sh` line 28; `tests/test_release_manifest.py` passes
(`V210_RELEASE_MANIFEST=PASS`) and
`install-unattended.sh --host OPNsense.internal --check` reports
`CHECK_OK version=2.10 predecessor=2.10 files=48 daemon_running=1`.

**Re-pinned (29 September 2026):** the manifest was regenerated again for the O4 view work and the
29 September GUI repair, so the pin recorded in the paragraph above is historical. The current values
are `release/v2.10-runtime.manifest` SHA256
`ced20c442a28acb544b9b683549cb0f2553b0335ba44dd78682d3b4013b3cf4e`, with the three refreshed rows
(`devicemonitor_locale.inc`, `IndexController.php`, `NotificationHandler.php`) and the matching pin on
`install-unattended.sh` line 28 committed as `8faf09d`. `tests/test_release_manifest.py` passes
(`V210_RELEASE_MANIFEST=PASS`) and the installer's manifest gates (digest, 38 rows, source version
2.10) pass in isolation.

**Deferred (superseded 29 September 2026):** the Italian text-stream confirmation and the F1 dialog
decision, both of which needed a browser session or a source change and stayed outside the local
checkout work. Both were completed on 29 September 2026: the Italian confirmation as part of the
`DM-BL-008b` closure above, and `F1` as the Change Summary banner change recorded in the `F1` entry
above. The last item in this group, `DM-BL-008c`, was closed on 29 September 2026 (see its entry below).

### DM-BL-008c — Installed plugin catalogues are invisible to the GUI without the shared merge: **`CLOSED`**

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
installer, manifest, release-note or Makefile change is made now (superseded on 29 September 2026 — see the
resolution paragraph at the end of this entry). Reason: the candidate branch is a
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

**Resolved (29 September 2026) — `CLOSED`; the v2.10 merge engine ships it.** `release/merge-opnsense-catalog.sh`
implements the overlay the item asked for: core-first `msgcat --use-first` over the plugin catalogue with
assertions that no existing OPNsense translation changed and that every plugin string is present, plus a
`--plugin-only` mode for a locale whose core catalogue does not exist, which is how `nl_NL` is served without an
abort. `install-unattended.sh:101-124` stages one merged
`/usr/local/share/locale/<locale>/LC_MESSAGES/OPNsense.mo` per locale from the eleven catalogues (`en_US` is
skipped as the reference language), reuses the existing mode where a core catalogue exists, and hands the items to
the installer's own guard, backup, rollback and final-hash machinery. `uninstall.sh:107-154` restores the pristine
catalogues from first-write-wins records under `/var/backups/devicemonitor/core-locale/`, or deletes the file the
installer created (hash-verified) where no core catalogue existed, and refuses to touch a catalogue that is not
the injected one. The update target count therefore rises from **49 to 59** (`60` fresh: 38 manifest rows + 11
sidecar catalogues + 10 merged core catalogues, plus `rc.conf` when fresh), and `CHECK_OK`/`INSTALL_OK` report
`core_locales=10`. `tests/test_locale_merge.py` plus the CI step `Validate core catalogue merge (DM-BL-008c)` cover
both modes and the fail-closed guard; the installer dry run reports
`CHECK_OK version=2.10 predecessor=2.10 files=59 core_locales=10`. The candidate branch
`feature/optional-locale-installer-20260927` stays unmerged and is superseded: shipping all eleven catalogues
removes the `--languages` default sub-decision recorded above. **Validation completed (29 September 2026):** the
testbed install ran as `INSTALL_OK version=2.10 files=59 core_locales=10` (ten core catalogues merged, `nl_NL`
served plugin-only, backup `install-v210.O1Tggb`), the installer `--check` gate reports
`CHECK_OK version=2.10 predecessor=2.10 files=59 core_locales=10`, and
`python3 tests/test_language_acceptance.py --engine runtime` passes for the nine languages with **exit code 0**
(`LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0`); the English-fallback negative check is
evidenced by the preserved pre-merge fr_FR core catalogue returning the English message id for a plugin key that
the merged catalogue translates. Remaining caveat: the merge writes core package-owned files, so a core
`pkg upgrade` can replace them until the installer is re-run.

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
  file is read or written. (Partly superseded on 29 September 2026: the `DM-BL-008c` merge engine now
  also writes the core catalogues so the inline-script strings translate; the sidecar path itself still
  reads and writes nothing under `/usr/local/share/locale`.)

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

### Final sign-off — 28 September 2026

- **`O4` — view migration: `CLOSED` (verified via human browser pass)**, recorded on operator
  instruction. Provenance: operator attestation in this session; the run-book's evidence artifacts
  (screenshots, About-tab page source for both toggle states, browser and version, timestamps, the
  `<language>` value before and after) were not attached to this checkout, so this entry states the
  operator's reported result rather than an artifact-backed verification, as `DM-BL-008b` does.
- **Sidecar dialogue domain switching: `SUCCESSFUL`** — `fr_FR` and `it_IT` runtime validation
  matched the expected values in `verification/O4-HUMAN-ACCEPTANCE-RUNBOOK.md`, including the
  precedence case with the toggle on and the core-domain fallback with it off.
- `O3` (installer catalogue layout) remains `RESOLVED` and deployed. The `DM-BL-008c` merge decision was
  taken on 29 September 2026 (the v2.10 merge engine; see that entry above). `DM-BL-008a` (Dutch selectability) was closed as
  dropped on 28 September 2026 — an inherited `get_locale_list()` limitation, not a result of this
  work; see the `DM-BL-008a` entry above.

## O4-ageing — stale `unavailable` rows age to `unknown`; unseen hosts are retired: `OPEN` (deployed; retirement churns on multi-row IPs)

**Identifier note:** `PROJECT_STATE.md` and `DECISIONS.md` 52 use `O4` for this item. The `O4`
above (sidecar text-domain view migration, `CLOSED` 28 September 2026) is a different workstream;
neither references the other in the original records, so the ageing work is named
`O4-ageing` here.

**Description:** `device_services.status` only ever moved between `available` and `unavailable`.
Nothing aged an `unavailable` verdict, so a service that failed two consecutive probes stayed
down indefinitely, and rows whose hosts had not been seen since 2026-09-21 were still presented
as current inventory.

**Implemented (31 October 2026, branch `feature/async-db-v2.11`, commit `cd8ccbc`):**
`age_stale_service_state()` rewrites `unavailable` rows older than 7 days to `unknown` (clearing
`miss_count` so Decision 49's two-miss rule still applies afterwards) and deletes rows whose
`devices.last_seen` is older than 30 days, together with their held alert. The pass runs on the
hourly scheduled discovery gate and via `scan_network.py --age-services [--dry-run]`. It refuses
retirement outright when no host at all is fresh, and never retires an address that has no
`devices` row. The Devices view renders and filters `unknown`. Decision: `DECISIONS.md` 52.

**Deployed (31 October 2026)** to both HA nodes from a 2.10 predecessor:
`.252` (CARP BACKUP) `INSTALL_OK version=2.11 files=60`, backup `install-v211.Mni93b`;
`.253` (CARP MASTER) `INSTALL_OK version=2.11 files=60`, backup `install-v211.bMJF2H`. Both nodes
now carry `scan_network.py` `843c15f7…` and `infrastructureservices.volt` `6034d980…`, with the
`miss_count` schema migration applied in place.

**Live evidence:** `--age-services` on `.252` `aged 47, retired 0` (121 services, `unavailable`
55 -> 8, `unknown` 47); on `.253` `aged 46, retired 21` (128 -> 107 services, `unavailable`
54 -> 5, `unknown` 40), with 47 and 46 `SERVICE_CHANGED` activity events respectively. A second
dry run on both nodes reports `aged 0, retired 0`. `.253` retains 13 `devices` rows older than
30 days with no service rows attached, and both nodes keep their untracked-endpoint rows.

**Controlled proofs (live database byte-identical after each):**
1. copy of the master database with back-dated `last_verified`/`last_seen`: retirement at the
   30-day boundary, ageing at the 7-day boundary, `miss_count` reset, untracked endpoint kept,
   idempotent second run — `PROOF=PASS`, live SHA256 `83a1418c…` unchanged;
2. copy of the master database with `service_discovery_state.last_run` back-dated and discovery
   stubbed: the scheduled wrapper logged
   `[SERVICES] Stale-state ageing: aged 0 row(s) to unknown, retired 0 row(s)` after
   `[SERVICES] Scheduled discovery completed` — `SCHED_PROOF=PASS`.

**Operator note:** the automatic ageing path sits behind `service_observation_allowed()`, so only
the CARP MASTER ages state in a scheduled scan; the backup logs `skipping service discovery and
service alerts on this node`. The `.252` ageing above was an explicit CLI run, consistent with the
rows its own Devices view shows.

**Open defect found in the first scheduled cycle (19:43:16 on `.253`):**
`[SERVICES] Scheduled discovery completed: 71 verified service(s)` was followed by
`[SERVICES] Stale-state ageing: aged 0 row(s) to unknown, retired 12 row(s)` although the manual run
had left no service rows attached to a stale host. Net inventory stayed at 107 and
`rows_on_stale_devices` returned to 0, so 12 rows had been inserted by discovery (this cycle or
a preceding targeted-scan inventory sync) for endpoints whose `devices.last_seen` is older than
30 days, and the retirement step deleted them. No
`SERVICE_DISCOVERED` event was written, so those services never reach the Changes feed, and the
underlying `devices` rows (all long-standing, none added today) stay stale.

Cause: retirement keys on the *device* timestamp; discovery has positive evidence the endpoint
answers. Candidate fixes: (a) exempt rows whose `last_verified` is inside the retirement window,
(b) refresh `devices.last_seen` when a service is verified, (c) retire on
`device_services.last_verified` age alone.

**Resolved by Decision 53 (operator chose (b)), commit `6258914`, deployed 31 October 2026:**
`upsert_device_service()` advances the existing `devices` row's `last_seen` after a successful
verification (`available` status, detection method other than `authoritative`, forward-only, never
inserting a device). Bundle `6a66a068…` installed on both nodes
(`.252` backup `install-v211.qW0WKO`, `.253` backup `install-v211.apLeor`), installed
`scan_network.py` `2f3c05b1…`. Live evidence on the master: `192.168.20.127` moved from
`last_seen 2026-09-12` to `19:56:31` through its DNS/NTP/WEB_ADMIN verifications, those three rows
now persist and are `available`, `kept_rows_on_refreshed_hosts=5`, `stale_devices` 13 -> 12 and
`--age-services --dry-run` reports `retired 0` (against 21 then 12 by churn before the fix). The
backup never runs discovery, so it neither refreshes nor churns.

**Two residual seams found immediately afterwards (measured 19:58:16 on `.253`) — one withdrawn, one
fixed by Decision 54:**

1. *Withdrawn — the `retired 3` was not churn.* Those three rows (`192.168.20.116`, RDP 3389 and SMB
   139/445, `nmap_service`, `last_verified 2026-09-21`) were original inventory, not re-imported
   rows: the only insert path is `upsert_device_service()` and every caller stamps a current time.
   The scheduled cycle at 22:08:27 retired them once
   (`aged 0 row(s) to unknown, retired 3 row(s)`), leaving `total=116`, `rows_on_stale=0`.
2. *Fixed — ageing could re-flip a still-probed endpoint.* `record_service_miss()` never wrote
   `last_verified` (by design, it is last known-good), so an `unavailable` row aged to `unknown`
   kept an old timestamp and flipped back to `unavailable` after two failed probes, then aged
   again — an oscillation with an emailable `SERVICE_UNAVAILABLE` each round. Measured before the
   fix: 40 `unknown` rows, 22 at `miss_count = 1`, one probe from the first re-flip.
   `device_services.last_checked` (Decision 54, commit `d266698`) now records every observation and
   ageing keys on `COALESCE(last_checked, last_verified)`; existing databases are migrated with
   `ALTER TABLE` plus a backfill. Deployed as bundle `c45715b1…` (`.252` backup
   `install-v211.4x90pm`, `.253` backup `install-v211.1rHLrw`), installed `scan_network.py`
   `7560406b…`, `last_checked` present with no NULLs; `.253` ageing then retired 5 pre-existing rows
   on unseen hosts and a following dry run reads `aged 0, retired 0`, `.252` reads `0/0`; 62 rows
   carry a `last_checked` inside two hours and no `SERVICE_UNAVAILABLE` event has appeared since
   19:43. Pinned by `AGE_MISS_ADVANCES_LAST_CHECKED` and `AGE_LAST_CHECKED_MIGRATION`
   (18 cases), full local suite 30/30, `V211_RELEASE_MANIFEST=PASS`.

**Reopened 31 October 2026 (node time 23:14:22):** the next scheduled cycle logged
`aged 0 row(s) to unknown, retired 3 row(s)` again, so retirement still churns. Measured cause, on
the master:

- address `192.168.20.254` has **two** `devices` rows: `a0:10:a2:ba:06:e5`
  (`last_seen 2026-08-15 11:10:03`) and `00:00:5e:00:01:01` (`last_seen 2026-10-31 12:32:29`);
- its five service rows were verified at `23:13:37 … 23:14:09` and are `available`;
- the retirement predicate is `s.ip IN (SELECT ip FROM devices WHERE last_seen < cutoff)`, so **one**
  stale row for an IP makes every service on that IP retireable, regardless of a fresh sibling row;
- `touch_device_last_seen()` did advance both rows, but the scan's own hostwatch import then writes
  `UPDATE devices SET … last_seen = ? … WHERE mac = ?`
  (`scan_network.py:8428-8435`) with hostwatch's value, which rewinds the legacy row to `2026-08-15`
  every cycle. The refresh is undone before retirement runs.

Two candidate fixes, both narrow:
(A) retirement requires that **no** device row for the address is fresh —
`NOT EXISTS (SELECT 1 FROM devices d WHERE d.ip = s.ip AND COALESCE(d.last_seen,'') >= cutoff)` —
so "someone has seen this host recently" is enough to keep its inventory;
(B) the hostwatch upsert must not move `last_seen` backwards
(`last_seen = MAX(COALESCE(last_seen,''), ?)`), so a replayed hostwatch value cannot undo a probe.

(A) is the smallest change that stops this churn and is correct on its own terms; (B) removes the
rewind that made it possible. Both were applied as Decision 55, commit `9a300cd`, bundle
`c2aedfc0…`, installed on both nodes (`.252` backup `install-v211.MBQu7J`, `.253` backup
`install-v211.EJPCJH`), installed `scan_network.py` `71e2edfc…`.

Field effect of the redeploy, measured on the master:

- `(B)` is proven: the legacy `192.168.20.254` row moved from `2026-08-15 11:10:03` to
  `2026-11-01 00:16:52` and stayed there instead of being rewound by the hostwatch import;
- `(A)` is proven for that address: both of its rows are now fresh and its five services
  (verified `00:16:18 … 00:16:52`) persist;
- no address now has service rows with no fresh device row, and no address has a mixed stale/fresh
  row set — the candidate set the predicate looks at is empty;
- **but** the `00:17:06` cycle (the first scheduled discovery after this install) still logged
  `aged 0 row(s) to unknown, retired 3 row(s)`, with the total unchanged at 116. Those three rows
  could not be identified afterwards: no device row was refreshed between `00:17:06` and `00:25:00`,
  no service row was verified after `00:17:06`, and the candidate query returns nothing. They were
  therefore either genuinely abandoned rows retired once (correct behaviour) or authoritative
  (config-derived) rows whose address never refreshes by design. The `01:17` cycle decides which:
  `retired 0` means the churn is over, a repeat of `retired 3` means the authoritative path is the
  remaining source and needs an insert-side guard.

**Identified and fixed 1 November 2026 — Decision 56, commit `6493d5a`.** The `01:23:03` cycle
repeated `retired 3`, so one real discovery pass was run against a **copy** of the live database
(`sqlite3 .backup`, live file hash-checked before and after). It named the rows exactly:
`192.168.20.116` RDP 3389 and SMB 139/445, `detection_method` `nmap_service`, `last_verified`
`2026-09-21 09:07:55` — the `finished_at` of nmap history row 35. Phase-3 discovery re-uses previous
Nmap evidence and stamped inventory with that historical time
(`evidence_time = finished_at or now_text`, `scan_network.py:5488-5506`), so each cycle recreated the
rows six weeks old; Decision 53's forward-only refresh correctly refused to move `devices.last_seen`
backwards to that date; Decision 55's predicate then treated the address as unseen and retirement
deleted the rows again. Both earlier fixes were correct but aimed at the wrong side of the loop.

`nmap_evidence_is_current()` now rejects evidence older than `SERVICE_UNKNOWN_AFTER_DAYS` and the
pass logs `[SERVICES] Skipped N Nmap evidence row(s) older than 7 days`. Deployed as bundle
`41cd357b…` (`.252` backup `install-v211.UE7JJ9`, `.253` backup `install-v211.AzOAj2`), installed
`scan_network.py` `175598e4…` on both; dry runs read `{"aged": 0, "retired": 0}` on both.

Proof against the same copy of the live database, with the new build performing a full real
discovery:

```
LOG [SERVICES] Skipped 6 Nmap evidence row(s) older than 7 days
DISCOVERED=66            (was 72)
CANDIDATES=0             (was 3)
ALL_STALE_ADDRESSES=192.168.20.109(2),192.168.20.116(1),…
LIVE_UNCHANGED=True
```

i.e. the three rows are no longer recreated, and no service row is attached to an address whose
device rows are all stale. Tests: `PHASE3_STALE_EVIDENCE_SKIPPED` (a six-week-old evidence row writes
no inventory) and `NMAP_EVIDENCE_AGE_BOUND` (one hour and exactly seven days are current, seven days
plus a second is not, empty/unparseable fall back to current); full local suite 30/30 PASS,
`V211_RELEASE_MANIFEST=PASS`.

**Closes when:** the next scheduled cycle on the master logs
`aged 0 row(s) to unknown, retired 0 row(s)` and the rows stay gone. Until then this item stays
open, because the copy run proves the code and only the live cycle proves the deployment.

**Not caused by this item, recorded because it was observed during the deployment:** both nodes log
chronic `database is locked` scan failures (14,760 on `.252` since 06-10-2026, 16,130 on `.253`
since 09-09-2026) and `/usr/local/sbin/sendmail: not found` from the targeted-Nmap email path.

### DM-BL-009 — 2.14.0 `main` reconciliation and integration: **`CLOSED`** (7 November 2026)

**Description:** after the canonical clone was refetched on 3 November 2026, the remediation branch
was neither ahead of nor behind `origin/main` but **diverged** from it:

    git rev-list --left-right --count origin/main...HEAD   ->   14   48
    merge base                                             ->   40cced8

(Measured against the locally recorded `origin/main` at the validated M5 checkpoint
`a1f759e9b64a1265a951260d45845df46435b1be`. This is a point-in-time evidence reference, not a
claim that the branch tip remains at that commit; re-measure before any `main` reconciliation.)

`origin/main` (`d5d73ed`) carried work the branch did not contain — `8ea1203 release: v2.12`,
`c494485 merge: bring v2.12 (and the About-version fix) onto main`, `c9373b8 fix(ha)`,
`a12ede8 feat(identity)`, `d268680 fix(devicemonitor)` and `d5d73ed test: pin fail-open non-HA
behaviour` — while the branch carried the 48 commits of the 2.13.3 remediation and its records at
that checkpoint.

**Closure result (7 November 2026):** PR #6 was fast-forwarded from `d5d73ed` to
`282517744260920b18c9217efd09ce738af21d70`, preserving all 54 integration commits. Remote `main`
and its tree `73750b8e1247f21a8b5dd2c888e5ece64bbfe8af` match the reviewed head. Exact-main CI
run `42342362864` completed successfully with `RELEASE_INPUTS=PASS cases=7`,
`V2140_RELEASE_MANIFEST=PASS`, and bundle SHA-256
`5149bfd41e5842a144a9d1280c008511f20f3783932eca9beb1f48fca6173f5f` / 1,725,593 bytes. Evidence:
`verification/MAIN-INTEGRATION-2.14.0-20261107.md`.

**This does not block the 2.13.3 release.** `origin/release/2.13` (`6bd122e`) is an **ancestor** of
the branch, so integrating there is a **fast-forward with zero conflicts** — no merge and no rebase is
necessary (Decision 66, `verification/RELEASE-INTEGRATION-ASSESSMENT-20261103.md` §2 and §4).

**Local reconciliation completed:** `integration/dm-bl-009-reconcile-20261105` was created from
`origin/main` `d5d73ed` and merges `fix/pruning-remediation-20261103` `b2c74fc`. Both histories are
preserved; the combined payload is a new candidate, `2.14.0`
(`release/v2.14.0-runtime.manifest`, 42 rows). The integration history starts at `eac1160` and
includes the rollback correction. Its immutable candidate is 1,725,593 bytes with sha256
`5149bfd41e5842a144a9d1280c008511f20f3783932eca9beb1f48fca6173f5f`; the validation evidence
records `CANDIDATE_SOURCE=worktree` because it was collected before the branch commit. Local
bundle, manifest, installer, pruning, reconciliation, Python, PHP, JavaScript and catalogue/language
checks passed. It was subsequently deployed to `.23` on 6 November; the 2.13.3 live deployment and
historical M5 jail results do not themselves validate the changed tree.

**2.14.0 rollback correction:** the earlier `530facc…` candidate exposed a real rollback defect.
After an injected post-prune `configd` failure it reported `ROLLBACK_STATUS=COMPLETE` and restored
all 63 targets and the record, but all ten pre-existing
`/var/backups/devicemonitor/core-locale/*.state` files retained the attempted 2.14.0 `installed=`
digest. Those files are the ownership/restore record used by `uninstall.sh`, not disposable
metadata. The corrected installer snapshots the whole state directory before mutation and restores
its files, metadata and absence semantics during rollback; the tampered-backup path is refused
before mutation. The release-input pin was regenerated through the established build script.

On 6 November the full installer-jail set ran against the corrected candidate digest and all five
scenarios passed. Rollback reported `ROLLBACK_STATUS=COMPLETE`, target restoration
`restored=31 skipped=32 conflicts=0 failed=0`, prune restoration
`restored=1 skipped=0 conflicts=0 failed=0`, and core-locale restoration
`restored=19 removed=0 conflicts=0 failed=0`. The before/after snapshots differ only by the retained
installer backup directory. The earlier candidate digest and failed transcripts remain preserved
as superseded diagnostic evidence. The later live deployment exercised the real configd restart and
daemon stop/wait/start lifecycle.

**2.14.0 fresh-install correction and validation:** the harness now has `fresh` and
`fresh-rollback` scenarios. Both passed on 6 November against the unchanged bundle. `fresh`
reported `CHECK_OK ... predecessor=fresh files=64 core_locales=10 prunable=0 daemon_running=0 ...`
and `INSTALL_OK version=2.14.0 files=64 core_locales=10 pruned=0 ... daemon_restarted=0 unchanged=0
repaired=0`; all 64 targets, the 64-row record, the ten pristine core catalogues, the rc.conf/rc.d
wiring and a running daemon were verified, with no database or configuration created. The injected
post-mutation failure reported `ROLLBACK_STATUS=COMPLETE`, targets `restored=64 skipped=0
conflicts=0 failed=0`, core-locale `restored=0 removed=19 conflicts=0 failed=0`, and restored every
originally absent path. Evidence: `/root/dm-validation-2140/jail-evidence-fresh-20261106/`
(`SHA256SUMS` sha256 `1448ec56adf75dab2461da9f0fda6447486a9258fadd4afa9c4deec70e43b05b`). The
jail-only `rc.configure_plugins` stub proves the call boundary, not real OPNsense plugin
registration. Live `FRESH=1` and real plugin registration remain untested; the bounded monitoring
exercise is recorded separately below. The live successful-install rollback is recorded below.
Real-host fresh-install and plugin lifecycle validation are tracked as **DM-BL-012**.

**Deployment status:** Device Monitor 2.14.0 is installed on the `.23` testbed only. The host runs
OPNsense 26.7.8_2; `os-git-backup-1.1_5` was installed immediately before the upgrade and caused an
OPNsense configuration migration/plugin-registration revision, which the pre-install backup
captured. `.253` and `.252` remain on 2.13.2 and were not contacted.

**2.14.0 host preflight:** pre-integration pushed HEAD `690204bb1d6c402de9a2b41e16f753b37335279f` passed CI
run `42116897417` (one `validate` job, 66 steps, zero failures or skips). A read-only `.23`
preflight confirmed OPNsense `26.7.8_2`, installed Device Monitor 2.13.3, 61 valid record rows,
SQLite integrity `ok`, monitoring disabled, no WAL, healthy daemon/configd and 3.0 GB free. The
non-mutating installer check reported
`CHECK_OK version=2.14.0 predecessor=2.13.3 files=63 core_locales=10 prunable=0 daemon_running=1 host=OPNsense.internal legacy_prunable=0 retained=0`;
live state, the 90-entry backup inventory and temporary stages were unchanged. Those counts are
the actual-predecessor expectations, not the jail fixtures. The candidate adds the lazy
`device_identity_events.notified_at` column and six default-off settings without changing any
existing common default. A disposable database copy migrated idempotently with all rows preserved;
the live database intentionally remains on the old schema while monitoring stays disabled.

**2.14.0 live deployment:** the authorised normal upgrade completed with
`INSTALL_OK version=2.14.0 files=63 core_locales=10 pruned=0 backup=/var/backups/devicemonitor/install-v214.JeYC44 daemon_restarted=1 unchanged=32 repaired=0`.
All 42 manifest rows and all 63 installer-plan targets passed digest/mode/ownership checks. The
record has 63 digest rows including 21 locale rows. Database, Device Monitor configuration and
OPNsense configuration remained byte-identical; SQLite integrity is `ok`; monitoring is disabled
with no WAL. Daemon PID `34058` → `79168` remained alive after 60 seconds; configd PID `639` →
`35685`; `configctl devicemonitor status` is `running`. Rollback was **not invoked during the
initial deployment**; the separate live rollback test follows.

**2.14.0 successful-install live rollback (6 November): PASS.** The authorised §9.3 cycle first
restored the accepted 2.14.0 state to 2.13.3 through `install-v214.JeYC44`, then installed 2.14.0
normally and created `/var/backups/devicemonitor/install-v214.zGJRuq`. The helper rollback of that
successful installation reported `ROLLBACK_SUMMARY=restored=31 skipped=32 conflicts=0 failed=0`
and `CORE_LOCALE_ROLLBACK_SUMMARY=restored=19 removed=0 conflicts=0 failed=0`; the manual helper
does not emit `ROLLBACK_STATUS`. Independent checks found 61 restored targets and the 2.13.3
record, unchanged database/configuration, SQLite integrity `ok`, the two 2.14-only targets absent
again, and healthy daemon/configd. A final normal install returned to 2.14.0 with 63 targets,
zero prunes, record `d891ce68…`, unchanged data/configuration and
`backup=/var/backups/devicemonitor/install-v214.qMPS7n`. Evidence:
`/root/dm-validation-2140/live-rollback-20261105T231701Z/` (`SHA256SUMS` sha256
`5cc19b38d4b8a294ef83f8ddfdf86db0622a652c943c4f83a48bdaa258f79fe3`).

Pre-install backup: `/root/dm-pre-2140/runtime-data.tgz`, 7,632,213 bytes, sha256
`ff7873ce0fbc1826663aa86c3271014c9c2ad3cdb3bd7b4eacce164a4a63753e`, with 61 payload files,
19 core-locale files, record, consistent database and configuration. Installer backup:
`/var/backups/devicemonitor/install-v214.JeYC44`. The rollback test and final reinstall are
preserved as `install-v214.zGJRuq` and `install-v214.qMPS7n`; the pre-mutation recovery point is
`/root/dm-validation-2140/rollback/20261105T231610Z`. The exact procedures and evidence references
are in `verification/DEPLOY-2.14.0-23-PLAN.md` and
`verification/LIVE-ROLLBACK-2.14.0-23-20261106.md`.

**§9.4 bounded monitoring execution (6 November 2026): COMPLETE / ACCEPTANCE PASS — further execution is unauthorised.** After operator acceptance of `/conf/config.xml` `15ce9e6c…831b4` and preservation of the current Git Backup configuration, the reviewed detached watchdog completed exactly two scheduled inventory scans (`3497 → 3499`) within the 900-second limit. The scheduled scans logged service discovery as not due; the five DMTEST services were observed through a separate direct `scan_network.py --discover-services` command. Visibility probing covered 253 addresses within `opt1`/DMTEST/`192.168.50.0/24` only. The loopback SMTP sink captured two messages from directly invoked PHP helpers, not daemon-generated notification delivery. Identity/service/new-device/aged/retired and fresh-host refusal were copy-only fixtures. Final `ACCEPTANCE=PASS`: monitoring `enabled=0`, empty interface selection, Device Monitor and configd running, no `2525` listener, no scan/Nmap/sink/sampler process and no WAL/SHM. Device Monitor configuration `027594eb…`, record `d891ce68…`, OPNsense configuration `15ce9e6c…` and all 19 core-locale files are byte-identical.

**Live `notified_at` migration and database restoration.** The migration was observed live before restoration: the guard/pre-install snapshot had the column absent, `live-after-discovery.txt` recorded it present at `08:36:24Z` before monitoring was enabled at `08:36:26Z`, and it remained present after the cycles. Its final absence is restoration evidence, not proof that migration did not occur. The saved evidence records the original live database as `c17874a7…` and the verified consistent SQLite snapshot as `796d28c7…`; the final guard snapshot and live file are both `796d28c7…`. Both states produced `.dump` digest `d7ed7f81…` and guard `iterdump` digest `10460718…`; the retained snapshot has 21 schema tables, 22 indexes, one trigger, 382 user rows, the same 26/60/2/96 counts and `notified_at` absent. The transition is traced: `/root/dm-pre-2133/devices.db` first retained `796d28c7…` via `src.backup(dst)` on 5 November while the live hash was `c17874a7…`; at `08:31:33Z` the historical guard independently backed up the then-live `c17874a7…` database to `796d28c7…`; after pre-monitoring configuration validation failed, its `08:32:04Z` recovery copied that snapshot over the live path. The installer did not replace the live file during §9.3. No retained physical database matches `c17874a7…` (21 files named `devices.db` and 12 retained archive members checked), so the internal header/page delta cannot be compared or reproduced. The historical guard's `prestate.db_sha` was its backup hash rather than the original live hash, so `PASS` proved restoration to the verified snapshot, not byte identity to `c17874a7…`. Physical byte identity is not claimed for the completed exercise and remains an unresolved acceptance discrepancy under its recorded criteria. The guard was subsequently corrected to stop and verify writers before capture, retain original database/WAL/SHM bytes separately from the consistent SQLite fallback, archive the post-state database before restoration, and verify restored physical bytes, metadata, schema/data and integrity against the original recovery copy. That correction prevents recurrence but cannot retroactively prove the historical bytes.

The first supervised status check saw a transient configd socket; manual `guard recover` passed and the wrapper now retries within a bounded window. The SMTP parser now normalises angle-bracketed addresses and ESMTP `SIZE=` values while retaining the single-recipient rule. The corrected guard keeps original, snapshot and restored database identities separate; its 35 mock/disposable-copy tests all pass, including distinguishing logically equal but physically different snapshots, rejecting normalised snapshot bytes as physical restoration, accepting original bytes, archiving WAL/SHM before replacement, capturing and restoring a real uncheckpointed WAL/SHM pair exactly, and leaving monitoring stopped on unsafe capture or restoration. This correction cannot retroactively prove the completed exercise's physical bytes. Evidence: `verification/monitoring-validation/EXECUTION-20261106.md` and `/root/dm-validation-2140/monitoring/20261106T083522Z/`.

The remaining validation limits do not reopen DM-BL-009; they are separately identified. Physical DB byte identity for the completed exercise is **DM-BL-011** and remains a release blocker for an unqualified exact-restoration claim: the operation is traced and the logical state is verified, but the original bytes and their page map were never retained. The corrected guard now enforces original-byte identity for any future authorised run but cannot prove the historical bytes. Live `FRESH=1` and real OPNsense plugin registration/lifecycle are **DM-BL-012**; the disposable jail proves the call boundary but is not a real-host pass. Full reminder/ageing/CARP and daemon-generated notification/service-discovery paths are **DM-BL-013**, as are exact daemon-triggered attribution of the `notified_at` migration and external delivery. No further run is authorised. Issue #5 remains **OPEN**; §9.4 is paused.

**Main integration completed (7 November 2026):** draft PR #6 was reviewed and then fast-forwarded
with no squash, rebase or force-push. The authenticated About/Features screenshot remains accepted
as visual evidence; its Network-capture evidence was not required for visual acceptance. The latest
published GitHub release remains v2.12.1, and 2.14.0 has no tag or GitHub release.

**Also open here: CI went red on the first run.** The validated M5 checkpoint is published at
`a1f759e9b64a` and run #41609297193 failed at "Verify the bundle is deterministic across
checkouts"; Decision 67 fixed the two causes, Decision 68 replaced the archive tail and
compressor, and Decision 69 made the build-safety tar fixtures platform-neutral. **CI at the
validated M5 checkpoint `a1f759e9b64a` is green: run #41977736287, 64/64 steps, zero skips**,
so review item H1b is closed.

**Closure criterion (met):** the chosen `main` path was executed by fast-forwarding the exact
reviewed head into `main` and validating the resulting SHA. Live `FRESH=1`, real
`rc.configure_plugins` registration and full reminder/ageing/CARP/lifecycle behaviour were not
claimed as part of this reconciliation item; they remain open as DM-BL-012 and DM-BL-013. The
isolated fresh-install scenarios, the live successful-install rollback and the bounded two-cycle
monitoring exercise remain validated evidence, not a transfer of those residual gates.

**Related, also open:** `/usr/local/cline-freebsd/src/cline` still sets `origin` to this repository
while carrying an untracked Cline installation (Decision 65 §Preservation). Repointing it needs the
intended Cline remote and explicit authorisation; it is preserved unchanged until then.

### DM-BL-010 — translation-header metadata warnings in the v2.12.1 installation output (`PO-Revision-Date`, `Last-Translator`, `Language-Team`): **`OPEN`** — integrated in `main`; publication pending

**Description:** the reporter's v2.12.1 installation log contains non-fatal translation-header
metadata warnings for catalogue entries missing the following headers:

- `PO-Revision-Date`
- `Last-Translator`
- `Language-Team`

The run still ended `INSTALL_OK` with `daemon_restarted=1`, so the warnings did **not** prevent
installation and no reinstall is required for them. They are recorded here for separate cleanup and
are **not** a defect of the issue #5 installation result.

**Cross-links:**

- GitHub issue #5 — **OPEN** (installation result recorded 7 November 2026)
- Investigation: `verification/ISSUE-5-V2.12-MANIFEST-20261106.md`, section *Reporter result (7 November 2026)*
- Verification: `verification/DM-BL-010-CATALOGUE-HEADERS-20261107.md`
- Phase 1 evidence: `verification/PHASE1-EXACT-CANDIDATE-23-20261107.md`
- DM-BL-009 — **CLOSED** (main reconciliation completed 7 November 2026)

**Implementation state (7 November 2026):**

- The pre-repair `msgunfmt` → `msgcat` → `msgfmt --check` sequence was reproduced against a
  sparse core header. It exited `0` but emitted exactly the three reporter warning fields; the
  retained evidence is `/root/dm-validation-2140/dm-bl-010-20261107/warning-reproduction/`.
- `release/merge-opnsense-catalog.sh` now fills only absent or empty `PO-Revision-Date`,
  `Last-Translator` and `Language-Team` fields from the plugin catalogue's real metadata. Existing
  core metadata and translations are never replaced, incomplete plugin metadata aborts, and both
  the prepared core and final merged catalogue remain subject to `msgfmt --check`.
- `tests/test_locale_merge.py` covers warning-free sparse-header merging, preservation of existing
  metadata/translations, rejection of incomplete plugin headers, and rejection of malformed plugin
  and core catalogues. The suite is wired into CI and passes locally as `LOCALE_MERGE=PASS`.
- Published v2.12.1 is now an accepted installer predecessor, covered by the ten-case local upgrade
  matrix (`UPGRADE_PREDECESSORS=PASS passed=10 skipped=0`) and a jail upgrade from the actual
  published `v2.12.1` payload.
- The affected release-input pin was regenerated (`VERIFY_OK=4`). Four independent builds are
  byte-identical: 1,729,177 bytes, SHA-256
  `90afa55dd826c0dc3be8a23902b809baa465e25191dc372dc6cc2ef4e57fc243`.
- The previous main-integration candidate (1,725,593 bytes, SHA-256 `5149bfd4…`) and its evidence
  remain preserved as superseded, not deleted or overwritten.
- PR #7 integrated the candidate into `main` at
  `e9ec5486a8cc9e87e3b6d3cf6098f26ed15e1370`; exact-main CI run `42359428985` passed. It is not in
  any published release; published v2.12.1 assets remain unchanged.
- The exact candidate was installed once on `.23` as a same-version repair:
  `INSTALL_OK version=2.14.0 files=63 core_locales=10 pruned=0 backup=/var/backups/devicemonitor/install-v214.Uwwqu1 daemon_restarted=1 unchanged=63 repaired=0`.
  All 42 manifest rows and 63 targets passed, current core catalogues merged warning-free, nine
  available pristine translations were preserved, `nl_NL` remained plugin-only as expected, and
  configuration plus logical/physical database bytes were unchanged. Services remained healthy and
  monitoring/notifications remained disabled. Authenticated UI rendering was not observed.
- Because all 63 installed targets were already byte-identical, this live run did not exercise a
  sparse-header repair delta. That case remains covered by the regression and jail evidence.

**Constraints preserved by the implementation:**

- Preserve translation validation and meaningful diagnostics; these warnings must not become silent.
- Do **not** broadly suppress stderr or filter installer output generally.
- Do **not** modify published assets: tag `v2.12`, tag `v2.12.1`, their release notes and their
  assets remain immutable.
- Repair belongs in the catalogue/header data (or the build inputs that produce it), not in the
  published release payloads.

**Status:** **`OPEN`** — the source, regression, deterministic bundle and exact-candidate Phase 1
live validation are complete, and the correction is integrated into `main`. The item stays open
only because 2.14.0 is not yet published. Device Monitor 2.14.0 remains unpublished and v2.12.1
remains the latest published release.

### DM-BL-011 — historical database-byte identity for the completed §9.4 monitoring exercise: **`OPEN`**

**Description:** the completed bounded monitoring exercise has verified logical restoration but no
proven physical database-byte identity. The original live database was `c17874a7…`; the retained
consistent SQLite snapshot and later live file were `796d28c7…`. Both produced the same logical
`.dump` and `iterdump` digests, with clean integrity/quick checks and matching schema/table/row
counts, but the original bytes and their page map were not retained. Exact physical attribution is
therefore unproven and no unqualified exact-restoration claim may be made.

**Guard status:** the guard was corrected to stop and verify writers before capture, preserve the
original database/WAL/SHM bytes separately from the SQLite fallback, archive the post-state
database, and compare restored bytes/metadata/schema/data/integrity against the original recovery
copy. The 35 mock/disposable-copy guard tests pass. This prevents recurrence but cannot prove the
historical bytes.

**Closure evidence:** either new evidence capable of reconstructing and comparing the original
bytes, or explicit operator acceptance of the historical byte-identity limitation. Neither is
currently recorded. The limitation is distinct from DM-BL-009's completed `main` reconciliation.

**Evidence:** `verification/monitoring-validation/EXECUTION-20261106.md` and
`/root/dm-validation-2140/monitoring/20261106T083522Z/`.

### DM-BL-012 — real-host 2.14.0 `FRESH=1` and OPNsense plugin lifecycle validation: **`OPEN`**

**Description:** the isolated FreeBSD-jail `fresh` and `fresh-rollback` scenarios passed against the
unchanged 2.14.0 bundle, but their `configd`, `rc.configure_plugins` and `pgrep` stubs prove only
the installer's call boundary. They do not demonstrate real OPNsense plugin registration, real
configd interaction, a real daemon lifecycle after a fresh install, real-host `FRESH=1`, or
whole-tree live core-locale continuity.

The normal 2.13.3 → 2.14.0 upgrade on `.23` and its live successful-install rollback are validated
and are not this item. The outstanding work is specifically the **real-host fresh-install path and
real plugin lifecycle**.

**Closure evidence:** a separately authorised real-host `FRESH=1` test and plugin lifecycle check,
or explicit operator acceptance of the residual risk. The existing jail evidence must not be
described as equivalent.

**Evidence:** `verification/FRESH-INSTALL-JAIL-2.14.0-20261106.md`,
`verification/INSTALLER-JAIL-2.14.0-20261106.md`, and `PROJECT_STATE.md`.

### DM-BL-013 — full monitoring lifecycle, HA/CARP and delivery-path validation: **`OPEN`**

**Description:** the bounded §9.4 exercise completed two scheduled inventory scans, DMTEST-only
direct service discovery and two loopback SMTP messages from directly invoked PHP helpers. It did
not exercise scheduled daemon-triggered service discovery, full reminder/ageing/CARP behaviour,
daemon-generated notification delivery, exact daemon attribution of the `notified_at` migration,
external SMTP/webhook/AdGuard/Pi-hole delivery or targeted Nmap delivery.

**Closure evidence:** separately authorised live tests covering the relevant paths, or explicit
operator acceptance of the residual risk. No further live execution is currently authorised.

**Evidence:** `verification/monitoring-validation/EXECUTION-20261106.md` and
`verification/monitoring-validation/PREFLIGHT-20261106.md`.

## Deployment verification notes

### 2.13.3 live upgrade lifecycle on `.23` — **`CLOSED`** (5 November 2026)

**Description:** the M5 sandbox deliberately did not execute the daemon stop/wait/start branch or a
real `service configd restart`. The gated 2.13.3 deployment on `.23` exercised both.

**Evidence:** `INSTALL_OK version=2.13.3 files=61 core_locales=10 pruned=0
backup=/var/backups/devicemonitor/install-v213.xKjyg1 daemon_restarted=1 unchanged=60
repaired=6`. The old daemon PID 6557 exited; replacement PID 31483 started and remained running
after 60 seconds. The log records `Daemon stopping`, `Daemon stopped`, `Daemon started` and
`Monitoring DISABLED`. configd restarted from PID 71926 to 76711; `service configd status` and
`configctl devicemonitor status` both passed.

All 40 manifest rows and all 61 installed targets passed digest/mode/owner/group checks. The new
record has 61 digest rows (21 `.mo` targets), while the database and configuration remained
byte-identical and SQLite integrity passed. Six notification scripts were corrected to `0644
root:wheel`; this was the installer's non-fatal `repaired=6` result, not a failure. Monitoring
remained disabled.

**Closed scope:** the live daemon stop/wait/start and real configd restart verification gaps.

**Deliberately not established:** rollback was not invoked, so this deployment is not a live
rollback test. `FRESH=1` was not exercised on this host; it was later validated only in the
isolated 2.14.0 jail scenarios. The installer backup
`/var/backups/devicemonitor/install-v213.xKjyg1` and pre-install backup `/root/dm-pre-2133` remain
in place. `.253` and `.252` were not touched and remain on 2.13.2. DM-BL-009 was later closed by
the 2.14.0 `main` integration; live `FRESH=1` remains tracked as DM-BL-012.

### OPNsense 26.7.8_2 retained the 2.13.3 baseline on `.23` — **`CLOSED`** (5 November 2026)

**Description:** the authorised testbed OS update completed through `configctl firmware update`
and the required reboot. `POSTBOOT_RESULT=PASS` covered all 61 installed targets, the 61-digest
record, unchanged Device Monitor database/configuration, SQLite integrity, configd, the daemon and
`configctl devicemonitor status`; monitoring remained disabled. The post-update host is OPNsense
`26.7.8_2` / FreeBSD `15.1-RELEASE-p6`.

**Host tooling repair:** Codex initially could not load `libdbus-1.so.3` after the reboot.
`dbus 1.16.2_4,1` was installed from the OPNsense repository; `codex-cli 0.165.0` then started
normally. This did not change the Device Monitor payload or its configuration.

**Retained warning:** the update log records one package-audit warning for `libgpg-error-1.61`.
No Device Monitor or service check failed. Rollback was not invoked, `FRESH=1` remains untested,
the OPNsense-generated configuration backup remains under `/conf/backup/`, and real-host
`FRESH=1` remains tracked as **DM-BL-012**.
