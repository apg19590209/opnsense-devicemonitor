# FINAL REPORT — v2.15.1 release approval package

**Status: ACCEPTED — candidate-bound installation passed on `.23`, `.252` and `.253`.**
Ready for approval of merge, tag and publication; none has occurred.

## Candidate

- Archive: `dm-v2.15.1-runtime.tar.gz`
- SHA-256: `5391535a9f64792ddfc23f096b437293ce37daf47fd60dad4a49b90a47bf20ab`
- Size: 12,562,386 bytes
- Members: 96
- Build source: `bbfc69fdd2a713825f17ad070c6a72d774388ed1`
- Corrected local deployment wrapper: `5cdfc5d96f26b4342ffc6d06f2362c9388d06bd0`,
  SHA-256 `0c41b1dd3e50e45ef919665a056d88eed6653dd68b9507c114f19e346da44c6b`

## Validation

- Wrapper exact-head CI `44515852385`: SUCCESS.
- Release preflight: PASS.
- Deterministic archive reproduced byte-identically from worktree and clean export; CI also
  passed two-checkout bundle determinism.
- Manifest: 51 runtime rows; installer record: 70 targets on every node.
- All 12 accepted predecessors pass, including 2.15.0.

## Host Acceptance

| Stage | Role | Installer backup | Checks |
|---|---|---|---|
| `.23` | Testbed | `/var/backups/devicemonitor/install-v214.pLnRXe` | 12/12; peer N/A |
| `.252` | BACKUP/100 | `/var/backups/devicemonitor/install-v214.HrmR8F` | 13/13 incl. peer/authenticated |
| `.253` | MASTER/0 | `/var/backups/devicemonitor/install-v214.6wmHxZ` | 13/13 incl. peer/authenticated |

Each stage reported `INSTALL_OK version=2.15.1 files=70 core_locales=9 pruned=0` with
`unchanged=68 repaired=0`. The two changed targets are the reviewed service runtime and version
metadata. Device Monitor settings, functional OPNsense configuration, database counts/integrity,
certificate fingerprints and daemon health were preserved. Temporary accounts, API keys and
credential files were removed. Reciprocal peer reads passed.

Evidence:
`/var/backups/devicemonitor/acceptance-v2.15.1-ha-20261119T120038Z/`

Evidence manifest SHA-256:
`395ec5b06b570b4afd7893b9579f997de1e3c544631800f114253c3b4800bbd5`

## Remaining Limitations

Live ageing validation, shared-IP retention, DHCP newest-row ownership and the historical
unreproduced churn remain open.

## Publication Approval Requested

Approve merging PR #17 with history preserved, tagging the resulting merge commit `v2.15.1`,
and publishing `dm-v2.15.1-runtime.tar.gz` with `release/v2.15.1-checksums.txt`. Do not rebuild
or substitute the accepted archive.
