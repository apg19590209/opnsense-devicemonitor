# Device Monitor — Project State

## Current state

Last updated: 3 November 2026

Branch: `release/2.13` (HEAD `74e1f6f`) — the released line. `baseline/2.12` (`d04739a`)
holds the recovered pre-HA 2.12 tree; `feature/async-db-v2.11` (`0ad95b0`) is the
historical v2.11 development branch.

### Current release: 2.13.2

| Item | Value |
|---|---|
| Commit | `74e1f6f` on `release/2.13`, tag `v2.13.2` |
| Payload | `release/v2.13.2-runtime.manifest`, 40 rows, staged targets 61 |
| Bundle | `dm-v2.13.2-runtime.tar.gz`, 336 261 bytes, sha256 `8fd6a7a703a63b4fa23f694d6dbd9d0aa50947f60ce23f37ffbd2c67a6b16f5a` |
| Deployed | `192.168.20.23` (testbed), `.253` (CARP master), `.252` (CARP standby) — 40/40 manifest parity on each |
| Rollback | `/var/backups/devicemonitor/install-v213.{6KTQFY,.HuGjkL,.ivbMZd}` |
| Gates | 16 of 16 green, including `test_service_ageing`, `test_carp_role_gate`, `test_language_acceptance` |
| New behaviour | A standby ages its own inventory: `[SERVICES] Stale-state ageing (standby)` (Decision 60) |

Lineage: `2.13` (`59d6d08`, no O4 ageing, never tagged) → `2.13.1` (`19f8d4d`, tag
`v2.13.1`, O4 restored, Decision 59) → `2.13.2` (`74e1f6f`, tag `v2.13.2`, standby ageing,
Decision 60).

## O4 divergence closed: ageing restored in 2.13.1 (3 November 2026)

The section above ("O4 ageing is absent from the running 2.12 line") is **closed**. The
restore shipped as 2.13.1 (`19f8d4d`, tag `v2.13.1`) and is running on all three nodes;
`tests/test_service_ageing.py` is green and the suite is 15 of 15. Decision 59 carries
the full record, including the correction to Decision 57 about when a standby starts
suppressing observation.

### Deployment records

| When | Version | Node | Result | Backup |
|---|---|---|---|---|
| 3 Nov 2026 00:01 | 2.13 | `.23` | INSTALL_OK files=61 | `install-v213.f0Psxp` |
| 3 Nov 2026 00:06 | 2.13 | `.253` (master) | INSTALL_OK files=61 | `install-v213.8h11R7` |
| 3 Nov 2026 00:09 | 2.13 | `.252` (standby) | INSTALL_OK files=61 | `install-v213.eLrgfA` |
| 3 Nov 2026 00:24 | 2.13.1 | `.23` | first attempt ROLLBACK_ATTEMPTED (daemon start race, installer fixed), second attempt INSTALL_OK | `install-v213.bsp83b` (rolled back), `install-v213.97t9Ns` |
| 3 Nov 2026 00:29 | 2.13.1 | `.253` (master) | INSTALL_OK files=61 | `install-v213.SAA2LN` |
| 3 Nov 2026 00:31 | 2.13.1 | `.252` (standby) | INSTALL_OK files=61 | (own `install-v213.*` dir) |
| 3 Nov 2026 00:46 | 2.13.2 | `.23` | CHECK_OK then INSTALL_OK files=61 | `install-v213.6KTQFY` |
| 3 Nov 2026 00:47 | 2.13.2 | `.253` (master) | INSTALL_OK files=61 | `install-v213.HuGjkL` |
| 3 Nov 2026 00:48 | 2.13.2 | `.252` (standby) | INSTALL_OK files=61 | `install-v213.ivbMZd` |

2.13.2 standby evidence: `.252` logs `[SERVICES] Stale-state ageing (standby): aged 1 row(s) to unknown, retired 0 row(s)` at 00:49:34, the first ageing cycle it has ever run while refusing service observation; `.253` keeps ageing on the discovery gate as before.

Post-deployment reconciliation: all 40 manifest rows hash-match on each node; `.253` logs
`Stale-state ageing: aged 1 row(s) to unknown, retired 0 row(s)`; standby dry-run `0/0`;
testbed backlog `38/42` (monitoring disabled there, left in place).
