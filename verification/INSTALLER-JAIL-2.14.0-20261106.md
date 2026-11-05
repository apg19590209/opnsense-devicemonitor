# Device Monitor 2.14.0 installer-jail validation — 6 November 2026

## Scope and candidate identity

This record covers the disposable-FreeBSD-jail adaptation and execution for the local
2.14.0 integration candidate. It does not deploy the candidate, change a live service or
validate an authenticated browser.

| Item | Value |
|---|---|
| Repository | `/root/src/opnsense-devicemonitor-upstream` |
| Branch | `integration/dm-bl-009-reconcile-20261105` |
| Validated source form | HEAD `eac1160557352d45648c4a25310b8daeaad440f6` plus the rollback correction before publication (`CANDIDATE_SOURCE=worktree`) |
| Predecessor | live Device Monitor 2.13.3, commit `eadfc577b9ef184a12edba72780ec548a8486510` |
| Bundle | `/root/dm-backups/dm-bl009-candidate-rollback-fix-20261106-083105/dm-v2.14.0-runtime.tar.gz` |
| Bundle identity | 1,725,593 bytes; sha256 `5149bfd41e5842a144a9d1280c008511f20f3783932eca9beb1f48fca6173f5f`; 60 members |
| Publication state | Validated before publication; exact-commit CI is tracked in the milestone report; not deployed |
| Target set | 42 manifest rows + 11 plugin catalogues + 10 merged core catalogues = 63 |

The harness copies the live 2.13.3 installation record and all 61 recorded targets into the jail,
builds the immutable bundle from the explicit worktree candidate, and compares every bundle member
with that source before executing the unmodified installer. The historical 2.13.3 evidence under
`verification/installer-sandbox/evidence/` was not modified; new evidence is under
`verification/installer-sandbox/evidence-2.14.0/`.

## About and Features version source

The deployed 2.13.3 line has a confirmed source defect: its About page contains the hardcoded
heading `v2.10 Features and Enhancements`. The separate report of an About badge showing
`v2.13.2` is not established by server evidence. The 2.13.3 controller reads the installed
`defaults.json` (`2.13.3`), so the stale badge remains an unconfirmed browser/page-state
explanation until an authenticated browser network capture is available.

The 2.14.0 candidate contains the heading correction. Its `settings.volt` has one
`/api/devicemonitor/config/getversion` callback, derives `v` from the response's `version` field,
and assigns that value to both `#about-version` and `#about-features-version`. The controller reads
the installed `defaults.json`. The focused check recorded:

```text
ABOUT_ENDPOINT=2.14.0
ABOUT_BINDINGS=about-version,about-features-version
FEATURES_STATIC_FALLBACK=v2.14
ABOUT_MODE=source-endpoint-binding; authenticated-browser=not-performed
```

Both displayed values therefore come from the endpoint on a successful request. The Features span
retains a non-authoritative `v2.14` initial fallback if the request does not complete. No
authenticated browser validation was performed.

## Harness adaptation

The harness now selects and verifies an explicit version, commit, bundle digest and bundle size;
derives expected counts from the reviewed manifest and locale plan; preserves the live 2.13.3
predecessor state; plants one unchanged and one deliberately modified published legacy path; and
checks every installed target for digest, mode and `root:wheel` ownership. It also compares the
live host fingerprint before and after every scenario.

The only host-service stub is `service configd`; it records calls and injects the rollback-test
failure. A directory overlay keeps the jail on the real `/bin` binaries while replacing only
`pgrep` with a wrapper that delegates to the real binary with `-j dm-installer-sandbox`. This keeps
the live daemon invisible to the installer without changing its process pattern.

## Core-locale rollback defect and correction

The earlier 2.14.0 candidate (`530facc…`) restored installed targets, prunes and the record after an
injected post-prune `configd` failure, but it did not back up the core-locale state directory.
Consequently all ten pre-existing `/var/backups/devicemonitor/core-locale/*.state` files retained
the attempted `installed=` digest. These files are not disposable metadata: `uninstall.sh` uses
them as the locale ownership and restore record. The pristine `.OPNsense.mo` copies happened to
remain unchanged, but that did not repair the state files.

`release/prune-plan.sh` now snapshots the state directory and every `*.state` and
`*.OPNsense.mo` file, including content digest, mode and owner/group. Restore is exact and removes
state files or the directory itself when they did not exist before the failed run. A damaged state
backup is refused before current state is changed. `install-unattended.sh` creates this backup
before mutation and invokes it during automatic rollback; failure is reported as
`ROLLBACK_CORE_LOCALE_STATE_INCOMPLETE`. The release-input pin was regenerated with
`sh release/build-release-inputs.sh`, and `sh release/verify-release-inputs.sh .` reports
`VERIFY_OK=4`.

## Scenario results

All scenarios ran against the candidate above with the price gate off-peak and no bypass.

