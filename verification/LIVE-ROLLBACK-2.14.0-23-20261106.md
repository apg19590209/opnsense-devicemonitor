# Device Monitor 2.14.0 — live successful-install rollback validation on `.23`

**Status: PASS for the authorised §9.3 preparatory reset, test installation, live
successful-install rollback and final 2.14.0 reinstall. This does not validate `FRESH=1`, a
monitoring-enabled run, real `rc.configure_plugins` registration or the live lazy schema
migration. DM-BL-009 remains OPEN.**

## Scope and identity

| Item | Value |
|---|---|
| Host | `OPNsense.internal` / `192.168.20.23` only |
| OPNsense | `26.7.8_2 (amd64)` |
| Branch / HEAD | `integration/dm-bl-009-reconcile-20261105` / `690204bb1d6c402de9a2b41e16f753b37335279f` |
| Candidate | `/root/dm-backups/dm-bl009-candidate-rollback-fix-20261106-083105/dm-v2.14.0-runtime.tar.gz` |
| Candidate identity | 1,725,593 bytes; SHA-256 `5149bfd41e5842a144a9d1280c008511f20f3783932eca9beb1f48fca6173f5f`; 60 members |
| Starting Device Monitor | 2.14.0; monitoring `enabled=0`; no WAL/SHM; daemon/configd healthy |
| Final Device Monitor | 2.14.0; monitoring `enabled=0`; no WAL/SHM; daemon/configd healthy |

The bundle was extracted afresh before the test installation and again before the final
reinstall. The candidate was unchanged throughout. No downgrade was attempted through the
upgrade installer: the preparatory 2.14.0 → 2.13.3 state restoration used the reviewed
`prune-plan.sh` helper and the retained installer backup.

## Recovery point and preconditions

Before mutation, `/root/dm-pre-2140` and
`/var/backups/devicemonitor/install-v214.JeYC44` were verified:

* `dm-pre-2140/runtime-data.tgz` is 7,632,213 bytes with SHA-256
  `ff7873ce0fbc1826663aa86c3271014c9c2ad3cdb3bd7b4eacce164a4a63753e`; its manifest,
  61 payload files, 19 core-locale files, record, database and configuration verified.
* `JeYC44/plan` has 63 rows: 61 predecessor copies match their recorded old digests exactly and
  two rows record an originally absent target. Its record backup is
  `0afb4e4e68edd331f22c88ef559dd1163af0baaaba0cd77a76b3ed672c17dea7`; its core-locale
  snapshot has 19 entries.
* Current installed 2.14.0 targets: 63/63 matched the plan and record by digest, mode and
  `root:wheel` ownership.
* A new recovery point was created at
  `/root/dm-validation-2140/rollback/20261105T231610Z`, mode `0700`, `root:wheel`. It contains a
  consistent SQLite backup, config.json, record, `/conf/config.xml`, 19 core-locale files, copies
  of `JeYC44`, both bundles, the candidate helper and a verified `SHA256SUMS` manifest
  (manifest SHA-256 `fcf9822c51cb50a8579827bc6c124acf5b60925e039d571071b70447fc18a49e`).

The SQLite backup's physical file hash is `796d28c7b8c5fd0b8442f74a4bca843b518d9e5b2a8db9f3fe7e5f0860d11f3d`,
not the live file hash `c17874a7…`. Its logical `.dump` hash,
`d7ed7f816c414387bf136d2782ac6c2e1e3e6c08e8c302ae924726d77adb2479`, is identical to the
live database. The backup integrity check is `ok`. A physical-hash assertion against the live
database would be incorrect; no such assertion was used as acceptance.

## Preparatory reset to 2.13.3

The old daemon PID `79168` was stopped and observed to exit before restoration. The reviewed
`prune-plan.sh` from the fresh 2.14.0 extraction restored the `JeYC44` plan, core-locale state
and record. The menu cache was invalidated, configd was restarted and the daemon was started:

```text
ROLLBACK_SUMMARY=restored=31 skipped=32 conflicts=0 failed=0
CORE_LOCALE_ROLLBACK_SUMMARY=restored=19 removed=0 conflicts=0 failed=0
RECORD_RESTORED=/var/db/devicemonitor/installed-manifest.txt
daemon 79168 -> 5602
configd 35685 -> 84886
```

Independent verification found Device Monitor `2.13.3`, 61 target files matching
`/root/dm-pre-2140/payload-state.txt`, the original 61-row record, 19 matching core-locale
files with metadata, unchanged database/configuration hashes, SQLite `ok`, monitoring disabled
and a healthy running daemon/configd.

## Test installation

The 2.13.3 non-mutating check reported 61 targets with zero prunes/retained files. The 2.14.0
check then reported:

```text
CHECK_OK version=2.14.0 predecessor=2.13.3 files=63 core_locales=10 prunable=0 daemon_running=1 host=OPNsense.internal legacy_prunable=0 retained=0
```

The normal upgrade completed:

```text
INSTALL_OK version=2.14.0 files=63 core_locales=10 pruned=0 backup=/var/backups/devicemonitor/install-v214.zGJRuq daemon_restarted=1 unchanged=32 repaired=0
```

