# Deployment plan — Device Monitor 2.14.0 to the `.23` testbed

**Status: EXECUTED — deployment and §9.3 rollback PASS on `192.168.20.23`, 6 November 2026; the bounded §9.4 monitoring exercise is COMPLETE / ACCEPTANCE PASS, with further execution unauthorised.** Authenticated visual About/Features acceptance, isolated fresh-install jail scenarios, the controlled successful-install live rollback cycle and one bounded two-cycle monitoring exercise passed on 6 November. The monitoring exercise used the accepted baseline, DMTEST scope and loopback SMTP only. It observed the lazy `notified_at` migration live before restoration; the two SMTP messages came from direct PHP helpers, and the copy-only fixtures are not live-lifecycle evidence. Full live reminder/ageing/CARP/plugin-registration behaviour remains unestablished. The database is logically restored but not physically byte-identical to the earlier live file; the 6 November investigation traced the change to the guard's `796d28c7…` snapshot copy at `08:32:04Z`, but the original bytes were not retained, so exact byte attribution remains an unresolved acceptance discrepancy. See
`verification/monitoring-validation/EXECUTION-20261106.md`.

This document now records both the gated procedure and its actual result. Device Monitor
2.13.3 was upgraded to 2.14.0 on the `.23` testbed. The initial deployment did not invoke
rollback. The later §9.3 cycle restored a test installation to 2.13.3 with the installer backup
and reinstalled 2.14.0 successfully. A later bounded monitoring exercise observed a live lazy
`notified_at` migration before restoration, then restored the schema to absent; final absence alone
is not counted as migration evidence. Live `FRESH=1`, real plugin registration and full
reminder/ageing/CARP behaviour remain untested. DM-BL-009 remains **OPEN**.

## Execution record

| Item | Result |
|---|---|
| Host baseline | OPNsense `26.7.8_2 (amd64)`, FreeBSD `15.1-RELEASE-p6`; Device Monitor `2.13.3`; `os-git-backup-1.1_5` installed immediately before deployment |
| Candidate | 1,725,593 bytes, SHA-256 `5149bfd41e5842a144a9d1280c008511f20f3783932eca9beb1f48fca6173f5f`, 60 members |
| Check | `CHECK_OK version=2.14.0 predecessor=2.13.3 files=63 core_locales=10 prunable=0 daemon_running=1 host=OPNsense.internal legacy_prunable=0 retained=0` |
| Install | `INSTALL_OK version=2.14.0 files=63 core_locales=10 pruned=0 backup=/var/backups/devicemonitor/install-v214.JeYC44 daemon_restarted=1 unchanged=32 repaired=0` |
| Target parity | All 42 manifest rows and all 63 installer-plan targets matched digest, mode and `root:wheel` ownership |
| Record | 63 digest rows, including 21 locale rows; SHA-256 `d891ce68c9035b3bcd2384d6f3705d6c8d9bc20fb5ef13cc9ca80b2ae1c035a2` |
| Database/configuration | At the initial deployment, `devices.db`, Device Monitor `config.json` and OPNsense `/conf/config.xml` remained byte-identical; SQLite quick/integrity checks `ok`; lazy `notified_at` migration was not executed then. The later bounded §9.4 exercise observed the migration live and restored the column to absent. |
| Service lifecycle | daemon PID `34058` → `79168`; configd PID `639` → `35685`; replacement daemon remained alive after 60 seconds; `configctl devicemonitor status` = `running` |
| Monitoring | `enabled=0`; no SQLite WAL/SHM; log records `Monitoring DISABLED` at 09:21:39 AEDT |
| Pre-install backup | `/root/dm-pre-2140/runtime-data.tgz`, 7,632,213 bytes, SHA-256 `ff7873ce0fbc1826663aa86c3271014c9c2ad3cdb3bd7b4eacce164a4a63753e`; 61 payload, 19 core-locale and record/database/configuration files verified |
| Installer backups | `/var/backups/devicemonitor/install-v214.JeYC44` (original deployment), `install-v214.zGJRuq` (test installation rolled back live) and `install-v214.qMPS7n` (final accepted installation); each has a 63-row plan and 19-file core-locale snapshot |
| Rollback | The initial deployment did not invoke rollback. The later §9.3 successful-install live rollback passed using `install-v214.zGJRuq`. This is a manual-helper result, not an automatic installer `ROLLBACK_STATUS` result |
| Rollback lifecycle | preparatory reset daemon `79168` → `5602`, configd `35685` → `84886`; test install `5602` → `92938`, configd `84886` → `47387`; rollback `92938` → `49278`, configd `47387` → `30312`; final install `49278` → `74577`, configd `30312` → `32439` |
| Final state after §9.3 | Device Monitor `2.14.0`; 63 targets and 63-row record `d891ce68…`; database `c17874a7…`, Device Monitor configuration `027594eb…` and OPNsense configuration `c2ce5800…` unchanged at this checkpoint; monitoring `enabled=0`; no WAL/SHM. The later §9.4 exercise changed the physical database representation to the consistent snapshot `796d28c7…`; the current accepted `/conf/config.xml` is `15ce9e6c…` |
| Browser acceptance | **PASS (6 November, operator-supplied screenshot)** — both About and Features render `v2.14.0`; no Network capture supplied. At deployment time this was pending because no authenticated session was available and the unauthenticated version endpoint redirects to login |
| Evidence | Initial deployment: `/root/dm-deploy-2140/install.log`, `/root/dm-deploy-2140/post-install-evidence.txt` (SHA-256 `c226c860dfcfb55ce150a780d7567e983b2a06d0bd67ceedee65aa9325096a12`), `.cline-reports/REPORT-20261106-092516.md`. Live rollback cycle: `/root/dm-validation-2140/live-rollback-20261105T231701Z/`, `SHA256SUMS` SHA-256 `5cc19b38d4b8a294ef83f8ddfdf86db0622a652c943c4f83a48bdaa258f79fe3`; `verification/LIVE-ROLLBACK-2.14.0-23-20261106.md` |

## Candidate and repository checkpoint

| Item | Verified value |
|---|---|
| Repository | `/root/src/opnsense-devicemonitor-upstream` |
| Branch | `integration/dm-bl-009-reconcile-20261105` |
| HEAD and remote | `690204bb1d6c402de9a2b41e16f753b37335279f` |
| Working tree | source tree at the verified HEAD; deployment-record edits remained uncommitted as required |
| CI | GitHub Actions run `42116897417`: `validate` success, 66 steps, 0 failures, 0 skips, exact tested SHA `690204bb1d6c402de9a2b41e16f753b37335279f` |
| Bundle | `/root/dm-backups/dm-bl009-candidate-rollback-fix-20261106-083105/dm-v2.14.0-runtime.tar.gz` |
| Bundle identity | 1,725,593 bytes; SHA-256 `5149bfd41e5842a144a9d1280c008511f20f3783932eca9beb1f48fca6173f5f`; 60 members |
| Published source evidence | `CANDIDATE_SOURCE=worktree`; CI and publication occurred after the candidate evidence was collected, so the exact bundle identity must be rechecked before installation |
| Target set | 42 reviewed manifest rows + 11 plugin catalogues + 10 merged core catalogues = 63 upgrade targets |

GitHub CI is Linux validation. It does not execute the FreeBSD installer-jail scenarios or
any live service lifecycle. The five passed 2.14.0 jail scenarios remain separate evidence;
they do not by themselves prove live rollback, `FRESH=1`, or monitoring-enabled behaviour. The
separate live rollback and bounded monitoring results are recorded below.

## 0. Authorisation and execution gate

The operator authorised installation after the read-only preflight and limited it to:

* creating the pre-install backup under `/root/dm-pre-2140`;
* installing on `192.168.20.23` only through the normal upgrade path;
* the installer's real `service configd restart` and daemon stop/wait/start lifecycle;
* post-install verification, including an authenticated About/Features check;
* rollback only if the documented acceptance criteria fail.

The authorisation did not include `FRESH=1`, monitoring activation, `.252`/`.253` access, an
OPNsense update, commits/pushes or branch/release/tag movement. DM-BL-009 remains **OPEN**.

## 1. Read-only preflight and stop conditions

Repeat these checks immediately before mutation. Abort rather than install if any differs.

```sh
set -eu
cd /root/src/opnsense-devicemonitor-upstream
[ "$(git rev-parse --abbrev-ref HEAD)" = integration/dm-bl-009-reconcile-20261105 ]
[ "$(git rev-parse HEAD)" = 690204bb1d6c402de9a2b41e16f753b37335279f ]
unexpected=$(git status --porcelain | cut -c4- | grep -Ev \
  '^(PROJECT_STATE.md|PRODUCT_BACKLOG.md|verification/DEPLOY-2.14.0-23-PLAN.md)$' || true)
[ -z "$unexpected" ]

BUNDLE=/root/dm-backups/dm-bl009-candidate-rollback-fix-20261106-083105/dm-v2.14.0-runtime.tar.gz
[ "$(stat -f %z "$BUNDLE")" -eq 1725593 ]
[ "$(sha256 -q "$BUNDLE")" = 5149bfd41e5842a144a9d1280c008511f20f3783932eca9beb1f48fca6173f5f ]
[ "$(tar -tzf "$BUNDLE" | wc -l | tr -d ' ')" -eq 60 ]

/bin/hostname                                      # OPNsense.internal
/usr/local/sbin/opnsense-version                   # OPNsense 26.7.8_2 (amd64)
python3 -c 'import json;print(json.load(open("/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json"))["version"])'
                                                    # 2.13.3
python3 -c 'import json;d=json.load(open("/var/db/devicemonitor/config.json"));print(d["enabled"])'
                                                    # 0
df -h /var                                         # sufficient for backup and one install-v214.* tree
find /var/db/devicemonitor -maxdepth 1 -type f \( -name '*.db-wal' -o -name '*.db-shm' \) -print
                                                    # no output
/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/daemon_status.sh
service devicemonitor status
service configd status
configctl -w 5 devicemonitor status
```

The preflight observed:

* OPNsense `26.7.8_2 (amd64)`, FreeBSD `15.1-RELEASE-p6`, Device Monitor `2.13.3`.
* Root filesystem approximately 3.0 GB available before the plugin installation and 2.9 GB at
  execution time.
* Monitoring `enabled=0`; no SQLite WAL/SHM files; daemon and configd running.
* Daemon PID `34058`, configd PID `639`, `configctl devicemonitor status` = `running`.
* Record SHA-256 `0afb4e4e68edd331f22c88ef559dd1163af0baaaba0cd77a76b3ed672c17dea7`;
  61 digest rows, all digest/mode/regular-file/root-ownership checks passed.
* `config.json` SHA-256 `027594eb735cf35e4b617163106031971567d0ba74027783e42cae46d37fd47d`;
  mode `0600 root:wheel`, 44 keys.
* `devices.db` SHA-256 `c17874a717cebe2c2e1dbaf537fd13a65b4ded47e10dfcce1849f2088136144e`;
  `quick_check=ok`, `integrity_check=ok`; 26 devices, 60 service rows, 2 identity events
  and 96 activity events.
* The original preflight observed `/conf/config.xml` SHA-256
  `cbba358a646aaeb28aa63dccafdd5e971a437c21637466493e415b17b67df61b`. Installing
  `os-git-backup-1.1_5` then ran OPNsense migrations and firmware plugin registration and added
  an automatic configuration revision; the execution backup therefore captured the stable
  post-plugin hash `8c08b0a07821c5579d0ec6fcc7a9b8ba358c5ac67d5e39a904b9466ba5b8e1a6`.
* Retained settings include `ha_carp_enabled=1` and `ha_role_override=auto`; reminder and
  identity-email switches are `0`.
* Core-locale state/pristine directory contains 19 files under
  `/var/backups/devicemonitor/core-locale/`; 90 top-level installation history entries existed
  before the 2.14.0 install and 91 remain afterwards. All are retained.
* Existing recovery assets include `/root/dm-pre-2133/runtime-data.tgz`
  (3,604,198 bytes, SHA-256 `dfa44d4c893fbc89c22389fc813774d8b9d123b71497ef47d73bb4aeb70ed9ba`)
  and `/var/backups/devicemonitor/install-v213.xKjyg1`. The OPNsense configuration backup
  `/conf/backup/config-1793868107.8517.xml` also remains available.

Stop if the host is not `.23`/`OPNsense.internal`, the installed version is not 2.13.3,
monitoring is enabled, a SQLite WAL is present, daemon/configd is unhealthy, free space is
insufficient, the record/database fails validation, or the candidate identity differs.

## 2. Installer dry run — verified non-mutating contract

`install-unattended.sh --check` computes verification and the replacement/prune plan, prints
`CHECK_OK`, and exits before creating an installer backup, pruning, merging catalogues or
replacing targets. Its disposable `/tmp/dm_install_v214.*` stage is removed by its exit trap.

The preflight ran the contract only after reading the installer flow. The candidate was
freshly extracted; output was:

```text
VERIFY_OK=4
NOTICE: merged the plugin keys into 10 core catalogue(s); uninstall.sh restores the pristine files
CHECK_OK version=2.14.0 predecessor=2.13.3 files=63 core_locales=10 prunable=0 daemon_running=1 host=OPNsense.internal legacy_prunable=0 retained=0
```

Mutation checks after the dry run all passed: live state hashes unchanged, backup directory
count `90` before and after, and no staged `/tmp/dm_install_v214.*` directory remained.

The actual-predecessor expectations are therefore **63 targets, 0 prunes, 0 retained and 0
legacy prunes**, with 10 core locale merges. These counts replace all synthetic jail counts;
the jail's `prune=1/retain=1` fixtures are not expectations for this host. No `PRUNE_PLAN=`
line should appear.

## 3. Schema and configuration migration review

### Database

Comparison of the live 2.13.3 `scan_network.py` with the candidate (the live file exactly
matches `release/2.13`) found one schema change: the lazy migration

```sql
ALTER TABLE device_identity_events ADD COLUMN notified_at DATETIME DEFAULT NULL
```

There are no new tables, destructive migrations or other column additions in the 2.14.0
difference. Existing identity rows receive `NULL`, which means no reminder has yet been
sent. The installer does not call `init_db()` and does not migrate the live database.

The daemon calls a scan only when `enabled=1`. With monitoring disabled, installation and
daemon stop/start leave the live schema and data untouched. A disposable consistent copy of
the live database was upgraded with the candidate's `init_db()` twice:

```text
MIGRATION_BEFORE_HAS_NOTIFIED_AT=0
MIGRATION_AFTER_HAS_NOTIFIED_AT=1
MIGRATION_ROWS_PRESERVED=1 tables=20
MIGRATION_IDENTITY_ROWS=2 notified_at_null=2
MIGRATION_IDEMPOTENT=PASS
MIGRATION_INTEGRITY=ok
MIGRATION_SCOPE=disposable-copy; live-db-unchanged
```

This proves only the migration logic on a copy. The live lazy migration is intentionally not
executed by this upgrade and remains a post-deployment/monitoring-enabled verification item.

### Configuration and combined defaults

The candidate adds six default settings and changes no existing common default:

| Added setting | 2.14.0 default | Live 2.13.3 `config.json` |
|---|---:|---|
| `email_reminder_identity` | `0` | present, `0` |
| `email_reminder_new_device` | `0` | present, `0` |
| `email_reminder_scan` | `0` | present, `0` |
| `email_reminder_service` | `0` | present, `0` |
| `identity_email_enabled` | `0` | present, `0` |
| `visibility_prime_interval` | `0` | absent; code falls back to `0` |

The installer replaces the installed `defaults.json` but preserves
`/var/db/devicemonitor/config.json`. The absent `visibility_prime_interval` must remain absent
and therefore effective as `0`; it must not be silently inserted during this deployment.
Identity-email and repeat-reminder behaviour remains disabled. Preserved HA values are
`ha_carp_enabled=1` and `ha_role_override=auto`.

The deliberate user-visible changes after installation are the 2.14.0 version and the About
heading correction. Scan/alert refactoring, identity email, reminder controls, configuration
visibility, non-HA fail-open behaviour, HA/CARP gating and O4 ageing are carried as code and
UI functionality, but are not activated or behaviourally proven by this disabled-monitoring
upgrade.

## 4. Pre-install backup — completed

The authorised run created and verified the archive below. It contains credentials and
remains root-only; `config.json` and `/conf/config.xml` contents were not printed or copied
into project records.

```sh
set -eu
umask 077
PRE=/root/dm-pre-2140
test ! -e "$PRE"
install -d -m 700 -o root -g wheel "$PRE"

cp -p /var/db/devicemonitor/config.json "$PRE/config.json"
cp -p /var/db/devicemonitor/installed-manifest.txt "$PRE/installed-manifest.txt"
cp -p /conf/config.xml "$PRE/config.xml"
cp -Rp /var/backups/devicemonitor/core-locale "$PRE/core-locale"

find /var/backups/devicemonitor/core-locale -type f -exec sh -c \
  'for f do printf "%s  %s\n" "$(sha256 -q "$f")" "$f"; done' sh {} + \
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

python3 - "$PRE/pre-state.txt" <<'PY'
import hashlib, json, sqlite3, sys
paths = [
    '/var/db/devicemonitor/config.json',
    '/var/db/devicemonitor/installed-manifest.txt',
    '/var/db/devicemonitor/devices.db',
    '/conf/config.xml',
]
with open(sys.argv[1], 'w') as out:
    for path in paths:
        with open(path, 'rb') as fh:
            out.write(f'{hashlib.sha256(fh.read()).hexdigest()}  {path}\n')
    defaults = json.load(open('/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'))
    out.write(f'version={defaults["version"]}\n')
    cfg = json.load(open('/var/db/devicemonitor/config.json'))
    out.write(f'enabled={cfg.get("enabled", "<absent>")}\n')
    con = sqlite3.connect('/var/db/devicemonitor/devices.db')
    out.write(f'quick_check={con.execute("PRAGMA quick_check").fetchone()[0]}\n')
    con.close()
    out.write('daemon_pid=%s\n' % open('/var/run/devicemonitor.pid').read().strip())
    out.write('configd_pid=%s\n' % open('/var/run/configd.pid').read().strip())
PY

printf '%s\n' /var/backups/devicemonitor/* | sort > "$PRE/backup-inventory.txt"
sha256 -q /root/dm-backups/dm-bl009-candidate-rollback-fix-20261106-083105/dm-v2.14.0-runtime.tar.gz \
  > "$PRE/candidate.sha256"

tar -czf "$PRE/runtime-data.tgz" -C "$PRE" \
  devices.db config.json installed-manifest.txt config.xml pre-state.txt \
  core-locale core-locale.sha256 backup-inventory.txt candidate.sha256
chmod 600 "$PRE/runtime-data.tgz"
tar -tzf "$PRE/runtime-data.tgz"
sha256 -q "$PRE/runtime-data.tgz"

VERIFY=$(mktemp -d /root/dm-backup-verify.XXXXXX)
tar -xzf "$PRE/runtime-data.tgz" -C "$VERIFY"
[ "$(find "$VERIFY/core-locale" -type f | wc -l | tr -d ' ')" -eq 19 ]
[ "$(sha256 -q "$VERIFY/config.json")" = "$(sha256 -q /var/db/devicemonitor/config.json)" ]
[ "$(sha256 -q "$VERIFY/installed-manifest.txt")" = "$(sha256 -q /var/db/devicemonitor/installed-manifest.txt)" ]
[ "$(sha256 -q "$VERIFY/config.xml")" = "$(sha256 -q /conf/config.xml)" ]
python3 - "$VERIFY/devices.db" <<'PY'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
assert c.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
assert c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
c.close()
PY
find "$VERIFY/core-locale" -type f -exec sh -c \
  'for f do printf "%s  %s\n" "$(sha256 -q "$f")" "$f"; done' sh {} + \
  | sort | awk '{print $1}' > "$VERIFY/core-locale.copy-hashes.txt"
awk '{print $1}' "$PRE/core-locale.sha256" > "$VERIFY/core-locale.source-hashes.txt"
cmp "$VERIFY/core-locale.source-hashes.txt" "$VERIFY/core-locale.copy-hashes.txt"
rm -rf "$VERIFY"
```

Acceptance of the backup requires a readable archive, successful extraction to a disposable
directory, matching `config.json`/record/database/configuration hashes and all 19 core-locale
files verified by `core-locale.sha256`. Record the archive size and SHA-256 without exposing
credentials. Preserve `/root/dm-pre-2133` and every existing `install-v213.*` directory.

The actual execution additionally captured the complete 61-file installed payload under
`payload/`, with `record-paths.txt` and `payload-state.txt` recording every digest and mode.
Archive verification compared all 61 payload digests/modes and all 19 core-locale files. The
verified archive is 7,632,213 bytes, contains 170 members and has SHA-256
`ff7873ce0fbc1826663aa86c3271014c9c2ad3cdb3bd7b4eacce164a4a63753e`.

## 5. Installation — executed

The authorised run used the fresh extraction shown below. The exact command completed with
exit status 0; its output is retained at `/root/dm-deploy-2140/install.log`.

```sh
set -eu
BUNDLE=/root/dm-backups/dm-bl009-candidate-rollback-fix-20261106-083105/dm-v2.14.0-runtime.tar.gz
DEPLOY=/root/dm-deploy-2140
EXTRACT="$DEPLOY/extracted-$(date +%Y%m%d-%H%M%S)"   # actual: extracted-20261106-092004
[ "$(stat -f %z "$BUNDLE")" -eq 1725593 ]
[ "$(sha256 -q "$BUNDLE")" = 5149bfd41e5842a144a9d1280c008511f20f3783932eca9beb1f48fca6173f5f ]
test ! -e "$EXTRACT"
install -d -m 700 "$DEPLOY"
install -d -m 755 "$EXTRACT"
tar -xzf "$BUNDLE" -C "$EXTRACT"
cd "$EXTRACT"
sh install-unattended.sh --host "$(/bin/hostname)" --check
# Stop and review the exact CHECK_OK line before continuing.
sh install-unattended.sh --host "$(/bin/hostname)"
```

The run did not use `FRESH=1`. Its actual result was:

```text
VERIFY_OK=4
NOTICE: merged the plugin keys into 10 core catalogue(s); uninstall.sh restores the pristine files
CHECK_OK version=2.14.0 predecessor=2.13.3 files=63 core_locales=10 prunable=0 daemon_running=1 host=OPNsense.internal legacy_prunable=0 retained=0
RECORD_BACKED_UP=/var/db/devicemonitor/installed-manifest.txt
BACKUP_READY=/var/backups/devicemonitor/install-v214.JeYC44
CORE_LOCALE_STATE_BACKED_UP=present files=19
CORE_LOCALE_STATE=/var/backups/devicemonitor/core-locale
UNCHANGED=32
Stopping configd...done
Starting configd.
Stopping devicemonitor.
Waiting for PIDS: 34058.
Starting devicemonitor.
INSTALL_OK version=2.14.0 files=63 core_locales=10 pruned=0 backup=/var/backups/devicemonitor/install-v214.JeYC44 daemon_restarted=1 unchanged=32 repaired=0
```

`files=63`, `core_locales=10`, `pruned=0` and the new `install-v214.JeYC44` backup were
confirmed. No `PRUNE_PLAN=`, `PRUNE_RETAINED`, `ABORT:` or unexpected `RETAINED` line appeared.
The installer backup is retained as a rollback asset.

## 6. Post-install acceptance

The package, record, target, database, configuration and service checks below completed against
the live installation. The authenticated browser subsection was later closed by the operator's
visual evidence; the Network-capture portion remains unsupplied.

### Package, record and target parity

```sh
set -eu
EXTRACT=/root/dm-deploy-2140/extracted-20261106-092004
BK=/var/backups/devicemonitor/install-v214.JeYC44

python3 -c 'import json;print(json.load(open("/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json"))["version"])'
[ "$(python3 -c 'import json;print(json.load(open("/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json"))["version"])')" = 2.14.0 ]

cd "$EXTRACT"
while read -r hash mode source target; do
    [ "$(sha256 -q "$target")" = "$hash" ] || { echo "MANIFEST_MISMATCH=$target"; exit 1; }
    [ "$(stat -f %Lp "$target")" = "$mode" ] || { echo "MODE_MISMATCH=$target"; exit 1; }
    [ "$(stat -f %Su "$target"):$(stat -f %Sg "$target")" = root:wheel ] \
        || { echo "OWNER_MISMATCH=$target"; exit 1; }
done < release/v2.14.0-runtime.manifest

[ "$(wc -l < "$BK/plan" | tr -d ' ')" -eq 63 ]
while read -r id old new mode source target; do
    [ "$(sha256 -q "$target")" = "$new" ] || { echo "PLAN_MISMATCH=$target"; exit 1; }
    [ "$(stat -f %Lp "$target")" = "$mode" ] || { echo "PLAN_MODE_MISMATCH=$target"; exit 1; }
    [ "$(stat -f %Su "$target"):$(stat -f %Sg "$target")" = root:wheel ] \
        || { echo "PLAN_OWNER_MISMATCH=$target"; exit 1; }
done < "$BK/plan"

RECORD=/var/db/devicemonitor/installed-manifest.txt
[ "$(grep -vc '^#' "$RECORD")" -eq 63 ]
[ "$(grep -c '^[0-9a-f]\{64\} ' "$RECORD")" -eq 63 ]
[ "$(grep -c '\.mo$' "$RECORD")" -eq 21 ]
while read -r hash target; do
    [ "$(sha256 -q "$target")" = "$hash" ] || { echo "RECORD_MISMATCH=$target"; exit 1; }
done <<EOF
$(grep '^[0-9a-f]\{64\} ' "$RECORD")
EOF
sha256 -q "$RECORD"
```

The new record digest is
`d891ce68c9035b3bcd2384d6f3705d6c8d9bc20fb5ef13cc9ca80b2ae1c035a2`. Its count, paths,
digests and manifest relationship are internally consistent.

