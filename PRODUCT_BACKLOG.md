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

**Latest 2.14.0 runtime confirmation:** the production-engine run on the installed tree reports
`LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0`; the sole gap is this
same `nl_NL` selector omission. All nine languages render 10 pages and 490 keys. See
`verification/LANGUAGE-ACCEPTANCE-GAP-20261107.md`.

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

The remaining validation limits do not reopen DM-BL-009; they are separately identified. Physical DB byte identity for the completed exercise was tracked as **DM-BL-011** and was **closed on 13 November 2026** by explicit operator acceptance of the historical evidence limitation: the operation is traced and the logical state is verified, but the original bytes and their page map were never retained, so no byte-identity claim is made. The corrected guard now enforces original-byte identity for any future authorised run but cannot prove the historical bytes. Live `FRESH=1` and real OPNsense plugin registration/lifecycle were tracked as **DM-BL-012** and **closed on 12 November 2026** by explicit operator acceptance after lifecycle testing on `.23`. Full reminder/ageing/CARP and daemon-generated notification/service-discovery paths remain under **DM-BL-013**, as do the presence/service timestamp defect, exact daemon-triggered attribution of the `notified_at` migration and external delivery. No further run is authorised. Issue #5 remains **OPEN**; §9.4 is paused.

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
claimed as part of this reconciliation item. DM-BL-012 was later closed by explicit operator
acceptance; DM-BL-013 remains open. The
isolated fresh-install scenarios, the live successful-install rollback and the bounded two-cycle
monitoring exercise remain validated evidence, not a transfer of those residual gates.

**Related, also open:** `/usr/local/cline-freebsd/src/cline` still sets `origin` to this repository
while carrying an untracked Cline installation (Decision 65 §Preservation). Repointing it needs the
intended Cline remote and explicit authorisation; it is preserved unchanged until then.

### DM-BL-010 — translation-header metadata warnings in the v2.12.1 installation output (`PO-Revision-Date`, `Last-Translator`, `Language-Team`): **`CLOSED`** — fix integrated and validated; release tracked separately (16 November 2026)

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
- Release-readiness record: `verification/RELEASE-READINESS-2.14.0-4611447-20261107.md`
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
- The reviewed documentation candidate is
  `4611447089e2482a0c6af7a1844e9f6fa16c84d1` (tree
  `e3d551967fcd673cefd9031448c0e1791db2a2ab`), one docs-only commit ahead of `main`. Its CI run
  `42368818807` passed and reproduced the unchanged 1,729,177-byte / `90afa55d…` archive.
- The exact candidate was installed once on `.23` as a same-version repair:
  `INSTALL_OK version=2.14.0 files=63 core_locales=10 pruned=0 backup=/var/backups/devicemonitor/install-v214.Uwwqu1 daemon_restarted=1 unchanged=63 repaired=0`.
  All 42 manifest rows and 63 targets passed, current core catalogues merged warning-free, nine
  available pristine translations were preserved, `nl_NL` remained plugin-only as expected, and
  configuration plus logical/physical database bytes were unchanged. Services remained healthy and
  monitoring/notifications remained disabled. Operator-supplied authenticated evidence received
  7 November 2026 (Australia/Sydney) shows Device Monitor `v2.14.0` and
  `v2.14.0 Features and Enhancements` in the About screenshot; the operator confirms Devices loads
  without error. No exact observation time was recorded.
- Because all 63 installed targets were already byte-identical, this live run did not exercise a
  sparse-header repair delta. That case remains covered by the regression and jail evidence.
- The GitHub Actions native language runtime matrix remains skipped because that runner lacks the
  required assets. A separate local production-engine run on the installed 2.14.0 tree passed on
  7 November 2026: `LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0`, with 10
  pages and 490 keys per language. The `nl_NL` GUI-selector absence remains the documented gap; it
  is not a runtime rendering failure. Report:
  `/root/dm-validation-2140/language-runtime-2.14.0-20261107.md`.
- A validation-closure pass on 7 November 2026 found and fixed a guard snapshot-side-effect defect,
  passed a disposable DB/WAL/SHM rehearsal and changed publication to **NO-GO** pending the then-open
  DM-BL-011/012/013 gates; DM-BL-011 and DM-BL-012 have since closed, while DM-BL-013 remains open.
  See `verification/VALIDATION-CLOSURE-2.14.0-20261107.md` and
  `verification/RELEASE-READINESS-2.14.0-4611447-20261107.md`.

**Constraints preserved by the implementation:**

- Preserve translation validation and meaningful diagnostics; these warnings must not become silent.
- Do **not** broadly suppress stderr or filter installer output generally.
- Do **not** modify published assets: tag `v2.12`, tag `v2.12.1`, their release notes and their
  assets remain immutable.
- Repair belongs in the catalogue/header data (or the build inputs that produce it), not in the
  published release payloads.

**Status:** **`CLOSED` (implementation and validation) as of 16 November 2026.** The source
correction, regression coverage, deterministic bundle, exact-candidate Phase 1 live validation,
operator-supplied authenticated About/Features/Devices-loading evidence and the native runtime
language matrix are complete, and the correction is integrated into `main` (PR #7, `e9ec5486…`,
exact-main CI run `42359428985`). **No further coding work is required for this item**, and none is
duplicated elsewhere in the backlog.

**Publication obligation — tracked by the release tracker, not here.** Device Monitor 2.14.0 is
**not published**; v2.12.1 remains the latest published release (tag `v2.12.1`, GitHub release
2026-11-06). The corrected catalogues therefore reach users only when 2.14.0 is released. That
release is gated by DM-BL-013 and the remaining release controls, not by any deficiency in this
defect. This record makes **no claim that the fix has been published**.

### DM-BL-011 — historical database-byte identity for the completed §9.4 monitoring exercise: **`CLOSED`** (13 November 2026; explicit operator acceptance of the historical evidence limitation)

**Description:** the completed bounded monitoring exercise has verified logical restoration but no
proven physical database-byte identity. The original live database was `c17874a7…`; the retained
consistent SQLite snapshot and later live file were `796d28c7…`. Both produced the same logical
`.dump` and `iterdump` digests, with clean integrity/quick checks and matching schema/table/row
counts, but the original bytes and their page map were not retained. Exact physical attribution is
therefore unproven and no unqualified exact-restoration claim may be made.

**Guard status:** the guard was corrected to stop and verify writers before capture, preserve the
original database/WAL/SHM bytes separately from the SQLite fallback, archive the post-state
database, and compare restored bytes/metadata/schema/data/integrity against the original recovery
copy. A disposable Phase 2A rehearsal on 7 November found that the fallback snapshot was being taken
from the live WAL-mode database and could checkpoint/remove its sidecars; the guard now snapshots a
disposable copy of the exact recovery assets instead. The strengthened WAL/SHM regression and all
35 guard tests pass locally and have now been added to the validation-only CI workflow with an exact
`Ran 35 tests`/`OK` assertion; `tests/test_ci_config.py` pins that wiring. The workflow change is not
yet exercised by an exact-SHA run, so execution in CI remains unproven until that run is recorded. The
rehearsal also passes separate DB/WAL/SHM capture, mutation detection,
snapshot-equivalence rejection, exact-byte restoration, configuration/record/OPNsense/core-locale
preservation and post-state archiving. This prevents recurrence but cannot prove the historical
bytes.

