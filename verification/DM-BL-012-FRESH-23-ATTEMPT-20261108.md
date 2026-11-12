# DM-BL-012 — real-host fresh-install attempt on `.23` (8 November 2026)

**Status: ABORTED BEFORE REBOOT; HOST RECOVERED; DM-BL-012 REMAINS OPEN.**

This was an expressly authorised attempt to exercise the real-host uninstall and fresh-install
path on `192.168.20.23` only, using the approved 2.14.0 candidate. No source file, release input or
bundle was changed. The attempt did not reach the planned reboot or authenticated UI checks.

## Candidate and starting state

| Item | Value |
|---|---|
| Host | `OPNsense.internal`, `re0 = 192.168.20.23`, OPNsense `26.7.8_2` |
| Candidate | `dm-v2.14.0-runtime.tar.gz` |
| Size / SHA-256 | `1,729,177` bytes / `90afa55dd826c0dc3be8a23902b809baa465e25191dc372dc6cc2ef4e57fc243` |
| Initial Device Monitor | `2.14.0`, daemon running, monitoring disabled |
| Initial OPNsense configuration | `/conf/config.xml` SHA-256 `e86a7058b894a3cea6d63e4edee420885e9dc3d136ad72f054aa9c1f6b5f0e72` |
| Initial Device Monitor configuration / database | `027594eb735cf35e4b617163106031971567d0ba74027783e42cae46d37fd47d` / physical `796d28c7b8c5fd0b8442f74a4bca843b518d9e5b2a8db9f3fe7e5f0860d11f3d` |
| Initial manifest | 63 verified targets, record `d891ce68c9035b3bcd2384d6f3705d6c8d9bc20fb5ef13cc9ca80b2ae1c035a2` |

Recovery was prepared and independently verified before mutation:

* pre-state archive `prestate-files.tar`, SHA-256
  `f147e8b0f60828f8c10860717f8d833206d2b09d434bb457a85303cc3ed1a5f4`;
* consistent database copy `prestate/devices.consistent.db`, SHA-256
  `796d28c7b8c5fd0b8442f74a4bca843b518d9e5b2a8db9f3fe7e5f0860d11f3d`;
* verified console/root access and 1.3 GiB free space;
* the candidate archive was verified byte-for-byte before mutation.

## Uninstall

The supported `uninstall.sh` from the extracted candidate was run once. It removed the Device
Monitor plugin files, translations, data and configuration, restored nine pristine core catalogues,
removed the plugin-created `nl_NL` core catalogue, and left `/conf/config.xml` unchanged. The web
GUI was returned to HTTP `200`.

Two uninstaller defects were confirmed:

1. `uninstall.sh` removes `/tmp/opnsense_menu_cache.xml`, but the active OPNsense cache is
   `/var/lib/php/tmp/opnsense_menu_cache.xml`. The backend plugin is removed, but an already-loaded
   browser can continue to show the Device Monitor menu until the correct cache is regenerated.
   The menu disappeared after cache refresh; it was not a residual plugin registration.
2. `uninstall.sh` calls `service php-fpm restart`; this OPNsense host has no `php-fpm` rc service.
   The command prints an error even though the uninstall has already completed. The current web GUI
   remained reachable (`HTTP 200`) after the documented `configctl webgui restart` path.

The uninstall deliberately retained 44 historical language backup files, the locale binder, the
core-locale backup directory and the runtime log. Those files were preserved in
`evidence/post-uninstall-leftovers/` and `evidence/leftover-language-files.tar` (SHA-256
`500a5a31a34b2edf5413efb7868559a8f6d552fc2de60ca5ce7cf86d940240b9`) before the Device Monitor
language files were removed to establish the clean predecessor required by the fresh-install test.

## Fresh install and registration

The non-mutating check passed:

```text
CHECK_OK version=2.14.0 predecessor=fresh files=64 core_locales=10 prunable=0 daemon_running=0 host=OPNsense.internal legacy_prunable=0 retained=0
```

