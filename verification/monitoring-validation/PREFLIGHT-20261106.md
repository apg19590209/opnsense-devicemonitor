# §9.4 execution preflight — 6 November 2026

**Final status: OPERATOR ACCEPTED; ONE BOUNDED EXERCISE COMPLETED; `ACCEPTANCE=PASS`.** The
operator accepted `15ce9e6cde3798faa63e5ef3f48ada4c63ccd09e81d8e9d22b599360023831b4` as the
`/conf/config.xml` baseline and authorised one §9.4 exercise. The pre-acceptance NO-GO checkpoint
below is retained as history. The executed evidence, wrapper corrections, restoration caveats,
backups and rollback guidance are recorded in
`verification/monitoring-validation/EXECUTION-20261106.md`. No further monitoring run is
authorised; §9.4 is paused after the single run. No commit, push, deployment, release/tag change,
GitHub reply or production access occurred.

## Initial preflight result (superseded)

**Initial result: BLOCKED — NOT EXECUTED.** The observations below are retained as the original
blocked checkpoint. The host subsequently became quiescent and the live configuration advanced to
the resumed baseline recorded later in this document.

## Environment

| Item | Value |
|---|---|
| Host | `OPNsense.internal` / `192.168.20.23` |
| OPNsense | `26.7.8_2`; FreeBSD `15.1-RELEASE-p6` |
| Branch / HEAD | `integration/dm-bl-009-reconcile-20261105` / `690204bb1d6c` |
| Price gate | `peak=true premium window active`; no bypass used |
| Worktree | 10 pending entries preserved; no live state changed |

## Checks performed (read-only)

| Check | Result |
|---|---|
| Interface | `re0=192.168.20.23`; `vlan0.50` description `DMTEST (opt1)`, `192.168.50.1/24` |
| OPNsense `opt1` | enabled, `vlan0.50`, `192.168.50.1/24`, description `DMTEST`; zero `carp` nodes |
| Device Monitor | `2.14.0`; `configctl devicemonitor status` = `running`; daemon PID `74577` |
| Monitoring | `enabled=0`; `monitored_interfaces=""` |
| Database | SHA-256 `c17874a7…`; `integrity_check=ok`; `quick_check=ok`; `journal_mode=delete`; no WAL/SHM |
| Device Monitor config | SHA-256 `027594eb…` |
| Record | SHA-256 `d891ce68…`; two header lines and 63 digest rows |
| Counts | 26 devices; 60 services; 2 identity events; 96 activity events |
| DMTEST | 3 device rows (`192.168.50.1` active + historical, `.50.180` historical); 5 service rows on `192.168.50.1` |
| Core locale | exactly 19 files |
| Disk | approximately 2.6 GiB available on `/` |
| Port discovery | one enabled target `18:60:24:6a:64:8c`, `next_scan_at=2026-11-07 15:55:31`; no target due |
| SMTP listener | nothing bound to `127.0.0.1:2525` |

## Initial blocking finding (superseded)

The accepted `/conf/config.xml` hash is
`c2ce5800c76fcf8470283d6ada559fd6c2eba5a8e0372b409cc046afd8307abf`. The live file was
`80b5fb9de58404a9969c66a2621d5eddd95c3786fd3078b10a05313f54ac3f94` with mtime
`2026-11-06T12:40:38Z`. The XML diff against the accepted revision contained only:

* `/opnsense/revision/time`;
* `/opnsense/system/backup/git/dest_type` (`<absent>` → `remote`);
* `/opnsense/system/backup/git/force_push` (`0` → `1`).

The host recorded Git Backup configuration revisions at 12:30 and 12:40 during preflight. No Device
Monitor, interface or CARP value differed. The drift still means the recorded accepted starting
state was not stable, so the execution gate stopped before mutation. The operator must let the host
become quiescent and either restore the accepted configuration or explicitly accept the new
baseline. Do not edit `/conf/config.xml` merely to force a hash match.

## Wrapper readiness correction

