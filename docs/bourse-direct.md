# Bourse Direct adapter contract and compatibility proof

This document records the offline assessment for `infra-zlth.52` on 2026-11-01.
The public engine revision is
`4a9bffc46015b1c6e36d0bf16b0de2b8634265cb`.
The [maintainer agreement](https://github.com/s-t-e-f-a-n/BillCollector/issues/51#issuecomment-6560326064)
sets the contribution boundary. Beads owns current work status.

## Accepted candidate contract

| Boundary | Required behavior |
| --- | --- |
| Task | One configured account per task. Full and incremental actions share the task and history. No invocation overrides. |
| Login | Use the shipped vault, optional fresh TOTP and protected native login. Prove the final session. Do not add another login or variable engine. |
| Dates | Use the fixed run-start date context. Read every complete month that intersects its inclusive window. |
| Source identity | Prove the offered account and month before acquisition. Keep PEA and PEA-PME distinct. Stop on absent, ambiguous or changed identity. |
| Traversal | Bound months, total offered items and elapsed time. Follow offered controls. An explicit empty marker proves an empty month. Missing evidence does not. |
| Originals | Follow calendar -> notice HTML -> unique offered `Format PDF` link. Check account, type and date. Read unchanged bytes through the authenticated request context. |
| Repeats and corrections | Fetch the original before applying the shipped notice-revision rule. Use `nc`, `type`, `year`, `month`, `day` as source identity fields. A daily source key cannot suppress corrections. |
| Delivery | Keep the shipped at-least-once `task_id:sha256` contract. No fork-only strict state, archive receipts or new C4/C8 semantics. |
| Validation | Pass the shipped C3 gates at load, save and run start. Validate adapter page calls against the installed Playwright surface. |

Synthetic acceptance must cover stored session reuse, password and optional TOTP,
final session proof, account drift, year boundaries, first-month retention,
explicit empty listings, invalid listings, each traversal bound, several original
PDF reads, unchanged bytes, regenerated repeats and material corrections.
The engine owns empty/partial Run results. The adapter must not invent success
for an empty listing.

## Exact engine gap

The retained recipe at engine commit `3110157` calls `locator` followed by
`bourse_direct`. The exact credential-free YAML is retained as a **negative test
fixture**, not as an exported provider recipe:
[`historical-recipe.yaml`](../tests/fixtures/bourse_direct/historical-recipe.yaml).
Its SHA-256 is
`41fd1785adecce5427a41025f73f01f4e5f434cd716b7f240adcb8cae10804ff`.

At the public revision above, C3 reports:

```text
invalid method contract: service BourseDirect, step 2, method bourse_direct: unknown public Playwright attribute
```

The error occurs at validation, load, save and run start. A rejected save keeps
the previous file. Run start returns 1 before display, vault or browser access.
The fifteen shipped recipes and the documented native login candidate validate
in the same environment with `playwright==1.63.0`.

The source confirms the missing integration boundary:

- `apps/billcollector/methods.py::validate_method_recipe` accepts reserved
  engine methods and the installed public Playwright API. It has no adapter
  registration interface. `bourse_direct` is neither.
- `apps/billcollector/runner.py::_process_step` dispatches ordinary methods on
  Playwright objects. `_collection_actions` supplies only `click_until_absent`,
  `download_all` and `replacement_calendar`. It has no provider-adapter hook.
- `apps/billcollector/calendar.py::collect_calendar` expects DOM selectors for
  account/year/month/readiness and uses the browser-download-event contract.
  It does not expose the retained notice-HTML -> authenticated-request-PDF
  acquisition chain as an adapter callback.

Native phased login, date variables and notice revisions already exist. They
are not the missing engine capability. An adapter Python file in the catalog
alone cannot make this YAML load or execute. Disabling C3, monkey-patching
Playwright or hiding a collector in recipe JavaScript would bypass the agreed
surface. This contribution does none of these.

Route the missing validated adapter execution boundary to the BillCollector
engine owner before changing that interface. The engine owner must determine
the supported integration shape under issue #51. Catalog implementation can
then use that shipped boundary and repeat the exact-revision proof. There is
no runnable public-engine Bourse Direct adapter in this assessment.
The self-contained engine handoff is `infra-zlth.84`.

## Reproduce the offline gate proof

Use a local engine Git repository that contains the pinned public revision.
The probe archives that exact commit. It does not modify the repository.
Install its `apps/requirements.txt` in an isolated environment first.

```sh
<isolated-python> tests/bourse_direct_gate_probe.py /path/to/BillCollector/git
```

The probe uses disposable SQLite, profiles, downloads and runtime paths.
It removes inherited `BC_*`, `BW_*`, `BEADS_*` and Python import overrides.
It denies socket connections and asserts zero display/vault/browser calls.
It requires Playwright 1.63.0. Exit 0 means **the documented incompatibility
was reproduced**, not that provider acquisition passed.

The exact engine's `tests/test_bc_method_validation.py` supplies the relevant
C3 regression. Run the catalog suite with the repository's standard unittest
command. No typechecker is configured in this catalog.

Recorded results on 2026-11-01:

- `tmp/venv/bin/python tests/bourse_direct_gate_probe.py
  /home/flow/claude_project/BillCollector/upstream`: exit 0; the incompatibility
  reproduced at all four gates; fifteen shipped recipes and native login passed.
- From the disposable engine archive,
  `PLAYWRIGHT_BROWSERS_PATH=/data/cache/flow/ms-playwright
  BC_BROWSER_DIR=/data/cache/flow/ms-playwright ../venv/bin/python -m pytest
  tests/test_bc_method_validation.py -q`: 57 passed. One pytest warning reports
  the unused `asyncio_mode` option because this focused environment does not
  install pytest-asyncio. The first run lacked the browser at the archive's
  default path; the rerun used the existing matching Chromium cache.
- From the recipes worktree,
  `/home/flow/claude_project/billcollector-recipes/.venv/bin/python -m unittest
  discover -s tests -v`: 11 passed.

## Historical evidence and limits

The source inventory is `BillCollector/docs/bourse-direct-preparation.yaml`
in the sibling workspace. It links the retained source at
`4c41ac772eb35f35c4fe7bef6c09b35cfa8e4c84` and local recipe `3110157`.
The historical PEA qualification downloaded five originals on its first pass.
Its second pass reported five duplicates and no new original. The separate
63-PDF retained corpus is historical evidence. Neither proves current portal
behavior or compatibility with this public engine revision.

Private originals, accounts, sessions and credentials stay outside this
repository. No portal, vault, archive or financial action is part of this proof.
Production activation and Paperless belong to `infra-1lr1`. Archive interfaces
remain separate from this local deliverable.

Recovery is a focused revert of this assessment commit. It changes no engine,
exported catalog entry, retained evidence or live state.