| Scenario | Result | Evidence |
|---|---|---|
| `check` | **PASS** — no mutation; 63 targets, 10 core locales, one prunable, one retained, no daemon running | `evidence-2.14.0/check/` |
| `install` | **PASS** — 63 targets verified; `pruned=1`; `unchanged=32`; modified legacy path retained; database/configuration byte-identical | `evidence-2.14.0/install/` |
| `repair` | **PASS** — record-driven dropped locale pruned; `unchanged=63`; record returned to 63 rows | `evidence-2.14.0/repair/` |
| `rollback` | **PASS** — `ROLLBACK_STATUS=COMPLETE`; all 63 targets, the prune fixture, the record and 19 core-locale state/pristine files restored exactly; only the expected backup directory remained | `evidence-2.14.0/rollback/` |
| `failclosed` | **PASS** — tampered prune helper refused with `ABORT: release inputs`; no mutation | `evidence-2.14.0/failclosed/` |

The rollback evidence shows target restoration `restored=31 skipped=32 conflicts=0 failed=0`,
prune restoration `restored=1 skipped=0 conflicts=0 failed=0`, and core-locale restoration
`restored=19 removed=0 conflicts=0 failed=0`. The before/after snapshots are identical except for
the retained installer backup directory. The failed run's evidence remains preserved at
`verification/installer-sandbox/evidence-2.14.0-pre-rollback-fix-eac1160/`; it and the `530facc…`
bundle are diagnostic predecessors, not current acceptance evidence.

A separate harness-only negative check supplied a deliberately wrong expected bundle digest. It
exited `1`, recorded `SANDBOX_SCENARIO check FAIL`, ran teardown, and reported the live host
unchanged. This confirms unexpected failures are not converted to PASS. The expected installer
refusals in the rollback and fail-closed scenarios are distinguished by explicit assertion and do
not by themselves count as harness failures.

## Final wrapper regression and evidence regeneration

After the wrapper was corrected to preserve scenario status through the `tee` pipeline and teardown,
the rollback correction was applied and all five scenarios were rerun with `DM_SANDBOX_SAVE=1`
against the new immutable bundle. The regenerated evidence contains 53 files under
`evidence-2.14.0/`; the historical 2.13.3 and superseded 2.14.0 evidence trees remain unchanged.

A harness-only mocked check of the extracted `run_one` wrapper exercised the status boundaries:
success plus clean teardown produced PASS; an unexpected scenario exit `7` produced a nonzero
result; a successful scenario with teardown failure exited `1` and reported the cleanup error; a
scenario exit `7` combined with teardown failure retained exit `7`; and an expected installer
refusal handled by its assertion remained a scenario PASS. The scenario name in the body and the
saved-evidence call matched each time. This is a wrapper check, not a jail scenario.

## Other validation

```text
python3 tests/test_rollback_isolated.py
  six cases PASS; ROLLBACK_ISOLATED=PASS cases=6

python3 tests/test_installer_status.py
  six cases PASS

python3 tests/test_release_inputs.py
  six cases PASS

python3 tests/test_release_manifest.py
  V2140_RELEASE_MANIFEST=PASS

python3 tests/test_bundle_build_safety.py
  eight cases PASS

python3 tests/test_bundle_reproducibility.py
  nine cases PASS

sh release/verify-release-inputs.sh .
  VERIFY_OK=4
```

Two independent builds from the current worktree produced byte-identical candidates. The
committed-checkout `tests/test_bundle_determinism.py` remains pending because HEAD does not yet
contain the rollback correction and therefore still rebuilds the superseded `530facc…` identity;
it must be rerun after the reviewed changes are committed, without bypassing it.

`python3 -m pytest` is unavailable on this host (`No module named pytest`); the repository's
standalone test entry points were run directly instead.

Every scenario ended with no sandbox jail, no sandbox mount and no host installer-stage directory.
The live `.23` fingerprint matched before and after, including the 61 recorded targets, record,
database, configuration, backup listing, pristine catalogues, and the existing daemon/configd
processes. No deployment, service change, monitoring activation, production access, `.252`/`.253`
access, commit, push, release or tag change occurred.

## Remaining gaps and decision

* The corrected `5149bfd…` artifact must pass CI at its exact published commit before it can be
  treated as a publication candidate. Any source change requires a new bundle identity and fresh
  validation.
* `FRESH=1` remains untested.
* Jail rollback does not prove live rollback; no live rollback was invoked on `.23`.
* The configd and daemon lifecycle are still represented by the host-service stub/process-isolation
  shim in this harness, not by a real service restart.
* Authenticated browser validation of About and Features remains unperformed.
* Linux CI remains separate from the FreeBSD on-host jail validation. Historical 2.13.3 evidence
  does not validate 2.14.0.
* `tests/test_bundle_determinism.py` still validates committed HEAD and therefore cannot establish
  this worktree candidate before publication.
* DM-BL-009 remains **OPEN**.

Recommended next task: review and commit the rollback correction, publish the integration branch
without force, and verify CI against the exact resulting SHA before deciding on the `main`
integration path.
