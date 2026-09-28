# Product backlog

> **Stub file.** Authored 2026-09-28 by the locale-verification workstream. It contains
> **only** the items referenced by `verification/locales/REPORT-it_IT-2026-09-28.md`, plus
> `O2` added the same day from the Dutch language-selection investigation
> (`verification/locales/deferrals.md` → *Upstream Environment Warnings*). It is **not** a
> complete backlog: no existing backlog file was found in this tree, and no source material
> for other items was available. Migrate the real items in from the tracking system, or
> replace this file wholesale.

Status legend: `OPEN`, `DEFERRED`, `PENDING-EVIDENCE`, `RESOLVED`, `WONTFIX`, `CLOSED`.

`CLOSED` means the item is no longer tracked. Its `Resolution:` line states whether it was
fixed or dropped; a dropped item carries its reason there.

## DM-BL-008b

- Status: **`PENDING-EVIDENCE`** — *not* resolved
- Epic: DM-BL-008
- Reported: 2026-09-28 — operator-reported Italian (`it_IT`) text-stream pass against
  `192.168.20.23`, with both reported check strings passing
  (`[Riepilogo modifiche]`, `[Monitoraggio dispositivi]`) and a reported teardown
  restoring the OPNsense layout parameter to `en_US`.
- Acceptance criteria: not present in this repository.
- Why this is not `RESOLVED`: the report is an operator attestation with no attached
  artifacts. Missing: raw harness/tool output, result JSON/HTML, stream timeline,
  screenshot or page source, tool name and version, run timestamp, OPNsense build, and
  pre/post locale state for the reported `en_US` restore. Full list in
  `verification/locales/REPORT-it_IT-2026-09-28.md` → *Evidence gap*.
- Closes when: those artifacts are attached and the acceptance criteria are checked
  against them.

## DM-BL-008c

- Status: **`DEFERRED`** — unchanged
- Recorded as deferred in the French text-stream verification commit. The Italian pass
  does not cover this item and supplied no closure evidence, so the deferral stands.
- See `verification/locales/deferrals.md`.

## F1

- Status: **`DEFERRED`** — unchanged
- Description unknown to this repository; the identifier appears in the French
  verification commit message and in `verification/locales/REPORT-fr_FR-2026-09-28.md`,
  with no in-tree definition. Supply the tracking-system description, owner, and revisit
  trigger to make this entry actionable.

## O2

- Status: **`CLOSED`** — dropped, not fixed
- Title: Dutch (`nl_NL`) missing from the web GUI language selection
- Resolution: **Dropped: Upstream limitation / Non-native core locale**
- Closed: 2026-09-28
- Why it was raised: System → General → *Language* offers no Dutch option, and a Dutch
  catalog appeared to exist at the core locale path.
- Why it was dropped: the omission is upstream, not local. `get_locale_list()`
  (`/usr/local/etc/inc/system.inc:255-287`) defines 20 locales and contains no `nl_NL` key
  and no `'Dutch'` string — nothing is commented out. The on-disk file is byte-identical to
  upstream `opnsense/core` master and `stable/26.7` (sha256
  `3347f8761fd70498d0a4cb32b7b06b4eeda6647a076853eaf5a9ede0d972041f`; `pkg check -s
  opnsense` clean), and `src/etc/inc/system.inc` has no `nl_NL` entry in any branch checked
  (`stable/20.7` → master). `opnsense-lang-26.1.7` ships no `nl_NL` catalog
  (`pkg info -l … | grep -c nl_NL` = `0`). There is therefore no missing menu entry to
  restore and no shipped translation to attach it to.
- Artifact removed: `/usr/local/share/locale/nl_NL/LC_MESSAGES/OPNsense.mo` was an unowned
  copy of the Device Monitor plugin catalog (sha256
  `8bb2a6c7947ecef25f11dbc5648673c050a08f1726a53008264ab276835e1579`, md5
  `1a7651bce06f77744d5ef43b2d8cc4f8`, identical to
  `mvc/app/languages/nl_NL_devicemonitor.mo`, 452 msgids, `Project-Id-Version:
  Device Monitor 2.10`). Because the `OPNsense` domain is bound to `/usr/local/share/locale`
  without a catalog-existence check (`/usr/local/www/authgui.inc:39-68`, MVC
  `ControllerRoot.php:88-98`), that file would have produced a silent English fallback for a
  `system.language` of `nl_NL`. It was deleted on 2026-09-28; the now-empty
  `nl_NL/LC_MESSAGES/` directory went with it. A copy is kept outside the locale tree at
  `/root/opnsense-quarantine-20260928/` for the record.
- Re-open only if: upstream adds `nl_NL` to `get_locale_list()` (then re-verify that a
  genuine core catalog exists), or a Dutch GUI is commissioned as a non-upstream change.
- Cross-reference: `verification/locales/deferrals.md` → *Upstream Environment Warnings*
  (the nine pkg-owned catalog checksum mismatches found during the same investigation).
