# §9.4 bounded monitoring execution — 6 November 2026

**Result: COMPLETE / ACCEPTANCE PASS — further execution is unauthorised; documented caveats remain.** The operator accepted
`/conf/config.xml` SHA-256
`15ce9e6cde3798faa63e5ef3f48ada4c63ccd09e81d8e9d22b599360023831b4` and authorised one bounded
§9.4 exercise on `192.168.20.23`. Exactly one final live run executed. It used the reviewed
detached watchdog, a 900-second hard limit, at most two cycles, the existing DMTEST/opt1 scope and
the loopback SMTP restriction. The later acceptance and independent state checks passed. No
monitoring remains enabled. The exercise was not repeated; fixtures and live observations are
separated below.

## Authorisation and pre-mutation gate

| Item | Result |
|---|---|
| Host | `OPNsense.internal` / `192.168.20.23` only |
| OPNsense / kernel | `26.7.8_2` / FreeBSD `15.1-RELEASE-p6`, amd64 |
| Branch / HEAD | `integration/dm-bl-009-reconcile-20261105` / `690204bb1d6c` |
| Worktree | 12 pending entries preserved; no staging or commit |
| Price gate | `peak=true premium window active`; no bypass or `--force` used |
| Accepted `/conf/config.xml` | `15ce9e6c…831b4`, 67,111 bytes, mode `0640` |
| Git Backup configuration | Preserved; the old `c2ce5800…` baseline was not restored |
| Monitoring before mutation | `enabled=0`, `monitored_interfaces=''` |
| Interface | `re0=192.168.20.23/24`; `opt1=vlan0.50`, DMTEST, `192.168.50.1/24`; no CARP |
| Port discovery | one enabled target `18:60:24:6a:64:8c`, next run `2026-11-07 15:55:31` UTC; none due |
| SMTP listener | none on `127.0.0.1:2525` before execution |
| Database | logical digest `1046071815c73bce54125e46aa40d841c5940d6598b4e26b90c65afeed8a1a9e`; integrity/quick check `ok`; journal mode `delete`; no WAL/SHM |

The execution payload rechecked the accepted OPNsense configuration digest, the due-target count,
and the resolved target line before changing anything. `/conf/config.xml` remained at the accepted
digest throughout. The configuration was not edited to force a preflight pass.

## Live execution

Evidence root:
`/root/dm-validation-2140/monitoring/20261106T083522Z/`.

| Item | Live result |
|---|---|
| Payload | started `2026-11-06T08:36:10Z`; completed `08:37:48Z` |
| Guard | `PREFLIGHT=PASS`; watchdog PID `93647`; deadline `08:50:47Z` |
| Temporary scope | `opt1` / DMTEST / `vlan0.50` / `192.168.50.0/24` |
| Discovery | direct discovery returned the five expected services on `192.168.50.1` only |
| Visibility probes | 253 addresses within the selected `/24`; no out-of-scope destination |
| Monitoring | enabled only for the bounded window; `Monitoring DISABLED` at `19:37:43` local |
| Scans | `BEFORE_SCANS=3497`, `AFTER_SCANS=3499`, `ADDED_SCANS=2` |
| SMTP | loopback-only sink on `127.0.0.1:2525`; two declared helper messages captured |
| Helper results | both `{"result":"sent","transport":"smtp"}` |
| Core-locale | 19 files unchanged and byte-identical to the guard backup |
| Fixtures | copy-only fixture run passed; no fixture result is treated as live state |

The two scans completed successfully in the Device Monitor log. The direct discovery output was:

```text
DNS 192.168.50.1:53/udp
NTP 192.168.50.1:123/udp
SSH 192.168.50.1:22/tcp
WEB_ADMIN 192.168.50.1:80/tcp
WEB_ADMIN 192.168.50.1:443/tcp
```

The SMTP capture contains two envelopes and two `.eml` messages. Envelope values include the
ESMTP `SIZE=` parameter and angle brackets; the acceptance parser now normalises those forms while
still requiring exactly one approved recipient per message. The sink was stopped by the payload
trap before restoration. No outbound SMTP, webhook, AdGuard/Pi-hole, targeted-Nmap or `.252`/`.253`
contact was made by the exercise.

