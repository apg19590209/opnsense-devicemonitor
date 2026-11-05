# Deployment plan — Device Monitor 2.13.3 to the `.23` testbed

**Status: EXECUTED — PASS on `192.168.20.23`, 5 November 2026.** Scope was `.23` only;
`.253` (CARP master) and `.252` (CARP standby) were not touched and remain on 2.13.2.
This document now records both the gated procedure and its actual result. Rollback was
not invoked by this deployment and therefore is not live-tested by it.

## Execution record

| Item | Result |
|---|---|
| Host baseline | OPNsense `26.7.7`, FreeBSD `15.1-RELEASE-p3`, Device Monitor `2.13.2` before the run |
| Candidate | `/root/dm-deploy-2133/dm-v2.13.3-runtime.tar.gz`, 1,656,468 bytes, sha256 `7f389248707cf8fa0684760820db85c0fddac4b8b3964e0563318b38b2730fe2` |
| Check | `CHECK_OK version=2.13.3 predecessor=2.13.2 files=61 core_locales=10 prunable=0 daemon_running=1 host=OPNsense.internal legacy_prunable=0 retained=0` |
| Install | `INSTALL_OK version=2.13.3 files=61 core_locales=10 pruned=0 backup=/var/backups/devicemonitor/install-v213.xKjyg1 daemon_restarted=1 unchanged=60 repaired=6` |
| Post-install | 40/40 manifest rows and all 61 installed targets passed digest/mode/owner/group checks; 61-digest record with 21 `.mo` targets; database and configuration unchanged; SQLite integrity `ok`; monitoring disabled |
| Service lifecycle | old daemon PID 6557 exited; new PID 31483 remained running after 60 seconds; real configd restart moved PID 71926 → 76711; `configctl devicemonitor status` returned `running` |
| Permissions | six notification scripts repaired to `0644 root:wheel` (`repaired=6`); all post-install mode/ownership checks passed |
| Rollback | not invoked; installer backup retained; this run is **not** a live rollback test |
| Pre-install backup | `/root/dm-pre-2133`, mode `0700`; `runtime-data.tgz` is 3,604,198 bytes with sha256 `dfa44d4c893fbc89c22389fc813774d8b9d123b71497ef47d73bb4aeb70ed9ba` |
| Record after install | 63 lines; sha256 `0afb4e4e68edd331f22c88ef559dd1163af0baaaba0cd77a76b3ed672c17dea7` |

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
stat -f '%z' /root/dm-deploy-2133/dm-v2.13.3-runtime.tar.gz   # 1656468
sha256 -q /root/dm-deploy-2133/dm-v2.13.3-runtime.tar.gz      # 7f389248...

/bin/hostname                                          # OPNsense.internal
/usr/local/sbin/opnsense-version                       # OPNsense 26.7.7 (>= 26.1.5)
python3 -c 'import json;print(json.load(open("/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json"))["version"])'
                                                       # 2.13.2 before the run
wc -l < /var/db/devicemonitor/installed-manifest.txt    # 40 (2.13.2 bare-path record)
/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/daemon_status.sh   # running
service devicemonitor status
df -h /var                                             # room for one more install-v213.* dir
```

Dry run from a fresh extraction — this is the exact output observed on `.23` before the
mutation (also recorded in `PROJECT_STATE.md`):

```sh
BUNDLE=/root/dm-deploy-2133/dm-v2.13.3-runtime.tar.gz
EXTRACT=/root/dm-deploy-2133/extracted
test ! -e "$EXTRACT"
mkdir -m 755 "$EXTRACT"
tar -xzf "$BUNDLE" -C "$EXTRACT"
cd "$EXTRACT"
sh install.sh --host "$(/bin/hostname)" --check
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
set -eu
umask 077
PRE=/root/dm-pre-2133
test ! -e "$PRE"
mkdir -m 700 "$PRE"

cp -p /var/db/devicemonitor/config.json "$PRE/config.json"
cp -p /var/db/devicemonitor/installed-manifest.txt "$PRE/installed-manifest.txt"
cp -Rp /var/backups/devicemonitor/core-locale "$PRE/core-locale"

find /var/backups/devicemonitor/core-locale -type f -exec sh -c \
  'for f in "$@"; do printf "%s  %s\n" "$(sha256 -q "$f")" "$f"; done' sh {} + \
  | sort > "$PRE/core-locale.sha256"

python3 - "$PRE/devices.db" <<'PY'
import sqlite3, sys
src = sqlite3.connect('file:/var/db/devicemonitor/devices.db?mode=ro', uri=True)
dst = sqlite3.connect(sys.argv[1])
src.backup(dst)
assert dst.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
assert dst.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
dst.close(); src.close()
PY

tar -czf "$PRE/runtime-data.tgz" -C "$PRE" \
  devices.db config.json installed-manifest.txt core-locale core-locale.sha256
chmod 600 "$PRE/runtime-data.tgz"
sha256 -q "$PRE/runtime-data.tgz"                         # record the digest
tar -tzf "$PRE/runtime-data.tgz"

