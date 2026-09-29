# Project state

> **Stub file.** Authored 2026-09-28 by the locale-verification workstream. No project
> state file was found in this tree, so this file records **only** the locale
> verification tracks and the `DM-BL-008` items they touch. It is not a full project
> snapshot. Replace or merge it with the authoritative source.

## Repository state

- `verification/locales/` is new in this record set.
- **Added 2026-09-29:** `verification/locales/verify_locale_stream.py` (harness, version
  0.1.0), `verification/locales/tests/test_verify_locale_stream.py` (offline self-test, 13
  cases), `verification/locales/locale_cases/it_IT.json` (draft-unratified, all run fields
  `null`). No run artifact exists for any locale.
- **Corrected 2026-09-28 — the earlier entry read "No git repository was present in the
  tree at the time of writing, so nothing here has been committed".** That is stale: a git
  repository is present at the tree root (`/usr/local/cline-freebsd/src/cline`, branch
  `master`, initialised 2026-09-28) and this record set is committed there — `a8420d1`
  (`it_IT`), `17460a4` (`fr_FR`), `abb159e` (root `.gitignore`), `2ce962d`
  (`.clinerules/general.md`), plus the commit that adds the `fr_FR` case file.
- **Corrected 2026-09-28 (second revision) — `origin` is active.** The remote
  `https://github.com/apg19590209/opnsense-devicemonitor` is registered in this repository
  and both fetch and push work from this host (verified: `git ls-remote`, `git fetch`, and
  one completed `git push` whose branch was then deliberately deleted — see *Open
  blockers* item 3). The earlier sentence, "No remote is configured, so commits are local
  and cannot be pushed from this host", was accurate when written and is corrected here.
- The `verification/locales/` harness (`verify_locale_stream.py`) **is written as of
  2026-09-29 and committed with an offline self-test** (`tests/test_verify_locale_stream.py`).
  It is **still not runnable on the recording host**: no Selenium, no `pip`, no browser or
  WebDriver binary. The earlier sentence in this file — "remains a proposal: not written to
  disk" — was accurate when written and is corrected here. Being written is not being run:
  no locale has been through this harness, and `DM-BL-008b` stays `PENDING-EVIDENCE`.

## Locale verification tracks

| Locale | Target | Status | Record |
| --- | --- | --- | --- |
| `fr_FR` | `192.168.20.23` (OPNsense UI — operator-attested, not in the supplied log) | `OPERATOR-REPORTED` | `verification/locales/REPORT-fr_FR-2026-09-28.md` |
| `it_IT` | `192.168.20.23` (OPNsense UI) | `OPERATOR-REPORTED` | `verification/locales/REPORT-it_IT-2026-09-28.md` |

## DM-BL-008 epic

- **`DM-BL-008b`: `PENDING-EVIDENCE`** — not resolved. The 2026-09-28 Italian pass was
  reported by an operator with both check strings passing
  (`[Riepilogo modifiche]`, `[Monitoraggio dispositivi]`) and a reported teardown
  restoring the OPNsense layout parameter to `en_US`, but no artifacts were supplied.
  Closure requires the evidence checklist in `REPORT-it_IT-2026-09-28.md`.
- **`DM-BL-008c`: `DEFERRED`** — unchanged. Not covered by the Italian pass.
- **`F1`: `DEFERRED`** — unchanged. No in-tree description available.

## Closed items

- **`O2` — Dutch (`nl_NL`) language selection: `CLOSED`** (2026-09-28, dropped).
  Resolution: **Dropped: Upstream limitation / Non-native core locale**. `get_locale_list()`
  (`/usr/local/etc/inc/system.inc:255-287`) defines 20 locales and offers no `nl_NL` key and
  no `'Dutch'` string; nothing is commented out, and the file is byte-identical to upstream
  master and `stable/26.7` (sha256 `3347f876…`), whose `src/etc/inc/system.inc` carries no
  `nl_NL` entry in any branch checked (`stable/20.7` → master). `opnsense-lang-26.1.7` ships
  no Dutch catalog, so there is no menu entry to restore and no shipped translation to
  attach it to. The mislabelled `/usr/local/share/locale/nl_NL/LC_MESSAGES/OPNsense.mo` — a
  copy of the Device Monitor plugin catalog, not a core catalog — was removed on 2026-09-28
  so nothing can resolve a silent English fallback through it. No menu or locale
  requirement remains open.
  Backlog: `PRODUCT_BACKLOG.md` → `O2`. Evidence: `verification/locales/deferrals.md` →
  *Upstream Environment Warnings*.

## Open blockers

1. No evidence artifacts for the reported `it_IT` pass (blocking `DM-BL-008b`).
2. No confirmation of the OPNsense locale restore beyond operator attestation
   (infrastructure state, not a documentation fact).
3. **No push to `main` is possible yet, and this is unresolved.** `origin` is configured
   and pushes work, but the local history is **unrelated** to the remote:
   `git merge-base HEAD origin/main` finds no common ancestor — 292 commits on `origin/main`
   against a 6-commit record set here (7 locally once this correction is included). Three
   paths collide:
   - `PROJECT_STATE.md` — 4,161 bytes here (this stub) against 101,496 bytes / 1,896 lines
     of authoritative project state on `origin/main`.
   - `PRODUCT_BACKLOG.md` — 4,619 bytes here against 657 bytes on `origin/main`.
   - `.gitignore` — 2,209 bytes here against 49 bytes on `origin/main`.

   A trial rebase onto `origin/main` conflicted at commit 1 of 6 (`add/add` on
   `PROJECT_STATE.md` and `PRODUCT_BACKLOG.md`). Resolving in favour of this record set
   would replace the authoritative file by a net `71 insertions(+), 1896 deletions(-)`, so
   the alignment needs an explicit decision; a rebase by itself is **not**
   non-destructive. (Replaces the earlier stale claims that no git repository, and later
   that no remote, existed — see *Repository state*.)
4. Harness **implemented** as of 2026-09-29 and self-tested offline; its host prerequisites
   are still unmet (no Selenium, no `pip`, no browser, no WebDriver binary), `target.base_url`
   and `target.route` are `null` in every case file, and no locale has been run. Nothing about
   this blocker is closed by the harness existing.

## Next actions

- Obtain the artifacts listed in `verification/locales/REPORT-it_IT-2026-09-28.md`.
- Decide whether the locale harness should target a browser UI at all, given that the
  `apps/cli` application in this repository is a terminal TUI.
- Resolve *Open blockers* item 3 before any push to `main`: decide whether this record set
  is merged into the authoritative `origin/main:PROJECT_STATE.md` and `PRODUCT_BACKLOG.md`
  or discarded. `origin` is already configured and local commits already work, so the
  "initialise the repository" and "configure a remote" steps are done and must not be
  repeated here.
