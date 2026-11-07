# Device Monitor 2.14.0 — validation closure plan

**Status: ACTIVE. Publication remains blocked pending the gates below. No 2.14.0 tag or release
exists. DM-BL-010 remains integrated but publication-pending; DM-BL-011/012/013 and issue #5 remain
OPEN.**

## Objective and policy

The objective changed on 7 November 2026: resolve the outstanding validation items before publishing
2.14.0 instead of deferring them as publication limitations. A requirement is closed only by direct
evidence, a successful test, or an explicit operator decision that accepts a stated residual risk.
External dependencies are identified as dependencies, not rewritten as code fixes.

Completed Phase 1 and jail evidence is reused. The Phase 1 repair installation is not repeated.
`FRESH=1` is not run on the existing `.23` installation. Production, `.252`, `.253`, monitoring,
HA services, delivery endpoints, releases and tags are not contacted or changed by this plan.

## Current evidence and remaining work

| Item | Actual acceptance criterion | Evidence already held | What remains unproven | Classification |
|---|---|---|---|---|
| **DM-BL-011** — historical database-byte identity | Reconstruct and compare the original `c17874a7…` bytes, or record explicit operator acceptance of the historical limitation | Logical restoration, schema/data/integrity checks and the historical transition trace pass. The corrected guard now captures DB/WAL/SHM separately. A new disposable Phase 2A rehearsal passes, including exact-byte restore and rejection of a logically equal snapshot. A read-only expanded search found zero exact copies among 128 physical candidates and 67 archives, including a supplemental `/root/dm-backups` scan. | The original `c17874a7…` bytes are absent from all retained `/root/dm-*` and `/var/backups/devicemonitor` database files inspected on 7 November 2026; the retained copies are the snapshot `796d28c7…` or older unrelated states. Controlled SQLite copy/`VACUUM` transformations did not reproduce the hash. No local test can recreate the lost historical bytes. | Historical evidence plus operator decision. Not a live-service test. See `verification/DM-BL-011-BYTE-RECOVERY-20261107.md`. |
| **DM-BL-012** — real-host fresh install and plugin lifecycle | Run `FRESH=1` on a genuinely empty disposable OPNsense host; prove real `rc.configure_plugins`, configd, daemon autostart, menu/ACL registration and reboot persistence | Isolated jail `fresh` and `fresh-rollback` pass; the live 2.13.3→2.14.0 upgrade and repair lifecycle on `.23` pass. | Real-host fresh installation, real plugin registration, real daemon lifecycle after a fresh install and reboot persistence. Jail stubs are not equivalent. | Disposable OPNsense VM. Requires environment approval and provisioning. Exact setup and test procedure: `verification/PHASE3-DISPOSABLE-OPNSENSE-VM-PLAN-20261107.md`. |
| **DM-BL-013** — monitoring, HA/CARP and delivery | Exercise scheduled daemon-triggered discovery, reminders/ageing, daemon-generated notifications, targeted Nmap, enrichment, exact `notified_at` attribution, external-lab delivery and isolated HA failover | Two scheduled inventory scans, direct DMTEST discovery, scope-limited probes and direct loopback-helper SMTP pass. | Daemon-triggered service discovery, reminder/ageing lifecycle, daemon-generated delivery, targeted Nmap, enrichment, exact caller attribution and external delivery. CARP/failover is entirely unproven. | Phase 4A on a disposable single OPNsense VM; Phase 4B needs an isolated two-node pair. External delivery needs an approved lab endpoint. |
| **Native Phalcon/Volt/ViewTranslator runtime** | Render the ten Device Monitor pages through the production Phalcon/Volt/ViewTranslator path for every bundled language and verify resolved output | On 7 November 2026 the installed 2.14.0 tree passed `LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0`: 10 pages and 490 keys per language, zero failures. Evidence: `/root/dm-validation-2140/language-runtime-2.14.0-20261107.md`; gap analysis: `verification/LANGUAGE-ACCEPTANCE-GAP-20261107.md`. | `nl_NL` remains absent from the core GUI language selector by documented DM-BL-008a design; it renders when selected through the plugin path. Browser layout, JavaScript execution and translation quality are outside this test. | **Satisfied for the runtime matrix.** The known selector gap and human wording review remain separate, non-runtime items. |
| **Release documentation and control alignment** | Notes, runbook, readiness, tag message, final commit and CI evidence all describe the same artifact and the actual live/jail/local coverage | Candidate is 1,729,177 bytes / `90afa55d…`; CI `42368818807` is green at `4611447`; Phase 1 installed the exact archive on `.23`. | The final release commit and exact-SHA CI do not yet exist because validation closure is incomplete. Release notes must not claim the remaining real-host gates. | Documentation and release control. Can be prepared now; publication cannot proceed. |
| **Issue #5** | Reporter confirms the published v2.12.1 installation is functionally healthy: the service is running and pages load normally | The reporter already confirmed successful v2.12.1 installation, About displaying `v2.12.1`, and `INSTALL_OK` with `daemon_restarted=1`. The manifest investigation, DM-BL-010 repair, Phase 1 evidence and exact-main CI are recorded. Issue #5 remains OPEN. | Only reporter confirmation of service health and normal page loading remains. It is external and can be supplied against the already-published v2.12.1; a candidate handoff or issue reply would require separate authorisation. | External reporter dependency. Not a code fix and cannot be closed locally. |

