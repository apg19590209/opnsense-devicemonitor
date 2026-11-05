# Installer sandbox — executable end-to-end coverage of the 2.13.3 installer (M5)

`run-installer-sandbox.sh` executes the **unmodified** `install-unattended.sh` — taken from the
release bundle whose digest is published in `release/bundle-digest.txt` — inside a disposable
FreeBSD jail. It exists because review item M5 was that no test ever ran the installer itself:
every executable check stopped at `release/prune-plan.sh`.

```sh
# on the Device Monitor testbed, as root (FreeBSD only)
sh verification/installer-sandbox/run-installer-sandbox.sh all
DM_SANDBOX_SAVE=1 sh verification/installer-sandbox/run-installer-sandbox.sh scenario rollback
sh verification/installer-sandbox/run-installer-sandbox.sh clean
```

Scenarios: `check` (`--check` must not mutate), `install` (upgrade + legacy prune + record),
`repair` (same-version repair + record-driven prune), `rollback` (failure injected after the
prune, full restoration verified), `failclosed` (tampered helper refused before any mutation).

How isolation works, and what it does **not** cover, is recorded in
`verification/REVIEW-R2-REMEDIATION-20261103.md` §Phase 3. In short:

* read-only nullfs mounts of `/bin /sbin /lib /libexec /usr /etc` + `devfs`;
* a writable scratch overlay over every path the installer may write (`/var`, `/tmp`, `/root`,
  `/etc/rc.d`, `/etc/rc.conf.d`, the plugin trees, `/usr/local/share/locale`);
* the jail has its own hostname, and each installer invocation is preceded *inside* the jail by
  a marker + hostname + uid check — a broken jail can only produce a refusal;
* only `service configd` is stubbed (host service, not payload); it doubles as the
  failure-injection point.

Not covered, by design: the daemon stop/wait/start branch, a fresh install (`FRESH=1`), and the
real configd interaction. This harness is **not** wired into CI — GitHub runners are Linux and
cannot create a FreeBSD jail, so CI keeps running the 44 root-free suites.

`evidence/<scenario>/` holds the transcripts from the recorded run.