PRE_RECORD_SHA=$(sha256 -q /var/db/devicemonitor/installed-manifest.txt)
PRE_DB_SHA=$(sha256 -q /var/db/devicemonitor/devices.db)
PRE_CONFIG_SHA=$(sha256 -q /var/db/devicemonitor/config.json)
PRE_DAEMON_PID=$(cat /var/run/devicemonitor.pid)
PRE_CONFIGD_PID=$(cat /var/run/configd.pid)
PRE_LOG_LINES=$(wc -l < /var/log/devicemonitor.log | tr -d ' ')
```

The actual pre-install archive was `/root/dm-pre-2133/runtime-data.tgz`, mode `0600`, size
3,604,198 bytes, sha256 `dfa44d4c893fbc89c22389fc813774d8b9d123b71497ef47d73bb4aeb70ed9ba`.
The containing directory is mode `0700` (14,504 KiB allocated); its recorded pre-install record digest was
`3f63e4698cb1c55352095c937563cdf3c7c255fc2b6b9754836eb4423c6abf16`.

The installer's own rollback directory (`/var/backups/devicemonitor/install-v213.<id>/`,
`files/` + `plan` + optional `prune` + `installed-manifest.txt` and its `.sha256`) is created
by the run. Keep it as a historical rollback asset; monitoring is disabled, so do not wait for a
scan cycle before retaining it.

## 3. Install

```sh
set -eu
BUNDLE=/root/dm-deploy-2133/dm-v2.13.3-runtime.tar.gz
EXTRACT=/root/dm-deploy-2133/extracted
[ "$(stat -f %z "$BUNDLE")" -eq 1656468 ]
[ "$(sha256 -q "$BUNDLE")" = 7f389248707cf8fa0684760820db85c0fddac4b8b3964e0563318b38b2730fe2 ]
cd "$EXTRACT"
sh install.sh --host "$(/bin/hostname)"
```

Key actual result lines (the repair lines are listed below):

```text
VERIFY_OK=4
NOTICE: merged the plugin keys into 10 core catalogue(s); uninstall.sh restores the pristine files
BACKUP_READY=/var/backups/devicemonitor/install-v213.xKjyg1
CORE_LOCALE_STATE=/var/backups/devicemonitor/core-locale
UNCHANGED=60
INSTALL_OK version=2.13.3 files=61 core_locales=10 pruned=0 backup=/var/backups/devicemonitor/install-v213.xKjyg1 daemon_restarted=1 unchanged=60 repaired=6
```

`files=61` and `pruned=0` are mandatory. `repaired` counts mode/ownership corrections (Decision
64), not failures. The actual run reported `repaired=6` and logged these six files repaired to
`0644 root:wheel`:

* `NotificationHandler.php`
* `notify_email.php`
* `notify_identity_email.php`
* `notify_scan_email.php`
* `notify_service_email.php`
* `notify_webhook.php`

`unchanged=60` is expected because only `defaults.json` changes between 2.13.2 and 2.13.3; a lower
count is acceptable (a generated catalogue differed) but `files=61 pruned=0` is not negotiable.
No `PRUNE_PLAN=` line is expected. Any `ABORT:` line means the installer rolled back and printed
`ROLLBACK_ATTEMPTED=/var/backups/devicemonitor/install-v213.<id>`. The actual run used backup
`/var/backups/devicemonitor/install-v213.xKjyg1`.

## 4. Post-install verification

```sh
python3 -c 'import json;print(json.load(open("/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json"))["version"])'
                                                       # 2.13.3
/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/daemon_status.sh   # running
service devicemonitor status
service configd status
configctl -w 5 devicemonitor status                                  # running

NEW_DAEMON_PID=$(cat /var/run/devicemonitor.pid)
NEW_CONFIGD_PID=$(cat /var/run/configd.pid)
[ "$NEW_DAEMON_PID" != "$PRE_DAEMON_PID" ]
[ "$NEW_CONFIGD_PID" != "$PRE_CONFIGD_PID" ]

# Target parity: every manifest row matches byte for byte, no output expected.
cd "$EXTRACT"
while read -r hash mode source target; do
    [ "$(sha256 -q "$target")" = "$hash" ] || { echo "MISMATCH $target"; exit 1; }
    [ "$(stat -f %Lp "$target")" = "$mode" ] || { echo "MODE_MISMATCH $target"; exit 1; }
    [ "$(stat -f %Su "$target"):$(stat -f %Sg "$target")" = root:wheel ] \
        || { echo "OWNER_MISMATCH $target"; exit 1; }
done < release/v2.13.3-runtime.manifest

# The record is now the full target set with digests (61 targets + 2 comment lines).
grep -vc '^#' /var/db/devicemonitor/installed-manifest.txt                # 61
grep -c '^[0-9a-f]\{64\} ' /var/db/devicemonitor/installed-manifest.txt   # 61
grep -c '\.mo$' /var/db/devicemonitor/installed-manifest.txt              # 21 = 11 plugin + 10 merged core

