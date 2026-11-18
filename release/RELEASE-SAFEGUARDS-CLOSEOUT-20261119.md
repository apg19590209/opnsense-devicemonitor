# FINAL REPORT — Release and deployment safeguards merged

**Status: COMPLETE.** PR #11 was merged normally into `main` after confirming reviewed head `294caa3`, successful CI `44404713134`, clean mergeability and the absence of later head changes. No deployment, tag or publication occurred.

## Merge evidence

- PR #11: <https://github.com/apg19590209/opnsense-devicemonitor/pull/11>
- Reviewed head: `294caa39413938d169604619b498a39e99357555`.
- CI run `44404713134`: **success** for that exact head.
- Merge commit: `5b5f51b4dc3641241475fe4f54d6027cc991922f`; parents `eaf6868` and `294caa3`.
- The repository normal method is a merge commit; no protection bypass, force-push, branch deletion, tag or release publication was used.
- `main` contains no runtime application-file changes in this merge. The changes are installer, release tooling and tests.

## Candidate and host separation

- Final release-tool artifact: source `294caa3`, archive `be2b64caa5bb317f9ffef506beba8f5266babfab1c68f14b7b96d2fa7d51689b`, 12,554,194 bytes, 96 members. It is **not deployed**.
- Hosts continue to run the separately accepted runtime archive `b4e388ac86f03e0bead0cceae0f74a7b2a480457eb26d20998183ea59f208e72`, source `202d6ef`.
- The host acceptance for `b4e388ac` was not transferred to the tooling candidate. Hosts were preserved and not contacted for deployment.

## Merged controls

- A single deployment entry point validates source, archive identity, exact membership, required features and prior-stage acceptance before writes.
- Acceptance is derived from generated host-check evidence in the execution ledger; typed PASS results and missing evidence are refused.
- The stage order is `.23` then `.252` then `.253`; MASTER cannot proceed without BACKUP acceptance.
- The close-out audit compares the original requirements with execution records; exceptions are explicit.
- Exported archive modes are bound to the Git index and reproducible archive identity.

## Validation

- Affected local suites passed at the reviewed head: deployment safeguards, execution ledger, release safeguards, release inputs, bundle determinism, bundle safety, bundle reproducibility and catalogue repair.
- CI `44404713134` passed at the reviewed head before merge.
- The workflows that changed are release tooling and test fixtures; their tests exercise real refusal paths, including stale ancestry, altered archives, missing features, missing prior stages and hand-typed evidence.

## CI failure audit — grouped by cause (19 November 2026)

The feature branch had eight failed CI runs and two successful runs. They represent six distinct
causes; the later successes at `5b3867b` and `294caa3` cover the merge candidate.

| Cause | Runs | Classification | Local preflight should have caught it? | Repeated after diagnosis? | Status |
|---|---|---|---|---|---|
| Email Log delivery fixtures used a fixed old date, outside the live one-day observation window on the runner. | `44302961103` (`27aeffe`) | Incorrect test fixture, not runtime behaviour. | Yes: the focused Email Log fixture is cheap to run locally and now runs in preflight. | No. | Resolved by relative timestamps and a live-window assertion. |
| The candidate test and bundler assumed a local `main`; a PR checkout only has `origin/main`. | `44303269512` (`357f38f`), `44304134493` (`136c52a`) | Incorrect test/deployment-tooling assumption about CI checkout topology. | Yes, with a clean-export build or a checkout without local `main`. | Yes, once for the test helper, then once for the bundler. | Resolved by resolving the integration ref for CI; no gate weakened. |
| The determinism fixture called a helper that treats a missing `origin/main` as fatal instead of using the clone's head. | `44305339722` (`e3708bf`) | Incorrect test fixture. | Yes: run the test from a detached clone. | No. | Resolved by using the cloned head as the explicit integration ref. |
| A release-safeguard test still exercised the previous hand-written acceptance format after the ledger became authoritative. | `44303515863` (`2604d55`) | Incorrect/obsolete test path. | Yes: the focused suite failed locally once the new format landed. | No. | Resolved by moving the behavioural stage checks to the execution-ledger suite. |
| A pinned acceptance helper was added to installer inputs but omitted from the archive allow-list. | `44304691592` (`acd061f`) | Packaging problem. | Yes: the export build plus pinned-input verification catches it. | Yes: the same class recurred once with `results-file.py` at `44404173257` (`acaad79`). | Resolved by packaging both helpers. |
| Export metadata was needed to reproduce archives in CI; the mode map was not itself shipped. | `44304966659` (`3f68446`) | Packaging/configuration problem. | Yes: the export build and identity comparison catch it. | No. | Resolved by shipping `export-modes.txt`. |

No infrastructure failure was observed. None of these runs changed a host. The final required run
`44404713134` at reviewed head `294caa3` passed; current `main` also contains the separately tested
close-out record.

**Small prevention change:** `release/preflight.sh` runs the existing Email Log fixture,
candidate/deployment/acceptance suites, pinned-input and bundle checks, then builds from a clean
export before a push. It is an aggregator, not a new test framework. The remaining model-dependent
step is remembering to run it; the runner does not eliminate that judgment or CI-environment drift.

## Remaining release work

- Adoption of the newer installer/tooling archive requires a separately authorised sequential deployment and generated host acceptance.
- Manual certificate renewal remains due before 17 December 2026.
- Any tag or publication needs a separate explicit release decision and approval.

This close-out corresponds to the local canonical task report in `.cline-reports/`, which remains intentionally untracked by repository policy.

END OF REPORT
