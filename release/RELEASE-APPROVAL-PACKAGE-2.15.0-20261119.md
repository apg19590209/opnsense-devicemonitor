# FINAL REPORT — Email Log release approval package

**Status: APPROVED — INSTALLATION BLOCKED BEFORE .23 WRITE (ROLE-CHECK FORMAT DEFECT).** Approval for archive `3a2dacc2…` (source `d2e3c4f`) with tool `0f17f282…` was granted on 19 November 2026. Pre-install snapshotting was done on `.23`; no installation ran and no acceptance exists. The shipped `role_check` matches `carp: (BACKUP|MASTER) vhid N advskew N`, but FreeBSD prints `carp: BACKUP vhid 1 advbase 1 advskew 100`, so the approved deployment identity would FAIL the `.252` role check. Promotion was stopped; the tool must not be changed under this approval.

**Earlier status (preserved): BLOCKED (APPROVED ARCHIVE DEFECT; NO PROMOTION).** The v2.15.0 approval package and exact-head CI are complete. An unauthorised ad hoc `.252` move of `email_log.db` was reconciled: the original file was restored from the pre-incident consistent snapshot and verified byte-identical (`de99a51c…`, two records/five events), with authenticated reads and integrity checks passing. The approved archive was then installed on `.23`; the post-install result collector exposed a separate tooling bug, so host acceptance is not yet recorded and `.252`/`.253` promotion has not begun. No tag or publication occurred.

The approved `aa1270ed…` archive cannot produce generated acceptance. It was reproduced byte-for-byte from its own source `b0e8355`, and its packaged runner aborts under `set -u` with `RESULT_ARGS: parameter not set`. The later committed fix was incomplete: it resolved its helpers beside the invoking script (outside `release/` on an installed host) and returned a failing check's status under `set -e`, which aborted before the evidence file was written. Separately, `3dac69c` pinned `release/build-bundle.sh` in `release-inputs.sha256` while removing it from the archive allow-list, so every such archive failed `verify-release-inputs.sh` (CI run `44419526545`).

A second defect was found in the approved cut `c3b6a723…` (source `f86d2b8`): its `role_check` only grepped `carp: BACKUP`/`carp: MASTER`, so a node with the wrong advskew still passed. That identity is superseded and must not be installed; approval for it does not transfer.

The corrected candidate is a tooling-only change; no runtime application file changed.

- Runtime identity: the 51-row `release/v2.15.0-runtime.manifest` (unchanged by this candidate).
- Archive build source: **`d2e3c4f16415f8c70a769c3ddc927c9cfb124541`** — the immutable source named in the archive's identity file. The tree at that source is the `f86d2b8` code with the CARP-advskew `role_check`; commits after it are tests, identity records and deployment tooling, which build the same archive.
- Archive: **`dm-v2.15.0-runtime.tar.gz`**, **12,557,266 bytes**, SHA-256 **`3a2dacc256b92977e5cc9f2fbb1f22186b8c0b3ba8b3589940e8f66e4a782dd5`**, 96 members, builder not packaged.
- Built from a clean archive export of that source with the merged bundler under the declared build conditions (`TZ=UTC0`, canonical ustar, fixed ownership and mtime, deterministic gzip). The identity equals `release/bundle-digest.txt`, is reproduced by independent clean checkouts, and equals the export build from the local full preflight.
- Packaged-path sandbox checks (isolated fixtures; no host contacted and no host acceptance implied): the runner executed straight from the archive's bytes. `.23` passed all 12 checks. `.252` recorded all 13 checks with `peer` PASS; its `role` check passes with `carp: BACKUP vhid 1 advskew 100` and fails with the MASTER line or advskew 0. `.253` passes with `carp: MASTER vhid 1 advskew 0` and fails with the BACKUP line or advskew 100. A genuine FAIL is recorded and exits non-zero without losing the evidence file.
- The deployment gate accepts this identity for `.23` (`DEPLOYMENT_CHECK_OK`) and refuses `.252` before `.23` acceptance exists for it.
- Deployment tool: `release/deploy-candidate.sh`, SHA-256 `0f17f2820158c8cad06ecedd4905c8faae089a9359930dc25c4ad72da22f5e5e`. It is run from the checkout, not packaged. Its local target (`--host local`, hostname and management address) is proven by fixtures; `.252`/`.253` stage the verified toolchain at `/var/tmp/dm-release-tools/<source>` and install through SSH (`DM_SSH`), refusing `.252`/`.253` without it.
- Pre-package tools outside the install: `release/record-acceptance.sh`, `release/record-bundle-identity.py`, `release/preflight.sh`. Runtime identity is the 51-row manifest; archive identity is above; deployment-tool identity is recorded separately and neither implies the other.

**CI:** run `44437667465` passed at `d29b990`, which contains the local/SSH deployment tool (`19b44e3`) and these records; the tree rebuilds to the same `3a2dacc2…` bytes. Earlier heads: `44430535745` at `b7e3550`, `44430176957` at `ada0f8e`.