The real install then returned:

```text
INSTALL_OK version=2.14.0 files=64 core_locales=10 pruned=0 backup=/var/backups/devicemonitor/install-v214.WjAc3q daemon_restarted=0 unchanged=1 repaired=0
```

The install log is `evidence/fresh-install.log` (SHA-256
`ba56ec61613547e8cf743ed1b6d804eab12d175ab8ad77a75589b75429e228d7`). Independent checks before
the recovery established:

* 64 plan rows and 64 record rows, with every target matching digest, mode and `root:wheel`;
* all 11 plugin catalogues and all 10 merged core catalogues recomputed byte-for-byte;
* `devicemonitor_enable="YES"`, the `/etc/rc.d/devicemonitor` symlink, the plugin include,
  configd actions and nine Device Monitor menu-cache entries;
* configd and the daemon were healthy, and `configctl devicemonitor status` reported `running`;
* the initial fresh state created no `config.json` or `devices.db`, matching the jail expectation;
* the installed defaults were version `2.14.0` with monitoring and both delivery channels disabled.

## Abort condition

At `07:37:08` local time, a Device Monitor configuration save created `config.json` with
`enabled=1`, `monitored_interfaces=lan`, `email_enabled=0` and `webhook_enabled=0`. The command
stream of this validation did not issue that save; the OPNsense audit log does not identify the
originating authenticated GUI request. The daemon logged `Monitoring ENABLED` at `07:37:10` and ran
one scheduled scan. That scan performed service discovery against `.252` and `.253` (SSH, HTTP,
HTTPS and NTP probes) as well as `.1` and `.2`; it made no configuration change and sent no email or
webhook. This breached the task's no-monitoring/no-`.252`/`.253` boundary, so forward execution was
stopped before reboot.

At `07:38:06` the daemon was stopped with `configctl devicemonitor stop`. The activation state,
daemon log and a consistent 18-table database snapshot (146 rows, SQLite integrity `ok`) were
preserved under `evidence/unexpected-monitoring/`.

## Recovery and final state

The reviewed recovery procedure restored the accepted pre-test data and configuration. `config.json`
is `027594eb…`, the database is physically `796d28c7…`, the manifest has 63 rows and the daemon is
running with monitoring disabled. `/conf/config.xml` remains `e86a7058…`; SQLite has 21 tables and
both integrity checks report `ok`; no WAL or SHM is present. The web GUI returned HTTP `200`.

The first recovery invocation completed the restore but exited 1 because its post-check compared
JSON string `"0"` with integer `0`. The live files were already correct. The local recovery verifier
was corrected and a read-only live mode was added; `RECOVERY_LIVE_VERIFY=PASS` now covers the
recovered state. The corrected script SHA-256 is
`b7c444b598a61bdefd74302ae6ef8011593a624acf8b45148254d39f3bf06ad3`. No restore was rerun.

The fresh-install backup `/var/backups/devicemonitor/install-v214.WjAc3q` remains preserved for
evidence. No reboot was performed, so reboot persistence was not tested.

## Acceptance result

The fresh-install, manifest, catalogue, registration and service-start portions passed on the real
host. DM-BL-012 is nevertheless still **OPEN** because the test was aborted before reboot and the
monitoring-disabled condition was not sustained. Authenticated UI acceptance was not performed by
the agent; the operator had a browser session open, but no exact per-page observation was recorded
for this attempt.

## Evidence

Root: `/root/dm-validation-2140/dm-bl-012-fresh-20261107T202736Z/`

* `evidence/fresh-install.log`
* `evidence/fresh-before-reboot.txt`
* `evidence/fresh-post-install-before-recovery.txt`
* `evidence/unexpected-monitoring/`
* `evidence/recovery.log`
* `evidence/post-recovery.txt`
* `evidence/final-verification.txt`
* `recovery/RECOVERY.sh`
* `SHA256SUMS`, SHA-256 `bb1acd5df8204332d2b20aa1575fde25a152c129b76a277427ad183c80b76dc6`

