# O4 human acceptance run-book — GUI translation domain (Settings → About)

Manual browser procedure that closes the only remaining condition of `O4` (view call-site migration
to the sidecar translator) and, with it, the browser-facing part of `O3`/`DM-BL-008c`.

Scope: the OPNsense testbed `192.168.20.23` (`OPNsense.internal`, OPNsense 26.7.4) only. Out of
scope and forbidden: production `192.168.20.254`, enabling Device Monitor monitoring or scanning
(`re0` sits on the live `192.168.20.0/24` LAN), editing `/usr/local/share/locale`, and attempting
Selenium/WebDriver automation (unavailable in this environment).

## 1. What is being asserted

The nine Device Monitor views call `devicemonitor_t()`, which resolves in this order:

1. the plugin's own sidecar catalogue
   `/usr/local/opnsense/mvc/app/languages/<locale>/LC_MESSAGES/devicemonitor.mo`;
2. the core OPNsense catalogue `/usr/local/share/locale/<locale>/LC_MESSAGES/OPNsense.mo`;
3. the message id itself (English).

`Settings → About` exposes the switch for step 1 (`sidecar_translation_enabled`, checkbox
`#sidecar_translation_enabled`). Checked = step 1 first; unchecked = stock behaviour, step 2 first.

## 2. Preconditions (verify, do not change)

```sh
# on the testbed host
sh install-unattended.sh --host OPNsense.internal --check   # CHECK_OK version=2.10 files=49
ls /usr/local/etc/inc/devicemonitor_locale.inc              # binder present
ls /usr/local/opnsense/mvc/app/languages/fr_FR/LC_MESSAGES/devicemonitor.mo
python3 -c 'import json;print(json.load(open("/var/db/devicemonitor/config.json"))["enabled"])'  # 0
```

`enabled` must be `0` and must stay `0`: this testbed must not scan. The checkbox in the GUI is the
only field this run-book changes.

## 3. Expected values (captured from the deployed system, not invented)

| Message id | fr_FR, sidecar ON | fr_FR, sidecar OFF | it_IT, sidecar ON | it_IT, sidecar OFF |
| --- | --- | --- | --- | --- |
| `Language` (heading) | `Langue` | `Langue` | `Lingua` | `Lingua` |
| `Plugin translations (sidecar catalogue)` (checkbox label) | `Traductions du plugin (catalogue sidecar)` | `Plugin translations (sidecar catalogue)` | `Traduzioni del plugin (catalogo sidecar)` | `Plugin translations (sidecar catalogue)` |
| Help text under the checkbox | French, starts `Traduit les chaînes de Device Monitor depuis le catalogue sidecar du plugin.` | English, starts `Translate Device Monitor strings from the plugin sidecar catalogue…` | Italian, starts `Traduce le stringhe di Device Monitor dal catalogo sidecar del plugin.` | English |
| `Total Devices` (Devices page) | `Total des appareils` | `Total des appareils` | `Dispositivi totali` | `Dispositivi totali` |

**The checkbox label and the help text are the discriminators.** Do not use the heading
`Language`/`Langue` or `Total Devices`: the core catalogue also translates those, so they read the
same in both states.

## 4. Procedure

Record every screenshot as `runbook-<step>-<locale>-<state>.png` and save the page source for the
two About-tab captures.

0. **Baseline.** As the testbed administrator, confirm the current GUI language is English:
   `System → Settings → General → Language` shows English (`en_US`). Note the time.
1. **Authenticate from the external workstation.** Browse to `https://192.168.20.23`, accept the
   self-signed certificate, log in with the administrator credentials (not recorded here). Capture
   `runbook-00-login.png`.
2. **Reach the plugin.** `Services → Device Monitor → Settings`, or go directly to
   `https://192.168.20.23/ui/devicemonitor/index/settings`. Open the fifth tab, **About**
   (`#tab-about`). Confirm the **Language** block: heading, checkbox
   `Plugin translations (sidecar catalogue)` (checked by default), help text, and the tab's own
   **Apply** button (`#btn-apply-about`). Capture `runbook-01-about-en_US.png` plus page source.