### Database and configuration preservation

```sh
set -eu
[ "$(sha256 -q /var/db/devicemonitor/devices.db)" = c17874a717cebe2c2e1dbaf537fd13a65b4ded47e10dfcce1849f2088136144e ]
[ "$(sha256 -q /var/db/devicemonitor/config.json)" = 027594eb735cf35e4b617163106031971567d0ba74027783e42cae46d37fd47d ]
[ "$(sha256 -q /conf/config.xml)" = 8c08b0a07821c5579d0ec6fcc7a9b8ba358c5ac67d5e39a904b9466ba5b8e1a6 ]

python3 - <<'PY'
import json, sqlite3
c = sqlite3.connect('file:/var/db/devicemonitor/devices.db?mode=ro', uri=True)
assert c.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
assert c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
assert c.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='devices'").fetchone()[0] == 1
assert c.execute('SELECT count(*) FROM devices').fetchone()[0] == 26
assert c.execute('SELECT count(*) FROM device_services').fetchone()[0] == 60
assert c.execute('SELECT count(*) FROM device_identity_events').fetchone()[0] == 2
assert c.execute('SELECT count(*) FROM device_activity_events').fetchone()[0] == 96
cols = {r[1] for r in c.execute('PRAGMA table_info(device_identity_events)')}
assert 'notified_at' not in cols, 'unexpected live schema migration'
c.close()
d = json.load(open('/var/db/devicemonitor/config.json'))
assert d.get('enabled') == '0'
assert d.get('ha_carp_enabled') == '1'
assert d.get('ha_role_override') == 'auto'
for key in ('email_reminder_identity', 'email_reminder_new_device',
            'email_reminder_scan', 'email_reminder_service'):
    assert int(d.get(key, 0)) == 0
assert d.get('identity_email_enabled') == '0'
assert int(d.get('visibility_prime_interval', 0)) == 0
assert d.get('sidecar_translation_enabled', '1') == '1'
PY
```

Exact database/configuration hashes are acceptance criteria while monitoring remains disabled.
If any changes, stop and diagnose before further actions. In particular, do not treat the
absence of `notified_at` as failure: the installer must not have run the lazy scan migration.

### Daemon, configd and monitoring state

```sh
set -eu
PRE=/root/dm-pre-2140
PRE_DAEMON_PID=$(sed -n 's/^daemon_pid=//p' "$PRE/pre-state.txt")
PRE_CONFIGD_PID=$(sed -n 's/^configd_pid=//p' "$PRE/pre-state.txt")
[ -n "$PRE_DAEMON_PID" ] && [ -n "$PRE_CONFIGD_PID" ]
NEW_DAEMON_PID=$(cat /var/run/devicemonitor.pid)
NEW_CONFIGD_PID=$(cat /var/run/configd.pid)
[ "$NEW_DAEMON_PID" != "$PRE_DAEMON_PID" ]
[ "$NEW_CONFIGD_PID" != "$PRE_CONFIGD_PID" ]
sleep 60
[ "$(cat /var/run/devicemonitor.pid)" = "$NEW_DAEMON_PID" ]
pgrep -f '^/usr/local/bin/python3 /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/monitor_daemon.py$' >/dev/null
/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/daemon_status.sh
service devicemonitor status
service configd status
configctl -w 5 devicemonitor status
tail -n 40 /var/log/devicemonitor.log | grep -E 'Daemon (stopping|stopped|started)|Monitoring DISABLED'
```

Acceptance requires the old daemon not to be reused, the replacement to remain alive after
60 seconds, configd to restart and answer `configctl`, and the log to show `Monitoring
DISABLED` without `Monitoring ENABLED` or a scan-cycle activation.

### Authenticated About and Features check

Use an authenticated OPNsense browser session; never place credentials in commands or reports.

1. Open `Services -> Device Monitor -> Settings -> About`.
2. In the browser network panel, confirm `GET
   /api/devicemonitor/config/getversion` returns `{"version":"2.14.0"}`.
3. Confirm `#about-version` displays `v2.14.0` and `#about-features-version` displays
   `v2.14.0`.
4. Confirm the heading no longer says `v2.10 Features and Enhancements` and no stale
   `v2.13.2` badge remains after a hard reload with cache disabled.
5. Capture a screenshot and the endpoint response; do not record session cookies.

No browser or authenticated session was available during acceptance. The unauthenticated
`/api/devicemonitor/config/getversion` request redirected to login, so the rendered check was
not performed. Source-level binding was checked previously, but a successful endpoint response
alone is not a substitute for the visible check.

### Retained main and 2.13.x behaviour

With monitoring disabled, the following remain UI smoke requirements rather than live
behavioural proof. The authenticated UI smoke checks are pending; code-level regressions passed.

* Existing Devices, Activity Timeline, Identity Events, service inventory and Settings views
  load in the authenticated UI and show the pre-existing 26 devices, 60 service rows, 96 activity
  events and 2 identity events without changing state.
* The Settings form exposes the reminder, identity-email, configuration-visibility and
  HA/CARP controls. Reminder and identity-email controls remain off; HA remains enabled with
  role `auto`; the O4 sidecar translation setting remains enabled.
* No reminder, identity, service or scan email/webhook is sent during acceptance.
* Run the existing focused regressions from the authoritative checkout:

```sh
python3 tests/test_carp_role_gate.py
python3 tests/test_non_ha_operation.py
python3 tests/test_service_ageing.py
python3 tests/test_hostwatch_lan_visibility.py
python3 tests/test_fresh_install_defaults.py
python3 tests/test_upgrade_predecessors.py
```

These passed in preflight. They establish code-level retention of HA/CARP/O4/non-HA and
default behaviour, not a live CARP failover, ageing cycle or reminder delivery. Those live
behaviours remain unverified until monitoring is separately authorised.

## 7. Failure and rollback

On any install abort, stop forward actions. Inspect the installer's own
`ROLLBACK_STATUS=COMPLETE|INCOMPLETE` and the retained
`/var/backups/devicemonitor/install-v214.<id>` directory. A complete automatic rollback must
restore targets, prunes, the record and all 19 core-locale state/pristine files. Verify the
restored 2.13.3 version, original record hash
`0afb4e4e68edd331f22c88ef559dd1163af0baaaba0cd77a76b3ed672c17dea7`, database/config hashes,
daemon/configd health and monitoring disabled. Do not run manual recovery after a complete
automatic rollback.

If an accepted installation later must be reverted, use the candidate's own reviewed rollback
helpers and the installer backup. This path was exercised live on 6 November from the
`install-v214.zGJRuq` test installation and passed; the sequence below remains the reviewed
recovery mechanism.

```sh
set -eu
EXTRACT=/root/dm-deploy-2140/extracted-20261106-092004
BK=/var/backups/devicemonitor/install-v214.JeYC44
service devicemonitor stop || :
i=0
while pgrep -f '^/usr/local/bin/python3 /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/monitor_daemon.py$' >/dev/null \
      && [ "$i" -lt 20 ]; do sleep 1; i=$((i + 1)); done
! pgrep -f '^/usr/local/bin/python3 /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/monitor_daemon.py$' >/dev/null

sh "$EXTRACT/release/prune-plan.sh" restore-targets --plan "$BK/plan" --backup "$BK"
[ ! -f "$BK/prune" ] || sh "$EXTRACT/release/prune-plan.sh" restore --plan "$BK/prune" --backup "$BK"
sh "$EXTRACT/release/prune-plan.sh" restore-core-locale-state \
  --state /var/backups/devicemonitor/core-locale --backup "$BK"
sh "$EXTRACT/release/prune-plan.sh" restore-record \
  --record /var/db/devicemonitor/installed-manifest.txt --backup "$BK"

rm -f /var/lib/php/tmp/opnsense_menu_cache.xml
service configd restart
service devicemonitor start
i=0
while ! pgrep -f '^/usr/local/bin/python3 /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/monitor_daemon.py$' >/dev/null \
      && [ "$i" -lt 30 ]; do sleep 1; i=$((i + 1)); done
pgrep -f '^/usr/local/bin/python3 /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/monitor_daemon.py$' >/dev/null

service configd status
service devicemonitor status
configctl -w 5 devicemonitor status
python3 -c 'import json;print(json.load(open("/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json"))["version"])'
[ "$(sha256 -q /var/db/devicemonitor/installed-manifest.txt)" = 0afb4e4e68edd331f22c88ef559dd1163af0baaaba0cd77a76b3ed672c17dea7 ]
[ "$(sha256 -q /var/db/devicemonitor/devices.db)" = c17874a717cebe2c2e1dbaf537fd13a65b4ded47e10dfcce1849f2088136144e ]
[ "$(sha256 -q /var/db/devicemonitor/config.json)" = 027594eb735cf35e4b617163106031971567d0ba74027783e42cae46d37fd47d ]
```

Expected restoration lines are `ROLLBACK_RESTORED=`, `RECORD_RESTORED=`, and a
`ROLLBACK_SUMMARY=restored=<n> skipped=<n> conflicts=0 failed=0`; any conflict/failure, wrong
version, record mismatch, database/configuration change or unhealthy service is a stop
condition. Preserve `/root/dm-pre-2140` and every 2.13.x/2.14.0 backup even after successful
recovery.

This manual helper does **not** emit `ROLLBACK_STATUS`; that status belongs to the installer's
automatic failure path. A manual rollback is accepted only from the helper's
`ROLLBACK_SUMMARY=...` and `CORE_LOCALE_ROLLBACK_SUMMARY=...` lines plus independent target,
record, data, configuration, service and ownership checks. The successful live test reported
`restored=31 skipped=32 conflicts=0 failed=0` and
`CORE_LOCALE_ROLLBACK_SUMMARY=restored=19 removed=0 conflicts=0 failed=0`.

If the database itself is damaged, stop Device Monitor first and restore only the verified
consistent database from `/root/dm-pre-2140/runtime-data.tgz`; do not restore it merely because
the target rollback succeeded. A plain tar copy of a live database is not an acceptable
substitute for the `sqlite3.backup()` file in that archive.

The installer must leave the database and `config.json` byte-identical. If diagnosis nevertheless
shows that either changed, stop Device Monitor before restoring data and preserve the changed copy
for investigation. Only after confirming that no new monitoring data must be retained, and with a
second explicit recovery decision, use the verified pre-install copy:

```sh
set -eu
PRE=/root/dm-pre-2140
RESTORE=$(mktemp -d /root/dm-rollback-restore.XXXXXX)
tar -xzf "$PRE/runtime-data.tgz" -C "$RESTORE" devices.db config.json
[ "$(sha256 -q "$RESTORE/devices.db")" = 796d28c7b8c5fd0b8442f74a4bca843b518d9e5b2a8db9f3fe7e5f0860d11f3d ]
[ "$(sha256 -q "$RESTORE/config.json")" = 027594eb735cf35e4b617163106031971567d0ba74027783e42cae46d37fd47d ]
service devicemonitor stop || :
i=0
while pgrep -f '^/usr/local/bin/python3 /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/monitor_daemon.py$' >/dev/null \
      && [ "$i" -lt 20 ]; do sleep 1; i=$((i + 1)); done
install -m 644 -o root -g wheel "$RESTORE/devices.db" /var/db/devicemonitor/devices.db
install -m 600 -o root -g wheel "$RESTORE/config.json" /var/db/devicemonitor/config.json
rm -rf "$RESTORE"
service devicemonitor start
configctl -w 5 devicemonitor status
```

The SQLite `.backup` file in `/root/dm-pre-2140/runtime-data.tgz` has physical SHA-256
`796d28c7b8c5fd0b8442f74a4bca843b518d9e5b2a8db9f3fe7e5f0860d11f3d`, not the live file's
`c17874a7…` digest: SQLite page layout can change when a consistent copy is made. Its logical
`.dump` SHA-256 is `d7ed7f816c414387bf136d2782ac6c2e1e3e6c08e8c302ae924726d77adb2479`,
identical to the live database. Recovery must verify integrity and logical equivalence, not the
live file's physical digest.

Do not restore `/conf/config.xml` as part of a package rollback; it is an OPNsense configuration
recovery asset, not a Device Monitor installation target. Any need to restore it is a separate
OS-level incident and requires the normal OPNsense configuration recovery procedure.

## 8. Evidence boundary and approval

