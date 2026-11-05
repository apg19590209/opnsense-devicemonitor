# OPNsense 26.7.8 update record — the `.23` testbed

**Status: EXECUTED AND VERIFIED on 5 November 2026.** The `.23` testbed was updated through the
supported `configctl firmware update` path, rebooted, and checked by
`/root/dm-os-26.7.8-postboot-check.sh`. Device Monitor 2.13.3 remained installed and monitoring
stayed disabled. Production and `.252`/`.253` were not contacted; no release or tag was changed.

## Execution record

| Item | Actual result |
|---|---|
| Pre-update OS | OPNsense `26.7.7`; FreeBSD `15.1-RELEASE-p3 amd64` |
| Applied offer | `opnsense 26.7.8_2`, `opnsense-update 26.7.8`, base and kernel `26.7.8`; 48 upgrades, 7 reinstalls, 0 removals, 0 downgrades |
| Action | `configctl firmware update` — not `firmware upgrade`, `pkg upgrade`, or `FRESH=1` |
| Reboot | Completed; boot time `Thu Nov 5 19:46:14 2026 AEDT` (`kern.boottime`) |
| Post-update OS | OPNsense `26.7.8_2`; FreeBSD `15.1-RELEASE-p6 amd64` |
| Firmware state | `configctl firmware running` returned `ready`; the update log ends with `Please reboot.` / `***REBOOT***` |
| Device Monitor | `2.13.3`; monitoring `enabled=0`; no SQLite WAL |
| Payload record | 61 targets, 61 digest rows, 21 `.mo` targets; sha256 `0afb4e4e68edd331f22c88ef559dd1163af0baaaba0cd77a76b3ed672c17dea7` |
| Database | `c17874a717cebe2c2e1dbaf537fd13a65b4ded47e10dfcce1849f2088136144e` — unchanged |
| Device Monitor configuration | `8115a7eee5104e4ddad4a508caf06cbbe1822ee9722578db527104b366cb1c22` — unchanged |
| Target verification | All 61 targets matched their record digest and pre-update snapshot digest, mode and ownership |
| Services | configd PID 639 and Device Monitor PID 34058 running; `configctl -w 5 devicemonitor status` returned `running` |
| Management | `re0` retained `192.168.20.23`; HTTPS listener present |
| Post-boot result | `POSTBOOT_RESULT=PASS`, `targets_checked=61`; evidence `/root/dm-os-26.7.8-postboot-evidence.txt` and `/root/dm-os-26.7.8-postboot-status.txt` |
| Pre-update backup | `/root/dm-os-26.7.8-preupdate`; encrypted archive `/root/dm-os-26.7.8-preupdate.tar.gz.enc`, 26,470,432 bytes, sha256 `64986b9a7564b28c53200af664f4247198d125e0748baecf8732f83909749934` |
| Off-host verification | The operator confirmed the Windows archive and passphrase-file hashes match and retained the passphrase separately; no passphrase material is recorded here |
| OPNsense configuration | Pre-update automatic backup `config-1792253831.0427.xml` (sha256 `4b30c2b2e3b1be8ddf66ffb869e752ba3f1c6be9df8b8ef54358d4d0608efb45`); the update generated `config-1793868107.8517.xml`, byte-identical to the current `/conf/config.xml` (sha256 `cbba358a646aaeb28aa63dccafdd5e971a437c21637466493e415b17b67df61b`, mode `0640`, owner `wwwonly:wheel`) |
| Codex dependency repair | Codex initially failed after reboot because `libdbus-1.so.3` was missing; `dbus-1.16.2_4,1` was installed from the OPNsense repository and `codex-cli 0.165.0` now starts |
| Remaining warning | The update log records one package-audit warning: `libgpg-error-1.61` has a known vulnerability. This was not a failed update or Device Monitor check and was not remediated in this task |

The update created a new OPNsense automatic configuration backup as part of its normal operation.
That does not mean Device Monitor configuration changed: the Device Monitor configuration,
database and installation record remained byte-identical to the pre-update baseline.

No post-boot Device Monitor or service check failed. Rollback was not invoked. The root filesystem
is UFS without ZFS boot environments, so this record does not claim an OS-version rollback test.
`FRESH=1` remains untested, and DM-BL-009 remains **OPEN**.

The procedure below preserves the reviewed pre-update plan; the execution record above is the
authoritative outcome. Do not repeat the update as part of this record.

## Pre-update baseline (preserved)

Recorded before the OS update, after the successful 2.13.3 deployment on 5 November 2026:

| Item | Value |
|---|---|
| Host | `OPNsense.internal`, `re0=192.168.20.23` |
| OS | OPNsense `26.7.7`; FreeBSD `15.1-RELEASE-p3 amd64` |
| Root filesystem | `/dev/gpt/rootfs` on UFS with soft updates; **no ZFS datasets or boot environments** |
| Device Monitor | `2.13.3`, monitoring disabled |
| Payload record | 61 digest rows, 21 `.mo` targets, `sha256 0afb4e4e68edd331f22c88ef559dd1163af0baaaba0cd77a76b3ed672c17dea7` |
| Database | `/var/db/devicemonitor/devices.db`, `sha256 c17874a717cebe2c2e1dbaf537fd13a65b4ded47e10dfcce1849f2088136144e` |
| Device Monitor config | `/var/db/devicemonitor/config.json`, `sha256 8115a7eee5104e4ddad4a508caf06cbbe1822ee9722578db527104b366cb1c22` |
| Deployment bundle | `/root/dm-deploy-2133/dm-v2.13.3-runtime.tar.gz`, 1,656,468 bytes, `sha256 7f389248707cf8fa0684760820db85c0fddac4b8b3964e0563318b38b2730fe2` |
| Installer rollback asset | `/var/backups/devicemonitor/install-v213.xKjyg1` |
| Pre-2.13.3 backup | `/root/dm-pre-2133` |

The applied target was the `26.7.8` release line. The live firmware check offered
`opnsense 26.7.8_2`, `opnsense-update 26.7.8`, and base/kernel `26.7.8`; `opnsense-version` and
the update log agree that the post-update host is `OPNsense 26.7.8_2`.

## Pre-update configuration backup (historical)

OPNsense currently has 60 automatic configuration backups under `/conf/backup`. The latest one,
`/conf/backup/config-1792253831.0427.xml`, is byte-identical to `/conf/config.xml`; both are mode
`0640`, owner `wwwonly:wheel`, size 66,711 bytes, SHA-256
`4b30c2b2e3b1be8ddf66ffb869e752ba3f1c6be9df8b8ef54358d4d0608efb45`. These files contain
credentials and keys; never print their contents or copy them into the repository.

Before the update, make a fresh root-only backup and preserve a copy off the firewall:

```sh
set -eu
umask 077
OSPRE=/root/dm-os-26.7.8-preupdate
test ! -e "$OSPRE"
mkdir -m 700 "$OSPRE"

cp -p /conf/config.xml "$OSPRE/config.xml"
cp -p /conf/backup/config-1792253831.0427.xml "$OSPRE/config-auto-latest.xml"
cp -p /root/dm-deploy-2133/dm-v2.13.3-runtime.tar.gz "$OSPRE/"
cp -p /var/db/devicemonitor/config.json "$OSPRE/devicemonitor-config.json"
cp -p /var/db/devicemonitor/installed-manifest.txt "$OSPRE/devicemonitor-installed-manifest.txt"
cp -Rp /var/backups/devicemonitor/core-locale "$OSPRE/devicemonitor-core-locale"

python3 - "$OSPRE/devices.db" <<'PY'
import sqlite3, sys
src = sqlite3.connect('file:/var/db/devicemonitor/devices.db?mode=ro', uri=True)
dst = sqlite3.connect(sys.argv[1])
src.backup(dst)
assert dst.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
assert dst.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
dst.close()
src.close()
PY
chmod 600 "$OSPRE/devices.db"

python3 - <<'PY'
import xml.etree.ElementTree as ET
ET.parse('/root/dm-os-26.7.8-preupdate/config.xml')
print('CONFIG_XML=valid')
PY
sha256 -q "$OSPRE/config.xml"
sha256 -q "$OSPRE/config-auto-latest.xml"
CONFIG_SHA=4b30c2b2e3b1be8ddf66ffb869e752ba3f1c6be9df8b8ef54358d4d0608efb45
[ "$(sha256 -q "$OSPRE/config.xml")" = "$CONFIG_SHA" ]
[ "$(sha256 -q "$OSPRE/config-auto-latest.xml")" = "$CONFIG_SHA" ]
cmp -s "$OSPRE/config.xml" "$OSPRE/config-auto-latest.xml"

tar -czf /root/dm-os-26.7.8-preupdate.tgz -C /root dm-os-26.7.8-preupdate
chmod 600 /root/dm-os-26.7.8-preupdate.tgz
sha256 -q /root/dm-os-26.7.8-preupdate.tgz
tar -tzf /root/dm-os-26.7.8-preupdate.tgz
```

