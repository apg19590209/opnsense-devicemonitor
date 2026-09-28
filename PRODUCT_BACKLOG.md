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

### O4 — Route the Device Monitor GUI through the sidecar text domain

- Status: `OPEN`. Raised 2026-09-28 from the `DM-BL-008c` scope boundary.
- All 376 `lang._()` call sites across the nine `OPNsense/DeviceMonitor/*.volt` views
  still resolve through the core `OPNsense` domain, so the plugin's `devicemonitor`
  sidecar catalogue is bound but unused by the GUI. The only sidecar consumer is the core
  Services page description in `plugins.inc.d/devicemonitor.inc`.
- Closes when: the views call `devicemonitor_t()` (or an equivalent sidecar-bound
  translator) and a browser acceptance pass confirms translated strings render with the
  sidecar toggle both on and off.

## Closed items

### DM-BL-008c — Non-Destructive Sidecar Localisation

- Status: `RESOLVED` 2026-09-28. Scope: the catalogue layout and the binding framework.
  See the *Scope boundary* note below before reading this as a GUI localisation.
- **Structural layout fix (D2).** The shipped catalogues were flat
  (`languages/<locale>_devicemonitor.{po,mo}`), a layout `bindtextdomain` cannot resolve:
  it looks for `<dir>/<locale>/LC_MESSAGES/<domain>.mo`. All 11 locales were migrated to
  `languages/<locale>/LC_MESSAGES/devicemonitor.{po,mo}` on the testbed `192.168.20.23`
  and each `.mo` recompiled from its `.po`. Verified by round-tripping the compiled `.mo`
  through `msgunfmt`: the msgid set is identical to the `.po` (452 translated messages), so
  the recompile changed no content. The `.po` alongside it is inert for gettext; only the
  `.mo` at that level resolves.
- **`devicemonitor_locale.inc` deployment.** New plugin-owned file at
  `/usr/local/etc/inc/devicemonitor_locale.inc` registers a second text domain
  (`devicemonitor`) rooted at `/usr/local/opnsense/mvc/app/languages`. Bound from
  `IndexController::initialize()` after `parent::initialize()`, guarded on `is_file()` so an
  undeployed binder cannot fatal the page, and also from
  `plugins.inc.d/devicemonitor.inc`.
- **Fallback chain.** `devicemonitor_t()` resolves sidecar -> core `OPNsense` -> msgid, and
  short-circuits to stock core behaviour when the `sidecar_translation_enabled` toggle is
  disabled or a key is missing. The toggle defaults to `"1"` in `defaults.json`, is saved by
  `ConfigController::setAction()` only when actually posted, and appears as a checkbox on
  Settings -> About.
- **Non-destructive proof.** All 19 `/usr/local/share/locale/*/LC_MESSAGES/OPNsense.mo`,
  plus `authgui.inc` and `ControllerRoot.php`, retain their exact pre-change sha256.
- **Scope boundary.** This resolution covers the layout fix and the binding framework only.
  No view was migrated: 0 of 376 GUI strings route through the sidecar. The view call-site
  migration is tracked as `O4`. No browser acceptance pass was run; verification was
  `php -l` and per-process gettext resolution.
- Evidence: `verification/locales/deferrals.md`; branch
  `feature/sidecar-catalogue-20260928`.