| Path or behaviour | Current evidence |
|---|---|
| 2.14.0 candidate build, bundle identity, manifest and installer-jail scenarios | PASS locally; exact SHA `5149bfd41e...` |
| Exact-commit Linux CI | PASS, run `42116897417`, 66 steps, 0 failures/skips |
| `.23` read-only preflight and non-mutating `--check` | PASS; 63 targets, 0 prune, 0 retain |
| Live 2.13.3 → 2.14.0 upgrade | **PASS** — 63 targets, 63-row record, unchanged data/configuration, daemon/configd lifecycle passed |
| Lazy identity-reminder schema migration on a database copy | PASS on disposable copy |
| Lazy identity-reminder schema migration on the live database | **OBSERVED LIVE before restoration**: absent in the guard/pre-install snapshot, present after direct discovery at `08:36:24Z` before monitoring was enabled at `08:36:26Z`, present after both cycles, then absent after restoration. Final absence is restoration evidence, not proof that migration did not occur |
| Authenticated About/Features acceptance | **PASS** on operator-supplied screenshot; no Network capture |
| Successful-install live rollback | **PASS** — 2.14.0 test installation restored to 2.13.3, then 2.14.0 reinstalled; no `ROLLBACK_STATUS` emitted by the manual helper |
| `FRESH=1` | **NOT TESTED** |
| Monitoring-enabled behaviour on 2.14.0 | **COMPLETE / ACCEPTANCE PASS within the bounded scope; further execution unauthorised**: two live scheduled scans, separate direct DMTEST service discovery, scope-limited visibility probing and two loopback SMTP messages from direct PHP helper calls. Scheduled daemon-triggered service discovery, full reminders, ageing, CARP, real plugin registration and lifecycle remain unexercised |
| Live, helper and fixture boundary | Live: scheduled scans, direct discovery and visibility scope. Live helpers: the two SMTP messages were directly invoked PHP helpers, not daemon-generated delivery. Copy-only fixtures: identity/service/new-device/aged/retired and fresh-host refusal. The fixtures do not prove real OPNsense registration or lifecycle |
| Physical database restoration | **UNRESOLVED FOR THE COMPLETED EXERCISE; recurrence corrected in the guard**: original live `c17874a7…`; verified consistent snapshot and final live/guard file `796d28c7…`; both share logical digest `10460718…`, 21 schema tables, the same 26/60/2/96 counts and `notified_at` absent. The transition is traced to the historical guard's `.backup()` snapshot and its `08:32:04Z` recovery copy; the installer did not replace the live file. No retained physical file contains `c17874a7…`, so the header/page delta cannot be compared. The corrected guard now enforces original-byte identity for future authorised runs, but cannot retroactively prove the completed exercise. Do not claim historical byte-identical restoration |

**Outcome:** the authorised package/data/service deployment and controlled successful-install
rollback cycle passed. The bounded §9.4 monitoring exercise is **COMPLETE / ACCEPTANCE PASS** and
further execution is **unauthorised**. Its residual gaps are classified below; DM-BL-009 remains
**OPEN**.

| Residual gap | Classification | Rationale |
|---|---|---|
| Physical DB byte identity (`c17874a7…` → `796d28c7…`) | **Release blocker for an unqualified exact-restoration claim about the completed exercise; recurrence corrected in the guard** | Logical digest, schema, integrity and row counts match, and the historical guard recovery is traced. The original bytes were never retained, leaving the internal byte delta unverified. The corrected guard now separates original bytes from the SQLite snapshot and performs physical, metadata, schema/data and integrity checks, but that cannot prove the historical bytes were restored. |
| Live `FRESH=1` and real OPNsense plugin registration/lifecycle | **Deferred limitation for the bounded exercise; release blocker for DM-BL-009 closure** | Jail and copy-only fixtures prove call boundaries, not real-host registration or lifecycle. |
| Full reminder/ageing/CARP and daemon-generated notification/service-discovery paths | **Deferred limitation for the bounded exercise; release blocker for full monitoring sign-off** | The scheduled scans did not run scheduled service discovery; reminders, ageing and CARP were not exercised, and helper emails were direct calls. |
| Exact daemon-triggered attribution of `notified_at` | **Deferred limitation, not a blocker for the observed mutation** | The column was observed live-present after direct discovery and before restoration; the caller beyond the direct-discovery path was not separately instrumented. |
| External SMTP, webhook, AdGuard/Pi-hole and targeted-Nmap delivery | **Deferred limitation; intentionally excluded** | The authorised scope permitted only the loopback SMTP sink. |

## 9. Outstanding validation closure plan and execution record

Prepared on 6 November 2026. Steps 1–4 were later authorised and executed. Step 4 is **COMPLETE /
ACCEPTANCE PASS** within its two-cycle scope, and further execution is **unauthorised**. This work
does not reopen the initial 2.13.3 → 2.14.0 package deployment or change the historical M5 result.
DM-BL-009 remains **OPEN** until the classified residual gaps and the main-integration decision are
completed.

The four areas are deliberately separate. Each has its own authorisation, evidence directory and
stop point. No result in one area may be used to claim a result in another.

### 9.1 Authenticated About and Features rendering

**Prerequisites**

* An already authenticated OPNsense browser session for `192.168.20.23`. No Codex, curl, API-key or
  cookie extraction is required.
* No password, session cookie, CSRF token or authorisation header may be copied into a command,
  report or evidence file.
* Store sanitised screenshots and text evidence under
  `/root/dm-validation-2140/authenticated-ui/` (mode `0700`, `root:wheel`).

**Actions**

1. In the authenticated browser, open
   `https://192.168.20.23/ui/devicemonitor/index/settings`.
2. Open **Settings → About**.
3. Open the browser developer tools, select **Network**, enable **Disable cache** and **Preserve
   log**, then hard-reload the page.
4. Select the `GET /api/devicemonitor/config/getversion` request and capture its status and response
   body. The expected body is `{"version":"2.14.0"}`.
5. In the browser console, run the following read-only assertion and capture its textual output:

   ```js
   JSON.stringify({
     about: document.querySelector('#about-version').textContent.trim(),
     features: document.querySelector('#about-features-version').textContent.trim(),
     heading: document.querySelector('#about-features-version').parentElement.textContent.trim()
   })
   ```

6. Capture a screenshot showing both the About version and the Features heading. Save the console
   text and the endpoint response as separate sanitised evidence files.

**Expected result**

* The endpoint returns HTTP 200 with `{"version":"2.14.0"}`.
* `#about-version` renders exactly `v2.14.0`.
* `#about-features-version` renders exactly `v2.14.0`.
* The heading reads `v2.14.0 Features and Enhancements`; no `v2.10 Features and Enhancements` and no
  stale `v2.13.2` badge remains after the hard reload.

**Result (6 November 2026): PASS on operator-supplied evidence.** The operator's authenticated
screenshot of Settings → About shows both Device Monitor `v2.14.0` and `v2.14.0 Features and
Enhancements`. This closes the visual rendering gap only. No browser Network capture, endpoint
response, console output or cache-behaviour evidence was supplied, so those are not claimed.

**Stop conditions and unsupported evidence**

* A login redirect, missing element, mismatched endpoint value or stale rendered value is a failure;
  do not clear caches before capturing the failed state.
* An authenticated endpoint response without a visible render is not sufficient to close this gap.
* An unauthenticated request is also not sufficient. The currently observed redirect to login
  remains recorded as the reason this check was previously pending.

**Backup and rollback**

This check is read-only. No backup or rollback is required. Removing `Disable cache` and refreshing
afterwards restores the browser's ordinary cache behaviour.

### 9.2 Fresh installation in a disposable FreeBSD jail

**Prerequisite change (implemented and executed 6 November 2026)**

The harness previously began every scenario from the live 2.13.3 predecessor and had no
fresh-install scenario. It now provides `fresh` and `fresh-rollback` scenarios, selected with a
mode-aware guard, and starts each from an empty predecessor tree: no Device Monitor files, record,
`devices.db`, `config.json`, rc link, `/etc/rc.conf.d/devicemonitor`, plugin tree or core-locale
state/pristine archive.

The unmodified 2.14.0 installer and payload remain the subject under test. Do not stub the
installer, manifest, prune helper, payload, daemon service script or daemon binary.

**Isolated host-service boundaries**

Two OPNsense host services are outside the payload and must be represented explicitly:

* `service configd` keeps the existing recording stub. For `fresh-rollback`, make the stub fail the
  first restart after mutation and succeed on the rollback restart, so the installer's actual abort
  path is exercised without an artificial permanent failure.
* `rc.configure_plugins` must be shadowed by a jail-only stub in
  `/usr/local/etc/rc.configure_plugins`. It must verify the jail marker, hostname and uid, append a
  call record, write only inside the jail scratch tree, and never execute the host script or touch
  the host `/conf`.

This tests the installer's call boundary, not OPNsense's real plugin-registration internals. That
residual gap must stay stated: a jail cannot prove that a real OPNsense installation regenerates all
host registration state correctly.

**Actions**

```sh
DM_SANDBOX_SAVE=1 sh verification/installer-sandbox/run-installer-sandbox.sh scenario fresh
DM_SANDBOX_SAVE=1 sh verification/installer-sandbox/run-installer-sandbox.sh scenario fresh-rollback
```

The harness must still prove the candidate bundle's size, SHA-256, member list and source
relationship before running either scenario.

**Expected result — successful fresh installation**

* The non-mutating check reports
  `CHECK_OK version=2.14.0 predecessor=fresh files=64 core_locales=10 prunable=0 daemon_running=0 ...`.
* Installation reports `version=2.14.0 files=64 core_locales=10 pruned=0` with
  `daemon_restarted=0`, `unchanged=0` and `repaired=0`. `daemon_restarted=0` is correct for a fresh
  install because the installer's counter reports only the predecessor daemon; the daemon must still
  be started and observed running.
* All 64 targets exist with the manifest digest, mode and `root:wheel` ownership: 42 manifest rows,
  11 sidecar catalogues, 10 merged core catalogues and `/etc/rc.conf.d/devicemonitor`.
* The installation record contains 64 digest rows. Its paths are exactly the installed target set.
* `/etc/rc.d/devicemonitor` is the expected symlink; the rc.conf stub has mode `0644`.
* No `config.json`, `devices.db`, WAL or SHM exists immediately after installation. The daemon reads
  the defaults, logs `Monitoring DISABLED`, and does not create a database while monitoring is off.
* The two host-service stubs show one `rc.configure_plugins` call and the expected configd calls.

**Expected result — fresh-install abort**

* The stateful configd stub makes the first post-mutation restart fail.
* The installer reports its own nonzero failure and `ROLLBACK_STATUS=COMPLETE`.
* All 64 new targets are removed, including the rc.conf file and rc.d link; the new record is
  removed; `config.json`, `devices.db`, WAL and SHM remain absent.
* No staged installer directory remains. The jail, mounts and host scratch directories are removed,
  and the live `.23` fingerprint remains unchanged.
* Any conflict, incomplete rollback, payload target left behind, host-service leak or live-state
  change is a hard stop. Do not clean up by deleting the evidence.

**Result (6 November 2026): PASS for both isolated scenarios.** `fresh` reported
`CHECK_OK ... files=64 core_locales=10 prunable=0 daemon_running=0 ... legacy_prunable=0 retained=0`
and `INSTALL_OK version=2.14.0 files=64 core_locales=10 pruned=0 ... daemon_restarted=0 unchanged=0
repaired=0`. All 64 targets, the 64-row record, the rc.conf/rc.d wiring, the ten pristine core
catalogues, the running daemon and the absence of `devices.db`/`config.json` were verified
independently. `fresh-rollback` aborted non-zero and reported `ROLLBACK_STATUS=COMPLETE`,
`restored=64 ... conflicts=0 failed=0` and `CORE_LOCALE_ROLLBACK_SUMMARY=restored=0 removed=19
conflicts=0 failed=0`; every originally absent path was absent again and only the installer backup
directory remained. Both scenarios removed the jail, mounts and host stages and left the live
fingerprint unchanged. Evidence:
`/root/dm-validation-2140/jail-evidence-fresh-20261106/` (`SHA256SUMS` SHA-256
`1448ec56adf75dab2461da9f0fda6447486a9258fadd4afa9c4deec70e43b05b`). Full record:
`verification/FRESH-INSTALL-JAIL-2.14.0-20261106.md`. The jail-only `rc.configure_plugins` stub
does not prove real OPNsense registration, and live `FRESH=1` remains untested.

**Backup and rollback**

No live host file is changed. The jail overlays and the temporary test roots are disposable. Keep the
candidate, the `fresh` and `fresh-rollback` transcripts, before/after snapshots, stub call logs and
the teardown result. Preserve the historical 2.13.3 and existing 2.14.0 evidence without replacing
it.

### 9.3 Live successful-install rollback cycle on `.23`

This is the highest-risk remaining package test. It requires a separate explicit authorisation. The
cycle is:

`2.13.3 baseline → normal install 2.14.0 → restore the new 2.14.0 backup to 2.13.3 → normal
install 2.14.0 again`

The preparatory reset from the currently accepted 2.14.0 state to 2.13.3 is not counted as the
rollback test. The tested rollback is the one performed from the newly installed 2.14.0 state using
the backup created by that installation.

**Preconditions**

* `.23` is the only target; monitoring is disabled; no SQLite WAL/SHM exists; daemon and configd are
  healthy; free space is sufficient for three extracted bundles and the backups.