The copy-only fixture result was:

```text
FIXTURE_PASS identity=1 service=1 new_device=1 aged=1 retired=1
NO_FRESH_HOST_REFUSAL_PASS aged=0 retired=0
```

That fixture proves only the tested copy paths. It is not evidence of live reminder delivery,
real OPNsense registration, plugin lifecycle or full CARP/ageing behaviour.

## Evidence classification

| Behaviour | Evidence class | Result |
|---|---|---|
| Two scheduled inventory scans | live | Two cycles completed (`3497 → 3499`); service discovery was logged as not due on both scheduled scans |
| Direct service discovery | live direct command on the host | `scan_network.py --discover-services` returned the five expected services on `192.168.50.1` |
| Visibility probing and scope | live | 253 addresses within `192.168.50.0/24`; no out-of-scope target |
| `notified_at` schema mutation | live, direct-discovery phase | Guard/pre-install snapshot had the column absent; `live-after-discovery.txt` recorded it present after direct discovery at `08:36:24Z`, before monitoring was enabled at `08:36:26Z`; it remained present in `live-after-cycles.txt` and was absent after restoration. The final absence is the restoration result, not the proof of migration. |
| SMTP helper notifications | helper invoked live, captured on loopback | Two direct PHP helper invocations reported `result=sent transport=smtp`; these are not proof of daemon-generated alert delivery |
| SMTP capture acceptance | live loopback capture | Two envelopes/messages accepted from the real capture; parser regression covers angle brackets and ESMTP `SIZE=` |
| Identity/service/new-device/aged/retired fixtures | copy-only fixture | `FIXTURE_PASS identity=1 service=1 new_device=1 aged=1 retired=1`; no live state dependency |
| Fresh-host refusal fixture | copy-only fixture | `NO_FRESH_HOST_REFUSAL_PASS aged=0 retired=0`; not a live fresh-host test |
| Daemon-triggered service discovery | untested | Both scheduled scans reported discovery not due; the observed service discovery was the separate direct command |
| Full reminder/ageing/CARP behaviour | untested | Not reached by the bounded exercise; helpers and copy-only fixtures do not substitute |
| External SMTP/webhook/AdGuard/Pi-hole/targeted Nmap | not exercised | Prohibited by the authorised scope; only the loopback SMTP sink was used |

The `notified_at` observation is an actual live schema mutation before restoration. The saved
`scan_network.py` direct-discovery path calls `init_db()`, which contains the `ALTER TABLE`
migration. The evidence does not separately instrument which caller performed that migration,
but it does establish that the column was live-present after direct discovery and before the
monitoring window, rather than inferring migration from the final absent column.

## Restoration and final state

The first supervised restoration reported `FAIL` because the daemon start was followed by a single
immediate `configctl devicemonitor status` call while configd was transiently unavailable
(`configd socket missing (@/var/run/configd.socket)`). The guard stopped the service and retained
the evidence. The idempotent manual recovery, `guard.py recover`, then passed; `restore.status` is
now `PASS`. The wrapper now retries the status check within a bounded 30-second window and has a
regression test for both recovery and failure.

Final independent read-only state, recorded in `final-readonly-verification.txt`:

```text
CONFIG_SHA=027594eb735cf35e4b617163106031971567d0ba74027783e42cae46d37fd47d
RECORD_SHA=d891ce68c9035b3bcd2384d6f3705d6c8d9bc20fb5ef13cc9ca80b2ae1c035a2
OPNSENSE_CONFIG_SHA=15ce9e6cde3798faa63e5ef3f48ada4c63ccd09e81d8e9d22b599360023831b4
DEVICES_DB_PHYSICAL_SHA=796d28c7b8c5fd0b8442f74a4bca843b518d9e5b2a8db9f3fe7e5f0860d11f3d
DEVICES_DB_LOGICAL=1046071815c73bce54125e46aa40d841c5940d6598b4e26b90c65afeed8a1a9e
SQLITE_INTEGRITY=ok
SQLITE_QUICK_CHECK=ok
SQLITE_JOURNAL_MODE=delete
MONITORING=enabled=0 monitored_interfaces=''
DB_SIDECARS_WAL=False SHM=False
DEVICE_MONITOR_STATUS=running
CONFIGD_STATUS=configd is running as pid 7386.
LISTENER_2525_COUNT=0
DB_COUNT_devices=26
DB_COUNT_device_services=60
DB_COUNT_device_identity_events=2
DB_COUNT_device_activity_events=96
DB_COUNT_port_discovery_targets=3
DB_COUNT_DMTEST_DEVICES=3
DB_COUNT_DMTEST_SERVICES=5
DB_DUE_TARGETS=0
DB_NOTIFIED_AT_PRESENT=False
SINK_OR_SAMPLER_PROCS=0
SCAN_PROCS=0
NMAP_PROCS=0
CORE_LOCALE_COUNTS=EVIDENCE:19,GUARD_BACKUP:19,LIVE:19
CORE_LOCALE_IDENTICAL=True
```

`python3 verification/monitoring-validation/guard.py accept ...` returned `ACCEPTANCE=PASS`.
`acceptance-current.txt` and `final-readonly-verification.txt` are the preserved outputs.

### Physical database hash: transition traced; original bytes not retained

The live-file transition from `c17874a7…` to `796d28c7…` is now attributable at the operation
level. It was not an installer write or a data/schema change. It was the guard's recovery path
copying its own consistent `.backup()` snapshot over the live path after a pre-monitoring setup
failure. The original `c17874a7…` bytes were not retained, so an exact header/page-byte delta
cannot be reconstructed; that limitation remains an **unresolved acceptance discrepancy** for an
unqualified byte-identity claim.

**Saved occurrences and provenance**

* The earliest retained textual occurrence of `c17874a7…` is the 2.13.3 preflight record
  `/root/dm-backups/deploy-2133-record-20261105-183914/.cline-reports/REPORT-20261105-182716.md`
  at `2026-11-05T18:28:06Z`. It records the result of
  `sha256 -q /var/db/devicemonitor/devices.db`; `/root/dm-pre-2133/baseline.env` repeats the
  value at `18:31:12Z`. No retained physical file contains those bytes.
* The earliest retained physical `796d28c7…` file is `/root/dm-pre-2133/devices.db` at
  `2026-11-05T18:31:10Z`. The retained 2.13.3 plan
  `/root/dm-backups/deploy-2133-record-20261105-183914/verification/DEPLOY-2.13.3-23-PLAN.md`
  shows that it was produced by `src.backup(dst)` from the live database, after which the live
  `c17874a7…` hash was recorded. Its `runtime-data.tgz` archive member is the same hash.
* Every later independent SQLite backup inspected has the same physical `796d28c7…` result:
  the 2.14.0 pre-install backup, the 2.14.0 installer backup, the rollback recovery point and
  all three §9.4 guard snapshots. The §9.4 snapshot at `08:28:34Z` was created with
  `sqlite3 … ".backup …"` while the live file was still `c17874a7…`.
* A search of all 21 files named `devices.db` under `/root` found 17 copies at `796d28c7…` and
  none at `c17874a7…`. All 12 `devices.db` members found in the pre-install, rollback,
  §9.4-monitoring and DM-backup archive trees had `796d28c7…`. The original live bytes are
  therefore absent from the retained evidence, not merely misnamed in the first two trees.
  The earlier live file is known from saved checks to have been 258,048 bytes with
  `integrity_check=ok`, `quick_check=ok`, `journal_mode=delete` and no WAL/SHM. Its header
  counters, freelist layout and page map were not captured.

**Logical comparison**

