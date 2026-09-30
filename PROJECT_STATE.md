# Device Monitor — Project State

## Current state

Last updated: 30 September 2026

Branch: `v2.10-development`

Authoritative development checkout: `/root/src/opnsense-devicemonitor-upstream`
(FreeBSD 15.1-RELEASE amd64; OPNsense testbed host `192.168.20.23`)

Latest released implementation commit: `96cdd464640af6449afb1aa75c4aa193bc93f2ee` — `Release Device Monitor v2.9 with guarded installer`.

Status:

- **Production was updated to the `45e8c86` v2.10 payload (30 September 2026).** The
  production firewall `192.168.20.254` (`OPNsense.home.arpa`, OPNsense 26.7.4_1) ran the
  guarded installer; that run's log was written at 12:19 (+1000) and reports
  `CHECK_OK version=2.10 predecessor=2.10 files=59 core_locales=10 daemon_running=1` followed
  by `INSTALL_OK version=2.10 files=59 core_locales=10 daemon_restarted=1 backup=/var/backups/devicemonitor/install-v210.RulQty`.
  A subsequent read-only audit re-derived the installed digests on production and matched
  **38/38 rows** of `release/v2.10-runtime.manifest`
  (`sha256 15aa829f0a5be8dc5a31438a2ddfc4cf1aaf7bfbef68cec7f9a77936b0d7f7c3`, 38 rows)
  byte-for-byte, plus the two sampled `cs_CZ`/`en_US` sidecar catalogues, so production's
  installed payload is the `45e8c86` tree. Two statements elsewhere in this file are now
  stale and are superseded by this entry — "Production still runs v2.9" (already wrong when
  written: the guard reported a `2.10` **predecessor**, so production was on an earlier v2.10
  build, not v2.9) and the note that the v2.10 metadata is "repository-only". One recorded
  conflict is carried, not resolved, here: tag `v2.10` points at `1315c80`, ten commits
  *before* `45e8c86`, and the deployed artifact (`sha256 13ed23e8…`) is not the `28ce829d…`
  asset hash recorded for the v2.10 release draft. Full record at the end of this file.
- Development is on `v2.10-development`: nine major UI translations and the v2.10 version bump (`199be95`), followed by the completed view translation patch and JavaScript encoding correction documented below, then the v2.10 version-metadata and config-API alignment (`702d674`). Service email warning implementation is `4b2b992`; the latest released implementation remains v2.9.
- Latest source fix `aa25fe7` and its guarded v2.10 runtime-manifest update `0708239` are pushed to `origin/v2.10-development`; full GitHub Actions CI run `36315636699` PASS. Those commits changed no testbed runtime file or service; the nine corrected views were deployed to the testbed separately on 27 September 2026 (deployment record under DM-BL-008 below). `0708239` left the manifest SHA256 pinned in `install-unattended.sh` at the pre-refresh value, so the guarded installer aborted; that pin is restored by `3eeb78b`, which with its documentation commit `3fc9dfc` is pushed to `origin/v2.10-development` and green in GitHub Actions Device Monitor CI run `36323794636`; the following record commit `02a1eba` is also pushed and green in CI run `36324231410`, so no commit on this branch is local-only (see the install-guard section below).
- Device Monitor GUI repair (29 September 2026): the views' `devicemonitor_t()` macro was never registered with the Volt compiler, so every application tab aborted with `MacroNotFound` and rendered a blank content block. The plugin controller now wraps the framework's `.volt` engine and registers the sidecar translator; the pending PHP 8.1+ null guards and the three matching `release/v2.10-runtime.manifest` digests plus the installer pin are refreshed in the same commit `8faf09d`, which is pushed to `origin/v2.10-development` and green in GitHub Actions Device Monitor CI run `36501061119`, with its record commit `58b9628` pushed and green in CI run `36501202440` (see the 29 September 2026 section below).
- Change Summary confirmation banner (`F1`) fixed and closed (29 September 2026): the Change Summary view's `showToast()` no longer guards on the absent `$.fn.notify`/`window.bootbox` plugins; it renders the same self-contained jQuery banner already used by `devices.volt`, with the icon and message appended as DOM nodes and a 4-second auto-dismiss. The refreshed view digest, `release/v2.10-runtime.manifest` row 17 and the `install-unattended.sh` line 28 manifest pin are in the same change set; the live operator check and the full record are in the `F1` closure section at the end of this file.
- Testbed background scanner active (29 September 2026): the daemon (PID 94999, running unchanged since 28 September 2026 23:15) hot-loaded `"enabled": "1"` from `/var/db/devicemonitor/config.json` through its own 10 s config reload — no service restart and no web-GUI restart — polling every 60 s over the fail-closed scope `opt1` → `vlan0.50` (`192.168.50.0/24`, DMTEST), with two clean scan cycles and no database-lock or runtime errors observed; rollback copy `/var/backups/devicemonitor/scan-activation-20260929/`.
- DM-BL-008c **resolved** (29 September 2026): the v2.10 installer now merges the plugin's text keys into the core catalogues (`/usr/local/share/locale/<locale>/LC_MESSAGES/OPNsense.mo`) so the inline-script strings translate too, using `release/merge-opnsense-catalog.sh` (core-first `msgcat --use-first`, with `--plugin-only` for a locale that has no core catalogue such as `nl_NL`), first-write-wins pristine records that `uninstall.sh` restores, and a new CI gate (`python3 tests/test_locale_merge.py`). The update target count rises from **49 to 59** (`60` fresh: 38 manifest rows + 11 sidecar catalogues + 10 merged core catalogues, plus `rc.conf` when fresh); the installer was then executed on the testbed the same day (`INSTALL_OK version=2.10 files=59 core_locales=10`, backup `install-v210.O1Tggb`) and the nine-language runtime acceptance passes with exit code 0 — see the deployment record in the closure section at the end of this file.
- That v2.10 metadata is repository-only: no v2.10 tag, GitHub release or runtime package exists, the published `v2.9` release asset is unchanged, and no testbed or production install was performed.
- Notification dispatch remains on configd permanently: the HTTP API integration for `apiEmailUrl`/`apiWebhookUrl` is not implemented (`DECISIONS.md` 33 supersedes the cutover gates recorded in `DECISIONS.md` 32); `scan_network.py` and the live notification path are unchanged. The `www` privilege claim originally recorded for the API path is corrected by `DECISIONS.md` 34 (the web GUI runs `php-cgi` as root).
- GitHub `v2.9` release is published at commit `96cdd464640af6449afb1aa75c4aa193bc93f2ee`. The runtime-only asset SHA256 is `c8ae2562a3ea895de8d0810a3a1af2a44ac8dfe8739b75c06c9cf9348b2aa07c`; both pull-request and development-branch CI passed.
- The final v2.9 runtime package was installed and hash-verified on the testbed on 25 September 2026. The checkout has since advanced to v2.10 development; the installed model and Network Identity Details template match `4b2b992` (verified 26 September). Other installed files were not re-audited in that verification.
- That partial testbed state was superseded on 27 September 2026: the full v2.10 development payload is deployed on the testbed (`files=48`, backup `install-v210.rdQhGA`), with 37/37 manifest hashes and 11/11 catalogues verified, and configd-based daemon status reporting running (see the section below). Production still runs v2.9.
- The DM-BL-008 language acceptance passed on the testbed on 27 September 2026 for all nine languages across 10 pages and 448 strings. Dutch (`nl_NL`) is not offered by the GUI language list. The JavaScript-encoding correction (raw `query()` before `json_encode(15)`) was deployed to the testbed on 27 September 2026 at 21:17:12 AEST with a rollback backup, and the post-deploy runtime acceptance passed; see the deployment record under "27 September 2026 automated language acceptance (DM-BL-008)" below.
- The final v2.9 runtime package is installed and independently verified on production. The `v2.9` release tag remains at the implementation commit; this later documentation commit records deployment acceptance.
- v2.9 was promoted to production; see the historical section
  "## v2.9 production promotion" for the earlier release-candidate promotion.
- The post-v2.9 changes through DM-STICKY2F were promoted to production on 24 September 2026. The installed scope includes the guarded interface scoping and loopback exclusions as well as the UI changes.
- Targeted TCP Port Discovery, service archiving, responsive tables and the Devices refresh focus fix were promoted to production on 25 September 2026 (see below).
- Current production OS version and runtime settings are not restated here; the
  historical sections below record what was known when they were written.

## 27 September 2026 v2.10 install-guard pin restoration

Description: restored the guarded v2.10 installer, which aborted with
`ABORT: release manifest mismatch` after `0708239` regenerated
`release/v2.10-runtime.manifest` for the nine corrected DM-BL-008 views without
updating the SHA256 pinned on `install-unattended.sh` line 28.

Method: changed only that pin, from the pre-refresh
`29ac9a165cef55b416b3602e1489a007e58a5f942849481d9a13822b7b5aaaa5` to the current
manifest SHA256 `11472b464798344b93ac4be3dc220632cbec62e5a07cdba311f6f77f7161ed76`,
confirmed independently with `sha256 -q` and Python `hashlib`. No other line of the
installer, manifest, view, catalogue, payload count, service or runtime file changed.

Result (local checkout, 27 September 2026): the guard passes again —
`sh install-unattended.sh --host OPNsense.internal --check` →
`CHECK_OK version=2.10 predecessor=2.10 files=48 daemon_running=1 host=OPNsense.internal`,
against the pre-change baseline `ABORT: release manifest mismatch` (exit 1).

Changed: `install-unattended.sh` (one line, commit `3eeb78b`), `PROJECT_STATE.md` and
`PRODUCT_BACKLOG.md`. Nothing was installed, deployed, tagged, released or pushed; no
testbed or production file, service, database or configuration was touched.

Validation: `sh -n install-unattended.sh`, `python3 tests/test_release_manifest.py`
(`V210_RELEASE_MANIFEST=PASS`), the `--check` run above and `git diff --check` all PASS.

Pushed and verified (27 September 2026): `3eeb78b` and this record (`3fc9dfc`) are on
`origin/v2.10-development`, so the install-guard fix is no longer local-only. The GitHub
Actions Device Monitor CI run for that push is `36323794636` (`Device Monitor CI`, branch
`v2.10-development`, head `3fc9dfc`, push event, job `validate`, run 1) — **PASS**,
including the `Validate translated JavaScript` and `Validate language acceptance
(DM-BL-008)` steps.

Resolved (29 September 2026): `DM-BL-008b` is **`CLOSED`** — the row-1 confirmation dialog
(Devices → per-row Delete) was verified live in French and Italian, and the runtime test harness
now certifies languages on the production Volt path (commit `7b4bb46`); see the closure section
below. `DM-BL-008c` (the shared-catalogue merge that makes the installed plugin catalogues readable
by the GUI) was **resolved on 29 September 2026**, when the v2.10 installer gained the merge engine
(see the closure section at the end of this file), so both language items are now closed. `DM-BL-008a` (Dutch cannot be
selected through the current GUI language list) was **`CLOSED`** as dropped on 28 September
2026: the language list is core-owned and cannot be changed from this repository — the live
`/usr/local/etc/inc/system.inc` (SHA256 `3347f876…`, byte identical to upstream) carries no
`nl_NL` entry, nothing is commented out, and no Dutch core catalogue ships — which is the same
conclusion the parallel locale-verification track recorded for `O2`. **GUI exposure for `nl_NL` is
therefore withdrawn rather than pending**: the item is closed as dropped, this plugin neither patches nor
wants a patch to the core language list, and it renders the Dutch catalogue whenever a session already
uses `nl_NL`. The
`release/v2.10-notes.md` review that was outstanding here was completed on 28 September 2026
(see the end of the DM-BL-008 section below).

Next recommended step (superseded 29 September 2026): decide DM-BL-008c — merge the pushed
`feature/optional-locale-installer-20260927` branch or implement the equivalent merge for v2.10.
That decision was taken by implementing the merge engine in the v2.10 installer
(`release/merge-opnsense-catalog.sh`, wired into the installer's catalogue loop and its matching
uninstall restoration), so the nine translations are no longer inert on a firewall installed from the
release asset alone; the candidate branch stays unmerged and is superseded. The installer guard itself
needs no further work.

## 27 September 2026 automated language acceptance (DM-BL-008)

Description: automated the recorded DM-BL-008 browser check — select each of the nine
languages and confirm the Device Monitor pages render translated text — because the
testbed has neither a browser nor GUI credentials, and the languages cannot be read by the
developer.

Method: `tests/test_language_acceptance.py` renders every Device Monitor page from its
installed Volt template for each of the nine languages with the production view path — the
locale handling of `ControllerRoot::setLang()`, the real `OPNsense\Base\ViewTranslator`
over `/usr/local/share/locale`, and the real Phalcon Volt compiler, through the new
`tests/render_device_monitor_page.php` — and compares the rendered page with the
catalogues. Expected text comes from the catalogues, so no knowledge of the target
languages is needed. It also verifies that the source `.po`, the installed plugin `.mo` and
the deployed shared `OPNsense.mo` agree for every string the pages use, that the rendered
page text matches the selected language and no other installed language, and that the
language is offered by `System > Settings > General > Language` (`get_locale_list()`).

Result on the testbed (27 September 2026): **PASS** for all nine languages, 10 pages and
448 message ids each — de_DE 432 translated, fr_FR 430, es_ES 440, it_IT 439, pt_BR 435,
nl_NL 428, ru_RU 443, ja_JP 440, zh_CN 440 (the remainder are strings that are identical in
English by design, for example *Status*). Every page rendered the selected language's text
with no English fallback, the text did not match any other installed language better, and
the expected writing systems (Cyrillic, CJK) were present.

One platform gap remains:

- **`nl_NL` cannot be selected in the GUI.** The installed `get_locale_list()`
  (`/usr/local/etc/inc/system.inc`) offers 19 languages and omits Dutch, and OPNsense ships
  no Dutch core catalogue, so the deployed
  `/usr/local/share/locale/nl_NL/LC_MESSAGES/OPNsense.mo` contains the Device Monitor
  catalogue alone. The Dutch pages render correctly through the deployed catalogue and
  locale (`nl_NL.UTF-8` exists), but the recorded step "select Dutch in
  System → Settings → General → Language" cannot be performed; the live configuration value
  was not changed by this work.
- **JavaScript translation escaping is corrected and deployed.** `ViewTranslator::_()` HTML-escapes
  translations, so JavaScript expressions use its inherited raw `query()` method,
  followed by `json_encode(15)` (`JSON_HEX_TAG|AMP|APOS|QUOT`). This keeps the output a
  JavaScript string while preventing script-boundary injection. Runtime acceptance and
  Node execution verify the exact translated string, including apostrophes, entities and
  hostile markup. The nine views are now deployed on the testbed (deployment record below), and
  the v2.10 development payload carries the same corrected views: `0708239` refreshed the nine
  guarded `release/v2.10-runtime.manifest` view hashes to them, and
  `tests/test_release_manifest.py` reports `V210_RELEASE_MANIFEST=PASS` against the current
  checkout (re-checked 28 September 2026). No v2.10 package, tag or release asset has been
  built from that payload.

Deployed (testbed `192.168.20.23`, host `OPNsense.internal`):

- Deployment timestamp: `2026-09-27 21:17:12 AEST` (`2026-09-27T11:17:12Z`).
- Scope: the nine corrected views, copied from
  `/root/src/opnsense-devicemonitor-upstream/src/opnsense/mvc/app/views/OPNsense/DeviceMonitor`
  to `/usr/local/opnsense/mvc/app/views/OPNsense/DeviceMonitor`.
- Backup path: `/root/devicemonitor_backup/dm-language-js-query-views-20260927-211712` —
  pre-deployment `*.pre` originals, `DEPLOY-INFO.txt` with per-file before/after SHA256,
  and `rollback.sh`, which restores all nine views.
- Verification: each deployed view is byte identical to its source view by SHA256
  (re-checked 27 September 2026).
- Post-deploy acceptance: **PASS** — `python3 tests/test_language_acceptance.py --engine runtime`
  ran against the deployed runtime views at `2026-09-27 21:17:37 AEST` (record:
  `/root/DM-BL-008_language_acceptance_20260927-js-deployed.md`), and was re-run on
  27 September 2026 after this record was written with
  `LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0`: nine languages,
  10 pages, 448 strings, zero failures and no JavaScript-entity finding. The single gap is
  the `nl_NL` GUI-selectability warning recorded above.
- Not changed by that deployment: no catalogue, configuration, service, database or production
  file. The guarded payload was refreshed to the corrected views afterwards by `0708239`, and
  the release-notes review recorded at the end of this section was performed on 28 September
  2026.

Validation:

- Initial negative controls: a catalogue without Device Monitor strings reports 390
  source mismatches; a French catalogue installed in a German locale reports 441.
- Candidate source views passed runtime acceptance through the installed Phalcon Volt
  compiler and `ViewTranslator` for all nine languages, 10 pages and 448 strings, with
  zero failures. The only gap is that `nl_NL` is absent from the 19-language GUI list.
- The same nine-language acceptance passed using the CI interpolation engine.
- All 120 rendered script blocks (11 catalogues plus the hostile fixture) passed Node
  syntax checks. Executing the hostile translated string preserved its exact content,
  including quotes, backslashes, newlines, `</script>`, ampersands and U+2028/U+2029.
- All 11 Node UI tests passed. PHP lint, Python compile and `git diff --check` passed.
- `tests/test_release_manifest.py` passed after refreshing the nine guarded
  `release/v2.10-runtime.manifest` view hashes; every recorded preimage matched the
  parent commit.
- Source commit `aa25fe7` and manifest update `0708239` are pushed; full CI run
  `36315636699` passed, including both new language-acceptance steps.

Not covered: HTTP transport, full page JavaScript interactions, page layout and translation
wording. Those remain browser/human acceptance checks.

Changed areas: nine Volt views, the nine corresponding hashes in
`release/v2.10-runtime.manifest`, the language acceptance renderer and test, the translated
JavaScript test/render helpers, one affected Change Summary UI assertion, the CI workflow
and this record. The same nine views were then deployed to the testbed (deployment record
above); no catalogue, configuration, service, database or production file was changed.

Release-notes review (28 September 2026): `release/v2.10-notes.md` was reviewed against the
nine corrected views and now records the JavaScript-encoding correction (the raw translated
value is JSON-encoded, so apostrophes, quotation marks, backslashes, line breaks and
`</script>` in translations render exactly and cannot break or inject into a page), the eleven
installed catalogues and the validated nine-language acceptance (10 pages, 448 strings per
language, zero failures), and the `nl_NL` GUI-selectability limitation. `release/v2.10-notes.md`
is not one of the 37 files in `release/v2.10-runtime.manifest`, so the review changed no guarded
hash and `tests/test_release_manifest.py`, `sh -n install-unattended.sh` and `git diff --check`
stayed PASS. `PRODUCT_BACKLOG.md` DM-BL-008b records the same review as resolved on 28 September
2026, the French text-stream verification described below, and the item's closure on 29 September
2026 after the runtime harness patch and the live French/Italian dialog pass.

French text-stream verification (28 September 2026): the French translation stream was verified on
the target UI by an operator-run remote Selenium text-stream assertion against
`https://192.168.20.23`, which found `Résumé des modifications` (`Change Summary`) and
`Surveillance des appareils` (`Device Monitor`) in the rendered text; both match the deployed
`/usr/local/share/locale/fr_FR/LC_MESSAGES/OPNsense.mo` and `fr_FR_devicemonitor.po`. This replaces
the former French browser-dialog confirmation for DM-BL-008b, because there is no dialog to confirm
on OPNsense 26.7.4: `showToast()` in the Change Summary view guards on `$.fn.notify` and
`window.bootbox`, neither of which the core page loads (`/ui/js/theme.js` is an empty placeholder,
no bootbox or notify file exists under either web root, and the plugin calls no dialog API at all),
so that toast path is inert and the core dialog API is `BootstrapDialog`, exposed as
`stdDialogInform()` in `opnsense_ui.js` (F1). The verifying Selenium script and its output were not
archived in this checkout or on the testbed, so this result is recorded as operator-reported.
Correction (29 September 2026): the "no dialog to confirm" reasoning above covers the Change Summary
`showToast()` path only. The plugin does use real browser dialogs elsewhere — native `confirm()` at
`devices.volt:941`, `devicehistory.volt:612/895/1075`, `physicaldevices.volt:730/785/840`, and native
`alert()` at `identityevents.volt:427/431` and
`infrastructureservices.volt:1351/1356/1494/1506` — so the row-1 per-row Delete dialog is observable
and was verified live in French and Italian on 29 September 2026 (see the DM-BL-008b closure section
at the end of this file). `F1` remains open for the inert toast path.

Push and CI confirmed: the local-only statements this section originally carried were resolved
by the push of `3eeb78b` and `3fc9dfc` (GitHub Actions Device Monitor CI run `36323794636`,
head `3fc9dfc`, job `validate` — PASS), of the record commit `02a1eba` (CI run
`36324231410`, head `02a1eba` — PASS) and of the project-state and release-notes commit
`e6443bc` (CI run `36355695028`, head `e6443bc` — PASS). Local and remote `v2.10-development` are
the same commit; nothing on this branch is local-only.

Still outstanding at that point: F1 was an open decision — the Change Summary toast rendered nothing
because the core ships `BootstrapDialog` and neither `$.fn.notify` nor `bootbox` — and DM-BL-008c (the
shared-catalogue merge that makes the installed plugin catalogues readable by the GUI) remained open
but was formally deferred as of 28 September 2026: documentation only, no installer, manifest,
release-note or Makefile change, because the candidate branch could not be adopted into v2.10 unchanged
and its `--languages` default was still an open sub-decision. Both items were closed on 29 September
2026 (`F1` by the Change Summary banner change, DM-BL-008c by the v2.10 merge engine, which removes the
sub-decision by shipping all eleven catalogues); see the closure sections at the end of this file.

Next recommended step: record the `F1` decision — leave the inert Change Summary toast as documented
behaviour, or move `showToast()` to `BootstrapDialog`/`stdDialogInform()`. The language acceptance was
completed on 29 September 2026: the Italian text stream is verified and `DM-BL-008b` is `CLOSED` (see
the closure section at the end of this file). DM-BL-008c is closed as of 29 September 2026 too.

Correction (29 September 2026): the `F1` decision recorded above is settled — `showToast()` was not
moved to `BootstrapDialog`/`stdDialogInform()`; it was replaced with the self-contained jQuery banner
already used by `devices.volt`, with a 4-second auto-dismiss, and `F1` is `CLOSED`. The `F1` item is
therefore no longer open or outstanding, and the later references in this file that still describe it as
open or unresolved (including the `DM-BL-008b` closure section at the end of this file) are superseded by
the `F1` closure section below. `DM-BL-008c` was closed on 29 September 2026 by the v2.10 merge engine.

## 27 September 2026 Settings delivery-action acceptance attempt

Description: checked the report that the Settings delivery actions were working,
using the device-monitor log, the live configuration, the web-server log and
direct network probes.
Outcome: **no acceptance claimed** — the only attempts present are two email
tests issued from the Settings page, both failing; there is no evidence that a
webhook test was ever invoked.

- Email test: two attempts at 19:48:06 and 19:48:09 both logged
  `Test email result: FAILED | Reason: Sendmail is not available. Install/configure
  a local mailer or select Direct SMTP.` `email_method` is `sendmail`, but neither
  `/usr/sbin/sendmail` nor `/usr/local/sbin/sendmail` exists on the testbed and
  PHP `sendmail_path` points at `/usr/sbin/sendmail`, so delivery is impossible.
  The Settings email toast shows the failure reason for any result other than
  `sent`, so the interface reports this as an error.
- Webhook: the device-monitor log contains no webhook line at all (no
  `Preparing to send test webhook`, no result line) and the lighttpd log shows
  no related request, so there is no evidence that a webhook test was ever
  invoked; nothing here indicates the webhook path was exercised. For the record,
  the currently stored `webhook_url` is malformed — `ntfy.sh` is duplicated
  before the scheme, so `urlsplit` reports `scheme=ntfy.shhttps`, `host=ntfy.sh`
  and `curl` cannot resolve it (`Could not resolve host: ntfy.shhttps`), while
  `https://ntfy.sh/` itself answers HTTP 200. This affects nothing while webhook
  delivery is unused.
- Web server: lighttpd logged `connect() /var/lib/php/tmp/php-fastcgi.socket-4:
  Connection refused` at 19:46:20, i.e. the PHP backend was briefly unreachable
  while the tests were being attempted.
- Interface gap (no code change): `#test_webhook` in `settings.volt` has no
  jQuery `error:` callback, so a failed request leaves the blue
  "Sending..." text in place instead of showing an error, which can look like a
  successful test.
- Correction recorded: the web GUI runs `/usr/local/bin/php-cgi` FastCGI workers
  as root (php-fpm is not installed), so the `www` privilege claim made earlier
  for the API path was wrong (`DECISIONS.md` 34).

Changed: `DECISIONS.md` and this state record only. No source, test,
configuration, service or live notification path was modified.

Next recommended step: proceed to the DM-BL-008 language acceptance on the
testbed. Email delivery is no longer an open testbed item (see the operator
clarification below); webhook delivery is confirmed working.

Operator clarification (27 September 2026, 20:07): email delivery has worked in
production and was never tested or configured in the testbed. The testbed
failure is therefore a testbed configuration gap (no mailer, no SMTP
credentials, no local MTA ever installed), not a regression, not a code defect
and not a production problem. This is operator-attested here: confirming
production's transport (a local mailer via `os-postfix` versus Direct SMTP)
would require reading production configuration, which is outside this session's
authorisation. Email is consequently dropped from the v2.10 testbed acceptance
scope, and `email_method` is deliberately left unchanged at `sendmail` on the
testbed.

Follow-up (27 September 2026, 19:59): the malformed webhook URL was repaired on
the testbed. `config.json` was backed up first
(`/root/devicemonitor_backup/config-json-pre-webhook-url-fix-20260927-195948`),
the duplicated `ntfy.sh` prefix was removed deterministically (the topic token
was not altered) and the stored value now parses as
`scheme=https host=ntfy.sh` with the original path preserved; the file remains
valid JSON, mode 0600 root:wheel. A test through the same handler path the
Settings button uses returned
`{"result":"ok","message":"Webhook sent (HTTP 200)","type":"ntfy","test":true,"count":0}`,
so webhook delivery is confirmed end to end.

Email cannot be repaired from existing data: no mailer is installed
(`sendmail`, `mail`, `msmtp`, `dma` all absent; the plugin's `sendmail` method
requires `/usr/local/sbin/sendmail`, typically provided by `os-postfix`),
`/conf/config.xml` holds no system notification SMTP settings, and no plugin
backup contains SMTP credentials — every archived `config.json` shows
`email_method=sendmail` with empty host, user and password. Direct SMTP is
therefore the only practical route and requires credentials held only by the
operator.

Checked on request (27 September 2026, 20:03): the current `sendmail` method
cannot be made to work on this testbed as-is. No mailer has ever been installed
on this host — no `postfix`/`dma`/`exim`/`sendmail` package, no
`/usr/local/etc/postfix` or `/var/db/postfix` leftovers, no
`/usr/local/sbin/sendmail`, and `/conf/config.xml` lists no plugins at all
(`plugins: []`, no postfix settings block). Outbound port 25 to
`gmail-smtp-in.l.google.com` fails with `No route to host`, while
`smtp.gmail.com` is reachable on 587 and 465. Installing `os-postfix` would
therefore still not deliver mail without a relayhost, which is Direct SMTP with
extra moving parts. Email delivery from this testbed requires Direct SMTP
(`email_method=smtp`) with operator-supplied credentials; the Settings UI labels
the two options "Local Sendmail / Postfix" and "Direct SMTP (built into Device
Monitor)".

## 27 September 2026 v2.10 testbed deployment

Description: deployed the verified v2.10 development build to the testbed
(`OPNsense.internal`, 192.168.20.23) with the guarded installer, after taking
independent rollback protection.
Benefit: the testbed now runs the committed v2.10 payload (config API actions,
configd-based daemon status, corrected views), unblocking the pending
Settings/GUI and multilingual browser acceptance work.

- Preflight: installed predecessor `2.9`; daemon running as pid 98406;
  `configctl devicemonitor status` = running; 25 of 37 manifest targets already
  identical and 12 to change (both API controllers, `defaults.json`, nine
  `.volt` views); all 11 compiled catalogues present; `devices.db` 3 devices,
  0 pending, `quick_check` ok.
- Rollback protection in place before the install: independent snapshot
  `/root/devicemonitor_backup/pre-v210-20260927-181424` (37 targets, plan with
  hashes, `config.json`, `devices.db`, executable `rollback.sh`), plus the
  installer's own hash-guarded backup `install-v210.rdQhGA`.
- `install-unattended.sh --host OPNsense.internal --check` →
  `CHECK_OK version=2.10 predecessor=2.9 files=48 daemon_running=1`.
- Apply → `INSTALL_OK version=2.10 files=48 backup=/var/backups/devicemonitor/install-v210.rdQhGA daemon_restarted=1`;
  configd and the daemon restarted once (daemon pid 98406 → 653, log shows
  clean stop/start).

Verification after deployment:

- 37/37 manifest targets match the release manifest hashes; 11/11 `.mo`
  catalogues match a fresh `msgfmt --check` compile of the repository sources.
- Installed `defaults.json` reports `2.10`; deployed `ServiceController` calls
  `configdRun('devicemonitor status')`; deployed `ConfigController` exposes both
  new real-mode actions; `php -l` PASS on both deployed controllers.
- `configctl devicemonitor status` = `running`; pidfile matches the live pid;
  rc status running; 7 device-monitor configd actions loaded; daemon still
  running with the same pid after a stability interval.
- Unauthenticated API probes (`config/getversion`, `service/status`,
  `config/sendEmail`, `config/sendWebhook`) were redirected by the login layer
  (HTTP 302) with zero `*-ConfigController` log lines, confirming the routes are
  auth-gated and that the probes caused no delivery.
- Notification code paths executed on the testbed return
  `{"result":"skipped","message":"Email disabled"}` and
  `{"result":"skipped","message":"Webhook disabled"}` — the guards stop delivery
  because the testbed configuration has email and webhook disabled with no
  recipient or URL.
- Runtime data preserved: `config.json` byte-identical to the snapshot,
  `devices.db` `quick_check` ok with the same 3 devices and 0 pending rows.

Limits: live email/webhook delivery was not exercised — both channels are
disabled in the testbed configuration, and the configuration was deliberately
left unchanged. Settings-page test actions, the nine new languages (DM-BL-008)
and the other GUI checks still require an authenticated browser session.
Observation only (no code change): `ConfigController::sendWebhookAction` passes
an empty string when the `webhook_url` parameter is absent, which bypasses the
handler's "Webhook disabled" guard and would attempt delivery to an empty URL.

Next recommended step: complete the authenticated browser acceptance run on the
testbed — the Settings email/webhook test actions and the nine new UI languages
recorded under DM-BL-008.

## 27 September 2026 notification HTTP cutover — design only

Description: assessed switching daemon notification dispatch from the configd
actions to the `ConfigController` `sendEmail`/`sendWebhook` HTTP endpoints and
recorded the outcome as Decision 32 in `DECISIONS.md`.
Benefit: avoids a change that would have broken working delivery; the recorded
blockers remain the documented reason the HTTP route is not taken.

- Confirmed the endpoints run the same real-mode `NotificationHandler` methods
  as `notify_email.php`/`notify_webhook.php`; only transport, authentication and
  privileges would change. `apiEmailUrl`/`apiWebhookUrl` remain unused.
