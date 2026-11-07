# Device Monitor 2.14.0 — Phase 1 exact-candidate validation on `.23`

## Result

The exact 2.14.0 candidate was checked and installed once on the `.23` testbed as a same-version
repair. The installer and all Phase 1 acceptance gates passed. Monitoring and notification
delivery remained disabled. No source, commit, push, tag, release, production or `.252`/`.253`
change occurred. Publication remains paused.

One limitation is explicit: the authenticated Device Monitor UI was not observed in this run. The
installed model version and the unauthenticated login endpoint were checked, but no authenticated
UI claim is made.

## Candidate and baseline

| Item | Value |
|---|---|
| Host | `.23` / `OPNsense.internal`, OPNsense `26.7.8_2` |
| Candidate | `dm-v2.14.0-runtime.tar.gz`, 1,729,177 bytes |
| Candidate SHA-256 | `90afa55dd826c0dc3be8a23902b809baa465e25191dc372dc6cc2ef4e57fc243` |
| Accepted `/conf/config.xml` | `e86a7058b894a3cea6d63e4edee420885e9dc3d136ad72f054aa9c1f6b5f0e72` |
| Installed predecessor | `2.14.0` |
| Monitoring | `enabled=0`; empty `monitored_interfaces`; email/webhook delivery disabled |
| Recovery evidence | `/root/dm-validation-2140/phase1-90afa55d-20261107T104937Z/` |

The preflight verified the archive size and digest, `SHA256SUMS`, the accepted configuration hash,
the 63-row install record, SQLite integrity and journal mode, the 19 core-locale state files,
monitoring-disabled settings, no CARP interface, no WAL/SHM, no `2525` listener, a clean Git
Backup repository, no active Git Backup/ACME process, and sufficient free space. The final
pre-mutation gate passed immediately before installation.

## Check and install

The non-mutating check produced:

```text
VERIFY_OK=4
NOTICE: merged the plugin keys into 10 core catalogue(s); uninstall.sh restores the pristine files
CHECK_OK version=2.14.0 predecessor=2.14.0 files=63 core_locales=10 prunable=0 daemon_running=1 host=OPNsense.internal legacy_prunable=0 retained=0
```

The normal same-version repair produced:

```text
BACKUP_READY=/var/backups/devicemonitor/install-v214.Uwwqu1
CORE_LOCALE_STATE_BACKED_UP=present files=19
UNCHANGED=63
INSTALL_OK version=2.14.0 files=63 core_locales=10 pruned=0 backup=/var/backups/devicemonitor/install-v214.Uwwqu1 daemon_restarted=1 unchanged=63 repaired=0
```

No warning, `ABORT`, failed step or rollback status appeared in the install transcript. The
installer performed the real `configd` restart and Device Monitor stop/wait/start lifecycle.

## Recovery assets

The recovery set under the evidence root contains a consistent SQLite backup, Device Monitor
configuration, install record, `/conf/config.xml`, the 19 core-locale state files, target
pre-state metadata and an installer-backup reference. The assets were extracted and independently
verified; SQLite `quick_check` and `integrity_check` are `ok`.

| Asset | SHA-256 |
|---|---|
| `pre-state.tgz` | `7a000f2e0391dfd1a71004543228964ad910f2ed2c538dbfc7c4c6f70d8a8b8e` |
| `installer-backup-reference.tgz` | `3668a1ea85b32d9d084171ff6939723772281c966795c485adeb6be33f5932e8` |

The installer backup-reference archive matches the preserved `install-v214.qMPS7n` directory
byte-for-byte. Existing `JeYC44`, `zGJRuq` and `qMPS7n` backups remain present. The new installer
backup is `/var/backups/devicemonitor/install-v214.Uwwqu1`; its `plan` has 63 rows and its database
passes both SQLite integrity checks.

## Acceptance evidence

| Gate | Result |
|---|---|
| Release manifest | 42 rows; every target matches digest, mode, owner `root` and group `wheel` |
| Installer plan / record | 63 rows each; identical target set and digests |
| Locale paths | 11 sidecar `.mo`, 2 source `.po`, and 10 merged core `.mo` paths (21 `.mo` locale rows) |
| Catalogue compilation | 10 core and 11 sidecar catalogues compile warning-free |
| Catalogue headers | All 10 core catalogues contain non-empty `PO-Revision-Date`, `Last-Translator` and `Language-Team` |
| Translation preservation | All nine available pristine core catalogues retain their prior translations; `nl_NL` had no pristine core catalogue and is plugin-only as expected |
| Configuration | `/conf/config.xml` remains `e86a7058…`; Device Monitor `config.json` remains `027594eb…`; no ACME/Git Backup metadata change |
| Database | Logical digest `d7ed7f816c414387bf136d2782ac6c2e1e3e6c08e8c302ae924726d77adb2479` before and after; physical bytes `796d28c7…` also unchanged; `quick_check=ok`, `integrity_check=ok`, journal mode `delete` |
| Install record | `d891ce68…`, 63 rows; core-locale state has 19 unchanged files |
| Services | Daemon PID `16776` → `18384`, alive at 60 seconds; configd PID `728` → `328`; `configctl devicemonitor status` is `running` |
| Monitoring | `enabled=0`, empty interfaces, email/webhook disabled, no WAL/SHM, no `2525` listener, no CARP interface |
| UI source | Installed `defaults.json` version is `2.14.0`; unauthenticated login endpoint returned HTTP `200`; authenticated UI was not observed |

The live run exercises the new merge helper against the current `.23` catalogues and confirms
warning-free output, but all 63 installed targets were already byte-identical (`UNCHANGED=63`).
It therefore does not demonstrate a live sparse-header repair delta; that repair remains covered by
the DM-BL-010 regression and disposable-jail evidence.

## Gaps closed and remaining

Closed by this phase:

- Live same-version repair of the exact 1,729,177-byte candidate on `.23`.
- Live warning-free catalogue merge and header presence on the current ten core catalogues.
- Translation preservation for the nine available pristine core catalogues; `nl_NL` absent as expected.
- Manifest, 63-target, data/config, SQLite, service-restart and monitoring-disabled acceptance.
- Recovery-asset creation and independent verification.

Remaining:

- **DM-BL-011:** historical database-byte identity remains unresolved; this phase proves the current
  pre/post bytes and logical content, not the historical `c17874a7…` bytes.
- **DM-BL-012:** real-host `FRESH=1` and real OPNsense plugin registration/lifecycle remain
  unvalidated.
- **DM-BL-013:** full monitoring lifecycle, HA/CARP and daemon-generated/external delivery remain
  unvalidated.
- Authenticated Settings → About/Features UI rendering was not observed; no such claim is made.
- Sparse-header live repair is not a delta in this run because the live targets were already
  complete; regression/jail evidence remains the proof for that path.
- Publication of 2.14.0 remains paused; v2.12.1 remains the latest published release. Issue #5
  remains **OPEN**. DM-BL-010 remains integrated in `main` but publication-pending.

## Boundaries

No monitoring activation, notification delivery, `FRESH=1`, production or `.252`/`.253` contact,
VM creation, commit, push, tag, release or issue reply occurred. The only writes were the authorised
`.23` repair, its recovery/evidence files and project records.