**Closure evidence:** on 13 November 2026 the operator explicitly accepted the historical
physical-byte limitation. The closure basis is the verified logical restoration, matching logical
digest, schema, row counts and integrity checks, together with the corrected and tested byte-preserving
guard. This makes no historical byte-identity claim: the original `c17874a7…` bytes remain unavailable
and the retained copies are `796d28c7…` or older unrelated states. All retained database files
rechecked on 7 November are `796d28c7…` or older; the
`/var/backups/devicemonitor/devices.db.pre-monitor-scan-20260923-070801` copy is `65e11a3b…`, not the
6 November original. A broader read-only search covered 128 physical database candidates and 67
archives; no exact copy was found, and common SQLite copy/`VACUUM`/`VACUUM INTO`/`PRAGMA optimize`
transformations on a copy did not reproduce the hash. This is an accepted historical evidence
limitation, not a current recovery defect, and is distinct from DM-BL-009's completed `main`
reconciliation.

**Evidence:** `verification/monitoring-validation/EXECUTION-20261106.md`,
`verification/VALIDATION-CLOSURE-2.14.0-20261107.md`,
`verification/DM-BL-011-BYTE-RECOVERY-20261107.md`,
`/root/dm-validation-2140/monitoring/20261106T083522Z/` and
`/root/dm-validation-2140/phase2a-guard-20261107T123250Z/`.

### DM-BL-012 — real-host 2.14.0 `FRESH=1` and OPNsense plugin lifecycle validation: **`CLOSED`** (12 November 2026; operator-accepted `.23` lifecycle)

**Description:** the isolated FreeBSD-jail `fresh` and `fresh-rollback` scenarios passed against the
unchanged 2.14.0 bundle, but their `configd`, `rc.configure_plugins` and `pgrep` stubs prove only
the installer's call boundary. They do not demonstrate real OPNsense plugin registration, real
configd interaction, a real daemon lifecycle after a fresh install, real-host `FRESH=1`, or
whole-tree live core-locale continuity.

The normal 2.13.3 → 2.14.0 upgrade on `.23` and its live successful-install rollback are validated
and are not this item. The outstanding work is specifically the **real-host fresh-install path and
real plugin lifecycle**.

**Attempt on 8 November 2026 — aborted; DM-BL-012 was subsequently CLOSED on 12 November 2026.**
An expressly authorised uninstall and
fresh install of the exact 1,729,177-byte candidate on `.23` passed `CHECK_OK` and `INSTALL_OK`
(64 targets, 10 core locales), and independently passed the 64-target manifest, 11 plugin plus 10
core catalogue recomputation, real plugin/configd/daemon registration and initial disabled-default
checks. Before the planned reboot, a configuration save (not issued by the validation command
stream; the authenticated GUI request origin was not logged) set `enabled=1` and
`monitored_interfaces=lan`. The daemon immediately ran one scan and probed `.252`/`.253` for
services. Email and webhook remained disabled. The daemon was stopped, the state was preserved and
the verified pre-test recovery restored `config.json` `027594eb…`, database `796d28c7…`, 63 targets
and `enabled=0`. The attempt therefore did not test reboot persistence or authenticated UI pages
and does not close this item. Two uninstaller defects were also confirmed: it clears the obsolete
`/tmp/opnsense_menu_cache.xml` instead of `/var/lib/php/tmp/opnsense_menu_cache.xml`, and it calls a
non-existent `php-fpm` rc service. See
`verification/DM-BL-012-FRESH-23-ATTEMPT-20261108.md` and the evidence root
`/root/dm-validation-2140/dm-bl-012-fresh-20261107T202736Z/`.

**Lifecycle closure on `.23` (12 November 2026): CLOSED.** The operator explicitly superseded the
disposable-VM environment gate and authorised uninstall, reinstall, necessary service actions and
one reboot on the existing development host `.23`, replacing VM snapshots with verified backups and
an executable recovery procedure. That is the documented alternative — explicit operator acceptance
of the residual risk — and it is not a pristine-VM validation. The lifecycle run used candidate
`772a6660…` for the menu-cache/php-fpm repair and candidate `3675c7271ad3bbd3a04c325c9f7b03bfea80a19e6ff913c2c3114b78eaa46891`
(1,731,225 bytes) for the residual cleanup. Across the two candidate runs, normal uninstall (exit
0, no `php-fpm`, correct active menu/ACL cache paths), fresh-state reinstall (`CHECK_OK …
predecessor=fresh files=64`, `INSTALL_OK … files=64 core_locales=10`), real plugin registration,
configd and daemon start, 64/64 manifest targets, SQLite integrity, corrected menu-cache
regeneration with all seven Device Monitor entries, and operator attestation that the authenticated
Devices and Settings pages display correctly passed. The `772a6660…` run included the one reboot
with unchanged config/database and `Monitoring DISABLED` at boot; the `3675c7271…` run repeated
uninstall/reinstall and did not repeat the reboot. The 12 November residual repair removed
`/usr/local/etc/inc/devicemonitor_locale.inc` and
`actions_devicemonitor_update.conf` on normal uninstall and proved all 42 payload targets are
removed while unrelated files, configuration and data are preserved. Evidence:
`/root/dm-validation-2140/dm-bl-012-live-23-20261112T191143/` and
`/root/dm-validation-2140/dm-bl-012-residuals-20261112T194900/`.
The latest candidate's uninstall and reinstall were **directly tested**. Reboot persistence is
**reused** from the preceding `772a6660…` candidate: the only delta is uninstall cleanup
(`uninstall.sh` and its tests), which does not alter installed payload, rc wiring, daemon start or
reboot behaviour. Historical monitoring-activation attribution remains **UNKNOWN**: the 8 November
evidence records an un-attributed settings write and one scan, not a confirmed automatic-activation
defect. The documented DM-BL-012 acceptance criteria are real plugin registration and a daemon that
survives reboot with no stub claim (or explicit operator acceptance of the residual risk); no
acceptance criterion requires historical attribution. Uncertainty alone therefore does not add a
release blocker; release remains **NO-GO** on the separately documented DM-BL-013 criteria. DM-BL-011
was **CLOSED** on 13 November 2026 by explicit operator acceptance of the historical byte-evidence
limitation, with no byte-identity claim.

**Closure evidence:** a separately authorised real-host `FRESH=1` test and plugin lifecycle check
on a disposable OPNsense VM, or explicit operator acceptance of the residual risk. The existing jail
evidence must not be described as equivalent. The explicit-acceptance alternative was exercised on
12 November 2026 and is recorded above. The phase had been environment-blocked rather than
code-blocked because the host has no `vmm`, `/dev/vmm` or `vm-bhyve`.

**Evidence:** `verification/FRESH-INSTALL-JAIL-2.14.0-20261106.md`,
`verification/INSTALLER-JAIL-2.14.0-20261106.md`, `verification/VALIDATION-CLOSURE-2.14.0-20261107.md`,
`verification/PHASE3-DISPOSABLE-OPNSENSE-VM-PLAN-20261107.md`,
`verification/DM-BL-012-FRESH-23-ATTEMPT-20261108.md` and `PROJECT_STATE.md`.

### DM-BL-013 — full monitoring lifecycle, HA/CARP and delivery-path validation: **`OPEN`**

**Subcriteria status (consolidated 16 November 2026).** Tracked here so completed work is closed
explicitly and the unresolved obligations stay visible. Historical entries below are preserved
verbatim; this table is the current summary.

