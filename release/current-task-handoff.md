# Current task handoff

Objective: deliver the corrected v2.15.0 Email Log acceptance package and run its staged acceptance.

Authority: Tony approved c3b6a723... (source f86d2b8); push and CI were authorised. The replacement 3a2dacc2... has no approval and must not be installed until explicitly approved. c3b6a723... is superseded (role check ignored advskew) and must not be installed.

Pinned hosted archive: b4e388ac86f03e0bead0cceae0f74a7b2a480457eb26d20998183ea59f208e72 (hosts stay on it)
Superseded candidate: aa1270ededce9935b0a77bdd610c54a8bbc29c8b8e71d66fc040641db51f0f3f (source b0e8355) - defective runner; never install
Proposed candidate (awaiting approval): 3a2dacc256b92977e5cc9f2fbb1f22186b8c0b3ba8b3589940e8f66e4a782dd5, 12557266 bytes, 96 members (source f86d2b88b0dd7bd6efd6d4e4cd51b9d85cfd03c4)

- .23: this session runs on .23; no acceptance for 3a2dacc2...; install held pending approval (local filesystem and API verification available)
- .252: no acceptance for 3a2dacc2...; incident reconciled, records preserved
- .253: no acceptance for 3a2dacc2...; MASTER/0 unchanged

Outstanding checks: explicit approval of 3a2dacc2...; snapshots then `--host local` installation on .23, then .252/.253 over SSH, then `python3 release/execution-ledger.py status`. CI 44430535745 passed at b7e3550; the local-target dispatcher correction (32f8872) needs CI. API account: dm-test-202611191013 removed, cleanup verified.

Stop conditions: price gate premium without approval; missing access; unsafe verification failure; any archive or source substitution.

Deployment order: .23, then .252, then .253. Rollback: the prepared supported rollback plus the per-host installer backups.
