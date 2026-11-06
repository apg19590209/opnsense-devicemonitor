# GitHub issue #5 — v2.12 release manifest investigation

**Result: root cause confirmed. The manifest-only v2.12.1 candidate failed rollback validation and
is retained as superseded. The corrected isolated candidate now includes the authorised core-locale
rollback and bundle-reproducibility repairs. Focused regressions, two byte-identical builds and all
six disposable-jail scenarios pass, including independent rollback restoration, live-state
preservation and clean teardown. Issue #5 remains OPEN. No release asset, tag, repository, host,
deployment or GitHub state was changed.**

## Scope

This was the separately authorised packaging investigation for GitHub issue #5, “not able to
update to 2.12”. The reporter’s error is `ABORT: release manifest mismatch` on OPNsense
`26.7.8_2-amd64`. §9.4 remained paused, and all pre-existing worktree changes were preserved.

The published asset was read from GitHub and audited only in `/tmp`. No firewall was contacted and
no live installer was run.

## Release identity

| Item | Value |
|---|---|
| Release / tag | `v2.12` / annotated tag object, target commit `92072a53ff036fbb2b56eb663ef6d7a89fd0f36e` |
| Published asset | `dm-v2.12-runtime.tar.gz` |
| Size | `320511` bytes |
| GitHub and local SHA-256 | `6b0ed37e2f215b6e874b59d546a6c7e08424fbbe5e5065554201d009e3358071` |
| Members | 55 regular files, no `.pyc` or `__pycache__` |
| Tag comparison | all 55 extracted files are byte-identical to `v2.12` blobs |

The release asset is internally coherent with the tag. It is the installer’s embedded guards that
do not agree with the tag’s manifest.

## Manifest and payload audit

| Check | Result |
|---|---|
| Manifest | `release/v2.12-runtime.manifest`, 41 rows |
| Manifest SHA-256 | `00698f943b3c3fd79fa9a8dcfa061020df0306ef9952b29b444d725f938a5d3a` |
| Manifest shape | 41 rows, four fields each; 41 unique sources and 41 unique targets |
| Payload hashes | **41/41 match**, with modes `644` or `755` and valid source-to-target mappings |
| Catalogue rows | two `.po` rows; the installer compiles all 11 packaged sidecar catalogues separately |

`ASSET_AUDIT=PASS files=55 manifest_rows=41 unique_sources=41 unique_targets=41 po_rows=2 pyc=0 tag_mismatches=0`

## Root cause

`install-unattended.sh` in the published asset was not moved with the v2.12 manifest:

| Guard | Published value | Correct v2.12 value |
|---|---:|---:|
| `MANIFEST_SHA` | `8ae03861694a36641c91a7cfbbc81cd358137d8cf96606625b1b7eb15f940097` | `00698f943b3c3fd79fa9a8dcfa061020df0306ef9952b29b444d725f938a5d3a` |
| `wc -l` manifest assertion | `39` | `41` |
| upgrade target total | `60` | `62` |
| fresh-install target total | `61` | `63` |

The stale digest matches an older 39-row v2.11 manifest blob (`a1f44f2d73ca8d9fcbe9d0415a57078df5698de3`).
It is not the v2.11-patch1 release digest and not any committed v2.12 manifest: it is a leftover pin.

The first guard therefore always aborts before any mutation. If it were corrected alone, the next
guard would abort on the row count; if that were corrected alone, the target-total guard would abort
after staging. The three guards and the payload are one identity and must move together.

The v2.12 release notes correctly describe a 41-row payload, so the mismatch is between the notes and
the executable guard, not an ambiguity in the intended release shape.

## Why CI did not catch it

At tag `v2.12`, `tests/test_release_manifest.py` still validated the v2.11 manifest (`39` rows and
version `2.11`). The release commit had not advanced that test with the payload. It was repaired
after the tag on `main` by `d5d73ed`, which explains why the published tag can fail while later main
tests pass. The repaired test also only validates the manifest itself, not the installer’s row and
target-count guards.

## Regression test added in this workspace

`tests/test_release_inputs.py` now derives the expected values from the manifest and the installer’s
locale loop and asserts all three coupled guards:

* manifest `wc -l` guard equals the actual row count;
* upgrade target total equals manifest rows + 11 sidecar `.mo` files + 10 non-`en_US` core catalogues;
* fresh target total is the upgrade total plus the `rc.conf` target.

Validation on the current 2.14.0 tree: `RELEASE_INPUTS=PASS cases=7`.

Negative validation against the published v2.12 inputs reports the exact failures:

```text
V2_12_COUNT_GUARD_CAUGHT=('39', 41)
V2_12_TARGET_GUARD_CAUGHT=('60', 62, ['en_US', 'cs_CZ', 'de_DE', 'fr_FR', 'es_ES', 'it_IT', 'pt_BR', 'nl_NL', 'ru_RU', 'ja_JP', 'zh_CN'])
```

## v2.12.1 repair candidate (6 November 2026)

The corrected candidate was prepared in the retained isolated snapshot, without switching,
resetting or writing to the dirty integration checkout:

| Item | Value |
|---|---|
| Base | `main` commit `d5d73ed` (v2.12 line; 2.14.0 integration changes excluded) |
| Isolated workspace | `/root/dm-issue5-v2121-repair-20261106T045721Z` |
| Candidate snapshot | `/root/dm-issue5-v2121-repair-20261106T045721Z/candidate` |
| Pristine base | `git archive d5d73ed`, extracted at `.../baseline` |
| Candidate bundle | `/root/dm-issue5-v2121-repair-20261106T045721Z/dm-v2.12.1-runtime.tar.gz` |
| Size | `1584271` bytes |
| SHA-256 | `adaa2b2def784eb5d4b3f33c2b3a66b0ba4913fc16fdb6fd51d552b4fb4091bc` |
| Members | 56 regular files; no `.pyc` or `__pycache__` |
| Member-inventory SHA-256 | `48967935bb847fe2384a6caf18c7901a7eee2d6afeca4b73458b315cf36c12cf` |
| Decompressed tar SHA-256 | `8e2bbbbbc4cdbb1e56edafcd57257510e1d44fcb83a52049782dd34d7e901226` |
| Manifest | `release/v2.12.1-runtime.manifest`, 41 rows |
| Manifest SHA-256 | `77947c4b8cf915344cf167085f1ff8a609d488f617f37c2cc2a37d5cc9afc9d6` |
| Payload audit | **41/41 hashes and modes match; target counts 62/63** |
| Historical v2.12 manifest | unchanged, SHA-256 `00698f943b3c3fd79fa9a8dcfa061020df0306ef9952b29b444d725f938a5d3a` |
| Superseded candidate | `/root/dm-issue5-v2121-validation-20261106T035748Z/dm-v2.12.1-runtime.tar.gz` |
| Superseded identity | 320571 bytes, SHA-256 `da14af8d63eea847e253650087357822f7cc886b20b8fa6e85786aa442e43efb`, 55 members |

The superseded failed candidate and its jail evidence are retained unchanged. The corrected
candidate differs from `d5d73ed` in 16 files. Each change is required by the release identity, one
of the two authorised repairs, or regression coverage for those changes:

* `.github/workflows/ci.yml`: runs the new core-locale and reproducibility regressions and checks
  the new shell entry points before release inputs are accepted.
* `README.md`: points operators at the v2.12.1 asset and installation directory.
* `README_CZ.md`: keeps the Czech installation instructions on the same release identity.
* `install-unattended.sh`: moves every guard to the 41-row v2.12.1 identity, snapshots core-locale
  state before mutation, restores it in rollback, verifies restored target hashes, and reports
  `ROLLBACK_STATUS=COMPLETE/INCOMPLETE` instead of silently leaving partial state.
* `release/build-bundle.sh`: stages the rollback helper, sorts and canonicalises archived modes,
  fixes ownership and timestamps, canonicalises the ustar headers and archive tail, uses the
  deterministic compressor, and fails closed at each stage.
* `release/bundle-gzip.py` (new): writes a fixed gzip header and version-independent stored-block
  deflate stream, then inflates and compares the stream before publishing the output.