| Subcriterion | Status | Evidence |
|---|---|---|
| Authenticated UI rendering on both roles (U1–U8) | **CLOSED** — operator-attested PASS | UI attestation 15 Nov 2026 (`dm-bl-013-ui-attestation-20261115T011305Z`) |
| U9 browser-console checks | **CLOSED** — PASS for the observed workflow, operator capture and originating-conversation visual review; not independent inspection, no continuous monitoring claimed | `dm-bl-013-ui-screenshots-verified-20261115T020427Z`, manifest `13f73a82…` |
| U10 screenshot files and hashes | **CLOSED** — four files and SHA-256 match operator expectations; content observations operator-supplied | same package, manifest `13f73a82…` |
| Daemon-triggered CARP failover webhook, both nodes/legs | **CLOSED as demonstrated** — 4 frames (demotion `.253`/`.252`, return `.252`/`.253`), isolated capture, full restoration | P1 run 2, sealed `c6007d34…` + `ADDENDUM-1-RECONCILIATION.md` |
| Direction-A procedure compliance | **OPEN — deviation D1.** A2 `.252 100→0` was written after A1 transferred the VIP, which `P1-PROCEDURE-REV1.md` §2.5 did not authorise. The four-frame notification result stands as evidence obtained under the deviation; the single-write A1 path remains unproven | reconciliation `PROCEDURE-COMPLIANCE.md` |
| Live identity acceptance | **OPEN — UNVALIDATED by user decision**, explicitly not itself a release blocker; never PASS. Rendering evidence is technical only | identity/Nmap procedure addendum 2 |
| Email delivery (sendmail/SMTP) | **OPEN — unperformed** | — |
| External webhook delivery | **OPEN — unperformed** | — |
| Live ageing transitions | **OPEN — unperformed** (isolated 21/21 is not live acceptance) | ageing-isolated package |
| Targeted Nmap / new-device alert delivery | **OPEN — unperformed** | identity/Nmap procedure REV1 |
| Historical monitoring-activation attribution | **OPEN — UNKNOWN**, not a demonstrated defect | PROJECT_STATE event-path entry |

**Description:** the bounded §9.4 exercise completed two scheduled inventory scans, DMTEST-only
direct service discovery and two loopback SMTP messages from directly invoked PHP helpers. It did
not exercise scheduled daemon-triggered service discovery, full reminder/ageing/CARP behaviour,
daemon-generated notification delivery, exact daemon attribution of the `notified_at` migration,
external SMTP/webhook/AdGuard/Pi-hole delivery or targeted Nmap delivery.

The ageing scope now also includes the confirmed UTC/local `devices.last_seen` inconsistency from
2.14.0 development on 12 November 2026. The defect arose because service verification wrote local
wall time while hostwatch and the freshness/retirement readers used UTC. The candidate now writes
canonical UTC and reads legacy mixed values conservatively without a production database rewrite.
Historical monitoring-activation attribution remains **UNKNOWN** and is not a confirmed
automatic-activation defect. Replacement candidate: 1,735,321 bytes, SHA-256
`ecaecb04814af41479e1b6e614b05a63de9676158870d749ab51b63d5eee87df`; current evidence at
`/root/dm-validation-2140/dm-bl-013-timestamp-r3-20261112/`, with the preceding review and
investigation preserved under `/root/dm-validation-2140/dm-bl-013-timestamp-r2-20261112/` and
`/root/dm-validation-2140/dm-bl-013-timestamp-20261112/`.

The timestamp candidate was installed on production CARP BACKUP `.252` on 13 November 2026
(08:14:54–08:15:06 AEDT). The reviewed installer exited 0 after verifying 63 targets, SQLite
integrity passed, the Device Monitor configuration was unchanged and the node remained BACKUP while
`.253` remained MASTER. Two normal 300-second cycles completed at approximately 08:20 and 08:25
AEDT; 23 rows received new canonical UTC `last_seen` values, 21 during the observation window.
MASTER-only visibility, discovery, identity/new-device alerting, targeted Nmap and notification
delivery remain unexercised. Evidence:
`/root/dm-validation-2140/dm-bl-013-prod-252-install-20261112T211341Z/`, sealed at
`63d740365b2be61e4c0fe9a6c8688d3a33269f85a13ea1d886f4a5c37c0d2315`.

HA-role visibility is a later source candidate, installed on testbed `.23` on 13 November 2026 but
not on production: 1,795,230 bytes, SHA-256
`e7dcb7f88ec8f98ca4455542f2106416e2447740c95c818ff2cfdd31d4ef3124`. It reuses the
existing `getcarpstatus` API for Devices and Settings, distinguishes detected role from effective
mode, names the exact BACKUP-gated activities, leaves manual scans and scheduled port discovery out
of that list, and clears stale status on refresh failure. The reviewed correction parses the actual
daemon scan-log format with a bounded reverse lookup, distinguishes missing history from unreadable
history and API fetch failure, and reports observation continuation only for the confirmed detector-
failure state. The checked-in validation is local to `.23` source and does not exercise browser
rendering or a live CARP role change; the available host lacked a browser, so the agent captured no
screenshots. An operator-supplied isolated-fixture review on 13 November 2026 reported clear MASTER
and BACKUP notices, distinct fetch-failure and backend-unavailable messages, correct wrapping for
German Settings and English Devices at narrow widths, and a simulated MASTER-to-BACKUP transition
ending in the correct BACKUP view. That is fixture-only operator attestation, not live CARP,
production rendering or full-matrix acceptance. The earlier HA builds `2dab1385…`, `709288cd…`,
`e789fb96…` and `f51f1adf…` and all earlier evidence remain preserved.

The `.23` installation returned `INSTALL_OK … files=63 … pruned=0
backup=/var/backups/devicemonitor/install-v214.lulG0h daemon_restarted=1 unchanged=36 repaired=0`;
all 63 installed rows verified, configuration (`027594eb…`), database (`796d28c7…`) and OPNsense
configuration (`e86a7058…`) were unchanged, monitoring stayed disabled and no reboot or CARP change
occurred. Evidence: `/root/dm-validation-2140/dm-bl-013-ha-deploy-23-20261112T234608Z/`.

A later uncommitted compact-summary revision adds the collapsed Show details/Hide details notice, the read-only monitoring-enabled state, separate HA-pause summary and role/unavailable warnings. It is source-only and is not part of the installed `e7dcb7f8…3124` candidate.

A further source-only automatic-relevance revision makes HA content conditional on a positive
non-HA result from the existing detector: readable `ifconfig` and `/conf/config.xml`, at least one
resolved monitored interface, no CARP VIP, no CARP state on monitored devices and no explicit role
override. Confirmed non-HA hides HA-specific notice content but retains node identity, monitoring
state and the expanded last successful scan. The HA / CARP tab remains accessible, explains that no
CARP configuration was detected, disables CARP awareness and failover notification without changing
saved values, and leaves the role override editable. Unknown detector/API states retain warnings and
never become non-HA. CARP awareness disabled remains distinct from detected role/effective mode.
Focused API/UI, non-HA, integration, catalogue, CI, fixture and diff checks passed. The updated
fixture is sealed at `/root/dm-validation-2140/dm-bl-013-ha-relevance-fixture-20261113T004225Z/`
(373,094 bytes, SHA-256 `687cc9f2…fbe5`). Language acceptance remains price-gated and browser visual
acceptance of this revision is pending. This revision is not installed; DM-BL-013 remains **OPEN**
and historical monitoring-activation attribution remains **UNKNOWN**.