- Blockers measured on the testbed: mandatory API key/secret with ACL page
  access (the installed `ApiControllerBase` has no localhost bypass); TLS
  hostname mismatch for the default `https://localhost/...` URL; and loss of
  root privileges for `fLog()` (0640 root:wheel) and direct-SMTP `config.json`
  (0600 root:wheel) because php-fpm runs as `www`. **Corrected (27 September
  2026):** this bullet is wrong — the web GUI runs `/usr/local/bin/php-cgi` as
  root, so the API path keeps the same privileges as configd
  (`DECISIONS.md` 34).
- Decision and gates (credentials source, TLS identity, privilege model,
  failure handling, validation) recorded in `DECISIONS.md` 32.

Changed: `DECISIONS.md` and this state record only. No implementation was
performed: `scan_network.py` still dispatches through configctl, and no source,
database, configuration, service, test or live notification path was modified.

Outcome (27 September 2026): the HTTP API integration is **not implemented**.
configd dispatch is retained permanently and the cutover gates in Decision 32
are superseded by Decision 33. No further notification-transport work is
planned for v2.10; the remaining open item for this phase is the authenticated
browser acceptance recorded above.

## 27 September 2026 v2.10 version metadata and config API alignment

Description: synchronised the self-referential v2.10 version data with the
`v2.10-development` branch and exposed the email/webhook delivery tests through
the config API.
Benefit: version checks, the release manifest and the guarded installer no
longer contradict the branch, and the Settings page can test email and webhook
delivery through the documented API URLs.

- `release/v2.9-notes.md` and `release/v2.9-runtime.manifest` became
  `release/v2.10-notes.md` and `release/v2.10-runtime.manifest` (still 37 rows).
  The new manifest SHA256 is
  `29ac9a165cef55b416b3602e1489a007e58a5f942849481d9a13822b7b5aaaa5`, re-pinned
  in `install-unattended.sh`.
- `install-unattended.sh` requires source `defaults.json` version `2.10`,
  accepts `2.8|2.9|2.10` as installable predecessors, uses `v210` staging and
  backup names, and reports `version=2.10` in `CHECK_OK` and `INSTALL_OK`.
- `ConfigController` gained `sendEmailAction` and `sendWebhookAction`
  (real-mode `sendEmail(false)` / `sendWebhook(false, ...)`) so the Settings
  page can test delivery through the documented
  `POST /api/devicemonitor/config/sendEmail` and
  `POST /api/devicemonitor/config/sendWebhook` URLs; results log
  SUCCESS/SKIPPED/FAILED.
- `ServiceController::statusAction` reports state from the configd
  `devicemonitor status` action instead of `ps` on the pidfile; the pidfile is
  read only for the returned `pid`. The live
  `src/opnsense/service/conf/actions.d/actions_devicemonitor.conf` is unchanged
  and still defines `status`.
- README and README_CZ runtime-package, upgrade and uninstall notes now use the
  v2.10 package and asset names.
- Deleted the unreferenced legacy `src/etc/configd/devicemonitor.conf` (3 lines;
  superseded by `actions_devicemonitor.conf`).
- `tests/test_release_manifest.py` validates the manifest against the working
  tree instead of the immutable `v2.9` tag. The `.github/workflows/ci.yml`
  `fetch-depth: 0` comment still refers to the old tag-based check; the comment
  was not changed by this commit.

Changed: 10 files, 126 insertions, 97 deletions. No database, live
configuration, installed file, service or production host was touched, and no
v2.10 tag, release or runtime package was created.

Validation before commit: `php -l` on 11 sources,
`sh -n install-unattended.sh`, `python3 tests/test_release_manifest.py`
(`V210_RELEASE_MANIFEST=PASS`) and `git diff --check` all PASS locally.
Pushed to `origin/v2.10-development`; GitHub Actions Device Monitor CI run
`36303936147` PASS.

Next recommended step: deploy the verified v2.10 development build to the
testbed with rollback protection, which also enables the pending DM-BL-008
multilingual browser acceptance and the new Settings delivery tests.

## 27 September 2026 translated JavaScript correction

Description: complete the pending view/catalogue translation patch and encode
translated values safely when embedding them in inline JavaScript.
Benefit: apostrophes, quotation marks, backslashes and line breaks in translations
no longer break Device Monitor pages, and translated closing script tags cannot
terminate the surrounding inline script.

- Reproduced the existing Device Profiles, Network Identity Details and Change
  Summary UI test failures in an isolated snapshot.
- Replaced direct interpolation inside quoted JavaScript with unquoted Volt
  `lang._(...)|json_encode(15)` values (JSON_HEX_TAG, JSON_HEX_AMP,
  JSON_HEX_APOS and JSON_HEX_QUOT). Preserved the existing catalogue changes.
- Applied the same encoding to all nine views containing inline translations,
  including pre-existing unsafe interpolation in Settings and IP/MAC Conflicts.
- Updated structural/behavior UI tests to render translated string values and
  updated the Change Summary empty-state assertion for the gettext message.
- Added `tests/test_translated_javascript.py`, its PHP renderer and the shared
  Node test helper. CI now compiles every catalogue and parses every rendered
  inline script, including an adversarial translation fixture. On OPNsense the
  renderer uses the actual Volt compiler; CI without Phalcon uses the same PHP
  JSON encoder and rejects unencoded translation expressions.

Validation before commit: all existing Node UI tests PASS; the final summary
and VLAN helper corrections were rerun and PASS. All 11 catalogues PASS
`msgfmt --check --check-format`; 120 actual Volt-rendered JavaScript blocks
(10 blocks x 11 locales plus one adversarial fixture) PASS Node parsing.
The fixture covers both quote styles, backslashes, newlines, Unicode separators,
non-Latin text and closing script tags. PHP renderer lint and `git diff --check`
PASS. Remote CI result is tracked against this change's commit.

Changed areas: nine `.volt` views, eleven existing catalogue edits, affected UI
tests, translation regression helpers, `.github/workflows/ci.yml` and this state
record. No installed template, live configuration, database or service changed.
The untracked local optimization rules were not included. Production was not
accessed; PR #2 (optional locale installer) was not merged by this task.

Remaining validation: rendering/parsing does not constitute visual language QA.
Next recommended step: deploy the verified candidate to the testbed with rollback
protection for multilingual browser acceptance before release or PR #2 merge.

## 27 September 2026 testbed HTTPS and browser verification

Description: repaired testbed HTTPS trust using the existing step-ca service,
then resumed authenticated Service Email Alerts browser checks.
Benefit: the in-app browser can validate the testbed certificate normally,
allowing UI verification without a certificate-warning bypass.

Environment work (testbed only):

- Installed official `os-acme-client` 4.17 and its dependencies. The package
  installer restarted configd; the web GUI was restarted to load the new cert.
- Used the separately authorized CA at `https://192.168.20.16:8443`, ACME
  provisioner `opnsense-acme`. Imported its public root into testbed trust;
  Windows trust and CA server configuration were not changed.
- Issued and activated certificate `6ab85b5c0c251`, with IP SAN
  `192.168.20.23`, valid through 26 October 2026 23:54:59 UTC. The original
  web certificate `6aaa3fe2b625e` remains available for rollback.
- Native renewal: daily check at 03:17 firewall-local time, renew after 20 days,
  reload the web GUI on success. Verified the generated job in
  `/var/cron/tabs/nobody`, zero model validation errors, and a successful
  non-due cron execution (exit 0). A future renewal has not yet been observed.
- Root-only configuration backups and state record are retained under
  `/var/backups/devicemonitor/tls-20260926-235345/`. These contain sensitive
  configuration and must not be published.
- Windows HTTPS check returned HTTP 200 with chain/hostname validation enabled
  (best-effort handling of unavailable revocation information). The in-app
  browser opened the login page without a certificate error; user signed in.

Authenticated browser results: PASS for disabled-email warning text, navigation
from the warning to the Email Notifications Settings tab, return to the same
network identity, save-success feedback, and preference persistence on reload.
The New service preference was temporarily changed from Use global setting to
Off, saved and reloaded, then restored to Use global setting and reloaded again.
All three original preference values were restored. Global monitoring/email
settings were unchanged; normal preference-change audit records may remain.

Limits: other unavailable reasons and the available state passed the earlier
isolated controller/model tests, but were not exercised through live global
settings changes in this browser session. No production host was accessed.

Changed files for this reconciliation: `PROJECT_STATE.md` only. Existing
uncommitted views, translations and local rules were preserved; the separate
DM-BL-008 language acceptance task is not claimed complete by these checks.

Next recommended step: review the automated DM-BL-008 language acceptance result in
"27 September 2026 automated language acceptance (DM-BL-008)" above; its two findings
(`nl_NL` selectability and JavaScript entity escaping) are still open.

## 26 September 2026 — major language UI translations (DM-BL-008)

Description: added gettext catalogues for nine major UI languages so the
Device Monitor is fully translatable beyond English and Czech.

Completed implementation:

- Created `<locale>_devicemonitor.po` for `de_DE`, `fr_FR`, `es_ES`, `it_IT`,
  `pt_BR`, `nl_NL`, `ru_RU`, `ja_JP`, `zh_CN` — 289 strings translated per
  catalogue from `en_US_devicemonitor.po`.

Changed areas: `src/opnsense/mvc/app/languages/` (nine new catalogues).

Validation: each catalogue passes `msgfmt --check --check-format`; 290 msgids
identical to `en_US`; 289/289 strings translated (0 missing).

Deployment (testbed `192.168.20.23`): all 11 catalogues compiled with
`msgfmt --check --check-format` (en_US, cs_CZ + the nine new locales) and
installed to `/usr/local/opnsense/mvc/app/languages/` (`.po` and `.mo`,
root:wheel 644, hash-parity verified against the staged compile). Rollback
backups retained at `/root/devicemonitor_backup/*.pre-dmbl008-20260926-111132`.
Unauthenticated route smoke check: HTTP 301→302, no PHP fatal.

Next step: human GUI acceptance — select each of the nine new languages in
System → Settings → General → Language and confirm the Device Monitor pages
render translated strings. Superseded on 27 September 2026 by the automated
acceptance run recorded in "27 September 2026 automated language acceptance
(DM-BL-008)" above, which also found that `nl_NL` is not offered by that
language list.

## 26 September 2026 v2.10 development and service email verification

Description: per-network-identity Service Email Alerts with clearer delivery
warnings, terminology, contextual help and Settings navigation.
Benefit: administrators can tune service alerts for one identity and understand
why saved preferences cannot currently deliver email.

Completed implementation (dates grouped in Australia/Sydney local time):

- `81d0941`: per-identity `inherit` / `on` / `off` service email preferences,
  persistence, API actions and service-alert processing integration. Decision 31
  records the master-switch, recipient, lifecycle and cursor semantics.
- `88a193f`: v2.10 CI checks the v2.9 release manifest against its immutable tag.
- `e7c2a40`, `b8ff319`, `b201169`: aligned service-alert controls and save feedback,
  explained disabled delivery, and added Email Notifications / return navigation.
- `126d9d1`: Network Identity terminology, matching labels and manual updates.
- `0e7ee17`, `32a0f08`, `3fda0e1`, `a1a9ce7`: accessible information icons,
  contextual help beside the warning and within active tabs, and Settings help
  aligned with labels.
- `4b2b992`: specific unavailable-delivery reasons for global email disabled,
  monitoring disabled and missing recipient, plus fallback warning text.

Changed areas: `DevicesController.php`, `DeviceMonitor.php`, `scan_network.py`,
Network Identity Details, Devices, Device Activity, Device Profiles,
Infrastructure Services and Settings views; en_US/cs_CZ catalogues;
`docs/USER_MANUAL.md`, `DECISIONS.md`, `PROJECT_RULES.md`, CI and focused
UI, service-alert-processing and release-manifest tests. This reconciliation
changes only `PROJECT_STATE.md`.

Verified on testbed `192.168.20.23` during the 26 September SSH review:

- Repository HEAD `4b2b992`; working tree clean before this documentation edit.
- Installed `DeviceMonitor.php` and `devicehistory.volt` SHA256 hashes exactly
  matched their repository sources.
- User visually accepted the service email warning on the testbed.
- Installed API controller/model methods passed isolated tests against a private
  configuration and consistent SQLite snapshot: all three unavailable reasons,
  blank/whitespace recipient, available state, email-disabled precedence when
  multiple prerequisites fail, and effective alerts disabled when unavailable.
- `inherit`, `on` and `off` saves persisted when read through a fresh model;
  invalid preference values and non-POST saves were rejected.
- Original configuration and preference fingerprints were recorded before tests;
  snapshot configuration/preferences were restored and checked. Live configuration
  and preferences were verified unchanged. No email was sent.
- The diagnostic rerun passed (exit 0). Its temporary script was reviewed and
  deleted because it depended on installed paths and live fixture data; it was
  not added as a portable repository regression test.

Verification limits / unresolved checks:

- These were direct installed controller/model tests with a request fixture,
  not authenticated HTTP API tests or a fresh local full-suite run. GitHub
  Device Monitor CI for exact development commit `4b2b992d1605184ba488e52452603b55f5673289`
  subsequently verified SUCCESS: run `36223055438`,
  https://github.com/apg19590209/opnsense-devicemonitor/actions/runs/36223055438.
  This run covers the implementation commit; CI for the documentation
  reconciliation is tracked separately by its own commit. Deployment parity beyond the two files above was not
  independently established in this review.
- The original browser certificate blocker was resolved on 27 September.
  Disabled-email warning, Settings/return navigation and preference save/reload
  checks subsequently passed; see the 27 September entry for scope and limits.
- Production was not contacted or changed during this work. Today's changes
  are not recorded here as production-deployed.

Follow-up: authenticated interaction checks completed on 27 September as recorded above.

## 25 September 2026 v2.9 GitHub release

- Annotated tag `v2.9` points to `96cdd464640af6449afb1aa75c4aa193bc93f2ee`; feature and development CI runs succeeded.
- The release asset contains 37 allowlisted runtime sources, two installer scripts and a SHA256 manifest; gettext `.mo` files are compiled during installation. It excludes the live database, configuration, credentials and backups.
- Final package: testbed preflight and guarded install passed, with 39 target hashes verified and a rollback backup retained on the testbed. `configd` and the Device Monitor daemon restarted. The gettext catalogues compiled without warnings.
- Production final-package installation completed on `OPNsense.home.arpa` with 39 file hashes verified. Rollback and online database backups are retained at `/var/backups/devicemonitor/install-v29.bWS1aH`. The installer restarted `configd` and the Device Monitor daemon.
- Independent post-install checks confirmed all 39 file hashes, v2.9 metadata, SQLite `quick_check=ok` and a running daemon. Four notification scripts retained their pre-installation executable mode (`755`); their content hashes match the release package. No production GUI acceptance was repeated after the final-package installation.

Environment: native FreeBSD toolchain (`/bin/sh`, `/usr/local/bin/bash`, git,
php, python3); GitHub CLI (`gh`) authenticated as `apg19590209`; SSH via a
workstation-local host alias. Workstation-local access rules remain in the
untracked `.clinerules/90-local-remote-access.md` (never committed). Production
`192.168.20.254` is never targeted without explicit authorisation.

## 25 September 2026 production promotion

- Feature branch: `feature/targeted-port-discovery` at `9fe0265863beb5ebe1d9c9516a29afb75b011985`.
- Installed nine runtime files and two compiled gettext catalogues on `OPNsense.home.arpa` (`192.168.20.254`): Port Discovery, service archiving, responsive Infrastructure Services/Change Summary/IP & MAC Conflicts tables, and the Devices keyboard-focus fix.
- Guarded predecessor and candidate hashes, retained file and online SQLite rollback backup at `/var/backups/devicemonitor/prod-port.SGfYgq` (`devices.db` SHA256 `08fdb066c24ec7875374e00256be2d0d7ec4c843b809cc7cd7bd6e61a27f8592`). Menu and affected Volt caches invalidated. Existing Device Monitor daemon restarted to load opt-in scheduled scanning; no scan was requested by the deployment.
- Post-install: 11 file hashes, PHP/Python syntax, daemon presence and SQLite `quick_check` passed. Authenticated Firefox smoke checks at 1280 px passed for Devices, Change Summary, IP & MAC Conflicts, Infrastructure Services and Port Discovery (HTTP 200, no page overflow or JavaScript errors). The 1024/1280 Change Summary scroll and sticky checks had passed on the testbed.
- Follow-up: fixed transparent Port Discovery device-table header overlap and changed the fixed 420 px list limit to a viewport-relative 65vh limit. Committed as `4ef94e4`; 1024/1280 testbed browser scroll/layering checks passed. One production view deployed with rollback at `/var/backups/devicemonitor/port-table-prod.8Sx07f`; no daemon restart. The user visually accepted the production Devices and Scans tabs.
- Next step: retain rollback backups while observing normal monitoring.

## 24 September 2026 production promotion

- Candidate: `58b5782439f52ab8e3ab6227716bfc86bb9b60a6`.
- Nine runtime files and two compiled gettext catalogues installed on
  `OPNsense.home.arpa` (`192.168.20.254`), with pre/post SHA256 and mode checks.
  `ConfigController.php` and `settings.volt` already matched the candidate.
- Rollback copies: `/tmp/dm_backup.lwMIW0/preinstall-20260924092941.i9OijB`.
  Plugin-tree, locale and online SQLite backups are retained in
  `/tmp/dm_backup.lwMIW0`.
- Menu cache invalidated. No daemon restart or database migration.
- Post-checks: 11 file hashes, PHP syntax, daemon presence and SQLite
  `quick_check` passed. Production Devices, Device Details, Physical Devices,
  Change Summary and Settings GUI checks passed by the user.
- Next step: retain backups while observing normal monitoring.

## History

The dated sections below are historical records of completed work and are
retained for reference. The "## Current state" section above is authoritative
for the current branch and production/testbed status.


## Device Monitor: stabilise VLAN filtering

Repaired the Network Identities VLAN multi-select and its sticky header.

- Root cause: the VLAN checklist wrapped checkboxes in `<a href="#">` anchors
  (unreliable single-click toggling and page jumps) and `persistVlans()` re-rendered
  the whole table on every checkbox change. The sticky summary/toolbar/thead stack
  was positioned from a fixed `padding-top` offset rather than the measured natural
  flow gap, so it could jump upward and cover the navigation tabs.
- Interaction change: checkboxes are now native `<label>` items that only update a
  pending selection; explicit **Apply** and **Clear** buttons commit the selection
  once. `applyFilters()` preserves vertical and horizontal scroll position around the
  single re-render, and `updateStickyOffsets()` now derives the sticky offsets from a
  measured `getBoundingClientRect()` gap so the header stays below the page
  navigation area and never covers the tabs.
- Status filtering, filtered summary counters, refresh behaviour and VLAN label
  formatting are unchanged. No API, route, database, scanner or stored-data changes.
- Files changed: `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devices.volt`,
  `src/opnsense/mvc/app/languages/cs_CZ_devicemonitor.po`,
  `src/opnsense/mvc/app/languages/en_US_devicemonitor.po`,
  `docs/USER_MANUAL.md`, `.github/workflows/ci.yml`,
  `tests/test_devices_page_vlan.js` (new).
- Tests: added `tests/test_devices_page_vlan.js`; full Node/Python/PHP suite,
  `py_compile`, `php -l`, `sh -n`, `msgfmt` and `git diff --check` all PASS.
- Deployed to testbed `192.168.20.23` with rollback backup retained at
  `/tmp/dm_deploy_backup_20260922075730`. Production `192.168.20.254` untouched;
  daemon, database, config.json and config.xml unchanged.
- Next step: authenticated testbed visual acceptance.


## Device Monitor: correct identities filter layout

Corrected the remaining authenticated visual defects in the Network Identities
VLAN filter without regressing the Apply/Clear interaction.

- Root cause (layout): a custom measured-gap sticky stack (`updateStickyOffsets()`
  with a cached `getBoundingClientRect()` gap) plus global `scroll-snap` let body
  rows overlap the column header, reordered the summary/toolbar/thead during
  scroll, left blank space below the title, and let the tabs scroll out of view.
- Root cause (count): `updateVlanLabel()` derived the button from the applied
  `activeVlans` state instead of the pending checkbox state, so the button could
  read "2 VLANs" while only one checkbox was selected.
- Change: removed all custom sticky positioning and `scroll-snap` (CSS and JS); the
  page now renders in natural DOM order and filtering preserves scroll position.
  `updateVlanLabel()` now counts checked VLANs ("All VLANs" / "1 VLAN" / "N VLANs")
  and is invoked on every checkbox change without filtering.
- Files changed: `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devices.volt`,
  `tests/test_devices_page_vlan.js`, `DECISIONS.md` (Decision 28).
- Tests: `tests/test_devices_page_vlan.js` extended (layout order, sticky removal,
  VLAN count state); full Node/Python/PHP suite, lint, `py_compile`, `sh -n`,
  `msgfmt`, Volt compile and `git diff --check` all PASS.
- Next step: authenticated testbed visual acceptance (top/middle/lower table,
  pending count, Apply, Clear, scroll preservation, tab visibility).


## Device Monitor: stable identities table header (DM-STICKY2)

Reintroduced a correct, stable sticky region on the Network Identities page
after the previous fragile custom sticky stack was removed.

- Root cause: removing the measured-gap sticky stack (`9701d1d`, Decision 28)
  fixed the overlap/jumping/tab coverage but also let the useful column header
  scroll away with long device lists. The page relies on normal document
  scrolling with the OPNsense top navbar fixed at ~62px, and no table ancestor
  clips the content, so CSS `position: sticky` is safe.
- Change: one sticky wrapper (`#devices-sticky-header`) now pins the summary
  counters and the VLAN/status toolbar, and the column headings
  (`#grid-devices thead th`) stick immediately below it. Offsets use CSS custom
  properties (`--devices-sticky-top`, `--devices-sticky-thead-top`) recalculated
  from live measurements on load, resize and genuine toolbar-height changes
  (`ResizeObserver`); measuring never triggers a table render. No scroll-snap,
  pseudo-element shield, cached one-shot geometry or `scrollIntoView` is used.
  Filtering, VLAN pending/applied semantics, Apply/Clear single-render and
  scroll preservation are unchanged.
- Files changed: `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devices.volt`,
  `tests/test_devices_page_vlan.js`, `DECISIONS.md` (Decision 29),
  `docs/USER_MANUAL.md`.
- Tests: 11 Node (UI), 13 Python and 11 PHP tests PASS; `php -l`, `py_compile`,
  `sh -n`, `msgfmt`, Volt compile and `git diff --check` PASS.
- Next step: authenticated testbed visual acceptance (sticky counters/toolbar/
  headings while scrolling, no row show-through, tabs not covered, pending VLAN
  count, Apply/Clear single-render without viewport jump, resize behaviour).


## Device Monitor: fix row bleed behind sticky column headings (DM-STICKY2B)

Authenticated screenshots confirmed the sticky region works but device-row text
("DMTEST", First/Last Seen dates) still showed through the column-heading band.

- Root cause: `#grid-devices` inherits Bootstrap's `border-collapse: collapse`;
  with the collapsed border model, browsers do not clip scrolled `tbody` cell
  content to the sticky `th` box, so rows bleed through despite the opaque
  heading background.
- Change: switch `#grid-devices` to `border-collapse: separate;
  border-spacing: 0` (each sticky `th` owns an opaque, contiguous box), and
  suppress the first body row's `border-top` so the single 1px heading
  separator is preserved. No change to sticky offsets, VLAN behaviour or
  scroll preservation.
- Files changed: `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devices.volt`,
  `tests/test_devices_page_vlan.js`, `DECISIONS.md` (Decision 29 refinement).
- Tests: 11 Node (UI), 13 Python and 11 PHP tests PASS; `php -l`, `py_compile`,
  `sh -n`, `msgfmt`, Volt compile and `git diff --check` PASS.
- Next step: authenticated testbed visual acceptance of the opaque heading band
  (new screenshots of the page top and of the scrolled heading band with the
  first visible row).


## Device Monitor: keep complete identities header visible (DM-STICKY2C)

DM-STICKY2B's visual acceptance failed: the complete page header still scrolled
away, and device-row content bled at the right edge in the narrow view.

- Root cause (incomplete header): the OPNsense page title
  (`header.page-content-head`) and the navigation tabs/explanatory text sat
  outside the sticky wrapper, so only the counters, toolbar and column
  headings stayed while scrolling.
- Root cause (edge bleed): the 13-column table overflowed `.content-box`
  horizontally, so rows painted beside the content-box-width sticky header.
- Change: make the OPNsense page title sticky (z-index 30); move the navigation
  tabs and explanatory text into the `#devices-sticky-header` wrapper; measure
  three offsets (title, header block, thead) on load/resize/`ResizeObserver`;
  and fix the table to the content width with `table-layout: fixed` plus a
  `<colgroup>` so it can no longer overflow around the header. The DM-STICKY2B
  separated border model is preserved.
- Files changed: `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devices.volt`,
  `tests/test_devices_page_vlan.js`, `DECISIONS.md` (Decision 29),
  `docs/USER_MANUAL.md`.
- Tests: 11 Node (UI), 13 Python and 11 PHP tests PASS; `php -l`, `py_compile`,
  `sh -n`, `msgfmt`, Volt compile and `git diff --check` PASS.
- Next step: authenticated testbed visual acceptance (three screenshots: page
  top; desktop scrolled; narrow/resized scrolled).


## Device Monitor: correct responsive identities table layout (DM-STICKY2D)

DM-STICKY2C failed visual acceptance: its fixed-percentage `table-layout: fixed`
layout squeezed the 13 columns, causing Services badges to overlap VLAN/Status,
VLAN/Status collision, First/Last Seen concatenation, excessive date/vendor
wrapping and tall rows; a blank gap also remained between the title and tabs.

- Root cause (gap): redundant `page-content-main`/`content-box-main` top
  padding plus the tabs' `margin-top:10px` stacked below the sticky title.
- Root cause (table): `table-layout: fixed` plus a percentage `<colgroup>`
  forced columns narrower than their content.
- Change: revert to natural (auto) column widths; remove the title-to-tabs gap
  (`padding-top:0` overrides + tabs `margin:0`); at narrower widths (<1200px)
  hide lower-priority columns (Services, Device Profile, Scan Status, First
  Seen, Last Seen) via a `devices-col-secondary` class + media query, keeping
  IP/Friendly Name/Hostname/MAC/Vendor/VLAN/Status/Actions usable. The sticky
  header and the DM-STICKY2B separated border model are preserved.
- Files changed: `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devices.volt`,
  `tests/test_devices_page_vlan.js`, `DECISIONS.md` (Decision 29),
  `docs/USER_MANUAL.md`.
- Tests: 11 Node (UI), 13 Python and 11 PHP tests PASS; `php -l`, `py_compile`,
  `sh -n`, `msgfmt`, Volt compile and `git diff --check` PASS.
- Next step: authenticated testbed visual acceptance (four screenshots: desktop
  page top; desktop scrolled; narrow page top; narrow scrolled).


## Device Monitor: contain identities table + clarify VLAN apply (DM-STICKY2E)

Contained the Network Identities table within its content box and clarified the
VLAN Apply workflow.

- Root cause (overflow/clipping): the 13-column table overflowed its content-box
  owner because the only responsive control was a viewport `max-width: 1199px`
  media query, so the wide table painted past the right edge (and beside the
  sticky header) whenever the content box was narrower than the viewport, clipping
  the First/Last Seen dates at the document edge.
- Root cause (seam): the toolbar's `border-bottom: 1px solid #333` and the table's
  `border-top: 2px solid #444` (under `border-collapse: separate`) formed a
  double-line seam that only appeared at the top of the page.
- Change (contain): replaced the viewport media query with
  `syncResponsiveColumns()`, which measures the table against its content-box
  owner (ResizeObserver + post-render + resize) and progressively hides
  Services -> Device Profile -> Scan Status -> First Seen -> Last Seen
  (`devices-hide-N` / `devices-col-sec-N`) - only as many as needed. Removed the
  table's redundant `border-top` so the toolbar border is the single separator.
- Change (VLAN workflow): removed the standalone VLAN **Clear** button and renamed
  **Apply** to **Apply VLAN Filter**. Checkbox changes only update the pending
  selection and the dropdown label (All VLANs / 1 VLAN / N VLANs); the button is
  muted+disabled while pending equals applied, and switches to the OPNsense orange
  action style (with an optional "Not applied" hint) only when they differ.
  Applying commits once, renders once, preserves scroll position, then disables;
  selecting all VLANs and applying restores the unfiltered view.
- Files changed: `devices.volt`, `tests/test_devices_page_vlan.js`,
  `DECISIONS.md` (Decision 29 refinement), both gettext catalogues,
  `docs/USER_MANUAL.md`.
- Tests: 11 Node (UI), 13 Python, 11 PHP PASS; `php -l`, `py_compile`, `sh -n`,
  `msgfmt`, Volt compile, `git diff --check` PASS.
- Deployment (`192.168.20.23`, guarded hostname/IP/source-hash): `devices.volt`
  and both compiled `.mo` catalogues deployed; Volt cache entry for
  `devices.volt` cleared; no service restart; production `192.168.20.254`
  untouched. Durable backup:
  `/var/backups/devicemonitor/dm-sticky2e-20260922-235424`.
- Next step: authenticated testbed visual acceptance (four screenshots: desktop
  top; desktop scrolled; narrow top; narrow scrolled). **VISUAL ACCEPTANCE:
  USER-PENDING** - do not claim the layout is fixed without those screenshots.

## Device Monitor: clarify empty VLAN selection and stabilise sticky offsets (DM-STICKY2F)

Clarified the empty VLAN-filter state and replaced the integer-rounded sticky
offset with fractional measurement.

- Root cause (VLAN empty state): clearing every VLAN checkbox previously
  collapsed to the "All VLANs" label, so an empty selection was ambiguous and
  could read as the unfiltered view. A zero-checked selection is now an
  incomplete draft rather than the all-VLAN choice.
- Root cause (sticky offset): the sticky heading offset was measured with
  integer `offsetHeight`, which rounds away sub-pixel fractions, so a prior
  `calc(... - 1px)` "tuck" experiment over-corrected the heading band (a
  +0.73px overlap against the toolbar bottom) and produced a visible 1px jump
  when scrolling began.
- Change (VLAN): a zero-checked selection now shows **Select a VLAN**, disables
  **Apply VLAN Filter** (muted, no pending hint) and keeps the last applied
  filter. `resolveVlanDraft()` resolves the pending checkboxes into a valid
  draft or a `{valid: false}` incomplete draft; an unapplied pending selection
  is preserved across a dropdown rebuild / data refresh (`pendingVlans` +
  `effectiveCheckedVlans()`). All-VLAN and subset behaviour is unchanged.
- Change (sticky): the three sticky offsets are now computed from fractional
  `getBoundingClientRect().height` measurements via `computeStickyOffsets()`;
  the heading band sticks flush beneath the toolbar with no `-1px` adjustment.
- Files changed: `devices.volt`, `tests/test_devices_page_vlan.js`, both gettext
  catalogues, `docs/USER_MANUAL.md`.
- Tests: 11 Node (UI), 13 Python, 11 PHP PASS; `php -l`, `py_compile`, `sh -n`,
  `msgfmt`, Volt compile, `git diff --check` PASS.
- Deployment: testbed `192.168.20.23` files already in parity with the
  authoritative checkout (`devices.volt` and both compiled `.mo` catalogues
  SHA256-verified identical); production `192.168.20.254` untouched.
- Visual acceptance (testbed `192.168.20.23`): VLAN empty state, pending state
  and the applied RE0 filter all observed working; tab outline stable; no
  row-text artifacts. Residual: a very minor text movement remains when
  scrolling begins (including at Firefox 100% zoom). This residual effect is
  not described as fixed, and no further CSS changes are planned for it.
- Next step: none for this change.


## Device navigation and terminology consolidation

