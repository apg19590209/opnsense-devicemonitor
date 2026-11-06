# Device Monitor 2.14.0 — fresh-install jail validation, 6 November 2026

**Status: PASS for the isolated `fresh` and `fresh-rollback` scenarios. Live `FRESH=1`, live
rollback, monitoring-enabled behaviour and real OPNsense plugin registration remain outside this
result. DM-BL-009 remains OPEN.**

## Objective

Exercise the unmodified 2.14.0 installer's genuine fresh-install path and its post-mutation abort
path without touching the live `.23` installation or any host service.

## Candidate and repository

| Item | Value |
|---|---|
| Repository | `/root/src/opnsense-devicemonitor-upstream` |
| Branch | `integration/dm-bl-009-reconcile-20261105` |
| HEAD | `690204bb1d6c402de9a2b41e16f753b37335279f` |
| Bundle | `/root/dm-backups/dm-bl009-candidate-rollback-fix-20261106-083105/dm-v2.14.0-runtime.tar.gz` |
| Size | 1,725,593 bytes |
| SHA-256 | `5149bfd41e5842a144a9d1280c008511f20f3783932eca9beb1f48fca6173f5f` |
| Members | 60 |
| Candidate source | commit `690204b`; every extracted bundle member compared byte-for-byte against that commit |

## Harness changes

`verification/installer-sandbox/run-installer-sandbox.sh` now provides:

* `fresh` — an empty Device Monitor predecessor, including no record, database, configuration,
  rc link, rc.conf, plugin tree or core-locale archive.
* `fresh-rollback` — the same empty predecessor with a one-shot `configd` failure injected after
  the install has mutated the target set.
* A mode-aware host guard: the historical upgrade scenarios still require the live 2.13.3
  predecessor; the fresh scenarios do not read the live record, database or configuration.
* Parent-directory overlays for the four `OPNsense/DeviceMonitor` plugin trees, so the empty
  predecessor really lacks `DeviceMonitor/` rather than merely having an empty mountpoint.
* Core catalogues reset to the first-write-wins pristine copies recorded under
  `/var/backups/devicemonitor/core-locale`. `nl_NL` is correctly left without a core catalogue
  and therefore exercises the plugin-only path.

## Service stubs and coverage limits

Two OPNsense host services are outside the payload and are represented explicitly in the jail:

* `service configd` — records each call in `/var/log/sandbox-services.log`; supports a permanent
  failure injection and a one-shot failure used by `fresh-rollback`. It does not run the host
  configd.
* `/usr/local/etc/rc.configure_plugins` — a jail-only stub that checks the sandbox marker,
  hostname and uid, records the call, and exits. It never executes the host script and never reads
  or writes `/conf`.

This proves the installer's call boundary, not OPNsense's real plugin-registration internals. A
jail cannot prove that a real host regenerates menu, ACL, plugin and configd registration state
correctly. That remains a live-install gap, and live `FRESH=1` is not authorised.

The `pgrep` process probe is a shim: a jail cannot use `pgrep -j`, and plain `pgrep -f` also sees the
live host daemon. The shim excludes the live daemon PID(s) recorded at sandbox start and relies on
the before/after fingerprint to prove the host daemon did not change.

## `fresh` result

```text
CHECK_OK version=2.14.0 predecessor=fresh files=64 core_locales=10 prunable=0 daemon_running=0 host=dm-installer-sandbox.internal legacy_prunable=0 retained=0
INSTALL_OK version=2.14.0 files=64 core_locales=10 pruned=0 backup=/var/backups/devicemonitor/install-v214.2LlxeV daemon_restarted=0 unchanged=0 repaired=0
```

Verified independently:

* all 64 targets exist with the manifest digest, mode and `root:wheel` ownership;
* the 11 sidecar catalogues recompile to the installed digests;
* the 10 merged core catalogues match a fresh recomputation from the pristine archive and the
  candidate `.po` (including the `nl_NL` plugin-only path);
* the installation record contains exactly 64 digest rows;
* `/etc/rc.conf.d/devicemonitor` is `devicemonitor_enable="YES"`, mode `0644`, `root:wheel`, and
  `/etc/rc.d/devicemonitor` is the expected symlink;
* no `devices.db`, `config.json`, WAL or SHM exists after installation;
* the daemon starts and remains running;
* exactly one `rc.configure_plugins` call and one `configd` restart are recorded;
* the certificate/menu-independent About/Features source binding reports both labels fed from the
  single `/api/devicemonitor/config/getversion` endpoint (source check only, not browser rendering);
* the jail, mounts and host stage directories are removed;
* the live record, database, Device Monitor configuration, targets, daemon PID, configd PID and
  backup inventory are unchanged.

## `fresh-rollback` result

The one-shot `configd` failure aborts the fresh install after `rc.configure_plugins` and the target
replacement have run. The installer's own cleanup path reports:

```text
ROLLBACK_SUMMARY=restored=64 skipped=0 conflicts=0 failed=0
CORE_LOCALE_ROLLBACK_SUMMARY=restored=0 removed=19 conflicts=0 failed=0
ROLLBACK_STATUS=COMPLETE
ROLLBACK_ATTEMPTED=/var/backups/devicemonitor/install-v214.ywrtzJ
```

Verified independently:

* the installer exits non-zero and does not print `INSTALL_OK`;
* `rc.configure_plugins` had already run once and two `configd` calls are recorded (the injected
  failure and the rollback restart);
* all 64 originally absent targets are removed, including the rc.conf file and rc.d link;
* the record, database, configuration, WAL/SHM, core-locale state/pristine files and plugin tree
  are absent again;
* the before/after snapshots differ only by the retained installer backup directory;
* no half-written `installed-manifest.txt.new` remains;
* the jail, mounts and host stage directories are removed;
* the live host fingerprint is unchanged.

## Evidence

Directory: `/root/dm-validation-2140/jail-evidence-fresh-20261106/`
`SHA256SUMS` SHA-256: `1448ec56adf75dab2461da9f0fda6447486a9258fadd4afa9c4deec70e43b05b`

Key files:

* `fresh/fresh.log`, `fresh/fresh-verify.log`, `fresh/core-locale.log`, `fresh/daemon.log`,
  `fresh/before.snapshot`, `fresh/after.snapshot`, `fresh/live-after.fingerprint`;
* `fresh-rollback/failing.log`, `fresh-rollback/before.snapshot`,
  `fresh-rollback/after.snapshot`, `fresh-rollback/live-after.fingerprint`;
* `fresh/sandbox-services.log` and `fresh-rollback/sandbox-services.log` — stub call records.

The two `live-after.fingerprint` files are identical. They record record
`d891ce68c9035b3bcd2384d6f3705d6c8d9bc20fb5ef13cc9ca80b2ae1c035a2`, database
`c17874a717cebe2c2e1dbaf537fd13a65b4ded47e10dfcce1849f2088136144e`, Device Monitor configuration
`027594eb735cf35e4b617163106031971567d0ba74027783e42cae46d37fd47d`, daemon PID `79168`,
configd PID `35685`, zero host stages, zero sandboxes and zero sandbox mounts.

## Authenticated About/Features evidence

The operator supplied a screenshot of the authenticated Settings → About page on `.23` showing both
Device Monitor `v2.14.0` and `v2.14.0 Features and Enhancements`. Visual rendering acceptance is
**PASS** on that operator-supplied evidence. No browser Network capture was supplied, so no
`getversion` response, console value or cache-behaviour claim is made.

## Live-configuration note observed during this work

At 09:55:54 on 6 November the live `/conf/config.xml` changed from
`8c08b0a07821c5579d0ec6fcc7a9b8ba358c5ac67d5e39a904b9466ba5b8e1a6` to
`c2ce5800c76fcf8470283d6ada559fd6c2eba5a8e0372b409cc046afd8307abf`. The OPNsense backup shows a
`root@192.168.20.192` revision via `/diag_backup.php`; the only differences are the Git Backup
plugin's `persisted_at` value and the revision metadata. This is an operator UI backup action, not a
jail or installer mutation. The harness fingerprint does not include `/conf/config.xml`; the
record, Device Monitor database/configuration and installed targets it does cover were unchanged.

## Remaining gaps

* Live `FRESH=1` on a real OPNsense host is still untested and must never be exercised on `.23`.
* Real `rc.configure_plugins` registration and its effect on menu/ACL/plugin state remain unproven.
* Live successful-install rollback on `.23` was outside this jail result and was later executed
  separately with PASS on 6 November 2026; see
  `verification/LIVE-ROLLBACK-2.14.0-23-20261106.md`.
* Monitoring-enabled behaviour was outside this jail result. A later bounded §9.4 run completed
  two scheduled inventory scans, direct DMTEST-only service discovery, scope-limited probing and
  two direct loopback helper SMTP deliveries. Reminder, ageing, identity-email, CARP, HA,
  daemon-generated notification and full lifecycle paths remain unestablished.
* Authenticated browser Network capture was not collected; only visual rendering is accepted.

## Rollback of this documentation/harness change

Backups made before editing:
`/root/dm-backups/fresh-validation-20261106-094435/` (mode `0700`, `root:wheel`), containing the
harness, README, deployment plan, `PROJECT_STATE.md` and `PRODUCT_BACKLOG.md` with `SHA256SUMS`.

```sh
cp -p /root/dm-backups/fresh-validation-20261106-094435/verification/installer-sandbox/run-installer-sandbox.sh \
  /root/src/opnsense-devicemonitor-upstream/verification/installer-sandbox/run-installer-sandbox.sh
cp -p /root/dm-backups/fresh-validation-20261106-094435/verification/installer-sandbox/README.md \
  /root/src/opnsense-devicemonitor-upstream/verification/installer-sandbox/README.md
```

DM-BL-009 remains **OPEN**.
