# Pull request submission notes — O4 sidecar view migration + O3 catalogue layout

Reusable body for the GitHub pull request. Head `feature/o4-sidecar-views-20260928`
(`fc35626`) → base `v2.10-development`. Totals over the eight development commits:
45 files changed, 1386 insertions(+), 424 deletions(-); the branch adds one further commit
for this file.

Suggested title:

```
feat: route Device Monitor views through the plugin sidecar translator (O4) and resolve the O3 catalogue layout
```

Suggested labels/topics: `translations`, `installer`, `verification`.

## What this changes

1. **O4 — view call-site migration.** All 372 HTML-context translation call sites in the nine
   Device Monitor views now call `devicemonitor_t()` instead of the core view translator
   `$lang->_()`. The 241 `lang.query()` call sites inside inline `<script>` bodies are unchanged,
   because those need the raw value. Every call site's argument text is byte-identical, so no
   message id changed.
2. **O3 — installer catalogue layout.** The eleven catalogues moved from the flat
   `<locale>_devicemonitor.po` layout, which `bindtextdomain()` cannot resolve, to
   `<locale>/LC_MESSAGES/devicemonitor.po`; the installer compiles and installs to the bound path,
   the uninstaller removes both the nested and the legacy flat pair, and CI mirrors the layout.
3. **Sidecar binder shipped as a payload row.** `src/etc/inc/devicemonitor_locale.inc` (new) binds
   the plugin's own `devicemonitor` domain, exposes `devicemonitor_t()` (HTML-escaped exactly like
   `ViewTranslator` with `view_html_safe`) and `devicemonitor_raw()` (raw, for script contexts),
   with the fallback chain sidecar → core `OPNsense` → msgid, plus the
   `sidecar_translation_enabled` toggle (default `1`, Settings → About).
4. **Webhook guard bypass closed.** `ConfigController::sendWebhookAction()` passed `''` when the
   caller omitted `webhook_url`, and the handler only short-circuits on `null`, so the
   "Webhook disabled" guard was skipped and delivery was attempted to an empty URL. Absent, null,
   empty and whitespace-only values are now detected in the controller and normalised again in
   `NotificationHandler::sendWebhook()`; `testWebhookAction()` rejects an empty URL.

## Highlighted items

### `#btn-apply-about` — sidecar toggle persistence

The About tab had no save control while every other Settings tab has one, so the value of the
sidecar toggle could not be saved from the tab it lives on. About now has its own
`#btn-apply-about`, following the same pattern as `#btn-apply-monitoring`, `#btn-apply-nmap`,
`#btn-apply-email` and `#btn-apply-webhook`. It reuses the existing `Apply` message id, so no
catalogue change was needed. The toggle is still written only when the field is posted, and an
unreadable or absent configuration key keeps the sidecar enabled.

### 30-second service-startup polling in `install-unattended.sh`

The installer verified the daemon restart with a single `pgrep` immediately after
`service devicemonitor restart`. On 2026-09-28 that one-shot check failed on a healthy restart
(`ABORT: daemon not running`) and the rollback reverted a complete, correct installation, while the
daemon came up seconds later. The check now polls for up to 30 seconds and only then aborts, with
the timeout named in the message. Observed manually during the same session: the failure mode is a
false negative in the check, not a daemon fault.

### O4 Volt migrations — 372 sites

Nine views converted (`activitytimeline`, `changesummary`, `devicehistory`, `devices`,
`identityevents`, `infrastructureservices`, `physicaldevices`, `scanhistory`, `settings`), verified
by extracting the call arguments before and after and diffing them: identical, 372 before, 372
after, zero `lang._()` call sites remaining. HTML escaping is preserved by construction, because
`devicemonitor_t()` applies `htmlspecialchars(ENT_QUOTES | ENT_HTML401)` with newlines as `&#10;`,
the same encoding `ViewTranslator` uses with `view_html_safe`.

### Precedence and fallback proven without a browser

`tests/test_sidecar_catalogue.py` with `tests/sidecar_translate_probe.php` compiles the real
catalogues into the bound layout, adds a stand-in core domain containing hostile content, and
asserts: sidecar precedence, the core fallback for a locale with no plugin catalogue, the
`sidecar_translation_enabled = "0"` toggle, the msgid fallback, and that the HTML path escapes while
the raw path does not. It also fails if a flat catalogue reappears in the source tree. This is the
automated equivalent of the run-book's browser assertions.

## Commit list

| Commit | Subject |
| --- | --- |
| `43891db` | feat: route Device Monitor views through the sidecar translator (O4) and close the webhook guard bypass |
| `565535d` | feat: resolve the O3 installer catalogue layout so the sidecar translations resolve |
| `9b6b363` | docs: record the O3 installer layout and the O4 view migration |
| `8beda89` | fix: admit the sidecar binder in the installer payload allowlist and target count |
| `9772de9` | docs: record the v2.10 testbed deployment and the cleared O3 deployment lag |
| `993ef62` | test: model sidecar precedence in the language acceptance gate |
| `302f266` | fix: give the About tab its own Apply button and stop aborting on a slow daemon start |
| `fc35626` | docs: add the O4 human acceptance run-book |