A further source-only review correction addresses the browser findings against the compact-line
fixture. Confirmed non-HA expanded details now hide the detected/effective role facts and use the
node-local ownership wording rather than a CARP-peer statement; last-scan information remains. The
Settings HA / CARP row is now `HA policy permission` with `permitted` / `paused by HA policy` values,
distinguishing policy permission from actual monitoring activity. The fixture's role-fact leakage
came from `display:flex` overriding its `hidden` attribute; an explicit `[hidden]` rule now prevents
that, and the fixture tabs wrap at narrow widths. The real Settings CSS was inspected and left
unchanged because the clipping was fixture-only; the live view uses Bootstrap `nav-tabs` without that
fixture overflow rule. Affected checks pass. Updated fixture archive: 374,294 bytes, SHA-256
`40b2e6b3548b0d664665fa5021989ac660d9613bd72d99c8f741b23facff450b`; the prior `7376a65a…acbab`
archive is preserved. Language acceptance remains price-gated, browser acceptance remains pending,
and this revision is not installed. DM-BL-013 remains **OPEN** and historical activation
attribution remains **UNKNOWN**.

A subsequent source-only compact-line revision removes the repeated collapsed content: the notice now
shows `node · role · Monitoring enabled` on one line (the role is omitted for confirmed non-HA), adds
the short `Some activities paused` indicator for BACKUP, and keeps unavailable/override warnings
visible while collapsed. Expanded details contain detected/effective roles, local-data ownership,
paused/continuing activities and the last scan once each; the duplicate monitoring note and generic
`No activities paused` text were removed. The API supplies a timezone label only from a valid
configured OPNsense timezone and the UI otherwise says `Timezone unavailable`. PHP/JS, translation,
CI, catalogue, fixture, inline-script and diff checks passed. The fixture was resealed after inline
JavaScript syntax validation was added to its static checker: 373,818 bytes, SHA-256
`7376a65a3a0640496926461fdbb76272421c9839ed9e6d630e0aac77d91acbab`. Only the checker and recorded
log changed; the fixture HTML remains `9dfa112d…a18fa`. The previous `c34d3414…1c88` archive is
preserved under `.../preserved-c34d3414/`. Language acceptance remains price-gated and browser
acceptance of this revision is pending. The revision is not installed; DM-BL-013 remains **OPEN**
and historical monitoring-activation attribution remains **UNKNOWN**.

The operator supplied a screenshot review of the R5 isolated fixture (`374,294` bytes, SHA-256
`40b2e6b3548b0d664665fa5021989ac660d9613bd72d99c8f741b23facff450b`) on 13 November 2026. The
sampled review passed for compact and expanded MASTER and BACKUP, confirmed non-HA with monitoring
disabled, an active role override, narrow-screen tab wrapping and the simulated
MASTER-to-fetch-failure transition. These are operator attestations of isolated simulated states,
not agent-observed browser results. No exact observation timestamp was supplied and none is
inferred. The review does not establish the full state matrix, keyboard acceptance, live CARP, a
live role change, production rendering, MASTER-only operation or delivery paths.

The final source-only candidate was rebuilt twice with separate stage, output and allow-list paths
and produced byte-identical results: 1,827,998 bytes, SHA-256
`2d2c0a884ef169a4f9609a84f2860918bd7fc8432dfb23be52c4b9d6f35d8874`, 60 archive members. Review
found the first final build still depended on checkout umask and a transient `0600` manifest
permission; the builder now normalises `0644`/`0755` from the Git index and the determinism test
varies both timestamps and worktree modes. The regenerated runtime manifest plus release-input pins
verify against the current sources. Evidence:
`/root/dm-validation-2140/dm-bl-013-final-20261113T013258Z/`. The superseded installed `.23`
payload `e7dcb7f8…3124` and all earlier candidates and evidence remain preserved. This final
candidate is not installed. The premium price gate deferred language acceptance at finalisation;
no bypass was used. DM-BL-013 remains **OPEN**, and historical monitoring-activation attribution
remains **UNKNOWN**.

The superseding reviewed keyboard candidate was
`2f69a69751755891578fb53a3d15f27be1200798b89a0f23ad24137d75d5ef33` (1,850,531 bytes). It was
deployed to `.23` with a clean preflight and a fresh installer backup. All 63
installed hashes matched, SQLite integrity remained `ok`, and the configuration, database and
`/conf/config.xml` stayed byte-identical. The saved role override remained `auto`, monitoring and
notification gates remained disabled, and the services stayed healthy; no reboot occurred. The
operator subsequently confirmed, without an observation timestamp being recorded, that Space and
Enter open the deployed dropdown, Escape closes it, and `Automatic (use CARP role)` remains
selected.
This closes only the dropdown keyboard acceptance check. DM-BL-013 remains **OPEN** for production
MASTER, HA-transition and delivery-path validation, and historical monitoring-activation attribution
remains **UNKNOWN**.

**Production HA transition run (14 November 2026, webhook-only, controlled):** an operator-authorised
run on the live CARP pair `.253` (MASTER) / `.252` (BACKUP), running the installed `2f69a697…`
candidate, exercised the plan's control, demotion, return and stable-cycle legs with notifications
redirected to a node-local capture listener (`http://192.168.20.253:18013/`) and `email_enabled=0`.
**Reconciled counts (addendum 1, after a read-only audit of the captured frames):** control **0**
frames; demotion **exactly 1** frame, from `.252` (`role MASTER`, `observing true`, 16:06:20 AEDT);
return **exactly 1** frame, from `.252` (`role BACKUP`, 16:11:14 AEDT), with **no `.253` frame**; stable
cycle **0** frames over fresh 300 s cycles on both nodes. The whole run produced **2** frames, so the
return-leg “two frames, one from each node” criterion and the “three frames total” expectation are
**NOT MET**; the one-frame demotion criterion, stable-cycle suppression, control case, settings
isolation and byte-identical restore are **MET**. Email remains **NOT EXERCISED**.

The sealed `ACCEPTANCE-REPORT.md` previously recorded “return: exactly 2 frames (both from `.252`)”,
an internal inconsistency; it is preserved unmodified and corrected by
`ADDENDUM-1-RECONCILIATION.md` (new manifest), which also restates the accepted frames and their
payloads.

**Cause of the missing `.253` frame (facts):** the sampler reads only `carp:` lines once per 300 s
cycle (`parse_carp_roles` `:3472`, `detect_carp_role` `:3509`, called from `:9499`); the transition
is `read_carp_role()` (`:3633`) versus the fresh sample, and the notification gate is
`config['ha_notify_failover'] and previous_carp_role` (`:9546`). `carp_set_status.php disable` set
`net.inet.carp.allow=0`, so `.253` had no CARP state for 16:06:07–16:09:40; no cycle ran in that
window, so the persisted `carp_role` stayed `MASTER`; `enable` made `.253` MASTER again within one
second (`BACKUP → MASTER (preempting)`), so its next cycle saw no change. Classification:
**unsuitable test method plus an incorrect acceptance expectation**, not a demonstrated
implementation defect. Open hypotheses (not defects): the empty-`previous` first-observation guard
may suppress `.253`'s first real failover after a fresh install; whether any failover mechanism can
produce a `.253` demotion notification is untested; the payload has no effective `previous` field.

