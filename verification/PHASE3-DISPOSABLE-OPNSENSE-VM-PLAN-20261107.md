# Phase 3 — disposable OPNsense VM setup and test procedure

**Status: READY FOR APPROVAL; NOT EXECUTED. No VM, host, `.23`, `.252`, `.253` or `.254` was
provisioned, contacted or changed in this pass.**

## Purpose and candidate

Close the real-host part of **DM-BL-012**: a genuine fresh OPNsense installation, real
`rc.configure_plugins`/configd/plugin registration, daemon autostart and reboot persistence.
The exact candidate is:

| Item | Value |
|---|---|
| Archive | `dm-v2.14.0-runtime.tar.gz` |
| Size | 1,729,177 bytes |
| SHA-256 | `90afa55dd826c0dc3be8a23902b809baa465e25191dc372dc6cc2ef4e57fc243` |
| Source | `main` at `e9ec5486a8cc9e87e3b6d3cf6098f26ed15e1370` plus the reviewed closure branch |
| Prior evidence | Phase 1 repair on `.23`; fresh/fresh-rollback jail; v2.12.1 predecessor jail |

The existing `.23` installation is not a fresh-install target. It has an accepted 2.14.0
installation and must not be changed for this phase. The `.252`/`.253` CARP pair is prohibited.

## Infrastructure inventory

The local records and read-only host inventory show:

| Resource | Status |
|---|---|
| Local `vmm` | `kern.vmm` absent; `/dev/vmm` absent |
| `bhyve` binary | Present at `/usr/sbin/bhyve`, but no usable guest image or `/dev/vmm` |
| Local OPNsense image | None found under `/root`, `/var/tmp` or `/tmp` |
| External hypervisor / disposable VM | Not recorded or supplied |
| `.23` | Existing integration testbed; not empty and not a fresh-install target |
| `.252`/`.253` | Existing CARP pair; expressly prohibited |
| External delivery endpoint | Not supplied; not needed for Phase 3 |

The first required dependency is therefore an approved external hypervisor or an approved
disposable-VM service/image. No local provisioning is possible from the current records.

## Required VM and isolation

- OPNsense `26.7.8_2` or an approved compatible image, installed on a disposable VM.
- At least 2 vCPU, 4 GB RAM and 20 GB free virtual disk, plus a dedicated snapshot facility.
- Two isolated NICs: a private WAN and a private LAN/test network; no route to production,
  `.23`, `.252` or `.253`.
- Console access through the hypervisor, not the live OPNsense host.
- A host name such as `dm-phase3.internal` passed explicitly to the installer.
- No SMTP/webhook/notification recipient, monitoring activation, HA configuration or external
  service dependency.
- A fresh copy of the archive, kept outside the VM, and enough local storage for a 3–5 GB VM
  snapshot and evidence copy. The current workstation has only about 1.4 GiB free on `/`, so
  provisioning and evidence storage must not be placed there unless space is supplied.

## Backups and rollback

Before installation:

1. Create a clean VM snapshot and record its identifier.
2. Record the candidate archive size and SHA-256 on the hypervisor side.
3. Preserve the empty-state console transcript and any installation media identity.
4. Confirm the VM has no Device Monitor package, `/var/db/devicemonitor`, `/etc/rc.conf.d/devicemonitor`
   or `/etc/rc.d/devicemonitor` before the installer runs.

On failure, stop forward execution and revert the VM to the clean snapshot; do not repair the
disposable host in place. A second clean snapshot may be used for a rollback check. Do not use a
production host as the recovery target.

## Exact test procedure

Commands run inside the approved disposable VM unless marked otherwise.

1. Verify the candidate before extraction:

   ```sh
   test "$(wc -c < /root/dm-v2.14.0-runtime.tar.gz | tr -d ' ')" = 1729177
   test "$(sha256 -q /root/dm-v2.14.0-runtime.tar.gz)" = \
     90afa55dd826c0dc3be8a23902b809baa465e25191dc372dc6cc2ef4e57fc243
   (cd /root && sha256 -c SHA256SUMS)
   ```