* Current accepted baseline: OPNsense `26.7.8_2`, Device Monitor `2.14.0`, record
  `d891ce68c9035b3bcd2384d6f3705d6c8d9bc20fb5ef13cc9ca80b2ae1c035a2`, database
  `c17874a717cebe2c2e1dbaf537fd13a65b4ded47e10dfcce1849f2088136144e`, Device Monitor config
  `027594eb735cf35e4b617163106031971567d0ba74027783e42cae46d37fd47d` and OPNsense config
  `c2ce5800c76fcf8470283d6ada559fd6c2eba5a8e0372b409cc046afd8307abf`. The latter supersedes the
  post-2.14.0 hash `8c08b0a0…` because the operator made a `/diag_backup.php` configuration backup
  at 09:55:54 on 6 November; the only document changes were the Git Backup plugin's `persisted_at`
  value and the revision metadata. Recheck the hash at execution time rather than treating either
  value as permanent.
* The 2.13.3 bundle is the preserved `/root/dm-deploy-2133/dm-v2.13.3-runtime.tar.gz`, exactly
  1,656,468 bytes and SHA-256
  `7f389248707cf8fa0684760820db85c0fddac4b8b3964e0563318b38b2730fe2`.
* The 2.14.0 bundle is the preserved
  `/root/dm-backups/dm-bl009-candidate-rollback-fix-20261106-083105/dm-v2.14.0-runtime.tar.gz`,
  exactly 1,725,593 bytes and SHA-256
  `5149bfd41e5842a144a9d1280c008511f20f3783932eca9beb1f48fca6173f5f`.
* Extract each bundle afresh. Do not reuse `/root/dm-deploy-2140/extracted-20261106-092004` or any
  previous extraction as the sole source.
* The current installer backup `/var/backups/devicemonitor/install-v214.JeYC44` is the known
  2.13.3 → 2.14.0 backup. Preserve a copy before the preparatory reset.

**Backup before mutation**

Create `/root/dm-validation-2140/rollback/<UTC-stamp>/`, mode `0700`, `root:wheel`, containing:

* a consistent SQLite backup of `devices.db` made with `sqlite3 ... ".backup ..."`, not a live-file
  copy;
* exact copies of `config.json`, `installed-manifest.txt`, `/conf/config.xml` (read-only reference
  only) and the current `/var/backups/devicemonitor/core-locale` state/pristine archive;
* a preserved copy of `/var/backups/devicemonitor/install-v214.JeYC44`;
* the current package target list and hashes;
* `SHA256SUMS` verified against every source.

Also preserve the bundle files themselves and record their sizes and digests. Do not copy
credentials, session data or `/conf/config.xml` secrets into reports.

**Preparatory reset to 2.13.3**

Use the reviewed §7 helper sequence with `BK=/var/backups/devicemonitor/install-v214.JeYC44` and the
helper extracted from the verified 2.14.0 bundle. Stop and wait for the daemon before restoration;
restore targets, core-locale state and record; invalidate the menu cache; restart configd; start the
daemon; verify:

* installed version `2.13.3`;
* record SHA-256 `0afb4e4e68edd331f22c88ef559dd1163af0baaaba0cd77a76b3ed672c17dea7`;
* unchanged database/config hashes above;
* healthy daemon, configd and monitoring disabled.

Stop if the preparatory reset is incomplete. Do not proceed to the test cycle.

**Test cycle**

1. Extract and verify the 2.13.3 bundle. Run its non-mutating check and expect the 61-target
   predecessor state, zero prunes and zero retained files.
2. Extract and verify the 2.14.0 bundle. Run `--check` from 2.13.3 and expect `files=63`,
   `prunable=0` and `retained=0`.
3. Install 2.14.0 normally. Record the newly printed `INSTALL_OK` backup directory.
4. Verify version, all 63 targets, the 63-row record, unchanged database/configuration, SQLite
   integrity, daemon stop/wait/start, real configd restart and monitoring disabled.
5. Immediately roll back using the new backup and the verified helper sequence from §7. This is the
   successful-install live rollback under test.
6. Require the helper's zero-conflict/zero-failure `ROLLBACK_SUMMARY` and
   `CORE_LOCALE_ROLLBACK_SUMMARY`, the original 2.13.3 record hash, unchanged
   database/configuration and healthy services. The manual helper does not emit
   `ROLLBACK_STATUS`; do not attribute that installer-only status to this path.
7. Install 2.14.0 normally again from the verified bundle. Verify the same 63-target, 63-row and
   service/data acceptance criteria. The final state must be the accepted 2.14.0 baseline with
   monitoring disabled.

**Executed result — 6 November 2026**

The reviewed cycle completed on `.23` with the unchanged candidate:

* Preparatory reset using `install-v214.JeYC44`: 2.14.0 → 2.13.3; targets
  `restored=31 skipped=32 conflicts=0 failed=0`, core-locale
  `restored=19 removed=0 conflicts=0 failed=0`; 61 targets/record and healthy services verified.
* Test installation: 2.13.3 → 2.14.0; `INSTALL_OK version=2.14.0 files=63 core_locales=10
  pruned=0 backup=/var/backups/devicemonitor/install-v214.zGJRuq daemon_restarted=1
  unchanged=32 repaired=0`; all 63 targets and the 63-row record verified.
* Successful-install rollback under test using `install-v214.zGJRuq`: targets
  `restored=31 skipped=32 conflicts=0 failed=0`, core-locale
  `restored=19 removed=0 conflicts=0 failed=0`; 61 restored targets and 2.13.3 record verified,
  database/config unchanged, SQLite integrity `ok`, the two 2.14-only targets absent again, and
  daemon/configd healthy. No `ROLLBACK_STATUS` line was emitted or claimed.
* Final reinstall: normal 2.14.0 upgrade; `INSTALL_OK ... backup=/var/backups/devicemonitor/install-v214.qMPS7n
  ... unchanged=32 repaired=0`; final 63-target, record, data, configuration, service and
  monitoring-disabled acceptance passed.

Evidence: `/root/dm-validation-2140/live-rollback-20261105T231701Z/`; `SHA256SUMS` SHA-256
`5cc19b38d4b8a294ef83f8ddfdf86db0622a652c943c4f83a48bdaa258f79fe3`; detailed record in
`verification/LIVE-ROLLBACK-2.14.0-23-20261106.md`.

**What this proves, and does not prove**

* It proves the real installer backup can restore a successful live 2.14.0 installation to 2.13.3,
  and that the normal upgrade can return the node to 2.14.0.
* It proves that the installer does not itself need to change Device Monitor data/configuration
  during this cycle. The pre-test database/config backup is a recovery asset, not an expected
  installer output.
* It does not prove automatic rollback after an injected live failure; that remains covered only by
  the isolated jail scenario. It does not prove `FRESH=1` or CARP failover.

**Interruptions and recovery**

* Each stop/restore/start may interrupt Device Monitor observation for roughly one to two minutes.
* `configd` is restarted; firewall, routing and the OPNsense web service are not restarted. No reboot
  is part of this check.
* On any failed step, stop forward actions. Preserve the new and old installer backups and use the
  pre-test consistent database/config snapshot only after the documented recovery decision. Do not
  improvise a partial rollback or reuse a mismatched helper.

### 9.4 Monitoring-enabled behaviour on `.23`

**Status: COMPLETE / ACCEPTANCE PASS — further execution is unauthorised (6 November 2026).** This section is the
corrected execution procedure. One final bounded run was executed after operator acceptance of the
baseline; the live evidence is under
`/root/dm-validation-2140/monitoring/20261106T083522Z/` and is recorded in
`verification/monitoring-validation/EXECUTION-20261106.md`. The procedure is retained for review,
not for another run. It supersedes the earlier draft details that assumed a `DB_FILE` environment
override and that described the identity email path imprecisely.

#### 9.4.0 Verified live pre-state at preparation time

Read-only checks on `.23` (`OPNsense.internal`, OPNsense `26.7.8_2`, FreeBSD
`15.1-RELEASE-p6`) established:

| Item | Verified value |
|---|---|
| Device Monitor | `2.14.0`; manifest header `# Device Monitor 2.14.0 install record (Decision 62)` |
| Installation record | 63 digest rows; SHA-256 `d891ce68c9035b3bcd2384d6f3705d6c8d9bc20fb5ef13cc9ca80b2ae1c035a2` |
| Daemon / configd | daemon PID `74577`; `configd` PID `32439`; `configctl devicemonitor status` healthy |
| Monitoring | `enabled=0`, `monitored_interfaces=""`, no WAL/SHM, `journal_mode=delete` |
| Database | SHA-256 `c17874a717cebe2c2e1dbaf537fd13a65b4ded47e10dfcce1849f2088136144e`; `integrity_check=ok`; 26 devices, 60 services, 2 identity events, 96 activity events |
| Device Monitor config | SHA-256 `027594eb735cf35e4b617163106031971567d0ba74027783e42cae46d37fd47d` |
| OPNsense config | `/conf/config.xml` SHA-256 `c2ce5800c76fcf8470283d6ada559fd6c2eba5a8e0372b409cc046afd8307abf` |
| DMTEST data | 3 device rows (`192.168.50.1` active + historical, `.50.180` historical) and 5 service rows on `192.168.50.1` |
| HA/CARP | no `carp` interface on `.23`; `ha_carp_enabled=1`, `ha_role_override=auto`, `ha_notify_failover=0` |
| Outbound-capable settings | `adguard_rewrite_enabled=1` with `adguard_url=http://192.0.2.53`; `pihole_enabled=0`; `webhook_enabled=0`; `identity_webhook_enabled=0`; `targeted_nmap_enabled=1` |
| Port discovery | one enabled target (`18:60:24:6a:64:8c`) with `next_scan_at=2026-11-07 15:55:31` (not due at preparation) |
| SMTP listener | nothing bound to `127.0.0.1:2525` |
| Free space | 2.7 GiB available on `/` (90% used); the backup set is only a few MiB |

The current empty selection fails closed: `scan_network.py --list-targets` returns exit `2` with
`ERROR: No monitored interfaces selected (monitored_interfaces is empty)`. This was observed and
must remain the expected behaviour whenever the temporary configuration is absent.

#### 9.4.0a Execution preflight — historical NO-GO checkpoint (superseded)

The authorised execution attempt stopped before mutation. Read-only checks at 12:40–12:47 AEDT
confirmed the host, `opt1`/DMTEST interface, daemon PID `74577`, `enabled=0`, empty
`monitored_interfaces`, no WAL/SHM, SQLite integrity `ok`, 26 devices, 60 services, 63 record rows,
19 core-locale files, no CARP interface, no `127.0.0.1:2525` listener and no due
port-discovery target. The enabled target `18:60:24:6a:64:8c` remains scheduled for
`2026-11-07 15:55:31`.

The accepted `/conf/config.xml` digest is `c2ce5800c76fcf8470283d6ada559fd6c2eba5a8e0372b409cc046afd8307abf`.
The live file is `80b5fb9de58404a9969c66a2621d5eddd95c3786fd3078b10a05313f54ac3f94` (mtime
`2026-11-06T12:40:38Z`). The XML diff against the accepted revision is limited to the Git Backup
`dest_type` (`<absent>` → `remote`), `force_push` (`0` → `1`) and revision timestamp; no Device
Monitor, interface or CARP value changed. The host also recorded Git Backup configuration revisions
at 12:30 and 12:40 while the preflight was running. This is still a departure from the recorded
accepted baseline, so no monitoring activation, scan, notification, daemon restart, database
migration, configuration edit or recovery start was performed.

The operator must let the host become quiescent and either restore the accepted configuration or
explicitly accept the new baseline before the full §9.4.2 gate is re-run. Do not edit
`/conf/config.xml` merely to make the hashes match. `$BASE/execute-s94.sh` was therefore not
assembled; the reviewed guard was retained and its directory-backup handling was corrected.

#### 9.4.0b Accepted baseline and final execution result

The operator accepted
`15ce9e6cde3798faa63e5ef3f48ada4c63ccd09e81d8e9d22b599360023831b4` as the current
`/conf/config.xml` baseline and preserved the Git Backup configuration. The final run completed
exactly two scans (`3497 → 3499`) and restored with `ACCEPTANCE=PASS`. The restored Device Monitor
configuration is `027594eb…` (byte-identical), the installation record is `d891ce68…`, the
OPNsense configuration is `15ce9e6c…`, and all 19 core-locale files match the guard backup. The
database is logically identical at `10460718…`; its physical bytes are `796d28c7…` after the
guard's consistent snapshot was copied back at `08:32:04Z`, so physical identity with the earlier
`c17874a7…` observation is not claimed. The saved evidence records the same 21 schema tables, the
same 26/60/2/96 counts and `notified_at` absent in both logical states. The original `c17874a7…`
bytes were not retained, so its header/page delta cannot be compared or reproduced; this remains
an unresolved acceptance discrepancy rather than a data-integrity failure.

The live `notified_at` mutation was directly observed before restoration: absent in the guard
snapshot, present in `live-after-discovery.txt` at `08:36:24Z` before monitoring was enabled at
`08:36:26Z`, and present after both cycles. The final absence is restoration evidence. The two
scheduled scans logged service discovery as not due; the five services were returned by the
separate direct `scan_network.py --discover-services` command. The two SMTP messages were direct PHP
helper invocations, and the copy-only fixtures do not prove live reminder, ageing, CARP or plugin
lifecycle behaviour. The service was transiently stopped during the supervised cleanup and manual
recovery then passed; the wrapper now retries the post-start status check within a bounded window.
The mock suite is 35 tests, all passing after the later physical-identity correction.

