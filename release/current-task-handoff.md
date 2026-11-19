# Current task handoff

Objective: deliver the corrected v2.15.0 Email Log acceptance package and run its staged acceptance.

Authority: Tony approved archive 3a2dacc2... by source f86d2b8 and authorised the push, required CI and the guarded `.23` -> `.252` -> `.253` acceptance. c3b6a723... is superseded (role check ignored advskew) and must not be installed. No emails, genuine-record deletion, merge, tag or publication.

Pinned hosted archive: b4e388ac86f03e0bead0cceae0f74a7b2a480457eb26d20998183ea59f208e72 (hosts stay on it)
Superseded candidate: aa1270ededce9935b0a77bdd610c54a8bbc29c8b8e71d66fc040641db51f0f3f (source b0e8355) - defective runner; never install
Approved candidate: 3a2dacc256b92977e5cc9f2fbb1f22186b8c0b3ba8b3589940e8f66e4a782dd5, 12557266 bytes, 96 members (source f86d2b88b0dd7bd6efd6d4e4cd51b9d85cfd03c4)

- .23: no acceptance for the approved archive; superseded marker only
- .252: no acceptance for the approved archive; incident reconciled, records preserved
- .253: no acceptance for the approved archive; MASTER/0 unchanged

Outstanding checks: push and CI at the final head; then sequential generated acceptance per host for the approved hash, then `python3 release/execution-ledger.py status`.

Stop conditions: price gate premium without approval; missing access; unsafe verification failure; any archive or source substitution.

Deployment order: .23, then .252, then .253. Rollback: the prepared supported rollback plus the per-host installer backups.
