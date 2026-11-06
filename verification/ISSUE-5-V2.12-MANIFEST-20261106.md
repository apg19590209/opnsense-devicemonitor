# GitHub issue #5 — v2.12 release manifest investigation

**Result: root cause confirmed and the v2.12.1 repair published. The repair source is on
`fix/issue-5-v2.12.1` at commit `5c3ee29e9bc3ae7baf1f55a8cf7f25ad231399d6`, and exact-commit
CI is green. Its language-catalogue correction, core-locale rollback, reproducible bundle and all
six disposable-jail scenarios pass. The annotated `v2.12.1` tag and release publish the exact
`ba5737…` tested archive and `SHA256SUMS`; an independent download matched the tested bytes, size,
inventory, manifest and installer guards. The v2.12 release notes now carry an installer-defect
warning and v2.12.1 link, while its tag and asset remain unchanged. The earlier `adaa2b2…` and
intermediate `dbf350…` candidates remain retained as superseded. One scoped publication follow-up
was posted to issue #5, which remains OPEN. No host deployment, monitoring activation or
main/release movement was made. DM-BL-009 remains OPEN and §9.4 remains paused.**

## Scope

This was the separately authorised packaging investigation for GitHub issue #5, “not able to
update to 2.12”. The reporter’s error is `ABORT: release manifest mismatch` on OPNsense
`26.7.8_2-amd64`. §9.4 remained paused, and all pre-existing worktree changes were preserved.

The historical v2.12 asset was read from GitHub and audited only in `/tmp`. The v2.12.1 release was
later downloaded into the isolated publication evidence directory and compared with the jail-tested
archive. No firewall was contacted and no live installer was run.

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

## Final v2.12.1 candidate (6 November 2026)

The final candidate was prepared in an isolated extracted tree. The integration checkout, its
branch, index and pending work were never switched, reset or written. The commit was created
through the canonical object store with a temporary index, then only
`refs/heads/fix/issue-5-v2.12.1` was advanced and pushed without force.

| Item | Value |
|---|---|
| Base | `main` commit `d5d73ed`; 2.14.0 integration changes excluded |
| Repair branch | `fix/issue-5-v2.12.1` |
| Final commit | `5c3ee29e9bc3ae7baf1f55a8cf7f25ad231399d6` |
| Commit tree | `2f7e0a6e386431ab89d383d9bfc54bd20adacefa` |
| Commit parent | `a21373a6297edc1fcafd6a9be35e9d2c071f6129` |
| Correction scope | 56 files versus the parent (`+3473/-52`): 15 modified and 41 sanitised evidence files added |
| Cumulative repair scope | 97 files versus `d5d73ed` (`+7267/-79`) |
| Remote branch | `refs/heads/fix/issue-5-v2.12.1` at the final commit; non-force push |
| Isolated workspace | `/root/dm-issue5-v2121-langfix-20261106T061929Z` |
| Committed tree | `.../committed-tree-5c3ee29e9bc3ae7baf1f55a8cf7f25ad231399d6` |
| Final bundle | `/root/dm-issue5-v2121-langfix-20261106T061929Z/dm-v2.12.1-runtime.tar.gz` |
| Size | `1596559` bytes |
| SHA-256 | `ba5737e9e2fc0d9b78edaacef82aeee30c9a8656db4f27cc9800473af71957c0` |
| Members | 56 regular files; no `.pyc` or `__pycache__` |
| Member-inventory SHA-256 | `48967935bb847fe2384a6caf18c7901a7eee2d6afeca4b73458b315cf36c12cf` |
| Decompressed tar SHA-256 | `d480160198f649336683f71b924d57f2699c9111036ede1ab4524d375b5d9da2` |
| Manifest | `release/v2.12.1-runtime.manifest`, 41 rows |
| Manifest SHA-256 / installer pin | `dd61ffe5ed51d05091417feb5bc43de059b551b922b6ef9923a62073cb351e5a` |
| Payload audit | **41/41 hashes and modes match; target counts 62 upgrade/63 fresh; pyc 0** |
| Sanitised evidence | `verification/ISSUE-5-V2.12.1-LANG-EVIDENCE-20261106/`, 41 files |
| Evidence `SHA256SUMS` | `d667246e9e226f356af7f316526739ad1fc59dc0e01502020dbea37cacbe5333` (covers 40 files) |
| Final jail harness | `.../jail-harness.py`, SHA-256 `299414158631614af4866dd72c39bbc1af5e946520c71c63a79e0592969e45ac` |
| Superseded initial candidate | `adaa2b2def784eb5d4b3f3c2b3a66b0ba4913fc16fdb6fd51d552b4fb4091bc`, retained unchanged |
| Superseded intermediate | `dbf350ffd1c58959504d934b9b02c8ad58412013df2a68d7173b5d4af37951f0`, `1596559` bytes, 56 members, retained under `superseded/` |