**Acceptance:** not started; installation is held pending approval of this identity. This session runs on `.23` (`OPNsense.internal`, `192.168.20.23`), where SSH to itself is refused; the deployment gate now maps `--host local` to `.23` only when the hostname and management address both match (`32f8872`), so installation, backups and checks run locally through the same gate. The authorised scoped account passed authenticated search, message, CSV and mutation denial against `https://192.168.20.23` and was then removed (`ACCOUNT_REMOVED`, zero `dm-test-*` users, credential file deleted, absent from its path and from /root and /tmp). `.252` and `.253` remain unchanged and SSH-only.

**Approved:** installation and staged acceptance of `3a2dacc2…` (source `d2e3c4f`) with tool `0f17f282…` (revision `19b44e3`), `.23` local → `.252` BACKUP/100 → `.253` MASTER/0 (Tony, 19 November 2026). Held pending a corrected role check and a new approval reference.

## Proposed version

**2.15.0** is the next minor release. The published release is v2.14.0. This candidate adds the Email Log feature, peer viewing, message formatting and release tooling; it preserves the v2.14.0 payload under a new version identity. The repository's earlier intended framing for this feature was also v2.15.0; that defective candidate (`15c5735`) remains quarantined and is not this package.

## Pinned candidate

- Candidate source: **`b0e8355c3b67d3845c9fcac3edc5ec23223c7095`**.
- Archive: **`dm-v2.15.0-runtime.tar.gz`**, **12,554,194 bytes**, SHA-256 **`aa1270ededce9935b0a77bdd610c54a8bbc29c8b8e71d66fc040641db51f0f3f`**, 96 members.
- The archive was generated by the merged bundler from a clean export; two independent builds of the candidate were byte-identical.
- Package records: `release/v2.15.0-runtime.manifest`, `release/manifests/v2.15.0-runtime.manifest`, `release/v2.15.0-notes.md`, `release/v2.15.0-acceptance-requirements.md` and `release/v2.15.0-checksums.txt`.

## Completed checks

- Release manifest: 51/51 rows match current source files; the 51-row baseline is retained for removal protection.
- Pinned release inputs: 21/21 verify.
- Merged preflight passed at source `b0e8355`: Email Log fixture, release/deployment safeguards, execution ledger, release inputs, bundle safety, reproducibility and determinism, and the clean-export build.
- Runtime checks reused from the accepted recovery build: Email Log authenticated listing, message retrieval and CSV; restricted mutation denial; database integrity and preserved records; settings, catalogue, daemon and HA role checks. Those checks were performed against the runtime from the `038f44c` recovery line, which is the same runtime feature set embodied here.
- The prior installer/tool archive `be2b64ca…` was not transferred to this release identity; its evidence is separate.

## Remaining acceptance requirements

Fresh acceptance is required for archive **`aa1270ed…`**. The installed hosts remain on `b4e388ac…`; acceptance is not transferred between archive hashes. Before release, the authorised sequence must be:

1. Approve this candidate and exact hash.
2. Install sequentially on `.23` testbed, then `.252` BACKUP, then `.253` MASTER using the merged safeguards; each stage needs generated acceptance for the same hash before the next.
3. Verify installation metadata, installed hashes, catalogue loading, database integrity, settings and records, daemon health, authenticated listing/message/CSV and mutation denial; verify reciprocal peer access and `.252` BACKUP/100, `.253` MASTER/0.
4. Record acceptance from generated host results and complete the independent close-out audit; confirm temporary credentials are gone.
5. Obtain explicit release approval, then tag, publish and attach the archive plus checksums.

Manual certificate renewal remains due before 2026-12-17. Webhook destination/TLS and the parked USB finding are unchanged. No host deployment, tag or publication is included in this package.

## Incident reconciliation and staged acceptance (19 November 2026)

### `.252` database move: ad hoc command, preserved data

The move was a mistaken ad hoc SSH command from `.23`, not the release tooling. The exact command was:

```
ssh -i /root/.ssh/id_ed25519_legacy254 -o IdentitiesOnly=yes root@192.168.20.252 '/bin/sh -s' <<'EOF'
mv -f /var/db/devicemonitor/email_log.db /var/db/devicemonitor/email_log.db.pre-deploy 2>/dev/null || true
EOF
```

Its apparent purpose was to create a `/var/backups`-style copy, but it acted on the live database
in `/var/db` and was outside the deployment sequence. The session log records the command at
**2026-11-18T22:53:01.834Z**; the receiving `.252` sshd audit shows the session accepted and closed
at **09:53:01 +11:00** (22:53:01Z). A read-only inspection at **22:53:06.437Z** showed the live path
absent and the moved file present at `/var/db/devicemonitor/email_log.db.pre-deploy`, hash
`de99a51c…`, integrity `ok`, two records. The restoration command ran at
**2026-11-18T22:53:10.325Z**, verified the predecessor hash, copied it back, and rechecked
integrity `ok`, two records and the same hash at **22:53:10Z**. The receiving sshd audit shows the
copy session at **09:53:10 +11:00**.