#### 9.4.1 Scope and hard limits

* Interface: `opt1` / `DMTEST`, device `vlan0.50`, `192.168.50.1/24`.
* Permitted network actions: one ICMP visibility pass over `192.168.50.2–254`, service probes to
  in-scope endpoints only (currently `192.168.50.1`), and the normal Hostwatch read.
* At most two 60-second daemon cycles, hard stop at 15 minutes.
* No LAN `192.168.20.0/24` probing, no subnet/range Nmap, no targeted Nmap, no webhook, no external
  SMTP, no AdGuard/Pi-hole call, no `.252`/`.253` access and no CARP failover.
* Monitoring is enabled only for the two cycles and is disabled again before the helper-email and
  fixture phases. The daemon is stopped for the mode-preserving setup and for the final
  database/config restoration; it is not restarted between the two cycles.

#### 9.4.2 Preconditions — stop before mutation if any differ

1. `hostname` is `OPNsense.internal`; `ifconfig` shows `192.168.20.23` and `vlan0.50` with
   `description: DMTEST (opt1)` and `192.168.50.1/24`.
2. Installed version is `2.14.0`; the 63-row record hash is `d891ce68…`; the candidate has not
   changed since the accepted deployment.
3. `enabled=0`, `monitored_interfaces=""`; no `devices.db-wal` or `devices.db-shm`; SQLite
   `integrity_check=ok`.
4. Daemon and configd are healthy; `configctl devicemonitor status` reports `running`.
5. `ifconfig carp` reports no CARP interface.
6. No enabled `port_discovery_targets` row has `next_scan_at <= datetime('now')`. If one is due,
   stop; do not silently disable it or run it.
7. At least 1 GiB free on `/`.
8. Nothing is listening on `127.0.0.1:2525`.

#### 9.4.3 Backup and pre-state snapshot

Create a private directory and capture a consistent SQLite copy, configuration, record, OPNsense
configuration, core-locale state/pristine archive and installer backup reference:

```sh
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
BASE=/root/dm-validation-2140/monitoring/$STAMP
install -d -m 700 -o root -g wheel "$BASE"

sqlite3 /var/db/devicemonitor/devices.db ".backup '$BASE/devices.db'"
sqlite3 "file:$BASE/devices.db?mode=ro" 'pragma integrity_check;'

cp -p /var/db/devicemonitor/config.json "$BASE/config.json"
cp -p /var/db/devicemonitor/installed-manifest.txt "$BASE/installed-manifest.txt"
cp -p /conf/config.xml "$BASE/opnsense-config.xml"
cp -Rp /var/backups/devicemonitor/core-locale "$BASE/core-locale"
tar -C /var/backups/devicemonitor -czf "$BASE/install-v214.qMPS7n.tgz" install-v214.qMPS7n

{
  sha256sum "$BASE/devices.db" "$BASE/config.json" "$BASE/installed-manifest.txt" \
    "$BASE/opnsense-config.xml"
  find "$BASE/core-locale" -type f -exec sha256sum {} \;
} > "$BASE/pre-state.sha256"

sqlite3 "$BASE/devices.db" .dump | sha256sum > "$BASE/devices.db.logical.sha256"
stat -f '%Sp %Su:%Sg %z %N' "$BASE/devices.db" "$BASE/config.json" \
  "$BASE/installed-manifest.txt" "$BASE/opnsense-config.xml" > "$BASE/pre-state.stat"
```

Verify the copied database by comparing its logical dump hash with the live database and by running
`pragma quick_check` and `pragma integrity_check`. Confirm the core-locale directory has 19 files.
Retain the existing `/root/dm-pre-2140` and installer backups unchanged.
The guard accepts either a file or the documented non-empty installer-backup directory; it archives
the directory recursively, verifies the archive is readable and non-empty, and rejects a missing or
empty backup before the watchdog is armed.

#### 9.4.4 Enforcement of interface scope and notification routing

These checks must be executed and recorded **before** enabling monitoring:

* **Interface restriction.** The temporary configuration sets `monitored_interfaces=opt1` only.
  `scan_network.py --list-targets` must print exactly:
  `opt1: description=DMTEST device=vlan0.50 subnet=192.168.50.0/24`
  and nothing else. A non-zero exit or any second subnet is a stop condition.
* **Disable outbound-capable features.** `adguard_rewrite_enabled` must be `0` for the test.
  The current live value is `1` pointing at `http://192.0.2.53`; leaving it enabled would make
  `full_scan()` attempt an outbound HTTP request and would violate this task's boundary. Also
  require `pihole_enabled=0`, `unbound_enabled=0`, `webhook_enabled=0`,
  `identity_webhook_enabled=0`, `targeted_nmap_enabled=0`, and no due port-discovery target.
* **Notification routing.** `email_enabled=0` during setup, discovery and the two cycles, so the
  daemon cannot emit a new-device or alert email accidentally. It becomes `1` only for the two
  direct helper calls, with `email_method=smtp`, `smtp_host=127.0.0.1`, `smtp_port=2525`,
  `smtp_encryption=none`, empty SMTP username/password, and
  `email_to=devicemonitor-test@example.invalid`. The `NotificationHandler` does not fall back
  from `smtp` to `sendmail` when direct SMTP fails, so a failed SMTP send remains a failure rather
  than an external delivery.
* **Loopback-only sink.** The sink must bind `127.0.0.1` explicitly and abort on any other bind
  address. After start, `sockstat -4l` must show only `127.0.0.1:2525`, never `0.0.0.0:2525` or
  `*:2525`. It records every SMTP envelope and message under `$BASE/smtp/`.
* **Connection guard.** While the sink and monitoring are active, sample `sockstat -c -4` once per
  second to `$BASE/sockstat.log`. After the test, reject any `python3`/`php` connection whose
  foreign address is not `127.0.0.1` or inside `192.168.50.0/24`.
* **Recipient assertion.** Every captured message must have `To: devicemonitor-test@example.invalid`
  and no other recipient. Any other recipient, or any message in the capture that was not produced
  by the two declared synthetic helper calls, is a stop condition.

#### 9.4.5 Temporary configuration

Apply these values only for the exercise. Preserve every other key byte-for-byte.

| Setting | Temporary value |
|---|---|
| `enabled` | `0` during setup and discovery; `1` only for the two cycles |
| `monitored_interfaces` | `opt1` |
| `scan_interval` | `60` |
| `visibility_prime_interval` | `86400` |
| `email_enabled` | `0` during setup/discovery/cycles; `1` only for the two helper calls |
| `email_to` / `email_from` | `devicemonitor-test@example.invalid` |
| `email_method` | `smtp` |
| `smtp_host` / `smtp_port` | `127.0.0.1` / `2525` |
| `smtp_encryption` | `none` |
| `smtp_username` / `smtp_password` | empty (current values are unset; do not copy credentials) |
| `identity_email_enabled` | `0` during the two cycles; `1` only for the identity helper call |
| `service_email_enabled` | `0` during the two cycles; `1` only for the service helper call |
| `adguard_rewrite_enabled` | `0` |
| `pihole_enabled` / `unbound_enabled` | `0` / `0` |
| `targeted_nmap_enabled` | `0` |
| `webhook_enabled` / `identity_webhook_enabled` | `0` / `0` |
| `email_reminder_identity`, `email_reminder_service`, `email_reminder_new_device`, `email_reminder_scan` | `0` for the live pass |
| `ha_carp_enabled` / `ha_role_override` / `ha_notify_failover` | preserve `1` / `auto` / `0` |

Write the configuration only while the daemon is stopped, using a mode-preserving replacement:

```sh
service devicemonitor stop
# wait until `pgrep -f monitor_daemon.py` is empty (up to 30 s)

python3 - "$BASE" <<'PY'
import json, os, sys
base = sys.argv[1]
original = json.load(open(base + '/config.json'))
config = dict(original)
changes = {
    'enabled': '0', 'monitored_interfaces': 'opt1', 'scan_interval': 60,
    'visibility_prime_interval': 86400, 'email_enabled': '0',
    'email_to': 'devicemonitor-test@example.invalid',
    'email_from': 'devicemonitor-test@example.invalid',
    'email_method': 'smtp', 'smtp_host': '127.0.0.1', 'smtp_port': 2525,
    'smtp_encryption': 'none', 'smtp_username': '', 'smtp_password': '',
    'identity_email_enabled': '0', 'service_email_enabled': '0',
    'adguard_rewrite_enabled': '0', 'pihole_enabled': '0', 'unbound_enabled': '0',
    'targeted_nmap_enabled': '0', 'webhook_enabled': '0',
    'identity_webhook_enabled': '0',
    'email_reminder_identity': 0, 'email_reminder_service': 0,
    'email_reminder_new_device': 0, 'email_reminder_scan': 0,
}
config.update(changes)
assert set(original) == set(config)
tmp = base + '/config.json.tmp'
with open(tmp, 'w') as handle:
    json.dump(config, handle, indent=2)
os.chmod(tmp, 0o600)
os.replace(tmp, '/var/db/devicemonitor/config.json')
PY

# Assert the diff contains exactly the intended keys and no others.
python3 - "$BASE" <<'PY'
import json, sys
base = sys.argv[1]
a = json.load(open(base + '/config.json'))
b = json.load(open('/var/db/devicemonitor/config.json'))
changed = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
print('CHANGED_KEYS=' + ','.join(changed))
PY

service devicemonitor start
```

The `CHANGED_KEYS` list must match the table above exactly. Record it in the evidence directory.
Do not print `smtp_password`, `adguard_password`, `pihole_password` or any other credential.

#### 9.4.6 Execution sequence

1. **Interface guard (no scan).** Run `--list-targets` and require the single `opt1` line above.
2. **Direct in-scope discovery (no daemon cycle).** With monitoring still `enabled=0`:

   ```sh
   /usr/local/bin/python3 \
     /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py \
     --discover-services > "$BASE/discover-services.out" 2>&1
   ```

   This probes only `192.168.50.1` for DHCP/DNS/NTP/SSH/WEB_ADMIN/PHASE3 evidence and records
   `service_discovery_state.last_run`. It does not send email. It may update `device_services`
   rows and `device_activity_events`; those changes are within the live-change list below.
3. **Start the loopback sink and guard.** Run the sink from §9.4.9 and confirm the listener is
   `127.0.0.1:2525` only. Start the `sockstat` sampler.
4. **Two monitoring cycles.** Record the baseline log count, then replace `enabled` with `1` only.
   The daemon reloads within 10 seconds and runs immediately, then again after 60 seconds:

   ```sh
   LOG=/var/log/devicemonitor.log
   BEFORE=$(grep -c 'Scan completed successfully' "$LOG")
   python3 - <<'PY'
   import json, os
   path = '/var/db/devicemonitor/config.json'
   config = json.load(open(path))
   assert config['enabled'] == '0', config['enabled']
   config['enabled'] = '1'
   tmp = path + '.tmp'
   with open(tmp, 'w') as handle:
       json.dump(config, handle, indent=2)
   os.chmod(tmp, 0o600)
   os.replace(tmp, path)
   PY

   for i in $(seq 1 36); do
     NOW=$(grep -c 'Scan completed successfully' "$LOG")
     if [ "$NOW" -ge $((BEFORE + 2)) ]; then break; fi
     sleep 5
   done
   ```

   Capture `devicemonitor.log`, waiting for at most two added `Scan completed successfully` lines
   (hard cap 180 seconds; the outer task cap is 15 minutes). Record the exact `Monitoring ENABLED`,
   `Running scheduled scan`, `Scan completed successfully`, visibility-priming and
   service-discovery lines.
5. **Disable monitoring.** Replace `enabled` with `0` and wait for `Monitoring DISABLED`:

   ```sh
   python3 - <<'PY'
   import json, os
   path = '/var/db/devicemonitor/config.json'
   config = json.load(open(path))
   assert config['enabled'] == '1', config['enabled']
   config['enabled'] = '0'
   tmp = path + '.tmp'
   with open(tmp, 'w') as handle:
       json.dump(config, handle, indent=2)
   os.chmod(tmp, 0o600)
   os.replace(tmp, path)
   PY
   # wait up to 30 s for the next 10-second daemon poll to log "Monitoring DISABLED"
   ```

   Do not leave a cycle running.