**Transition count (corrected):** only **one** operator-authorised transition and return was executed
(`carp_set_status.php disable` 16:06:07 / `enable` 16:09:36). Three **additional, unintended** CARP
handover pairs occurred before it during recovery and diagnosis — 15:45/15:48 (OPNsense CARP event
hook re-applied demotion during the restore attempts), 15:50:59/15:51:01 (the
`carp_set_status.php maintenance` toggle itself), and 15:58:57/15:59:00 (re-adding the VIP alias).
The plan's `ifconfig … carp demote 1` variant is rejected by this build (`carp: bad value`) and a
transient `sysctl net.inet.carp.demotion=1` did not hand over in 8 minutes.

**No-production-delivery evidence:** during every window in which notification gates were active the
effective `webhook_url` was the node-local capture URL (`ntfy.sh` count 0 in each config) and
`email_enabled` was `0`; the 15:45–15:59 handovers therefore occurred with the first test settings in
force, not with production destinations configured. Limits: `.253` never entered the failover send
path so its own skip is not directly logged; no listener was armed on `.252` during 15:28–15:54; the
carrier side cannot be inspected. No production delivery is claimed on the basis of configuration
isolation alone.

**configd blocker on `.253` — diagnosed, withdrawn as a node fault (15 November 2026):** a P1
execution on 14 November 2026 stopped before any CARP transition because the executor's settings
apply call used `vip.configure`, which configd reported as missing. Read-only diagnosis established
the action is registered as **`interface vip configure`** (`actions_interface.conf:238`, topic
`interface` + section `vip.configure`); the stock Virtual IPs page applies it via
`VipSettingsController::reconfigureAction()` → `Backend::configdRun('interface vip configure')`
(`Interface/vip.volt:109` → `/api/interfaces/vip_settings/reconfigure`). `configd actions` lists it
on both nodes (564 / 551 actions); the audit records `not found for user root`, never
`action denied`; package `opnsense 26.7.8_2`, `configd.py`, `configd_ctl.py`, `processhandler.py`,
`Backend.php`, `VipSettingsController.php`, `reconfigure_vips.php`, `configd.conf` and
`actions_interface.conf` are byte-identical on `.253` and `.252`. The earlier "configd
registration/startup issue on `.253`" is **withdrawn**; the cause was the executor's own action
name. Nothing executed: the audit shows only `not found` for `vip.configure`, `system.list`,
`interfaces.list`, `unbound.start` and the other invented names, with no `action allowed` line for
them; no config, CARP state or service changed. The run's XML comparison also had a defect (it never
excluded `/opnsense/revision`); re-running with a corrected order-preserving comparator confirms both
configs unchanged apart from documented metadata, and **restoration is confirmed**. Correct exclusion
totals are 128 (`.253`) / 109 (`.252`), not 130 / 111. No remedy was implemented. Proposed minimal
remedy: use the page's Apply path (or `configctl interface vip configure` inside an authorised
window), then re-approve P1. Evidence:
`/root/dm-validation-2140/dm-bl-013-configd-diagnosis-20261115T0815Z/ROOT-CAUSE-REPORT.md`.

**P1 run 2 — CARP failover webhook proven on both nodes; direction-A procedure deviation
(15 November 2026):** re-executed with the corrected apply action `interface vip configure`. **Four
frames, one per node per leg:** demotion `.253` BACKUP at `2026-11-14T23:59:57Z`
(`2026-11-15T10:59:57+11:00` AEDT) and `.252` MASTER at `2026-11-15T00:00:02Z`
(`11:00:02+11:00`); return `.252` BACKUP at `2026-11-15T00:09:50Z` (`11:09:50+11:00`) and `.253`
MASTER at `2026-11-15T00:10:28Z` (`11:10:28+11:00`); stable window 0 further frames. The `.253`
return-leg frame that the 14 November disabled-CARP method could never produce is now **proven**.
The B1 tie (`0/0`) transferred nothing and was not treated as a transfer; settled ownership was
assessed only after both final values were effective and settled inside the 30 s operational limit.
Restoration verified: saved `advskew` `0`/`100`, `.253` MASTER / `.252` BACKUP, VIP `.254` on
`.253`, tunables `1/1/0/240/0`, boot and daemons unchanged, `config.json` byte-identical,
`/conf/config.xml` ordered-equivalent apart from documented metadata (0 VIP differences), listener
removed, mail queue read-only empty on `.253` / no MTA on `.252`.

**Procedure deviation D1 (recorded, not excused):** the executed direction A continued with the A2
write (`.252 advskew 100 → 0`) **after** A1 had already transferred the VIP (`.252` became MASTER at
`2026-11-15T10:59:28+11:00`, six seconds before A2 was saved). The procedure in force
(`P1-PROCEDURE-REV1.md` §2.5, sealed `cb714841…`) authorises A2 only in the "A1 does not transfer"
branch; after an A1 transfer it requires a **single revert of `.253` to `0`** before a §2.3.1 settle
check. Continuing past A1 was **not authorised**. The four-frame notification evidence stands (it is
genuine, isolated and correctly attributed), but the run is recorded as **notification acceptance
met by evidence obtained under a procedure deviation**, not as a clean procedural qualification; the
single-write A1 variant remains unproven. No stop condition was hit and restoration is unaffected.
Frame payload `timestamp` fields are node-local AEDT without an offset
(`scan_network.py:3667`), while the listener recorded UTC; both zones are recorded in the
reconciliation. Notification acceptance and procedure compliance are recorded separately: the former is met by evidence, the latter is not met for direction A.

Email delivery remains **NOT EXERCISED**; identity/new-device alerts, targeted Nmap, ageing,
external delivery and authenticated UI checks remain outstanding. A bounded plan for those is at
`/root/dm-validation-2140/dm-bl-013-p1-run2-reconciliation-20261115T0026Z/REMAINING-CRITERIA-PLAN.md`.

Evidence: run report (sealed `c6007d34…`) plus addendum `RUN-REPORT-ADDENDUM-1.md`, and the
reconciliation package `/root/dm-validation-2140/dm-bl-013-p1-run2-reconciliation-20261115T0026Z/`
(`PROCEDURE-COMPLIANCE.md`, `evidence/CARP-AND-FRAME-TIMELINE.md`).

**Read-only acceptance checks (15 November 2026):** roles/health revalidated without a swap —
`.253` was MASTER (advskew 0, VIP, `allow/preempt/demotion 1/1/0`) and `.252` BACKUP (advskew 100)
at `2026-11-15T00:33:41Z` / `2026-11-15T11:33:41+11:00`, both daemons healthy and both GUIs
returning 200 on their own addresses. **UI checks are PENDING**: both APIs redirect to the login
page (302), so an authenticated operator session is required; exact steps and the per-node
acceptance grid are in
`/root/dm-validation-2140/dm-bl-013-readonly-checks-20261115T003341Z/UI-CHECK-PROCEDURE.md`. No
operator result is claimed until returned. **Ageing census (read-only)**: thresholds
`SERVICE_UNKNOWN_AFTER_DAYS=7` and `SERVICE_RETIRE_AFTER_DAYS=30`; at
`2026-11-15T00:34Z`, `.253` had 76 available / 50 unavailable / 0 unknown and `.252` 71 / 28 /
11 unknown; exact implementation SQL found **0** rows that would age and **0** retirement
candidates on either node, with 57/54 fresh hosts so retirement was not refused. Current state is
consistent with the code, including standby ageing on `.252`; boundary-crossing transitions remain
**UNTESTED** live (no row crossed either boundary, `.253` has no historic `unknown` history, and the
`.252` 11 `unknown` rows predate this pass with mixed provenance). Unit tests cover the boundary
paths but are not counted as live acceptance. Evidence:
`/root/dm-validation-2140/dm-bl-013-readonly-checks-20261115T003341Z/` (`AGEING-CENSUS.md`,
`ROLES-HEALTH.md`, `UI-CHECK-PROCEDURE.md`, JSON census files).

