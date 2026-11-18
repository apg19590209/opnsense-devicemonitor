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

## Remaining release work

- Adoption of the newer installer/tooling archive requires a separately authorised sequential deployment and generated host acceptance.
- Manual certificate renewal remains due before 17 December 2026.
- Any tag or publication needs a separate explicit release decision and approval.

This close-out corresponds to the local canonical task report in `.cline-reports/`, which remains intentionally untracked by repository policy.

END OF REPORT
