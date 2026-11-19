# Current task handoff

Objective: prepare the v2.15.0 Email Log release approval package; no deployment, tag or publication is authorised.

Authority: local commits and release-candidate construction only. Hosts remain on the separately accepted runtime archive; no stage is authorised in this package.

Pinned hosted archive: b4e388ac86f03e0bead0cceae0f74a7b2a480457eb26d20998183ea59f208e72 (hosts stay on it)
Superseded candidate: aa1270ededce9935b0a77bdd610c54a8bbc29c8b8e71d66fc040641db51f0f3f (source b0e8355) - defective runner; never install
Corrected candidate: c3b6a723f20969ec63c25032abf2dfbd235345ea0c28891185cbe41929c7f16c, 12556754 bytes, 96 members (source 589ed0001fa4ed428805f19e02c42af3c3487fdb)

- .23: historical acceptance marker exists; no generated-evidence ledger record
- .252: historical acceptance marker exists; no generated-evidence ledger record
- .253: historical acceptance marker exists; no generated-evidence ledger record

Outstanding checks: exact-head CI after a push (needs explicit instruction); generated acceptance
per host for c3b6a723...; then `python3 release/execution-ledger.py status`. Nothing is installed
from the corrected archive and no COMPLETE claim may rest on the older markers.

Decision required: approve c3b6a723... and authorise guarded .23 -> .252 -> .253 acceptance;
see release/RELEASE-APPROVAL-PACKAGE-2.15.0-20261119.md.

Stop conditions: price gate premium without approval; missing access; unsafe verification failure; action outside authority.

Deployment order: .23, then .252, then .253; the earlier report text was corrected without redeployment.
Current correction: the accepted host archive is b4e388ac; the prevention-tool archive f02bc9a8 is not deployed.
