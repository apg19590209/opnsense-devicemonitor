# Deployment plan — Device Monitor 2.13.3 to the `.23` testbed

**Status: NOT EXECUTED.** This is the gated phase that follows code review and a green CI
run. Scope is `192.168.20.23` only. `.253` (CARP master) and `.252` (CARP standby) are
explicitly out of scope for this phase and must not be touched.

Branch under test: `fix/pruning-remediation-20261103`.
Bundle: `dm-v2.13.3-runtime.tar.gz`, 1 656 468 bytes,
sha256 `7f389248707cf8fa0684760820db85c0fddac4b8b3964e0563318b38b2730fe2`
(the bundle identity is reproducible — `release/bundle-digest.txt` records it and
`tests/test_bundle_determinism.py` rebuilds it from two clean checkouts while
`tests/test_bundle_reproducibility.py` pins canonical tar termination and a stored-block gzip
header; Decisions 67-68 retired the earlier `ce92a09a…`, `b29e1166…` and `451a03f4…`
identities, which depended on the builder's timezone, tar termination and gzip implementation;
the archive is uncompressed by design, 1.66 MB instead of 349 KB, because determinism outranks
payload size; the 2.13.2 bundle is
untouched).

## 0. Authorisation gate

* CI on the branch is green, including `test_upgrade_predecessors.py` with
  `passed=8 skipped=0`; the branch is listed in `push.branches`, so a push triggers the full
  workflow (`workflow_dispatch` is also available).
* The reviewer has signed off on `verification/PRUNING_REMEDIATION_20261103.md` and
  `verification/REVIEW-R2-REMEDIATION-20261103.md`.
* The operator has confirmed the window: no other change is in flight on `.23`, and the
  CARP pair is not being upgraded in the same window.
* The 2.13.3 tarball digest above matches what was reviewed. Rebuilding from the same commit
  now reproduces that digest; a mismatch means a different tree, not a different clock.

## 1. Preflight (read-only)

```sh
cd /root/src/opnsense-devicemonitor-upstream            # authoritative checkout
git rev-parse --abbrev-ref HEAD                        # fix/pruning-remediation-20261103
git status --porcelain                                 # empty
sha256 -q /tmp/dm-v2.13.3-runtime.tar.gz               # 7f389248...

/bin/hostname                                          # OPNsense.internal
/usr/local/sbin/opnsense-version                       # OPNsense 26.7.7 (>= 26.1.5)
python3 -c 'import json;print(json.load(open("/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json"))["version"])'
                                                       # 2.13.2 before the run
wc -l < /var/db/devicemonitor/installed-manifest.txt    # 40 (2.13.2 bare-path record)
/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/daemon_status.sh   # running
service devicemonitor status
df -h /var                                             # room for one more install-v213.* dir
```

Dry run from the checkout — this is the exact output already observed on `.23` (see
`PROJECT_STATE.md`):

```sh
sh install-unattended.sh --host "$(/bin/hostname)" --check
```

```text
VERIFY_OK=4
NOTICE: merged the plugin keys into 10 core catalogue(s); uninstall.sh restores the pristine files
CHECK_OK version=2.13.3 predecessor=2.13.2 files=61 core_locales=10 prunable=0 daemon_running=1 host=OPNsense.internal legacy_prunable=0 retained=0
```

Abort and investigate if `prunable=` is not 0, if `retained=` is not 0, or if any
`PRUNE_PLAN=` / `PRUNE_RETAINED` line appears: on this node no file qualifies, so any
candidate means the record or the evidence disagrees with the tree.

Confirm `--check` did not mutate: no new `/var/backups/devicemonitor/install-v213.*`
directory, and `/var/db/devicemonitor/installed-manifest.txt` mtime unchanged.

## 2. Backup verification (before the install)

`devices.db` is a live SQLite database: a plain `tar` of it is not a consistent snapshot, so
it is copied with `sqlite3 .backup` (the same primitive the installer uses for its own
rollback asset) and only then archived together with the configuration and the record.

```sh
mkdir -p /root/dm-pre-2133
cp -p /var/db/devicemonitor/config.json /root/dm-pre-2133/config.json
cp -p /var/db/devicemonitor/installed-manifest.txt /root/dm-pre-2133/installed-manifest.txt
python3 - <<'PY'
import sqlite3
src = sqlite3.connect('file:/var/db/devicemonitor/devices.db?mode=ro', uri=True)
dst = sqlite3.connect('/root/dm-pre-2133/devices.db')
src.backup(dst)
assert dst.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
dst.close(); src.close()
PY
tar -czf /root/dm-pre-2133/runtime-data.tgz -C /root/dm-pre-2133 \
    devices.db config.json installed-manifest.txt
sha256 -q /root/dm-pre-2133/runtime-data.tgz             # record the digest
tar -tzf /root/dm-pre-2133/runtime-data.tgz              # devices.db, config.json, installed-manifest.txt
sha256 -q /var/db/devicemonitor/devices.db               # must be identical after the install
```

The installer's own rollback directory (`/var/backups/devicemonitor/install-v213.<id>/`,
`files/` + `plan` + optional `prune` + `installed-manifest.txt` and its `.sha256`) is created
by the run and must be kept until a clean scan cycle has been observed.

## 3. Install

```sh
cd /tmp && mkdir -p dm-v2.13.3 && tar -xzf dm-v2.13.3-runtime.tar.gz -C dm-v2.13.3 && cd dm-v2.13.3
sh install.sh --host "$(/bin/hostname)"
```

Expected lines, in this order (`<id>` is generated):

