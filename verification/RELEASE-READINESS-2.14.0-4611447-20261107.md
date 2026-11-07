# Device Monitor 2.14.0 — release readiness at `4611447`

**Assessment date:** 7 November 2026 (Australia/Sydney)
**Publication recommendation: NO-GO.** The runtime artifact and catalogue repair are ready, but the
revised objective requires the remaining real-host and historical-byte validation gates to be closed
or explicitly accepted before publication.

## Reviewed candidate

| Item | Value |
|---|---|
| Exact reviewed documentation/evidence commit | `4611447089e2482a0c6af7a1844e9f6fa16c84d1` |
| Parent / integrated source | `e9ec5486a8cc9e87e3b6d3cf6098f26ed15e1370` on `main` |
| Exact-candidate CI | [run `42368818807`](https://github.com/apg19590209/opnsense-devicemonitor/actions/runs/42368818807): success |
| Runtime archive | `dm-v2.14.0-runtime.tar.gz` |
| Size | 1,729,177 bytes |
| SHA-256 | `90afa55dd826c0dc3be8a23902b809baa465e25191dc372dc6cc2ef4e57fc243` |
| Members | 60 |
| Latest published release | v2.12.1 |
| 2.14.0 tag/release | none |

## Satisfied release acceptance

- Exact-candidate CI is green at `4611447`. Logs report `LOCALE_MERGE=PASS`,
  `UPGRADE_PREDECESSORS=PASS passed=10 skipped=0`, `RELEASE_INPUTS=PASS cases=7`,
  `V2140_RELEASE_MANIFEST=PASS` and bundle reproducibility.
- The exact archive passed the Phase 1 same-version repair on `.23`:
  `INSTALL_OK version=2.14.0 files=63 ... unchanged=63 repaired=0`. All 42 manifest rows and 63
  generated/installed targets matched; current catalogues merged warning-free; translations were
  preserved; configuration, logical/physical database bytes and the 19 core-locale files were
  unchanged; SQLite integrity and service restoration passed.
- Disposable FreeBSD jail coverage passes for check/install/repair/rollback/failclosed,
  fresh/fresh-rollback and the actual published v2.12.1 predecessor.
- Operator-supplied authenticated evidence received 7 November 2026 (Australia/Sydney) shows
  Device Monitor `v2.14.0` and `v2.14.0 Features and Enhancements`, and the operator confirms that
  Devices loads without error. No exact observation time was supplied.
- The native Phalcon/Volt/ViewTranslator runtime matrix now passes for all nine bundled languages:
  `LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0`, 10 pages and 490 keys
  per language. The gap is the documented `nl_NL` GUI-selector absence, not a rendering failure.
- Phase 2A now passes on disposable DB/WAL/SHM assets, and the discovered snapshot-side-effect
  defect is fixed with a strengthened existing guard regression. All 35 guard tests pass locally.
  The suite is now wired into the validation-only CI workflow with exact `Ran 35 tests`/`OK`
  assertions and pinned by `tests/test_ci_config.py`; no exact-SHA run has yet exercised the new
  step, so CI execution remains unproven until that run is recorded.

## Publication blockers under the revised objective

| Blocker | Why it blocks | Required closure |
|---|---|---|
| **DM-BL-011** — historical `c17874a7…` byte identity | The original bytes were not retained. The corrected guard and Phase 2A prove future recurrence is controlled, but do not prove the historical restoration | Locate a retained original-byte copy, or record explicit operator acceptance of the historical limitation |
| **DM-BL-012** — real-host fresh install/plugin lifecycle | Jail stubs prove only installer call boundaries; no real `FRESH=1`, real `rc.configure_plugins`, configd or reboot-persistent daemon has been observed | Run Phase 3 on a disposable OPNsense VM with clean snapshots and real plugin/service checks |
| **DM-BL-013** — remaining monitoring/HA/delivery | The completed exercise covered two scans and direct helper SMTP only; daemon-triggered discovery, reminders/ageing, targeted Nmap, enrichment, exact caller attribution, external delivery and CARP/failover remain unproven | Phase 4A single-host tests on the disposable VM; Phase 4B isolated HA pair; separately approved external lab endpoint where required |

`nl_NL` selector absence, browser layout/JavaScript execution and translation-quality review are
known residual limits but do not reopen the native runtime matrix. They are not claimed as closed.

## Issue #5 dependency

Issue #5 remains **OPEN**. Reporter confirmation of service health and normal page loading cannot be
obtained before a published release unless a separate candidate handoff or issue reply is authorised.
No reply or release has been made. This is an external reporter dependency, not a code fix.

## Artifact versus validation evidence

The exact `90afa55d…` archive is the artifact that passed Phase 1 and exact-candidate CI. The earlier
1,725,593-byte `5149bfd4…` archive remains preserved as superseded evidence and must not be
substituted. The guard source/test correction made during this closure pass is verification-only and
is not a member of the runtime archive; the archive identity is unchanged.

## Release-control state

- The intended final release commit must be a new reviewed commit containing the closure records and
  the guard fix; `4611447` is no longer sufficient as the final documentation commit because these
  changes are not committed.
- That commit must be reviewed, pushed without force, integrated into `main` without rewriting
  history, and followed by exact-main CI.
- The runtime archive must remain 1,729,177 bytes / `90afa55d…` unless runtime inputs change; any
  change requires a new bundle, full relevant validation and a new readiness record.
- The 35-test guard pass is local evidence at `4611447`. The workflow now contains a step that
  asserts exactly `Ran 35 tests` and `OK`, but the reviewed `4611447` run predates that wiring. A
  final record must cite a new exact-SHA run before claiming CI execution.
- No tag or release is authorised. Publication requires separate approval after DM-BL-011/012/013
  and the final control gates are resolved or explicitly dispositioned.

## Decision

**NO-GO for publication today.** The catalogue-header repair and exact archive are ready, but the
revised completion criteria are not: real-host fresh/plugin lifecycle, single-host monitoring and
HA/delivery evidence, and historical-byte acceptance remain outstanding. The next concrete test is
Phase 3 on a disposable OPNsense VM; the only alternative for DM-BL-011 is explicit operator
acceptance of the historical limitation.