`verification/monitoring-validation/guard.py` previously required the installer backup to be a
regular file, but the documented recovery asset
`/var/backups/devicemonitor/install-v214.qMPS7n` is a directory. `create_backup()` now accepts a
file or a non-empty directory, archives the directory recursively, verifies the archive is readable
and non-empty, and rejects a missing or empty backup. Two mock cases cover directory archiving and
empty-directory refusal.

Validation:

* `python3 -m py_compile verification/monitoring-validation/guard.py verification/monitoring-validation/test_guard.py` — PASS.
* `python3 verification/monitoring-validation/test_guard.py` — 25 tests, `OK` at this checkpoint;
  after the final wrapper corrections the retained suite is 28 tests, `OK`.
* `.codex/hooks/session_start.py` direct check — branch warning absent; peak-price warning present.
* `git diff --check` — PASS.

Those suite counts are historical checkpoints. After the later physical-database-identity
correction the mock/disposable-copy suite is 35 tests, all passing. Those regressions were run
locally and did not constitute or authorise a new live monitoring run.

## Initial remaining readiness steps (superseded)

1. Stop the concurrent Git Backup/configuration activity and confirm `/conf/config.xml` is stable.
2. Resolve the accepted-baseline drift or obtain explicit operator acceptance of the new baseline.
3. Re-run the complete §9.4.2 preflight, including the due-target check.
4. Assemble `$BASE/execute-s94.sh` from the reviewed §9.4.4–§9.4.9 steps only after `$BASE` exists.
5. Run `sh -n` and `scope-check`, verify recovery assets, then arm the watchdog with `begin`.

## Resumed preflight — 6 November 2026 (08:05–08:08 UTC)

The canonical checkout remains on `integration/dm-bl-009-reconcile-20261105` at
`690204bb1d6c402de9a2b41e16f753b37335279f`, with all 12 pending entries preserved (7 modified,
5 untracked) and zero staged. The previous 10-entry count in the initial environment table is
historical. The price gate was checked before this resume and reported
`peak=true premium window active`; no bypass, `--force` or gate modification was used.

### Git Backup quiescence

The concurrent Git Backup work is finished for this baseline. The checkpoint sampled
`/conf/config.xml` five times over 60 seconds with no byte change, found no active Git or backup
process, and observed no further configuration write after the file's final modification. The
Git Backup source checkout is clean at commit
`484d4e70a141a9a3376188cf14dcc6cfef1ce971` (`2026-11-06 18:24:03 +1100`). A final read-only
recheck at 08:08 UTC found no active Git or backup process and the same configuration mtime.

### Proposed baseline

| Item | Value |
|---|---|
| Proposed `/conf/config.xml` SHA-256 | `15ce9e6cde3798faa63e5ef3f48ada4c63ccd09e81d8e9d22b599360023831b4` |
| Size / mode | `67,111` bytes / `0640` |
| Last modification | `2026-11-06 18:28:41 AEDT` (`2026-11-06T07:28:41Z`) |
| Previously accepted baseline | `c2ce5800c76fcf8470283d6ada559fd6c2eba5a8e0372b409cc046afd8307abf` from `/root/dm-validation-2140/rollback/20261105T231610Z/config.xml` |

The semantic diff against the accepted baseline is limited to four leaves:

```text
/opnsense/revision/description
  OLD '/diag_backup.php made changes'
  NEW '/api/gitbackup/settings/set made changes'
/opnsense/revision/time
  OLD '1793919354.32'
  NEW '1793950121.16'
/opnsense/system/backup/git/dest_type
  OLD <absent>
  NEW 'local'
/opnsense/system/backup/git/enabled
  OLD '0'
  NEW '1'
```

No Device Monitor, interface, CARP or other configuration value differed. The Git Backup
`force_push` value remains `0`; the earlier `80b5fb9d…` configuration state, including its `remote`
and `force_push=1` values, has been superseded by later Git Backup work and is not the current
baseline. The four leaves are consistent with enabling local Git Backup configuration, not with a
Device Monitor change or an unexplained configuration edit.

### Current prerequisites