Consolidated the Device Monitor submenu and terminology. Implemented, validated
and deployed to the testbed `192.168.20.23`. Production `192.168.20.254` was
not touched; no scan, provider, daemon or database behaviour was changed.

- Single **Devices** submenu entry replaces the separate **Devices** and
  **Physical Devices** entries (`Menu.xml`).
- Two tab-style views link between the existing routes:
  - **Network Identities** (`/ui/devicemonitor/index/devices`) — the MAC-level
    discovered-device table.
  - **Device Profiles** (`/ui/devicemonitor/index/physicaldevices`) — the
    user-confirmed real-world device grouping (formerly "Physical Devices").
- Terminology: "Physical Devices" → "Device Profiles", "Physical Device" →
  "Device Profile", "Create Device" → "Create Profile", "Device Summary" →
  "Profile Summary", "All/Current/Archived Devices" → "All/Current/Archived
  Profiles"; "Current Identities", "Previous Identities", "Add Identity" and
  "Unlink Identity" retained.
- All internal routes, URLs, controller actions, API endpoints, model methods,
  JSON fields and database identifiers remain unchanged (including
  `index/physicaldevices`, `physicaldevices`, `listphysicaldevices`,
  `createphysicaldevice`, `linkphysicaldeviceidentity`,
  `removephysicaldeviceidentity`, `physical_devices` and
  `physical_device_memberships`). No database migration.

Files changed: `Menu.xml`, `devices.volt`, `physicaldevices.volt`,
`devicehistory.volt`, `changesummary.volt`, `DeviceMonitor.php` (two
change-summary description strings), both gettext catalogues, the new
`tests/test_device_navigation.js`, `.github/workflows/ci.yml`,
`docs/USER_MANUAL.md`, and `DECISIONS.md` (Decision 27 supersedes the earlier
"Physical Device is retained" wording).

Validation (local): Python compile, PHP lint, shell syntax, gettext
(`msgfmt --check`), `git diff --check`, 10 Node (UI) tests, 13 Python tests and
11 PHP tests — all PASS.

Deployment (`192.168.20.23`, guarded): 8 runtime files (`Menu.xml`, four
`.volt` views, `DeviceMonitor.php`, both compiled `.mo` catalogues) deployed
with candidate/pre/post SHA256 parity and timestamped `cp -p` rollback backups.
Menu cache and Volt template cache invalidated; no service restart; daemon
unchanged. Unauthenticated route smoke check: HTTP 302 (no PHP fatal) for both
`/ui/devicemonitor/index/devices` and `/ui/devicemonitor/index/physicaldevices`.
Read-only DB safety unchanged (`devices.db`, `config.json`, `/conf/config.xml`
hashes identical to the pre-deployment state).

Next step: confirm the GitHub Actions CI run for this commit passes.

## Device navigation visual-acceptance follow-up

Applied a minimal follow-up to `cc7255e` to correct confirmed visual issues on
the Device Profiles view. Testbed `192.168.20.23` only; production
`192.168.20.254` was not touched. No routes, APIs, database, scanner, daemon,
config or existing profile data were changed.

- Device Profiles route now renders the same standard page heading as Network
  Identities (`Services: Device Monitor: Devices`) by setting `title` and
  `headTitle` in `IndexController::physicaldevicesAction()`.
- Device Profiles summary stat label changed from "Devices" to "Profiles"
  (`physicaldevices.volt`); a new `Profiles` msgid was added to both gettext
  catalogues (`en_US` → "Profiles", `cs_CZ` → "Profily").
- Network Identities explanatory text was already present from `cc7255e` and is
  unchanged.

Files changed: `IndexController.php`, `physicaldevices.volt`, both gettext
catalogues, `tests/test_device_navigation.js` (new heading check) and
`tests/test_physical_devices_page.js` (new summary-label checks).

Validation (local): Python compile, PHP lint, shell syntax, gettext
(`msgfmt --check`), `git diff --check`, 9 Node (UI) tests, 11 Python tests and
9 PHP tests — all PASS.

Deployment (`192.168.20.23`, guarded): 4 runtime files (`IndexController.php`,
`physicaldevices.volt`, both compiled `.mo` catalogues) deployed with
candidate/pre/post SHA256 parity and timestamped `cp -p` rollback backups.
Volt template cache entry for `physicaldevices.volt` cleared; menu cache not
affected (no `Menu.xml` change); no service restart. Unauthenticated route
smoke check: HTTP 302 for both `/ui/devicemonitor/index/devices` and
`/ui/devicemonitor/index/physicaldevices`. Deployed view verified to contain
the `Profiles` summary label; deployed controller verified to set the standard
heading; compiled `.mo` verified to contain `Profiles`/`Profily`. Read-only DB
safety unchanged (`devices.db`, `config.json`, `/conf/config.xml` hashes
identical to pre-deployment state).

Next step: commit, push and confirm the GitHub Actions CI run passes.

## v2.9 development — Pi-hole and Unbound experimental opt-in

Marked Pi-hole and Unbound hostname enrichment as **Experimental** and made Unbound
opt-in (disabled by default).

- New `unbound_enabled` setting (default `"0"`) wired through `defaults.json`,
  `ConfigController.php` (read/save/validation), the Settings Monitoring UI, and
  provider construction in `scan_network.py`.
- `get_unbound_hostnames()` is only called when `unbound_enabled` is set; a missing
  key after an upgrade means disabled.
- Pi-hole config fields (`pihole_enabled`, `pihole_url`, `pihole_password`) are now
  forwarded through `load_config()` so the runtime honours the GUI setting
  (previously these fields were never read from `config.json`).
- Experimental badges and descriptions added to the Settings UI (Pi-hole and
  Unbound), English/Czech gettext catalogues, README/README_CZ, and the user manual.
- `DECISIONS.md` Decision 26 records the change and supersedes Decision 24's
  "always available / no enable-disable setting" wording.
- New regression tests: `tests/test_pihole_config.php`,
  `tests/test_unbound_config.php`, Unbound opt-in coverage in
  `tests/test_unbound_provider.py`, and provider default coverage in
  `tests/test_fresh_install_defaults.py`.

Validation and deployment: see the commit for this change.


## Completed work — fail-closed monitored-interface scoping