# Data untouched.
[ "$(sha256 -q /var/db/devicemonitor/devices.db)" = "$PRE_DB_SHA" ]
[ "$(sha256 -q /var/db/devicemonitor/config.json)" = "$PRE_CONFIG_SHA" ]
python3 - <<'PY'
import sqlite3
c = sqlite3.connect('file:/var/db/devicemonitor/devices.db?mode=ro', uri=True)
assert c.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
assert c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
c.close()
PY

python3 -c 'import json;print(json.load(open("/var/db/devicemonitor/config.json"))["enabled"])'
                                                       # 0

# Monitoring is disabled, so do not wait for an ageing/scan line. Require the lifecycle lines.
tail -n +$((PRE_LOG_LINES + 1)) /var/log/devicemonitor.log \
  | grep -E 'Daemon stopping|Daemon stopped|Daemon started|Monitoring DISABLED'
sleep 60
kill -0 "$NEW_DAEMON_PID"
```

Acceptance: version 2.13.3, no manifest mismatch, record has 61 digest rows including 21
`.mo` paths, `devices.db` and Device Monitor configuration digests unchanged, `quick_check` and
`integrity_check` ok, monitoring value `0`, old daemon/configd PIDs replaced, the new daemon is
still alive after 60 seconds, configd is responsive, and `configctl devicemonitor status` returns
`running`. Do not require an ageing or scan line while monitoring remains disabled.

## 5. Rollback

**Rollback was not invoked by this deployment.** The procedure below is the documented manual
recovery path, not live evidence from 5 November. The installer does have a separately exercised
M5 sandbox rollback scenario and rolls itself back on abort, but that does not make this
successful-install manual path a tested live rollback.

The installer rolls itself back on any abort — replaced targets, then pruned files, then the
install record — with every restore digest-verified, and prints
`ROLLBACK_ATTEMPTED=<backup>`. If a rollback is needed after a *successful* install, use the
installer's own preserved assets. This is the only supported procedure: the published 2.13.2
bundle cannot be used, because its installer accepts only `2.8 … 2.13.1` and aborts with
`unsupported predecessor 2.13.3`.

```sh
BK='/var/backups/devicemonitor/install-v213.<id>'        # replace with the INSTALL_OK backup path
service devicemonitor stop || :
i=0
while pgrep -f '^/usr/local/bin/python3 /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/monitor_daemon.py$' >/dev/null \
      && [ "$i" -lt 20 ]; do
    sleep 1
    i=$((i + 1))
done
if pgrep -f '^/usr/local/bin/python3 /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/monitor_daemon.py$' >/dev/null; then
    echo 'ROLLBACK_ABORT=daemon still running'
    exit 1
fi

sh "$EXTRACT/release/prune-plan.sh" restore-targets --plan "$BK/plan" --backup "$BK"
[ ! -f "$BK/prune" ] || sh "$EXTRACT/release/prune-plan.sh" restore --plan "$BK/prune" --backup "$BK"
sh "$EXTRACT/release/prune-plan.sh" restore-record \
    --record /var/db/devicemonitor/installed-manifest.txt --backup "$BK"

rm -f /var/lib/php/tmp/opnsense_menu_cache.xml
service configd restart
service devicemonitor start

i=0
while ! pgrep -f '^/usr/local/bin/python3 /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/monitor_daemon.py$' >/dev/null \
      && [ "$i" -lt 30 ]; do
    sleep 1
    i=$((i + 1))
done
pgrep -f '^/usr/local/bin/python3 /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/monitor_daemon.py$' >/dev/null

service configd status
service devicemonitor status
configctl -w 5 devicemonitor status
python3 -c 'import json;print(json.load(open("/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json"))["version"])'
                                                       # 2.13.2
[ "$(sha256 -q /var/db/devicemonitor/installed-manifest.txt)" = "$PRE_RECORD_SHA" ]
[ "$(sha256 -q /var/db/devicemonitor/devices.db)" = "$PRE_DB_SHA" ]

while read -r id old new mode source target; do
    if [ "$old" = absent ]; then
        [ ! -e "$target" ] || { echo "ROLLBACK_EXTRA=$target"; exit 1; }
    else
        [ "$(sha256 -q "$target")" = "$old" ] || { echo "ROLLBACK_MISMATCH=$target"; exit 1; }
    fi
done < "$BK/plan"
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
`RETAINED` line, monitoring is enabled, a SQLite WAL is present, the daemon is not running
before the run, `/var` lacks space, or the pre-install backup cannot be re-verified. Roll back
if: `INSTALL_OK` is absent, any manifest/record mismatch appears, `quick_check` or
`integrity_check` is not `ok`, Device Monitor configuration or `devices.db` unexpectedly changes,
the daemon does not stay up, or configd does not restart and answer `configctl`.

## 7. What this phase must not do

* No change to `.253` or `.252` in any form (no install, no restart, no config edit).
* No publication of a v2.13.3 tag or GitHub release in this phase.
* No deletion of `/var/backups/devicemonitor/install-v213.*` or `/root/dm-pre-2133`; both are
  retained with the historical backups.