## Smallest meaningful closure procedures

### DM-BL-011 — historical-byte acceptance

- **Technical result:** Phase 2A cannot recover the prior `c17874a7…` bytes. It proves that the
  corrected guard no longer introduces the defect. The expanded read-only recovery search is
  recorded in `verification/DM-BL-011-BYTE-RECOVERY-20261107.md`.
- **Environment:** none. The decision is made from the existing evidence record.
- **Backups/rollback:** not applicable.
- **Acceptance:** a dated operator statement that the historical physical-byte limitation is
  accepted, with the logical digest, schema, row counts and integrity evidence retained; or a newly
  found original-byte copy that compares to `c17874a7…`.
- **Estimated effort:** 10–15 minutes for review and acceptance once the evidence is read.

### DM-BL-012 — real-host fresh install and plugin lifecycle

- **Environment:** one disposable OPNsense 26.7.8_2-compatible VM on an approved hypervisor, at
  least 2 vCPU, 4 GB RAM, 20 GB free virtual disk and isolated WAN/LAN networks. No production,
  `.23` reuse, `.252` or `.253` access. The current host has no `vmm`, `/dev/vmm` or `vm-bhyve`; no
  candidate image is available locally.
- **Backup/recovery:** take a clean VM snapshot before the install. Preserve console and installer
  transcripts. On failure, revert the snapshot or destroy and recreate the VM; do not repair a real
  host in place.
- **Procedure:** verify the archive size/SHA-256; run `--check` and require `predecessor=fresh`,
  64 targets and 10 core locales; run the real installer; require `INSTALL_OK version=2.14.0
  files=64 core_locales=10`; prove real `rc.configure_plugins`, configd and daemon state; verify
  menu/ACL/plugin registration; reboot and repeat the service/plugin checks; test the fresh-install
  rollback path from a second clean snapshot.
- **Acceptance:** real plugin registration and a daemon that survives reboot, with no stub claim.
- **Estimated effort:** 3–5 hours after environment handoff, excluding provisioning.

### DM-BL-013 — single-host monitoring and delivery (Phase 4A)

- **Environment:** reuse the isolated Phase 3 VM with a clean snapshot and a disposable test client;
  loopback SMTP and a local HTTP webhook stub only. No external account or production DNS.
- **Backup/recovery:** snapshot the VM; capture the pre-test database/configuration; restore the
  snapshot after each destructive scenario.
- **Procedure:** age `service_discovery_state.last_run` past the hourly gate and prove the daemon,
  not a manual scan, performs discovery; seed controlled in-scope rows and prove reminder/ageing and
  fresh-host refusal; generate identity/service/new-device messages and verify one delivery each;
  enable one opted-in literal DMTEST target and prove one-target Nmap/rate-limit scope; exercise
  local AdGuard/Pi-hole/Unbound stubs; start from a pre-migration snapshot and attribute the
  `notified_at` transition to a logged daemon cycle.
- **Acceptance:** daemon logs and loopback captures prove each path; no out-of-scope connection.
- **Estimated effort:** 3–5 hours after the VM exists.