**Isolated ageing validation (15 November 2026, disposable copies only):** the installed
`scan_network.py` (`cd82a60c…`) was exercised against consistent SQLite snapshots of both nodes
(taken with the online backup API from `mode=ro` connections; `integrity_check ok`), with every
path constant rebound to `work/`, `sqlite3.connect`/`builtins.open` guarded, outbound helpers
raised-on-call (blocked-call counter `[]`), and a fixed test-only `now` injected — the system clock
and installed files were not changed. **21/21 cases passed on each node**: `unavailable` > 7 d →
`unknown` with `miss_count=0` and exactly one history-only `SERVICE_CHANGED` event; host > 30 d
retired with its held alert removed; the no-fresh-host refusal guard (ageing still applied);
rows without a `devices` record retained; exact-threshold equality **not** aged/retired (strict
`<`) with ±1 s boundaries correct; DST cut-off picks the earlier UTC value, ambiguous wall time has
two fold candidates; the ageing core has no MASTER/BACKUP branch and the standby wrapper applies
the same logic. **Labelled isolated integration validation, not live daemon acceptance** — the
function was called directly with an injected clock; no daemon cycle produced these transitions,
and the `.253` baseline case aged 23 pre-existing rows only because the fixed clock was 12 h ahead
of the snapshot (under real time those rows are inside the window; live census showed 0 candidates).
Unit-test coverage remains separate and is not counted as acceptance. Authenticated UI checks stay
pending operator evidence. Evidence:
`/root/dm-validation-2140/dm-bl-013-ageing-isolated-20261115T003817Z/ISOLATED-AGEING-VALIDATION.md`
(sealed `a425b893…`).

**Operator UI attestation — Devices and HA/CARP Settings (15 November 2026):** the operator
supplied screenshots (described, not delivered as files) showing both nodes rendering Devices and
the HA/CARP Settings page with correct **detected and effective roles** (`.253` MASTER, `.252`
BACKUP), **CARP awareness enabled**, **Automatic** override, `.253` **monitoring permitted** and
`.252` **activities paused by HA policy**; device counts `.253` 75 total / 39 online and `.252` 63
total / 39 online. These are recorded as **PASS** for page rendering, detected/effective roles,
awareness, override, monitoring state and counts. **U9 is now PASS for the observed workflow
(15 November 2026)**: operator browser-console capture, visually reviewed in the originating
ChatGPT conversation, with Errors and Warnings enabled and no text filter, showed **no visible
console messages** on `.253` Devices (MASTER), `.253` Settings -> HA/CARP (MASTER/MASTER,
permitted), `.252` Devices (BACKUP, activities paused) and `.252` Settings -> HA/CARP
(BACKUP/BACKUP, paused by HA policy); Settings reload returns to Monitoring, so HA/CARP was opened
after the reload and the populated status table captured without another reload. This is
**operator-attested, not independent inspection**, and covers those four visits as observed — not
continuous browsing or monitoring; Info/Debug-level messages were outside the filter scope and no
console transcript, console image or browser/version detail was retained. **U10 is now PASS
(15 November 2026)**: the four operator-named originals
match all four recorded SHA-256 expectations, with packaged, extracted and archived copies
internally consistent and PNG dimensions consistent with the mapped page types, and the operator
supplied the per-file content observations (`010729` .253 Devices: MASTER, monitoring enabled,
75/39; `010753` .253 Settings: Automatic, MASTER/MASTER, permitted, VIP MASTER; `010832` .252
Devices: BACKUP, activities paused, 63/39; `010851` .252 Settings: Automatic, BACKUP/BACKUP, paused
by HA policy, VIP BACKUP). U10 is therefore **operator-content-attested, not independently
inspected**: this close-out used shell/text tools only and no image viewer or OCR is available, so
no visual or content confirmation was performed by the agent; page-to-file mapping is likewise the
operator's statement. New sealed package:
`/root/dm-validation-2140/dm-bl-013-ui-screenshots-verified-20261115T020427Z/` (12/12 files,
0 problems; manifest `13f73a82…`), including `U9-CONSOLE-CHECKS-OPERATOR.md` and
`CONTENT-OBSERVATIONS-OPERATOR.md`. The earlier attestation seal (`f4f88156…`) and supplement seal
(`3aaf083f…`) verify unchanged. Recorded as an observation only: `.252` shows **Failed 5/5** scan statuses — the last
six scheduled cycles on `.252` all logged `Scan completed successfully`, so the label is not a
scheduled-cycle outcome; a log search found a plausible shape-match from 2026-11-06 targeted Nmap
scans `permanently failed after 5 attempts`, but the attribution is a **hypothesis** and the cause is
**unverified**. No scan was run and no setting changed. Evidence:
`/root/dm-validation-2140/dm-bl-013-ui-attestation-20261115T011305Z/` (`OPERATOR-ATTESTATION.md`,
`UI-ACCEPTANCE-CORRECTED.md`).

**Next bounded work (not executed):** (P1) a precondition test that leaves `.253` with a readable
`carp:` line while the peer holds the VIP, to prove the `.253` notification leg — requires new
authorisation because it changes CARP state; (P2) a documentation-only correction to the plan stating
that removing CARP on `.253` makes it unobserving; (P3) review of the empty-`previous` guard (no code
change authorised). Identity/new-device alerts, targeted Nmap, ageing, external email/webhook
delivery and authenticated Devices/Settings UI checks on both roles also remain outstanding.

Evidence: `/root/dm-validation-2140/dm-bl-013-transition-exec-20261114T041703Z/ACCEPTANCE-REPORT.md`
(sealed) and its `ADDENDUM-1-RECONCILIATION.md` (read-only audit; addendum manifest
`b404e9c9…b1ec`, 82/82 files; node copy of the frame log `sha256 e43be493…32437`), plus the
preserved backups `/root/dm-bl-013-pretest/` on both nodes.

**Closure evidence:** separately authorised tests on a disposable single OPNsense VM for the
single-host paths and an isolated two-node CARP/pfsync pair for HA; external delivery requires a
separately approved lab endpoint, or explicit operator acceptance of the residual risk. No further
live execution is authorised by the HA-visibility task. This is a publication blocker under the revised objective.
Single-host success will not prove HA, and HA success will not prove an external provider path.

**Evidence:** `verification/monitoring-validation/EXECUTION-20261106.md`,
`verification/monitoring-validation/PREFLIGHT-20261106.md` and
`verification/VALIDATION-CLOSURE-2.14.0-20261107.md`.

**Source-only correction — identity-conflict alerts restored to webhook-only (15 November 2026):**
commit `a12ede8` had re-added an identity-conflict email leg without a recorded decision,
contradicting `DECISIONS.md` 36. Option A withdrew it: `should_send_identity_mail()`,
`send_identity_mail()` and `notify_identity_mail.php` are removed; the "Also email identity
conflict alerts" checkbox, its JS load/save wiring and the catalogue strings exclusive to it are
removed; `identity_email_enabled` remains a stored preference that `ConfigController` preserves
untouched; the identity webhook keeps its gates, high-severity filter, HA suppression and
`notified_at`-on-success-only semantics. New-device email/webhook, scan-result email and targeted
Nmap were deliberately left unchanged; Nmap's dependence on `email_enabled`/`email_to` is
implementation coupling, not a recorded requirement, and is documented separately in the
identity/Nmap procedure. Manifest drops from 42 to 41 rows and the installer guards, pinned inputs
and runtime-manifest digests were regenerated with the shipped tooling. `install-unattended.sh
--check` on `.23` reports `CHECK_OK … files=62 … prunable=1` with the prune plan naming only
`notify_identity_mail.php`, so upgrades and repair installs retire the helper through the existing
Decision 61/62 record-diff rule with no new mechanism. **Nothing is deployed**: expected
identity-conflict email count after the fix is **zero**, the identity/Nmap and live-ageing criteria
remain **UNTESTED**, D1 remains recorded, and publication stays **NO-GO**.