Record the printed digests. Download the configuration through the OPNsense
**System → Configuration → Backups** page and transfer `/root/dm-os-26.7.8-preupdate.tgz` over the
approved encrypted management channel to the operator's encrypted workstation storage. The archive
contains configuration, credentials and Device Monitor state; never paste its contents into the
repository or a report and never send it over an unencrypted channel. Merely keeping it under
`/root` on the same UFS disk is not an off-host disaster-recovery copy.

Preserve but do not delete `/root/dm-pre-2133`, `/var/backups/devicemonitor/install-v213.xKjyg1`,
or the historical Device Monitor backups.

## Update procedure (historical)

The sequence below is the reviewed pre-execution procedure. The executed action was
`configctl firmware update`; it must not be repeated as part of this record.

Use an out-of-band/console path: a kernel/base update may reboot the firewall and interrupt SSH.
No other firmware operation may be running. Confirm the update is a **minor/patch update**; do not
use the major-upgrade action.

```sh
set -eu
printf 'current='; /usr/local/sbin/opnsense-version
/usr/local/sbin/opnsense-update -v
[ "$(python3 -c 'import json;print(json.load(open("/var/db/devicemonitor/config.json"))["enabled"])')" = 0 ]
[ ! -e /var/db/devicemonitor/devices.db-wal ]
/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/daemon_status.sh
service configd status
service devicemonitor status
df -h /
configctl firmware running
configctl firmware status
configctl firmware check
```

`configctl firmware running` must return `ready` before starting. `configctl firmware check` is
asynchronous; poll `configctl firmware running` until it returns `ready` again, then run
`configctl firmware status` and inspect `/tmp/pkg_upgrade.json` without printing unrelated data.
Require the offered OPNsense package/revision to be the intended 26.7.8 build, the download size to
fit in the available root filesystem space, and the reboot flag to be recorded for operator
planning.

After that separate authorisation, the supported minor-update action is:

```sh
configctl firmware update
```

Do not substitute `configctl firmware upgrade` (the major-upgrade path) or a direct `pkg upgrade`.
From a separate console, poll `configctl firmware running` (`busy` during the operation, `ready`
afterward); `firmware status` is the update-offer view, not operation progress. If OPNsense
initiates a reboot, wait for the console/host to return. Afterwards inspect the persistent update
log with `/usr/local/sbin/opnsense-update -g`. The command was executed once as recorded above;
do not repeat it as part of this record.

Abort before update if the configuration backup cannot be read back, the off-host copy is absent,
the offered release is not the intended 26.7.8 build, free space is insufficient for the reported
download size, or another firmware operation is active.

## Recovery method (not invoked)

### If 26.7.8 boots

Restore the verified configuration through **System → Configuration → Backups**, or from the
console/shell using the installed restore utility:

```sh
CONFIG_SHA=4b30c2b2e3b1be8ddf66ffb869e752ba3f1c6be9df8b8ef54358d4d0608efb45
[ "$(sha256 -q /root/dm-os-26.7.8-preupdate/config.xml)" = "$CONFIG_SHA" ]
RESTORE=/conf/backup/config-$(date -u +%s).xml
test ! -e "$RESTORE"
install -o wwwonly -g wheel -m 0640 /root/dm-os-26.7.8-preupdate/config.xml "$RESTORE"
[ "$(sha256 -q "$RESTORE")" = "$CONFIG_SHA" ]
[ "$(stat -f '%Lp %Su:%Sg' "$RESTORE")" = '640 wwwonly:wheel' ]
sh /usr/local/opnsense/scripts/shell/restore.sh
```

That utility lists only `/conf/backup/config-*.xml`. The block above verifies the root-only copy,
installs it as a known backup with `wwwonly:wheel` ownership and mode `0640`, and then starts the
utility; select that entry and allow the offered reboot. Do not restore a backup with a different
digest without explaining why it is the correct one.

### If the web UI or normal boot is unavailable

Use the physical/virtual console's configuration-restore menu and select the verified automatic
backup. If the shell is reachable but the UI is not, the restore utility above is the supported
local fallback. If the OS itself is not bootable, use OPNsense installer/recovery media and restore
the configuration after reinstall.

**There is no OS-version rollback assumption.** The root filesystem is UFS and has no ZFS boot
environments, so this record does not claim a snapshot rollback to 26.7.7. Recovery is a verified
configuration restore, followed by reinstall/repair from installer media if required. Console access
and recovery media were confirmed before execution.

A configuration restore does not reinstall the Device Monitor payload. After an OS reinstall or
other loss of `/usr/local`, verify the plugin target set and use only a separately authorised
2.13.3 repair/install from the preserved bundle. Restore Device Monitor configuration or database
state from `/root/dm-os-26.7.8-preupdate` only with the daemon stopped and under separate
authorisation; do not merge old runtime state into a live daemon blindly.

