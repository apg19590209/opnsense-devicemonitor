# Deployment plan — Device Monitor 2.13.3 to the `.23` testbed

**Status: NOT EXECUTED.** This is the gated phase that follows code review and a green CI
run. Scope is `192.168.20.23` only. `.253` (CARP master) and `.252` (CARP standby) are
explicitly out of scope for this phase and must not be touched.

Branch under test: `fix/pruning-remediation-20261103`.
Bundle: `dm-v2.13.3-runtime.tar.gz`, 346 013 bytes,
sha256 `3131b8b481a5a6723d1733b214c118921def77e003863fcf4816e0b278caf9cb`
(build it from the branch with `release/build-bundle.sh`; the 2.13.2 bundle is untouched).

## 0. Authorisation gate

* CI on the branch is green, including `test_upgrade_predecessors.py` with `skipped=0`.
* The reviewer has signed off on `verification/PRUNING_REMEDIATION_20261103.md`.
* The operator has confirmed the window: no other change is in flight on `.23`, and the
  CARP pair is not being upgraded in the same window.
* The 2.13.3 tarball digest above matches what was reviewed. If the tarball is rebuilt, the
  digest changes and this plan must be reissued.

## 1. Preflight (read-only)

```sh
cd /root/src/opnsense-devicemonitor-upstream            # authoritative checkout
git rev-parse --abbrev-ref HEAD                        # fix/pruning-remediation-20261103
git status --porcelain                                 # empty
sha256 -q /tmp/dm-v2.13.3-runtime.tar.gz               # 3131b8b4...

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

```sh
mkdir -p /root/dm-pre-2133
tar -czf /root/dm-pre-2133/runtime-data.tgz /var/db/devicemonitor
sha256 -q /root/dm-pre-2133/runtime-data.tgz             # record the digest
tar -tzf /root/dm-pre-2133/runtime-data.tgz | head      # devices.db, config.json, installed-manifest.txt
cp -p /var/db/devicemonitor/installed-manifest.txt /root/dm-pre-2133/installed-manifest.txt
sha256 -q /var/db/devicemonitor/devices.db              # must be identical after the install
```

The installer's own rollback directory (`/var/backups/devicemonitor/install-v213.<id>/`,
`files/` + `plan` + optional `prune`) is created by the run and must be kept until a clean
scan cycle has been observed.

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
INSTALL_OK version=2.13.3 files=61 core_locales=10 pruned=0 backup=/var/backups/devicemonitor/install-v213.<id> daemon_restarted=1 unchanged=60
```

`files=61` and `pruned=0` are mandatory. `unchanged=60` is expected because only
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

The installer rolls itself back on any abort (replaced targets first, then pruned files,
every restore digest-verified) and prints `ROLLBACK_ATTEMPTED=<backup>`. If a rollback is
needed after the fact:

```sh
BK=/var/backups/devicemonitor/install-v213.<id>          # from the INSTALL_OK line
service devicemonitor stop
sh /tmp/dm-v2.13.3/release/prune-plan.sh restore-targets --plan "$BK/plan" --backup "$BK"
[ ! -f "$BK/prune" ] || sh /tmp/dm-v2.13.3/release/prune-plan.sh restore --plan "$BK/prune" --backup "$BK"
service devicemonitor start
python3 -c 'import json;print(json.load(open("/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json"))["version"])'
                                                       # 2.13.2
```

`installed-manifest.txt` needs no restore: it is written only after a fully successful run,
so a failed or rolled-back install leaves the previous record in place. Verify it still has
40 lines and no digests after a rollback.

Hard fallback: reinstall the published 2.13.2 bundle (`dm-v2.13.2-runtime.tar.gz`, sha256
`8fd6a7a3…`; 2.13.3 accepts it as a predecessor) and restore
`/root/dm-pre-2133/runtime-data.tgz` only if `devices.db` is found damaged.

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