* `release/core-locale-state.sh` (new): snapshots and restores the core-locale directory, its
  original files, bytes, mode and ownership, removes files created by a failed fresh install, and
  restores directory absence; a damaged backup is refused before mutation.
* `release/normalize-bundle-tar.py` (new): rewrites supported ustar headers into one canonical
  encoding and emits exactly two zero end blocks, refusing unsupported formats and metadata.
* `release/v2.12.1-notes.md` (new): records the patch-release identity and repair scope.
* `release/v2.12.1-runtime.manifest` (new): 41-row release payload. Only the three
  metadata-bearing payload digests differ from v2.12; all 41 source hashes and modes were re-audited.
* `src/etc/inc/devicemonitor_locale.inc`: names the v2.12.1 manifest in the payload comment.
* `src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json`: sets the runtime version to
  `2.12.1` so installer and repair installation share one identity.
* `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt`: exposes the same version on
  About / Features.
* `tests/test_bundle_reproducibility.py` (new): checks two complete builds, gzip header identity,
  compressor determinism, canonical headers/tails, member inventory and fail-closed cleanup.
* `tests/test_core_locale_rollback.py` (new): covers pre-existing state and metadata, files created
  by a failed fresh install, originally absent directories and refusal of a damaged backup.
* `tests/test_release_manifest.py`: checks the release identity, all payload hashes and modes,
  unique source/target mappings, manifest pin, 41-row guard, 62/63 target totals and historical
  v2.12 manifest preservation.

The core-locale helper adapts only the necessary snapshot/restore behaviour from the validated
2.14.0 correction. The tar/gzip determinism is generic build plumbing. No prune, monitoring,
provider or other 2.14 feature was imported. Regenerating the manifest did not change any of its
41 payload source hashes; the archive membership grew from 55 to 56 only because the rollback
helper is now shipped.

### Regression and artifact results

```text
V2121_RELEASE_MANIFEST=PASS rows=41 payload_hashes=41 upgrade_targets=62 fresh_targets=63
CORE_LOCALE_ROLLBACK=PASS cases=3
BUNDLE_REPRODUCIBILITY=PASS cases=7
BUNDLE_AUDIT=PASS members=56 manifest_rows=41 payload_hashes=41/41 payload_modes=41/41 target_counts=62/63 member_modes=canonical pyc=0
FRESH_INSTALL_DEFAULTS_REGRESSION=PASS
LOCALE_MERGE=PASS
SHELL_SYNTAX=PASS files=6
```

Two independent source copies produced byte-identical bundles: build A and build B are both
`1584271` bytes with SHA-256 `adaa2b2def784eb5d4b3f33c2b3a66b0ba4913fc16fdb6fd51d552b4fb4091bc`.
The fixed gzip header and canonical tar therefore close the prior timestamp-header divergence. The
audited member inventory, source hashes and archive metadata are in
`.../evidence/member-inventory.txt`, `member-sha256.txt`, `member-metadata.txt`,
`bundle-audit.txt`, `build-comparison.txt` and `focused-validation.log`.

### Disposable FreeBSD jail validation

Harness: `/root/dm-issue5-v2121-repair-20261106T045721Z/jail-harness.py`, SHA-256
`f37823774759cde3a445900da762a1224eebe3104951046d0f0e50edba663e86`. It calls
`enforce_peak_price_gate("v2.12.1 disposable jail harness")` before creating any work tree.

The first launch aborted before jail creation because the harness's embedded `CANDIDATE_SHA` was a
63-character typo missing one `3`. The independently verified candidate digest is 64 characters and
matches `adaa2b2def784eb5d4b3f33c2b3a66b0ba4913fc16fdb6fd51d552b4fb4091bc`. The pre-correction
harness was backed up at `.../backups/harness-pin-20261106T053755Z/jail-harness.py` (SHA-256
`1111482c9bcbbf6d4c065539a7d7fa63e59789432eaebb6d394c7a999921130f`). Only that harness pin was
corrected; it parsed cleanly and was rechecked against the bundle. This was a validation-harness
defect, not a candidate defect.

