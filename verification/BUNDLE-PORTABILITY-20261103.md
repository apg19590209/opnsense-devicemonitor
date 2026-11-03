# Bundle Portability and Fail-Safe Build — 2026-11-03

Repair record for the first GitHub Actions failure (run `#41609297193` at `cedd411`) and the
identity reissue it forced. Reference: Decision 67. Supersedes nothing in the review history;
it corrects it (see `verification/REVIEW-R2-REMEDIATION-20261103.md` Phase 2 note).

Canonical workspace: `/root/src/opnsense-devicemonitor-upstream`
(`origin` = `git@github.com:apg19590209/opnsense-devicemonitor.git`)

## 1. The failure, as observed

| Item | Value |
|---|---|
| Run | `#41609297193` — `https://github.com/apg19590209/opnsense-devicemonitor/actions/runs/41609297193` |
| Commit | `cedd41135a79a8a5949d983da3031d9d5c4cbb93`, event `push`, attempt 1 |
| Conclusion | `failure` — 62 steps: 1–32 success, **33 failed**, 34–62 skipped |
| Failing step | #33 *Verify the bundle is deterministic across checkouts* |

Exact output (step 33):

```
AssertionError: release/bundle-digest.txt says 451a03f4bc04542ea36c36ce7df42faaf5c3e044e574ea991e74d4f5a4570ae8
                but the tree builds 59869db34853933b239f1e2219cf7d431da006aa919635478511fabbfc8849d2
##[error]Process completed with exit code 1.
```

Root cause, from step 32's own transcript:

```
staged files      : 58
tar: unrecognized option '--uid'
archive bytes     : 20
bundle sha256: 59869db34853933b239f1e2219cf7d431da006aa919635478511fabbfc8849d2
```

`release/build-bundle.sh` called `tar --format ustar -cf - --uid 0 --gid 0 --uname root --gname
wheel -T LIST | gzip -n > OUT`. `--uid`/`--gid` are bsdtar options; GNU tar on `ubuntu-latest`
rejects them. Because `tar` was the non-final element of the pipeline, `$?` was gzip's status, so
`set -eu` never fired: an **empty gzip (20 bytes)** was published as the bundle and step 32 passed
(it only checked staged file counts). Step 33 caught it by digest.

## 2. Two defects behind the reported one

1. **Header encoding is producer-specific.** Dumping a bsdtar-built header: `mode 000644 \x00`,
   `uid 000000 \x00`, `devmajor 000000 \x00`, `magic/version ustar\x0000`. GNU tar writes
   `000644\0` and `ustar  \0`. Same metadata, different bytes — so "readable by both" is not the
   same as "identical from both".
2. **The identity was timezone-dependent.** `find … -exec touch -h -t 202601010000.00` reads the
   local timezone. Measured on this host with the pre-repair script:

   | TZ | bytes | sha256 |
   |---|---|---|
   | host (AEDT) | 348 932 | `451a03f4bc04542ea36c36ce7df42faaf5c3e044e574ea991e74d4f5a4570ae8` |
   | `UTC0` | 348 939 | `e6596665293a4d15af207bec071f1b8dda616947ec8891b3b95df897f54728e0` |

   The mtime in the archive was `15125217120` (octal) = 2026-01-01 00:00 **AEDT**; the runner
   would have written 2026-01-01 00:00 UTC. So even with the tar fix, CI would have failed.

## 3. Repair

`release/build-bundle.sh`
- **Implementation probe, not OS probe:** `tar --version` first line → `bsdtar` / `GNU tar` /
  unknown; printed as `tar implementation: bsdtar (…)` for the job log. Unknown → `UNSUPPORTED_TAR`
  and exit 1.
- **Per-implementation flags:** bsdtar `--format ustar --uid 0 --gid 0 --uname root --gname wheel`;
  GNU tar `--format=ustar --owner=0 --group=0 --uname=root --gname=wheel`.
- **Functional probe:** a one-file archive built with those flags must be parsed by
  `normalize-bundle-tar.py --check` (canonical ustar, regular members only) — otherwise
  `TAR_PROBE_UNSUPPORTED`. A tool that claims ustar but emits pax/GNU headers is refused.
- **`TZ=UTC0` exported** before the mtime normalisation.
- **Fail-closed stages:** `tar` to an explicit file, canonicalise, then `gzip -n`; each status is
  checked (`TAR_FAILED`, `TAR_EMPTY`, `TAR_CANONICALISE_FAILED`, `MEMBER_COUNT_MISMATCH`,
  `GZIP_FAILED`, `BUNDLE_EMPTY`), each exit non-zero, no partial archive left. No pipeline, no
  `pipefail` — still POSIX `sh`.
- **Member guard:** the canonicaliser's member count must equal the allow-list line count.

