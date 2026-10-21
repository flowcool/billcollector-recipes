# BillCollector recipes

This public repository contains provider recipes, metadata, schemas and export
tooling. It does not contain the BillCollector engine or deployment configuration.

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
implement experimental supervised single-document ports. Metadata records limits.
`tests/engine_probe.py` runs synthetic proof from an exact archived engine revision.
Validate against the exact engine revision that will load a recipe.
Keep historical Selenium validation separate from new Playwright evidence.

## Public data boundary

Commit only public provider selectors, synthetic fixtures and sanitized evidence.
Keep credentials, private URLs, browser profiles, account documents and deployment
topology outside this repository. Real-provider runs and deployment belong to the
infrastructure operation workflow, with separate authorization.

## Durable work

Beads project: `billcollector-recipes`. Catalog epic: `infra-spee`.
Infrastructure cutover owner: `infra-1lr1` (project `infra`).
Shared engine contracts remain under `infra-zlth` (project `BillCollector`).
Read Beads for progress and authorization; Markdown records design and evidence.