The operator explicitly authorised full-price execution for these already-scoped scenarios. The
gate still reported `peak=true premium window active`; the harness was relaunched and its supported
interactive confirmation was answered with `y`. No bypass variable, `--force` option, gate
modification or clock change was used. The command was:

```text
python3 jail-harness.py check upgrade fresh repair rollback fresh-rollback
```

| Scenario | Result |
|---|---|
| `check` | **PASS:** 62 targets, core state, database and configuration unchanged; no backup or service call; no stage leftover |
| `upgrade` | **PASS:** 62 targets and 41/41 payload hashes/modes; database and configuration preserved; `configd restart` then `devicemonitor restart` |
| `fresh` | **PASS:** 63 targets, no seeded database/configuration; plugin registration, `configd restart`, `devicemonitor start`, `rc.conf` and rc link created |
| `repair` | **PASS:** second 2.12.1 install, targets/data/configuration preserved, two service cycles and two retained backups |
| `rollback` | **PASS:** injected `configd` failure after mutation; `ROLLBACK_STATUS=COMPLETE`, all targets restored, `CORE_LOCALE_STATE_BACKED_UP=present files=19`, `restored=19 removed=0 conflicts=0 failed=0` |
| `fresh-rollback` | **PASS:** injected fresh-install failure; `ROLLBACK_STATUS=COMPLETE`, all targets restored, `CORE_LOCALE_STATE_BACKED_UP=absent files=0`, `restored=0 removed=19 conflicts=0 failed=0`, rc link/conf removed |

The harness writes independent before/after snapshots. For upgrade rollback, the target snapshots
are byte-identical (SHA-256 `449b8c1fa0cdf6020cb204c052f09dd1b41660263e47b8138697904037464330`) and
the core-locale snapshots are byte-identical (SHA-256
`842dd750b07cd9c7bf51f91cf2c1927be2b85fc7f453e4595b3cd434a831ab13`); all 19 files retain their
original digest, mode, ownership and mtime. For fresh rollback, both target snapshots are identical
(SHA-256 `b9e32655b14825f34c349776107206a77e231255a3a7bbe621d2b412cd26bfcb`) and both core-state
snapshots are exactly `{"directory": "absent"}` (SHA-256
`7b15bc2f349ae5c6e6ce4972ae939289e3b468493623bf3208c41f2bb64781a8`). The displayed
`before_files=1 after_files=1` is a harness label artifact that counts the snapshot dictionary key,
not files; the raw snapshots prove the directory was absent before and after.

All six live before/after fingerprints are byte-identical with SHA-256
`519741390cb119faf5ca05a22ee26f1c04ea80b6bc70fd99a8d8d002b3f16887`. The live installed record
remains `d891ce68c9035b3bcd2384d6f3705d6c8d9bc20fb5ef13cc9ca80b2ae1c035a2`, with 63 installed
targets and the host core-locale directory still mode `0755` with 19 files. Every scenario reports
`JAIL_TORN_DOWN`, `MOUNTS_TORN_DOWN`, `WORKDIR_REMOVED` and `LIVE_FINGERPRINT_UNCHANGED`; there was
no remaining `dm-v2121-sandbox` jail, mount or `/var/tmp/dm-v2121-jail-work` after the run. The
candidate SHA-256 was rechecked after validation and remained unchanged.

Service-call evidence is limited to the intended boundaries: upgrade `configd restart` and
`devicemonitor restart`; fresh plugin registration, `configd restart`, `devicemonitor start`;
repair two corresponding service cycles; upgrade rollback stop/restart and `configd restart`; fresh
rollback plugin registration, stop and `configd restart`. Evidence is in
`.../jail-evidence/`: 141 files checked by `SHA256SUMS` (SHA-256
`fae8c8cfc68ff1f9248125efd9733bdf557aed5899aa444803bc7e2258894cb3`). No result file contains a
`FAIL`, `SANDBOX_FAIL` or `ROLLBACK_STATUS=INCOMPLETE` marker.

### Jail boundary and limitations

