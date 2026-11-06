# Issue #5 v2.12.1 Validation Evidence

This directory is the sanitised evidence subset for the isolated v2.12.1 repair candidate. The
candidate is based on `main` commit `d5d73ed`; no 2.14.0 integration change is included.

The tested bundle is `dm-v2.12.1-runtime.tar.gz`, 1,584,271 bytes, SHA-256
`adaa2b2def784eb5d4b3f33c2b3a66b0ba4913fc16fdb6fd51d552b4fb4091bc`, with 56 members. The bundle
binary is not committed. `bundle-audit.txt`, `member-*.txt`, `build-comparison.txt` and
`focused-validation.log` record the payload and reproducibility checks. `restoration-summary.txt`
records the independent rollback comparisons, live-state preservation, service boundaries and
teardown assertions.

The six jail scenarios are `check`, `upgrade`, `fresh`, `repair`, `rollback` and `fresh-rollback`.
Their result files are included alongside the before/after snapshots for both rollback paths. The
operator authorised the full-price run and the harness's supported interactive confirmation was
answered with `y`; the gate was not bypassed or modified.

## Boundaries

The jail uses stubs for `opnsense-version`, `service`, `rc.configure_plugins` and daemon state.
Passing these scenarios proves installer behaviour and service-call boundaries, not real OPNsense
configd interaction, plugin registration, daemon lifecycle or live `FRESH=1`. No live deployment,
service change, monitoring activation, production access, tag, release or GitHub reply was part of
this validation.

The fresh-rollback result file displays `before_files=1 after_files=1` because the harness label
counts the snapshot dictionary key. The authoritative paired JSON snapshots both contain
`{"directory": "absent"}`.

## Integrity

`SHA256SUMS` covers every other file in this directory. The bundle was rebuilt twice byte-identically
before the jail run. A build from the published source commit must reproduce the same bundle bytes;
that committed-tree check and the exact-commit CI result are recorded in the project milestone
report rather than in this pre-commit evidence directory.
