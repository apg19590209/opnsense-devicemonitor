# Device Monitor — DM-BL-010 catalogue-header repair (7 November 2026)

## Result

DM-BL-010's non-fatal `msgfmt` warnings were reproduced and corrected in a development-branch
candidate for the forthcoming 2.14.0 release. The investigation evidence below predates the branch
commit; the companion milestone report records the commit, exact-SHA CI and PR evidence. The
correction is not merged, tagged or published. The live `.23` installation, published v2.12.1
payload and all existing tags/assets are unchanged. DM-BL-010 and issue #5 remain **OPEN**.

This candidate also adds the published v2.12.1 release to the supported upgrade-predecessor set. It
does not modify v2.12.1 itself and does not make 2.14.0 available.

## Reproduction

The pre-repair sequence (`msgunfmt` → `msgcat` → `msgfmt --check`) was run on a sparse core
catalogue and a complete plugin catalogue. `msgfmt` exited `0`, but emitted exactly:

```text
warning: header field 'PO-Revision-Date' missing in header
warning: header field 'Last-Translator' missing in header
warning: header field 'Language-Team' missing in header
```

The complete command output is preserved at
`/root/dm-validation-2140/dm-bl-010-20261107/warning-reproduction/` (`result.txt` SHA-256
`f55c35d6d3177eb91412b8b1f020a964614ef1a4a288b331e3eae8d3ecda8108`; stderr SHA-256
`412d570ab669db09f85d7ad79a1466b83f08e0677cbfb236e62ff2c0ec3a7517`).

The warning class is non-fatal metadata only. It does not change catalogue strings or installer
success.

## Correction

`release/merge-opnsense-catalog.sh` now:

- reads the real metadata from the plugin `.mo`;
- fills only absent or empty generated `PO-Revision-Date`, `Last-Translator` and `Language-Team`
  fields in the prepared core catalogue;
- leaves every field already present in the core catalogue unchanged;
- rejects an incomplete plugin header rather than inventing attribution;
- validates both the prepared core and final merged catalogue with `msgfmt --check`;
- preserves the existing core-first translation merge and digest checks; and
- leaves stderr visible rather than suppressing warnings globally.

No translation text, source `.po` content, published bundle, tag or release asset was changed.

## Regression coverage

`tests/test_locale_merge.py` now covers:

- warning-free merging from a sparse core header;
- preservation of existing core translations and metadata;
- use of real plugin metadata only for missing fields;
- rejection of an incomplete plugin header;
- rejection of a malformed plugin catalogue; and
- rejection of a malformed core catalogue.

The suite is selected by `.github/workflows/ci.yml`. Local results:

| Check | Result |
|---|---|
| `python3 tests/test_locale_merge.py` | `LOCALE_MERGE=PASS` |
| `python3 tests/test_upgrade_predecessors.py` | `UPGRADE_PREDECESSORS=PASS passed=10 skipped=0` |
| `python3 tests/test_ci_config.py` | `CI_CONFIG=PASS cases=6` |
| `python3 tests/test_release_inputs.py` | `RELEASE_INPUTS=PASS cases=7` |
| `python3 tests/test_release_manifest.py` | `V2140_RELEASE_MANIFEST=PASS` |
| `python3 tests/test_catalogue_determinism.py` | `CATALOGUE_DETERMINISM=PASS cases=2` |
| `python3 tests/test_bundle_reproducibility.py` | `BUNDLE_REPRODUCIBILITY=PASS cases=9` |
| `python3 tests/test_bundle_build_safety.py` | `BUNDLE_BUILD_SAFETY=PASS cases=8` |

`tests/test_bundle_determinism.py` is the clean-checkout/CI proof and cannot pass against a
pre-commit working tree because it clones `HEAD`. The equivalent local proof built the candidate
four times from the same worktree: `build-a`, `build-b`, `build-c` and `build-d` are byte-identical.
CI and this test must be run on the committed SHA before integration; the companion milestone
report records that result.

## Release inputs and bundle identity

- `release/release-inputs.sha256` was regenerated and verifies with `VERIFY_OK=4`.
- `release/merge-opnsense-catalog.sh` pin:
  `65e9bdd7fcdb321dec95349a67dd250d55eb99d6d53b615f2c1d13d5c091d957`.
- `release/release-inputs.sha256` SHA-256:
  `9430099d1254f5e95df0afdd71ae6d3aa02dfde2c1e5bcdd185dd08bcd875db3`.
- `release/bundle-digest.txt` now records the new candidate.
- Candidate bundle: **1,729,177 bytes**, SHA-256
  **`90afa55dd826c0dc3be8a23902b809baa465e25191dc372dc6cc2ef4e57fc243`**, 60 members.

Preserved evidence:

- candidate builds and previous candidate:
  `/root/dm-backups/dm-bl-010-candidate-20261107-075441/`;
- previous 2.14.0 main-integration candidate: 1,725,593 bytes, SHA-256
  `5149bfd41e5842a144a9d1280c008511f20f3783932eca9beb1f48fca6173f5f`;
- pre-edit backup: `/root/dm-backups/dm-bl-010-implementation-20261107-182800/`;
- pre-edit checksums: `/root/dm-backups/dm-bl-010-implementation2-20261107-075441/`.