Four `feat`/`fix` commits carry the code, and each states the evidence for its claim in its message;
the `docs`/`test` commits carry the records, the gate and the run-book.

## Verification

Local CI-mirroring battery on the testbed checkout: **101/101 PASS** (`php -l` on every PHP source,
`sh -n` on the installer and uninstaller, `python3 -m py_compile`, `msgfmt --check --check-format`
on all eleven catalogues, the node UI suites, the PHP and Python suites, `git diff --check`).

| Gate | Result |
| --- | --- |
| `tests/test_release_manifest.py` | PASS (38 rows, hashes == working tree) |
| `tests/test_translated_javascript.py` | PASS |
| `tests/test_language_acceptance.py --engine interpolate` | PASS — 9 languages, 10 pages, 451 keys, 0 failures |
| `tests/test_language_acceptance.py --engine runtime` | PASS — **9 languages, 10 pages, 451 keys, 0 failures** on the testbed after the DM-BL-008c merge install (`LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0`, exit 0; the gap is `nl_NL` absent from `get_locale_list()`, `DM-BL-008a`). CI runs the same engine as a guarded matrix (`ci.yml:74-105`): `--engine runtime --languages <catalogues present>`, an explicit `SKIPPED` line per absent language, and a stated skip instead of a failure on a runner without the Phalcon Volt compiler or `OPNsense\Base\ViewTranslator`. |
| `tests/test_sidecar_catalogue.py` | PASS — precedence, fallback, toggle, msgid fallback, escaping |
| `install-unattended.sh --host OPNsense.internal --check` | `CHECK_OK version=2.10 predecessor=2.10 files=59 core_locales=10 daemon_running=1 host=OPNsense.internal`; the install itself reported `INSTALL_OK version=2.10 files=59 core_locales=10 backup=/var/backups/devicemonitor/install-v210.O1Tggb daemon_restarted=1` |

Run against the *installed* tree the acceptance gate reports no failures; its remaining warnings name
the legacy shared core catalogue from the 26 September merge as behind the source, which the sidecar
resolves and which `--strict` still treats as fatal.

CI note: `.github/workflows/ci.yml` triggers only on pushes and pull requests targeting the
`v2.5`–`v2.10-development` branches, so pushing this feature branch created no run; opening this pull
request against `v2.10-development` is what executes the same gates in CI.

## Deployment status and rollback

The payload is deployed on the testbed `OPNsense.internal` (OPNsense 26.7.4):
`INSTALL_OK version=2.10 files=49`, backup `/var/backups/devicemonitor/install-v210.0smjpJ`, configd
and the Device Monitor daemon restarted once. All 38 manifest targets verify on disk, all ten views
are identical to source, all eleven catalogues match their sources (456/456 message ids for fr_FR),
the daemon is running, its log records `Monitoring DISABLED`, `"enabled": "0"` is unchanged and no
scan ran. Production `192.168.20.254` was not touched. Rollback: the installer's own plan in the
backup directory, or `git revert` plus a matching re-install, because the payload is
manifest-pinned.

## Not in this pull request

- `O4` closure: human browser confirmation via `verification/O4-HUMAN-ACCEPTANCE-RUNBOOK.md`; the
  automated gate cannot replace it.
- `DM-BL-008a`: Dutch (`nl_NL`) is still absent from `get_locale_list()`; an upstream decision.
- `DM-BL-008c`: **resolved after this submission** by the v2.10 merge engine. The expanded verification
  boundary is now `tests/test_locale_merge.py` (core-first `msgcat --use-first` precedence, input catalogues
  untouched, `--plugin-only` mode for a locale with no core catalogue, fail-closed guard, OUTPUT-overwrite
  refusal) running as the CI step `Validate core catalogue merge (DM-BL-008c)`, plus the installer dry run
  `CHECK_OK version=2.10 predecessor=2.10 files=59 core_locales=10` — **ten core catalogues merged successfully
  and validated** on the testbed checkout alongside the eleven staged plugin catalogues. The nine GUI-selectable
  languages therefore no longer depend on the sidecar alone for the inline-script strings, and both follow-ups
  named here are now complete on the testbed: the installer ran as
  `INSTALL_OK version=2.10 files=59 core_locales=10` (ten core catalogues merged, `nl_NL` served
  plugin-only) and `python3 tests/test_language_acceptance.py --engine runtime` passed for all nine languages with
  exit code 0, while the English-fallback negative check is evidenced by the preserved pre-merge fr_FR core
  catalogue returning the English message id for a plugin key that the merged catalogue translates.

## Reviewer checklist

- [ ] The views call `devicemonitor_t()` and no `lang._(` call site remains.
- [ ] `devicemonitor_locale.inc` escaping matches `ViewTranslator` with `view_html_safe`.
- [ ] The manifest is 38 rows, its hash matches the tree, and the installer pin matches the manifest.
- [ ] The installer path allowlist and counted target total (49 update, 50 fresh).
- [ ] The webhook guard cannot be bypassed with an absent, empty or whitespace-only URL.
- [ ] The parallel locales-verification working-tree changes are not part of this branch.