The resulting installation was independently verified: 63 targets and 63-row record, all plan
digests/modes/ownership, 19 core-locale files, unchanged database/configuration, SQLite `ok`,
monitoring `enabled=0`, no WAL/SHM, daemon PID `92938`, configd PID `47387` and
`configctl devicemonitor status` = `running`. The `zGJRuq` backup contains 63 plan rows, 61
verified predecessor copies, two absent-target rows, 19 core-locale entries and the record
backup.

## Live successful-install rollback under test

The test installation was stopped and waited on, then restored from `zGJRuq` with the verified
2.14.0 helper. The manual helper reported:

```text
ROLLBACK_SUMMARY=restored=31 skipped=32 conflicts=0 failed=0
CORE_LOCALE_ROLLBACK_SUMMARY=restored=19 removed=0 conflicts=0 failed=0
RECORD_RESTORED=/var/db/devicemonitor/installed-manifest.txt
```

This helper does not emit `ROLLBACK_STATUS`; no such output was fabricated or claimed.
Independent acceptance established:

* Device Monitor `2.13.3` and 61/61 restored targets matched the record;
* record SHA-256 `0afb4e4e68edd331f22c88ef559dd1163af0baaaba0cd77a76b3ed672c17dea7`;
* database `c17874a717cebe2c2e1dbaf537fd13a65b4ded47e10dfcce1849f2088136144e` and
  Device Monitor configuration `027594eb735cf35e4b617163106031971567d0ba74027783e42cae46d37fd47d`
  unchanged;
* 19 core-locale files restored with the expected contents, modes and ownership;
* the two 2.14-only targets, `notify_identity_mail.php` and `verify-devicemonitor.sh`, absent;
* SQLite quick/integrity `ok`, monitoring disabled, no WAL/SHM;
* daemon PID `92938` → `49278`, configd PID `47387` → `30312`, both healthy.

## Final reinstall and acceptance

The unchanged candidate was freshly extracted again and installed through the normal upgrade
path:

```text
INSTALL_OK version=2.14.0 files=63 core_locales=10 pruned=0 backup=/var/backups/devicemonitor/install-v214.qMPS7n daemon_restarted=1 unchanged=32 repaired=0
```

Final independent acceptance:

* 63/63 targets matched the `qMPS7n` plan and 63-row record by digest, mode and `root:wheel`;
* record `d891ce68c9035b3bcd2384d6f3705d6c8d9bc20fb5ef13cc9ca80b2ae1c035a2`;
* database `c17874a717cebe2c2e1dbaf537fd13a65b4ded47e10dfcce1849f2088136144e` and Device Monitor
  configuration `027594eb735cf35e4b617163106031971567d0ba74027783e42cae46d37fd47d` unchanged;
* OPNsense `/conf/config.xml` remained `c2ce5800c76fcf8470283d6ada559fd6c2eba5a8e0372b409cc046afd8307abf`;
* SQLite quick/integrity `ok`; monitoring `enabled=0`; zero monitored interfaces; no WAL/SHM;
* daemon PID `49278` → `74577`, configd PID `30312` → `32439`; daemon alive after five seconds;
* `configctl devicemonitor status` = `running`; `qMPS7n` has 63 plan rows, 61 predecessor copies,
  two absent-target rows and 19 core-locale entries.

## Evidence and preserved assets

Transcript directory: `/root/dm-validation-2140/live-rollback-20261105T231701Z/`

```text
SHA256SUMS SHA-256 = 5cc19b38d4b8a294ef83f8ddfdf86db0622a652c943c4f83a48bdaa258f79fe3
```

The directory contains the pre-state, both non-mutating checks, preparatory-reset and
rollback-test scripts and logs, both installation logs, the post-install check, final acceptance
and a summary. The checksum manifest verified all 14 files.

Preserved backups: `/root/dm-pre-2140`,
`/var/backups/devicemonitor/install-v214.JeYC44` (original deployment and preparatory reset),
`/var/backups/devicemonitor/install-v214.zGJRuq` (test installation, rolled back) and
`/var/backups/devicemonitor/install-v214.qMPS7n` (final accepted installation). The pre-mutation
recovery point remains at `/root/dm-validation-2140/rollback/20261105T231610Z`.

## Remaining gaps

* Live `FRESH=1` on a real OPNsense host remains untested and must not be selected on `.23`.
* Real `rc.configure_plugins` menu/ACL/plugin registration remains unproven by the jail stub.
* Monitoring-enabled behaviour was outside this rollback run. A later bounded §9.4 run completed
  two scheduled inventory scans, direct DMTEST-only service discovery, scope-limited probing and
  two direct loopback helper SMTP deliveries. Reminder, ageing, identity-email, HA/CARP and full
  notification/lifecycle behaviour remain unestablished.
* The live lazy `notified_at` migration was outside this rollback run. It was later observed
  present during the bounded §9.4 exercise and absent after restoration, without instrumenting
  the exact daemon trigger.
* Browser Network/console/cache evidence for About/Features remains unsupplied; the visual PASS
  rests only on the operator-provided screenshot.
* DM-BL-009 remains **OPEN**.

## Recovery/rollback of this validation record

Documentation backups are in `/root/dm-backups/live-rollback-docs-20261106-102301/`, with a
verified `SHA256SUMS`. The live package changes are not reverted by restoring those documents.
To return the live node to the 2.14.0 state captured before this validation, use the verified
`/root/dm-validation-2140/rollback/20261105T231610Z` recovery point and the documented
recovery decision; do not restore `/conf/config.xml` as part of a Device Monitor package rollback.