**Preservation evidence:** the move used a same-filesystem rename and preserved the original inode
(`300504`) and `mtime` (`2026-11-18T13:43:50Z`), now visible at `.pre-deploy`; the restored live
path is a separate inode (`366590`) with identical bytes. The original file at move time was
captured before the incident in `/var/backups/devicemonitor/pre-final-b4e388ac/email_log.db.pre`
(hash `de99a51c…`). The live and moved files match that snapshot exactly: SHA-256
`de99a51c3d16fbe0db9dd5670865706b26ed39f69539d36ebbdb390097eb363d`, 40,960 bytes, two
`email_log` rows and five `email_log_events` rows (`email_log` ids 1–2, events 1–5), integrity and
quick check both `ok`. The restored state includes every record/event present in that
pre-incident snapshot; no record or event was added between the snapshot and the move.

**WAL/SHM:** both paths currently have a 32,768-byte SHM file and a zero-byte WAL. The database
was in SQLite WAL mode before and after. The SHA-256 snapshot captured before the incident and the
restored file are identical; no persistent record sat only in the WAL. The authenticator has no
history of WAL contents at the instant of the move, so I cannot prove the transient WAL state. At
the move, the separate `.db-wal` and `.db-shm` siblings were not moved with the database, and the
restoration copied only the main file. The daemon (`monitor_daemon.py`, PID 86450) and web server
remained running throughout; the daemon can start the bounded `prune_email_log.php` and
`observe_email_log.php` maintenance jobs. There is no audit or process trace proving that either
actually wrote during the 4.1-second interval; that is the remaining uncertainty. It cannot have
created a new persistent record in either path without the audit evidence above, and the final
database matches the pre-incident snapshot exactly.

**Post-restoration checks:** authenticated search returned HTTP `200` with two rows; CSV returned
`200` with a header plus two entries; message retrieval returned `200` with content available;
`delete`, `restore`, `bulkdelete`, `deleteall` and `restorebulk` all refused validation without
touching a genuine record. The temporary scoped test account was removed with its key and
credential file; its absence was verified. `devices.db` and `email_log.db` integrity remained
`ok`; the daemon remained healthy; `.252` remained BACKUP/advskew 100. `.253` remained MASTER/0.

**Cause:** this was an operator-side ad hoc error during preparation; release tooling did not
issue the move. The preflight and deployment gate contain no live database mutation, so there is
no tooling defect to fix for this incident. The subsequent `.23` installation exposed a separate,
real tooling defect: `release/run-host-checks.sh` did not initialise its result collector under
`set -u`, so the post-install gate stopped before acceptance. That bug is being corrected and
regression-tested; no acceptance was fabricated from the incomplete run.

### Staged acceptance status

`.23` installation completed from the approved archive `aa1270ed…` with backup
`/var/backups/devicemonitor/install-v214.MYgsEH` and `INSTALL_OK version=2.15.0 files=70
core_locales=9 pruned=0 unchanged=69`. The post-install result collector then failed, so no host
acceptance has been recorded and no promotion to `.252` has begun. `.252` and `.253` remain on the
previously accepted runtime and were not redeployed by this attempt.

### Final decision required — approved archive contains a defective acceptance runner

The incident itself is reconciled in the section above and did **not** lose `.252` data. The live
database and its moved predecessor both hold the original two records and five events; the
authenticated listing, CSV, message and denied-mutation checks pass. That does not close the
release sequence.

A separate tooling defect affected the approved archive. `release/run-host-checks.sh` did not
initialise its result collector under `set -u`, so `.23` installed successfully but could not
produce generated acceptance. The source fix was committed and `.23` acceptance was then recorded
against **`aa1270ed…`**. However, the archive already used for `.23` contains the defective runner;
and the corrected runner changes the archive identity. The approved hash therefore cannot be
used to complete a valid generated-acceptance sequence without either:

- approving a new archive that packages the corrected runner and repeating `.23` acceptance for
  that new identity; or
- accepting that the approved `aa1270ed…` archive has no generated-acceptance path.

The latter is not recommended and is not a release-ready state. The `.23` host remains on the
approved archive; `.252` remains on its earlier accepted runtime with preserved data; `.253`
remains MASTER/0. No promotion, merge, tag or publication was performed.

**Exact action required:** approve a corrected v2.15.0 archive built from the release branch with
the fixed runner and acceptance helper, then authorise its fresh sequential `.23` → `.252` → `.253`
acceptance. The approved `aa1270ed…` identity must not be silently substituted.

## Approval and next step

Proposed: **v2.15.0 at archive `3a2dacc256b92977e5cc9f2fbb1f22186b8c0b3ba8b3589940e8f66e4a782dd5` (source `d2e3c4f16415f8c70a769c3ddc927c9cfb124541`)** — awaiting Tony's explicit approval. Approved and still valid: `c3b6a723…` was approved, but it is superseded and must not be installed. Not installable: `aa1270ed…`. Next after approval: verified snapshots, installation and generated acceptance on `.23`, then `.252`, then `.253`.

END OF REPORT
