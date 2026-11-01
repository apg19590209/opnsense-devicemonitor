# Device Monitor deployment

Production was found running a `scan_network.py` that existed in **no commit**
(9225 lines, 377 changed lines of drift against the nearest branch tip). These
scripts exist so that cannot happen again: appliances are installed from a git
ref only, they record exactly what was installed, and they check themselves
against that record once a day.

## Files

| Script | Runs on | Purpose |
|---|---|---|
| `publish-devicemonitor.sh` | the workstation holding the checkout | Builds a payload from a git ref and deploys it to the nodes |
| `deploy-devicemonitor.sh` | each appliance (invoked by publish, or by hand with a staging dir) | Verifies the payload, backs up, installs atomically, records the manifest, restarts, smoke-tests |
| `verify-devicemonitor.sh` | each appliance (installed into the plugin dir, run daily from `/etc/cron.d/devicemonitor-drift`) | Compares installed files to the manifest; reports drift |

## Deploying

```sh
cd /usr/local/cline-freebsd/src/cline

# HA pair: the jump host is the MASTER, the peer is reached through it
NODES="LOCAL root@192.168.20.252" deploy/publish-devicemonitor.sh \
    origin/fix/scan-loop-and-alert-noise-20261101
```

`REF` can be any branch, tag or commit. Files always come from `git cat-file`,
never from a working tree, so uncommitted edits cannot be deployed by accident.

Each target:

1. hashes every staged file against `MANIFEST` and aborts before writing
   anything on a mismatch,
2. copies the files it is about to replace to
   `/root/devicemonitor-deploy-backup-<timestamp>/`,
3. installs atomically (`cp` to a temp name, then `mv`), 755 for scripts and
   `rc.d`, 644 otherwise,
4. writes `/var/db/devicemonitor/deployed.manifest` (every path + md5, with the
   ref and commit on the first line) and `/var/db/devicemonitor/deployed.json`,
5. restarts `devicemonitor` and fails the deploy unless a scan cycle completes
   cleanly within 120 s,
6. runs the drift check it just installed.

## Drift detection

```sh
/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/verify-devicemonitor.sh
```

Exit codes: `0` clean, `1` drift, `2` no manifest (never deployed this way).

It flags:

* a tracked file that is missing,
* a tracked file whose md5 differs (someone hand-edited the appliance),
* a code file (`*.py *.php *.sh *.inc *.volt *.conf *.json *.xml *.js`) inside
  the plugin tree that is not in the manifest — the exact failure mode that let
  production run uncommitted code.

Backup artefacts (`*.bak*`, `*.orig`, `*.pre-*`, `*.pyc`, `*.mo`, `*~`) are
ignored. Results are appended to `/var/log/devicemonitor-drift.log` and sent to
syslog as `devicemonitor-drift`.

The daily job is installed by the deploy script:

```
/etc/cron.d/devicemonitor-drift
17 4 * * * root /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/verify-devicemonitor.sh >/dev/null 2>&1
```

## Rollback

Files are plain copies; restore from the backup taken by the deploy:

```sh
cd /root/devicemonitor-deploy-backup-<timestamp>
find . -type f | while read -r f; do cp -p "$f" "/$f"; done
/usr/sbin/service devicemonitor restart
```

Re-deploying an older ref is the supported path:

```sh
NODES="LOCAL root@192.168.20.252" deploy/publish-devicemonitor.sh <older-ref>
```