## Published v2.12.1 predecessor

The actual published archive used for jail validation is:

```text
/root/dm-issue5-v2121-langfix-20261106T061929Z/publication/independent-download/dm-v2.12.1-runtime.tar.gz
```

It is 1,596,559 bytes with SHA-256
`ba5737e9e2fc0d9b78edaacef82aeee30c9a8656db4f27cc9800473af71957c0`. All 56 archive members
match tag `v2.12.1`.

The new candidate accepts `2.12.1` as an upgrade predecessor. The local matrix now contains ten
predecessors including that tag, and the suite requires ten passes with zero skips. The installer
also accepts v2.12.1 in its runtime predecessor guard without changing the current-version path.

## Disposable-jail results

| Scenario | Result | Evidence |
|---|---|---|
| Existing live 2.14.0-predecessor `check` | PASS | `/root/dm-validation-2140/dm-bl-010-20261107/legacy-scenarios/check/` |
| Existing live 2.14.0-predecessor `install` | PASS | `/root/dm-validation-2140/dm-bl-010-20261107/legacy-scenarios/install/` |
| Existing live 2.14.0-predecessor `repair` | PASS | `/root/dm-validation-2140/dm-bl-010-20261107/legacy-scenarios/repair/` |
| Existing live 2.14.0-predecessor `rollback` | PASS | `/root/dm-validation-2140/dm-bl-010-20261107/legacy-scenarios/rollback/` |
| Existing live 2.14.0-predecessor `failclosed` | PASS | `/root/dm-validation-2140/dm-bl-010-20261107/legacy-scenarios/failclosed/` |
| Fresh install | PASS | `/root/dm-validation-2140/dm-bl-010-20261107/fresh-scenarios/fresh/` |
| Fresh install with injected rollback | PASS | `/root/dm-validation-2140/dm-bl-010-20261107/fresh-scenarios/fresh-rollback/` |
| Published v2.12.1 predecessor `check` | PASS | `/root/dm-validation-2140/dm-bl-010-20261107/v2121-predecessor/check/` |
| Published v2.12.1 predecessor `install` | PASS | `/root/dm-validation-2140/dm-bl-010-20261107/v2121-predecessor/install/` |
| Published v2.12.1 predecessor `rollback` | PASS | `/root/dm-validation-2140/dm-bl-010-20261107/v2121-predecessor/rollback/` |

The v2.12.1 install reported:

```text
INSTALL_OK version=2.14.0 files=63 core_locales=10 pruned=1 backup=/var/backups/devicemonitor/install-v214.7Y78Qq daemon_restarted=0 unchanged=34 repaired=7
```

`devices.db` and `config.json` remained byte-identical. The seven `repaired` entries were
mode/ownership corrections to content-identical notification helpers, not translation or data
changes. The unchanged historical leftover was pruned, the deliberately modified one was retained,
and all target content/modes matched the candidate manifest. The rollback run restored all 63
targets, the record, database, configuration and 19 core-locale state/pristine files with zero
conflicts or failures.

A first v2.12.1 install attempt correctly stopped on an over-specific harness assertion that
required `repaired=0`; its evidence is retained at
`/root/dm-validation-2140/dm-bl-010-20261107/v2121-predecessor/install-failed-assertion/`. The
harness was corrected to validate the reported repair count against the byte-identical target set,
while retaining the zero-repair requirement for the live predecessor. The installer itself was not
changed by that correction.

## Boundaries and remaining gates

- The investigation itself made no live deployment, host contact, production access, monitoring
  change, commit, push, merge, tag, release or issue reply.
- The `.23` host remains on the accepted 2.14.0 main-integration build; the new candidate was not
  installed there.
- Published v2.12.1 and all existing tags/assets remain unchanged. 2.14.0 remains unpublished.
- Jail coverage proves installer paths with stubs, not real OPNsense plugin registration, configd,
  live `FRESH=1` or the real plugin lifecycle. These remain **DM-BL-012**.
- The historical database-byte limitation remains **DM-BL-011**; logical restoration evidence for
  the completed §9.4 exercise does not prove the original physical bytes.
- The broader monitoring lifecycle and delivery paths remain **DM-BL-013**.
- DM-BL-010 remains **OPEN** until this development-branch candidate is integrated and published
  under separate authorisation. Issue #5 remains **OPEN** pending reporter confirmation.

## Authorised commit scope

The exact source and record scope is:

```text
.github/workflows/ci.yml
PRODUCT_BACKLOG.md
PROJECT_STATE.md
install-unattended.sh
release/bundle-digest.txt
release/merge-opnsense-catalog.sh
release/release-inputs.sha256
tests/test_ci_config.py
tests/test_locale_merge.py
tests/test_upgrade_predecessors.py
verification/DM-BL-010-CATALOGUE-HEADERS-20261107.md
verification/ISSUE-5-V2.12-MANIFEST-20261106.md
verification/installer-sandbox/README.md
verification/installer-sandbox/run-installer-sandbox.sh
```

The companion milestone report records the commit, push, exact-SHA CI, PR and clean-checkout bundle
determinism evidence after those gates are completed.
