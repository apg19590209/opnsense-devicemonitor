# Phase 2A — disposable guard physical-restoration rehearsal

**Status: PASS after one real defect was found and corrected.**
**Scope: disposable filesystem only; no live database, service, monitoring, HA or delivery change.**

## Objective

Exercise the corrected guard's full capture/restore lifecycle with a copy of the accepted Phase 1
pre-state and real SQLite DB/WAL/SHM files. This proves recurrence protection for DM-BL-011; it does
not reconstruct the historical `c17874a7…` bytes.

## Defect found and fixed

The first rehearsal showed that `create_backup()` took the fallback SQLite snapshot directly from
the live WAL-mode database. Opening that database to make the snapshot could checkpoint it and remove
its WAL/SHM sidecars after the exact recovery copy had already been captured. That changed the live
pre-state before payload execution.

The guard now:

1. copies the exact live DB/WAL/SHM to the recovery location;
2. copies that recovery set to a disposable temporary directory; and
3. takes the consistent SQLite fallback snapshot from the disposable copy.

The live database and the retained recovery copy are therefore not modified by snapshot creation.
The existing `test_real_wal_and_shm_are_captured_and_restored_exactly` regression now asserts that
both remain unchanged across `create_backup()`, in addition to its prior restore assertions.

## Rehearsal result

Evidence root:
`/root/dm-validation-2140/phase2a-guard-20261107T123250Z/` (`result.json`, transcript, original and
post-state assets). Inputs came from
`/root/dm-validation-2140/phase1-90afa55d-20261107T104937Z/pre-state/`.

```text
CLEANUP_PASS=PASS
RESTORE_STATUS_PASS=PASS
ORIGINAL_DB_CAPTURED=PASS
ORIGINAL_WAL_CAPTURED=PASS
ORIGINAL_SHM_CAPTURED=PASS
SNAPSHOT_PHYSICALLY_DIFFERENT=PASS
SNAPSHOT_HAS_NO_SIDECARS=PASS
SNAPSHOT_LOGICALLY_EQUAL=PASS
MUTATION_DETECTED=PASS
SNAPSHOT_EQUIVALENCE_REJECTED=PASS
EXACT_DB_RESTORED=PASS
CONFIG_RESTORED=PASS
RECORD_UNCHANGED=PASS
OPNSENSE_CONFIG_UNCHANGED=PASS
CORE_LOCALE_UNCHANGED=PASS
POSTSTATE_ARCHIVED=PASS
POSTSTATE_SUMMARY_MATCHES=PASS
VERIFY_RESTORED_CLEAN=PASS
PHASE2A=PASS
ORIGINAL_DB_SHA=0f964e59ef3673948acb16938918f4a6368520b2c88868a9cc6205614313e026
ORIGINAL_WAL_SHA=3b82731a73755552be0382f726130bd535dd53443c9ff1d85d89709dc9ecb946
ORIGINAL_SHM_SHA=984681af71ab706710b6f6ab243320e263eb52ab591f0eb94ab04b669cd7184f
SNAPSHOT_DB_SHA=42cfd0d5a604eeb0f83a57ae4243a973fec637c9e637f6f273de461ed3bc9117
RESTORE_STATUS=PASS
```

The rehearsal deliberately changed monitoring configuration and added a SQLite schema/data mutation,
created real WAL/SHM assets, detected the mutation, archived the post-state, restored the exact
original DB/WAL/SHM bytes and metadata, and verified configuration, record, OPNsense configuration
and all 19 core-locale files were unchanged.

## Regression result

```text
python3 -m unittest test_guard.GuardTests.test_real_wal_and_shm_are_captured_and_restored_exactly
Ran 1 test ... OK

python3 test_guard.py
Ran 35 tests ... OK
```

The 35-test result above is local evidence. The suite is now wired into the validation-only CI
workflow with exact `Ran 35 tests`/`OK` assertions, and `tests/test_ci_config.py` pins that wiring.
No exact-SHA run has yet exercised the new step, so CI execution remains unproven until that run is
recorded.

## Boundaries and remaining DM-BL-011 work

- No live Device Monitor service, database, monitoring setting, host configuration or notification
  path was changed.
- The disposable writer proxies are modelled after the real service boundary; this rehearsal does not
  replace a future authorised live guard run.
- No retained database file checked on 7 November contains the historical `c17874a7…` bytes. The
  retained pre-monitor-scan backup is `65e11a3b…`; the 6 November original remains unavailable.
- DM-BL-011 therefore still needs a recovered original-byte copy or explicit operator acceptance.
  Phase 2A proves the corrected guard prevents recurrence but cannot change the historical record.