## Post-update Device Monitor checks

These checks were executed through `/root/dm-os-26.7.8-postboot-check.sh` on 5 November 2026;
`POSTBOOT_RESULT=PASS` with all 61 targets checked. The commands remain below as the reproducible
verification procedure.

Run after the host has completed any reboot and the web console is available. Monitoring must stay
disabled throughout.

```sh
set -eu
/usr/local/sbin/opnsense-version
uname -a
/usr/local/sbin/opnsense-update -g

python3 -c 'import json;print("dm_version="+json.load(open("/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json"))["version"])'
python3 -c 'import json;print("monitoring_enabled="+str(json.load(open("/var/db/devicemonitor/config.json")).get("enabled")))'
[ "$(python3 -c 'import json;print(json.load(open("/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json"))["version"])')" = 2.13.3 ]
[ "$(python3 -c 'import json;print(json.load(open("/var/db/devicemonitor/config.json"))["enabled"])')" = 0 ]
[ ! -e /var/db/devicemonitor/devices.db-wal ]

service configd status
service devicemonitor status
configctl -w 5 devicemonitor status
sha256 -q /var/db/devicemonitor/installed-manifest.txt
sha256 -q /var/db/devicemonitor/devices.db
sha256 -q /var/db/devicemonitor/config.json
```

Require Device Monitor `2.13.3`, monitoring value `0`, configd and the daemon running, and the
`configctl` plugin action responding. Compare the database/configuration digests with the baseline
above; if either changed, stop and inspect before touching the plugin.

Then verify the installed target set against the preserved 2.13.3 manifest and record:

```sh
set -eu
EXTRACT=/root/dm-os-26.7.8-postupdate-extract
BUNDLE=/root/dm-os-26.7.8-preupdate/dm-v2.13.3-runtime.tar.gz
REC=/var/db/devicemonitor/installed-manifest.txt
[ "$(sha256 -q "$BUNDLE")" = 7f389248707cf8fa0684760820db85c0fddac4b8b3964e0563318b38b2730fe2 ]
test ! -e "$EXTRACT"
mkdir -m 755 "$EXTRACT"
tar -xzf "$BUNDLE" -C "$EXTRACT"
[ "$(grep -vc '^#' "$REC")" -eq 61 ]
[ "$(grep -Ec '^[0-9a-f]{64} ' "$REC")" -eq 61 ]
[ "$(grep -Ec '\.mo$' "$REC")" -eq 21 ]
[ "$(sha256 -q "$REC")" = 0afb4e4e68edd331f22c88ef559dd1163af0baaaba0cd77a76b3ed672c17dea7 ]
[ "$(sha256 -q /var/db/devicemonitor/config.json)" = 8115a7eee5104e4ddad4a508caf06cbbe1822ee9722578db527104b366cb1c22 ]
[ "$(sha256 -q /var/db/devicemonitor/devices.db)" = c17874a717cebe2c2e1dbaf537fd13a65b4ded47e10dfcce1849f2088136144e ]

while read -r hash mode source target; do
    [ "$(sha256 -q "$target")" = "$hash" ] || { echo "MANIFEST_MISMATCH=$target"; exit 1; }
    [ "$(stat -f %Lp "$target")" = "$mode" ] || { echo "MODE_MISMATCH=$target"; exit 1; }
    [ "$(stat -f %Su "$target"):$(stat -f %Sg "$target")" = root:wheel ] || { echo "OWNER_MISMATCH=$target"; exit 1; }
done < "$EXTRACT/release/v2.13.3-runtime.manifest"

while read -r hash target; do
    case "$hash" in \#*) continue;; esac
    [ "$(sha256 -q "$target")" = "$hash" ] || { echo "RECORD_MISMATCH=$target"; exit 1; }
done < "$REC"

python3 - <<'PY'
import sqlite3
c = sqlite3.connect('file:/var/db/devicemonitor/devices.db?mode=ro', uri=True)
assert c.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
assert c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
c.close()
PY

tail -n 30 /var/log/devicemonitor.log
```

An OPNsense core package update may replace the ten merged core-domain catalogues that the 2.13.3
installer owns. If the target checks fail only in those catalogue paths, stop rather than deleting
or hand-merging files. A separately authorised 2.13.3 repair install is the supported restoration;
never use `FRESH=1` on this existing installation.

## Boundaries

- `.23` only. Never update, reboot, query or restore `.252`/`.253` under this plan.
- No Device Monitor monitoring activation.
- No `FRESH=1` install.
- No branch integration, commit, push, release promotion or tag change.
- DM-BL-009 remains OPEN.
