# Device Monitor 2.14.0 — main integration record (7 November 2026)

## Result

The reviewed 2.14.0 integration was fast-forwarded into `main` without rewriting any
commit, and exact-main CI passed. DM-BL-009's reconciliation criterion is met and
the item is closed. The residual validation limitations are tracked separately as
DM-BL-011, DM-BL-012 and DM-BL-013.

This is a source integration record, not a release. The latest published GitHub release
remains v2.12.1. There is no v2.14.0 tag, GitHub release or release asset.

## Pre-mutation guards

| Check | Result |
|---|---|
| Canonical workspace | `/root/src/opnsense-devicemonitor-upstream` |
| Working tree | clean |
| Previous `main` | `d5d73edffc0200cf8c84a63689e1937f92002435` |
| Approved PR head | `282517744260920b18c9217efd09ce738af21d70` |
| Integration branch remote | `282517744260920b18c9217efd09ce738af21d70` |
| PR #6 | OPEN and draft, base `main`, exact approved head |
| Reviewed tree | `73750b8e1247f21a8b5dd2c888e5ece64bbfe8af` |
| Ancestry | previous `main` was an ancestor of the approved head |

Any mismatch was required to stop the operation without adapting the target. All
guards passed before mutation.

## Merge

```text
Updating d5d73ed..2825177
Fast-forward
   d5d73ed..2825177  main -> main
```

- Method: `git merge --ff-only` followed by `git push --no-force origin main:main`.
- No squash, rebase, force-push or cherry-pick.
- All 54 integration commits were preserved.
- PR #6 is merged with reported merge commit
  `282517744260920b18c9217efd09ce738af21d70`.

## Remote verification

| Item | Value |
|---|---|
| Remote `refs/heads/main` | `282517744260920b18c9217efd09ce738af21d70` |
| Remote `main` tree | `73750b8e1247f21a8b5dd2c888e5ece64bbfe8af` |
| Local `main` after push | `282517744260920b18c9217efd09ce738af21d70` |
| Working tree after push | clean |

## Exact-main CI

- URL: https://github.com/apg19590209/opnsense-devicemonitor/actions/runs/42342362864
- Run ID: `42342362864`
- Event: `workflow_dispatch`
- Branch: `main`
- Head SHA: `282517744260920b18c9217efd09ce738af21d70`
- Result: completed / `success`
- Required log evidence:

```text
RELEASE_INPUTS=PASS cases=7
V2140_RELEASE_MANIFEST=PASS
bundle identity: 5149bfd41e5842a144a9d1280c008511f20f3783932eca9beb1f48fca6173f5f (1725593 bytes)
```

- Bundle size: `1,725,593` bytes.
- Bundle SHA-256:
  `5149bfd41e5842a144a9d1280c008511f20f3783932eca9beb1f48fca6173f5f`.

The workflow's explicit push-branch list and pull-request base filter do not include
`main`; the workflow was therefore dispatched explicitly against `main` after the
fast-forward.

## Acceptance review

DM-BL-009's explicit closure criterion was execution of the chosen `main` path.
That criterion is met by the fast-forward, remote identity check and successful
exact-main CI above. The item is therefore **CLOSED**.

Closure does not assert 2.14.0 publication or complete real-host monitoring
acceptance. The remaining limitations are intentionally separate:

- **DM-BL-011** — historical database-byte identity for the completed §9.4
  exercise. Logical restoration is verified, but the original `c17874a7…` bytes
  were not retained and the later physical representation was `796d28c7…`.
  Exact byte-level attribution remains unproven.
- **DM-BL-012** — real-host `FRESH=1`, OPNsense plugin registration/lifecycle and
  real configd interaction. The isolated fresh/fresh-rollback jail scenarios pass,
  but their `rc.configure_plugins` and `pgrep` stubs prove only the call boundary.
- **DM-BL-013** — full reminder/ageing/CARP, daemon-generated notification and
  service-discovery, and external delivery paths. The bounded two-cycle exercise
  observed direct discovery and direct PHP-helper SMTP, not those full paths.

The `operator-note.txt` assertion delta is non-blocking and test-only. The
integration implementation operates only on `*.state` and `*.OPNsense.mo`; a
disposable check preserved an unrelated file's bytes, mode, uid and gid.

## Version guidance

- `main` source: Device Monitor **2.14.0**.
- Latest published GitHub release: **v2.12.1**.
- 2.14.0 release: **not yet published**; no tag or release asset exists.

GitHub issue #5 remains **OPEN** pending reporter confirmation. No host was
contacted, no deployment or live test was performed, and no tag or release was
created or changed.