## Deployment verification notes
**v2.14.0 PUBLISHED (16 November 2026).** Tag `v2.14.0` (annotated object
`da9c3b698634f6c1a726cca97f026d9f171444f9`) targets the approved commit
`ee38d070ae7980edbabf822b7540c9e795f7f6f6`. Release: https://github.com/apg19590209/opnsense-devicemonitor/releases/tag/v2.14.0; non-draft, non-prerelease. Assets:
`dm-v2.14.0-runtime.tar.gz` 1,792,158 bytes, SHA-256
`abab6ad7a46d2a12d9176d6752421fde88a7460395df167d096055a4e00e0207`, and `SHA256SUMS`. The published
archive was re-downloaded and matches the approved candidate byte-for-byte; the release body equals
the prepared notes. DM-BL-010's publication obligation is discharged — the header fix is now in a
published release. Issue #5 received a factual reply
(https://github.com/apg19590209/opnsense-devicemonitor/issues/5#issuecomment-6912981224) and
remains **OPEN** pending the reporter's functional confirmation; the reply states the warnings were
harmless and that no reinstall is needed for them.

**Release limitations accepted by the user; none of these tests passed.** Daemon email delivery,
external webhook delivery, targeted Nmap / new-device delivery and live ageing transitions remain
**unperformed**; the isolated ageing 21/21 result is not live acceptance. **Deviation D1** is
retained: the four-frame CARP failover webhook result is genuine evidence obtained under a procedure
deviation, and the single-write A1 path remains unproven. Historical monitoring-activation
attribution remains **UNKNOWN** and cannot be established from existing evidence. Live identity
acceptance remains **UNVALIDATED** under the user's standing acceptance.

**Dutch deferral installed on `.23` (16 November 2026):** candidate
`dm-v2.14.0-runtime.tar.gz` 1,792,158 bytes, SHA-256 `c620e892a9cac0fdb126e7d64b7359a21e636e3b68d0488ac0d2c2d724abf205`,
installed under a fail-closed guard (`--check` `files=60 core_locales=9 prunable=1`). Result:
`INSTALL_OK version=2.14.0 files=60 core_locales=9 pruned=1 retired_core=1 unchanged=60 repaired=0
daemon_restarted=1`; installer backup `/var/backups/devicemonitor/install-v214.ozDITV`. Both Dutch
runtime artefacts are gone (sidecar pruned, plugin-created core catalogue retired with a rollback copy);
all 41 manifest targets and the ten shipped sidecar catalogues verify; `config.json` (`027594eb…`) and
`/conf/config.xml` (`e86a7058…`) are byte-identical; monitoring and every channel remain disabled;
`devices.db` integrity `ok`. Residual `/usr/local/opnsense/mvc/app/languages/nl_NL/LC_MESSAGES/` holds
four pre-existing manual `.pre-*` backups from earlier work, not runtime artefacts. The release
language requirement is corrected to ten shipped locales / eight translated runtime languages, the CI
runtime matrix no longer includes `nl_NL`, and historical nine-language results are preserved as
history. Live identity acceptance remains **UNVALIDATED**; D1 preserved; DM-BL-013 **OPEN**;
publication **NO-GO**. Evidence: `/root/dm-validation-2140/dm-bl-013-dutch-deferral-install-23-20261116T083540Z/` (sealed 12/12).

**Dutch deferral implemented in source/package (16 November 2026; candidate built, NOT installed):**
`release/supported-locales.sh` is now the single shipped-locale policy (`en_US cs_CZ de_DE fr_FR es_ES
it_IT pt_BR ru_RU ja_JP zh_CN`; `nl_NL` excluded) and is sourced by both `install-unattended.sh` and
`release/build-bundle.sh`, which no longer uses `find src -name '*.po'`. The Dutch `.po` is retained
unchanged in the repository as deferred source (`e3e09a11…`). Installer target counts are derived from
the payload (41 rows + 10 sidecars + 9 core catalogues = **60**, 61 fresh) instead of hardcoded.
Upgrade/repair retirement: the sidecar is removed by the existing Decision 61/62 prune
(`prunable=1`); the plugin-created core catalogue is retired only when `core-locale/<lang>.state`
records `pristine=absent` **and** the file still matches the recorded installed digest — otherwise it
is retained and reported (`NOTICE: retained core catalogue …`). Package-owned or independently
modified `OPNsense.mo` files are never deleted. New `tests/test_dutch_deferral.py` (11 cases) covers
policy, source retention, no-discovery, derived counts, manifest absence and fresh/upgrade/repair
behaviour including both retention paths. Language acceptance over the eight supported translated
languages now reports `LANGUAGE_ACCEPTANCE=PASS languages=8 gaps=0 engine=runtime failures=0`
(Dutch rendering remains technical evidence only). Candidate: `/root/dm-backups/dm-bl-013-dutch-deferral-candidate-20261116T083000Z/dm-v2.14.0-runtime.tar.gz`,
1,792,158 bytes, SHA-256 `c620e892a9cac0fdb126e7d64b7359a21e636e3b68d0488ac0d2c2d724abf205`,
59 members, deterministic rebuild identical; `--check` on `.23` reports
`files=60 core_locales=9 prunable=1`. Nothing deployed; DM-BL-013 remains **OPEN**; publication
**NO-GO**; D1 preserved; live identity acceptance remains **UNVALIDATED**.

**Dutch disposition superseded by governing operator intent (16 November 2026, documentation only):**
the user has confirmed the governing requirement — **the Dutch plugin translation must not become
available until Dutch is selectable in OPNsense**, and successful catalogue rendering does not satisfy
that condition. The recorded history is preserved unchanged: DM-BL-008a remains **closed as dropped
(on withdrawal) for the current release** on 28 September 2026 (commit `c93085d`), and the entry's
"the `nl_NL` catalogue stays in the eleven-catalogue payload" scope note is superseded by this
intent. It is **not** re-recorded as "closed by platform dependency". Read together with the O2/W2
records in `verification/locales/deferrals.md`, the current delivery contradicts the intent.

*Discrepancy (exact).* Dutch is still delivered: `install-unattended.sh:153` lists `nl_NL` in the
compile loop and installs `/usr/local/opnsense/mvc/app/languages/nl_NL/LC_MESSAGES/devicemonitor.mo`;
because OPNsense ships no Dutch core catalogue (`nl_NL` is not in `get_locale_list()`,
`/usr/local/etc/inc/system.inc:255-285`), `install-unattended.sh:163-172` runs
`merge-opnsense-catalog.sh --plugin-only` and installs
`/usr/local/share/locale/nl_NL/LC_MESSAGES/OPNsense.mo` (installed `555e23b8…`,
`pkg which` → not owned). `/var/backups/devicemonitor/core-locale/nl_NL.state` records
`pristine=absent`, so the core file is plugin-created and safe to delete. The archive carries the
catalogue through `src/**/*.po` in the bundle allow-list, not through a manifest row.

*Retained evidence, not support.* The `nl_NL` runtime result (10/10 pages, 528 keys, 0 failures,
`LANGUAGE_ACCEPTANCE=PASS languages=1 gaps=1 failures=0`) is **technical rendering evidence only**.
**Release language requirement (corrected 16 November 2026 by operator decision).** The release
ships **ten locales** (`en_US cs_CZ de_DE fr_FR es_ES it_IT pt_BR ru_RU ja_JP zh_CN`) and requires
**eight translated languages** to render through the production
Phalcon/Volt/ViewTranslator path — `de_DE fr_FR es_ES it_IT pt_BR ru_RU ja_JP zh_CN` — with
`en_US` as the reference set and `cs_CZ` installed and checked as part of the shipped ten.
**Dutch (`nl_NL`) is source-only and deferred under DM-BL-008a**: it is not shipped, not selectable,
not a release language, and its rendering evidence remains technical only. The earlier "nine-language"
wording described the set that included Dutch and is superseded; historical runs that reported nine
languages remain valid history of that period.

*Smallest next fix (documented, not executed).* Remove `nl_NL` from the installer locale list and
from the bundle's catalogue set so it is neither compiled nor installed; keep the `.po` in the
repository as deferred source; keep the `--plugin-only` merge fallback for genuinely core-less
locales; and let the existing install machinery delete the plugin-created core file on upgrade
(`pristine=absent`), while **never** touching package-owned `OPNsense.mo` files. Documentation now
states Dutch as deferred. Re-open only if OPNsense core offers `nl_NL`.

**Core-catalogue "drift" corrected in the records — expected core-domain wording (16 November 2026,
documentation only):** the seven reported entries are message ids carried by both the plugin and the
OPNsense core catalogues with different wording; Decision 35's core-first merge preserves the core wording
by design, so they are **expected core-domain wording differences**, not missing translations or
unresolved product drift. `de_DE State`→`Zustand`, `es_ES Language`→`Lenguaje`, `es_ES Virtual IP`→`Virtual IP`,
`ru_RU Unknown`→`Неизвестный`, `ru_RU Virtual IP`→`Виртуальный IP-адрес`, `ru_RU minutes`→`мин`,
`ja_JP State`→`ステート`, `zh_CN Virtual IP`→`虚拟IP` in the core (`lang.query()`) domain; the sidecar
(`devicemonitor_t()`) domain keeps the plugin values. Canonical invocation
`python3 tests/test_language_acceptance.py --engine runtime --views <abs source views>` (default
`--installed-po /usr/local/opnsense/mvc/app/languages`) returns
`LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0`, with the seven as warnings. The
earlier fatal classification came from pointing `--installed-po` at the source tree, which ships no
compiled `.mo`, so plugin coverage was unknown. These seven are **removed from the release-blocker list**
under Decision 35. `--strict` findings remain supplemental diagnostics; `nl_NL` selectability and any
other language defect are **not waived**. Evidence (sealed): `/root/dm-validation-2140/dm-bl-013-catalogue-drift-correction-20261116T072923Z/CORRECTION-ADDENDUM.md`. No catalogue
edit, package regeneration, installation, commit, push or publication.

**Ordering-fix candidate installed on `.23` (16 November 2026):**
`dm-v2.14.0-runtime.tar.gz` 1,841,827 bytes, SHA-256 `93c673d9fe87b767fb809593ad366bb4e09d82fd507607216c27f57db5810ad6`, installed under full
preflight and the single conditional guard; `--check` reported `files=62 prunable=0` before and
installation returned `INSTALL_OK version=2.14.0 files=62 core_locales=10 pruned=0
unchanged=61 repaired=0 daemon_restarted=1`. All 41 manifest targets hash-match; the installed
scanner is `ecd31899abb6365960d48c8b347c27e217f8d0641512e062b715ee208d3d7090`; the retired
identity-email helper remains absent and is absent from the new 64-line install record.
`config.json` (`027594eb…`) and `/conf/config.xml` (`e86a7058…`) are byte-identical; monitoring
stayed disabled and every channel stayed off; `devices.db` and the hostwatch DB both passed
`integrity_check` and row counts were unchanged (26 devices / 2 identity events / 0 Nmap history);
no scan, Nmap, email or webhook occurred. Installer backup:
`/var/backups/devicemonitor/install-v214.wH9DgM`. Evidence directory (sealed 13/13):
`/root/dm-validation-2140/dm-bl-013-identity-event-order-install-23-20261115T222532Z/`. **Live identity acceptance remains UNVALIDATED** by user decision and is never recorded as
PASS. Email/webhook/external delivery, live ageing, direction-A procedure compliance (D1) and the
five-language core catalogue drift remain open. DM-BL-013 remains **OPEN**; publication **NO-GO**.

**Ordering-fix candidate prepared (15 November 2026, not installed):**
`/root/dm-backups/dm-bl-013-identity-event-order-candidate-20261115T111500Z/dm-v2.14.0-runtime.tar.gz`
— 1,841,827 bytes, SHA-256 `93c673d9fe87b767fb809593ad366bb4e09d82fd507607216c27f57db5810ad6`,
59 members, 41 manifest rows, deterministic rebuild identical, installed scanner would be
`ecd31899…`. Regression extended with a `full_scan`-level case that delivers the cycle's own
rotation event and fails against a late-snapshot copy of the scanner (verified). `--check` on `.23`:
`files=62 prunable=0` (the identity-email helper is already absent), which is the expected result.
Earlier candidates are byte-identical. **Installation of these bytes is not authorised**; the
`.23`-only plan with stop gates and rollback is `INSTALL-AND-ROLLBACK-PLAN-23.md` in that directory.
Live identity acceptance remains **UNVALIDATED** (user-accepted, not a release blocker); email/webhook/
external delivery, live ageing, direction-A procedure compliance (D1) and the core catalogue drift remain
open. **Nothing deployed**; DM-BL-013 **OPEN**; publication **NO-GO**.

**Rotation-alert ordering defect (15 November 2026, source-only fix, not deployed):**
`identity_event_start_id` — the high-water mark `get_new_high_identity_events()` filters on — was
read **after** the device loop (`scan_network.py`), so the high-severity `IP_IDENTITY_CHANGED` event
that `detect_mac_rotation()` records inside that loop was never eligible for notification. Rotation
events were therefore permanently silent-to-alert, while still being recorded. **Correction to the
earlier finding:** the rotation path was never silent — it records a high-severity event; what was
broken was alert selection. **Affected versions (source evidence):** `v2.12.1` (rotation call at
`:9182`, snapshot at `:9224`) and the 2.14.0 line, including the installed `cd82a60c…`;
`v2.13`/`v2.13.2` contain the snapshot but no rotation classifier, so they are not affected.
Fix: take the snapshot before any producer runs; `tests/test_identity_event_capture_order.py`
reproduces the defect and pins no-replay, dedupe, severity filtering and the producer ordering.
**Live identity acceptance remains UNVALIDATED** and is recorded as not a release blocker; that
decision stands. Evidence wording corrected: an empty `mailq` and the absence of a mail process at
inspection time do **not** prove no transient email attempt occurred; the zero-identity-email
claim rests on the structural absence of the email leg, with external email delivery **UNTESTED**.
**Nothing is deployed**, and D1 remains recorded.


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