At `08:28:43Z`, both `/root/dm-validation-2140/monitoring/20261106T082834Z/devices.db` and
`live-devices.db.logical.sha256` produced `.dump` digest
`d7ed7f816c414387bf136d2782ac6c2e1e3e6c08e8c302ae924726d77adb2479`. That dump covers the
schema, all table contents, indexes and triggers. At `08:31:33Z`, the guard's
`sqlite_logical_sha()` comparison between the live database and its backup also passed; the
guard state records the distinct `iterdump` digest
`1046071815c73bce54125e46aa40d841c5940d6598b4e26b90c65afeed8a1a9e`. These two logical digests
use different canonicalisation methods and are not interchangeable. Together they prove the
pre-recovery live and saved states were logically equal; neither proves physical byte equality.

The retained `796d28c7…` database was audited on private read-only copies. It is a 258,048-byte,
4,096-byte-page SQLite file with 63 pages and three free pages (`47`, `48`, `60`), UTF-8,
`journal_mode=delete`, `integrity_check=ok`, `quick_check=ok` and zero foreign-key violations.
Its header records `file_change_counter=1`, `schema_cookie=1`, schema format 4 and SQLite
3.53.4. It contains 20 user tables plus `sqlite_sequence` (21 schema tables), 22 indexes, one
trigger and 382 user rows, including the recorded 26 devices, 60 services, two identity events
and 96 activity events. The complete audit, including every table's row count and content hash,
is `/root/dm-validation-2140/db-hash-analysis-20261106T092138Z/db-audit.txt`.

Two further `.backup()` operations from private copies of `796d28c7…` produced the identical
258,048-byte file and SHA-256 twice. Thus `796d28c7…` is a byte-stable fixed point of this SQLite
backup process. This supports physical normalisation by `.backup()`, but without the original
`c17874a7…` bytes it does not identify which header counters or pages differed.

**Exact live replacement**

1. At `08:30:44Z`, the first corrected-attempt start failed in `guard.py begin` because the
   `--space-path` argument was missing. No guard directory had been created and the preserved
   evidence records `MUTATION=NONE`; the live hash remained `c17874a7…`.
2. At `08:31:31Z` the orchestrator re-ran, passed its explicit live `c17874a7…` check and
   preflight, then invoked `guard.py begin`. At `08:31:33Z` `create_backup()` called
   `sqlite_backup(state["db"], state["backup_db"])`; the guard snapshot became `796d28c7…` and
   `guard-state.json` recorded that snapshot hash plus logical digest `10460718…`.
3. Temporary configuration validation then refused the absent optional key before monitoring
   was enabled. The orchestrator invoked `guard.py recover`. At `08:32:04Z`, guard events record
   `restore_copy_begin` and `restore_copy_complete`; `restore_files()` calls
   `copy_with_metadata()` (`shutil.copyfile`, fsync, mode/owner application and atomic
   `os.replace`) to copy the saved `796d28c7…` database over the live path. This is the first
   retained live-file transition.
4. The `08:33:26Z` retry then stopped because the live hash was already `796d28c7…`. The later
   `08:37:53Z` and `08:38:06Z` recovery copies re-applied the same snapshot bytes; they did not
   cause a second physical identity change.

The installer also created `796d28c7…` backup files through the same `.backup()` primitive, but
the §9.3 live acceptance logs still recorded `c17874a7…`; the installer did not replace the live
file. The live replacement belongs specifically to the reviewed §9.4 guard recovery above.

**Additional validation defect and residual risk**

`guard.py` assigns `prestate["db_sha"]` from `sha256_file(state["backup_db"])`, not from the live
database. `verify_restored()` consequently verifies restoration to the consistent snapshot,
while only the logical digest demonstrates equivalence to the earlier live state. That is why
the guard reported `PASS` despite the physical change. The finding does not retroactively alter
the acceptance criteria, invalidate the logical restoration or prove data loss; it explains why
the historical acceptance gate could not detect byte-level divergence.