`release/normalize-bundle-tar.py` (new, 158 lines)
- Rewrites the producer-dependent header fields to one canonical encoding (6 octal digits + space
  + NUL for mode/uid/gid/devmajor/devminor; 11 digits + space for size/mtime; 6 digits + NUL +
  space for the checksum; `ustar`+`00`; uid/gid 0; `root`/`wheel`; mtime `1767225600`; empty
  prefix), recomputes the checksum, preserves name, order, size, content and mode.
- Refuses pax/GNU headers, non-regular members and ustar name prefixes rather than guessing.

Because the canonicaliser is the last writer, bsdtar and GNU tar converge on the same bytes.

## 4. Identity reissue

| | bytes | sha256 |
|---|---|---|
| Before (retired) | 348 932 | `451a03f4bc04542ea36c36ce7df42faaf5c3e044e574ea991e74d4f5a4570ae8` |
| UTC variant (never published) | 348 939 | `e6596665293a4d15af207bec071f1b8dda616947ec8891b3b95df897f54728e0` |
| **Now canonical** | **348 920** | **`ce92a09a2d0ffd79bea33ca3087137264c5ef1ff992bb983b3d7e4dbf738befd`** |

Both predecessors are recorded as superseded in `release/bundle-digest.txt`. 2.13.3 is untagged,
unreleased and undeployed, so nothing published is invalidated. The test was **not** adjusted to
accept the old value.

Records updated consistently: `release/bundle-digest.txt`, `PROJECT_STATE.md` (bundle row and gate
counts 43 suites / 60 steps), `verification/DEPLOY-2.13.3-23-PLAN.md`, the Phase 2 note in
`verification/REVIEW-R2-REMEDIATION-20261103.md`, `PRODUCT_BACKLOG.md` DM-BL-009, Decision 66's
payload-scope paragraph and the new Decision 67.

## 5. Acceptance results (local, this host, committed tree `93d7dcc` + this record)

| Check | Command | Result |
|---|---|---|
| Bundle determinism (4 cases) | `python3 tests/test_bundle_determinism.py` | `BUNDLE_DETERMINISM=PASS cases=4` — two checkouts identical; canonical metadata 58 members, uid/gid 0, root/wheel, mtime `15125334400`; GNU-style input collapsed to 1 656 320 identical bytes; recorded digest matched |
| Build fail-safe (5 cases) | `python3 tests/test_bundle_build_safety.py` | `BUNDLE_BUILD_SAFETY=PASS cases=5` — failing tar, empty tar, failing gzip, unknown tar and pax producer all rejected with no archive left |
| CI wiring | `python3 tests/test_ci_config.py` | `CI_CONFIG=PASS cases=5`; 43 suites referenced, 43 present, 60 steps |
| Pinned inputs | `sh release/verify-release-inputs.sh` | `VERIFY_OK=4` |
| Manifest vs tree | re-hash of `release/v2.13.3-runtime.manifest` | 40 ok, 0 mismatched |
| Timezone independence | build under host TZ and `TZ=Asia/Tokyo` | both `ce92a09a…` / 348 920 |
| `v2.13.2` untouched | `git rev-parse v2.13.2` | `011100a0…` → `74e1f6f` (unchanged) |
| Shell/Python syntax | `sh -n release/build-bundle.sh`, `py_compile` | clean |

Not verified here: a real GNU-tar build. The GNU path is exercised by the header re-encoding case
and by the runner on the next push; the *flags* were chosen from GNU tar's documented
`--owner/--group/--uname/--gname` spelling and are validated by the functional probe (an
implementation that rejects them exits `TAR_PROBE_FAILED` rather than mis-building).

## 6. Backups and rollback

Backup set `/root/dm-bundle-fix-backup-20261103/`: `branch-cedd411.bundle` (complete history,
verified), `HEAD.txt`, copies of the pre-change `release/build-bundle.sh`, `.github/workflows/ci.yml`,
`tests/test_bundle_determinism.py`, `tests/test_ci_config.py`, and `SHA256SUMS` over all of them.

Rollback:

1. This commit only: `git reset --soft HEAD~1`.
2. Restore the pre-repair files: verify against `SHA256SUMS`, then copy back the four saved files.
3. Whole branch: `git clone /root/dm-bundle-fix-backup-20261103/branch-cedd411.bundle`.
4. Repository-wide: `/root/dm-consolidation-backup-20261103/upstream/upstream-all.bundle`.

## 7. Outstanding

1. **Remote CI is still red** — the fix is committed but not pushed (this task forbids publication);
   H1b stays open until a run is green.
2. **GNU tar path unproven on real GNU tar** until that push; the runner will exercise it.
3. **DM-BL-009** (`main` divergence 14/41) untouched and still **OPEN**.
4. No deployment, tag or release was performed; the 2.13.3 bundle remains unpublished.