2. Extract only into a disposable staging directory and record the empty-predecessor evidence:

   ```sh
   mkdir -p /root/dm-phase3
   tar -xzf /root/dm-v2.14.0-runtime.tar.gz -C /root/dm-phase3
   cd /root/dm-phase3
   test ! -e /var/db/devicemonitor
   test ! -e /etc/rc.conf.d/devicemonitor
   test ! -e /usr/local/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor
   opnsense-version
   service configd status
   test -x /usr/local/etc/rc.configure_plugins
   pgrep -f '^/usr/local/bin/python3 /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/monitor_daemon.py$' || true
   ```

3. Run the non-mutating installer check:

   ```sh
   ./install-unattended.sh --check --host dm-phase3.internal
   ```

   Accept only `CHECK_OK version=2.14.0 predecessor=fresh files=64 core_locales=10` with
   `daemon_running=0` and the expected host name.

4. Run the real fresh install:

   ```sh
   ./install-unattended.sh --host dm-phase3.internal
   ```

   Require `INSTALL_OK version=2.14.0 files=64 core_locales=10` and no non-zero exit. Preserve
   the complete transcript and installer backup path.

5. Verify package and plugin registration:

   ```sh
   test -x /usr/local/etc/rc.configure_plugins
   test -f /usr/local/etc/inc/plugins.inc.d/devicemonitor.inc
   test -L /etc/rc.d/devicemonitor
   test -f /etc/rc.conf.d/devicemonitor
   grep -F 'devicemonitor_enable="YES"' /etc/rc.conf.d/devicemonitor
   wc -l /var/db/devicemonitor/installed-manifest.txt
   configctl devicemonitor status
   service configd status
   pgrep -af 'monitor_daemon.py$'
   ```

   Verify the plugin's menu/ACL registration through the authenticated OPNsense UI and record
   the exact evidence. A source file or stub check alone is not a real registration pass.

6. Verify the fresh runtime state and About/Features binding through the authenticated UI:
   About/Features must show `v2.14.0`; Devices must load without error; monitoring must remain
   disabled unless a separate Phase 4 authorisation changes it. Record whether `devices.db` and
   `config.json` were created rather than assuming the jail's empty-post-install state.

7. Reboot and repeat the real plugin/service checks:

   ```sh
   reboot
   # reconnect through the hypervisor console or isolated SSH after boot
   service configd status
   configctl devicemonitor status
   pgrep -af 'monitor_daemon.py$'
   test -f /usr/local/etc/inc/plugins.inc.d/devicemonitor.inc
   test -f /etc/rc.conf.d/devicemonitor
   ```

8. Record evidence outside the VM: install and reboot transcripts, snapshot identifier, archive
   hash, manifest/record counts, plugin/ACL/menu evidence, service IDs and UI evidence. Do not
   upload or publish any artifact.

## Acceptance criteria

- Real fresh-install `CHECK_OK` and `INSTALL_OK` with 64 targets and 10 core locales.
- Real `rc.configure_plugins`, configd restart and plugin/menu/ACL registration, not a jail stub.
- Daemon starts after installation and remains healthy after reboot.
- The authenticated UI shows 2.14.0 and renders the expected pages without error.
- Monitoring and notification delivery remain disabled.
- Clean snapshot restore works and leaves no reliance on `.23`, `.252`, `.253` or production.

## Estimated effort and next approval

**3–5 hours after VM and image handoff**, excluding provisioning and hypervisor setup. Phase 4A
can reuse the same VM only after a clean snapshot and separate approval; Phase 4B needs an isolated
two-node CARP pair. The exact next action requiring authorisation is:

> Supply or authorise an external disposable OPNsense `26.7.8_2` VM, with the required snapshots
> and isolated networks, and authorise Phase 3 execution on that VM only.