**Guard correction (6 November 2026).** The verification guard was corrected after this
investigation without contacting the host or rerunning monitoring. It now keeps three distinct
identities: the byte-preserving original database recovery copy, the consistent SQLite fallback
snapshot, and the restored live database. Capture stops the service and verifies that all writers
are absent before copying the database or its `-wal`/`-shm` sidecars. The SQLite snapshot is
independently verified as logically equal and retained as a fallback. Before restoration, the
current database and sidecars are archived rather than discarded; the original database and
sidecars are then restored with their recorded metadata. Acceptance compares the restored file
against the original recovery copy's physical SHA-256 and metadata, plus integrity, schema/data
and journal-mode checks. A logically equivalent snapshot can no longer satisfy original-byte
identity. The mock-only suite increased from 28 to 35 passing tests, including distinct original
and snapshot identities, rejection of normalised snapshot bytes as a physical restoration,
successful original-byte restoration, WAL/SHM archival, exact capture and restoration of a real
uncheckpointed WAL/SHM pair, and stopped-service failure paths.

This correction cannot retroactively prove that the completed exercise restored the unavailable
`c17874a7…` bytes, because that file was never retained. The historical result remains logically
verified and physically unverified.

The practical residual risk is limited to physical/nonlogical SQLite metadata and page layout:
all schema and user-content checks, integrity checks and foreign-key checks are clean, and the
verified snapshot is the recovery asset. Exact byte attribution is impossible because the
original `c17874a7…` file and its header/page map were never saved. An unqualified
"byte-identical restoration" claim remains a **release blocker**; the bounded exercise result
remains **COMPLETE / ACCEPTANCE PASS** under its recorded criteria.

## Wrapper corrections required by the investigation

The final live run exposed validation-wrapper defects; they were kept separate from the live
exercise and from the candidate source:

1. `begin` initially lacked `--space-path`, causing a pre-execution `AttributeError`. The parser now
   exposes the reviewed default `/`; a regression test covers it. No monitoring was activated by
   that failed attempt.
2. Temporary configuration setup initially rejected the optional absent
   `visibility_prime_interval`; it now preserves the reviewed optional-key behaviour. No monitoring
   was activated by that failed attempt.
3. The payload invocation requires `--payload /bin/sh <script>`; the earlier `--` form was corrected
   before the live run. No monitoring was activated by that failed invocation.
4. The service restoration check now retries transient configd/socket startup for a bounded period
   instead of failing on one immediate status call.
5. SMTP capture parsing now normalises `MAIL FROM:<addr> SIZE=…`, `RCPT TO:<addr>` and
   `X-Envelope-To: <addr>` while preserving the exact single-recipient rule.

The wrapper suite is now 35 tests, all passing after the later physical-identity correction.
The earlier failed-attempt directories remain under
`/root/dm-validation-2140/monitoring/20261106T082834Z/` and
`/root/dm-validation-2140/monitoring/20261106T083326Z/`; they are superseded evidence, not live
exercise results.

## Backups, rollback and teardown

Preserved recovery assets:

| Asset | Meaning |
|---|---|
| `/root/dm-validation-2140/monitoring/20261106T083522Z/guard/` | live guard state, backups, events and `restore.status=PASS` |
| `/root/dm-validation-2140/monitoring/20261106T083522Z/guard/config.json` | pre-state Device Monitor configuration |
| `/root/dm-validation-2140/monitoring/20261106T083522Z/guard/devices.db` | consistent pre-state SQLite snapshot |
| `/root/dm-validation-2140/monitoring/20261106T083522Z/guard/core-locale/` | 19-file core-locale snapshot |
| `/var/backups/devicemonitor/install-v214.qMPS7n` | installer backup used by the reviewed recovery path |
| `/root/dm-validation-2140/backups/monitoring-wrapper-20261106T084032Z/` | pre-correction wrapper and test backup, with `SHA256SUMS` |
| `/root/dm-validation-2140/backups/s94-records-20261106T084313Z/` | pre-update record backups, with `SHA256SUMS` |

No further monitoring run is authorised. If the guard state is reopened after an interruption,
use only the serialized recovery path and retain the evidence:

```sh
python3 verification/monitoring-validation/guard.py status \
  --state /root/dm-validation-2140/monitoring/20261106T083522Z/guard/guard-state.json
python3 verification/monitoring-validation/guard.py recover \
  --state /root/dm-validation-2140/monitoring/20261106T083522Z/guard/guard-state.json
python3 verification/monitoring-validation/guard.py accept \
  --state /root/dm-validation-2140/monitoring/20261106T083522Z/guard/guard-state.json \
  --sockstat-log /root/dm-validation-2140/monitoring/20261106T083522Z/sockstat.log \
  --smtp-capture /root/dm-validation-2140/monitoring/20261106T083522Z/smtp
```

