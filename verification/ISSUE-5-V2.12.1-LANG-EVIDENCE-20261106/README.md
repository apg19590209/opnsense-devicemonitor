# Issue #5 v2.12.1 Language-Catalogue Correction Evidence

This directory is the sanitised evidence subset for the authorised language-catalogue correction on
`fix/issue-5-v2.12.1`. The correction is based on repair commit
`a21373a6297edc1fcafd6a9be35e9d2c071f6129`, itself based on `main` commit `d5d73ed`.

The tested bundle is `dm-v2.12.1-runtime.tar.gz`, 1,596,559 bytes, SHA-256
`ba5737e9e2fc0d9b78edaacef82aeee30c9a8656db4f27cc9800473af71957c0`, with 56 members. The bundle
binary is not committed. Two independent builds were byte-identical and equal to the archive used
by the six jail scenarios.

The language failure was reproduced at parent `d5d73ed`, then corrected by adding only the missing
message IDs required by existing UI strings. Existing catalogue entries were not removed or
changed. Translations came from the existing integration-branch catalogues; no new wording or UI
logic was introduced.

## Validation

* Parent reproduction: failed with ten missing page strings.
* Corrected language acceptance: `LANGUAGE_ACCEPTANCE=PASS languages=9 failures=0` in the clean
  runner-equivalent path.
* Catalogue validation: all 11 PO files pass `msgfmt --check`; `LOCALE_MERGE=PASS`; translated
  JavaScript passes.
* Release checks: `V2121_RELEASE_MANIFEST=PASS rows=41 payload_hashes=41 upgrade_targets=62
  fresh_targets=63`; fresh-install defaults PASS.
* Rollback regressions: `CORE_LOCALE_ROLLBACK=PASS cases=3`; bundle reproducibility PASS with seven
  cases.
* Bundle audit: all 41 manifest payload hashes match, all tested target modes pass, members are
  canonical and contain no bytecode.
* Six jail scenarios: `check`, `upgrade`, `fresh`, `repair`, `rollback` and `fresh-rollback` all
  PASS. Both rollback paths restored their independent before/after snapshots, preserved live state
  and tore down cleanly.

## Boundaries

The jail uses stubs for `opnsense-version`, `service`, `rc.configure_plugins` and daemon state.
Passing these scenarios proves installer behaviour and service-call boundaries, not real OPNsense
configd interaction, plugin registration, daemon lifecycle or live `FRESH=1`.

The full-price gate was confirmed interactively with `y`; no bypass or gate modification was used.
No live deployment, service change, monitoring activation, production access, tag, release or
GitHub reply formed part of this validation.

`SHA256SUMS` covers every other file in this directory. The prior
`ISSUE-5-V2.12.1-EVIDENCE-20261106` set and its bundle identity remain unchanged and are
superseded. The intermediate `dbf350ff…951f0` candidate is also retained under `superseded/`
because normalising the catalogue tails changed its bundled bytes.