6. **Live helper emails.** With monitoring disabled, set `email_enabled=1`,
   `identity_email_enabled=1` and `service_email_enabled=1`, then invoke the installed email
   helpers directly. This exercises the deployed PHP `NotificationHandler` and the loopback SMTP
   transport, not the daemon's alert selector. `email_enabled=0` during the cycles is deliberate:
   it prevents a new-device or service alert from adding an unplanned message:

   ```sh
   printf '%s' '{"events":[{"detected_at":"2026-11-06 10:00:00","event_type":"IP_IDENTITY_CHANGED","severity":"high","mac":"02:00:00:00:00:01","other_mac":"02:00:00:00:00:02","ip":"192.168.50.1","other_ip":"192.168.50.2","interface":"opt1","other_interface":"opt1","details":"synthetic validation"}]}' \
     | /usr/local/bin/php \
       /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/notify_identity_mail.php \
       > "$BASE/identity-helper.out" 2>&1

   printf '%s' '{"events":[{"event_type":"SERVICE_UNAVAILABLE","alert_eligible":true,"occurred_at":"2026-11-06 10:00:00","service_type":"SSH","mac":"02:00:00:00:00:01","ip":"192.168.50.1","port":22,"protocol":"tcp","interface":"opt1","detection_method":"probe","confidence":"high","product":"synthetic","version":"0","old_value":"available","new_value":"unavailable"}]}' \
     | /usr/local/bin/php \
       /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/notify_service_email.php \
       > "$BASE/service-helper.out" 2>&1
   ```

   The identity email leg is `notify_identity_mail.php`. The similarly named
   `notify_identity_email.php` is the webhook leg and must not be used here. Require
   `{"result":"sent",...,"transport":"smtp"}` from both helpers and exactly two captured messages.
   Then set all three switches back to `0`.
7. **Stop the sink and guard.** Keep their logs and captures; do not delete them.
8. **Fixture checks (§9.4.7).** Run against private copies only, while the live daemon is still
   running with monitoring disabled or stopped for restoration. No fixture command may open the
   live database for writing.
9. **Restore and verify (§9.4.8).**

#### 9.4.7 Reminder, identity and O4 fixtures (copy-only)

The installed scanner has no `DB_FILE` environment override: `DB_FILE` is read from
`defaults.json` at import. The earlier instruction to redirect it with an environment variable was
incorrect. Use an in-process wrapper that sets the module global before calling functions, and pass
explicit connections wherever the function accepts one. This keeps every write on the copy.

```sh
mkdir -p "$BASE/fixtures"
cp -p "$BASE/devices.db" "$BASE/fixtures/devices.db"

cat > "$BASE/fixtures/fixture_runner.py" <<'PY'
import importlib.util
import json
import sqlite3
import sys
from datetime import datetime, timedelta

DB = sys.argv[1]
SRC = '/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py'
spec = importlib.util.spec_from_file_location('dm_fixture', SRC)
dm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dm)
dm.DB_FILE = DB
dm.CONFIG_FILE = DB + '.config-not-used.json'
dm.LOG_FILE = DB + '.fixture.log'

dm.init_db()  # copies only; applies the lazy notified_at migration to the copy
conn = sqlite3.connect(DB)
now = datetime.now()
fmt = '%Y-%m-%d %H:%M:%S'
old = (now - timedelta(hours=2)).strftime(fmt)

# Identity reminder fixture.
conn.execute(
    "INSERT INTO device_identity_events "
    "(mac,event_type,severity,detected_at,ip,interface,details,notified_at) "
    "VALUES (?,?,?,?,?,?,?,?)",
    ('02:00:00:00:00:11', 'IP_IDENTITY_CHANGED', 'high', old,
     '192.168.50.201', 'opt1', 'fixture reminder', old),
)
# Service repeat-reminder fixture.
payload = json.dumps({
    'event_type': 'SERVICE_UNAVAILABLE', 'service_type': 'SSH',
    'mac': '02:00:00:00:00:11', 'ip': '192.168.50.201', 'port': 22,
    'protocol': 'tcp', 'interface': 'opt1', 'alert_eligible': True,
})
conn.execute(
    "INSERT OR REPLACE INTO service_alert_pending "
    "(service_key,mac,event_json,held_at,notified,notified_at) VALUES (?,?,?,?,1,?)",
    ('fixture-service-key', '02:00:00:00:00:11', payload, old, old),
)
conn.commit()

identity = dm.get_pending_high_identity_reminders(
    conn, {'email_reminder_identity': 60})
service = dm.collect_service_alert_reminders(
    conn, {'email_reminder_service': 60}, now=now)
new_device = dm.rotation_announcement_due(
    conn, '02:00:00:00:00:11', '192.168.50.201',
    {'email_reminder_new_device': 60})

assert len(identity) == 1, identity
assert len(service) == 1 and service[0]['event_type'] == 'SERVICE_UNAVAILABLE', service
assert new_device is True, new_device
assert dm.get_pending_high_identity_reminders(
    conn, {'email_reminder_identity': 0}) == []
assert dm.collect_service_alert_reminders(
    conn, {'email_reminder_service': 0}, now=now) == []
assert dm.rotation_announcement_due(
    conn, '02:00:00:00:00:11', '192.168.50.201',
    {'email_reminder_new_device': 0}) is False

# O4 fixtures on the same copy: fresh host, old host, stale unavailable verdict.
fresh = (now - timedelta(hours=1)).strftime(fmt)
unseen = (now - timedelta(days=40)).strftime(fmt)
stale = (now - timedelta(days=8)).strftime(fmt)
for mac, ip, last_seen, active in (
    ('02:00:00:00:00:21', '192.168.50.211', fresh, 1),
    ('02:00:00:00:00:22', '192.168.50.212', unseen, 0),
    ('02:00:00:00:00:23', '192.168.50.213', fresh, 1),
):
    conn.execute(
        "INSERT OR REPLACE INTO devices (mac,ip,vlan,is_active,first_seen,last_seen) "
        "VALUES (?,?,?,?,?,?)", (mac, ip, 'VLAN50', active, unseen, last_seen))
for mac, ip, status, checked in (
    ('02:00:00:00:00:21', '192.168.50.211', 'available', fresh),
    ('02:00:00:00:00:22', '192.168.50.212', 'available', unseen),
    ('02:00:00:00:00:23', '192.168.50.213', 'unavailable', stale),
):
    conn.execute(
        "INSERT INTO device_services "
        "(mac,ip,interface,service_type,port,protocol,status,detection_method,"
        "confidence,first_detected,last_verified,last_checked,miss_count) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,0)",
        (mac, ip, 'opt1', 'SSH', 22, 'tcp', status, 'probe', 'high',
         unseen, checked, checked))
conn.commit()
aged, retired = dm.age_stale_service_state(conn, now=now, dry_run=False)
assert aged == 1, aged
assert retired == 1, retired
assert conn.execute(
    "SELECT status FROM device_services WHERE ip='192.168.50.213'"
).fetchone()[0] == 'unknown'
assert conn.execute(
    "SELECT COUNT(*) FROM device_services WHERE ip='192.168.50.211'"
).fetchone()[0] == 1
assert conn.execute(
    "SELECT COUNT(*) FROM device_services WHERE ip='192.168.50.212'"
).fetchone()[0] == 0
print('FIXTURE_PASS identity=1 service=1 new_device=1 aged=1 retired=1')
conn.close()

# Separate no-fresh-host copy, derived from the already-migrated fixture DB so
# the schema is exact. Retirement must refuse when no host is fresh.
import shutil
shutil.copy2(DB, DB + '.nofresh')
conn = sqlite3.connect(DB + '.nofresh')
conn.execute("DELETE FROM device_services")
conn.execute("DELETE FROM devices")
conn.execute(
    "INSERT INTO devices (mac,ip,vlan,is_active,first_seen,last_seen) "
    "VALUES (?,?,?,?,?,?)",
    ('02:00:00:00:00:31', '192.168.50.221', 'VLAN50', 0, unseen, unseen))
conn.execute(
    "INSERT INTO device_services "
    "(mac,ip,interface,service_type,port,protocol,status,detection_method,"
    "confidence,first_detected,last_verified,last_checked,miss_count) "
    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,0)",
    ('02:00:00:00:00:31', '192.168.50.221', 'opt1', 'SSH', 22, 'tcp',
     'available', 'probe', 'high', unseen, unseen, unseen))
conn.commit()
aged2, retired2 = dm.age_stale_service_state(conn, now=now, dry_run=False)
assert aged2 == 0, aged2
assert retired2 == 0, retired2
print('NO_FRESH_HOST_REFUSAL_PASS aged=0 retired=0')
conn.close()
PY

/usr/local/bin/python3 "$BASE/fixtures/fixture_runner.py" "$BASE/fixtures/devices.db" \
  > "$BASE/fixtures/fixture.out" 2>&1
```

The no-fresh-host file is copied from the already-migrated fixture database, so it carries the exact
schema. The assertions above are the minimum; do not weaken them to accommodate a simplified schema.

These are **fixture results**, not live monitoring results. They cover reminder selection, identity
reminder selection, new-device/MAC-rotation reminder timing, O4 ageing, O4 retirement, preservation
of a fresh host and the no-fresh-host refusal. They do not prove that the live daemon would emit
those alerts; the live evidence covers discovery, two scan cycles and the two direct email helpers.

#### 9.4.8 Expected live changes and restoration

Expected live changes while the exercise is active:

* `init_db()` on the first full scan adds the nullable
  `device_identity_events.notified_at` column. **The `notified_at` migration is exercised on the
  live database**, not only on a copy. It is an additive schema migration; the pre-test database
  backup restores the pre-migration schema at the end. If the column is already present, record
  that and do not claim the migration ran.
* `service_discovery_state.last_run` changes during the direct discovery pass; `carp_role` may be
  written from its previous empty value to the detected non-HA role.
* DMTEST `devices` rows may update `last_seen`, `is_active`, lifecycle metadata and
  `device_activity_events`.
* `device_services` rows for `192.168.50.1` may update `last_checked`, status, miss counters and
  activity history during direct discovery. No service row outside `192.168.50.0/24` may change.
* The two helper calls must produce exactly two local SMTP captures and no other message.
* O4 ageing/retirement is **not** run against the live database; it is fixture-only in this plan.

Restoration after the daemon is stopped:

```sh
service devicemonitor stop
# wait until no monitor_daemon.py and no scan_network.py process remains

cp -p "$BASE/config.json" /var/db/devicemonitor/config.json
cp -p "$BASE/devices.db" /var/db/devicemonitor/devices.db
rm -f /var/db/devicemonitor/devices.db-wal /var/db/devicemonitor/devices.db-shm

service devicemonitor start
```

Only remove WAL/SHM files if they were created by this exercise, the daemon is stopped and the
restored database has passed `integrity_check`. Never delete a pre-existing sidecar.

Post-restoration acceptance:

* `config.json`, `devices.db`, `installed-manifest.txt` and `/conf/config.xml` hashes match
  `pre-state.sha256`; the restored database logical dump hash matches
  `devices.db.logical.sha256`.
* SQLite `quick_check=ok`, `integrity_check=ok`, `journal_mode=delete`, no WAL/SHM.
* `enabled=0`, `monitored_interfaces=""`; log contains `Monitoring DISABLED`; daemon and configd
  healthy; `configctl devicemonitor status` = `running`.
* The 63-row record hash is unchanged and no installed target changed.
* DMTEST device/service counts return to the pre-state counts.
* No listener remains on `127.0.0.1:2525`; the sink and sampler processes are gone.
* The `sockstat` guard shows no `python3`/`php` connection outside loopback or
  `192.168.50.0/24`.

#### 9.4.9 Loopback SMTP sink (create at execution, never bind wider)

```sh
cat > "$BASE/smtp-sink.py" <<'PY'
#!/usr/local/bin/python3
import argparse, json, os, socketserver, threading, time

class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.wfile.write(b'220 dm-validation sink\r\n')
        envelope = {'mail_from': '', 'rcpt_to': []}
        while True:
            line = self.rfile.readline()
            if not line:
                return
            text = line.decode('utf-8', 'replace').rstrip('\r\n')
            with open(os.path.join(CAPTURE, 'commands.log'), 'a') as log:
                log.write(text + '\n')
            upper = text.upper()
            if upper.startswith('EHLO') or upper.startswith('HELO'):
                self.wfile.write(b'250-dm-validation\r\n250 SIZE 10485760\r\n')
            elif upper.startswith('MAIL FROM:'):
                envelope['mail_from'] = text[10:].strip()
                self.wfile.write(b'250 OK\r\n')
            elif upper.startswith('RCPT TO:'):
                envelope['rcpt_to'].append(text[8:].strip())
                self.wfile.write(b'250 OK\r\n')
            elif upper == 'DATA':
                self.wfile.write(b'354 End data with <CR><LF>.<CR><LF>\r\n')
                data = []
                while True:
                    chunk = self.rfile.readline()
                    if not chunk or chunk in (b'.\r\n', b'.\n'):
                        break
                    data.append(chunk)
                name = 'message-%d.eml' % int(time.time() * 1000)
                with open(os.path.join(CAPTURE, name), 'wb') as out:
                    out.write(('X-Envelope-From: %s\r\nX-Envelope-To: %s\r\n' % (
                        envelope['mail_from'], ', '.join(envelope['rcpt_to']))).encode())
                    out.writelines(data)
                with open(os.path.join(CAPTURE, 'envelopes.jsonl'), 'a') as out:
                    out.write(json.dumps(envelope) + '\n')
                self.wfile.write(b'250 queued\r\n')
            elif upper == 'QUIT':
                self.wfile.write(b'221 bye\r\n')
                return
            elif upper in ('RSET', 'NOOP'):
                self.wfile.write(b'250 OK\r\n')
            else:
                self.wfile.write(b'250 OK\r\n')

parser = argparse.ArgumentParser()
parser.add_argument('--bind', required=True)
parser.add_argument('--port', type=int, required=True)
parser.add_argument('--capture', required=True)
args = parser.parse_args()
if args.bind != '127.0.0.1':
    raise SystemExit('refusing non-loopback bind')
CAPTURE = args.capture
os.makedirs(CAPTURE, mode=0o700, exist_ok=True)
class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
Server((args.bind, args.port), Handler).serve_forever()
PY
chmod 700 "$BASE/smtp-sink.py"
```