Do not start the daemon manually if recovery fails, do not edit `/conf/config.xml` to force a
pass, and do not restore the old `c2ce5800…` baseline. The current Git Backup configuration is the
operator-accepted state.

The final teardown is clean: the watchdog is cancelled, no SMTP sink or sockstat sampler remains,
no scan/Nmap process remains, no listener is bound to 2525, no WAL/SHM sidecar exists, and the live
installation is running with monitoring disabled.

## Remaining validation gaps and classification

Classification is relative to the requested bounded §9.4 exercise and the separate DM-BL-009
closure. A **release blocker** prevents an unqualified release or acceptance claim; a **deferred
limitation** is outside this bounded exercise and remains recorded for later work.

| Gap | Classification | Rationale |
|---|---|---|
| Physical DB byte identity (`c17874a7…` → `796d28c7…`) | **Release blocker for an unqualified exact-restoration claim about the completed exercise; recurrence corrected in the guard** | The transition is traced to the historical guard's `.backup()` snapshot and `08:32:04Z` recovery copy, and the logical contents match. The original live bytes were never retained, so the internal header/page delta cannot be verified or reproduced. The guard now captures original bytes only after stopping writers, restores those bytes, and distinguishes them from the SQLite snapshot, but that correction cannot prove the historical file was byte-identical. This remains a physical-byte limitation, not a demonstrated data-integrity defect. |
| Live `FRESH=1` and real OPNsense plugin registration/lifecycle | **Deferred limitation for this bounded exercise; release blocker for DM-BL-009 closure** | The disposable jail and copy-only fixtures prove call boundaries, not a real host fresh install, registration or lifecycle. |
| Full reminder/ageing/CARP and daemon-generated notification/service-discovery paths | **Deferred limitation for this bounded exercise; release blocker for full monitoring sign-off** | The two scheduled scans did not run scheduled service discovery; reminders/ageing/CARP were not exercised. Helper emails were direct PHP calls and the fixtures were copy-only. |
| Daemon-triggered attribution of the `notified_at` migration | **Deferred limitation, not a blocker for the observed live mutation** | The column was observed live-present after direct discovery before restoration; the exact caller beyond the direct-discovery path was not separately instrumented. |
| External SMTP, webhook, AdGuard/Pi-hole and targeted-Nmap delivery | **Deferred limitation; intentionally excluded** | These were prohibited by the authorised scope; the loopback SMTP sink was the only notification boundary used. |

The bounded exercise is **COMPLETE / ACCEPTANCE PASS** for the executed two-cycle scope. Further
execution is **unauthorised**. Issue #5 and DM-BL-009 remain **OPEN**; §9.4 remains **PAUSED**.
No deployment, commit, push, release, tag, GitHub reply or production access was performed.
The original exercise ran under the active premium-window gate without bypass; this follow-up
investigation ran at `peak=false off-peak` and also did not bypass or modify the gate.

## Documentation closeout

The records were reconciled on 6 November 2026 without contacting the host or rerunning monitoring.
The follow-up investigation used retained evidence and disposable copies only. It established the
earliest saved occurrences, the exact guard snapshot/recovery sequence that replaced the live file,
the logical equivalence checks and the retained `796d28c7…` audit. The original `c17874a7…` bytes
remain absent, so the physical database difference stays an unresolved acceptance discrepancy rather
than being claimed as byte identity. The separate guard correction now enforces original-byte
identity for any future authorised run, but it does not retroactively prove the completed run. The
residual gaps are classified in the table above. The investigation price-gate status was
`peak=false off-peak`; no bypass was used. Evidence is under
`/root/dm-validation-2140/db-hash-analysis-20261106T092138Z/`. The milestone records are
`.cline-reports/REPORT-20261106-201147.md` and `.cline-reports/REPORT-20261106-203343.md`.
