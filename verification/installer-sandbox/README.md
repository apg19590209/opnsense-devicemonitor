# Installer sandbox — executable end-to-end coverage of selected release bundles

`run-installer-sandbox.sh` executes the **unmodified** `install-unattended.sh` — taken from the
explicitly selected release bundle whose commit, digest and size are verified before execution —
inside a disposable FreeBSD jail. It exists because review item M5 was that no test ever ran the
installer itself: every executable check stopped at `release/prune-plan.sh`.

The current defaults select the rollback-corrected 2.14.0 candidate that was validated from HEAD
`eac1160557352d45648c4a25310b8daeaad440f6` plus the correction before publication. Its immutable bundle is
`/root/dm-backups/dm-bl009-candidate-rollback-fix-20261106-083105/dm-v2.14.0-runtime.tar.gz`,
sha256 `5149bfd41e5842a144a9d1280c008511f20f3783932eca9beb1f48fca6173f5f` (1,725,593 bytes).
The evidence records `CANDIDATE_SOURCE=worktree`, compares every bundle member with that source and
binds the result to the immutable digest above. The deployed 2.13.3 state is copied into the jail
as the predecessor. Historical M5 evidence under `evidence/` is retained unchanged; current 2.14.0
transcripts belong in `evidence-2.14.0/`.

```sh
# on the Device Monitor testbed, as root (FreeBSD only)
sh verification/installer-sandbox/run-installer-sandbox.sh all
DM_SANDBOX_SAVE=1 sh verification/installer-sandbox/run-installer-sandbox.sh scenario rollback
sh verification/installer-sandbox/run-installer-sandbox.sh clean
```

Scenarios: `check` (`--check` must not mutate), `install` (upgrade + legacy prune + record),
`repair` (same-version repair + record-driven prune), `rollback` (failure injected after the
prune, full restoration verified), `failclosed` (tampered helper refused before any mutation).

The 6 November 2026 corrected 2.14.0 run passed all five scenarios. Rollback restored the 63-target
set, the prune fixture, the record and 19 core-locale `.state`/pristine files with zero conflicts
or failures. The earlier candidate's failure to restore ten `.state` files, its digest and its
transcripts are retained under `evidence-2.14.0-pre-rollback-fix-eac1160/` as superseded diagnostic
evidence. The complete result, root cause and correction are recorded in
`verification/INSTALLER-JAIL-2.14.0-20261106.md`.

How isolation works, and what it does **not** cover, is recorded in
`verification/REVIEW-R2-REMEDIATION-20261103.md` §Phase 3. In short:

* read-only nullfs mounts of `/bin /sbin /lib /libexec /usr /etc` + `devfs`;
* a writable scratch overlay over every path the installer may write (`/var`, `/tmp`, `/root`,
  `/etc/rc.d`, `/etc/rc.conf.d`, the plugin trees, `/usr/local/share/locale`);
* the jail has its own hostname, and each installer invocation is preceded *inside* the jail by
  a marker + hostname + uid check — a broken jail can only produce a refusal;
* `/bin` is a directory overlay over a read-only host mount; only `pgrep` delegates to the real
  binary with `-j <sandbox>` so the live daemon cannot enter the installer's stop/start branch;
* only `service configd` is stubbed (host service, not payload); it doubles as the failure-
  injection point.

Not covered, by design: the real daemon stop/wait/start branch, a fresh install (`FRESH=1`), the
real configd interaction, live rollback, and authenticated browser validation. This harness is
**not** wired into CI — GitHub runners are Linux and cannot create a FreeBSD jail, so CI keeps
running the root-free suites separately.

Each scenario ends with an assertion that its jail, mounts and host stage directories are gone and
that the live host fingerprint is unchanged. The wrapper records the scenario exit status in a
sidecar so pipeline and teardown results cannot turn a failed scenario into PASS; a successful
scenario becomes FAIL if teardown, cleanliness or live-state verification fails. An unexpected
scenario failure retains its own exit status when cleanup also fails. An expected installer refusal
is accepted only by the scenario assertion that checks it.

`evidence/<scenario>/` holds the historical 2.13.3 M5 transcripts.
`evidence-2.14.0/<scenario>/` holds the corrected candidate's current transcripts;
`evidence-2.14.0-pre-rollback-fix-eac1160/<scenario>/` preserves the superseded failure.
