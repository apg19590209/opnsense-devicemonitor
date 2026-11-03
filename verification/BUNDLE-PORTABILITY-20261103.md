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
| Build fail-safe (5 cases) | `python3 tests/test_bundle_build_safety.py` | `BUNDLE_BUILD_SAFETY=PASS cases=5` — failing tar, empty tar, failing gzip, unknown tar and pax producer all rejected with no archive left (the suite grew to **7 cases** after run #41611564118; see §8) |
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

## 8. Second CI run (#41611564118) and the GNU flag correction

The repair above was pushed as `8ff76ef` and run `#41611564118`
(`https://github.com/apg19590209/opnsense-devicemonitor/actions/runs/41611564118`) **failed at step
32 — "Verify the release bundle inputs"**. It did not fail the way the first run did:

```
tar implementation: gnu (tar - tar (GNU tar) 1.35)
tar: unrecognized option '--uname=root'
TAR_PROBE_FAILED=tar (flags rejected: --format=ustar --owner=0 --group=0 --uname=root --gname=wheel)
##[error]Process completed with exit code 1.
```

Reading:

- **The detection and the fail-safe worked.** The runner was correctly identified as GNU tar 1.35,
  the functional probe refused the flag set, the build exited non-zero, and **no archive was
  produced or fingerprinted** — there is no 20-byte artefact this time. Steps 1–31 passed
  (including predecessors `passed=8 skipped=0` and repair permissions `PASS cases=4`); steps 33–61
  were skipped.
- **The remaining defect was my GNU flag spelling.** GNU tar has no `--uname`/`--gname` options;
  those are bsdtar's. GNU expresses ownership as `--owner=NAME[:UID]` and `--group=NAME[:GID]`,
  which set the symbolic name *and* the numeric id.

Correction (`release/build-bundle.sh`, gnu arm only — the bsdtar arm, the detection and the probe
are unchanged):

```sh
TAR_OPTS="--format=ustar --owner=root:0 --group=wheel:0"
```

**The identity did not change**, which is the point of canonicalisation: the same tree still builds
`ce92a09a2d0ffd79bea33ca3087137264c5ef1ff992bb983b3d7e4dbf738befd` / 348 920 bytes.

### Verification performed locally

| Check | Result |
|---|---|
| `tests/test_bundle_build_safety.py` | `BUNDLE_BUILD_SAFETY=PASS cases=7` — the 5 original cases plus the two new GNU ones |
| GNU flag grammar (static) | `gnu flags: --format=ustar --owner=root:0 --group=wheel:0`; assertion refuses `--uname`, `--gname`, `--uid`, `--gid` in the GNU arm and pins the bsdtar arm |
| GNU option grammar (model) | a shim that answers `GNU tar 1.35` and rejects `--uname/--gname/--uid/--gid` with "unrecognized option" runs the real build start to finish: probe accepted, `TAR_CANONICALISED members=58`, identity `ce92a09a…` = recorded |
| Real GNU-format producer | `bsdtar --format=gnutar` (GNU tar *format*, real libarchive) through the same pipeline: `TAR_CANONICALISED members=58`, `archive bytes: 348920`, `bundle sha256: ce92a09a…` = recorded |
| `tests/test_bundle_determinism.py` | `BUNDLE_DETERMINISM=PASS cases=4` |
| `tests/test_ci_config.py` | `CI_CONFIG=PASS cases=5` |
| Pinned inputs | `VERIFY_OK=4`; manifest 40/40 |
| `v2.13.2` | tag `011100a0…` → `74e1f6f`, manifest unchanged vs the tag |

**Not verified here:** the actual GNU tar 1.35 binary. This host is the OPNsense appliance: it has
bsdtar 3.8.7 only, the OPNsense repository carries no `gtar`, there is no Linux compat layer and no
container runtime, and installing packages on the appliance is out of scope. The GNU *grammar* is
therefore modelled and the GNU *format* is produced by a real tool, but the flags will only be
exercised for real by the runner on the next authorised push.

### Outstanding after this correction

1. **H1b stays open** — remote CI has failed twice; a green run is still the only closure.
2. **Real GNU tar path unproven locally** (see above); the next authorised push is the test.
3. **M5 stays open** — the installer's own process is still not executed by any test (needs a
   sandboxed installer mode).
4. **DM-BL-009 stays open** — `origin/main` divergence 14 behind / 41 ahead, merge base `40cced8`.
5. **Coverage note:** `release/normalize-bundle-tar.py` and `build-bundle.sh` are build-time tools
   and are not in `release/release-inputs.sha256` (which pins only files the installer executes).
   If build-time tools must be pinned too, that is a separate change.

## 9. Third CI run (#41627234610) — tar termination and gzip reproducibility

The GNU flag fix was pushed as `ee3cccc`; run `#41627234610`
(`https://github.com/apg19590209/opnsense-devicemonitor/actions/runs/41627234610`) **failed at step
32** with a *different* symptom — the build worked, the identity did not:

```
tar implementation: gnu (tar - tar (GNU tar) 1.35)
TAR_FORMAT=canonical-ustar members=1
TAR_CANONICALISED members=58 bytes=1658880
archive bytes     : 349052
bundle sha256: b29e1166a75a823fda1a8a2997aac4131d14681e9acb0e7cd38ead79e5615550
BUNDLE_DIGEST_MISMATCH=recorded:ce92a09a… built:b29e1166…
```

Measured differences, member payload identical (58 members, same sizes, same modes, same ownership):

| Fact | FreeBSD (bsdtar + BSD gzip) | Runner (GNU tar 1.35 + GNU gzip) |
|---|---|---|
| data end offset | 1 655 296 | 1 655 296 |
| trailing bytes after the last member | **1 024** (two POSIX blocks) | **3 584** (two blocks + padding to a 10 240-byte record) |
| canonical tar length | 1 656 320 | 1 658 880 |
| bytes for the *same* 1 658 880-byte tar through `gzip -n` | 348 939 | 349 052 |

So two platform facts had leaked into the identity: how the local tar terminates an archive, and
which gzip implementation compresses it.

### Repair (Decision 68)

`release/normalize-bundle-tar.py` now parses every member, records the end of the final member,
requires **all** remaining bytes to be zero (rejecting nonzero trailing data), discards the
producer's padding and appends exactly two 512-byte zero blocks. Canonical length for this payload
is 1 656 320 bytes, as required.

`release/bundle-gzip.py` (new) writes the .tar.gz itself — fixed header
`1f 8b 08 00 / FLG 0 / MTIME 0 / XFL 0 / OS 255`, stored deflate blocks, `binascii` CRC-32, ISIZE,
and an inflate-and-compare guard before the file is written. `build-bundle.sh` calls it instead of
the host `gzip`, keeps the fail-safe stage checks (`GZIP_FAILED` non-zero, no partial bundle) and
gains a `DM_BUNDLE_GZIP` seam so the tests can substitute a failing compressor.

Accepted cost: **1 656 468 bytes** instead of ~349 KB. Determinism and a version-free
implementation outrank payload size; `tar -xzf` reads stored blocks unchanged.

### Identity reissued (once, documented)

| | bytes | sha256 |
|---|---|---|
| retired by Decision 67 | 348 920 | `ce92a09a2d0ffd79bea33ca3087137264c5ef1ff992bb983b3d7e4dbf738befd` |
| runner variant, never published | 349 052 | `b29e1166a75a823fda1a8a2997aac4131d14681e9acb0e7cd38ead79e5615550` |
| **canonical now** | **1 656 468** | **`7f389248707cf8fa0684760820db85c0fddac4b8b3964e0563318b38b2730fe2`** |

Updated with it: `release/bundle-digest.txt` (both predecessors recorded as superseded),
`PROJECT_STATE.md` (identity and 44 suites / 61 steps), `verification/DEPLOY-2.13.3-23-PLAN.md`,
the `REVIEW-R2` second correction, the integration assessment, Decision 66's payload note and the
new Decision 68.

### Local verification

| Check | Result |
|---|---|
| `tests/test_bundle_reproducibility.py` (new, 9 cases) | `BUNDLE_REPRODUCIBILITY=PASS cases=9` — 1 024 / 3 584 / 10 240 byte tails normalise identically; idempotent; nonzero, missing and short tails rejected; compression deterministic across runs; header fixed (`mtime 0`, `OS 255`, no filename); zlib, `gzip -dc` and `tar -tzf` all agree on 58 members; size and sha match `release/bundle-digest.txt`; a failing compressor leaves no bundle; payload metadata unchanged |
| `tests/test_bundle_build_safety.py` | `BUNDLE_BUILD_SAFETY=PASS cases=7` |
| `tests/test_bundle_determinism.py` | run after the commit (it clones HEAD) |
| pinned inputs / manifest | `VERIFY_OK=4`; 40/40 rows |
| `v2.13.2` | tag `011100a0…` → `74e1f6f` and its manifest unchanged |

### Rollback

Backup set `/root/dm-reprogzip-backup-20261103/`: `branch-ee3cccc.bundle` (verified complete),
`HEAD.txt`, pre-change `release/build-bundle.sh`, `release/normalize-bundle-tar.py`,
`release/bundle-digest.txt`, `tests/test_bundle_determinism.py`,
`tests/test_bundle_build_safety.py`, `.github/workflows/ci.yml`, and `SHA256SUMS`.
`git reset --soft HEAD~1`; `git reset --hard ee3cccc` for the tree; individual files restored from
the backup after checking `SHA256SUMS`; whole branch from the bundle.

## 10. Fourth CI run (#41629115055) — production identity verified, test fixture at fault

Commit `d62d9ae` was pushed; run `#41629115055`
(`https://github.com/apg19590209/opnsense-devicemonitor/actions/runs/41629115055`) **failed at step
33**, one step *after* the identity check:

```
step 32  success  Verify the release bundle inputs
   tar implementation: gnu (tar - tar (GNU tar) 1.35)
   TAR_FORMAT=canonical-ustar members=1
   TAR_CANONICALISED members=58 bytes=1656320
   archive bytes     : 1656468
   bundle sha256: 7f389248707cf8fa0684760820db85c0fddac4b8b3964e0563318b38b2730fe2
   VERIFY_OK=4
   bundle identity: 7f389248707cf8fa0684760820db85c0fddac4b8b3964e0563318b38b2730fe2 (1656468 bytes)

step 33  failure  Validate the bundle build fails safely
AssertionError: ('TAR_FAILED',
  '... tar implementation: bsdtar (/tmp/tmpol_y35ay/tar - bsdtar 3.8.7 (fake)) ...',
  "tar: unrecognized option '--uid'\n
   TAR_PROBE_FAILED=/tmp/tmpol_y35ay/tar (flags rejected: --format ustar --uid 0 --gid 0 --uname root --gname wheel)\n")
```

**What that proves:** the canonical tar (**1 656 320** bytes), the 58 members and the deterministic
gzip (**1 656 468** bytes, `7f389248…`) are correct on GNU tar 1.35 + Linux. The portability work is
done; nothing in `release/` needed changing.

**Root cause of the failure:** the safety suite's fake tars advertised themselves as bsdtar, refused
the `-T` list, and otherwise did `exec <host tar> "$@"`. On FreeBSD the host tar *is* bsdtar, so the
forwarded `--uid/--gid/--uname/--gname` worked; on the runner the host tar is GNU tar, which rejects
`--uid`, so the fake died during the **functional probe** and the build correctly stopped with
`TAR_PROBE_FAILED` before the intended `TAR_FAILED` stage. A test-harness defect, not a production
one.

### Fixture correction (Decision 69, test-only)

`tests/test_bundle_build_safety.py` now uses one platform-neutral fixture, generated from an
embedded Python script, that **implements the interface** `release/build-bundle.sh` uses instead of
forwarding to the host:

- `--version` prints the announced flavour (`bsdtar 3.8.7 (fake)` or `tar (GNU tar) 1.35`);
- it parses `-cf OUT`, `-T LIST`, positional members and both ownership spellings (`--uid 0 …` and
  `--owner=root:0 --group=wheel:0`), rejecting a configurable option list as `unrecognized option`;
- it writes a real ustar archive itself (magic `ustar\0`+`00`, checksums, file modes read from
  disk), so no host tar is involved and the archive content is identical on both platforms;
- modes: `normal`, `fail-archive` (fails only at the `-T` archive stage), `empty-archive`,
  `fail-any` (fails at the probe).

Case-by-case outcome, all on FreeBSD:

| Case | Behaviour now proven |
|---|---|
| `test_tar_failure_is_fatal` | probe passes (`TAR_FORMAT=canonical-ustar members=1`), archive stage fails → `TAR_FAILED`, no bundle |
| `test_probe_failure_is_reported` **(new)** | probe failure reported as `TAR_PROBE_FAILED`, and *not* as a later stage |
| `test_empty_tar_is_fatal` | probe passes, empty archive → `TAR_EMPTY` |
| `test_gnu_option_grammar_accepts_the_build` | GNU-flavour fixture rejects `--uname/--gname/--uid/--gid`, accepts `--owner=root:0 --group=wheel:0`, build completes and the identity equals `7f389248…` |
| `test_unknown_tar_implementation_is_refused` | `UNSUPPORTED_TAR` (probe never reached) |
| `test_pax_archive_is_refused` | pax member refused by the canonicaliser |
| `test_gzip_failure_is_fatal` | `GZIP_FAILED`, no bundle |
| `test_gnu_flag_string_is_valid_for_gnu_tar` | static assertion on both flag sets |

### Verification

`BUNDLE_BUILD_SAFETY=PASS cases=8` · `BUNDLE_REPRODUCIBILITY=PASS cases=9` ·
`BUNDLE_DETERMINISM=PASS cases=4` (run against the committed tree) · `CI_CONFIG=PASS cases=5` ·
`VERIFY_OK=4` · manifest 40/40 · `v2.13.2` `011100a0…`→`74e1f6f` unchanged.
Identity unchanged and unreissued: 58 members, 1 656 320-byte canonical tar, 1 656 468-byte bundle,
`7f389248707cf8fa0684760820db85c0fddac4b8b3964e0563318b38b2730fe2`. **No file under `release/` was
touched** — the diff is the test suite and this record only.

**Remaining requirement:** this host has no GNU tar (OPNsense appliance, no `gtar` package, no Linux
compat layer, no container runtime), so the real GNU execution remains a **remote-CI verification
requirement**. The fixture models the interface; the runner is the only place the real binary runs.

### Rollback

Backup set `/root/dm-fixture-fix-backup-20261103/`: `branch-d62d9ae.bundle` (verified complete),
`HEAD.txt`, pre-change `tests/test_bundle_build_safety.py` and this document, plus `SHA256SUMS`.
`git reset --soft HEAD~1`; `git reset --hard d62d9ae`; single-file restore after checking
`SHA256SUMS`; whole branch from the bundle.