| Check | Result |
|---|---|
| Host | `OPNsense.internal` |
| OPNsense / kernel | `26.7.8_2` / FreeBSD `15.1-RELEASE-p6`, amd64 |
| WAN/LAN | `re0=192.168.20.23/24` |
| DMTEST | `opt1`, `vlan0.50`, description `DMTEST`, `192.168.50.1/24` |
| CARP interfaces | none |
| Monitoring | `enabled=0`; `monitored_interfaces=""` |
| Device Monitor config | SHA-256 `027594eb735cf35e4b617163106031971567d0ba74027783e42cae46d37fd47d` |
| Database | SHA-256 `c17874a717cebe2c2e1dbaf537fd13a65b4ded47e10dfcce1849f2088136144e`; `integrity_check=ok`; `quick_check=ok`; `journal_mode=delete`; no WAL/SHM |
| Install record | SHA-256 `d891ce68c9035b3bcd2384d6f3705d6c8d9bc20fb5ef13cc9ca80b2ae1c035a2`; 2 header lines and 63 digest rows |
| Counts | 26 devices; 60 services; 2 identity events; 96 activity events |
| DMTEST data | 3 device rows (`192.168.50.1` active plus historical, `.50.180` historical); 5 service rows on `192.168.50.1` |
| Core locale | 19 files |
| Disk | `2,100,628` KiB available on `/` |
| Device Monitor service | `configctl devicemonitor status` = `running`; PID `74577` |
| configd service | running; PID `32439` |
| SMTP listener | nothing bound to `127.0.0.1:2525` |
| Port-discovery due state | `due_targets=0` at 08:08 UTC |
| Enabled port-discovery target | one: `18:60:24:6a:64:8c`, `next_scan_at=2026-11-07 15:55:31` UTC |
| Guard preflight | `PREFLIGHT=PASS` in the completed checkpoint |
| Empty-config target listing | expected exit `2`, `ERROR: No monitored interfaces selected` |

The enabled target is not currently due. It becomes a hard blocker at
`2026-11-07 15:55:31Z`; it must not be disabled or rescheduled merely to make a later preflight
pass. `execute-s94.sh` was not assembled, the watchdog was not armed, and no monitoring or execution
wrapper state was changed.

## Operator acceptance and execution result

The operator accepted the baseline and authorised one bounded exercise. The final live run used
the reviewed wrapper at
`/root/dm-validation-2140/monitoring/20261106T083522Z/`; it completed exactly two scans
(`3497 → 3499`), used only `opt1`/DMTEST/`192.168.50.0/24`, captured two loopback SMTP messages, and
restored with monitoring disabled. The supervised status check initially failed on a transient
configd socket; the idempotent recovery passed, and the wrapper now retries that check within a
bounded window. The SMTP acceptance parser was corrected for angle-bracketed addresses and
`SIZE=` parameters. The then-current 28-test guard suite and the read-only acceptance pass.

Final live hashes and state are in `EXECUTION-20261106.md`. `/conf/config.xml` and the Device
Monitor configuration and record are byte-identical to the accepted pre-state. The physical
database is `796d28c7…` after consistent-snapshot normalisation; its logical digest is
`10460718…`, with matching row counts and integrity. That physical-byte caveat is recorded rather
than claiming byte identity with the earlier `c17874a7…` observation. The 19 core-locale files are
byte-identical to the guard backup, no WAL/SHM or test listener/process remains, and Device Monitor
and configd are healthy.

At this checkpoint the pre-update record is backed up at
`/root/dm-validation-2140/backups/PREFLIGHT-20261106.md.20261106T080724Z.bak`; source and backup
matched SHA-256 `1272055f2df35c4743691c9b130d9b3937a47faffd401673a1a580b67bdf2036` at mode `0644`.

The guard suite was later expanded from the 28 tests recorded here to 35 mock/disposable-copy
regressions by the physical-identity correction; no additional live monitoring run was performed
for that correction. See `verification/monitoring-validation/EXECUTION-20261106.md`.

§9.4 is **PAUSED after one executed exercise**; no further arming is authorised. DM-BL-009 remains
**OPEN**. Issue #5 remains **OPEN**.