3. **Switch the GUI to French.** `System → Settings → General → Language` → `French (fr_FR)` →
   **Save**. Wait for the GUI to reload.
4. **Sidecar ON — assert precedence.** Return to `Services → Device Monitor → Settings → About`. The
   checkbox must still be checked and the label must now read
   `Traductions du plugin (catalogue sidecar)` with the French help text. Capture
   `runbook-02-about-fr_FR-on.png` plus page source. Also open `Services → Device Monitor → Devices`
   and confirm `Total des appareils`. **This is the O4 assertion: plugin strings resolve through the
   plugin's own catalogue.**
5. **Sidecar OFF — assert core fallback.** On `About`, uncheck the checkbox and click **Apply**.
   Reload the page. Expected: the checkbox stays unchecked and the label falls back to the English
   message id `Plugin translations (sidecar catalogue)` with the English help text, while
   `Total des appareils` and the rest of the page stay French (those come from the core catalogue).
   Capture `runbook-03-about-fr_FR-off.png` plus page source.
6. **Repeat for Italian.** `System → Settings → General → Language` → `Italian (it_IT)` → **Save**.
   `About`: switch ON → `Traduzioni del plugin (catalogo sidecar)`, `Lingua`, Italian help text
   (`runbook-04-about-it_IT-on.png`); switch OFF → the label returns to the English message id
   (`runbook-05-about-it_IT-off.png`).
7. **Teardown.** Switch the checkbox back ON and click **Apply**. Set
   `System → Settings → General → Language` back to `English (en_US)` and **Save**. Confirm
   `<language>en_US</language>` in `/conf/config.xml` and that no other configuration changed
   (`System → Configuration → History` shows only these two changes).
8. **Record the result** in `PROJECT_STATE.md` (see *Evidence*), or state plainly which assertion
   failed.

## 5. Evidence that closes `O4`

Attach, do not merely describe: the six screenshots; the About-tab page source for the ON and OFF
states (so the rendered label and the checkbox state are both provable); browser name/version and the
workstation's address class (never credentials); run timestamps; the `<language>` value before and
after; and the `sidecar_translation_enabled` value read from
`/var/db/devicemonitor/config.json` while each state was on screen. With those, `O4` moves from
CODE-COMPLETE to RESOLVED and the `O3` browser-facing condition is discharged.

Pass criteria: steps 4 and 6 show the localized label with the checkbox checked; steps 5 and 6 show
the English message id with it unchecked; step 7 restores `en_US` and the checkbox to checked.

## 6. Troubleshooting

| Symptom | Check |
| --- | --- |
| Label is English with the checkbox checked | `ls -l /usr/local/opnsense/mvc/app/languages/fr_FR/LC_MESSAGES/devicemonitor.mo`; `python3 -c 'import json;print(json.load(open("/var/db/devicemonitor/config.json")).get("sidecar_translation_enabled","<absent = enabled>"))'` |
| Page returns 500 or blank | `php -l /usr/local/etc/inc/devicemonitor_locale.inc` and that the file exists: the views call a global function the binder defines |
| Label stays English with the checkbox unchecked | expected for a plugin-only string: the core catalogue has no entry, so the message id is correct behaviour |
| Checkbox does not persist | confirm **Apply** was clicked; the About tab has its own button (`#btn-apply-about`), added for this procedure |
| Only some strings localize | compare catalogue and view: `msgfmt --check --check-format` on the source `.po`, then `python3 tests/test_language_acceptance.py --engine interpolate` |

## 7. Cross-references

- `PROJECT_STATE.md` — the 28 September 2026 deployment and the O3/O4 records.
- `PRODUCT_BACKLOG.md` — `O4` (CODE-COMPLETE; this run-book is its remaining condition), `O3`
  (installer layout, RESOLVED), `DM-BL-008a` (`nl_NL` is not offered by
  `System → Settings → General → Language`, so Dutch is outside this procedure).
- `tests/test_sidecar_catalogue.py` + `tests/sidecar_translate_probe.php` — the automated
  equivalent of steps 4-5: same precedence, fallback, toggle and escaping, asserted without a
  browser and part of the CI `validate` job.