The following are jail-only stubs, not real OPNsense behaviour: `opnsense-version`, `service`
(`configd` and `devicemonitor` call recording/failure injection), `rc.configure_plugins`, and the
daemon-state `pgrep` shim. The harness therefore proves the installer's service-call boundaries and
the fresh plugin-registration call, but does not prove real configd interaction, real OPNsense
plugin registration, real daemon lifecycle, or live `FRESH=1`. `nmap` was present from the host
toolchain, so no package installation path was exercised. No live installation, service, monitoring
or production/`.252`/`.253` access occurred.

### Backups and rollback

The base is also retained as a pristine extracted copy at
`/root/dm-issue5-v2121-repair-20261106T045721Z/baseline`. The pre-change repair files are in
`.../backups/prechange/` with `backup-manifest.txt`; the captured hashes and modes were rechecked.
The records before this update are backed up at `.../backups/records/20261106T054748Z/`:
the investigation was SHA-256 `58410f394186cc4a653fe1328ea2081a64bcec5be4d16dc119a86cae84e895e6`
and the milestone report was SHA-256
`18c57a8d97a4aecfc7c0a7d0274bb3855df23d4a0b4c575a444f59b0aaebb017`; both are mode `644`.
The earlier record backup at `.../backups/records/20261106T050714Z/` is also retained.

To discard the whole isolated repair without touching the integration checkout, remove only
`/root/dm-issue5-v2121-repair-20261106T045721Z` and its pointer file after retaining the evidence
required by the operator. To restore the candidate to the pre-repair state, restore the files in
`backups/prechange/` with `cp -p`, remove `release/core-locale-state.sh`,
`release/normalize-bundle-tar.py`, `release/bundle-gzip.py`,
`tests/test_core_locale_rollback.py` and `tests/test_bundle_reproducibility.py`, and rebuild the
bundle. To restore the base exactly, replace only the isolated `candidate` directory from
`baseline`. To roll back this record, restore the verified record backup with `cp -p` to
`verification/ISSUE-5-V2.12-MANIFEST-20261106.md`. To revert the harness-only pin correction,
restore `.../backups/harness-pin-20261106T053755Z/jail-harness.py` with `cp -p`; this would
reintroduce the deliberately superseded 63-character pin and should only be used for diagnostic
comparison.

## Publication path

Do **not** overwrite `dm-v2.12-runtime.tar.gz` and do **not** move or replace tag `v2.12`. Preserve
that tag and asset as the immutable record of the defect. Do not direct the reporter to the
unreleased 2.14.0 integration candidate.

The safe path is a new patch release, `v2.12.1`, based on `main` at `d5d73ed` (the first commit
whose v2.12 test suite is repaired; it has no runtime `src/` changes relative to tag `v2.12`).
The candidate materialises the version bump, the 41-row manifest, the digest/row/target guards,
predecessor acceptance, stage/backup identity, release notes, installation text, the authorised
rollback correction and reproducible-build inputs. Publication remains gated by the items below.

## Remaining publication gates

1. With separate authorisation, establish the exact source commit for the candidate and run CI on that
   commit, create the `v2.12.1` tag/release, upload the exact validated bundle, verify the
   GitHub-reported digest, and confirm `v2.12` and its asset remain unchanged.
2. Only after publication and validation, reply to issue #5 with the new asset and exact cause.
3. Any live deployment or host-level validation remains separately gated and is not part of this
   investigation.

No production, `.252` or `.253` contact is required. A live `.23` deployment is not part of this
investigation proposal.

## Current state

* GitHub issue #5: **OPEN**.
* DM-BL-009: **OPEN**.
* §9.4: paused, not executed.
* v2.12.1 candidate: corrected, focused-regression validated and all six jail scenarios PASS in
  isolation; **not published**.
* Superseded failed candidate: retained at
  `/root/dm-issue5-v2121-validation-20261106T035748Z/` and copied into the repair workspace.
* Validation harness: one pre-run SHA pin typo corrected and backed up; one display-label artifact
  in the fresh-rollback file count documented. Neither changes the candidate or the PASS logic.
* Canonical integration checkout: preserved with its pre-existing dirty entries; nothing staged.
* Pending worktree changes: preserved; this investigation changed only this record in the
  canonical checkout. The milestone report is written under `.cline-reports/`.
