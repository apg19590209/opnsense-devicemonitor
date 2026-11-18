# Current task handoff

Objective: prepare the v2.15.0 Email Log release approval package; no deployment, tag or publication is authorised.

Authority: local commits and release-candidate construction only. Hosts remain on the separately accepted runtime archive; no stage is authorised in this package.

Pinned hosted archive: b4e388ac86f03e0bead0cceae0f74a7b2a480457eb26d20998183ea59f208e72; v2.15.0 candidate: aa1270ededce9935b0a77bdd610c54a8bbc29c8b8e71d66fc040641db51f0f3f
Source: 202d6efd4c126f85393116e569e72931d936efdc

- .23: historical acceptance marker exists; no generated-evidence ledger record
- .252: historical acceptance marker exists; no generated-evidence ledger record
- .253: historical acceptance marker exists; no generated-evidence ledger record

Outstanding checks: the current execution ledger has no generated evidence for a fresh host
acceptance, so a new COMPLETE claim must not be made from the prior manually summarized records.
Run the supported checks on each authorised host and then `python3 release/execution-ledger.py
status` (requirements file and consolidated report).

Stop conditions: price gate premium without approval; missing access; unsafe verification failure; action outside authority.

Deployment order: .23, then .252, then .253; the earlier report text was corrected without redeployment.
Current correction: the accepted host archive is b4e388ac; the prevention-tool archive f02bc9a8 is not deployed.