## Required next steps

1. Fix the uninstaller's menu-cache path and OPNsense-incompatible `php-fpm` restart before the next
   lifecycle attempt.
2. Repeat the fresh-install/reboot test in a clean isolated VM with no concurrent UI or settings
   writes, requiring monitoring to remain disabled throughout.
3. Record authenticated About/Features and Devices-page evidence after reboot if access is
   available; otherwise use an explicit operator checklist.

No monitoring activation, notification delivery or `.252`/`.253` access is authorised by this
record.

## 12 November 2026 — lifecycle completion and DM-BL-012 closure on `.23`

The operator explicitly superseded the disposable-VM environment gate and authorised uninstall,
reinstall, necessary service actions and one reboot on the existing development host `.23`,
replacing VM snapshots with verified backups and an executable recovery procedure. This is explicit
operator acceptance of the residual risk under the documented closure alternative; it is lifecycle
testing on an existing development host, not validation on a pristine OPNsense installation.

Two repair candidates were exercised:

* `772a6660e0ca5c6b7455e2751b0c404a1f25a4e1aaafc44167525d657eb6d299` (1,731,225 bytes) corrected
  the active menu-cache path and removed the unsupported `php-fpm` restart. Normal uninstall and
  exact-candidate reinstall passed, followed by one reboot. Post-boot checks confirmed 64/64
  targets, unchanged `/conf/config.xml`, `config.json` `027594eb…` and `devices.db` `796d28c7…`,
  SQLite integrity, configd and daemon running, `Monitoring DISABLED` at 19:28:56, no scan or
  notification events, and the corrected menu cache at `/var/lib/php/tmp/opnsense_menu_cache.xml`
  containing all seven Device Monitor entries.
* `3675c7271ad3bbd3a04c325c9f7b03bfea80a19e6ff913c2c3114b78eaa46891` (1,731,225 bytes) additionally
  removes `/usr/local/etc/inc/devicemonitor_locale.inc` and
  `/usr/local/opnsense/service/conf/actions.d/actions_devicemonitor_update.conf`. Live normal
  uninstall exit 0 left zero of the 42 payload targets, no `php-fpm` call, unchanged configuration
  and 4/4 unrelated sentinels. Reinstall exit 0 produced 64/64 targets and restored the preserved
  data hashes; no reboot was required for this payload-neutral uninstaller correction. The latest
  candidate's uninstall and reinstall were directly tested. Reboot persistence is reused from the
  preceding `772a6660…` candidate: the only delta is uninstall cleanup, which cannot affect
  installed payload, rc wiring, daemon start or reboot behaviour.

Operator attestation recorded at `2026-11-12T19:56:51+1100` states that Services → Device Monitor →
Devices and Services → Device Monitor → Settings display correctly. It is an operator attestation,
not a screenshot or agent-observed browser check. No observation timestamp was supplied and none is
inferred; the reboot remains `2026-11-12T19:28:06+1100`. Monitoring-disabled status was verified by
the automated post-boot checks, not separately attested.

**DM-BL-012 is CLOSED on the explicit-operator-acceptance basis above.** The documented acceptance
criterion is real plugin registration and a daemon that survives reboot with no stub claim, or
explicit operator acceptance of the residual risk. Historical monitoring-activation attribution
remains **UNKNOWN**: the 8 November record is an un-attributed settings write and one scan, not a
confirmed automatic-activation defect, and no documented criterion requires its attribution.
Uncertainty alone is therefore not a release blocker; release remains blocked by DM-BL-011 and
DM-BL-013.

Evidence roots: `/root/dm-validation-2140/dm-bl-012-live-23-20261112T191143/` and
`/root/dm-validation-2140/dm-bl-012-residuals-20261112T194900/`.
