# DM-BL-011 — historical database-byte recovery search

**Status: CLOSED on 13 November 2026 by explicit operator acceptance of the historical evidence
limitation; original bytes not recovered. No retained authorised local evidence or backup contains
the historical `c17874a7…` bytes. The logical database state is verified, but physical byte identity
cannot be reconstructed from the files currently retained. This record makes no byte-identity claim.**

## Search scope and method

The search was read-only. Database hashes were computed from existing files and archive members;
no retained evidence, backup or live host path was modified. The roots searched were:

- `/root/dm-validation-2140`
- `/root/dm-pre-2140`
- `/root/dm-pre-2133`
- `/root/dm-os-26.7.8-preupdate`
- `/root/dm-os-26.7.8-verify-extract`
- `/root/devicemonitor_backup`
- `/root/dm-restore`
- `/root/dm-backups`
- `/var/backups/devicemonitor`

The wider candidate set contained 128 physical files named `devices.db*` or `*.db`; the narrower
`devices.db*` set contained 91 files. All 67 archive files under those roots were scanned for
`devices.db` members: 22 from the primary evidence roots and 45 supplemental release/evidence
archives under `/root/dm-backups`. The exact target was:

```text
c17874a717cebe2c2e1dbaf537fd13a65b4ded47e10dfcce1849f2088136144e
```

## Results

```text
physical_db_candidates=128
exact_physical_hits=0
primary_archives_scanned=22
supplemental_backup_archives_scanned=45
archives_scanned_total=67
archive_members_with_devices_db=14
archive_exact_hits=0
textual_reference_files=29
supplemental_backup_text_references=270
```

The supplemental `/root/dm-backups` tree contained no physical `devices.db*` candidate and no
archive member named `devices.db`; its 270 textual references are preserved backup copies of
project records that quote the digest, not database bytes.

Every retained database copy that could be identified is either the consistent snapshot
`796d28c7b8c5fd0b8442f74a4bca843b518d9e5b2a8db9f3fe7e5f0860d11f3d` or an older unrelated state.
The older `/var/backups/devicemonitor/devices.db.pre-monitor-scan-20260923-070801` is
`65e11a3b…`, not the 6 November original. Archive members that contained `devices.db` also hashed
to `796d28c7…`.

The 29 textual hits are audit records that quote the digest, for example
`/root/dm-pre-2140/pre-state.txt`,
`/root/dm-os-26.7.8-preupdate/system-info/summary.txt`,
`/root/dm-validation-2140/live-rollback-20261105T231701Z/final-acceptance.log` and
`/root/dm-validation-2140/db-hash-analysis-20261106T092138Z/TRACE.txt`. They contain the expected
hash but not the database bytes.

## Controlled transformation attempts

Working only on temporary copies of the retained `796d28c7…` file, the following ordinary SQLite
operations were tried and did not produce `c17874a7…`:

```text
VACUUM                        700de9227b5c3d4e6bf5ae9c8b65793bf2e3211763422f619a9446b4cae7dd70
VACUUM INTO                    e03cf10a6febc2642120e2714fec3689b632a25c51aa03f880e064b7ed16efe7
PRAGMA optimize                54806ac4d1d1bc81c8c4cbed25bb51e2e679ac1a83394bcf12ef6bc2851e8982
```

The retained file is 258,048 bytes, page size 4,096, 63 pages, 3 free pages and
`journal_mode=delete`. The observed result is a stable logical snapshot, not the original physical
layout. No transformation with an observed match was found.

## Recovery assessment

- Recovery from retained files or archives: **not possible** with the evidence checked.
- Reconstruction from the other retained bytes: **not demonstrated**; the original header/page map
  was not retained and the controlled transformations did not match.
- Raw-disk undelete/forensics was not attempted: it is outside the authorised local evidence scope
  and would not be a safe or auditable substitute for an original retained copy.
- The closure paths were a newly discovered original-byte copy or an explicit operator decision
  accepting the historical physical-byte limitation. The second path was exercised on 13 November
  2026.

The corrected guard prevents recurrence and the Phase 2A rehearsal proves exact restoration on
future runs; neither fact retroactively reconstructs `c17874a7…`. DM-BL-011 is **CLOSED** on the
basis recorded below.

## Closure — 13 November 2026

The operator explicitly accepted that the historical recovery cannot be proven byte-identical.
Logical restoration was verified, and the byte-preserving guard was corrected and tested. The
original `c17874a7…` physical bytes remain unavailable; the retained state is `796d28c7…` and the
logical digest evidence is `10460718…`.

This is an accepted historical evidence limitation, not a current recovery defect. No historical
byte-identity claim is made. DM-BL-011 is **CLOSED**.