### DM-BL-013 — HA/CARP and external delivery (Phase 4B)

- **Environment:** two disposable OPNsense VMs on an isolated CARP/pfsync network, a shared virtual
  IP and an in-scope test client; a separately approved external SMTP/webhook lab endpoint for the
  external-delivery variant. `.252`/`.253` are not valid substitutes.
- **Backup/recovery:** clean snapshots of both nodes; preserve both consoles and captures; revert,
  do not repair, on failure.
- **Procedure:** verify role/IP display; prove standby suppression of service discovery and alerts
  while its own inventory ages; fail over master→backup; require one transition notification and no
  duplicate alerts; promote and return the original master; repeat role/registration checks on both
  nodes; then repeat delivery against the approved external endpoint.
- **Acceptance:** role transition, no duplicate alert, inventory ageing and one expected delivery.
- **Estimated effort:** 5–8 hours after both nodes exist; external endpoint setup is additional.

### Issue #5

The reporter has already confirmed that published v2.12.1 installed successfully, displays
`v2.12.1` in About, and ended with `INSTALL_OK` and `daemon_restarted=1`. The remaining requirement
is reporter confirmation that the service is running and pages load normally. This can be supplied
against the existing published release; it does not require 2.14.0 publication. It cannot be
manufactured locally. Keep issue #5 OPEN and do not post an issue reply without separate approval.

The command-level Phase 3, Phase 4A and Phase 4B procedure is preserved in
`/root/dm-release-v2.14.0-candidate-20261107-202600/PRE-RELEASE-VALIDATION-PLAN-20261107.md`.
The repository-ready Phase 3 setup, isolation, resource, backup, rollback and acceptance procedure
is `verification/PHASE3-DISPOSABLE-OPNSENSE-VM-PLAN-20261107.md`.
That plan remains subordinate to this acceptance record and the repository control documents; it
must be reconciled before any real-host phase is approved.

## Work completed in this closure pass

### Phase 2A disposable guard rehearsal — PASS

Evidence root:
`/root/dm-validation-2140/phase2a-guard-20261107T123250Z/` (`result.json`, transcript, original and
post-state assets). The rehearsal used a copy of the accepted Phase 1 pre-state database and real
SQLite DB/WAL/SHM files, with writer proxies and no live service mutation.

Results:

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

### Defect found and corrected

The first Phase 2A attempt showed that `create_backup()` took the fallback SQLite snapshot directly
from the live WAL-mode database. Opening that database for the snapshot could checkpoint it and
remove its WAL/SHM files, changing the live pre-state after the original recovery copy had been
captured. The guard now takes the fallback snapshot from a disposable copy of the exact recovery
assets, so neither the live pre-state nor the recovery copy is modified by snapshot creation.

`verification/monitoring-validation/test_guard.py` now asserts that the live DB/WAL/SHM assets and
the recovery copy remain unchanged across `create_backup()`. The strengthened suite passes all 35
existing guard tests. No guard test count was added; one existing WAL/SHM test was strengthened.
The 35-test suite has now been added to `.github/workflows/ci.yml` as a validation-job step that
fails unless the log contains `Ran 35 tests` and `OK`; `tests/test_ci_config.py` also pins that
wiring. The workflow itself parses and `CI_CONFIG=PASS cases=7` locally, but no exact-SHA CI run has
yet exercised the new step. The final release record must cite that exact run after it exists.

### Native runtime language matrix — PASS

`python3 tests/test_language_acceptance.py --engine runtime` passed on the installed 2.14.0 tree with
9 languages, 10 pages per language and 490 keys per language. Report:
`/root/dm-validation-2140/language-runtime-2.14.0-20261107.md`. The only gap is the documented
`nl_NL` selector absence; it is not a runtime rendering failure. Its user-visible effect and the
acceptance distinction are recorded in `verification/LANGUAGE-ACCEPTANCE-GAP-20261107.md`. This
closes the native runtime coverage gate, but not human translation-quality or browser-layout review.

### Retention and environment findings

- No retained `devices.db*` file in the expanded roots matches `c17874a7…`; 128 physical candidates
  and 67 archives were checked, including 45 supplemental `/root/dm-backups` archives. There was no
  exact archive member either.