```text
VERIFY_OK=4
NOTICE: merged the plugin keys into 10 core catalogue(s); uninstall.sh restores the pristine files
BACKUP_READY=/var/backups/devicemonitor/install-v213.<id>
CORE_LOCALE_STATE=/var/backups/devicemonitor/core-locale
UNCHANGED=60
INSTALL_OK version=2.13.3 files=61 core_locales=10 pruned=0 backup=/var/backups/devicemonitor/install-v213.<id> daemon_restarted=1 unchanged=60 repaired=0
```

`files=61` and `pruned=0` are mandatory; `repaired=0` is expected (a non-zero value means
mode or ownership drift was corrected — see Decision 64 — and is not a failure). `unchanged=60` is expected because only
`defaults.json` changes between 2.13.2 and 2.13.3; a lower count is acceptable (a generated
catalogue differed) but `files=61 pruned=0` is not negotiable. No `PRUNE_PLAN=` line is
expected. Any `ABORT:` line means the installer rolled back and printed
`ROLLBACK_ATTEMPTED=/var/backups/devicemonitor/install-v213.<id>`.

## 4. Post-install verification

```sh
python3 -c 'import json;print(json.load(open("/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json"))["version"])'
                                                       # 2.13.3
/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/daemon_status.sh   # running
service devicemonitor status

# Target parity: every manifest row matches byte for byte, no output expected.
cd /tmp/dm-v2.13.3
while read -r h m s t; do [ "$(sha256 -q "$t")" = "$h" ] || echo "MISMATCH $t"; done \
    < release/v2.13.3-runtime.manifest

# The record is now the full target set with digests (61 targets + 2 comment lines).
grep -vc '^#' /var/db/devicemonitor/installed-manifest.txt                # 61
grep -c '^[0-9a-f]\{64\} ' /var/db/devicemonitor/installed-manifest.txt   # 61
grep -c '\.mo$' /var/db/devicemonitor/installed-manifest.txt              # 21 = 11 plugin + 10 merged core

# Data untouched.
sha256 -q /var/db/devicemonitor/devices.db             # equals the pre-install digest
python3 -c 'import sqlite3;c=sqlite3.connect("file:/var/db/devicemonitor/devices.db?mode=ro",uri=True);print(c.execute("PRAGMA quick_check").fetchone()[0])'
                                                       # ok

# The daemon still produces its ageing line (Decision 60, unchanged by 2.13.3).
tail -50 /var/log/devicemonitor.log | grep -E 'Stale-state ageing|Scan complete'
```

Acceptance: version 2.13.3, no manifest mismatch, record has 61 digest rows including 21
`.mo` paths, `devices.db` digest unchanged, `quick_check` ok, daemon running.

## 5. Rollback

The installer rolls itself back on any abort — replaced targets, then pruned files, then the
install record — with every restore digest-verified, and prints
`ROLLBACK_ATTEMPTED=<backup>`. If a rollback is needed after a *successful* install, use the
installer's own preserved assets. This is the only supported procedure: the published 2.13.2
bundle cannot be used, because its installer accepts only `2.8 … 2.13.1` and aborts with
`unsupported predecessor 2.13.3`.

```sh
BK=/var/backups/devicemonitor/install-v213.<id>          # from the INSTALL_OK line
sh /tmp/dm-v2.13.3/release/prune-plan.sh restore-targets --plan "$BK/plan" --backup "$BK"
[ ! -f "$BK/prune" ] || sh /tmp/dm-v2.13.3/release/prune-plan.sh restore --plan "$BK/prune" --backup "$BK"
sh /tmp/dm-v2.13.3/release/prune-plan.sh restore-record \
    --record /var/db/devicemonitor/installed-manifest.txt --backup "$BK"
service devicemonitor restart
python3 -c 'import json;print(json.load(open("/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json"))["version"])'
                                                       # 2.13.2
```

Each step prints `ROLLBACK_RESTORED=<path>`, `RECORD_RESTORED=<record>`, a
`ROLLBACK_SUMMARY=restored=<n> skipped=<n> conflicts=<n> failed=<n>` line, or a
`ROLLBACK_FAILED=`/`ROLLBACK_CONFLICT=` line; the installer reports
`ROLLBACK_STATUS=COMPLETE|INCOMPLETE` for the automatic path; any `ROLLBACK_FAILED` means the node is not
back at its pre-install state and the runtime-data backup is the next step. The record
restore matters: without it the node keeps a 2.13.3 record describing files it no longer
has, which the next run would treat as unverifiable (`RETAINED modified`) rather than
replacing the target set.

`prune-plan.sh backup-record` already put the previous record into `$BK` before the first
mutation, so this works for a manual rollback. A *fresh* install has no previous record:
`restore-record` then removes the one the run created (`RECORD_REMOVED=`).

Rebuild the data only from `/root/dm-pre-2133/runtime-data.tgz` if `devices.db` is found
damaged (that archive must be taken with the daemon stopped or via `sqlite3 .backup` — a
plain `tar` of a live database is not a consistent snapshot).

## 6. Stop conditions

Do not install if: the bundle digest differs, `--check` shows any prune candidate or
`RETAINED` line, the daemon is not running before the run, `/var` lacks space, or the
runtime-data backup digest cannot be re-verified. Roll back if: `INSTALL_OK` is absent,
`MISMATCH` lines appear, `quick_check` is not `ok`, the daemon does not stay up, or
`devices.db` changes digest.

## 7. What this phase must not do

* No change to `.253` or `.252` in any form (no install, no restart, no config edit).
* No publication of a v2.13.3 tag or GitHub release in this phase.
* No deletion of `/var/backups/devicemonitor/install-v213.*` or `/root/dm-pre-2133`.