Completed 21 September 2026 (commit message: "Device Monitor: enforce fail-closed
interface scoping").

- **Fail-closed monitored-interface scoping**: new `monitored_interfaces` setting
  (`defaults.json`, `ConfigController.php`), Settings UI with a fail-closed warning
  (`settings.volt`), and `scan_network.py` scoping (`resolve_monitored_networks`,
  `ip_is_in_scope`, `scoped_device_macs`, `get_hostwatch_devices(networks)`). An
  empty selection is refused and there is no LAN fallback.
- **Scoped status counters / identity events / notification cleanup / Nmap queue**
  (`scan_network.py`), plus a starvation fix: out-of-scope queued scans no longer
  consume the in-scope batch limit.
- **Superseded LAN-only Hostwatch priming** with selected-interface/subnet priming
  (`DECISIONS.md` Decision 25).
- **Filtered Devices-page summary counters** (`devices.volt`) with CI coverage
  (`tests/test_devices_page_summary.js`, `.github/workflows/ci.yml`).
- **Documentation**: `docs/USER_MANUAL.md`, `README.md`, `README_CZ.md` and gettext
  catalogues updated.
- **Deployment**: `devices.volt` deployed to the OPNsense testbed (SHA-256
  verified). Device Monitor daemon remains disabled/stopped; the live database was
  not modified.
- **Validation**: Node UI suite 9/9 PASS, PHP lint PASS, Python compile PASS, shell
  syntax PASS, `git diff --check` PASS.

## Current objective

`DM-BL-001` — User-confirmed physical-device identity grouping — is implemented
and complete. Its **Create**, **list existing groups**, **Link** and **Remove**
flows, plus member-count display, have all been live-validated on the physical
OPNsense testbed `192.168.20.23` (see "DM-BL-001 live validation, purge and
link-safety UX" below). Inactive identities are intentionally rejected as
physical-device group seeds; this is confirmed, expected behaviour and not a
defect. Its same-physical-device Link safety UX (commit `14ee00f`) is deployed
and live-confirmed.

The associated Device Monitor UI consistency work is complete and live-validated
on `192.168.20.23`: app-wide compact status/action sizing was visually
normalized, the compact Device Monitor selects were converted to OPNsense's
`bootstrap-select`/`selectpicker` pattern, and the dynamic Physical Device
`#physical-device-select` now uses selectpicker with AJAX refresh and preserved
option ordering. Live Firefox visual validation passed on `192.168.20.23`.

No new product-backlog feature is designated as the next implementation task;
`PRODUCT_BACKLOG.md` remains authoritative for deferred work.

Stage 2 — dedicated Physical Devices page redesign — is in progress:

- Unit 1 (read path): `247d30c` — `getPhysicalDevicesOverview()` + `GET
  /api/devicemonitor/devices/physicaldevices` (active + archived groups with
  full membership history). CI `35496385491`: PASS.
- Unit 2 (page): `92fb429` — dedicated **Physical Devices** page
  (`physicaldevices.volt`, menu entry, route `/ui/devicemonitor/index/physicaldevices`).
  CI `35497551473`: PASS.
- Unit 3 (Device Details summary): `bb0cbee` — Device Details grouping is now a
  compact read-only **Physical Device** summary linking to the dedicated page;
  create/link/remove management removed from Device Details. CI `35498323464`: PASS.
- Unit 4 (Devices-page badge): `184819e` — the Devices-page **Physical Device**
  badge now routes to `/ui/devicemonitor/index/physicaldevices?group=<id>`.
  CI `35498804635`: PASS.

Stage 2 (dedicated Physical Devices page redesign) is complete.

**Description:** Add an explicit user-controlled physical-device grouping layer
above existing MAC identities so multiple legitimate MAC addresses can be
identified as belonging to the same physical device.

**Benefit:** Reduces false interpretation of legitimate multiple MAC identities
while preserving the exact MAC, lifecycle, identity-event and activity history
already recorded by Device Monitor.

**Current design:** Grouping is additive only. Existing device rows, lifecycle
ownership, returning-device resolution and identity-conflict detection remain
authoritative and are not merged or rewritten. Membership changes are auditable
and reversible.

**Implementation status:** All four DM-BL-001 implementation units are
complete, committed, deployed and validated. The additive `physical_devices` and
`physical_device_memberships` schema, active-membership uniqueness protection,
read-only `getPhysicalDeviceForMac()` access, explicit model operations to
create a physical-device group, link a known identity and soft-remove a
membership, and the corresponding explicit Devices API actions are now
present. Removed memberships retain their history. The production grouping
baseline was left at zero: a temporary GUI test group was created during Create
validation and later intentionally purged (see "DM-BL-001 live validation, purge
and link-safety UX" below). Existing discovery, lifecycle, identity and
pre-existing UI behaviour remains unchanged. Read-model
commit `4f866ba`; write-model commit `f6d547f`; API commit `752ee59`; GitHub
Actions runs `34693021844`, `34693933012` and `34694963846`: PASS. The live API
controller deployment was hash-verified and retained rollback backup
`DevicesController.php.pre-dmbl001-api-20260912-225811`.

Unit 4 — the `Physical Device / Related Identities` section on the Device
Details page — is complete:

- commit `be9b686` — `feat: add physical device grouping UI`
- implemented in
  `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devicehistory.volt`
- permanent regression coverage in `tests/test_physical_device_ui.js`
- CI step `Validate physical-device UI` added to `.github/workflows/ci.yml`
- GitHub Actions run `34696074421` for `be9b686`: PASS
- deployed `devicehistory.volt` SHA256
  `39291eb3614a3241329ae5ddb279fd8de4fe9d078f1cd3ef1cb6d4c5e55b9d29`
- deployed hash matches the repository file exactly
- live GUI validation: Device Details displayed the new Physical Device /
  Related Identities panel correctly for an ungrouped MAC
- at the time of Unit 4, Create/Link/Remove write flows were deliberately
  **not** exercised against production; the later Create validation and the
  intentional purge of its temporary test group are recorded below
- current production baseline (after that purge) remains `physical_devices` = 0
  and `physical_device_memberships` = 0

Unit 5 — grouping-eligibility refinement — is complete, deployed and
live-validated:

- commit `c28c14d04d84465fc6d726d8ce038e7e4ef0b519` —
  `fix: enforce physical device grouping eligibility`
- exactly three implementation files changed:
  `.github/workflows/ci.yml`,
  `src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/DeviceMonitor.php`,
  `tests/test_device_lifecycle_actions.php`
- admission rules now require a current, active, resolved device identity to
  create a group, and a current, resolved device record to link an identity;
  unresolved or non-current identities (historical-only, deleted-only,
  lifecycle-only and `return_pending`) are rejected, and an inactive current
  identity is accepted only when the group already has an active current
  resolved member
- local lint and regression validation passed: `php -l` for both changed PHP
  files, the full `tests/test_device_lifecycle_actions.php` suite, plus
  `tests/test_physical_device_api.php` and `tests/test_physical_device_ui.js`
- GitHub Actions run `34734837042` for `c28c14d`: PASS, including the new CI
  step `Validate device lifecycle actions` (step 15), which executed and passed
- removal behaviour remains admission-independent, as deliberately covered by
  the regression suite; no last-active-member removal guard was added
- the grouping lifecycle behaviour approved in `DECISIONS.md` §18 is now
  **implemented and deployed**, with live validation where safe (Unit 6 below)
- still unresolved and out of scope: per-member UI/API state
- deployment status: **DEPLOYED to OPNsense on 13 September 2026** via the
  guarded procedure (staged hash + pre-state hash + backup hash + post-deploy
  hash verified inside a single success/failure guard chain); deployed
  `DeviceMonitor.php` SHA256
  `ac3c1b418ded15342bad12c37757ca681954144e2fd0952a345b80b05f305b74` matches the
  repository source exactly and permissions remain `644 root:wheel`
- rollback backup retained:
  `/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/DeviceMonitor.php.pre-dmbl001-eligibility-20260913-134556`
  (verified pre-deployment live SHA256
  `938aedbaadccbdbf1d2d782c2e5e2d43a57d3425096959287164ab6b8f40688b`)
- live validation: PHP syntax check PASS on the deployed file; class loads
  (`CLASS_OK`); `getGroupingEligibility()` present; `service devicemonitor
  status` running; Device Monitor API and UI paths return HTTP 302 (no PHP
  fatal); no new Device Monitor or PHP errors (the only two log error lines
  date from 8–9 September)
- no service restart/reload was required or performed: the model is loaded per
  web request and `opcache.validate_timestamps => On`, and the Python daemon
  does not use PHP
- live grouping data (read-only): 45 devices (32 active), `return_pending` 0,
  `lifecycle_id` NULL 0, `physical_devices` 0, active memberships 0, lifecycles
  45 active / 0 archived, `deleted_devices` 1; 32 identities are eligible group
  seeds, 13 are inactive current resolved identities, 0 are lifecycle-only
  historical and 1 is deleted-only historical
- live create/link/remove **write** branches were deliberately not exercised:
  no live groups exist and creating them would add production groupings without
  user intent, so those branches remain regression-validated only via
  `tests/test_device_lifecycle_actions.php`

Unit 6 — the `DECISIONS.md` §18 grouping lifecycle behaviour — is implemented,
deployed and live-validated where safe:

- commit `d0f82b8e74513a6c09881b33f0095da3ccda6757` —
  `fix: enforce physical device grouping lifecycle`
- exactly two files changed (424 insertions, no deletions):
  `src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/DeviceMonitor.php` (+106)
  and `tests/test_device_lifecycle_actions.php` (+318)
- implemented behaviour: removing the final active membership remains allowed and
  is never blocked; membership removal remains a soft-close that preserves
  history; a group reaching zero active memberships now archives automatically
  via `archived_at` with no unarchive path; `deleteDevice()` soft-closes the
  deleted MAC's active memberships and then archives any affected empty group;
  `clearAll()` applies equivalent set-based semantics; no group or membership row
  is ever deleted
- the grouping admission rules introduced by `c28c14d` are unchanged, and the
  protected lifecycle/API/UI regressions still pass
- local validation: 13 PASS markers in `tests/test_device_lifecycle_actions.php`,
  including the new `DEVICE_PHYSICAL_GROUP_EMPTY_ARCHIVAL`,
  `DEVICE_PHYSICAL_GROUP_DELETE_CLEANUP` and
  `DEVICE_PHYSICAL_GROUP_CLEARALL_CLEANUP`; `tests/test_device_timeline.php`,
  `tests/test_device_timeline_history_preservation.php`,
  `tests/test_physical_device_api.php` and `tests/test_physical_device_ui.js`
  all pass
- GitHub Actions run `34738596652` for `d0f82b8`: PASS, including the
  `Validate device lifecycle actions` step (step 15)
- deployment status: **DEPLOYED to OPNsense on 13 September 2026** via the
  guarded procedure (staged hash + expected-predecessor hash + backup hash +
  post-deploy hash verified inside a single success/failure guard chain);
  deployed SHA256
  `2d903bb0a886da88d351754ed8fec5228b25a33f6b21225903cc230b268592fc` matches the
  repository source exactly and permissions remain `644 root:wheel`
- rollback backup retained:
  `/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/DeviceMonitor.php.pre-dmbl001-lifecycle-20260913-150103`
  (verified predecessor SHA256
  `ac3c1b418ded15342bad12c37757ca681954144e2fd0952a345b80b05f305b74`)
- live validation: PHP lint PASS; class loads (`CLASS_OK`); the §18 helpers and
  all three call sites are present in the deployed file; `service devicemonitor
  status` running; API and UI paths return HTTP 302 (no PHP fatal); no new
  Device Monitor or PHP errors; no service restart was required or performed
  (model loaded per web request, `opcache.validate_timestamps => On`, and the
  Python daemon does not use PHP)
- live grouping state before and after deployment is unchanged: one active
  user-created group (`Daikin Controller Entry`, id 1) with one open membership
  for `b4:8c:9d:73:20:98` (active, resolved, lifecycle 12); zero archived groups,
  zero empty active groups and zero orphan active memberships
- live-observed: deployed bytes equal the validated source; the existing active
  group was not archived by the emptiness rule; the archive predicate currently
  matches no group
- regression-validated only (no safe live fixture): non-final versus final member
  removal archival, `deleteDevice()` membership closure plus archival, and
  `clearAll()` equivalent semantics — all covered by the `d0f82b8` suite
- admission behaviour is unchanged (the `c28c14d` helper and guards are present
  in the deployed file); no orphan-membership backfill was performed
- observations retained without adding scope: the set-based
  `archiveEmptyPhysicalDevices()` can archive any active group with zero open
  memberships, not only groups touched by the current delete/clear operation;
  legacy orphan memberships are not retroactively repaired by this unit; the
  Devices-page grouping indicator that was then future UI work is delivered by
  Unit 7 below

Unit 7 — Devices-page Physical Device grouping indicator — is implemented,
deployed and live-validated:

- commit `7ca0fb9f575525b848d395a9d9c9f9f4b02eadf1` —
  `feat: show physical device grouping on Devices page`
- five files changed (325 insertions, 1 deletion): `.github/workflows/ci.yml`,
  `src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/DeviceMonitor.php`,
  `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devices.volt`,
  `tests/test_device_lifecycle_actions.php` and the new
  `tests/test_devices_page_grouping.js`; only the model and the view are
  deployable
- GitHub Actions run `34741415761` for `7ca0fb9`: PASS, including the new
  `Validate devices page grouping indicator` step (step 15) and
  `Validate device lifecycle actions` (step 16)
- read path: `getDevices()` loads grouping metadata with a single bulk query
  keyed by MAC (active memberships of non-archived groups) and merges it per row;
  there is no per-row `getPhysicalDeviceForMac()` call
- UI: a compact `Physical Device` column after `Status`; grouped rows show a
  clickable badge `Name · N identity|identities` and ungrouped rows show a quiet
  em-dash; the badge links to
  `/ui/devicemonitor/index/devicehistory?mac=<mac>#physical-device-grouping`;
  no grouping create/link/remove controls were added to the Devices table
- deployment status: **DEPLOYED to OPNsense on 13 September 2026** via the
  guarded procedure (staged hash + predecessor hash + backup hash + post-deploy
  hash verified inside one success/failure guard chain); deployed SHA256
  `ac5aa08d47eb8d165fd04d4732356f2b44c70f62bd5ed4e0ae53556818907110`
  (`DeviceMonitor.php`) and
  `a8ccde0833f0524bbfcba0b3a562be477cf4310c6c1463fb588a16d5f491f7ad`
  (`devices.volt`) both match the repository source exactly; permissions remain
  `644 root:wheel`
- rollback backups retained:
  `DeviceMonitor.php.pre-dmbl001-devices-ui-20260913-160832` (predecessor
  `2d903bb0a886da88d351754ed8fec5228b25a33f6b21225903cc230b268592fc`) and
  `devices.volt.pre-dmbl001-devices-ui-20260913-160832` (predecessor
  `e14ccd0f3d3a9d3aa300c5dfcec12a34e8a24f154e08fee958084a83d4248091`, which
  matched the repository version at every earlier commit checked — no live drift)
- live validation: PHP lint PASS; class loads (`CLASS_OK`); the deployed view
  contains the column, grouping helper, badge and `#physical-device-grouping`
  fragment and no grouping-management controls; the Device History page still
  carries the grouping anchor; API and UI routes return HTTP 302 (no PHP fatal);
  no new PHP or Device Monitor errors; no service restart was required or
  performed
- live grouping data at the time of this deployment (read-only, unchanged by
  this deployment): one active group (`Daikin Controller Entry`, id 1) with one
  open membership for `b4:8c:9d:73:20:98`; the deployed read-path query returned
  `b4:8c:9d:73:20:98 | 1 | Daikin Controller Entry | 1`, so that device presented
  as grouped with one identity while sampled devices remained ungrouped. That
  group was subsequently intentionally purged (see "DM-BL-001 live validation,
  purge and link-safety UX" below); the current live baseline is 0/0
- authenticated visual click-through of the live page was not performed by Cline
  (no GUI/API credentials available); the items above are the executed live
  evidence, and user confirmation of the rendered column and badge is advisable
- grouping admission (`c28c14d`) and lifecycle (`d0f82b8`) write semantics are
  unchanged, and no database write occurred during this deployment

## Stage 3 — Device Details / lifecycle usability redesign

Stage 3 is complete. Stage 1 (UI/header consistency) and Stage 2 (device
identity/grouping redesign) remain complete; Stage 2 is deployed and GUI
validated on `192.168.20.23`.

Design:

- Device Details is reframed as a concise operational summary of one MAC
  identity and its lifecycle context, with explicit navigation to Device
  Activity and grouping management rather than duplicating those pages.
- Panel order is now: Device Summary, Physical Device, Lifecycle History, Notes.
- Device Summary leads with **IP Address**, then **Friendly Name**, **Hostname**
  (with its source, when known), **MAC Address**, **Vendor**; the second column
  shows **Status**, **VLAN**, **First Seen**, **Last Seen**, **Current
  Lifecycle**. The separate Notes-count row was removed (notes live in the
  Notes panel).
- Lifecycle History gained a plain-language explanation and reordered columns
  (**Lifecycle, Status, IP Address, Friendly Name, Hostname, Vendor, VLAN,
  First Seen, Last Seen, Notes, Actions**); the Lifecycle column now shows the
  lifecycle number (`#n`).
- Returning-device semantics and controls (Start New Lifecycle / Relink) are
  unchanged; timestamped lifecycle comments remain historical.

Terminology:

- The user-facing term **Physical Device** is retained. The underlying model
  (one real-world device with multiple network identities/interfaces) is
  already described in `DECISIONS.md` §17 and the user manual, and members are
  already labelled "identities". No backend/database identifier was renamed.
- `DM-BL-004` (Unbound) and `DM-BL-007` (Pi-hole) are already complete in this
  repository and were deliberately not modified; they remain outside the
  Stage 3 release boundary, so `PRODUCT_BACKLOG.md` was left unchanged (it
  already records no open backlog items).

Files changed:

- `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devicehistory.volt`
- `src/opnsense/mvc/app/languages/en_US_devicemonitor.po`
- `src/opnsense/mvc/app/languages/cs_CZ_devicemonitor.po`
- `tests/test_device_details_ui.js` (new)
- `.github/workflows/ci.yml`
- `docs/USER_MANUAL.md`

Implementation commit:

- `5c45464` — `feat: redesign Device Details summary and lifecycle presentation`

Validation:

- full Node (UI) suite: PASS (incl. new `test_device_details_ui.js`)
- full PHP suite: PASS
- full Python suite: PASS
- PHP lint / Python compile / shell syntax / gettext (`msgfmt -c`): PASS
- `git diff --check`: PASS
- GitHub Actions: PASS (run `35502449067`)

Deployment (`192.168.20.23`):

- guarded deployment of `devicehistory.volt` and both compiled `.mo` catalogues
  (candidate/pre/post SHA256, timestamped `cp -p` rollback backups): PASS
- no `Menu.xml` change, so the OPNsense menu cache was not invalidated
- stale compiled `devicehistory.volt` Volt template removed to force recompilation
- no service restart / php-fpm reload / daemon change (file-only deployment)
- read-only DB safety counts unchanged by the deployment
- unauthenticated route smoke check (HTTP 302, no PHP fatal): PASS

GUI validation:

- authenticated visual click-through was not performed by Cline (no GUI
  credentials); a human validation checklist is provided in the final report.

## TESTBED environment and migration state

The Device Monitor testbed/development environment has been migrated to the
physical OPNsense host `192.168.20.23`.

- OPNsense `26.7.4`
- management and current LAN interface: `re0` `192.168.20.23/24`
- repository: `/root/src/opnsense-devicemonitor-upstream`
- branch: `v2.9-development`
- repository and GitHub origin verified synchronized at migration completion
- deployed Device Monitor files verified identical to the authoritative checkout
- testbed runtime state migrated from the former `192.168.56.2` VM:
  8 devices and 8 lifecycles
- automatic Device Monitor monitoring is deliberately disabled because `re0`
  is attached to the live `192.168.20.0/24` LAN; it must not be enabled until
  an intentionally isolated test interface/network is provided
- production OPNsense `192.168.20.254` was not modified by this migration
- retired and deleted VirtualBox VMs:
  `FreeBSD-15.1-DeviceMonitor`,
  `FreeBSD-15.1-DeviceMonitor-30G`, and
  `OPNsense-Testbed` (`192.168.56.2`)
- migration-critical runtime state is stored outside Git in:
  `/var/db/devicemonitor/config.json` and
  `/var/db/devicemonitor/devices.db`
## DM-BL-001 live validation, purge and link-safety UX

DM-BL-001 is complete, committed and deployed. Its live GUI validation —
completed on the testbed `192.168.20.23` — is recorded as follows.

### Create flow — live-validated

- **Create Physical Device** was manually validated through the OPNsense GUI.
- The resulting temporary test group (`Daikin Controller Entry`) existed only to
  validate the Create write flow and was later **intentionally TRUE-DELETED** as
  an authorised direct DB maintenance action, after: exact-state verification, a
  SQLite online backup, backup `PRAGMA integrity_check`, a guarded
  `BEGIN IMMEDIATE` transactional deletion (1 row from
  `physical_device_memberships`, 1 row from `physical_devices`, each guarded),
  and a post-delete `PRAGMA integrity_check`.
- Purge backup retained:
  `/var/backups/devicemonitor/devices.db.pre-test-group-purge-20260913-133147`
  (SHA256 `64b237651a5a14a8aeb90ac451e9a214689d64d845a6f71d6cf2d6871c60ed80`).
- The test group no longer exists and production retains no grouping rows.

### Full write-flow validation — live-validated on testbed

The complete DM-BL-001 grouping workflow was live-validated on the physical
OPNsense testbed `192.168.20.23`:

- **Create Physical Device**: PASS
- **Existing-group list** (dropdown): PASS
- **Member count** display: PASS
- **Link identity**: PASS
- **Remove identity**: PASS
- **Inactive identity rejection**: PASS — inactive identities intentionally
  cannot seed a physical-device group; this is confirmed, expected behaviour
  and not a defect

### Link-safety UX — deployed

- commit `14ee00f` — `fix: clarify physical device identity linking`
- changes: persistent helper warning adjacent to the Link Identity controls
  (`#physical-device-link-guidance`) and a strengthened SAME-physical-hardware
  `confirm()`; assertions added to `tests/test_physical_device_ui.js`
- no backend, schema, API or grouping-eligibility semantics changed; Create and
  Remove semantics are unchanged
- GitHub Actions run `34760874169` for `14ee00f`: PASS
- deployed `devicehistory.volt` SHA256
  `1d2498a353313c731d01fa2cb7f3ce75680512e16911868ce97175fba3f4d641` matches the
  repository source exactly; permissions remain `644 root:wheel`
- rollback backup retained:
  `devicehistory.volt.pre-dmbl001-linksafety-20260913-135353` (verified
  pre-deployment live SHA256
  `39291eb3614a3241329ae5ddb279fd8de4fe9d078f1cd3ef1cb6d4c5e55b9d29`, which
  equalled the predecessor commit `d83cd194` version — no live drift)
- no service restart was required or performed (the Volt view is loaded per
  request and the Python daemon does not use PHP)
- live baseline at this point: `physical_devices` = 0 and
  `physical_device_memberships` = 0; live `PRAGMA integrity_check` = ok

### Next environment objective

`192.168.20.23` is the physical Device Monitor testbed, but it is not isolated:
its `re0` interface sits on the live `192.168.20.0/24` LAN, so Device Monitor
automatic monitoring remains deliberately disabled. A genuinely isolated
interface/network remains the next environment objective before further
consequential live experimentation. No new product-backlog feature is designated
as the next implementation task.

The CrowdSec false-positive SSH brute-force defect caused by Device Monitor
service discovery is complete, deployed and validated live. After receiving a
valid SSH banner, the probe now sends a standards-compliant
`SSH_MSG_DISCONNECT` before closing. The existing `ssh_banner` service identity
and CrowdSec configuration remain unchanged.

Commit: `5d55be4` — `fix: cleanly disconnect SSH service probes`
CI: run `34684029960` — PASS.

## UI consistency and selectpicker conversion

App-wide compact status/action visual normalization and the conversion of
compact Device Monitor selects to OPNsense's `bootstrap-select`/`selectpicker`
pattern are complete and live-validated on the testbed `192.168.20.23`.

- App-wide compact status/action sizing was visually normalized; the approved
  compact status scale is 13px font / line-height 1.5 / padding 1px 5px /
  3px radius / 1px transparent border.
- Static compact selects converted to selectpicker:
  - `devices.volt` `#filter-status` (`btn-default btn-sm`)
  - `infrastructureservices.volt` `#services-type-filter`,
    `#services-status-filter` (`btn-default btn-sm`); `#services-type-filter`
    is AJAX-populated and now refreshes the selectpicker after appending types
  - `identityevents.volt` `#identity-events-status`, `#identity-events-limit`
    (`btn-default btn-xs`)
  - `scanhistory.volt` `#scan-history-limit` (`btn-default btn-xs`)
- Dynamic Physical Device `#physical-device-select` (`devicehistory.volt`)
  converted to selectpicker (`btn-default btn-xs`), initialized after DOM
  insertion and refreshed after the AJAX group list loads; option ordering
  (placeholder, existing groups, `+ Create new physical device...` last) is
  preserved.
- Live Firefox visual validation on `192.168.20.23`: PASS (Devices, Infrastructure
  Services, Identity Events, Nmap Scan History, and Device Details).
- Obsolete native-select vertical-metric CSS (heights, paddings, line-heights,
  and the `form-control input-sm` select styling) removed across the affected
  views.
- New regression coverage: `tests/test_selectpicker_static.js`; extended
  `tests/test_physical_device_ui.js`; CI step added in
  `.github/workflows/ci.yml`.
- The five affected views were deployed to the testbed with SHA256 verification
  and a rollback backup retained at
  `/root/dm-selectpicker-backup-20260918-123459`.

## Previously completed

- v2.8 IP & MAC Conflicts supports All/Unresolved/Resolved filtering through the Status selector and clickable Unresolved/Resolved summary links.

- v2.8 IP & MAC Conflicts heading shows separate Unresolved and Resolved counts; filtering remains through the Status selector.

- v2.8 IP & MAC Conflicts heading now shows separate Unresolved and Resolved counts.

- v2.8 IP & MAC Conflicts table now shows an explicit Unresolved/Resolved status badge.

- v2.8 IP & MAC Conflicts resolution filter implemented for All, Unresolved and Resolved events.

- v2.8 IP & MAC Conflicts Resolve/Reopen API and UI implemented; event history is preserved through the existing `resolved_at` field.

- v2.7 release preparation completed: version metadata, English/Czech version history, installation references and automated identity regression coverage are current.

- Added automated v2.7 identity regression coverage using isolated temporary SQLite databases.

- v2.7 README/version-history documentation updated for identity anomaly detection and IP & MAC Conflicts.

- Phase F.2 IPv6 identity-conflict detection completed and validated.
- Device Monitor IP & MAC Conflicts API/runtime completed and validated.
- IP & MAC Conflicts UI deployed and validated on OPNsense.
- IP & MAC Conflicts UI committed as `418ea5c`.
- Full Device Monitor scans completed successfully with deployed identity detection enabled.
- No identity anomalies were recorded during the validated scans.

## Settings-page work (committed)

The Settings UI restructuring and About-page metadata changes described below
are present in the committed tree. There is no current uncommitted
`settings.volt` change: the worktree was verified clean at `0b6496a`. That work
included:

- Monitoring tab
- Nmap Scanning tab
- removal/replacement of the previous Other Settings tab arrangement
- developer attribution
- development repository link
- Licensing & Compatibility section heading


## Current validation

Current validated work:

- `git diff --check`: PASS
- Licensing & Compatibility source inspection: PASS
- deployment to OPNsense: PASS
- live browser validation of all Settings tabs after deployment: PASS
- populated IP & MAC Conflicts row rendering using browser-only synthetic API data: PASS
- IP & MAC Conflicts expandable details rendering: PASS
- browser refresh restored the real empty-state API view: PASS
- GitHub push to `origin/v2.8-development`: PASS
- CI workflow includes `v2.8-development` for push and pull requests: PASS
- GitHub Actions CI run for `cf1a90e`: PASS
- v2.8 identity-email `git diff --check`: PASS
- live `scan_network.py` Python syntax validation: PASS
- isolated identity-email sent/skipped/invalid-result handling: PASS
- live `notify_identity_email.php` PHP syntax validation: PASS
- live synthetic IP & MAC conflict email delivery: PASS
- configured recipient validation: PASS
- final subject validation: `OPNsense: IP & MAC conflict alert (1 conflict)`: PASS
- final live email pluralisation validation (`conflict` / `conflicts`): PASS
- final live email font consistency validation (Arial body / monospace technical values): PASS
- final live email value-column alignment validation: PASS
- final live email visual consistency validation: PASS
- identity-conflict email commit `c92b61b`: PASS
- push of `c92b61b` to `origin/v2.8-development`: PASS
- GitHub Actions CI run `33970099256` for `c92b61b`: PASS
- observational-only message wording and IP/MAC evidence rendering: PASS
- Phase 3 single-host Nmap regression: PASS
- Phase 3 Nmap serialisation and SMB-Nmap serialisation: PASS
- Phase 3 lightweight protocol-probe worker bound (maximum 12): PASS
- Phase 3 protocol regression for SMB, NFS, RDP, VNC, WinRM, LDAP, SNMP/Kerberos/VPN classification and WireGuard runtime discovery: PASS
- Phase 3 strong-Nmap-evidence handling (`open|filtered` and unidentified services rejected): PASS
- isolated three-host real-network Phase 3 test: PASS
- isolated real-network test preserved the live Device Monitor database: PASS
- automatic fresh Phase 3 Nmap sweep removed after performance validation: PASS
- Phase 3 live deployment with pre-deployment SQLite backup: PASS
- live `--discover-services` execution: exit 0
- live Phase 3 RDP discovery: `192.168.20.111:3389/tcp` — verified
- live Phase 3 SMB discovery: `192.168.20.111:445/tcp` — verified, SMB 3.1.1
- live Phase 3 SNMP discovery: `192.168.20.214:161/udp` — structured Nmap service evidence
- live Phase 3 WireGuard discovery: `192.168.20.254:51821/udp` — authoritative runtime evidence
- Infrastructure Services Phase 3 UI groups and column alignment visually validated: PASS
- isolated Phase 3 active-service lifecycle regression using temporary SQLite: PASS
- Phase 3 Available -> Unavailable transition across all 8 actively verified service methods: PASS
- Phase 3 Unavailable -> Available recovery: PASS
- Phase 3 failed verification preserves the last known-good `last_verified`: PASS
- Phase 3 successful recovery refreshes `last_verified`: PASS
- Infrastructure Services actual UI stale-state JavaScript regression: PASS
- exact two-hour stale boundary: PASS
- older-than-two-hours, missing and invalid `last_verified` values derive Stale: PASS
- explicit Unavailable status takes precedence over derived Stale: PASS
- permanent Phase 3 infrastructure-service Python regression added: PASS
- permanent Infrastructure Services stale-state JavaScript regression added: PASS
- permanent Phase 3 regression validates no automatic fresh Nmap identification: PASS
- permanent Phase 3 regression validates one literal IPv4 per Nmap invocation: PASS
- permanent Phase 3 regression validates serial Nmap and SMB execution: PASS
- permanent Phase 3 regression validates lightweight worker bound of 12: PASS
- permanent Phase 3 regression validates strong Nmap evidence handling: PASS
- permanent Phase 3 regression validates Available -> Unavailable -> Available recovery: PASS
- SSH clean-disconnect focused regression: PASS
- SSH disconnect-send failure remains non-fatal after valid banner verification: PASS
- live OPNsense SSH self-probe still identifies OpenSSH correctly: PASS
- live sshd log now records `Received disconnect ... Device Monitor service probe complete [preauth]`: PASS
- no new self-generated `Connection closed by 192.168.20.254 ... [preauth]` after deployment: PASS
- GitHub Actions CI run `34684029960` for `5d55be4`: PASS

## Infrastructure service discovery — Phase 1

Phase 1 is implemented and validated live.

Implemented and verified:

- persistent infrastructure-service inventory
- protocol-verified DHCP discovery
- protocol-verified DNS discovery
- OPNsense-configured DNS resolvers included as candidates
- DHCP and DNS availability lifecycle handling
- `last_verified` persistence
- automatic discovery rate-limited to 3600 seconds
- manual `--discover-services` mode
- Devices page Services badges

Validated live inventory:

- DHCP `192.168.20.254` — UDP/67 — verified
- DNS `192.168.20.1` — UDP/53 — verified
- DNS `192.168.20.2` — UDP/53 — verified
- DNS `192.168.20.101` — UDP/53 — verified

Automatic discovery rate limiting was validated with an immediate repeat
returning `RAN=False`.

The Devices UI was visually validated after correcting the Services/VLAN
column alignment.

## AdGuard Home DNS rewrite hostname enrichment

Optional AdGuard Home DNS rewrite hostname enrichment is implemented and
validated on `v2.8-development`. The released `v2.8` tag remains unchanged.

- feature is disabled by default
- users explicitly configure their own AdGuard Home HTTPS URL, username and password
- automatic hostname precedence is:
  `AdGuard rewrite > Dnsmasq > Kea > ISC > Hostwatch`
- `custom_hostname` remains a separate user-controlled Friendly Name and is untouched
- only literal IPv4 rewrite answers are accepted
- CNAME/non-IP and IPv6 answers are ignored
- conflicting domains for the same IPv4 address are skipped as ambiguous
- scanner independently enforces HTTPS even if `config.json` is manually edited
- TLS certificate verification remains enabled through the system trust store
- HTTP redirects are disabled so the Basic Authorization header cannot be forwarded
- API/network/JSON failures are fail-soft and do not abort normal device scanning
- credentials are not placed on command lines or written to Device Monitor logs
- configuration validation rejects HTTP URLs, embedded credentials, query/fragment components and missing credentials when enabled
- live OPNsense deployment completed with pre-deployment backup and SHA256 verification
- no service restart was required; `scan_network.py` is invoked on demand through
  `actions_devicemonitor.conf`
- live authenticated AdGuard helper returned five expected IPv4 rewrite mappings
- live Device Monitor log reported `AdGuard DNS rewrites: 5 IPv4 hostname mappings`
- database hostnames for all five mapped devices matched the configured rewrites

Files changed:

- `.github/workflows/ci.yml`
- `DECISIONS.md`
- `PROJECT_STATE.md`
- `src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/ConfigController.php`
- `src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json`
- `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt`
- `src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py`
- `tests/test_adguard_config.php`
- `tests/test_adguard_rewrites.py`

Validation:

- Python candidate syntax: PASS
- PHP controller candidate syntax: PASS
- AdGuard Python regression suite: PASS
- existing Phase 3 Python regression suite: PASS
- PHP controller rejection tests on OPNsense, including unsafe URL components: PASS
- valid-save PHP test deliberately skipped when using the real live model
- `git diff --check`: PASS apart from existing CRLF/LF informational warnings
- live deployed SHA256 values matched the local candidate files exactly
- implementation commit `e854f0b` pushed to `origin/v2.8-development`
- GitHub Actions Device Monitor CI run `34177589841` for `e854f0b`: PASS

## Known unresolved issues

- No known unresolved Phase 1 DHCP/DNS service-discovery issues remain.
- No known unresolved v2.8 identity-conflict email issues remain.
- No known unresolved Device Monitor version-display issues remain.

## Current operating values

- monitored interface: IGC1
- scan interval: 300 seconds
- infrastructure-service discovery interval: 3600 seconds

## Infrastructure Services page

A dedicated Infrastructure Services page is implemented and visually
validated.

The page:

- reads the persistent `device_services` inventory through a read-only API
- groups services by infrastructure role
- shows IP, hostname, status, port/protocol, interface/VLAN, detection method,
  confidence, product/version and last verified time
- includes service-type, status and text-search filters
- shows both available and unavailable known services
- currently displays the verified DHCP and DNS Phase 1 inventory
- is designed to automatically accommodate later NTP, SSH, Web/Admin and other
  infrastructure-service discovery phases

The page is available from:

`Services -> Device Monitor -> Infrastructure Services`

Menu registration, routing, API loading and UI rendering were validated live.
Toolbar selector alignment was corrected and visually approved.

## Infrastructure service discovery — Phase 2

Phase 2 is implemented and validated live.

Protocol-verified discovery now includes:

- NTP using a real NTP request/response
- SSH using the SSH server identification banner
- Web/Admin services using real HTTP/HTTPS responses

Nmap evidence may identify non-standard SSH or web ports, but a service is
not marked verified until its protocol probe succeeds.

Validated live Phase 2 inventory:

- 2 NTP endpoints
- 7 SSH endpoints
- 14 HTTP/HTTPS endpoints

Observed verified products included OpenSSH, Dropbear, nginx, TP-LINK HTTPD,
GoAhead-Webs and OPNsense web services.

The Infrastructure Services page now displays DHCP, DNS, NTP, SSH and
Web/Admin Services. All service groups use consistent column positions.

## Infrastructure service discovery — Phase 3

Phase 3 is implemented and validated live.

Supported service roles now include:

- SMB and NFS file services
- RDP, VNC and WinRM remote access
- SNMP management
- LDAP and LDAPS directory services
- Kerberos authentication services
- VPN endpoints

Evidence handling is intentionally conservative:

- SMB, NFS, RDP, VNC, WinRM and LDAP/LDAPS use protocol-specific verification.
- SNMP, Kerberos and non-local VPN identification require structured Nmap
  service evidence; an open port alone is not sufficient.
- `open|filtered` Nmap results are not treated as proof of a service.
- local OPNsense WireGuard is discovered from authoritative `wg` runtime state.
- automatic Phase 3 discovery reuses existing targeted Nmap evidence and does
  not launch a fresh Nmap sweep across all known devices.
- any Nmap invocation used by Phase 3 remains limited to one literal IPv4
  target at a time.

Live Phase 3 inventory validated:

- RDP `192.168.20.111:3389/tcp` — verified
- SMB `192.168.20.111:445/tcp` — verified, SMB 3.1.1
- SNMP `192.168.20.214:161/udp` — discovered from Nmap service evidence
- WireGuard `192.168.20.254:51821/udp` — authoritative OPNsense runtime evidence

The Infrastructure Services page was visually validated with the new
File / NAS Services, Remote Access, SNMP / Management and VPN Endpoints
groups.

## Known unresolved issues

- No known unresolved Phase 1 DHCP/DNS discovery issues remain.
- No known unresolved Phase 2 NTP/SSH/Web discovery issues remain.

## Infrastructure Services usability foundations

Infrastructure Services usability improvements are implemented and validated.

Added:

- Discover Now button with automatic refresh after discovery
- consolidated evidence for duplicate service endpoints
- Available, Unavailable and Stale presentation states
- Stale after two missed hourly verification windows
- consolidated service counts
- consistent column positions across all service groups
- Last Verified timestamps wrap cleanly
- IPv4 column accommodates addresses such as `192.168.xxx.xxx` without wrapping

Discover Now was tested successfully against the live service inventory.

## v2.8 metadata, hostname and friendly-name work

Completed and validated:

- version metadata and user-facing v2.8 wording are consistent
- About-page summary and `IP and MAC` wording are current
- Kea DHCP hostname enrichment is implemented and live validated
- five active named Kea leases were confirmed to populate detected hostnames
- Friendly Name is stored separately in `custom_hostname`
- detected Hostname remains in `hostname`
- Friendly Name save, persistence across scan, and clear behaviour were validated live
- clearing a Friendly Name now reports `Friendly name cleared`
- Devices exposes Friendly Name, Hostname, First Seen and Last Seen separately
- CSV export includes Friendly Name, Hostname, First Seen and Last Seen
- Infrastructure Services search/display supports Friendly Name without hiding Hostname
- PHP syntax, Python syntax, gettext catalogues and `git diff --check` passed
- live Device Monitor daemon remained running during deployment
- stale Infrastructure Services were traced to the daemon having been cleanly stopped;
  restarting it restored scheduled discovery, so no stale-state source fix was required

Files changed for hostname/friendly-name task:

- `src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/DevicesController.php`
- `src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/DeviceMonitor.php`
- `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devices.volt`
- `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/infrastructureservices.volt`
- `src/opnsense/mvc/app/languages/en_US_devicemonitor.po`
- `src/opnsense/mvc/app/languages/cs_CZ_devicemonitor.po`
- `src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py`

Related completed commits already on `origin/v2.8-development`:

- `9f27bcd` — `Add Kea DHCP hostname enrichment to device discovery`
- `7550774` — `Update Device Monitor v2.8 UI wording and about description`
- `f714254` — `Display device friendly names with hostname fallback`

Commit `5188dcb` supersedes the fallback behaviour from `f714254`
by preserving Friendly Name and detected Hostname as separate identity fields.

## UK English standardisation

Repository-wide English-language review completed and validated.

- user-visible English, documentation and project-owned comments use UK English
- technical syntax and externally defined identifiers remain unchanged, including CSS/JS
  `color`/`center`, `grep --color`, the OPNsense `en_US` locale filename and `LICENSE`
- user-facing `License` was changed to `Licence`
- the official legal name `BSD 2-Clause License` remains unchanged
- README and About-page licence metadata were corrected from MIT to BSD 2-Clause License
  to match the repository `LICENSE` file
- repository-wide residual spelling audit found no remaining US-English prose requiring change
- Python syntax validation passed
- PHP syntax validation passed
- English and Czech gettext catalogues compiled successfully; only the existing optional
  gettext header warnings for Last-Translator, Language-Team and Language remain
- `git diff --check` passed

Files changed for this task:

- `.github/workflows/ci.yml`
- `DECISIONS.md`
- `Makefile`
- `PROJECT_STATE.md`
- `README.md`
- `README_CZ.md`
- `src/opnsense/mvc/app/languages/cs_CZ_devicemonitor.po`
- `src/opnsense/mvc/app/languages/en_US_devicemonitor.po`
- `src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/DeviceMonitor.php`
- `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devices.volt`
- `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt`
- `src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py`

## v2.8 release-readiness review

Release-facing metadata and documentation have been reviewed and corrected.

- `defaults.json` remains authoritative at version `2.8`
- English and Czech gettext metadata remain at Device Monitor 2.8
- English and Czech README version histories now include v2.8
- English and Czech installation instructions now target the `v2.8` tag from
  `apg19590209/opnsense-devicemonitor`
- stale v2.7 installation references and the obsolete upstream direct-download
  reference were removed
- stale `Device Monitor version-display review remains separate` state was resolved
- About heading changed from `v2.8 Development & Enhancements` to
  `v2.8 Features and Enhancements`
- the new About heading was added to both gettext catalogues
- English and Czech gettext catalogues compile successfully; only the existing
  optional gettext header warnings remain
- live About page was deployed without a service restart and visually validated
- live About page displays `v2.8 Features and Enhancements`, `Licence`, and
  `BSD 2-Clause License`
- repository release-reference residual audit found no remaining stale v2.7
  installation or obsolete development-heading references
- release-readiness changes committed as `e308f9f`
- GitHub Actions Device Monitor CI #51 for `e308f9f`: PASS
- final release candidate commit `abe1ccb` passed GitHub Actions Device Monitor CI #52
- annotated `v2.8` release tag created at `abe1ccb7306a4a35e60221d41212beff22aa52d9` and pushed to `origin`
- GitHub release `Device Monitor v2.8` published from the validated `v2.8` tag
- public `refs/tags/v2.8.zip` archive verified successfully

## Product backlog

- `PRODUCT_BACKLOG.md` remains the authoritative list of deferred Device Monitor work.
- `DM-BL-002` and `DM-BL-003` are complete and have been removed from the open backlog.
- `DM-BL-004` (Unbound) is functionally complete with regression coverage and
  testbed smoke validation; real-environment validation against actual Unbound
  data remains deferred because no suitable real Unbound data exists in the
  current environment (FUNCTIONALLY COMPLETE / VALIDATION DEFERRED).
- `DM-BL-001` is implemented, fully live-validated on the testbed
  `192.168.20.23`, and is no longer an open backlog feature (see the DM-BL-001
  live-validation section above).
- No open backlog items currently remain.
- Architectural constraints remain in `DECISIONS.md`; environment facts remain
  in `SYSTEM_MAP.md`.

## Hostname Source provenance

- Added persistent hostname_source provenance.
- Precedence remains AdGuard > Dnsmasq > Kea > ISC > Hostwatch.
- Friendly Name remains independent.
- UI and CSV expose hostname source.
- Migration, regression tests, PHP syntax, live deployment, GUI and CSV validation all passed.
- Implementation commit b5adf85 pushed to origin/v2.8-development.
- GitHub Actions run 34216125993: PASS.

## Hostwatch liveness fallback

- Added bounded ICMP confirmation for stale Hostwatch observations.
- Recent Hostwatch remains authoritative; no Nmap or subnet sweep is used.
- Previously-online devices get a 30-minute grace after failed probe.
- Recently-seen offline devices can recover by ping within 120 minutes.
- Both update-only and full-scan paths validated live against quiet Omada APs.
- Regression test passes on OPNsense.
- Decision 12 records the architecture change.
- Implementation commit b5a1ca4 pushed to origin/v2.8-development.
- GitHub Actions run 34223697871: PASS.

## Quiet LAN visibility discovery

- Added bounded LAN visibility priming before Hostwatch ingestion in full scans.
- LAN IPv4 address and prefix are read from `/conf/config.xml`.
- IPv4 networks larger than `/24` are rejected.
- Each usable address is probed with one ICMP echo using at most 32 workers and
  a 2-second subprocess timeout.
- OPNsense's own LAN IPv4 address is excluded.
- No Nmap scan is performed and no Device Monitor device row is created directly.
- `--update-only` remains passive and does not run subnet visibility priming.
- New regression test: `tests/test_hostwatch_lan_visibility.py`.
- Existing hostname-provenance and liveness-fallback regressions continue to pass.
- CI now includes the LAN visibility regression.
- Candidate and live `scan_network.py` SHA256 hashes matched exactly after deployment.
- Live full scans successfully probed 253 usable LAN targets.
- Previously-unseen static TP-Link devices `.250`, `.251` and `.252` are now
  present in Hostwatch and Device Monitor and are active.
- Decision 13 records the architecture and safety constraints.
- Implementation commit `f39b90c` pushed to `origin/v2.8-development`.
- GitHub Actions Device Monitor CI run `34299991865`: PASS.

## Known unresolved issues

- No known unresolved Phase 1 DHCP/DNS discovery issues remain.
- No known unresolved Phase 2 NTP/SSH/Web discovery issues remain.
- No known unresolved Infrastructure Services usability issues remain.
- No known unresolved Phase 3 infrastructure-service discovery issues remain.
- No known unresolved Friendly Name / detected Hostname separation issue remains.
- No known unresolved AdGuard DNS rewrite hostname-enrichment issue remains.

## Device lifecycle history and notes

- Added persistent device lifecycle history; lifecycle records are archived rather
  than deleted.
- A previously known MAC that returns after removal is marked `return_pending`.
  The user must explicitly choose either Start New Lifecycle or Relink Previous
  Lifecycle; returning devices are not automatically assigned a new lifecycle.
- Original lifecycle `first_seen` values and earliest-known MAC history are
  preserved.
- Added Device Details page reached from the Devices page.
- Device Details contains Device Summary, lifecycle-aware Notes, and Lifecycle
  History.
- Notes are individual timestamped lifecycle records with retained edit history.
- User-facing note removal is Archive, not Delete; archived notes remain in
  history and archived lifecycle notes are read-only.
- Device Summary online/offline status uses the device `is_active` state and is
  kept separate from lifecycle active/archived state.
- Stored UTC timestamps are displayed in the configured OPNsense local timezone,
  including daylight-saving changes.
- Removed the obsolete Device Comments popup/editor and its dead JavaScript from
  the Devices page.
- Standardised ordinary Device Monitor status labels to the approved compact
  scale — 13px font, line-height 1.5, padding 1px 5px, 3px radius, 1px
  transparent border — across relevant views.
- Device Details UI, note create/edit/archive history, ONLINE/OFFLINE display,
  legacy-popup removal, and test-data cleanup were validated live.
- Returning-device lifecycle behaviour is covered by regression tests; no live
  `return_pending` device was available for a natural UI validation.
- Python lifecycle-return regression and PHP lifecycle/comment-action regression
  suites pass.
- Final local validation: `git diff --check`, Python syntax, and lifecycle-return
  regression all pass.
- Final live validation: DeviceMonitor model, Devices API controller, and Index
  controller PHP syntax all pass; lifecycle/comment-action regression passes in
  full against the deployed model.
- Lifecycle/history implementation committed as `fc17e07`:
  `feat: add device lifecycle history and notes`.
- `v2.8-development` pushed successfully to `origin`; local and remote branches
  were confirmed synchronized.
- GitHub Actions for the pushed lifecycle/history change completed successfully.
- No known lifecycle/history implementation defect remains.
- Natural GUI validation of a real `return_pending` device remains deferred until
  one occurs; regression coverage for that workflow passes.
- `PRODUCT_BACKLOG.md` remains authoritative for deferred work; no open backlog
  items currently remain.

## v2.9 development — DM-BL-002 complete

`DM-BL-002` — Device activity and identity timeline — is implemented, deployed
and validated live on OPNsense.

Implemented:

- append-only `device_activity_events` history for meaningful state changes that
  would otherwise be lost from mutable current-state rows
- historical IP, detected hostname, hostname-source and Interface/VLAN transitions
- infrastructure-service availability/status transitions
- standalone per-device Activity Timeline page linked from Device Details
- read-only timeline API aggregating lifecycle, note/version, activity, identity,
  targeted Nmap and service-discovery history
- preserved lifecycle archive history when an archived lifecycle is relinked
- preserved identity-resolution history when a resolved identity issue is reopened
- historical Friendly Name changes with active-lifecycle synchronization
- no duplicate activity rows for unchanged Friendly Name or repeated identity-reopen
  operations
- no retroactive fabrication of historical transitions that were never stored

Validated:

- Python device-activity and infrastructure-service regressions: PASS
- PHP timeline aggregation regression: PASS
- PHP history-preservation regression: PASS
- timeline-page JavaScript regression and syntax validation: PASS
- repository `git diff --check`: PASS
- guarded live deployment with pre-deployment hash verification and rollback backup:
  PASS
- live PHP and Python syntax validation: PASS
- live `device_activity_events` table and service-status trigger initialization: PASS
- live GUI multi-source timeline rendering: PASS
- live newest-first ordering: PASS
- live Activity Timeline -> Device Details navigation: PASS

Related v2.9 commits:

- `ec36c6c` — `feat: record device activity state changes`
- `f0a4f65` — `feat: record service availability transitions`
- `dd4ce35` — `feat: add device activity timeline API`
- `bcc4205` — `fix: map edited note history in timeline`
- `0067a62` — `feat: add device activity timeline page`
- `d93ddfd` — `fix: preserve device timeline history`

The guarded live deployment retained rollback backup:

`/root/dm-bl002-predeploy-20260912-122105-85254`

## v2.9 development — DM-BL-003 complete

`DM-BL-003` — Infrastructure-service change alerts — is implemented, deployed
and validated live on OPNsense.

Implemented:

- persistent independent high-water marks for `device_services` and
  `device_activity_events`, seeded to current maxima on upgrade so historical
  rows do not generate an alert flood
- trusted alert candidates only from `verified` or `authoritative`
  infrastructure-service evidence
- configurable email controls for newly verified services, established services
  becoming unavailable, and unavailable services recovering
- generic `SERVICE_CHANGED` events retained as history-only in this version
- batched infrastructure-service email helper using the existing Device Monitor
  email transport
- non-blocking `flock` serialization for service-alert processing
- retry-safe cursor advancement that retains selected events after failed
  delivery while allowing safe-prefix housekeeping
- Recent Service Changes on the existing Infrastructure Services page
- History links from Recent Service Changes to the per-device Activity Timeline
- transition alert metadata now carries current trusted confidence, product and
  version values into the email payload

Validated:

- focused service-alert regression suite: PASS
- real Unix `flock` regression in GitHub Actions: PASS
- GitHub Actions run `34675820735`: PASS
- Recent Service Changes GitHub Actions run `34677469500`: PASS
- metadata-fix GitHub Actions run `34679430429`: PASS
- guarded initial live deployment: PASS
- initial live `service_alert_state` cursor seeded to source maxima `3282,16`: PASS
- live Infrastructure Services Recent Service Changes rendering: PASS
- live Recent Service Changes -> Activity Timeline navigation: PASS
- live Settings email controls and persisted configuration: PASS
- direct service-alert helper delivery through configured sendmail transport: PASS
- guarded live orchestration replay selected exactly one real
  `SERVICE_AVAILABLE` event and returned the cursor to `3282,16`: PASS
- post-fix recovery email displayed `Confidence: verified`, `Product: SMB` and
  `Version: max 3.1.1`: PASS
- no known DM-BL-003 implementation defect remains

Related v2.9 commits:

- `e74ce03` — `feat: add infrastructure service alert cursor state`
- `2f5d889` — `feat: read pending infrastructure service alerts`
- `c786ada` — `feat: add infrastructure service alert filtering`
- `ae2ded5` — `feat: configure infrastructure service alerts`
- `1fab4e8` — `feat: add infrastructure service alert email helper`
- `44a681b` — `feat: process infrastructure service alerts`
- `0f12c25` — `test: cover infrastructure service alert processing`
- `63f2c6d` — `ci: enable v2.9 development validation`
- `b0be04a` — `feat: show recent infrastructure service changes`
- `c00c41a` — `fix: include service metadata in transition alerts`

Guarded live rollback backups retained:

- `/root/dm-bl003-predeploy-20260912-162016-14325`
- `/root/dm-bl003-metadata-predeploy-20260912-170019-72771`

## v2.9 development — DM-BL-006 complete

`DM-BL-006` — Device Change Summary dashboard — is implemented, deployed and
live-validated on the physical OPNsense testbed `192.168.20.23` (Firefox GUI
validation PASS).

Implemented:

- read-only aggregation of existing authoritative Device Monitor history
- no parallel event-summary/event-store table
- no database schema or index changes
- no runtime database writes introduced by Change Summary
- read-only Change Summary API (GET, no state changes)
- supported time windows:
  - Since last review
  - Last 24 hours
  - Last 7 days
  - Last 30 days
  - Custom range up to 90 days
- category filtering
- pagination
- summary counters
- explicit browser-local last-reviewed marker
- localStorage key: `devicemonitor.changeSummary.lastReviewed`
- browser-local presentation of `occurred_at_utc` (UTC remains authoritative
  internally for sorting/filtering; the browser handles timezone/DST)
- stable display row numbering (newest = total; earliest filtered event = #1)
- full sticky Change Summary UI stack with sticky-gap opacity fixes

Authoritative sources used:

- device: `devices.first_seen`
- lifecycle: `device_lifecycles.first_seen` / `created_at`,
  `device_lifecycles.archived_at`, relevant `device_activity_events`
- identity: `device_identity_events.detected_at`,
  `device_identity_events.resolved_at`, relevant `device_activity_events`
- physical_device: `physical_devices.created_at`,
  `physical_devices.archived_at`, `physical_device_memberships.added_at`,
  `physical_device_memberships.removed_at`
- user_history: `device_comment_versions.action`
- infrastructure: `device_services.first_detected`, relevant
  `device_activity_events`

Intentionally unsupported / not fabricated:

- vendor-change history
- timestamped generic "device became inactive" transition where no
  authoritative event exists
- ordinary Nmap executions
- raw heartbeats
- repeated online observations
- `last_seen` refresh traffic

Validated:

- Change Summary menu/page: PASS
- read-only change aggregation: PASS
- full sticky Change Summary stack and opaque sticky-gap handling: PASS
- no row bleed / no vertical sticky jump: PASS
- Period/category filtering, counters, pagination: PASS
- browser-local timezone display (AEST observed in browser): PASS
- row numbering (newest-first; earliest filtered event = #1): PASS
- no heartbeat/raw-scan noise: PASS
- query timings: 24h ~10 ms, 7d ~11 ms, 30d ~10 ms
- production `192.168.20.254` untouched

## v2.9 development — DM-BL-005 complete

`DM-BL-005` — generic hostname-provider framework — is implemented, deployed and
validated on the physical OPNsense testbed `192.168.20.23`.

Implemented:

- centralized hostname enrichment behind a small Python provider abstraction
  (`HostnameProvider` with `name` + `lookup(device)`; plus
  `MappingHostnameProvider` for dict-backed sources)
- deterministic, centralized precedence via `build_hostname_providers` /
  `resolve_hostname` (strongest-first): AdGuard > Dnsmasq > Kea > ISC, with
  Hostwatch as the observational base value
- shared normalization (`normalize_hostname`): strip surrounding whitespace and
  a trailing dot
- provider failure isolation (a failing provider is logged and skipped; it
  cannot break the device scan)
- empty provider result is not an error and does not erase an already-resolved
  hostname
- `custom_hostname` (Friendly Name) remains independent of provider enrichment
- existing `apply_hostname_provenance` retained as a compatibility wrapper
- no schema changes

Validated:

- new hostname-provider framework regression suite: PASS
- existing hostname provenance / AdGuard / Hostwatch / device-activity /
  lifecycle-return / liveness regressions: PASS
- full Python test suite: PASS
- guarded live deployment of `scan_network.py` with hash verification: PASS
- live Python syntax check and import-based framework smoke test: PASS
- production `192.168.20.254` untouched

`DM-BL-007` (Pi-hole) can now implement the same `name` + `lookup` interface and
register in the provider list without modifying core selection logic.

## v2.9 development — DM-BL-007 complete

`DM-BL-007` — optional Pi-hole hostname enrichment — is implemented, deployed and
offline-validated on the physical OPNsense testbed `192.168.20.23`.

Implemented:

- Pi-hole provider (`get_pihole_hostnames`) using the generic DM-BL-005
  `HostnameProvider` framework (no Pi-hole logic inside `resolve_hostname`)
- Pi-hole v6 REST API, DHCP leases endpoint (`GET /api/dhcp/leases`) with
  session auth (`POST /api/auth` + `X-FTL-SID` header)
- disabled by default; settings `pihole_enabled`, `pihole_url`,
  `pihole_password` (app password) added to defaults.json, ConfigController
  validation/save, and the Settings UI
- HTTPS-only, TLS verification enabled, bounded timeout, no credential logging
- deterministic precedence: AdGuard > Dnsmasq > Kea > ISC > Pi-hole > Hostwatch
- normalization and provenance reuse the existing framework (`source=pihole`)
- provider failure / empty result never erases a retained hostname
- no schema changes

Validated:

- new Pi-hole provider regression suite (12 checks): PASS
- existing hostname-provider framework / hostname provenance / AdGuard /
  Hostwatch / device-activity / lifecycle / liveness regressions: PASS
- full Python/PHP/JS test suites: PASS
- guarded live deployment of `scan_network.py`, `ConfigController.php`,
  `defaults.json` and `settings.volt` with hash verification: PASS
- live syntax checks + import-based Pi-hole smoke test (disabled/missing-config/
  fixture lookup): PASS
- production `192.168.20.254` untouched

REAL_PIHOLE_VALIDATION = PASS (corrective TLS fix; see below).

## v2.9 development — DM-BL-007 Python 3.13 TLS corrective fix

The DM-BL-007 Pi-hole provider failed on Python 3.13 because the stock Pi-hole v6
local CA (`/etc/pihole/tls_ca.crt`) is `CA:TRUE` but lacks the X.509 Key Usage
extension that Python 3.13 strict verification requires, producing
`CERTIFICATE_VERIFY_FAILED`.

Corrective fix (Pi-hole provider only):

- in `get_pihole_hostnames()`, immediately after
  `context = ssl.create_default_context()`, clear only the
  `ssl.VERIFY_X509_STRICT` flag when available
- normal CA-chain validation (`ssl.CERT_REQUIRED`) and hostname verification
  (`check_hostname = True`) remain enabled
- no other TLS context or provider changed; no `CERT_NONE` or unverified context

Validated:

- Pi-hole provider regression suite (13 checks, incl. a strict-flag-clearing
  regression test): PASS
- hostname-provider framework / hostname provenance / AdGuard / Unbound
  regressions: PASS
- `python3 -m py_compile` and `git diff --check`: PASS
- real Pi-hole v6 validation PASS (one MAC hostname mapping returned); TLS chain
  and hostname verification remained enabled
- guarded deployment of `scan_network.py` with SHA256 match and syntax check: PASS
- production `192.168.20.254` untouched

## v2.9 development — DM-BL-004 complete

`DM-BL-004` — OPNsense/Unbound hostname enrichment — is implemented, deployed and
offline-validated on the physical OPNsense testbed `192.168.20.23`.

Implemented:

- Unbound provider (`get_unbound_hostnames`) using the generic DM-BL-005
  `HostnameProvider` framework (no Unbound logic inside `resolve_hostname`)
- authoritative local source: OPNsense Unbound host overrides (A records) and
  host aliases read from `/conf/config.xml` (no network access, no per-device
  DNS query)
- native, always-on (no enable/disable setting; no provider configuration)
- deterministic precedence: AdGuard > Dnsmasq > Kea > ISC > Unbound > Pi-hole >
  Hostwatch
- normalization and provenance reuse the existing framework (`source=unbound`)
- wildcard overrides supply no name; aliases resolve to their host override
- provider failure / empty result never erases a retained hostname
- no schema changes

Validated:

- new Unbound provider regression suite (13 checks): PASS
- existing hostname-provider framework / hostname provenance / Pi-hole / AdGuard
  / Hostwatch / device-activity / lifecycle / liveness regressions: PASS
- full Python test suite: PASS
- guarded live deployment of `scan_network.py` with hash verification: PASS
- live Python syntax check + import-based Unbound smoke test (no-source/fixture/
  precedence): PASS
- production `192.168.20.254` untouched

REAL_UNBOUND_VALIDATION = NOT PERFORMED (the implemented provider reads local
OPNsense `/conf/config.xml`, and the current testbed has no suitable real
Unbound source data).

## Infrastructure Services tabs and sticky headers

The Infrastructure Services page (Services → Device Monitor → Infrastructure
Services) now presents each service category in its own tab, with sticky page
controls and table headers.

Implemented:

- one tab per service category (DHCP Servers, DNS Servers, NTP Servers, SSH
  Servers, Web / Admin Services, File / NAS Services, Remote Access, Directory
  / Authentication, SNMP / Management, VPN Endpoints) plus a leading Recent
  Service Changes tab; categories derive from the existing `groupTitle()`
  mapping and preserve its order
- client-side tab switching (no additional API requests on tab change)
- sticky page heading, toolbar, tab strip and active table column headers,
  reusing the Change Summary sticky-header approach
- all existing data, counts, badges, status indicators, filters, buttons and
  discovery behaviour preserved; no backend, API, schema or detection changes

Files changed:

- `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/infrastructureservices.volt`
- `docs/USER_MANUAL.md`

Validated:

- full Python, Node (Bun) and PHP test suites: PASS
- JavaScript syntax build check (Bun): PASS
- Volt template compile check (Phalcon): PASS
- guarded live deployment of `infrastructureservices.volt` with hash
  verification: PASS (rollback backup retained at
  `/root/devicemonitor_backup/infrastructureservices.volt.pre-infratabs-20260920-043318`)
- LIVE_VISUAL_VALIDATION = PASS (visual QA on the `.23` testbed: tab layout,
  tab switching, and sticky controls/table headers correct; no bleed-through
  or vertical jumping; no defects observed)
- production `192.168.20.254` untouched

## Device Monitor UI consistency — Stage 1 (page headers)

Completed the first staged Device Monitor UI-consistency pass (low-risk
presentation/layout only).

- IP and MAC Conflicts (`identityevents.volt`) and Nmap Scan History
  (`scanhistory.volt`) table headers were converted from the nested-scroll
  sticky (`max-height` + `overflow-y: auto`, transparent `th`) to the proven
  Change Summary sticky-stack pattern: normal page scrolling, opaque header
  backgrounds, sticky `header.page-content-head`, gap cover, and table
  `thead th` sticky immediately beneath the controls heading.
- Removed the redundant in-page `Device Monitor – <Page>` banners from Devices,
  Change Summary, Infrastructure Services, IP and MAC Conflicts, Nmap Scan
  History and Settings; the OPNsense breadcrumb is now the primary page
  identity. Useful stats/controls/tab strips were retained.
- Removed the ordinary-page version display from the Devices header and the
  Settings page heading; version/repository/licensing information remains in
  Settings → About.
- Device Details now uses a single `Device Details` heading (redundant
  `Device Monitor –` prefix removed).
- The per-device activity page and its Device Details navigation button now
  use the visible label `Device Activity` (page heading, section heading and
  button label; internal identifiers remain `activitytimeline`).
- Device Details device-summary field order now leads with `IP Address`,
  followed by `Hostname`, `MAC Address`, `Vendor`, `Status`, `First Seen`,
  `Last Seen`, then the remaining fields (Friendly Name, VLAN, Current
  Lifecycle, Notes). Presentation-only; no backend/API/schema changes.
- Updated `docs/USER_MANUAL.md` to match the heading convention, terminology,
  field order and sticky behaviour.

Files changed: eight `.volt` views, the en_US and cs_CZ gettext catalogues,
`tests/test_change_summary_ui.js`, and `docs/USER_MANUAL.md`.

Validation:

- full Python suite: PASS
- Node (UI) suite: PASS
- PHP suite: PASS
- PHP lint / Python compile / shell syntax / gettext (`msgfmt`): PASS
- Volt template compile check (Phalcon): PASS
- `git diff --check`: PASS
- guarded testbed deployment of the eight changed `.volt` files (candidate/
  pre/post SHA256, timestamped `cp -p` rollback backups): PASS
- LIVE_VISUAL_VALIDATION = PASS (user-confirmed on the .23 testbed)
- production `192.168.20.254` untouched

## Physical Devices UX redesign (final pre-release)

Implemented the approved human-friendly Physical Devices redesign
(`v2.9-development`) without changing the underlying model, write actions,
lifecycle semantics or database schema.

- Unit 1 (read model): `getPhysicalDevicesOverview()` now enriches every
  identity with mac, friendly name, IP, hostname, hostname source, online
  state and last seen, and derives per-device current/previous identity counts,
  online/offline status and last seen. Read-only.
- Unit 2 (page): `physicaldevices.volt` now shows one panel per real-world
  device (Device Name, current identities, status, last seen) expanding to a
  Device Summary + Current Identities + Previous Identities layout.
  `devicehistory.volt` compact summary and the `devices.volt` badge wording
  were aligned; the obsolete `Grouped` badge fallback was removed.
- Translations (`en_US`/`cs_CZ`), `docs/USER_MANUAL.md` and the stale
  DECISIONS.md §18 status banner were reconciled.

Files changed: `DeviceMonitor.php`, `physicaldevices.volt`,
`devicehistory.volt`, `devices.volt`, both gettext catalogues, and the focused
UI/API/overview regression tests.

Validation: PHP suite, Node (UI) suite, PHP lint, gettext (`msgfmt -c`) and
`git diff --check` PASS locally; GitHub Actions PASS for commits `67a476c`
(run `35508985779`), `d8421ca` (run `35509262180`) and `97abb98`
(run `35509328114`).

Deployment (`192.168.20.23`, guarded): `DeviceMonitor.php`, three `.volt`
views and both compiled `.mo` catalogues deployed with candidate/pre/post
SHA256 parity and timestamped `cp -p` rollback backups (tag `uxredesign`).
Affected Volt template caches cleared; `Menu.xml` unchanged so the menu cache
was not invalidated; no service restart. Read-only DB safety counts unchanged
(`devices=8`, `physical_devices=1`, `physical_device_memberships=3`,
`device_lifecycles=8`). Unauthenticated route smoke check: HTTP 301→302, no
PHP fatal.

Authenticated GUI acceptance on `192.168.20.23`: PASS (human GUI checklist
completed against the redesigned Physical Devices page and Device Details
summary).

## v2.9 RC freeze

Release-candidate freeze is COMPLETE.

- RC candidate: `d0fe7afa587a28bf5418f75eb499f58a847b7ca6` (`v2.9-development`,
  `docs: prevent redundant finalisation checks`; final rules/documentation
  commit over the complete v2.9 implementation).
- Physical Devices GUI acceptance on `192.168.20.23`: PASS.
- Whole-plugin regression (local): PASS — Python compile, PHP lint, shell
  syntax, gettext (`msgfmt -c`), `git diff --check`, 8 PHP tests, 8 Node (UI)
  tests, 12 Python tests; 0 failures.
- GitHub Actions CI for `d0fe7af`: PASS (run `35510393264`).
- Pi-hole: COMPLETE. Unbound: FUNCTIONALLY COMPLETE / VALIDATION DEFERRED
  (non-blocking).
- Production `192.168.20.254` remained untouched until the explicit v2.9
  promotion authorisation (recorded below).

## v2.9 production promotion

Production promotion is COMPLETE.

- Frozen RC `d0fe7afa587a28bf5418f75eb499f58a847b7ca6` promoted to production
  `192.168.20.254` (OPNsense 26.7.4).
- Deployment: guarded install of 19 runtime files (17 changed + 2 new views
  `changesummary.volt`, `physicaldevices.volt`); candidate SHA256 == installed
  SHA256 for all; root:wheel, 644 (755 for `scan_network.py`).
- DB backup: `/var/db/devicemonitor/devices.db.pre-v29promo-20260921-002343`;
  17 runtime rollback backups `<file>.pre-v29promo-20260921-002343`.
- Menu cache cleared (Menu.xml changed); no service restart (daemon
  `monitor_daemon.py` unchanged); no stale Volt cache to clear.
- DB safety: pre/post counts identical (52 devices, 52 lifecycles, 607 activity
  events, 0 physical devices/comments/memberships); integrity ok.
- Technical validation: PASS. Production GUI smoke validation: PASS (human).
  Full Physical Device write workflow: PASS on testbed `192.168.20.23`;
  production write workflow not repeated (avoids modifying live data).
  Production data preservation: PASS.

Next step: none required — v2.9 is promoted to production and validated.

## 28 September 2026 — O3 installer layout and O4 view migration (sidecar translation)

Branch `feature/o4-sidecar-views-20260928`, cut from `origin/v2.10-development`. Code changes are
commit `43891db`, followed by the layout change recorded here and this record. Nothing was deployed
and no host was contacted.

- **O4 view migration — CODE-COMPLETE.** All 372 HTML-context `lang._()` call sites across the nine
  Device Monitor views now call `devicemonitor_t()`; the 241 `lang.query()` call sites inside inline
  script bodies are unchanged, because those need the raw value. The argument text of every call site
  is byte-identical to before, so no msgid changed. Remaining dependency: **human browser
  confirmation** of the rendered pages, which cannot be produced from this checkout (no
  Selenium/WebDriver here, and the change is not deployed).
- **O3 installer layout — RESOLVED.** The eleven catalogues moved from the flat
  `languages/<locale>_devicemonitor.po` layout, which `bindtextdomain()` cannot resolve, to
  `languages/<locale>/LC_MESSAGES/devicemonitor.po`. `install-unattended.sh` compiles each into
  `<locale>/LC_MESSAGES/devicemonitor.mo` under the path `devicemonitor_locale.inc` binds;
  `uninstall.sh` removes the nested catalogue and the legacy flat pair; the CI catalogue step mirrors
  the layout. The `en_US`/`cs_CZ` manifest rows were repathed, the manifest stays at 38 rows, and its
  new SHA256 `ee688415eb586abec361b84cd54ac75d5fe45a4fddb136f89bfcda610894ce69` is the pin in
  `install-unattended.sh`. With this, `devicemonitor_t()` stops falling through to the core domain on
  a firewall installed from the release asset: the sidecar is behaviour-changing, not merely
  behaviour-preserving.
- **`devicemonitor_locale.inc` is now a guarded payload file.** `IndexController::initialize()`
  requires it and binds the domain before any view renders, because the views call a global function
  that this file defines; a missing binder is a deployment error, not a silent English fallback.
- **Webhook guard bypass — CLOSED** (commit `43891db`). `ConfigController::sendWebhookAction()`
  passed `''` when the caller omitted `webhook_url`, and the handler only short-circuits on `null`,
  so the "Webhook disabled" guard was skipped and delivery was attempted to an empty URL. Absent,
  null, empty and whitespace-only values are now all detected in the controller and normalised again
  inside `NotificationHandler::sendWebhook()`; a whitespace-only configured URL is treated as absent,
  and `testWebhookAction()` rejects an empty URL instead of attempting it.
- **New gate: `tests/test_sidecar_catalogue.py` (+ `tests/sidecar_translate_probe.php`, new CI step).**
  It compiles the real catalogues into the bound layout, adds a stand-in core OPNsense domain with
  hostile content, and asserts sidecar precedence, the core fallback for a locale with no plugin
  catalogue, the `sidecar_translation_enabled = "0"` toggle, the msgid fallback, and that HTML
  escaping matches `htmlspecialchars(ENT_QUOTES | ENT_HTML401)` while the raw path stays unescaped.
- **Verification.** `php -l` and `sh -n` clean on every changed file; `git diff --check` clean;
  `test_release_manifest.py`, `test_translated_javascript.py`, `test_sidecar_catalogue.py` PASS; the
  language acceptance run PASSED 9 languages / 10 pages / 451 keys with the three new settings
  strings present in all eleven catalogues; the full local CI-mirroring battery is 97/97 PASS.
- **Deployment lag observed, not a defect.** Run against the *installed* tree, the acceptance test
  reports the deployment behind the checkout: the installed views differ from source and the eleven
  legacy flat catalogues lack the three new strings. That is the check working as designed and it
  clears when the v2.10 payload is deployed. `--installed-po` was added so a staged tree can be
  checked without touching a live deployment.

Next step: obtain human browser confirmation of the migrated views (sidecar toggle on and off), then
deploy the v2.10 payload to the testbed through the guarded installer under explicit authorisation.
No product-backlog feature is designated as the next implementation task.

## 28 September 2026 — v2.10 payload deployed to the testbed (deployment lag cleared)

Deployed from the authoritative checkout with the guarded unattended installer:

```
CHECK_OK version=2.10 predecessor=2.10 files=49 daemon_running=1 host=OPNsense.internal
BACKUP_READY=/var/backups/devicemonitor/install-v210.UmZ7ze
INSTALL_OK version=2.10 files=49 backup=/var/backups/devicemonitor/install-v210.UmZ7ze daemon_restarted=1
```

- Command: `sh install-unattended.sh --host OPNsense.internal`. This installer has no
  `--execute` flag - an unknown argument aborts with exit 2 - because applying is the default;
  `--check` is its read-only mode, run before the change (`CHECK_OK ... files=49`) and after it
  (`CHECK_OK ... files=49`). The target count was 49 for an update (38 manifest rows plus eleven
  catalogues) and 50 for a fresh install; the 29 September 2026 DM-BL-008c merge engine raised it to
  **59** for an update and **60** for a fresh install by adding ten merged core catalogues.
- Payload: the 38 manifest rows, now including the sidecar binder
  `src/etc/inc/devicemonitor_locale.inc`, plus the eleven catalogues compiled into
  `<locale>/LC_MESSAGES/devicemonitor.mo`. The hand-deployed binder from the O3 investigation
  was replaced by the committed payload copy.
- Post-deployment integrity: all 38 manifest targets verified on disk, 0 missing, 0 mismatched;
  catalogue msgid counts identical to source for all eleven locales (fr_FR 456/456), so the
  three-string asset variance is gone across the live tree.
- Service state: `configd` restarted once; the Device Monitor daemon restarted (pid 653 ->
  85147) and its log records `Monitoring DISABLED`. `config.json` is unchanged, `enabled` is
  still `0` on `opt1`, so no scan ran and `re0` on the live `192.168.20.0/24` LAN was not
  touched. The sidecar key is absent from the deployed configuration, which the binder treats as
  enabled (its documented default), so plugin strings now resolve through the sidecar catalogue.
- Database unchanged: 3 devices (49 deleted), 52 known MACs, 52 lifecycles, 46 activity events,
  89 services, 1 physical device, 3 memberships; `PRAGMA quick_check` = ok.
- Live resolution proof without a browser, run against the deployed directories with the domain
  bound: fr_FR `Total des appareils` / `Résumé des modifications` / `Surveillance des appareils`,
  de_DE `Geräte gesamt` / `Änderungsübersicht` / `Geräteüberwachung`, it_IT `Dispositivi totali` /
  `Riepilogo modifiche` / `Monitoraggio dispositivi`. The French and Italian strings match the
  operator reports of 28 September 2026 from this repository's locale track.
- Acceptance gate after deployment: 0 failures, 9 languages, 10 pages, 451 keys. Both
  pre-deployment finding classes are gone (installed views and installed plugin catalogues now
  match the source). The gate now models the deployed chain: drift in the plugin catalogue still
  fails, drift in the shared core catalogue is a warning when the plugin catalogue resolves the
  key (still fatal under `--strict`) and a failure when it cannot. That leaves one warning class:
  the legacy shared core catalogue from the 26 September out-of-band merge is behind the source
  for the plugin's new strings, and for `Language` it carries the core GUI's own wording.
- Still open: human browser confirmation of the migrated pages with the sidecar toggle both on
  and off (Settings -> About). That is the only unmet condition of `O4`; no browser or WebDriver
  is installed on this host.

## 28 September 2026 — `O4` sign-off (operator-attested browser pass) and local merge readiness

- **Status as instructed: `O4` view migration `CLOSED` (verified via human browser pass), and the
  sidecar domain switch recorded as `SUCCESSFUL` for `fr_FR` and `it_IT`.** Provenance: operator
  attestation in this session. No artifact was attached to this checkout: the run-book's evidence
  list (screenshots, the About-tab page source for the toggle ON and OFF states, browser name and
  version, run timestamps, the `<language>` value before and after, and the
  `sidecar_translation_enabled` value observed in each state) has not been supplied here. The record
  therefore states the operator's reported result, exactly as `DM-BL-008b` distinguishes an
  attestation from an artifact-backed verification; attaching those items raises this to
  artifact-verified and would need no other change.
- The technical preconditions for that pass are present and documented above: the About tab's
  `#btn-apply-about` is deployed, the sidecar domain resolves on the live host for `fr_FR`, `de_DE`
  and `it_IT` (`Résumé des modifications`, `Surveillance des appareils`, `Riepilogo modifiche`,
  `Monitoraggio dispositivi`), and `devicemonitor_t()` takes precedence over the core catalogue with
  the toggle on and falls through to it with the toggle off.
- **Local merge readiness verified without moving anything.** `origin/v2.10-development` (`548dbcc`)
  is an ancestor of `990a4b0`, so a plain merge into it fast-forwards. In a throwaway detached
  worktree the `--no-ff --no-commit` variant reported "Automatic merge went well", staged 46 files
  (1527 insertions, 424 deletions) with `MERGE_HEAD` present, and `merge --abort` returned the
  sandbox to clean; the readiness test itself, `merge --ff-only`, reported
  `Updating 548dbcc..990a4b0 - Fast-forward` with 125 tracked files and 0 conflict markers. The
  local `v2.10-development` ref was not moved (still `548dbcc`) and the main checkout still carries
  only the parallel locale-verification changes (75 insertions, 19 deletions).
- Note for the record: `--no-ff` is the opposite of a fast-forward test, because it forces a merge
  commit. The command that answers the question is `git merge-base --is-ancestor` followed by
  `git merge --ff-only`; `--no-ff --no-commit` only proves that a merge commit would apply cleanly.

## 29 September 2026 — Device Monitor tabs repaired (Volt macro registration) and v2.10 payload refreshed

Description: every Device Monitor application page (Devices, Physical Devices, Network Identities,
Device History, Activity Timeline, Scan History, Change Summary, Settings, Infrastructure Services)
rendered the outer OPNsense layout with an empty content block.

Root cause (live evidence, not inference): `/var/log/php_errors.log` does not exist on the testbed;
`php.ini` writes GUI errors to `/var/lib/php/tmp/PHP_errors.log`, which recorded
`Phalcon\Mvc\View\Engine\Volt\Exceptions\MacroNotFound: Macro 'devicemonitor_t' does not exist`
(Volt.zep:65) at 08:58:10, 09:02:01 and 09:07:49 on 29 September 2026, matching live GUI activity in
the same minutes (menu, ACL and model caches refreshed at 09:00-09:07). The call path is proven, not
assumed: an unregistered name compiles to `<?= $this->callMacro('devicemonitor_t', ['...']) ?>` and
renders blank, while a compiler-registered name compiles to `<?= devicemonitor_t('...') ?>` and
renders. Core `ControllerBase::__construct()` registers only `theme_file_or_default`, `file_exists`
and `cache_safe`, and `ControllerBase::$volt_functions` is private, so a plugin cannot extend that
list. The O4 migration moved nine views (340 call sites) onto `devicemonitor_t()` without registering
it with the compiler, and `lang` is still supplied by core (`ControllerBase.php:422`), so that single
unregistered name was the whole defect.

Method: `IndexController::initialize()` now calls `registerVoltFunctions()`, which reads the engine
the framework registered (`Phalcon\Mvc\View::getRegisteredEngines()`, verified callable on this build),
re-registers `.volt` as a wrapper that adds `addFunction('devicemonitor_t', 'devicemonitor_t')` to its
compiler, and falls back to `voltEngine()` mirroring the framework's own construction when no `.volt`
engine exists. The same commit applies the pending PHP 8.1+ null guards (`devicemonitor_locale.inc`
line 133; `NotificationHandler.php` lines 345/346/350), regenerates the three matching rows of
`release/v2.10-runtime.manifest` and re-pins the manifest SHA256 on `install-unattended.sh` line 28
from `dda5db1eb8f5341bc3dbf78d471cc85779a717b36d575f01b87ad2bbd3663638` to
`ced20c442a28acb544b9b683549cb0f2553b0335ba44dd78682d3b4013b3cf4e`. The three files were deployed to
the testbed behind the deployment guard (live pre-state hashes matched `f0003c4`; backups in
`/var/backups/devicemonitor/repair-20260929-093444`), the Volt compile directory (`/var/lib/php/cache`;
`/tmp/volt` and `/tmp/config.cache` do not exist on this build), the menu, ACL and model caches and
`pluginctl cache_flush` were cleared, and the web configurator was restarted with
`/usr/local/etc/rc.restart_webgui` (the configd `webgui restart` action; `pluginctl webgui` is not a
pluginctl hook).

Result (A/B on the production render path with a flushed compile cache): the pre-repair controller
failed all nine tabs with `MacroNotFound`; the repaired controller rendered all nine
(`devices` 49,541 B through `infrastructureservices` 53,716 B; `TAB_RENDER=PASS tabs=9`). Live state
after the repair: GUI answering (302 on `/ui/`), daemon running, no new `MacroNotFound` entry, and
background scanning still `"enabled": "0"`.

Changed: `IndexController.php`, `devicemonitor_locale.inc`, `NotificationHandler.php`,
`release/v2.10-runtime.manifest`, `install-unattended.sh`, plus this record and the
`PRODUCT_BACKLOG.md` re-pin note (commit `8faf09d` and its documentation commit). No branch was
switched, and no installer, `opnsense-bootstrap` or `pkg` command was run. The `count(Generator)` and
`Model validation failed` errors in the triage input were traced to ad-hoc `php` stdin/direct-test
runs (`Standard input code:9/20`, plus test scripts run without their stdin on 28 September); no such
construct exists in `src/` or `tests/`, so no code was changed for them.

Validation: `php -l` on the three patched files, `sh -n install-unattended.sh`,
`python3 tests/test_release_manifest.py` (`V210_RELEASE_MANIFEST=PASS`, 38/38 payload hashes), the
installer manifest gates in isolation (digest, 38 rows, source version 2.10), `git diff --check`, the
live-versus-manifest hash comparison for the three deployed files and the A/B tab render above all
PASS.

Pushed and verified (29 September 2026): `8faf09d` is on `origin/v2.10-development` and green in
GitHub Actions Device Monitor CI run `36501061119` (push event, branch `v2.10-development`, head
`8faf09d`, job `validate`), and the documentation commit `58b9628` carrying this record is pushed to
`origin/v2.10-development` and green in CI run `36501202440` (head `58b9628`, job `validate`), so no
commit on this branch is local-only.

## 29 September 2026 — DM-BL-008b closed: runtime harness patch and live French/Italian dialog pass

Description: the last open language-acceptance item, `DM-BL-008b`, was closed after two independent
checks — the runtime test harness was repaired so the production Volt compiler path can certify
languages again, and the row-1 confirmation dialog was verified on the live interface.

Work completed:
- `7b4bb46` — `tests/render_device_monitor_page.php:105` now registers `devicemonitor_t` on the
  harness's own Volt compiler, mirroring `IndexController.php:44`. Before the patch every runtime-engine
  acceptance run aborted with `Uncaught Error: Using $this when not in object context` on all ten pages
  (`failures=10`); after it `--engine runtime --languages it_IT` reports `it_IT PASS pages=10 keys=451
  translated=442 identical-to-english=9 selectable=True locale=True identity=it_IT engine=runtime`,
  `failures=0`.
- Runtime acceptance for the eight languages whose shared catalogues exist: `PASS languages=8 gaps=0
  failures=0`; the CI engine `--engine interpolate` across all nine: `PASS languages=9 gaps=1
  failures=0` (the single gap is the `nl_NL` GUI-list limitation, `DM-BL-008a`).
- The same commit adds `.gitignore:7` (`.cline-reports/`) so captured engineering reports stay
  local-only; the commit was verified before publication and pushed as `c22a8d8..7b4bb46`.
- Operator-attested live dialog verification on
  `https://192.168.20.23/ui/devicemonitor/index/devices` (per-row Delete): French renders exactly
  `Supprimer l'appareil <MAC>?` and Italian exactly `Elimina dispositivo <MAC>?`, with no HTML-entity
  leakage and no layout or button-container clipping. The message id resolves identically in the source
  `.po`, the deployed plugin `.mo` and the shared core `OPNsense.mo`.

Files changed: `tests/render_device_monitor_page.php` (runtime branch, +5 lines), `.gitignore` (+3
lines, committed as `7b4bb46`), plus this closure record in `PROJECT_STATE.md` and
`PRODUCT_BACKLOG.md`. No source, view, catalogue, manifest, installer, Makefile or service file changed,
so no guarded hash and no installer pin needed updating; no installer, `opnsense-bootstrap` or `pkg`
command was run and nothing was deployed.

Tests performed and results (already verified in this session, not re-run for this record): `php -l
tests/render_device_monitor_page.php` PASS; runtime Italian acceptance `failures=0`; runtime
eight-language acceptance PASS; interpolate nine-language acceptance PASS; GitHub Actions Device
Monitor CI run `36516155279` (branch `v2.10-development`, head `7b4bb46`, push event, job `validate`)
PASS in 42 s, with local and remote `v2.10-development` at the same commit
(`7b4bb463ab30546f97b5e51bf479205274f5f07d`).

Unresolved: `F1` (the Change Summary toast is inert on 26.7.4 — decide documented-inert versus
migration to `stdDialogInform()`/`BootstrapDialog`); `DM-BL-008c` resolved 29 September 2026; background scanning on the
testbed was re-enabled on 29 September 2026 and is running (see the activation record in the `F1`
closure section at the end of this file and the Current state bullet above); the nine-language
**runtime** matrix remains host-blocked
by the missing `nl_NL` shared catalogue (`DM-BL-008a`), which CI now bypasses per language instead of
hiding; CI integrates the repaired runtime branch as a guarded matrix (29 September 2026,
`ci.yml:74-105`): the `Validate language acceptance (DM-BL-008)` step runs `--engine interpolate` for all
nine languages and then `--engine runtime --languages <languages whose shared OPNsense.mo the runner
carries>`, prints one `SKIPPED <lang>` line for each host-blocked language, and skips the matrix with a
stated reason on a runner without the Phalcon Volt compiler or `OPNsense\Base\ViewTranslator`.

Next recommended step: record the `F1` decision.

Evidence status: the dialog observation is an operator attestation from this session; no screenshot, DOM
capture, browser/version or timestamp artifact was attached to this checkout, so it is recorded as
operator-reported, exactly as the `O4` sign-off and the 28 September French Selenium note are.

## 29 September 2026 — F1 closed: Change Summary confirmation banner with a 4-second auto-dismiss

Description: closed `F1`, the finding that the Change Summary confirmation path rendered nothing on
OPNsense 26.7.4. `showToast()` in `changesummary.volt` guarded on `$.fn.notify` and then on
`window.bootbox`; the core page loads neither (no such asset exists under `/usr/local/opnsense/www` or
`/usr/local/www`, and `/ui/js/theme.js` is an empty placeholder), so clicking **Mark reviewed now** produced
no feedback at all and the button appeared inert.

Work completed:
- `changesummary.volt:581-593` now renders a self-contained jQuery banner — the same pattern already proven
  in `devices.volt:435-444` — in place of the dead guard chain. Two deliberate differences from
  `devices.volt`: the icon and the message are appended as DOM nodes (`$('<i>').addClass('fa ' + ic)` plus
  `document.createTextNode(' ' + message)`) instead of being interpolated into `.html('<i …></i> ' + msg)`,
  so a translation can never be parsed as markup; and the auto-dismiss timeout is `4000` ms
  (`fadeIn(300)` → `setTimeout(4000)` → `fadeOut(300, remove)`) instead of `3000` ms. Geometry and palette
  are unchanged from `devices.volt` (`position: fixed`, `top/right: 20px`, `z-index: 9999`,
  `min-width: 280px`, `#4CAF50` success background, `fa-check-circle` icon).
- The `$.fn.notify(message, { type: 'success' })` shape proposed on 28 September is withdrawn: it cannot
  work on this build for the same reason the original guard chain was inert, so `showToast()` does not
  depend on a plugin the core does not ship.
- `release/v2.10-runtime.manifest` row 17 (view digest `0503e488…f527` → `b7aa5631…3d0c`) and the
  `install-unattended.sh` line 28 manifest pin (`ced20c44…cf4e` → `fc2669413c86c70b6bf4c72f0d1a014361cbe179e64ae50a7147d3d690b50ac2`)
  were refreshed in the same change set, so the guard and the manifest stay self-consistent; the manifest
  is still 38 rows and the source version is still 2.10.
- Operator live verification on `https://192.168.20.23/ui/devicemonitor/index/changesummary`: clicking
  **Mark reviewed now** renders the success banner with a clean, unclipped icon layout, the message
  appended as a text node, and the banner auto-dismisses after exactly four seconds; no new entry appeared
  in the PHP error log for the request.

Files changed: `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/changesummary.volt` (`showToast()`
replacement, +4 net lines), `release/v2.10-runtime.manifest` (1 digest row), `install-unattended.sh`
(1 pin), `PRODUCT_BACKLOG.md` (the `F1` entry) and this file. No controller, model, catalogue, Makefile,
service or documentation file changed, and no deploy, cache flush, installer or `pkg` command was run as
part of this closure record.

Tests performed and results (this session): `python3 tests/test_release_manifest.py` PASS
(`V210_RELEASE_MANIFEST=PASS`); `sh -n install-unattended.sh` PASS; `git diff --check` PASS (no whitespace
errors); `node tests/test_change_summary_ui.js` PASS (`DEVICE_CHANGE_SUMMARY_UI_STRUCTURE=PASS`,
`DEVICE_CHANGE_SUMMARY_UI_JAVASCRIPT=PASS`); `python3 tests/test_language_acceptance.py --engine
interpolate` PASS (`LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=interpolate failures=0`, the single
gap being the `nl_NL` GUI-list limitation, `DM-BL-008a`); source digests cross-checked — the view's SHA256
equals the manifest row (`b7aa5631344ea410326d18f6fc07a52e0a43ddf0a1e160c6c91f2f5326003d0c`) and the
manifest's SHA256 equals the installer pin (`fc2669413c86c70b6bf4c72f0d1a014361cbe179e64ae50a7147d3d690b50ac2`).

Unresolved at that point: `DM-BL-008c` (resolved later on 29 September 2026 by the v2.10 merge engine — see the closure section below); the testbed background scanner is **active** — on 29 September 2026
15:02:14 AEST the daemon (PID 94999, running unchanged since 28 September 2026 23:15) hot-loaded
`"enabled": "1"` from `/var/db/devicemonitor/config.json` without a service or web-GUI restart, polling
every 60 s over the fail-closed scope `opt1` (the descriptor for `vlan0.50`, `192.168.50.0/24`, DMTEST),
with two clean scan cycles and no database-lock or runtime errors, and rollback available at
`/var/backups/devicemonitor/scan-activation-20260929/`; the notification transports stay enabled but
broken (`sendmail` absent, malformed webhook URL) and will fail-log on the first new device;
the nine-language **runtime** matrix remains host-blocked by the missing `nl_NL` shared catalogue
(`DM-BL-008a`); CI now integrates the guarded runtime matrix (`ci.yml:74-105`, 29 September 2026), which
runs the runtime branch for every language the runner can serve and reports each host-blocked language as
an explicit `SKIPPED` line instead of failing the job — the managed `ubuntu-latest` runner reports the
whole matrix as skipped, because it carries no Phalcon Volt compiler and no
`OPNsense\Base\ViewTranslator`; `docs/USER_MANUAL.md` section 11.2 describes the **Mark reviewed now**
control without mentioning a confirmation banner, so the user-facing documentation rule was reviewed but
the manual was deliberately left unchanged inside this five-file commit set (see the `F1` report).

Next recommended step: add the one-line banner note to `docs/USER_MANUAL.md` section 11.2, matching the
"reports success/failure as a toast message" wording already used for the Devices **Check online** action.

Evidence status: the live banner observation is an operator attestation from this session; no screenshot,
DOM capture, browser/version, PHP error-log transcript or timestamp artifact was attached to this checkout,
so this section records the operator's reported result rather than an artifact-backed verification, exactly
as the `O4` sign-off, the 28 September French Selenium note and the `DM-BL-008b` dialog closure do.

## 29 September 2026 — Notification transport: webhook endpoint repaired and live delivery verified

Description: the testbed's webhook transport was enabled (`webhook_enabled = "1"`) but structurally
unusable: `webhook_url` was `htp://broken-link)`, so every attempt failed validation with
`Invalid webhook URL`. The endpoint was repaired to a reachable loopback mock on the testbed and the
transport was then exercised end to end, satisfying the notification proof rule that requires recipient
and message behaviour rather than configuration parsing.

Work completed:
- Guarded repair of `/var/db/devicemonitor/config.json`: `webhook_url` `htp://broken-link)` →
  `http://127.0.0.1:8777/dm-webhook`, SHA256 `7126710d7491076876316f5d2a58ae400f16569ce293254dcb607048c2a54469`
  → `dcec072b46da65953af113c4c946cd706ea8dae6b64172a60dbff7a92f6ef8a8`, mode 0600 preserved, 35 keys with
  only `webhook_url` differing; rollback copy `/var/backups/devicemonitor/webhook-url-20260929/config.json`.
- A loopback mock receiver (`127.0.0.1:8777`, POST-only, answers `200` with a JSON ack) was run for the test;
  it exists only for the duration of this verification, so the URL is structurally valid and was proven
  reachable, but its endpoint is not a permanent service.
- Test-mode dispatch through the backend harness that mirrors `ConfigController::testWebhookAction`
  (`$handler->sendWebhook(true, $url)`):
  `{"result":"ok","message":"Webhook sent (HTTP 200)","type":"generic","test":true,"count":0}` with exit 0.
- Real-mode dispatch through the configd action the plugin actually uses,
  `configctl devicemonitor sendWebhookNotification` (exit 0, output
  `{"result":"sent","message":"Webhook sent (HTTP 200)","type":"generic","test":false,"count":1}`), with one
  device's `notification_pending` flag raised to 1 for the test and restored to 0 afterwards (all three
  devices verified back at 0).
- Payload evidence from the receiver: test payload `event/title/message/timestamp/hostname/test`
  (`{"event":"test","title":"…OPNsense Device Monitor - Test","message":"This is a test notification!",
  "timestamp":"2026-09-29 17:32:39","hostname":"OPNsense.internal","test":true}`, 188 B) and real payload
  `{"event":"new_devices","hostname":"OPNsense.internal","timestamp":"2026-09-29 17:32:39","device_count":1,
  "devices":[{… 20 fields …}]}` (535 B); both parsed as valid JSON with no serialization errors.
- Plugin log: `[PHP-WEBHOOK-HARNESS] Test webhook result: SUCCESS`,
  `[PHP-WEBHOOK] Preparing to send webhook`, `[PHP-NOTIFY_WEBHOOK.php] Webhook notification result: SUCCESS`;
  no `Invalid webhook URL` line appears after the repair.
- Command-name correction recorded: `configctl devicemonitor testWebhookAction` is **not** a configd action
  (`Action not allowed or missing`) — that name is the MVC controller action; the dispatchable configd actions
  are `scan`, `start`, `stop`, `restart`, `status`, `sendEmailNotification` and `sendWebhookNotification`.

Unresolved: the webhook endpoint is a temporary loopback mock, so the URL now points at a port that no longer
listens — the tier needs either a permanent receiver or `webhook_enabled = "0"`; the email leg is still
unusable because no MTA exists (`sendmail`, `mail`, `postfix` and `/usr/local/sbin/sendmail` are all absent
while `email_method = "sendmail"` and `smtp_host` is empty), so the first new device would log one delivery
failure per enabled transport; `identity_email_enabled` and `service_email_enabled` remain `0`.

Next recommended step: decide the permanent webhook receiver (or disable the webhook leg) and the email
transport (`os-postfix`, direct SMTP, or disable), then record the resulting recipient/message evidence the
same way.

## 29 September 2026 — DM-BL-008c closed: core catalogue merge engine in the v2.10 installer

Description: closed `DM-BL-008c`, the item that kept the plugin's translations out of the domain the GUI
actually reads. The views' HTML text already resolved through the plugin's own sidecar domain, but the 241
inline-script `lang.query()` call sites resolve through `ControllerRoot::setLang()` → `ViewTranslator` with
`directory = /usr/local/share/locale` and `defaultDomain = OPNsense`, so on a firewall installed from the
release asset alone every JavaScript-supplied string (confirmations, toast bodies, table strings) stayed
English. The v2.10 installer now overlays the plugin's keys into the core catalogues.

Work completed:
- New `release/merge-opnsense-catalog.sh`: core-first `msgcat --use-first --no-location --sort-output` over
  `msgunfmt` output, `msgfmt --check` on the result, then assertions that no existing OPNsense translation
  changed and that every plugin string is present; it refuses an existing output file and never writes the
  installed catalogue itself. Its `--plugin-only` mode serves a locale whose core catalogue does not exist
  (`nl_NL`), which the unmerged candidate branch `feature/optional-locale-installer-20260927` treated as an
  abort; `en_US` is skipped because OPNsense ships no reference catalogue for it.
- `install-unattended.sh`: the catalogue loop (`:101-124`) stages one merged core catalogue per locale from
  the eleven catalogues (ten core-domain items), reuses the file's existing mode where the core catalogue
  exists, prints a `NOTICE` for the plugin-only case, and feeds the items through the existing guard, backup,
  rollback and final-hash machinery; `msgcat`/`msgunfmt` joined the dependency check (`:22`); the frozen
  target count moved from `49`/`50` to **`59`**/**`60`** (`:159-167`, 38 manifest rows + 11 sidecar catalogues
  + 10 merged core catalogues, plus `rc.conf` when fresh) and `CHECK_OK`/`INSTALL_OK` now report
  `core_locales=`. A new install-phase block (`:190-226`) records first-write-wins pristine copies under
  `/var/backups/devicemonitor/core-locale/<locale>.state` and `<locale>.OPNsense.mo`, adopting a catalogue
  that appeared from outside the installer (a core upgrade) as pristine rather than mistaking the merged
  output for it.
- `uninstall.sh` `:107-154` (new section `[5b/6]`): restores the pristine core catalogue when the recorded
  copy still matches its hash, otherwise deletes only a file this installer created (hash-verified) and prunes
  the empty directories, leaving foreign files and unverifiable records untouched with an explicit warning;
  reports `Core catalogues: restored=N removed=M`.
- New `tests/test_locale_merge.py` covers both modes with pure gettext fixtures in a temporary directory,
  including the guard failing closed; `.github/workflows/ci.yml:74-75` runs it as
  `Validate core catalogue merge (DM-BL-008c)`.

Files changed: `release/merge-opnsense-catalog.sh` (new), `tests/test_locale_merge.py` (new),
`install-unattended.sh`, `uninstall.sh`, `.github/workflows/ci.yml`, plus this record and the
`PRODUCT_BACKLOG.md`/`verification/PR_SUBMISSION_NOTES.md` updates. No manifest row changed — the merge tool
runs from the checkout at install time and is not part of the installed payload — so
`release/v2.10-runtime.manifest` is byte-identical (38 rows) and the pin on `install-unattended.sh:28` needed
no refresh. Current digests: installer
`918b875353b9bb664d20d9a97b63c19156ca9eb6b22eef46fcf8861988ab579d`, uninstaller
`0cbd1eae57e84bd3d4e89c24d688538ca3003eaeebe7f66485e2f23ce42c1193`, merge engine
`9378e70428e39ab8c95bd7ed4ad98a70d01cbe6adf7e2a5c04d3f0449dbc7e82`, merge test
`065b12fd43ca05c10b47398b5035225cb72f455ad11eddde0ba731e259ccffec`.

Tests performed and results: `sh -n` on the installer, uninstaller and merge engine PASS;
`python3 -m py_compile tests/test_locale_merge.py` PASS; `python3 tests/test_locale_merge.py`
`LOCALE_MERGE=PASS`; `python3 tests/test_release_manifest.py` `V210_RELEASE_MANIFEST=PASS`;
`python3 tests/test_fresh_install_defaults.py` PASS; `python3 tests/test_translated_javascript.py` PASS;
`python3 tests/test_sidecar_catalogue.py` `SIDECAR_CATALOGUE=PASS`; `git diff --check` exit 0; workflow YAML
parses with the new step as the only structural change (32 → 33 steps).
`sh install-unattended.sh --host OPNsense.internal --check` reports
`NOTICE: no core catalogue for nl_NL; installing the plugin catalogue alone`,
`NOTICE: merged the plugin keys into 10 core catalogue(s)` and
`CHECK_OK version=2.10 predecessor=2.10 files=59 core_locales=10 daemon_running=1 host=OPNsense.internal`
(42.9 s, against `files=49` before the change), proving the overlay stages and validates for all ten live
core catalogues without an abort. The new state logic was calibrated in a sandbox that executes the
committed block text against fixtures: `RUN1=PASS` (pristine capture, `absent` recorded where no core
catalogue exists), `RUN2=PASS` (first-write-wins on reinstall, external core upgrade tolerated, externally
appeared catalogue adopted as pristine) and `UNINSTALL=PASS` (3 restored, 1 removed with empty directories
pruned, 2 unsafe cases refused with warnings). The new `Validate core catalogue merge (DM-BL-008c)` CI step is
part of the wake of this change set; its run ID is recorded in the accompanying `.cline-reports/` report,
because a commit cannot name the CI run it triggers.

Deployment (29 September 2026): the installer was executed on the testbed
(`sh install-unattended.sh --host OPNsense.internal`) after a passing pre-flight
(`CHECK_OK version=2.10 predecessor=2.10 files=59 core_locales=10 daemon_running=1 host=OPNsense.internal`) and
reported `INSTALL_OK version=2.10 files=59 core_locales=10 backup=/var/backups/devicemonitor/install-v210.O1Tggb
daemon_restarted=1`. All nine previously existing core catalogues moved from UNCHANGED to MERGED (hashes differ
from the pre-state recorded in this session), the tenth (`nl_NL`) was created from the plugin catalogue alone
(`/usr/local/share/locale/nl_NL/LC_MESSAGES/OPNsense.mo`, 34,727 B, mode 644), and
`/var/backups/devicemonitor/core-locale/` now holds ten `.state` records plus nine pristine copies whose hashes
equal the recorded pre-state. The fr_FR core catalogue grew from 13,398 to 13,400 keys — exactly the two
plugin-only strings the out-of-band 26 September merge had missed — with no existing core entry altered. configd
and the Device Monitor daemon were restarted by the installer (daemon PID 94999 → 12810); the web GUI was not
restarted.

Post-merge runtime acceptance (29 September 2026): `python3 tests/test_language_acceptance.py --engine runtime`
over the nine target languages reports every language `PASS pages=10 keys=451 … engine=runtime`
(`de_DE 435/451 translated`, `fr_FR 433`, `es_ES 443`, `it_IT 442`, `pt_BR 438`, `nl_NL 431`, `ru_RU 446`,
`ja_JP 443`, `zh_CN 443`) and the summary
`LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0` with **exit code 0**; the single gap is
`nl_NL`'s absence from `get_locale_list()` (`DM-BL-008a`), and the two shared-catalogue drift warnings (`es_ES`,
`pt_BR`, one key each) are pre-existing core wording differences that the plugin catalogue resolves.

English-fallback negative check (29 September 2026): the pre-merge fr_FR core catalogue — preserved by the
installer as the pristine copy — lacks the two plugin keys added after the 26 September hand merge, and the real
translator chain returns the English message id for them
(`dgettext('OPNsense','Plugin translations (sidecar catalogue)')` → `Plugin translations (sidecar catalogue)` with
the pristine catalogue versus `Traductions du plugin (catalogue sidecar)` with the merged one), which is exactly
the English fallback the item predicted for a system without the merge.

Unresolved: the merge rewrites OPNsense-core package-owned catalogues, so a core `pkg upgrade` can replace them
until the installer is re-run (the pristine records keep the pre-merge files, which on this testbed are the
26 September hand-merged copies rather than vendor-clean originals). That trade-off is now recorded as
`DECISIONS.md` 35, together with the measured inert-orphan overhead (one retired message id per merged catalogue,
ten keys in total) which the same decision accepts as structural overhead until the next upstream core-package
replacement — a subtractive prune is explicitly not implemented and needs a new decision plus the
provenance/vendor-baseline preconditions listed there. The Settings help string and the manual were corrected and
deployed on 29 September 2026 (commit `d65eae4`). Also outstanding: `--check` takes about 43 s because it performs
ten real merges; `DM-BL-008a` (`nl_NL` not selectable through the core language list) is unchanged and
independent.

Next recommended step: settle the testbed notification transports (repair the recipient/method/webhook URL or
disable them) so the active background scanner stops accumulating guaranteed failure lines on the first new
device.

Evidence status: the installation, the post-install catalogue comparison, the nine-language runtime acceptance
(exit 0) and the English-fallback probe were executed on the testbed in this session and are reproducible from
this checkout; the counts, digests and hashes above are quoted from that live run, and the full transcript is in
`.cline-reports/`.

## 29 September 2026 — Identity conflicts re-routed to the webhook transport (direct payload override)

Description: the notification layer gained a queue-free dispatch path so a caller can post its own JSON frame,
and the identity consumer was re-routed from email to that path. `notify_identity_email.php` no longer builds an
HTML email; it forwards the scan cycle's high-severity identity conflicts to the configured webhook endpoint as an
`identity_conflict` frame.

Work completed:
- `NotificationHandler::sendWebhook()` now takes the optional third parameter `$payloadOverride = null`. When it is
  supplied the `notification_pending` queue is not read, the endpoint-keyword type detection is skipped (type
  forced to `generic`), `hostname`/`timestamp` are filled in only when the caller omitted them, and the caller's
  array is posted as `application/json` directly through the existing curl engine. A non-array override fails with
  `Webhook payload override must be an array` instead of silently falling back to the queue, and the new branch
  guards `curl_init()` returning `false`.
- `notify_identity_email.php` is now a webhook forwarder: the STDIN contract `{"events":[…]}` and the
  high-severity `IP_IDENTITY_CHANGED`/`IPV6_IDENTITY_CHANGED` filter are preserved, the email HTML builder and the
  `sendCustomEmail()` call are removed, the frame
  `{"event":"identity_conflict","hostname":…,"timestamp":…,"severity":"high","conflict_count":N,"conflicts":[…]}` is
  constructed, and the dispatch uses `$handler->sendWebhook(false, null, $identityPayload)`. Exit codes are
  unchanged: `0` for `sent`/`skipped`, `1` for `failed`, `2` for malformed STDIN.
- Files changed: `src/opnsense/scripts/OPNsense/DeviceMonitor/NotificationHandler.php` (+61/−1),
  `src/opnsense/scripts/OPNsense/DeviceMonitor/notify_identity_email.php` (200 → 71 lines),
  `docs/USER_MANUAL.md` (`Identity email` entry re-described as webhook-delivered).
- Tests performed (29 September 2026, testbed, loopback only): `php -l` on both scripts → no syntax errors;
  `git diff --check` → clean; forwarder run with a three-event STDIN sample against a loopback receiver on
  `127.0.0.1:8777` → `{"result":"sent","message":"Webhook sent (HTTP 200)","type":"generic","test":false,"count":0}`
  with exit 0 and the delivered body keyed
  `conflict_count, conflicts, event, hostname, severity, timestamp` (`conflict_count = 2`; the low-severity
  `MAC_MULTI_IP` event was filtered out; no `devices` key, proving the queue was not pulled); malformed STDIN and
  `{"events":"nope"}` → exit 2; an all-low-severity sample → `skipped`, exit 0; harness checks: non-array override →
  `failed`, override against an `ntfy`-keyword URL → `type` still `generic`, caller frame without hostname/timestamp
  → both filled in; regression checks of the two-argument calls → real mode `skipped` ("No pending notifications"),
  test mode `ok`/`type=generic` with the original placeholder frame.
- Hook engine: `.githooks/pre-commit` executed directly → exit 0; the run completed on Tuesday 20:03 AEST, i.e.
  outside both peak windows (11:00–14:00 and 16:00–20:00 AEST weekdays), so the work ran in the off-peak tier.

Unresolved: `scan_network.py::should_send_identity_email()` still gates the identity leg on `email_enabled`,
`email_to` and `identity_email_enabled` (testbed value `0`), so on this testbed the new identity→webhook path
cannot fire yet even though no email is sent (the replacement gate is now recorded as `DECISIONS.md` 36 and is not
implemented yet, pending sign-off); the Settings label and help (`Email high-severity conflict alerts`,
"Send an email when a new high-severity IPv4 or IPv6 address conflict is detected.") still describe email delivery
and are translated in eleven locales, so correcting them needs a catalogue regeneration step; the changed scripts
are committed to neither the repository nor `/usr/local` (no commit or deployment was instructed, so the live
installation still contains the old email-forwarding copy); `webhook_url` still points at the stopped loopback mock
(`http://127.0.0.1:8777/dm-webhook`).

Next recommended step: obtain sign-off on `DECISIONS.md` 36 — the dedicated `identity_webhook_enabled` subcategory
switch gating the identity leg — and then implement that decision (gate in `scan_network.py`, config key plus
validation, checkbox in the Webhook Notifications tab, catalogue labels, Settings wording, manual).

## 29 September 2026 — Identity gating policy evaluated: a dedicated webhook subcategory switch is selected

Description: the open question left by the identity re-route — which configuration switch should authorise
identity-conflict alerts — was evaluated against the two candidate routing policies and decided. This entry records
a policy decision only: no implementation file was changed and the Git index was left unmutated, pending sign-off.

Work completed:
- **Option A (map identity alerts onto the generic `webhook_enabled`/`webhook_url` gate) evaluated and rejected.**
  `webhook_enabled` is the documented master switch for new-device webhook notifications, so mapping identity
  alerts onto it widens the administrative permission set as a side effect of an unrelated action. The only
  existing webhook scope control, `webhook_vlans`, filters the new-device leg only, and identity events carry an
  `interface` rather than a VLAN, so the category would be delivered with no scope filter at all. The two
  categories could not be enabled or disabled independently, and the identity leg would light up on installations
  that never opted into conflict alerting, contrary to the fail-closed `"0"` defaults used by every other category.
- **Option B (`identity_webhook_enabled`, an isolated subcategory checkbox in the Webhook Notifications option
  tree) selected.** It keeps the administrative permission discrete and consistent with the existing per-category
  precedent (`identity_email_enabled`, `service_email_enabled` with its three sub-options), defaults to `"0"`, and
  stays independent of the email recipient and method that this testbed does not have.
- **Option C (reuse `identity_email_enabled` as the webhook gate) considered and rejected** as a third variant: an
  email-named key governing webhook delivery misleads operators, breaks the terminology rule, and would have to be
  split again when an email channel returns.
- Effective gate recorded as a three-part condition: `enabled`; `identity_webhook_enabled`; and `webhook_enabled`
  with a non-empty `webhook_url` (the precondition already enforced by `ConfigController::save` and
  `NotificationHandler::sendWebhook()`), with `identity_email_enabled` no longer consulted by the identity leg.
- `DECISIONS.md` 36 records the decision, the rejected alternatives and the accepted consequences; the previous
  ledger entry's `Unresolved` and `Next recommended step` records were updated to this path.
- Files changed (documentation only): `DECISIONS.md` (new decision 36), `PROJECT_STATE.md` (this entry plus the
  two updated records above).

Tests performed: `git --no-pager diff --cached --stat` → empty output (nothing staged, index unmutated);
`git --no-pager diff --check` → clean; no source, configuration, view or installer file modified in this task
(`git --no-pager diff --stat` lists only the two ledger files from this task, plus the still-uncommitted re-route
changes from the previous one, all unstaged). No runtime change exists to test, so no runtime evidence is claimed.

Unresolved: implementation of decision 36 has not started (gate predicate and call site in `scan_network.py`,
`identity_webhook_enabled` in `defaults.json`, read/validation/assignment in `ConfigController::save`, the checkbox
row in the Webhook Notifications tab with its JS load/save wiring, the label in 11 locale catalogues plus `en_US`,
and the manual section). Until then the identity leg stays dark wherever the email settings are unsatisfied, and
`identity_email_enabled` remains stored and displayed while no longer being consulted, so its label needs the same
correction step. Interface/VLAN scoping of identity frames is still undecided. The re-route itself remains
uncommitted and undeployed, and `webhook_url` still points at the stopped loopback mock.

Next recommended step: sign off `DECISIONS.md` 36, then implement it as one step (gate, config key, UI row, labels,
manual wording).

Evidence status: the evaluation is based on the checked-in sources inspected in this session — `settings.volt`
tabs at lines 35–240 with the JS load/save blocks at 677–773, `defaults.json`, `ConfigController::save`,
`scan_network.py`'s identity gate and notification section, and the eleven `docs`-referenced `.po` catalogues — and
is reproducible from this checkout without modifying it.

## 29 September 2026 — `identity_webhook_enabled` implemented: schema, backend, Webhook-tab switch and catalogues

Description: decision 36 was implemented end to end. The identity-conflict leg is now authorised by its own
Webhook-tab subcategory switch instead of the email settings, and the inert email-side control and its catalogue
strings were decommissioned.

Work completed:
- `src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json`: `"identity_webhook_enabled": "0"` added
  (36 → 37 config keys; fail-closed default).
- `.../Api/ConfigController.php`: the field is fetched (`:128`), validated as `"0"`/`"1"` (`:171`, message
  `Invalid identity webhook enabled value`) and written (`:418`) inside the same save transaction as the other
  webhook keys.
- `scan_network.py`: `should_send_identity_email()` now gates on `enabled` **and** `identity_webhook_enabled`
  **and** `webhook_enabled` **and** a non-empty `webhook_url` (`:6231`–`:6245`), with the legacy email variables
  removed from the predicate; the new key is populated in all three `load_config()` branches (`:75`, `:114`,
  `:151`); the legacy `identity_email_enabled` key stays in the loaded dict for schema compatibility but gates
  nothing.
- `settings.volt`: the Email-tab "Email high-severity conflict alerts" row and its help button were removed
  (lines 119–134 of the previous revision) and a "Identity conflict alerts" checkbox row with its help was added
  to the Webhook Notifications tab (`:209`); the JS load (`:676`) and save (`:772`) now use
  `identity_webhook_enabled`, and the dead `identity_email_enabled` post field was dropped.
- 11 catalogues (`cs_CZ`, `de_DE`, `en_US`, `es_ES`, `fr_FR`, `it_IT`, `ja_JP`, `nl_NL`, `pt_BR`, `ru_RU`,
  `zh_CN`): `Email high-severity conflict alerts`, `Send an email when a new high-severity IPv4 or IPv6 address
  conflict is detected.` and the now-unused `About Conflict Alerts` were removed, and
  `Identity conflict alerts` plus `Send a high-severity IPv4 or IPv6 address conflict alert to the webhook
  endpoint.` were added to each (1584 → 1581 lines per file).
- `.github/workflows/ci.yml`: the identity-leg step asserts the new default and drives the new gate, with added
  negative cases (transport off, empty URL, monitoring off, no events, missing key fails closed) and a positive
  case proving the email settings no longer gate the leg.
- `docs/USER_MANUAL.md`: the "Identity email" entry left section 14.2 and "Identity conflict alerts" is now
  documented in 14.3; `DECISIONS.md` 36 gained an amendment recording the control removal, the inert stored key
  and the retained `should_send_identity_email()`/`notify_identity_email.php` names.
- `release/v2.10-runtime.manifest` and `install-unattended.sh:28`: eight stale rows refreshed (the two
  notification scripts from the previous change set plus the six files changed here), row count still 38, manifest
  digest `ccdfe4c6555dc3537257159ea37c332e1aa648ff95b607d5738d2b56fa4905d8` →
  `b99d9ed0b9a3dbf8cde28fff904e8e012f1a7f8e6e04b4e8ffa1eb1a7a020c5f`, and the pinned digest on line 28 updated
  in the same step.

Tests performed and results (29 September 2026, testbed):
- `msgfmt --check` on all eleven catalogues → `OK` for each.
- `php -l` over every `src/**/*.php` → no syntax errors; `python3 -m py_compile` over every `src/**/*.py` → exit 0
  (bytecode caches removed afterwards).
- Identity-gate harness mirroring the CI block → `IDENTITY_GATE_HARNESS=PASS checks=9`: subcategory on → send;
  subcategory off → no send; webhook master off → no send; empty URL → no send; monitoring off → no send; no
  events → no send; `identity_email_enabled=False` ignored → still send; `email_enabled=False` with an empty
  recipient ignored → still send; key absent → fail closed. `load_config()` on this testbed reports the key as
  `False`.
- Language acceptance: `--engine runtime --views <source views> --installed-po <staged .mo>` →
  `LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 failures=0`, exit 0; the interpolate engine →
  `LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 failures=0`, exit 0. The only new warnings are the shared core
  catalogue still carrying the retired wording for the two new ids, because the deployment was not refreshed.
- `python3 tests/test_release_manifest.py` → `V210_RELEASE_MANIFEST=PASS` (it was failing before the regeneration,
  because the previous change set had already left two rows stale); `python3 tests/test_sidecar_catalogue.py` →
  `SIDECAR_CATALOGUE=PASS`; `sh -n install-unattended.sh` → clean; `git --no-pager diff --check` → clean.

Unresolved: nothing is deployed, so the live testbed still runs the previous view, catalogue, controller and
scanner; the acceptance test therefore used its documented staged mode (`--views` + `--installed-po`) and would
fail its installed-versus-source comparison until deployment; `identity_email_enabled` survives as a stored key
nothing posts, so it settles to `"0"` on the next save; the `email`-named function and helper file are recorded
naming residuals; interface/VLAN scoping of identity frames is still undecided; `webhook_url` still points at the
stopped loopback mock (`http://127.0.0.1:8777/dm-webhook`).

Next recommended step: deploy this change set on the testbed with the guarded installer, re-run the acceptance
test without the staged override so the installed artefacts are compared, and capture the identity-frame delivery
evidence with `identity_webhook_enabled = "1"`.

Evidence status: the catalogue, PHP, Python, gettext, manifest and acceptance results above were produced in this
session on the testbed and are reproducible from this checkout; nothing was committed or deployed.

## 29 September 2026 — Identity webhook tier deployed to the testbed and live delivery verified

Description: the `identity_webhook_enabled` change set was installed on the testbed with the guarded installer, the
deployed tree was accepted against the source by the language test, and the identity leg was then exercised end to
end against a loopback receiver.

Work completed:
- `sh install-unattended.sh --check --host OPNsense.internal` → `CHECK_OK version=2.10 predecessor=2.10 files=59
  core_locales=10 daemon_running=1 host=OPNsense.internal`, exit 0 (no mutation).
- `sh install-unattended.sh --host OPNsense.internal` → `INSTALL_OK version=2.10 files=59 core_locales=10
  backup=/var/backups/devicemonitor/install-v210.vVNqNB daemon_restarted=1`, exit 0; configd was restarted, the
  daemon stopped and started (now pid 12099).
- Deployed-versus-source comparison (`cmp -s`) reports byte-identical files for `settings.volt`,
  `Api/ConfigController.php`, `defaults.json`, `scan_network.py`, `notify_identity_email.php` and
  `NotificationHandler.php`; the installed view carries the three `identity_webhook_enabled` references, the
  installed defaults the key itself, and the installed controller five occurrences.
- Deployed-tree acceptance with no staged overrides: `python3 tests/test_language_acceptance.py --engine runtime` →
  `LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0`, exit 0. No installed-view or
  installed-catalogue drift is reported, and the two previous new-key warnings are gone because the merge installed
  the strings. The single gap remains the known `nl_NL`/`DM-BL-008a` omission from `get_locale_list()`; the only
  other warnings are the pre-existing core wording differences for the shared `Language` id (`es_ES`, `pt_BR`).
- Merge evidence: `msgunfmt` on the deployed core catalogues returns `Identity conflict alerts` →
  `Warnungen bei Identitätskonflikten` (`de_DE`) and `ID競合アラート` (`ja_JP`); the deployed plugin catalogue
  carries the new help string.
- Configuration tier: guarded rewrite of `/var/db/devicemonitor/config.json` setting
  `identity_webhook_enabled = "1"` (35 → 36 keys, only that key changed, mode 0600 preserved, sha256
  `dcec072b46da65953af113c4c946cd706ea8dae6b64172a60dbff7a92f6ef8a8` →
  `b96575bf7cfaf5ab2043cd388a88e0a29f9c7ee1c5f6e7ea7464ba63c44d8f20`, backup
  `/var/backups/devicemonitor/identity-webhook-20260929-202526/config.json`).
- Delivery against the loopback receiver on `127.0.0.1:8777` (the configured `webhook_url`):
  - Direct backend utility: `/usr/local/bin/php .../notify_identity_email.php` fed a three-event sample (two
    high-severity IP/IPv6 identity events plus one low-severity `MAC_MULTI_IP`) → `{"result":"sent","message":
    "Webhook sent (HTTP 200)","type":"generic","test":false,"count":0}`, exit 0. The received frame is 662 B with
    keys `conflict_count, conflicts, event, hostname, severity, timestamp`, `event=identity_conflict`,
    `severity=high`, `conflict_count=2` equal to the `conflicts` array length, `hostname=OPNsense.internal`, and
    **no `devices` key**; the low-severity sample was filtered out.
  - Scanner path: the deployed `scan_network.send_identity_email()` — the function the new gate authorises —
    returned `True`, logged `[IDENTITY-EMAIL] Sent batched alert for 2 high-severity event(s)`, and delivered a
    frame with `conflict_count=1` (only the high-severity event, the low-severity one filtered) and again no
    `devices` key.
  - Live gate check against the deployed module: `load_config()['identity_webhook_enabled']` is `True`,
    `webhook_enabled` is `True` with a non-empty `webhook_url`, `should_send_identity_email(cfg, events)` is `True`
    and `False` with an empty event list.
  - `/var/log/devicemonitor.log` contains zero `FAILED`/`Failed`/`Invalid webhook URL` lines in the whole
    post-install window (20:22–20:26).
- Receivers stopped afterwards; nothing is bound to `127.0.0.1:8777`.

Unresolved: `identity_webhook_enabled` is now `"1"` on the testbed while `webhook_url` still points at the
temporary loopback mock, so the next genuine conflict will log a delivery failure until a permanent receiver
exists or the flag returns to `"0"`; the change set is still uncommitted, so no CI run id exists; interface/VLAN
scoping of identity frames stays undecided; the inert `identity_email_enabled` key remains stored and unexposed;
`DM-BL-008a` (`nl_NL`) is unchanged.

Next recommended step: settle the endpoint tier — point `webhook_url` at a permanent receiver and keep
`identity_webhook_enabled = "1"`, or set the flag back to `"0"` — and record the resulting recipient/message
evidence.

Evidence status: the installer output, the deployed-versus-source comparisons, the installed-catalogue inspection,
the accepted language run and both delivery captures were produced in this session on the testbed and are
reproducible from the transcript in `.cline-reports/`; the change set itself is still uncommitted.

## 29 September 2026 — Identity webhook tier redeployed and live delivery re-verified

Description: the same `identity_webhook_enabled` change set was redeployed on the testbed with the guarded installer,
the deployed tree was re-accepted against source with no staged overrides, and the identity leg was re-exercised end
to end against the loopback receiver.

Work completed:
- `sh install-unattended.sh --host OPNsense.internal` (21:20) → `NOTICE: merged the plugin keys into 10 core
  catalogue(s)`, `CHECK_OK version=2.10 predecessor=2.10 files=59 core_locales=10 daemon_running=1
  host=OPNsense.internal`, then `INSTALL_OK version=2.10 files=59 core_locales=10
  backup=/var/backups/devicemonitor/install-v210.c6EzNx daemon_restarted=1` as the final output line; no `ABORT` or
  rollback path ran. `configd` was restarted and the daemon stopped and started (now pid 56372).
- Deployed-versus-source `cmp -s` reports byte-identical files for `settings.volt`, `Api/ConfigController.php`,
  `defaults.json`, `scan_network.py`, `notify_identity_email.php`, `NotificationHandler.php` and the `cs_CZ`/`en_US`
  `.po` files.
- Deployed-tree acceptance with no staged overrides: `python3 tests/test_language_acceptance.py --engine runtime` →
  `LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0`, exit 0. The single gap remains the known
  `nl_NL`/`DM-BL-008a` omission; the other warnings are the pre-existing core wording differences for the shared
  `Language` id (`es_ES`, `pt_BR`).
- Observation recorded, not a defect: `release/v2.10-runtime.manifest` packages only the `cs_CZ` and `en_US` `.po`
  files, so the nine other installed plugin `.po` files still carry 2026-09-26 timestamps and the pre-webhook wording;
  the runtime chain resolves the compiled `.mo`, which the installer stages for all eleven locales and which the
  acceptance engine audits, so no drift is reported. Nothing was changed.
- Configuration tier (idempotent guarded re-assert): `/var/db/devicemonitor/config.json` still carries
  `identity_webhook_enabled = "1"` (36 keys, mode 0600 preserved, sha256 unchanged
  `b96575bf7cfaf5ab2043cd388a88e0a29f9c7ee1c5f6e7ea7464ba63c44d8f20`, `changed_keys = []`), backup
  `/var/backups/devicemonitor/identity-webhook-20260929-212213/config.json`; `webhook_enabled = "1"` and
  `webhook_url = http://127.0.0.1:8777/dm-webhook`.
- Delivery against the loopback receiver on `127.0.0.1:8777` (receiver self-check `200`):
  - Direct backend utility: `/usr/local/bin/php .../notify_identity_email.php` fed the three-event sample (two
    high-severity IP/IPv6 identity events plus one low-severity `MAC_MULTI_IP`) →
    `{"result":"sent","message":"Webhook sent (HTTP 200)","type":"generic","test":false,"count":0}`, exit 0. The frame
    is 662 B, `application/json`, from `127.0.0.1`, with keys exactly
    `conflict_count, conflicts, event, hostname, severity, timestamp`, `conflict_count=2` equal to the `conflicts`
    array length, `hostname=OPNsense.internal`, and **no `devices` key**; the low-severity sample was filtered.
  - Scanner path: the deployed `scan_network.load_config()` resolves `identity_webhook_enabled` to `True`,
    `should_send_identity_email(cfg, events)` is `True` and `False` for an empty list, and the deployed
    `send_identity_email()` returned `True`, logged `[IDENTITY-EMAIL] Sent batched alert for 2 high-severity
    event(s)` at 21:22:34, and delivered a 409 B frame with `conflict_count=1` (low-severity event filtered) and no
    `devices` key. The log count is `len(events)` (`scan_network.py:6299–6302`) and matches the batch the production
    call site passes (`:7131` passes only high-severity events); the harness added the low-severity event on purpose
    to prove the helper filters it.
  - `/var/log/devicemonitor.log` contains zero `FAILED`/`Failed`/`ROLLBACK`/`ABORT`/`Invalid webhook URL` lines in the
    post-install window (21:21–21:23), and the daemon completed a normal scan at 21:22:40.
- Receivers stopped afterwards; nothing is bound to `127.0.0.1:8777`. Report: `.cline-reports/REPORT-20260929-212316.md`.

Unresolved: `identity_webhook_enabled` is `"1"` while `webhook_url` still points at the temporary loopback mock, so
the next genuine conflict will log a delivery failure until a permanent receiver exists or the flag returns to `"0"`;
the change set is still uncommitted, so no CI run id exists; interface/VLAN scoping of identity frames stays
undecided; the inert `identity_email_enabled` key remains stored and unexposed; `DM-BL-008a` (`nl_NL`) is unchanged.

Next recommended step: settle the endpoint tier — point `webhook_url` at a permanent receiver and keep
`identity_webhook_enabled = "1"`, or set the flag back to `"0"` — and record the resulting recipient/message evidence.

Evidence status: the installer output, the deployed-versus-source comparisons, the accepted language run and both
delivery captures were produced in this session on the testbed and are reproducible from
`.cline-reports/REPORT-20260929-212316.md`; the change set was still uncommitted at that point (it was committed the next
session as `57696ac`).

## 29 September 2026 — Identity webhook tier committed on `v2.10-development`, pushed, CI green

Description: the verified `identity_webhook_enabled` change set was committed and published to `origin`; the
repository baseline already ships the feature dark.

Work completed:
- Baseline check (no source edit needed): `src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json:20` is
  `"identity_webhook_enabled": "0"`, and `.github/workflows/ci.yml:487–488` asserts that value. The `"1"` in
  `/var/db/devicemonitor/config.json` is testbed operator state, not the baseline, and was left untouched; production
  (`192.168.20.254`) was not contacted in this task.
- Pre-commit inspection: `git --no-pager diff --stat` → 23 files, 591 insertions(+), 292 deletions(-);
  `git diff --check` → clean.
- Staging: `git add -u` staged exactly the 23 modified tracked files (`staged_files=23`); the instruction's bare
  filenames were replaced by modification-status staging, and `.github/workflows/ci.yml` plus `install-unattended.sh`
  (named by neither the example list nor excluded by the "all 23" criterion) were included.
- Commit `57696ac` — "feat/docs: implement identity_webhook_enabled tier, remove dead email code, and record delivery
  evidence" (23 files changed, 591 insertions(+), 292 deletions(-)); post-commit `git status` shows no modified
  tracked file.
- Push: `d37c261..57696ac v2.10-development -> v2.10-development` to
  `git@github.com:apg19590209/opnsense-devicemonitor.git`; `git rev-parse HEAD origin/v2.10-development` → both
  `57696acfb33f6d6c4f67d93f12742923f263808f`.
- CI: push event run `36561954052` for head SHA `57696ac` → `status=completed`, `conclusion=success`, 45 s
  (2026-09-29T11:28:25Z → 11:29:10Z), inspected with `gh run list`/`gh run view` per `.clinerules/90`.
- Deliberately left untracked (outside this task's 23-file set): `.clineignore`,
  `.clinerules/05-optimization-protocol.md`, `.clinerules/15-auto-capture-reports.md`.
- Report: `.cline-reports/REPORT-20260929-212946.md`. This ledger entry itself is uncommitted at the time of writing.

Unresolved: the testbed still runs `identity_webhook_enabled = "1"` while `webhook_url` points at the stopped loopback
mock, so a genuine conflict would log a delivery failure until an operator supplies a verified destination or clears
the flag; this `PROJECT_STATE.md` ledger update is uncommitted, so a docs-only commit is still pending; interface/VLAN
scoping of identity frames stays undecided; the inert `identity_email_enabled` key remains stored and unexposed;
`DM-BL-008a` (`nl_NL`) is unchanged.

Next recommended step: commit this ledger update as a docs-only commit on `v2.10-development` and check its CI run.

Evidence status: the diff statistics, staged-file count, commit, push and CI run id above were produced in this
session on the testbed and are reproducible from `.cline-reports/REPORT-20260929-212946.md`.

## 29 September 2026 — Testbed returned to safe-dark and `identity_email_enabled` storage footprint audited

Description: the live testbed flag was reverted to the safe-dark baseline and the obsolete email key was traced through
every parse and storage surface ahead of its deletion.

Work completed:
- Guarded one-key rewrite of `/var/db/devicemonitor/config.json` (helper `/tmp/dm-verify/disable_identity_webhook.py`,
  backup `/var/backups/devicemonitor/identity-webhook-disable-20260929-213718/config.json`):
  `identity_webhook_enabled` `"1"` → `"0"`, 36 keys before and after, `changed_keys = ['identity_webhook_enabled']`,
  `mode_before = 600 mode_after = 600`, sha256 `b96575bf7cfaf5ab2043cd388a88e0a29f9c7ee1c5f6e7ea7464ba63c44d8f20` →
  `52f7bdda6153d8aa31bb5a99b040ccef870857dcbebe56cf4a256179039b6d8a`, `SAFE_DARK_TIER=PASS`.
- Read-only proof through the deployed module: `load_config()` → `identity_webhook_enabled = False`,
  `should_send_identity_email(cfg, high-severity event)` → `False`. No restart was needed (`load_config()` runs per
  scan cycle at `scan_network.py:7515`/`:7588`, `monitor_daemon.py:174`/`:183`) and the 21:37:34 scheduled scan ran
  normally; the daemon (pid 56372) stayed healthy.
- `identity_email_enabled` audit result: it is **never persisted to a storage table or structural array**. Parse sites:
  `scan_network.py:74` (no-config branch), `:113` (normal branch), `:150` (exception fallback) — all `== '1'` bool
  coercion into the transient `load_config()` dict. Persistence sites: `Api/ConfigController.php:127` (dead POST field
  defaulting to `'0'`), `:167` (allow-list validation), `:395` (written to `config.json`). Baseline/CI:
  `defaults.json:19`, `ci.yml:486`.
- Negative evidence: `devices.db` has 19 tables and no `identity_email`/`config` column (the only `%identity%` value is
  the table name `device_identity_events` in `sqlite_sequence`); `/conf/config.xml` 0 hits (also 0 `devicemonitor`
  hits); `DeviceMonitor.xml` and `ACL/ACL.xml` 0 hits; live `settings.volt` 0 hits (stored but unexposed); `tests/`,
  `Makefile`, `install-unattended.sh`, `uninstall.sh`, `release/` 0 hits; source catalogues and deployed `.mo` files
  carry the replacement id (`Identity conflict alerts`) and 0 occurrences of the removed email string.
- Live/historical residues: deployed `defaults.json`, deployed `scan_network.py` + its compiled
  `__pycache__/scan_network.cpython-313.pyc`, deployed `Api/ConfigController.php` (3 sites), three stale view backups
  (`settings.volt.orig`, `settings.volt.pre-webfix-20260928`, `settings.volt.pre-dmbl004c-20260928-202215`),
  `/var/db/devicemonitor/config.json:5` and 17 `/var/backups/devicemonitor/*/config.json` copies.
- No rule literally named "SAFE protocol" exists in the repository; the audit was run under the closest documented
  discipline (`PROJECT_RULES.md:64` smallest safe change, read-only inspection) and nothing was deleted.
- Report: `.cline-reports/REPORT-20260929-213828.md`.

Unresolved: the `identity_email_enabled` deletion is prepared but not executed (it needs `defaults.json`,
`ConfigController.php`, `scan_network.py` and `ci.yml` edits plus a decision on existing `config.json` values); this
ledger entry is uncommitted; the generic `webhook_enabled = "1"` tier still points at the stopped loopback mock (no
longer reachable by the now-dark identity leg); interface/VLAN scoping of identity frames stays undecided;
`DM-BL-008a` (`nl_NL`) is unchanged.

Next recommended step: authorise the docs-only commit of this ledger entry (and check its CI run), then treat the
`identity_email_enabled` deletion as its own scoped task.

Evidence status: the rewrite output, the deployed-gate re-check and the audit greps were produced in this session on
the testbed and are reproducible from `.cline-reports/REPORT-20260929-213828.md`.

## 29 September 2026 — Dead `identity_email_enabled` key deleted from the schema, controller, scanner and CI guards

Description: the obsolete identity email flag was removed from every code and CI surface, with the release manifest and
its installer pin refreshed as a mechanical consequence.

Work completed:
- Ledger first: `PROJECT_STATE.md` (safe-dark reversion and footprint audit from the previous session) was committed as
  `4613ae9` and pushed (`e23af5a..4613ae9`).
- Deletions made (repository references now 0 in `src/`, `tests/`, `.github/`, `install.sh`, `install-unattended.sh`,
  `uninstall.sh`, `release/`, `Makefile`):
  - `defaults.json:19` — baseline row `"identity_email_enabled": "0"` removed (config keys 37 → 36).
  - `Api/ConfigController.php` — POST read (`:127`), allow-list validation (`:167–169`) and storage write (`:395`)
    removed; the `identity_webhook_enabled` validation block is untouched.
  - `scan_network.py` — the three `load_config()` load sites removed (`:74` no-config branch, `:113` normal branch,
    `:150` exception fallback); no adjacent boolean filter needed changing because the key had no consumer.
  - `.github/workflows/ci.yml:486` — the baseline assertion for the dead key removed; the
    `identity_webhook_enabled == "0"` assertion is retained.
- Mechanical release hygiene: `tests/test_release_manifest.py` pins the SHA-256 of every packaged file, so the three
  changed rows (`ConfigController.php`, `defaults.json`, `scan_network.py`) were refreshed in
  `release/v2.10-runtime.manifest` (38 rows, 3 digests changed) and the manifest pin at `install-unattended.sh:28` was
  re-pinned `b99d9ed0…` → `0abe6065ac290523bf5396c226e7a63d4b2ab09a1ec96ebf7eb28ebed8a70b32`.
- Validation: `python3 -m py_compile` over all packaged Python → PASS; `php -l` over all packaged controllers/models/
  scripts → PASS; `defaults.json` parses with 36 config keys, `identity_webhook_enabled` present and the dead key absent;
  `ci.yml` parses as YAML → PASS; `tests/test_fresh_install_defaults.py` and `tests/test_release_manifest.py` → PASS;
  guarded non-mutating `sh install-unattended.sh --check --host OPNsense.internal` → `CHECK_OK version=2.10
  predecessor=2.10 files=59 core_locales=10 daemon_running=1 host=OPNsense.internal`, exit 0.
- Behavioural proof (`/tmp/dm-verify/legacy_key_removed.py`, test scaffolding): the live `config.json` still contains the
  legacy key on disk, yet `load_config()` from source returns 31 keys with `identity_email_enabled` absent and
  `should_send_identity_email()` still returns `True`/`False` correctly → no unresolved variable, no `KeyError`, and
  existing configuration files keep working.
- Historical mentions were deliberately **not** rewritten: `DECISIONS.md` (decision 36 records why the key is no longer
  consulted), earlier `PROJECT_STATE.md` entries and the `.cline-reports/` artefacts describe the key as history.

Unresolved: the testbed still runs the previously deployed copies (no installer run or deployment was requested) and its
`/var/db/devicemonitor/config.json` still stores `identity_email_enabled: "0"` — the runtime ignores it and it would
disappear on the next GUI save, but the deployed tree drifts from source until the next guarded install; interface/VLAN
scoping of identity frames stays undecided; `DM-BL-008a` (`nl_NL`) is unchanged.

Next recommended step: redeploy on the testbed with `sh install-unattended.sh --host OPNsense.internal` and re-run
`python3 tests/test_language_acceptance.py --engine runtime` so the deployed tree matches source again.

Evidence status: the deletions, the document/AST/YAML/JSON checks, the release-manifest refresh, the `--check` run and
the loader harness were produced in this session and are reproducible from the accompanying `.cline-reports/` artefact.

## 29 September 2026 — Flag-deletion set deployed to the testbed; deployed-tree acceptance green; daemon cycles clean

Description: the committed `identity_email_enabled` deletion set was installed on the testbed with the guarded installer
and the deployed tree was re-accepted against source with the runtime language engine.

Work completed:
- `sh install-unattended.sh --host OPNsense.internal` (21:47:15 → 21:48:19) → `NOTICE: merged the plugin keys into 10 core
  catalogue(s)`, `CHECK_OK version=2.10 predecessor=2.10 files=59 core_locales=10 daemon_running=1
  host=OPNsense.internal`, `BACKUP_READY=/var/backups/devicemonitor/install-v210.lit1aY`, then
  `INSTALL_OK version=2.10 files=59 core_locales=10 backup=/var/backups/devicemonitor/install-v210.lit1aY
  daemon_restarted=1`, `install_rc=0`; no `ABORT` or rollback path ran. `configd` restarted and the daemon was
  stopped/started (pid 56372 → 22823).
- Manifest pin integrity: the installer accepted the regenerated manifest
  (`sha256 = 0abe6065ac290523bf5396c226e7a63d4b2ab09a1ec96ebf7eb28ebed8a70b32`, 38 rows) and re-hashed all 59 targets.
- Deployed-versus-source `cmp -s` → IDENTICAL for `Api/ConfigController.php`, `defaults.json`, `scan_network.py`,
  `settings.volt`, `notify_identity_email.php`, `NotificationHandler.php`; deployed `defaults.json` and `scan_network.py`
  contain 0 references to the deleted key.
- Deployed-tree acceptance with no staged overrides: `python3 tests/test_language_acceptance.py --engine runtime` →
  `LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0`, exit 0 (gap = known `nl_NL`/`DM-BL-008a`; the
  other warnings are the pre-existing core wording differences for the shared `Language` id in `es_ES`/`pt_BR`).
- Daemon configuration-map acceptance: the restarted daemon completed full scans at 21:48:38 and 21:49:39 and started
  one at 21:50:20; a `Traceback|KeyError|NameError|TypeError|ValueError|Exception|error|Error|FAILED|Failed` grep over
  the 21:47–21:50 log window returned no lines.
- Live configuration map through the deployed module: `load_config()` → 31 keys with `identity_email_enabled` absent and
  no exception; `should_send_identity_email(cfg, high-severity event)` → `False`, so the identity tier remains
  safe-dark. `/var/db/devicemonitor/config.json` still stores the inert `identity_email_enabled: "0"` and was not
  modified.
- Report: `.cline-reports/REPORT-20260929-215027.md`.

Unresolved: this ledger entry is uncommitted; the live `config.json` still carries the inert key (a separate authorised
cleanup); the generic `webhook_enabled = "1"` tier still points at the stopped loopback mock, now unreachable by the
identity leg; interface/VLAN scoping of identity frames stays undecided; nine stale installed plugin `.po` files remain
outside the runtime manifest; `DM-BL-008a` (`nl_NL`) is unchanged.

Next recommended step: commit and publish this ledger entry as a docs-only commit on `v2.10-development` and check its
CI run.

Evidence status: the installer output, the deployed-versus-source comparisons, the accepted language run and the daemon
log windows were produced in this session on the testbed and are reproducible from
`.cline-reports/REPORT-20260929-215027.md`.

## 29 September 2026 — Identity-webhook VLAN-bypass request closed as already implemented; testbed left safe-dark

Description: a request to modify `should_send_identity_email()` (or the adjacent identity alert block) in `scan_network.py`
so identity conflict webhooks bypass the `webhook_vlans` filter and alert on all interfaces was investigated and **closed
without a code change**: the requested behaviour is already the implemented behaviour, and the requested follow-ons
(installer deploy, language acceptance, manifest regeneration) are mutually inconsistent. The user then decided to leave
the tier safe-dark.

Work completed:
- Source inspection, read-only: `scan_network.py:6228-6243` (`should_send_identity_email()`) gates only on a non-empty
  `events`, `enabled`, `identity_webhook_enabled`, `webhook_enabled` and `webhook_url`, and contains **no reference to
  `webhook_vlans`**. Runtime proof with the function extracted via `ast` and executed against a synthetic high-severity
  event: `webhook_vlans` absent → `True`; `'LAN10'` → `True`; `'NOPE,OTHER'` → `True` (event VLAN deliberately outside
  every allow-list).
- `webhook_vlans` is enforced at exactly one site, `:7143`/`:7145`, and only over `new_devices` for the *new-device*
  webhook (`send_webhook_via_php_api()`, `:6151`) — a different notification leg from the identity conflict leg, whose
  chain (`:6197` → `:6228` → `:6246` → `notify_identity_email.php` → `NotificationHandler::sendWebhook()`) is VLAN-free
  end to end. `grep -i identity | grep -i vlan` over the file returns nothing, so there is no "adjacent identity alert
  block" carrying VLAN logic to edit. The docstring names `DECISIONS.md` 36 as the authority, i.e. the bypass is
  intentional by design.
- Follow-on inconsistency (why the requested chain could not be run): `install-unattended.sh:28` pins the manifest's own
  digest — `sha256 -q release/v2.10-runtime.manifest` must equal
  `0abe6065ac290523bf5396c226e7a63d4b2ab09a1ec96ebf7eb28ebed8a70b32` with 38 rows. The on-disk manifest matches that pin
  today, so regenerating it to "match the updated file signatures" changes the digest and the installer aborts at line 28
  — **before** the `--check` early exit, so even a read-only `--check` would fail. Regeneration would also have blessed
  pre-existing drift rather than this session's work: the deployed `scan_network.py` is byte-identical to the upstream
  working tree (`4fd87dc7…fce5e3ed`) while the v2.9 manifest on `origin/main` expects `02d1e265…`, and the live
  `defaults.json` is `version 2.10` against a v2.9 installer that refuses any predecessor other than `2.8|2.9`.
- Checkout correction: `install-unattended.sh`, `release/v2.10-runtime.manifest` and `tests/test_language_acceptance.py`
  all exist in `/root/src/opnsense-devicemonitor-upstream` (branch `v2.10-development`). They are absent from
  `/usr/local/cline-freebsd/src/cline` (`master`, a 5-path record set) and from `origin/main` (the older v2.9 tier). That
  checkout, not the record set, is the target for any future work of this kind.
- Safe-dark rationale recorded, not changed: `defaults.json:19` ships `"identity_webhook_enabled": "0"` and
  `.github/workflows/ci.yml:487` asserts that value; `PROJECT_STATE.md:3297-3300` already classifies the live `"1"` as
  "testbed operator state, not the baseline"; and commit `4613ae9` (21:40:59) recorded the deliberate reversion at
  21:37:18 with `SAFE_DARK_TIER=PASS`.
- Zero-mutation proof: `/var/db/devicemonitor/config.json` sha256 is `52f7bdda…b6d8a`, **byte-identical to the digest**
  that commit `4613ae9` recorded after the reversion, and its mtime is still 21:37; the deployed `scan_network.py`
  (`4fd87dc7…fce5e3ed`) and `NotificationHandler.php` (`28e2d252…`) are unchanged; `find -mmin -25` over the plugin and
  config directories shows only the daemon-written `devices.db`.
- Live read-only gate check through the deployed function: `should_send_identity_email(live_cfg, high-severity event)` →
  `False` (tier safe-dark), and the same config with only the flag forced to `True` → `True`, confirming the flag is the
  single gate holding the tier dark.
- Prior-session log lines re-interpreted, not disputed: the two `[IDENTITY-EMAIL] Sent batched alert for 2 high-severity
  event(s)` lines (`/var/log/devicemonitor.log:3498` 20:25:53, `:4133` 21:22:34) are **not** production dispatches.
  `REPORT-20260929-212316.md` §6 discloses that the deployed `send_identity_email()` was called directly with a synthetic
  sample against a temporary loopback mock and that the message counts the batch given rather than the filtered subset.
  Recorded so a future reader does not mistake them for genuine delivery evidence.
- Not done, deliberately: no installer run (mutating or `--check`), no language acceptance run, no manifest regeneration,
  no source or manifest edit, no config write, no commit, no CI run, no delivery against the configured endpoint. No tool
  failed, so the "stop only if a tool fails twice" condition never applied.
- Report: `.cline-reports/REPORT-20260929-221652.md`.

Unresolved: the endpoint tier is the remaining open decision — `webhook_url` still points at the stopped loopback mock
`http://127.0.0.1:8777/dm-webhook` (nothing bound; `http_code=000`), so the safe-dark reversion removed the failure
symptom but not the underlying gap, and enabling the flag requires a permanent verified receiver first; no high-severity
identity event exists to dispatch in any case (`device_identity_events` holds 2 rows, both `medium`/`MAC_MULTI_IP`).
Interface/VLAN scoping of identity frames stays undecided — if that was the real requirement it is a new feature, since
the identity path has never consulted `webhook_vlans`. The inert `identity_email_enabled` key remains stored in the live
`config.json`; nine stale installed plugin `.po` files remain outside the runtime manifest; `DM-BL-008a` (`nl_NL`) is
unchanged; this ledger entry and its report are uncommitted.

Next recommended step: settle the endpoint tier — point `webhook_url` at a permanent, verified receiver (and then keep
the flag enabled) or leave `identity_webhook_enabled` at `"0"` as the shipped baseline and CI assert — and record the
resulting decision.

Evidence status: the function-execution proof, the `grep` results, the SQLite query, the endpoint probe and the
before/after hashes were produced in this session on the testbed and are reproducible from
`.cline-reports/REPORT-20260929-221652.md`; no external host was contacted and no state was mutated.

## 30 September 2026 — v2.10 production deployment to `45e8c86`

Description: the production firewall `192.168.20.254` was updated to the v2.10 runtime
built from commit `45e8c86` using the guarded `install-unattended.sh`, and the deployed
payload was then re-derived and verified independently. The guard reported
`predecessor=2.10`, so production was already on an earlier v2.10 build and this run
replaced it — it was not a v2.9-to-v2.10 upgrade, and the "Production still runs v2.9"
statement earlier in this file was already inaccurate.

Benefit: production now runs the same v2.10 payload the testbed has been running, and the
deployment is recorded with reproducible hash evidence instead of being left un-logged.

Deployment (installer run on production; the run's log was written 30 September 2026
12:19 +1000):

- `NOTICE: merged the plugin keys into 10 core catalogue(s)` — the DM-BL-008c core
  catalogue merge ran on production.
- `CHECK_OK version=2.10 predecessor=2.10 files=59 core_locales=10 daemon_running=1 host=OPNsense.home.arpa`.
- `INSTALL_OK version=2.10 files=59 core_locales=10 daemon_restarted=1 backup=/var/backups/devicemonitor/install-v210.RulQty`;
  `configd` and the Device Monitor daemon were each restarted once.
- Rollback backup retained on production: `/var/backups/devicemonitor/install-v210.RulQty`
  (confirmed present). `/etc/rc.conf.d/devicemonitor` is `devicemonitor_enable="YES"` and the
  daemon was running (pid 48862) at verification time.

Independent verification (read-only, production, same day):

- Installed digests re-derived on production and compared row by row against
  `release/v2.10-runtime.manifest` as committed at `45e8c86`
  (`sha256 15aa829f0a5be8dc5a31438a2ddfc4cf1aaf7bfbef68cec7f9a77936b0d7f7c3`, 38 rows):
  **38/38 match, 0 mismatch, 0 missing**.
- All 11 sidecar catalogues are present; the two sampled (`cs_CZ`, `en_US`) are byte-identical
  to a fresh `msgfmt` compile of the `45e8c86` sources.
- Installed `defaults.json` reports `2.10` and carries the `identity_webhook` key, consistent
  with the `45e8c86` schema.

Record integrity (reported, not silently resolved):

- A second backup identifier supplied together with this record could not be found in any
  deployment log, in the collected local backup-ID set, or in production's
  `/var/backups/devicemonitor`; only `install-v210.RulQty` is evidenced by the run log and by
  the backup directory, so only that identifier is recorded. The unverifiable identifier is
  deliberately not written into this ledger.
- Tag `v2.10` points at `1315c80`; `45e8c86` is ten commits later. Production is therefore
  running a post-tag development tip, not the tagged release. The tag was **not** moved by
  this record, and moving it was declined; a follow-on release tag for `45e8c86` is the
  pending decision.
- The deployed runtime artifact has `sha256 13ed23e8c2fcd27d9ef18a035e9993065217ee35cb365417ea6b2ff3d06e031a`
  — the `45e8c86` bundle hash — and is not the `28ce829d…` asset hash recorded for the v2.10
  release draft.

Limits: verification was read-only and covered the 38 manifest rows plus two sampled
catalogues; the 10 merged core catalogues were not byte-compared individually, and
authenticated GUI and live notification behaviour on production were not exercised.

Next recommended step: decide how the post-tag commits now running on production are to be
represented as a release (for example a `v2.10.1`-style tag at `45e8c86`) rather than moving
the existing `v2.10` tag, and record that decision in `DECISIONS.md`.


## 30 September 2026 — strict 500px box for both interface-selection lists in Settings

Description: the Email and Webhook "Notify for interfaces" lists are the last two
elements of the notification settings that did not share one geometry — the Email tab
capped its list at `max-width:350px` while the Webhook tab used `max-width:500px`, so the
two tabs drew different-sized boxes for the same control. Both containers in
`src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt` now carry a strict box
declaration, `width: 500px !important; display: block;` (lines 164 and 235), replacing the
per-tab `max-width` values.

Benefit: the Email and Webhook interface lists now draw the same structural box from the
same declaration, so the two tabs are visually uniform instead of one being 350px wide.

Deployment (testbed `OPNsense.internal`, OPNsense 26.7.4_1, installer run 30 September 2026
16:38-16:41 +1000):

- `CHECK_OK version=2.10 predecessor=2.10 files=59 core_locales=10 daemon_running=1 host=OPNsense.internal`
  (`/tmp/dm_check.log`, exit 0).
- `INSTALL_OK version=2.10 files=59 core_locales=10 backup=/var/backups/devicemonitor/install-v210.a889Nj daemon_restarted=1`
  (`/tmp/dm_install.log`, exit 0); `configd` and the Device Monitor daemon were each
  restarted once, and the daemon was running as pid 4008 at verification time.
- Deployed file digest re-derived on the testbed: `aae216858f64bf7f833b8c1669823bc435ba46a7293f3773099de414c34338c9`,
  matching the manifest row for `settings.volt`.

Hash-chain bookkeeping (the installer's guard chain requires all three to move together):

- `release/v2.10-runtime.manifest` line 25 — `settings.volt` digest updated
  `ce2c7715…` -> `aae21685…`; the file remains 38 rows, which `install-unattended.sh:29`
  requires.
- `install-unattended.sh` line 28 — manifest self-digest updated
  `87f3f4db…` -> `412ac809…`, recomputed over the 38-row manifest.
- `tests/test_release_manifest.py` (re-derives every row from the working tree):
  `V210_RELEASE_MANIFEST=PASS`.

Cache hygiene: `/var/lib/php/cache` held 3 compiled Volt templates (including
`_usr_local_opnsense_mvc_app_views_opnsense_devicemonitor_settings.volt.php`) and was
emptied; `/usr/local/opnsense/mvc/app/cache` does not exist on this release, so there was
nothing to flush there. `configctl webgui restart` returned `OK` and the WebUI answered
`200` on `https://127.0.0.1/` afterwards. The compiled template re-appears on the first
authenticated load of the Settings page; it could not be regenerated from this session
because the render path requires a logged-in WebUI session.

Rendered-markup verification (not a browser measurement): `tests/render_device_monitor_page.php`
with `--engine runtime` (real Phalcon Volt compiler plus the production
`OPNsense\Base\ViewTranslator` over the installed `cs_CZ` catalogue) rendered
`settings.volt` and emitted the new declaration twice, once per container, with
`id="email-vlan-list"` and `id="webhook-vlan-list"` both reading
`width: 500px !important; display: block;`.

Broader regression check: `python3 tests/test_language_acceptance.py --engine runtime`
(DM-BL-008, the nine UI languages) returned
`LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0`, exit 0. That harness
renders the *deployed* views by default and cross-checks their digests against the working
tree first, so all ten Device Monitor pages of the installed plugin rendered in the
production Phalcon path in all nine languages with the new container declaration in place.

Limit: the WebUI box was **not** measured in a browser from this session — the testbed
session has no GUI/browser, so the layout claim rests on the rendered CSS plus the strict
`width`/`display` declaration rather than an Inspector readout. With the default
`content-box` sizing, the drawn outer box of each list is 518px wide (500px content plus
1px borders and 8px padding per side); the content box is 500px. If a literal 500px outer
box is required, `box-sizing: border-box` would be needed — that was not requested and was
not changed.

Files changed: `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt`,
`release/v2.10-runtime.manifest`, `install-unattended.sh`. The change is uncommitted;
`git diff --check` is clean.

Next recommended step: review the uncommitted three-file diff and commit it as the
`style/ux` change that makes both interface lists draw the identical 500px box.



## 30 September 2026 — Settings Email/Webhook panes re-scaffolded onto native grid rows

Requested change: replace the bespoke `table.table-striped` scaffolding inside the
**Email Notifications** and **Webhook Notifications** panes of
`src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt` with the native
Bootstrap grid row shape the rest of the form uses, so both panes read like ordinary
OPNsense settings rows instead of a striped table.

Implemented (view only — no PHP, API, schema or translation change):

- Every setting in the two panes is now its own `.row` of `<div class="col-md-3">` (label or
  heading, with that row's `dm-info` guidance button authored beside it) plus
  `<div class="col-md-9">` (input, checkbox, select or list container). The rendered page
  carries 17 rows, 17 `col-md-3` and 17 `col-md-9` columns.
- Rows created — Email: Email Notifications (Enable Email), Email Recipient, Email Sender,
  Email delivery method, SMTP Server, SMTP Port, Encryption, SMTP Username, SMTP Password,
  Test Email action, Infrastructure Services, Notify for interfaces. Webhook: Webhook
  Notifications (Enable Webhook), Webhook URL, Send Test action, Identity conflict alerts,
  Notify for interfaces.
- `#email-vlan-list` and `#webhook-vlan-list` now sit directly inside their `col-md-9`
  column and fill the responsive column like every other control; the earlier
  `width: 500px !important; display: block;` declarations are gone (0 occurrences in the
  rendered page).
- `#email_config`, `#email_smtp_config`, `#webhook_config` and `#service_email_options` remain
  as show/hide wrappers, so the existing `slideDown()/slideUp()/show()/hide()` behaviour is
  unchanged. The custom `max-width:600px` on `#email_smtp_config` was dropped so the SMTP rows
  align with the rows above them.
- JavaScript: the four now-dead guidance-relocation lines (`#tab-webhook > .dm-info`,
  `#email_sendmail_config`, `#email_smtp_config > .dm-info`, the `#smtp_username` button) were
  removed — those buttons are authored in their `col-md-3` label column. The generic
  `table > tbody > tr` loop still serves Monitoring, Nmap Scanning and Plugin Options.
- Message ids are unchanged: 113 used before and after, none added or removed, so no
  catalogue, sidecar or installer locale work was required.

Deployment (testbed `OPNsense.internal`, OPNsense 26.7.4_1, installer run 30 September 2026
16:58–17:00 +1000):

- `CHECK_OK version=2.10 predecessor=2.10 files=59 core_locales=10 daemon_running=1 host=OPNsense.internal`
  (`/tmp/dm_check.log`).
- `INSTALL_OK version=2.10 files=59 core_locales=10 backup=/var/backups/devicemonitor/install-v210.ed0eyk daemon_restarted=1`
  (`/tmp/dm_install.log`); the daemon was running as pid 76013 at verification time.
- Deployed digest `f047b6bce0c45ceb4395884a9870de24d1bf056bcc829b2349116c2a58a667b4` matches the
  manifest row for `settings.volt`.

Hash-chain bookkeeping: `release/v2.10-runtime.manifest` line 25 `settings.volt` digest
`aae21685…` -> `f047b6bc…` (file still 38 rows); `install-unattended.sh` line 28 manifest
self-digest `412ac809…` -> `b642cfe8…`; `tests/test_release_manifest.py`
`V210_RELEASE_MANIFEST=PASS`.

Cache hygiene: `/var/lib/php/cache` emptied of compiled Volt templates (3 -> 0, including
`_usr_local_opnsense_mvc_app_views_opnsense_devicemonitor_settings.volt.php`);
`configctl webgui restart` -> `OK`; `https://127.0.0.1/` -> HTTP `200`.

Validation: `sh -n install-unattended.sh`, `git diff --check`, `tests/test_release_manifest.py`,
`tests/test_device_navigation.js` and `python3 tests/test_language_acceptance.py --engine runtime`
(`LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0`) all PASS.
`settings.volt` also compiled through the real Phalcon Volt compiler (`engine=runtime`, exit 0)
emitting 17 rows / 17 `col-md-3` / 17 `col-md-9`, `table-striped` only in the three remaining
table panes (Monitoring, Nmap Scanning, Plugin Options) and zero `width: 500px !important`.

Limit: no browser/GUI in this session, so the alignment claim rests on the emitted markup and
grid classes rather than an Inspector readout of the laid-out rows.

Files changed: `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt` (+226/-180),
`release/v2.10-runtime.manifest`, `install-unattended.sh`. The change is uncommitted and
`git diff --check` is clean.

Next recommended step: review the uncommitted diff and commit it as the `style/ux` change that
puts the Email and Webhook panes on native grid rows.

## 30 September 2026 — Email Notifications pane spacing refinements

Follow-up to the grid-row re-scaffold: once the Email pane stopped using
`table.table-striped`, its rows lost the table-cell padding that used to separate them, so
Recipient / Sender / Delivery Method ran together and the Infrastructure Services block had no
break before Notify for interfaces.

Implemented in `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt` (spacing only;
no element ids, labels, message ids or behaviour changed):

- `class="row form-group"` added to the Email Recipient (line 60), Email Sender (line 69) and
  Email delivery method (line 78) row containers — Bootstrap 3's standard `margin-bottom:15px`
  form-row spacing, i.e. the theme's own value, so no new CSS was introduced.
- The `Email Notifications` / **Enable Email** heading row (line 47) received the same class so
  the first field no longer touches the master-switch row above it.
- `style="margin-bottom:25px;"` added to the Infrastructure Services row (line 166) — the
  distinct break requested before the Notify for interfaces row. No `<hr>`/`clearfix` was
  introduced: no view in the plugin uses one, and the other tabs separate categories through row
  spacing alone.
- The Direct SMTP sub-rows (Server, Port, Encryption, Username, Password) were left at their
  current spacing: they are hidden unless the SMTP delivery method is selected and were not part
  of the reported layout gap.

Deployment (testbed `OPNsense.internal`, 30 September 2026 18:52–18:56 +1000):

- `CHECK_OK version=2.10 predecessor=2.10 files=59 core_locales=10 daemon_running=1 host=OPNsense.internal`
  (`/tmp/dm_check.log`).
- `INSTALL_OK version=2.10 files=59 core_locales=10 backup=/var/backups/devicemonitor/install-v210.sSgelp daemon_restarted=1`
  (`/tmp/dm_install.log`); daemon running as pid 58567.
- Deployed digest `782b87016fbd1003f4048641689de8f268be77f3ce03838adce50158fe28a6ae` equals the
  manifest row.

Hash chain: `release/v2.10-runtime.manifest` line 25 `f047b6bc…` -> `782b8701…` (still 38 rows);
`install-unattended.sh` line 28 `b642cfe8…` -> `40c2f220…`; `V210_RELEASE_MANIFEST=PASS`.

Cache hygiene: `/var/lib/php/cache` emptied (3 -> 0 compiled Volt templates);
`configctl webgui restart` -> `OK`; `https://127.0.0.1/` -> HTTP `200`.

Validation: `sh -n install-unattended.sh`, `git diff --check`, `tests/test_release_manifest.py`,
`tests/test_device_navigation.js` and `python3 tests/test_language_acceptance.py --engine runtime`
(`LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0`) PASS. The Volt render
(`engine=runtime`, exit 0) emits 4 `row form-group` blocks, 17 rows / 17 `col-md-3` / 17 `col-md-9`,
the `margin-bottom:25px` break in document order between `#service_email_options` and
`#email-vlan-list`, and 0 `width: 500px !important`.

Limit: spacing is verified from the emitted classes and markup, not from a browser measurement.

Files changed: `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt`,
`release/v2.10-runtime.manifest`, `install-unattended.sh`. Uncommitted.

Next recommended step: review the uncommitted diff and commit the grid-row re-scaffold together
with this spacing refinement as one `style/ux` change.

## 30 September 2026 — Test Email action row spacing and redeploy

Last spacing gap on the Email Notifications pane: the row holding the **Test Email** button and
its guidance icon sat flush against the Infrastructure Services row below it.

Implemented in `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt` (line 153):

- `<div class="row">` -> `<div class="row form-group">` on the Test Email action row, so it
  inherits the same standard 15px bottom margin as the Recipient/Sender/Delivery Method rows.
  Nothing else changed — same ids, labels, message ids and JavaScript behaviour; the pane now has
  five `row form-group` rows (lines 47, 60, 69, 78, 153).

Deployment (testbed `OPNsense.internal`, 30 September 2026 19:00–19:03 +1000):

- `CHECK_OK version=2.10 predecessor=2.10 files=59 core_locales=10 daemon_running=1 host=OPNsense.internal` (`/tmp/dm_check.log`).
- `INSTALL_OK version=2.10 files=59 core_locales=10 backup=/var/backups/devicemonitor/install-v210.RCfBNn daemon_restarted=1` (`/tmp/dm_install.log`); daemon running as pid 82146.
- Deployed digest `ebe5068f107dfb8cd0e40cacd6cc428eab8b93817ad98e8b42d7fc3410634069` equals the working-tree source and the manifest row.

Hash chain: `release/v2.10-runtime.manifest` line 25 `782b8701…` -> `ebe5068f…` (still 38 rows);
`install-unattended.sh` line 28 `40c2f220…` -> `db664571…`; `V210_RELEASE_MANIFEST=PASS`.

Cache hygiene: `/var/lib/php/cache` emptied (3 -> 0 compiled Volt templates);
`configctl webgui restart` -> `OK`; `https://127.0.0.1/` -> HTTP `200`.

Validation: `sh -n install-unattended.sh`, `git diff --check`, `tests/test_release_manifest.py`,
`tests/test_device_navigation.js` and `python3 tests/test_language_acceptance.py --engine runtime`
(`LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0`) PASS. The Volt render
(`engine=runtime`, exit 0) emits 5 `row form-group` blocks with the Test Email row before the
`margin-bottom:25px` Infrastructure Services row, 17 rows / 17 `col-md-3` / 17 `col-md-9`, and 0
`width: 500px !important`.

Limit: spacing is verified from the emitted classes and markup, not a browser measurement.

Files changed: `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt`,
`release/v2.10-runtime.manifest`, `install-unattended.sh`. Uncommitted.

Next recommended step: commit the re-scaffold and the two spacing refinements together as one
`style/ux` change.


## 30 September 2026 — Interface list width match and redeploy

The `Notify for interfaces` list boxes on the Email Notifications and Webhook Notifications
panes filled the whole `col-md-9` column, so the bordered box ran past the right edge of the
input fields above it.

Implemented in `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt`:

- `#email-vlan-list` (line 205) and `#webhook-vlan-list` (line 286) gained a `max-width` in
  their existing inline style so each bordered box ends where the field above it ends:
  `max-width:400px;` on the Email pane (matching `#email_to`, `#email_from`, `#email_method`,
  `#smtp_host`, `#smtp_username`, `#smtp_password`) and `max-width:500px;` on the Webhook pane
  (matching `#webhook_url` and its Examples `<details>` box, and the same 500px the HEAD
  commit `34ccabd` used for this list).
- The width was set on the list container instead of inserting an inner wrapper `div`, so the
  `#email-vlan-list` / `#webhook-vlan-list` ids, their `.notif-vlan-cb` children and
  `buildVlanCheckList()` / `getSelectedVlans()` keep the identical DOM path. No other
  attribute, id, label, message id or script changed.

Deployment (testbed `OPNsense.internal`, 30 September 2026 19:42–19:47 +1000):

- `CHECK_OK version=2.10 predecessor=2.10 files=59 core_locales=10 daemon_running=1 host=OPNsense.internal`
  (`/tmp/dm_check.log`).
- `INSTALL_OK version=2.10 files=59 core_locales=10 backup=/var/backups/devicemonitor/install-v210.cCpfPu daemon_restarted=1`
  (`/tmp/dm_install.log`); daemon restarted, now running as pid 5079.
- Deployed digest `a85d4674c091bb82e32addb510bbcaf47af3caefee5695ff0b0297cbf3fb5496` equals the
  working-tree source and the manifest row.

Hash chain: `release/v2.10-runtime.manifest` line 25 `ebe5068f…` -> `a85d4674…` (still 38 rows);
`install-unattended.sh` line 28 `db664571…` -> `ba1d58ec…`; `V210_RELEASE_MANIFEST=PASS`.

Cache hygiene: `/var/lib/php/cache` emptied (3 -> 0 compiled Volt templates);
`configctl webgui restart` -> `OK`; `https://127.0.0.1/` -> HTTP `200`.

Validation: `sh -n install-unattended.sh`, `git diff --check`, `tests/test_release_manifest.py`,
`tests/test_device_navigation.js` (7 checks) and
`python3 tests/test_language_acceptance.py --engine runtime`
(`LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0`; the same test reported
the expected `installed view differs from the source: settings.volt` before the redeploy) PASS.
The Volt render (`engine=runtime`, exit 0) emits both list boxes with their new
`max-width:400px;` / `max-width:500px;` inline styles, 5 `row form-group` blocks, 17
`class="col-md-3"` / 17 `class="col-md-9"` and 0 `width: 500px !important`.

Limit: the widths are verified from the emitted inline styles and the sibling input
`max-width` values, not from a browser measurement.

Files changed: `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt`,
`release/v2.10-runtime.manifest`, `install-unattended.sh`. Uncommitted.

Next recommended step: review the uncommitted diff and commit the grid-row re-scaffold plus the
spacing and width refinements together as one `style/ux` change.


## 30 September 2026 — Full grid re-scaffold of Monitoring, Nmap Scanning and Plugin Options

Alignment sweep completed: the three remaining table panes now use the same native grid rows as the
Email and Webhook panes, and the Webhook pane received the last spacing refinements.

Implemented in `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt`:

- Webhook pane: the Enable Webhook row, the Webhook URL row and the Send Test action row became
  `<div class="row form-group">`; the Identity conflict alerts row became
  `<div class="row" style="margin-bottom:25px;">` — the same break the Email pane already uses on its
  Infrastructure Services row — so the interface list box is separated from the checkbox row above it.
- Monitoring (3 rows), Nmap Scanning (7 rows) and Plugin Options (9 rows) were re-scaffolded from
  `table class="table table-striped"` rows into `<div class="row form-group">` grid pairs:
  headings and `.dm-info` guidance buttons in `col-md-3`, controls (checkbox, number, select,
  text/password input, list box) in `col-md-9`. No striped table remains in any configuration pane.
- The Nmap section heading is a `col-md-12` row and its guidance button is now authored inside the
  `<h4>` instead of being moved there at runtime.
- Plugin Options kept `#adguard_rewrite_config` and `#pihole_config` as show/hide wrappers, with the
  AdGuard URL/Username/Password and Pi-hole URL/App password rows promoted to nested
  `row form-group` col-md-3/col-md-9 pairs; the custom `max-width:600px` was dropped from both
  wrappers for the same reason `#email_smtp_config` lost it earlier (sub-rows must align with the
  rows above them). `#monitored-interface-list` keeps its `max-width:450px`.
- JavaScript: the now-dead `table > tbody > tr` guidance-relocation loop, the `#tab-nmap h4` append
  and the `['adguard_url','pihole_url','pihole_password']` relocation were removed and replaced by a
  comment — all five configuration panes are authored in their final form, so no runtime DOM moves
  are required.
- Message ids, ids, labels and `data-content` strings are unchanged: `keys=450` per page before and
  after, and the language-acceptance counts are identical.

Deployment (testbed `OPNsense.internal`, 30 September 2026 19:53–20:00 +1000):

- `CHECK_OK version=2.10 predecessor=2.10 files=59 core_locales=10 daemon_running=1 host=OPNsense.internal`
  (`/tmp/dm_check.log`).
- `INSTALL_OK version=2.10 files=59 core_locales=10 backup=/var/backups/devicemonitor/install-v210.c18NcX daemon_restarted=1`
  (`/tmp/dm_install.log`); daemon running as pid 51779.
- Deployed digest `cc64ab42483a6a6cd422d78aaa20cd7251878da8d3fdb0145a9c862fb6236ea8` equals the
  working-tree source and the manifest row.

Hash chain: `release/v2.10-runtime.manifest` line 25 `a85d4674…` -> `cc64ab42…` (still 38 rows);
`install-unattended.sh` line 28 `ba1d58ec…` -> `7c9cefa3…`; `V210_RELEASE_MANIFEST=PASS`.

Cache hygiene: `/var/lib/php/cache` emptied (3 -> 0 compiled Volt templates);
`configctl webgui restart` -> `OK`; `https://127.0.0.1/` -> HTTP `200`.

Validation: `sh -n install-unattended.sh`, `git diff --check`, `tests/test_release_manifest.py`,
`tests/test_device_navigation.js` (7 checks), `tests/test_selectpicker_static.js` and
`python3 tests/test_language_acceptance.py --engine runtime`
(`LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0`; before the redeploy the
same run reported only the expected `installed view differs from the source: settings.volt`) PASS.
The Volt render (`engine=runtime`, exit 0) emits, for both the working tree and the deployed file,
27 `row form-group` rows, 35 `col-md-3` / 35 `col-md-9` columns, 0 `table-striped`, 2
`margin-bottom:25px` breaks, 26 `.dm-info` buttons (22 in `col-md-3`; the Email Test action row and
the Nmap section heading keep theirs in `col-md-9` / `col-md-12`) and one `table-condensed` left in
the About pane.

Limit: no browser/GUI in this session, so the alignment claim rests on the emitted grid markup, not
an Inspector readout of the laid-out rows. The About pane was deliberately left as an information
table — it is not one of the five configuration panes.

Files changed: `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt`,
`release/v2.10-runtime.manifest`, `install-unattended.sh`. Uncommitted.

Next recommended step: review the uncommitted diff and commit the grid re-scaffold plus the spacing
and width refinements together as one `style/ux` change.

## 30 September 2026 — Email SMTP sub-panel grid rows and guidance-icon column conformity

Closed the three residual items from the 20:01 report in
`src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt`: the hidden `#email_smtp_config`
rows (SMTP Server, Port, Encryption, Username, Password) are now `row form-group` with labels in
`col-xs-12 col-md-3` and controls in `col-xs-12 col-md-9`; the Email Test Email row and the Nmap
heading row carry their guidance buttons in a `col-xs-12 col-md-3` label column, so the file's last
`col-md-12` row is gone and no `.dm-info` button sits outside a `col-md-3` column. No
`max-width:600px` remained inside the five configuration panes to strip (the About information
wrapper keeps its one, unchanged); the sub-panel's uniform `max-width:400px` / `width:120px` /
`width:180px` control widths were preserved so it matches the main mail rows. No JavaScript changed;
the Test Email heading reuses the existing `Test Email` message id.

Hash chain: `release/v2.10-runtime.manifest` line 25 `cc64ab42…` -> `c631fec9…` (still 38 rows);
`install-unattended.sh` line 28 `7c9cefa3…` -> `ad7f4443…`; `V210_RELEASE_MANIFEST=PASS`.

Deployment (testbed `OPNsense.internal`, 30 September 2026 20:08–20:13 +1000): `CHECK_OK version=2.10
predecessor=2.10 files=59 core_locales=10 daemon_running=1`; `INSTALL_OK version=2.10 files=59
core_locales=10 backup=/var/backups/devicemonitor/install-v210.YHi3be daemon_restarted=1`; daemon
running as pid 80907. `/var/lib/php/cache` emptied (3 -> 0 compiled Volt templates);
`configctl webgui restart` -> `OK`; `https://127.0.0.1/` -> HTTP `200`.

Validation: `sh -n install-unattended.sh`, `git diff --check`, `tests/test_release_manifest.py`,
`tests/test_device_navigation.js` (7 checks), `tests/test_selectpicker_static.js` and
`python3 tests/test_language_acceptance.py --engine runtime` (`LANGUAGE_ACCEPTANCE=PASS languages=9
gaps=1 engine=runtime failures=0`; before the redeploy only the expected `installed view differs from
the source: settings.volt`). The Volt render (`engine=runtime`, exit 0) is byte-identical (54,242 B)
for the working tree and the deployed file: 32 `row form-group`, 7 `col-xs-12 col-md-3`, 6
`col-xs-12 col-md-9`, 37 `col-md-3`, 35 `col-md-9`, 0 `col-md-12`, 0 `table-striped`, 26 `.dm-info`
buttons with 0 outside a `col-md-3` label column; `keys=450` per page before and after.

Limit: no browser/GUI in this session, so the alignment claim rests on the emitted grid markup, not
an Inspector readout. Residual, outside the scoped instruction: the Webhook "Send Test" row keeps an
empty `col-md-3`, the two "Notify for interfaces" list rows remain plain `class="row"`, and
`docs/USER_MANUAL.md` §14 still lists five tabs without Plugin Options.

Files changed: `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt`,
`release/v2.10-runtime.manifest`, `install-unattended.sh`. Uncommitted.

Next recommended step: review the uncommitted diff and commit the grid re-scaffold plus these
Email/Nmap refinements as one `style/ux` change.


## 30 September 2026 — Webhook "Send Test" label column (final alignment pass)

Closed the residual asymmetry recorded at the end of the 20:13 report: the Webhook pane's "Send Test"
action row was the last `row form-group` in
`src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt` whose `col-md-3` label column was
empty. Line 256 `<div class="col-md-3"></div>` now reads `<div class="col-md-3"><strong>Send Test
Webhook</strong></div>` (lines 256-258); the row's `col-md-9` column is untouched, so the
`#test_webhook` button (🧪 `Send Test`) and the `#webhook_test_result` span keep their placement. The
row never had a `.dm-info` button, so no guidance icon moved. The file now holds zero empty
`col-md-3` cells, and the rendered grid is 29 plain `col-md-3` against 29 `col-md-9` columns.

Message-id conflict reported, not silently resolved: `Send Test Webhook` is not an existing message id
in any of the 12 catalogues, so wrapping it in `devicemonitor_t()` would add a page id and fail
`tests/test_language_acceptance.py`, which rejects any page id missing from a language's source
catalogue. The label is therefore literal markup, exactly as instructed, as the existing `Enable
sidecar catalogue translations` heading at line 537 already is; rendered `keys=450` per page is
unchanged, i.e. no message id was added or removed.

Hash chain: `release/v2.10-runtime.manifest` line 25 `c631fec9…` -> `52d0aefa…` (still 38 rows,
self-digest `ad7f4443…` -> `84087b44…`); `install-unattended.sh` line 28 `ad7f4443…` -> `84087b44…`.

Deployment (testbed `OPNsense.internal`, 30 September 2026 20:31-20:34 +1000): `CHECK_OK version=2.10
predecessor=2.10 files=59 core_locales=10 daemon_running=1`; `INSTALL_OK version=2.10 files=59
core_locales=10 backup=/var/backups/devicemonitor/install-v210.I7kIss daemon_restarted=1`;
`/var/lib/php/cache` emptied (3 -> 0 compiled Volt templates, including
`_usr_local_opnsense_mvc_app_views_opnsense_devicemonitor_settings.volt.php`); `configctl webgui
restart` -> `OK`; `https://127.0.0.1/` -> HTTP `200`. Deployed digest `52d0aefa…` = source = manifest
row 25.

Validation: `sh -n install-unattended.sh`, `git diff --check`, `V210_RELEASE_MANIFEST=PASS`,
`DEVICE_NAVIGATION_*=PASS` (7 checks), `DEVICE_SELECTPICKER_STATIC=PASS`, `SIDECAR_CATALOGUE=PASS`,
`LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0`. Volt render
(`engine=runtime`, exit 0, `de_DE`): 54,246 bytes, `<strong>Send Test Webhook</strong>` once, 0 empty
`col-md-3` cells, 26 `.dm-info` buttons; the row renders `<strong>Send Test Webhook</strong>` above
`🧪 Test senden`.

Limit: no browser/Inspector available, so the alignment claim rests on the emitted grid markup.
Residual, outside the scoped instruction: the two "Notify for interfaces" list rows remain plain
`class="row"`, and `docs/USER_MANUAL.md` §14 still lists five tabs without Plugin Options.

Files changed: `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt`,
`release/v2.10-runtime.manifest`, `install-unattended.sh`.

Next recommended step: push `v2.10-development` and read the `ci.yml` run for the new commit.

## 30 September 2026 — v2.10-development published; USER_MANUAL §14 Plugin Options tab documented

`0ba1e6d` (the settings grid layout overhaul) was pushed to `origin/v2.10-development`
(`d9899d1..0ba1e6d`) and CI run `36703847557` (`Device Monitor CI`, push, `ci.yml`) started for it.

Closed the documentation gap carried in the previous three reports. `docs/USER_MANUAL.md` §14
(lines 673-680) now itemises **six** settings tabs — **Monitoring**, **Nmap Scanning**, **Email
Notifications**, **Webhook Notifications**, **Plugin Options**, **About** — and adds one sentence of
functional summary: "The **Plugin Options** tab holds the plugin's own switches: **Plugin
translations (sidecar catalogue)** forces the interface to use the plugin's dedicated translation
file instead of the OPNsense core catalogues." The §14.6 cross-reference in the same section still
sent readers to the About tab for that switch; it now reads `Settings → Plugin Options tab`
(line 787), matching the tab the switch actually lives in (`settings.volt:26-27` nav entry,
`#tab-pluginoptions` pane at line 435).

No manifest or installer change was required and none was invented:
`docs/USER_MANUAL.md` is not a row of `release/v2.10-runtime.manifest` (`grep -c` = 0 — the manifest
carries only deployed runtime files), so manifest line 25 and the `install-unattended.sh` line 28
self-guard digest `84087b44…` both stay as committed in `0ba1e6d`.

Deployment re-check (testbed `OPNsense.internal`, 30 September 2026 20:40-20:42 +1000): `CHECK_OK
version=2.10 predecessor=2.10 files=59 core_locales=10 daemon_running=1`; `INSTALL_OK version=2.10
files=59 core_locales=10 backup=/var/backups/devicemonitor/install-v210.8nPeKq daemon_restarted=1`
(exit 0). `git diff --check` PASS.

Files changed: `docs/USER_MANUAL.md` only.

Next recommended step: watch the `ci.yml` run for the documentation commit and treat the change as
final only once it is green.

