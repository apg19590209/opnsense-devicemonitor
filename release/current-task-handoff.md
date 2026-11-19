# Current task handoff

PR #17 carries the v2.15.1 service-presence and atomic-retirement candidate accepted on `.23`,
`.252` and `.253`.

- Branch: `fix/service-retirement-atomic-20261119`; reviewed correction commits through `b01712c`.
- Identity source: `bbfc69fdd2a713825f17ad070c6a72d774388ed1`.
- Candidate: 96 members, 12,562,386 bytes, SHA-256
  `5391535a9f64792ddfc23f096b437293ce37daf47fd60dad4a49b90a47bf20ab`.
- The candidate was reproduced byte-identically from the worktree and a clean exported tree.
- Corrected local-dispatch wrapper: `5cdfc5d96f26b4342ffc6d06f2362c9388d06bd0`, SHA-256
  `0c41b1dd3e50e45ef919665a056d88eed6653dd68b9507c114f19e346da44c6b`; CI `44515852385` passed.
- `.23` acceptance: `CHECK_OK`/`INSTALL_OK` version 2.15.1, 70 targets, zero prunes, 68 unchanged;
  installer backup `/var/backups/devicemonitor/install-v214.pLnRXe`.
- Generated host checks and authenticated checks passed; temporary API account/key and credential
  file were removed. Data counts, settings, functional OPNsense configuration and certificate
  remained preserved.
- `.252` is BACKUP/advskew 100; installer backup `/var/backups/devicemonitor/install-v214.HrmR8F`.
- `.253` is MASTER/advskew 0; installer backup `/var/backups/devicemonitor/install-v214.6wmHxZ`.
- Reciprocal peer reads passed after both HA stages.
- Published v2.15.0 manifests, checksums, tag and assets are unchanged.
- No merge, tag or publication is claimed.