Start it only at execution time, after the interface guard, with
`--bind 127.0.0.1 --port 2525 --capture "$BASE/smtp"`. Verify with
`sockstat -4l | grep 2525` that the local address is exactly `127.0.0.1:2525`.

#### 9.4.10 Stop conditions

Stop and restore immediately on any of the following:

* a resolved target or probe outside `192.168.50.0/24`; any connection to `192.168.20.0/24`,
  `.252`, `.253`, an external SMTP server, a webhook or AdGuard/Pi-hole;
* an SMTP listener address other than `127.0.0.1:2525`, or a captured recipient other than
  `devicemonitor-test@example.invalid`;
* a port-discovery target becoming due; a targeted/manual Nmap scan; any full-range Nmap scan; or
  any Nmap destination outside `192.168.50.0/24`. Device Monitor's bounded Phase 3 SMB
  `smb-protocols` verification is permitted only as a synchronous call against one literal
  in-scope candidate after TCP/445 accepts a connection; record its process arguments. The former
  blanket “an Nmap process” wording was too broad and would have failed the reviewed service
  discovery path;
* a CARP role change or a second daemon process;
* a database integrity error, unexpected schema/data loss, or a failure to restore the saved
  hashes;
* more than two scan cycles, or the 15-minute hard stop;
* any change to the installed 2.14.0 target set or 63-row record.

This section does not authorise `FRESH=1`, a live rollback, configd restart, firewall changes,
monitoring beyond the two cycles, or any `.252`/`.253` contact.

#### 9.4.11 Prepared execution wrapper and exact approval commands

**Status: COMPLETE / ACCEPTANCE PASS — further execution is unauthorised; see the `EXECUTION-20261106.md` caveats.** The reviewed wrapper is
`verification/monitoring-validation/guard.py`; its mock-only suite is
`verification/monitoring-validation/test_guard.py`. The corrected wrapper starts a watchdog in a new
POSIX session, serializes cleanup with `flock`, stops the daemon and every
`monitor_daemon.py`/`scan_network.py` writer, verifies no writer remains, then captures a
byte-preserving original database recovery copy together with any `-wal`/`-shm` sidecars. It also
records a separate consistent SQLite snapshot as an independently verified fallback. Before
restoration it archives the current database and sidecars, restores the original recovery bytes and
metadata, verifies them against the original physical hash plus schema/data/integrity checks, starts
the daemon only after that verification, and cancels the watchdog only after a PASS. Snapshot
equivalence cannot satisfy original-byte identity. A timeout, payload failure or
`SIGINT`/`SIGTERM`/`SIGHUP` takes the same restoration path. A failed capture or restoration leaves
the service stopped, retains the evidence directory and does not create the watchdog cancel marker.
A late watchdog observes an existing PASS and does not restore again.

The mock suite has 35 passing cases covering detached watchdog start, timeout, interruption,
overlap rejection, writer blocking, stop-before-restore ordering, restoration failure retention,
post-restore service failure, exact `notified_at` rollback, approved scope acceptance, rejected
interface/email/SMTP/AdGuard/targeted-Nmap settings, sockstat detection and two-message SMTP
acceptance including the latest `Monitoring DISABLED` log state, plus installer-backup directory
archiving, empty-directory rejection and bounded transient-configd status recovery. The physical
identity cases prove that logically equal but physically different snapshots are distinguished,
that normalised snapshot bytes fail original-byte acceptance, that original bytes pass, that current
WAL/SHM is archived before replacement, that a real uncheckpointed WAL/SHM pair is captured and
restored exactly, and that unsafe capture or restoration leaves monitoring stopped. These are
isolated fixtures; the live evidence is separately recorded. The correction was
made after the completed exercise and cannot retroactively prove its original bytes.

After one separate execution approval, use this exact sequence from an interactive root shell on
`.23`. `$BASE` is the private `0700` directory created by §9.4.3. Do not run any command below
before that approval.

```sh
set -eu
GUARD=/root/src/opnsense-devicemonitor-upstream/verification/monitoring-validation/guard.py
# BASE must already be the §9.4.3 timestamped private directory.
STATE="$BASE/guard/guard-state.json"

# Read-only host, record/target-set, interface, listener, DB and due-target gate.
python3 "$GUARD" preflight \
  --config /var/db/devicemonitor/config.json \
  --db /var/db/devicemonitor/devices.db \
  --record /var/db/devicemonitor/installed-manifest.txt \
  --opnsense-config /conf/config.xml \
  --space-path /

# Back up all reviewed assets and start the detached 15-minute watchdog.
python3 "$GUARD" begin \
  --base "$BASE/guard" \
  --config /var/db/devicemonitor/config.json \
  --db /var/db/devicemonitor/devices.db \
  --record /var/db/devicemonitor/installed-manifest.txt \
  --opnsense-config /conf/config.xml \
  --core-locale /var/backups/devicemonitor/core-locale \
  --installer-backup /var/backups/devicemonitor/install-v214.qMPS7n \
  --timeout-seconds 900 \
  --lock-wait-seconds 30 \
  --stop-wait-seconds 30

# Apply §9.4.5 with the daemon stopped, then resolve and statically check the one approved target.
/usr/local/bin/python3 \
  /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py \
  --list-targets > "$BASE/targets.txt"
python3 "$GUARD" scope-check \
  --config /var/db/devicemonitor/config.json \
  --targets-file "$BASE/targets.txt" \
  --scan-source /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py \
  --notification-source /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/NotificationHandler.php \
  --smtp-source /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/smtp_send.py \
  --identity-source /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/notify_identity_mail.php

# Run the reviewed §9.4.4-§9.4.9 payload in one process group under the watchdog.
# execute-s94.sh must start the loopback sink and sockstat sampler as its children.
python3 "$GUARD" run --state "$STATE" --payload /bin/sh "$BASE/execute-s94.sh"
```

`scope-check` fails closed unless `monitored_interfaces=opt1`, the only resolved target is
`opt1: description=DMTEST device=vlan0.50 subnet=192.168.50.0/24`, AdGuard/Pi-hole/Unbound/webhook/
identity-webhook/targeted-Nmap are disabled, SMTP is `127.0.0.1:2525` with no credentials and the
single test recipient, and the deployed source still constructs probes/targeted scans from the
selected networks or one literal in-scope IPv4 target. The source check also proves that the SMB
Nmap path is one literal candidate and that the SMTP branch cannot fall back to sendmail. It does
not treat `sockstat` sampling as enforcement; the sampler is retrospective detection only.

**Execution result:** the accepted baseline was rechecked immediately before mutation and the
single bounded run completed; further execution is unauthorised. Live evidence covers two scheduled
inventory scans, direct DMTEST-only service discovery, scope-limited visibility probing and the
`notified_at` mutation observed before restoration. The two loopback SMTP messages came from direct
PHP helper invocations, not daemon-generated delivery; identity/service/new-device/aged/retired and
fresh-host refusal were copy-only fixtures. Scheduled daemon-triggered service discovery, full
reminder/ageing/CARP and real plugin lifecycle remain untested. The guard-level timeout,
interruption, overlap, writer and restoration checks remain fixture-validated; the live run exercised
the normal two-cycle path. A supervised post-start status call saw a transient configd socket and
required idempotent manual recovery; the final `restore.status` is `PASS`, and the wrapper retry
correction is fixture-tested. The database is logically identical at `10460718…`, but its physical
bytes are `796d28c7…` rather than the earlier live `c17874a7…`; the saved consistent snapshot
explains the page-layout difference, and byte-identical restoration is not claimed.

If the payload is interrupted, or `status` shows that the watchdog did not complete recovery, use
the idempotent manual recovery command. A second concurrent recovery cannot restore while another
holds the cleanup lock, and restoration is refused while a daemon/scan writer remains:

```sh
python3 "$GUARD" status --state "$STATE"
python3 "$GUARD" recover --state "$STATE"
python3 "$GUARD" status --state "$STATE"
```

If `recover` cannot restore, do not start the service manually. Leave monitoring stopped and retain
`$BASE`, `$BASE/guard/restore.status`, `$BASE/guard/guard-events.jsonl`, the watchdog log, sockstat
evidence and SMTP capture for diagnosis.

Final read-only acceptance:

```sh
python3 "$GUARD" accept \
  --state "$STATE" \
  --sockstat-log "$BASE/sockstat.log" \
  --smtp-capture "$BASE/smtp"
```

Acceptance requires the restored Device Monitor configuration, installation record, OPNsense
configuration and core-locale files to match the accepted/guard pre-state; the restored live
database must match the guard's verified consistent snapshot physically and match the earlier live
database logically. The physical database hash comparison is against the guard snapshot
(`796d28c7…`), not the earlier live file (`c17874a7…`), because the guard intentionally records a
consistent SQLite backup. This proves restoration to the snapshot, not original-byte identity; the
investigation found no retained copy of the original bytes. Acceptance also requires SQLite
`integrity_check=ok`, no WAL/SHM,
`enabled=0`, empty `monitored_interfaces`, a running daemon, no scan process, no listener on 2525,
exactly two approved SMTP captures, and no Python/PHP sockstat connection outside loopback or
`192.168.50.0/24`. Exit `ACCEPTANCE=PASS` is the only acceptable final result. It reports
`CONNECTIONS=SOCKSTAT_DETECTION_ONLY`; no firewall rule is changed by the wrapper. The physical
database difference from the earlier live file remains an unresolved acceptance discrepancy.

### 9.5 Recommended execution order and bounded authorisation

1. **Authenticated About/Features evidence** — operator browser only, no host mutation.
2. **Fresh-install jail scenarios** — harness-only implementation and execution, no live mutation.
3. **Live rollback cycle on `.23`** — package/service lifecycle only, after reviewing steps 1–2.
4. **Bounded monitoring exercise on `.23`** — temporary DMTEST-only config/DB exercise, local SMTP
   capture, exact restoration, after reviewing step 3.

Each step is a separate authorisation gate. The exact permission needed is:

* Step 1: use of an existing authenticated browser session and retention of sanitised screenshots,
  console text and endpoint response.
* Step 2: edit the isolated sandbox harness and run `fresh` plus `fresh-rollback` in a disposable
  FreeBSD jail; no live installation and no host service change.
* Step 3: on `.23` only, perform the documented 2.13.3 → 2.14.0 → rollback → 2.14.0 cycle, including
  daemon stop/wait/start, real configd restart, temporary observation interruption, verified
  backups, and recovery only through the reviewed helper sequence.
* Step 4: on `.23` only, temporarily enable monitoring for `opt1`/DMTEST for at most two cycles,
  perform the listed in-scope probes, use only a loopback SMTP sink, make the listed temporary
  config/database changes, then restore the exact pre-test state. No external notification,
  targeted Nmap, LAN probe, CARP change or `.252`/`.253` access. This approval also covers
  stopping and starting the Device Monitor daemon for the mode-preserving config/database
  replacement and restoration; it does **not** cover a `configd` restart, firewall changes,
  installation, `FRESH=1`, or any rollback exercise.

**Current execution result:** steps 1–3 are complete. Step 1 passed on operator-supplied
authenticated visual evidence; no Network capture was supplied. Step 2 passed both isolated jail
scenarios and left the live installation unchanged. Step 3 passed the controlled preparatory
reset, test installation, live successful-install rollback and final 2.14.0 reinstall. Step 4
(monitoring-enabled behaviour) is **COMPLETE / ACCEPTANCE PASS** within the documented boundary and
further execution is **unauthorised**: two cycles, separate direct DMTEST-only discovery, loopback
SMTP capture from direct helpers, copy-only fixtures and logical restoration with monitoring
disabled. The live `notified_at` mutation was observed before restoration. Physical database bytes
changed from `c17874a7…` to the verified consistent snapshot `796d28c7…` when guard recovery copied
its snapshot back at `08:32:04Z`; schema/data checks match, but the original bytes were never
retained and the header/page delta cannot be reconstructed. The guard was subsequently corrected to
capture original bytes only after writer stop, preserve WAL/SHM explicitly, restore the original
recovery copy, and verify physical identity independently of the SQLite snapshot; that correction
does not retroactively validate the historical bytes. Full live
reminder/ageing/CARP and real plugin lifecycle were not proven. No live `FRESH=1`, outbound
notification, commit, push or deployment was performed. DM-BL-009 and issue #5 remain **OPEN**;
§9.4 is paused and further execution is unauthorised.