- The local `/var/backups/devicemonitor/devices.db.pre-monitor-scan-20260923-070801` is
  `65e11a3b…`; it is an older backup, not the 6 November original.
- `vmm` is not loaded, `/dev/vmm` is absent, `bhyve` exists but has no usable guest device/image,
  `vm-bhyve` is absent, and no disposable OPNsense image or approved external hypervisor is
  recorded; DM-BL-012/013 real-host phases remain unavailable.
- The current `.23` installation was not modified by the Phase 2A or language tests. Monitoring and
  notification delivery remain disabled.

## Remaining approvals and dependencies

1. **DM-BL-011:** operator acceptance of the historical physical-byte limitation, or a new source of
   the original `c17874a7…` bytes.
2. **DM-BL-012 and Phase 4A:** approval to provision and use a disposable OPNsense VM.
3. **DM-BL-013 Phase 4B:** approval and provisioning of an isolated two-node CARP/pfsync pair.
4. **External delivery:** approval of a lab SMTP/webhook endpoint; no production recipient.
5. **Release publication:** after all above evidence and records are reviewed, a final release commit,
   exact-SHA CI, final bundle verification and separate tag/release approval.
6. **Issue #5:** reporter confirmation that the already-published v2.12.1 service is running and
   pages load normally. No issue reply or candidate handoff is authorised now.

## Review and proposed commit scope

No commit, push, tag or release was made during this closure pass. If this work is reviewed for a
future documentation/verification commit, the exact scope is:

| Path | Purpose |
|---|---|
| `.github/workflows/ci.yml` | Validation-only CI step requiring exactly 35 guard tests and `OK` |
| `PRODUCT_BACKLOG.md` | DM-BL-010 publication state, DM-BL-011/012/013 evidence and revised gates |
| `PROJECT_STATE.md` | Current validation-closure checkpoint and publication state |
| `tests/test_ci_config.py` | Pins the monitoring-guard CI wiring and seven configuration cases |
| `verification/DM-BL-010-CATALOGUE-HEADERS-20261107.md` | Authenticated Phase 1 evidence and revised publication gate |
| `verification/PHASE1-EXACT-CANDIDATE-23-20261107.md` | Authenticated UI evidence and remaining limitations |
| `verification/RELEASE-READINESS-2.14.0-4611447-20261107.md` | Exact-SHA CI, artifact identity and NO-GO assessment |
| `verification/VALIDATION-CLOSURE-2.14.0-20261107.md` | Consolidated acceptance plan and evidence |
| `verification/monitoring-validation/PHASE2A-DISPOSABLE-20261107.md` | Disposable guard rehearsal evidence |
| `verification/monitoring-validation/guard.py` | Verification-only snapshot-side-effect correction |
| `verification/monitoring-validation/test_guard.py` | Strengthened WAL/SHM regression |
| `verification/DM-BL-011-BYTE-RECOVERY-20261107.md` | Read-only search proving the historical bytes were not retained |
| `verification/LANGUAGE-ACCEPTANCE-GAP-20261107.md` | `nl_NL` selector gap and runtime-acceptance disposition |
| `verification/PHASE3-DISPOSABLE-OPNSENSE-VM-PLAN-20261107.md` | Approval-ready Phase 3 VM prerequisites and procedure |

The guard files are verification tooling, not runtime inputs. The archive remains 1,729,177 bytes
with SHA-256 `90afa55dd826c0dc3be8a23902b809baa465e25191dc372dc6cc2ef4e57fc243`; no release pin,
runtime source or manifest is in scope. Before any commit, run `git diff --check`, review the exact
file list and rerun the focused guard regression only if the guard changed after the recorded pass.
After any future push, exact-SHA CI is still required. The workflow now runs the 35 guard tests and
asserts both the exact test count and `OK`, but no exact-SHA run has yet exercised that new step.

## Recommended next test

The next smallest real validation step is **Phase 3 on an approved disposable OPNsense VM**: fresh
`FRESH=1` install with real plugin registration and a reboot persistence check. It cannot be run on
the existing `.23` installation or without the missing VM environment. If the VM cannot be supplied,
the only remaining closure action for DM-BL-011 is the operator's explicit historical-byte
acceptance; no local test can resolve it.
