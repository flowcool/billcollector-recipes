# BillCollector recipes

This public repository contains provider recipes, metadata, schemas and export
tooling. It does not contain the BillCollector engine or deployment configuration.
This project owns every provider recipe end to end, including the Bourse Direct
recipe. The engine belongs to the `BillCollector` project.

## Validation

```sh
uv venv .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
```

CI also exports the Selenium catalog with `scripts/export-recipes.sh`.
Use a disposable destination: this command replaces matching recipe files.

## Compatibility

`recipes/`, the root schemas and `scripts/export-recipes.sh` implement the Selenium contract.
For a Playwright port or export change, first read
`docs/plans/playwright-migration.md` and its linked source assessment.
`playwright/`, `schema/playwright/` and `scripts/export-playwright-recipes.sh`
implement provider ports with explicit qualification metadata. Read each provider
status and recorded blocker before use. Read `engineRevision` in the provider
metadata for the exact qualification baseline; deployment is owned by Infra.
`tests/engine_probe.py` records the historical single-document snapshot.
`tests/unattended_engine_probe.py` tests the current unattended collection paths.
Validate against the exact engine revision that will load a recipe.
Keep historical Selenium validation separate from new Playwright evidence.

## Public data boundary

Commit only public provider selectors, synthetic fixtures and sanitized evidence.
Keep credentials, private URLs, browser profiles, account documents and deployment
topology outside this repository. A real-provider qualification run needs
Florent's GO for that provider; run it in an isolated lab, never against shared
state or Paperless. Deployment belongs to Infra.

## Portal exploration

Write one throwaway script file, not quoted one-liners. Use native Playwright
actions and dismiss cookie banners first. After two failed probes, ask Florent
for a screenshot of the page instead of probing further. Throwaway scripts are
for read-only exploration only, never for a write, a deploy or a production run.

## Project boundaries (Florent 2026-10-30)

Each scope has one owner agent. Work only in the repositories and runtime of
your own project. This project: `billcollector-recipes`.

| Beads `project` | Agent | Owns |
| --- | --- | --- |
| `infra` | Claude, `~/claude_project/infra` | Production deployment (Komodo, GitOps `flowcool/mylittlemess`), image and catalog pins, schedules, collector task configuration, hosts and NAS outside the labs, Paperless configuration and permissions, SOPS secrets, backup, monitoring. |
| `BillCollector` | Codex | The engine only (`flowcool/BillCollector`): generic actions, scheduler, vault and TOTP, throttles, delivery, recipe schema, engine contract, upstream engine contributions. |
| `billcollector-recipes` | Codex | Every provider recipe end to end (`flowcool/billcollector-recipes`): portal exploration, selectors, history window, qualification on the exact engine revision, catalog release, upstream recipe contributions. |
| `ghostfolio-ibkr-sync`, `ghostfolio-degiro-sync`, `ghostfolio-boursedirect-sync` | Codex | Connector code, spec, lab tests, PRs and releases. The Ghostfolio financial operation, under Florent's GO. |

- **Routing.** For a need in another scope, search the open issues of the owner
  first. If no issue covers it, create one with
  `--metadata '{"project":"<owner>"}'`, the evidence, the exact need and its
  acceptance. Link it `related` to your issue. Never edit, deploy or test the
  code or runtime of another project.
- **Usual routes.** Portal, selector or history window: `billcollector-recipes`.
  Missing engine action, throttle, vault or delivery defect: `BillCollector`.
  Deployment, pin, schedule, task configuration, Komodo stack, NAS file,
  Paperless workflow or permission: `infra`. Importer behavior: the connector.
- **Release boundary.** A development project stops at a qualified release: an
  immutable image digest or catalog tag, with its proof. Infra deploys it.
- **Labs: free use on agentvm.** Create, configure, reset, restart, redeploy and
  scratch lab stacks under `stacks/a/` (Komodo server `a`). To add your own
  lab, open a `flowcool/mylittlemess` PR limited to `stacks/a/<lab>/` and its
  `komodo/sync.toml` entry; merge it on green CI. Separate authority remains for
  production, a login to a real broker or portal (Florent GO per provider),
  production secrets in a lab, and removal of proof. Reserve a shared lab and
  stop it after use (Infra runbook `docs/runbooks/ghostfolio-lab.md`).
- **Lab gate before merge.** Test the PR image in the lab before merge when the
  PR changes financial logic, deduplication or activity identity, Ghostfolio
  authentication, transport or writes, the state or journal format, a recipe,
  or a major dependency or base image. Connectors run the empty and golden
  Ghostfolio labs. Recipes and the engine run an isolated collector lab with
  synthetic fixtures. Other PRs need CI only.
- **Lab gate at release.** Every release passes the same lab scenarios on its
  exact digest. Promote that digest without a rebuild. Reuse the pre-merge proof
  when the digest is identical.

## Durable work

Beads project: `billcollector-recipes`. Catalog epic: `infra-spee`.
Infrastructure cutover owner: `infra-1lr1` (project `infra`).
Shared engine contracts remain under `infra-zlth` (project `BillCollector`).
Read Beads for progress and authorization; Markdown records design and evidence.

Unattended recipe qualification (closed): `infra-u4hbm`.
Incremental collection delivery: `infra-25goi`. Bourse Direct 13-month history
window: `infra-5iqmw`. Both moved to this project on 2026-10-30.