### Language-catalogue correction

The language failure was reproduced at parent `d5d73ed` with the clean-runner-equivalent review
path. `de_DE` reported ten page strings absent from its source catalogue and then failed with
`KeyError: 'Identity conflicts'`; CI showed the related `KeyError: 'MAC change announcements'`.
The source views already referenced those strings, but the catalogues did not contain their
message IDs.

Only the missing entries were appended to the eleven existing catalogues: nine entries were needed
for `en_US` and `cs_CZ`, and ten for the other nine languages. No existing translation, message
string, UI template or runtime behaviour was changed. The translated values came from the existing
integration-branch catalogues, preserving the project's historical translations. The manifest,
installer pin and release notes were regenerated consistently for the corrected catalogue bytes.

The first attempted language correction produced the intermediate `dbf350…` bundle. Tail
whitespace normalisation changed the bundled catalogue bytes, so that bundle, its source snapshot,
harness and jail evidence were retained as superseded rather than reused. The final `ba5737…`
bundle was rebuilt twice after the normalisation and both builds were byte-identical. The final
commit was rebuilt independently from its extracted tree into two clean output directories; both
matched the jail-tested `ba5737…` archive byte-for-byte. The actual archive, harness
`CANDIDATE_SHA`, sanitised evidence and these records therefore describe the same tested bytes.

The final source and test checks passed:

```text
LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=0 engine=interpolate failures=0
MSGFMT_CHECK=PASS files=11
LOCALE_MERGE=PASS
TRANSLATED_JAVASCRIPT=PASS
V2121_RELEASE_MANIFEST=PASS rows=41 payload_hashes=41 upgrade_targets=62 fresh_targets=63
CORE_LOCALE_ROLLBACK=PASS cases=3
BUNDLE_REPRODUCIBILITY=PASS cases=7
BUNDLE_AUDIT=PASS members=56 manifest_rows=41 payload_hashes=41/41 payload_target_modes=41/41 target_counts=62/63 member_modes=canonical pyc=0 noncanonical_modes=0
FRESH_INSTALL_DEFAULTS_REGRESSION=PASS
SHELL_SYNTAX=PASS files=6
JAIL_SCENARIOS=PASS passed=6 failed=0
```

The local clean-runner-equivalent rendering run also passed, with one warning-level gap because
`nl_NL` is absent from this host's language picker; CI reported `gaps=0` and failures remained zero
in both runs.

### Final exact-commit CI

