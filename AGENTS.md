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

## Recipe intake and done (Florent 2026-10-30)

Never implement a recipe from an unscoped idea. Scope it first.

1. **Request.** Florent names the provider and the need in one sentence.
2. **Read-only exploration.** One Florent GO per provider covers exploration,
   qualification and the first production run. Inventory what the portal
   offers: document families (invoices, statements, notices, tax documents and
   others), history depth per family, a stable key per family, and portal
   limits (throttle, 2FA, pagination, date windows).
3. **Intake card.** Split it in two parts.
   - Public, in `metadata.yaml` under `scope:`: the families the portal
     offers, history depth, keys, limits, and per family `implemented` or
     `documented` with the reason.
   - Private, in the owning issue: accounts and contracts, Florent's choices,
     and the Paperless mapping need for Infra. Never commit account data.
4. **One question to Florent:** the proposed scope. The default implements the
   needed families plus every family with a low marginal cost (same page, same
   pattern). Other families stay `documented`: offered, not implemented, with
   the way to add them. Do not implement before the answer.
5. **Implementation rule.** Read the complete offered list with a stable key and
   `incremental: true`. The engine skips known keys over the whole list, so the
   first run collects the full history and later runs collect only new or late
   documents. When the portal forces a date window or a page limit, declare
   that bound in `scope:` and tell Infra: such a recipe needs a periodic
   control run.
6. **Done.** Qualification in an isolated lab on the exact engine revision:
   first run equals the retained inventory, second run collects 0. Record the
   counts in `validation:`. Each family not covered is a written limit, never an
   omission. A missing engine capability is an issue for `BillCollector`.

Apply this rule to every new recipe and to Bourse Direct now. Apply it to an
existing qualified recipe at its next change.


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