GitHub Actions run
[42178982940](https://github.com/apg19590209/opnsense-devicemonitor/actions/runs/42178982940) was a
`push` event for `fix/issue-5-v2.12.1` with `headSha`
`5c3ee29e9bc3ae7baf1f55a8cf7f25ad231399d6`. Its single `validate` job completed with
`conclusion: success`; every step passed. The logs report:

```text
V2121_RELEASE_MANIFEST=PASS rows=41 payload_hashes=41 upgrade_targets=62 fresh_targets=63
CORE_LOCALE_ROLLBACK=PASS cases=3
BUNDLE_REPRODUCIBILITY=PASS cases=7
LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=0 engine=interpolate failures=0
LOCALE_MERGE=PASS
TRANSLATED_JAVASCRIPT=PASS
FRESH_INSTALL_DEFAULTS_REGRESSION=PASS
```

The workflow's runtime rendering matrix was skipped explicitly because the Ubuntu runner lacks the
Phalcon Volt compiler and OPNsense `ViewTranslator`; this is a documented runner limitation, not a
pass of production OPNsense rendering. At that pre-publication check, `main` remained at
`d5d73ed`, `release/2.13` remained at `6bd122e64ed5c65d632c45c03e1cd33796def7ba`, and no
`v2.12.1` tag existed. Publication followed under separate authorisation.

## Publication and independent verification (6 November 2026)

The separately authorised tag and release were created from the exact validated source. The tag is
annotated but not GPG-signed: GitHub reports `verification.verified=false` with reason `unsigned`.
That is the only signing limitation; the tag object resolves to the required commit.

| Item | Value |
|---|---|
| Release | https://github.com/apg19590209/opnsense-devicemonitor/releases/tag/v2.12.1 |
| Tag | `v2.12.1`, annotated tag object `349dc0932aebaa148a59b60cedf046a8a8414a88` (unsigned) |
| Target commit | `5c3ee29e9bc3ae7baf1f55a8cf7f25ad231399d6` |
| Commit tree | `2f7e0a6e386431ab89d383d9bfc54bd20adacefa` |
| Release state | published, non-draft, non-prerelease |
| Release API target field | `targetCommitish: main`; the tag object itself targets the exact commit above |
| Runtime asset | `dm-v2.12.1-runtime.tar.gz`, `1596559` bytes |
| Runtime SHA-256 | `ba5737e9e2fc0d9b78edaacef82aeee30c9a8656db4f27cc9800473af71957c0` |
| Checksums asset | `SHA256SUMS`, `92` bytes, SHA-256 `006a3404d6f2e3eca2997c820323eb9b85a89c5806fbd3faf616ff6ebe90823f` |
| Release notes | `publication/v2.12.1-release-notes.md`, `4003` bytes, SHA-256 `8c8d2f83093f00af7b5d425a648bbf33de0882e33c8fb35ec350ed16662c6fa5` |

The repair branch and tag were rechecked from the remote:

```text
5c3ee29e9bc3ae7baf1f55a8cf7f25ad231399d6	refs/heads/fix/issue-5-v2.12.1
349dc0932aebaa148a59b60cedf046a8a8414a88	refs/tags/v2.12.1
5c3ee29e9bc3ae7baf1f55a8cf7f25ad231399d6	refs/tags/v2.12.1^{}
```

Exact-SHA CI run
[42178982940](https://github.com/apg19590209/opnsense-devicemonitor/actions/runs/42178982940)
was re-read after publication: `headSha=5c3ee29e…`, target branch
`fix/issue-5-v2.12.1`, event `push`, overall conclusion `success`; its `validate` job and all
reported steps completed successfully.

### Independent upload audit

Both release assets were downloaded independently from the public release URLs to
`/root/dm-issue5-v2121-langfix-20261106T061929Z/publication/independent-download/`. The download
was compared with the archive actually used by the six jail scenarios, not merely with the local
upload copy.

| Check | Result |
|---|---|
| `sha256sum -c SHA256SUMS` | PASS |
| Archive size | `1596559` bytes, as published |
| Byte comparison with jail-tested archive | PASS (`cmp` identical) |
| Members | 56 regular files, canonical modes, no `.pyc`/`__pycache__` |
| Member-inventory SHA-256 | `48967935bb847fe2384a6caf18c7901a7eee2d6afeca4b73458b315cf36c12cf` |
| Decompressed tar SHA-256 | `d480160198f649336683f71b924d57f2699c9111036ede1ab4524d375b5d9da2` |
| Manifest | `release/v2.12.1-runtime.manifest`, 41 rows, 41 unique sources, 41 unique targets |
| Manifest SHA-256 / installer pin | `dd61ffe5ed51d05091417feb5bc43de059b551b922b6ef9923a62073cb351e5a` (match) |
| Payload audit | 41/41 source hashes and declared install modes match |
| Version identity | installer `VERSION=2.12.1`; `defaults.json` version `2.12.1` |
| Target derivation | 11 locale catalogues; 62 upgrade targets / 63 fresh targets |
| Archive member set | exactly the 41 manifest sources, 11 sidecar catalogues, manifest, two installers, two helpers and `uninstall.sh` |

```text
ARCHIVE_AUDIT=PASS
members=56 regular=56 archive_modes=canonical pyc=0
manifest_rows=41 unique_sources=41 unique_targets=41
payload_hashes=41 payload_install_modes=41 manifest_sha256=dd61ffe5ed51d05091417feb5bc43de059b551b922b6ef9923a62073cb351e5a
installer_version=2.12.1 manifest_pin_match=True install_mode_applied=yes
locales=11 upgrade_targets=62 fresh_targets=63
expected_member_set_match=True member_set_size=56
defaults_version=2.12.1 po_sidecars=11
```

The archive stores ordinary source members as canonical `644` members; the manifest's `755` rows
are applied by the installer's `install -m "$mode"` step. The audit therefore checks canonical
archive modes separately from the 41 declared target modes. This is intentional build
normalisation, not a mode mismatch.

The published release body was checked against `publication/v2.12.1-release-notes.md`: it records
issue #5, the exact artifact identity, download/preflight and install commands, successors from
2.8 through 2.12, backup/recovery guidance and validation limits. It explicitly says the jail
stubs exercise installer flow and service boundaries only and do not prove real OPNsense plugin
registration, configd interaction, daemon lifecycle or live `FRESH=1`.

### Preserved v2.12 release

Only the v2.12 release body was edited. The historical tag object remains
`39e427d63806731e2ca7d74264309f00dc903060`, targeting
`92072a53ff036fbb2b56eb663ef6d7a89fd0f36e`. Its sole asset remains
`dm-v2.12-runtime.tar.gz`, `320511` bytes, SHA-256
`6b0ed37e2f215b6e874b59d546a6c7e08424fbbe5e5065554201d009e3358071` and asset ID
`RA_kwDOUNJ0184pmwCG`.

The pre-edit body, including the stale “not yet published” wording, is retained at
`publication/v2.12-release-before.json` (body SHA-256
`7c776dd853cab858df7b056b781fcf380eb7abfc851f9c66a2bff9cf5d7df423`). The published body now
opens with a blockquote warning to use v2.12.1 and links to
https://github.com/apg19590209/opnsense-devicemonitor/releases/tag/v2.12.1; its SHA-256 is
`1765a75bdd95881a6512452818434f2b2325eee33b285e650e91a28bd77af99d`. The tag and asset identity
were re-read after the edit and are unchanged.

`main` remained `d5d73edffc0200cf8c84a63689e1937f92002435` locally and remotely; `release/2.13`
remained `6bd122e64ed5c65d632c45c03e1cd33796def7ba`.

### Reporter follow-up (6 November 2026)

One scoped follow-up comment was posted to GitHub issue #5:

https://github.com/apg19590209/opnsense-devicemonitor/issues/5#issuecomment-6680082397

The comment body SHA-256 is
`ccd54e0533ee1324cb4ab40138e5dca736ebce63d3c7659764dda1d5f64af2ba`. It thanks the reporter,
acknowledges that v2.12 shipped with inconsistent installer manifest checks, and explains that the
abort occurred before installed files changed. It links the verified v2.12.1 release and asks the
reporter to download both assets, verify the checksum, extract into a new empty directory, and run
the preflight with their exact hostname before following the release installation instructions. It
asks for the preflight and installation results with secrets redacted if an error remains, and
states that the disposable-jail evidence does not prove real-host registration or lifecycle
behaviour.

Issue #5 remained OPEN after the comment. GitHub reported one comment, updated
`2026-11-06T07:55:40Z`, and no other GitHub change was made.

## Initial v2.12.1 repair candidate (historical)

The first repair candidate was prepared in a retained isolated snapshot, without switching,
resetting or writing to the dirty integration checkout:

All bundle, manifest and remote-ref values in this historical table are the initial `a21373a`
values; they were replaced by the final candidate above.

| Item | Value |
|---|---|
| Base | `main` commit `d5d73ed` (v2.12 line; 2.14.0 integration changes excluded) |
| Repair branch | `fix/issue-5-v2.12.1` |
| Initial repair commit | `a21373a6297edc1fcafd6a9be35e9d2c071f6129` |
| Commit tree | `73b71dc63235d2b05fa4e7e3cc64604b10fc7da6` |
| Commit parent | `d5d73edffc0200cf8c84a63689e1937f92002435` |
| Historical remote ref | `refs/heads/fix/issue-5-v2.12.1` at `a21373a` before the language correction |
| Isolated workspace | `/root/dm-issue5-v2121-repair-20261106T045721Z` |
| Candidate snapshot | `/root/dm-issue5-v2121-repair-20261106T045721Z/candidate` |
| Pristine base | `git archive d5d73ed`, extracted at `.../baseline` |
| Initial candidate bundle | `/root/dm-issue5-v2121-repair-20261106T045721Z/dm-v2.12.1-runtime.tar.gz` |
| Size | `1584271` bytes |
| SHA-256 | `adaa2b2def784eb5d4b3f33c2b3a66b0ba4913fc16fdb6fd51d552b4fb4091bc` |
| Members | 56 regular files; no `.pyc` or `__pycache__` |
| Member-inventory SHA-256 | `48967935bb847fe2384a6caf18c7901a7eee2d6afeca4b73458b315cf36c12cf` |
| Decompressed tar SHA-256 | `8e2bbbbbc4cdbb1e56edafcd57257510e1d44fcb83a52049782dd34d7e901226` |
| Manifest | `release/v2.12.1-runtime.manifest`, 41 rows |
| Manifest SHA-256 | `77947c4b8cf915344cf167085f1ff8a609d488f617f37c2cc2a37d5cc9afc9d6` |
| Payload audit | **41/41 hashes and modes match; target counts 62/63** |
| Historical v2.12 manifest | unchanged, SHA-256 `00698f943b3c3fd79fa9a8dcfa061020df0306ef9952b29b444d725f938a5d3a` |
| Earlier manifest-only candidate | `/root/dm-issue5-v2121-validation-20261106T035748Z/dm-v2.12.1-runtime.tar.gz` |
| Earlier identity | 320571 bytes, SHA-256 `da14af8d63eea847e253650087357822f7cc886b20b8fa6e85786aa442e43efb`, 55 members |

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

### Initial regression and artifact results (historical)

These are the results for the initial `adaa2b2…` candidate, before the language correction. They
are retained to show the order of validation and are not the final bundle identity.

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

### Initial source publication and failed exact-commit CI (historical)

The repair source was committed without checking out or changing the dirty integration branch. The
single commit has parent `d5d73edffc0200cf8c84a63689e1937f92002435`, tree
`73b71dc63235d2b05fa4e7e3cc64604b10fc7da6`, and 45 files (`+3846/-79`): 16 repair
source/test/CI/release-documentation files, the sanitised investigation record and 28 sanitised
evidence files. Backups, credentials, ignored `.cline-reports`, bytecode and the bundle binary were
excluded. The branch was pushed non-force with the exact-SHA refspec
`a21373a6297edc1fcafd6a9be35e9d2c071f6129:refs/heads/fix/issue-5-v2.12.1`.

The actual archive, the corrected harness `CANDIDATE_SHA`, the committed sanitised
`build-comparison.txt`/`SHA256SUMS`, and the active records all agree on SHA-256
`adaa2b2def784eb5d4b3f3c2b3a66b0ba4913fc16fdb6fd51d552b4fb4091bc`. No conflicting tested bytes
were found. Two clean builds from the committed tree, at
`.../committed-build-20261106T055615Z/`, are both `1584271` bytes with that digest and are
byte-identical to the six-scenario jail-tested archive.

GitHub Actions run [42171501459](https://github.com/apg19590209/opnsense-devicemonitor/actions/runs/42171501459)
was a `push` event for branch `fix/issue-5-v2.12.1` and head SHA
`a21373a6297edc1fcafd6a9be35e9d2c071f6129`. The v2.12.1-specific checks passed on that exact
checkout:

```text
V2121_RELEASE_MANIFEST=PASS rows=41 payload_hashes=41 upgrade_targets=62 fresh_targets=63
CORE_LOCALE_ROLLBACK=PASS cases=3
BUNDLE_REPRODUCIBILITY=PASS cases=7
LOCALE_MERGE=PASS
```

The overall run nevertheless failed in the inherited `Validate language acceptance (DM-BL-008)`
step, before the remaining unrelated workflow steps:

```text
FAIL: de_DE: 10 page strings absent from the source catalogue, e.g. Also email identity conflict alerts
KeyError: 'MAC change announcements'
```

This is not introduced by the repair. `tests/test_language_acceptance.py` and the language
catalogues are unchanged from `d5d73ed`; the only `settings.volt` delta is the visible
`v2.12` to `v2.12.1` version label. At `d5d73ed`, the English source catalogue has no `msgid`
entry for the settings-page keys `Also email identity conflict alerts`, `Emails are sent when the
state changes. Set how often each category is repeated while the state has not changed. 0 never
repeats.`, `Features and Enhancements`, `Identity conflicts`, `MAC change announcements`, `Repeat
unchanged alerts`, `Scan results`, `Service outages` and `minutes`. Correcting that inherited
language/catalogue defect would expand the authorised repair scope, so the published commit and
remote ref were left unchanged and the test was not weakened. The exact-commit CI gate is therefore
**FAILED (overall)** despite the v2.12.1 release-input, rollback and reproducibility checks passing.

### Initial disposable FreeBSD jail validation (historical)

This section records the initial `adaa2b2…` candidate. The final language-corrected bundle was
validated separately below because its bytes changed.

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
targets and the harness's preserved core-locale state directory still mode `0755` with 19 files.
The live `/usr/local/share/locale` tree contains 20 `OPNsense.mo` files, but the harness fingerprint
covers the `/var/backups/devicemonitor/core-locale` state plus the manifest-installed targets,
not every live core catalogue. The 19-file figure is therefore not a complete live-catalogue
verification. Every scenario reports
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

### Final language-corrected disposable jail validation

The final `ba5737…` bundle was tested with the retained isolated harness
`.../jail-harness.py`, SHA-256
`299414158631614af4866dd72c39bbc1af5e946520c71c63a79e0592969e45ac`, which pins
`CANDIDATE_SHA=ba5737e9e2fc0d9b78edaacef82aeee30c9a8656db4f27cc9800473af71957c0`. The gate
reported premium status and its supported interactive `y` confirmation was used; no bypass,
`--force`, clock change or gate edit was used. All six scenarios passed against this exact bundle:

| Scenario | Final result |
|---|---|
| `check` | **PASS:** 62 targets; data, configuration and core state unchanged; no service calls, backup or stage leftover |
| `upgrade` | **PASS:** 62 targets; data and configuration preserved; `configd restart` then `devicemonitor restart` |
| `fresh` | **PASS:** 63 targets; no seeded data or configuration; plugin-registration, `configd restart`, `devicemonitor start`, `rc.conf` and rc link created |
| `repair` | **PASS:** second install preserved targets/data/configuration; two service cycles and two retained backups |
| `rollback` | **PASS:** injected `configd` failure; `ROLLBACK_STATUS=COMPLETE`; all targets restored; 19 core-locale files restored, none removed |
| `fresh-rollback` | **PASS:** injected fresh-install failure; `ROLLBACK_STATUS=COMPLETE`; targets restored; 19 installed core-locale files removed; rc link/conf removed |

Independent before/after evidence for the two rollback paths:

```text
UPGRADE_ROLLBACK_TARGETS_SHA256=449b8c1fa0cdf6020cb204c052f09dd1b41660263e47b8138697904037464330
UPGRADE_ROLLBACK_CORE_STATE_SHA256=fd9ce84bccb9606f8ca9dfe919aff65c960a7e8465982b0471c355e208dfd617
UPGRADE_CORE_LOCALE_STATE_BACKED_UP=present files=19
UPGRADE_CORE_LOCALE_ROLLBACK_SUMMARY=restored=19 removed=0 conflicts=0 failed=0
UPGRADE_ROLLBACK_STATUS=COMPLETE

FRESH_ROLLBACK_TARGETS_SHA256=b9e32655b14825f34c349776107206a77e231255a3a7bbe621d2b412cd26bfcb
FRESH_ROLLBACK_CORE_STATE_SHA256=7b15bc2f349ae5c6e6ce4972ae939289e3b468493623bf3208c41f2bb64781a8
FRESH_CORE_LOCALE_STATE_BACKED_UP=absent files=0
FRESH_CORE_LOCALE_ROLLBACK_SUMMARY=restored=0 removed=19 conflicts=0 failed=0
FRESH_ROLLBACK_STATUS=COMPLETE
```

The independent before/after live fingerprints were identical:

```text
LIVE_FINGERPRINT_SHA256=519741390cb119faf5ca05a22ee26f1c04ea80b6bc70fd99a8d8d002b3f16887
LIVE_FINGERPRINT_BEFORE_AFTER=PASS
LIVE_INSTALLED_RECORD_SHA256=d891ce68c9035b3bcd2384d6f3705d6c8d9bc20fb5ef13cc9ca80b2ae1c035a2
LIVE_INSTALLED_TARGETS=63
```

That fingerprint covers application database/configuration hashes, service rc files, backup
directory entries, the preserved core-locale state directory and all 63 manifest-installed targets.
It does not hash every file under `/usr/local/share/locale/*/LC_MESSAGES/`, so live core-catalogue
continuity is supported by the unchanged backup state rather than a whole-tree live hash.

The service-call boundaries were limited to `configd` restart, `devicemonitor` restart/start/stop,
and the sandbox plugin-registration call appropriate to each scenario. `check` recorded no service
call. The harness reported `JAIL_TORN_DOWN`, `MOUNTS_TORN_DOWN`, `WORKDIR_REMOVED` and
`LIVE_FINGERPRINT_UNCHANGED` for every scenario; `jls` was empty, no `dm-v2121` mount remained, and
`/var/tmp/dm-v2121-jail-work` was absent. The candidate identity was rechecked after the run and
remained `ba5737…`. Raw jail evidence contains 141 files; the committed sanitised subset contains
41 files and `SHA256SUMS` (digest
`d667246e9e226f356af7f316526739ad1fc59dc0e01502020dbea37cacbe5333`) covers the other 40.

### Jail boundary and limitations

The following are jail-only stubs, not real OPNsense behaviour: `opnsense-version`, `service`
(`configd` and `devicemonitor` call recording/failure injection), `rc.configure_plugins`, and the
daemon-state `pgrep` shim. The harness therefore proves the installer's service-call boundaries and
the fresh plugin-registration call, but does not prove real configd interaction, real OPNsense
plugin registration, real daemon lifecycle, or live `FRESH=1`. `nmap` was present from the host
toolchain, so no package installation path was exercised. No live installation, service, monitoring
or production/`.252`/`.253` access occurred. The harness did not hash the whole live locale tree,
so no whole-tree live catalogue continuity is claimed.

### Backups and rollback

The base is also retained as a pristine extracted copy at
`/root/dm-issue5-v2121-repair-20261106T045721Z/baseline`. The pre-change repair files are in
`.../backups/prechange/` with `backup-manifest.txt`; the captured hashes and modes were rechecked.
The records before this update are backed up at `.../backups/records/20261106T054748Z/`:
the investigation was SHA-256 `58410f394186cc4a653fe1328ea2081a64bcec5be4d16dc119a86cae84e895e6`
and the milestone report was SHA-256
`18c57a8d97a4aecfc7c0a7d0274bb3855df23d4a0b4c575a444f59b0aaebb017`; both are mode `644`.
The earlier record backup at `.../backups/records/20261106T050714Z/` is also retained.

The records before the publication/CI update were backed up at
`.../backups/records/20261106T060130Z-ci-update/`. The investigation was SHA-256
`978b4b9ed5c09927f2c20e7749c995db9eb4762eaf8570735f99493e76293cf7` and the preceding milestone
report was SHA-256 `9941abb1210ef4071d598575b156068a69b7a135a3ef7cd828e85a840770c1f5`; both
remain mode `644`. Exact-SHA CI output is retained outside the repository at
`.../ci-evidence-20261106T060130Z/`.

The canonical investigation record before this final language/CI update was backed up at
`/root/dm-issue5-v2121-langfix-20261106T061929Z/backups/records/20261106T181103Z-langfix-final/`.
Its source hash was `ec7c0ca2712f35b811609a6d63070baac662bbd88f19bf725614d75de4f66f81`; the
`cp -p` backup matched byte-for-byte and remained mode `644`. The final isolated workspace retains
the two committed-tree builds, current 141-file raw jail set, 41-file sanitised evidence set and
the superseded `dbf350…` snapshot. The initial `adaa2b2…` workspace remains preserved under
`/root/dm-issue5-v2121-repair-20261106T045721Z`.

The investigation record before this publication update was backed up with `cp -p` at
`/root/dm-issue5-v2121-langfix-20261106T061929Z/backups/records/20261106T184237Z-publication/`.
Its pre-update SHA-256 was
`3eed76f3e5ae2aac50457a08f6d77fce34dd45deece738103d3c2c7a2c0a4bb5`; the backup matched
byte-for-byte and remained mode `644`. The v2.12 release body and asset metadata before editing
are retained at `publication/v2.12-release-before.json` and
`publication/v2.12-release-pre-edit.json`; the updated body is
`publication/v2.12-release-updated.md`. Publication API responses and the independently
downloaded assets are retained under `publication/`.

The investigation record before this reporter-follow-up update was backed up with `cp -p` at
`/root/dm-issue5-v2121-langfix-20261106T061929Z/backups/records/20261106T185550Z-comment/`.
Its pre-update SHA-256 was
`2bd90f22fda2483a79e18ce34d4a07b9c1137498d9a8b9eddf3676033054ef90`; the backup matched
byte-for-byte and remained mode `644`. The prepared comment body is retained at
`publication/issue-5-follow-up.md` (SHA-256
`ccd54e0533ee1324cb4ab40138e5dca736ebce63d3c7659764dda1d5f64af2ba`), and the post-comment
issue snapshot is `publication/issue-5-after-comment.json`.

To discard the whole isolated repair without touching the integration checkout, remove only
`/root/dm-issue5-v2121-repair-20261106T045721Z` and its pointer file after retaining the evidence
required by the operator. Do the same for `/root/dm-issue5-v2121-langfix-20261106T061929Z` only
after its retained evidence is no longer needed. To restore the initial candidate to the
pre-repair state, restore the files in
`backups/prechange/` with `cp -p`, remove `release/core-locale-state.sh`,
`release/normalize-bundle-tar.py`, `release/bundle-gzip.py`,
`tests/test_core_locale_rollback.py` and `tests/test_bundle_reproducibility.py`, and rebuild the
bundle. To restore the base exactly, replace only the isolated `candidate` directory from
`baseline`. To roll back this record, restore
`.../backups/records/20261106T181103Z-langfix-final/ISSUE-5-V2.12-MANIFEST-20261106.md` with
`cp -p` to
`verification/ISSUE-5-V2.12-MANIFEST-20261106.md`. To undo only the publication-record update,
restore
`.../backups/records/20261106T184237Z-publication/ISSUE-5-V2.12-MANIFEST-20261106.md` with
`cp -p` instead. To undo only the reporter-follow-up record update, restore
`.../backups/records/20261106T185550Z-comment/ISSUE-5-V2.12-MANIFEST-20261106.md` with
`cp -p`. The posted GitHub comment is not altered by that rollback and must not be edited or
deleted without separate authorisation. To revert the harness-only pin correction,
restore `.../backups/harness-pin-20261106T053755Z/jail-harness.py` with `cp -p`; this would
reintroduce the deliberately superseded 63-character pin and should only be used for diagnostic
comparison. The published repair commit must be reverted with a new commit if that becomes
necessary; do not force-push or rewrite the already-pushed branch.

## Publication path (completed)

Do **not** overwrite `dm-v2.12-runtime.tar.gz` and do **not** move or replace tag `v2.12`. Preserve
that tag and asset as the immutable record of the defect. Do not direct the reporter to the
unreleased 2.14.0 integration candidate.

The safe path is a new patch release, `v2.12.1`, based on `main` at `d5d73ed` (the first commit
whose v2.12 test suite is repaired; it has no runtime `src/` changes relative to tag `v2.12`).
The final candidate materialises the version bump, the 41-row manifest, the digest/row/target guards,
predecessor acceptance, stage/backup identity, release notes, installation text, the authorised
rollback correction, the language-catalogue correction and reproducible-build inputs. Publication
was subsequently completed under separate authorisation; the items below are the remaining
verification and follow-up boundaries, not outstanding tag/release actions.

## Remaining validation and follow-up gates

1. Publication is **COMPLETE** at
   https://github.com/apg19590209/opnsense-devicemonitor/releases/tag/v2.12.1. Do not replace or
   move the `v2.12.1` tag, and do not replace either release asset. The independent download
   validated the uploaded archive and checksum file.
2. One scoped reporter follow-up was posted at
   https://github.com/apg19590209/opnsense-devicemonitor/issues/5#issuecomment-6680082397.
   Issue #5 remains OPEN pending the reporter's preflight/installation results and any further
   follow-up, which requires separate authorisation.
3. Any live deployment or host-level validation remains separately gated and is not part of this
   investigation. The jail proves installer paths with stubs, not real OPNsense plugin
   registration, configd interaction, daemon lifecycle or live `FRESH=1`; the CI runtime rendering
   matrix was explicitly skipped for missing runner assets.
4. The live locale fingerprint does not hash every file under
   `/usr/local/share/locale/*/LC_MESSAGES/`; whole-tree live catalogue continuity is not claimed.
5. DM-BL-009 remains **OPEN** and §9.4 remains paused; neither is moved by this release repair.

No production, `.252` or `.253` contact is required. A live `.23` deployment is not part of this
investigation proposal.

## Current state

* GitHub issue #5: **OPEN**, with one scoped follow-up comment at
  https://github.com/apg19590209/opnsense-devicemonitor/issues/5#issuecomment-6680082397;
  issue `updatedAt` is `2026-11-06T07:55:40Z`.
* DM-BL-009: **OPEN**.
* §9.4: paused, not executed.
* Published v2.12.1: annotated tag object `349dc0932aebaa148a59b60cedf046a8a8414a88` (unsigned)
  targets `5c3ee29e9bc3ae7baf1f55a8cf7f25ad231399d6`; release and tag URLs are recorded above.
  Exact-commit CI run `42178982940` is green. The tested and independently downloaded bundle is
  `1596559` bytes, SHA-256
  `ba5737e9e2fc0d9b78edaacef82aeee30c9a8656db4f27cc9800473af71957c0`, 56 members; `SHA256SUMS`
  is `92` bytes with SHA-256
  `006a3404d6f2e3eca2997c820323eb9b85a89c5806fbd3faf616ff6ebe90823f`.
* Historical v2.12: tag object `39e427d63806731e2ca7d74264309f00dc903060` and target
  `92072a53ff036fbb2b56eb663ef6d7a89fd0f36e` unchanged; asset `320511` bytes, SHA-256
  `6b0ed37e2f215b6e874b59d546a6c7e08424fbbe5e5065554201d009e3358071` unchanged. Only the
  release notes were edited to warn against the defective installer and link v2.12.1.
* Superseded failed candidates: the initial `adaa2b2…` candidate remains at
  `/root/dm-issue5-v2121-validation-20261106T035748Z/` and its repair workspace; the intermediate
  `dbf350…` candidate and jail evidence remain under
  `/root/dm-issue5-v2121-langfix-20261106T061929Z/superseded/`.
* Validation harness: one pre-run SHA pin typo corrected and backed up; one display-label artifact
  in the fresh-rollback file count documented. Neither changes the candidate or the PASS logic.
* Canonical integration checkout: preserved with its pre-existing dirty entries; nothing staged.
* Pending worktree changes: preserved; this reporter-follow-up update changed only this record and
  adds the milestone report in the canonical checkout. The current milestone report is
  `.cline-reports/REPORT-20261106-185550.md` and is not staged. The preceding publication report is
  `.cline-reports/REPORT-20261106-184237.md`.
