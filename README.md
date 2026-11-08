# BillCollector Recipes

Public provider recipes for [flowcool/BillCollector](https://github.com/flowcool/BillCollector).
This repository owns recipes, qualification metadata, schemas and catalog export.
The engine belongs to BillCollector. Infra owns deployment, task configuration,
provider activation and Paperless integration.

## Catalog status

| Provider | Recorded coverage | Real-provider qualification |
| --- | --- | --- |
| Free | All offered invoices across available years | 19 new, then 0 |
| Fulli | All offered invoices, including hidden history rows | 14 new, then 0 |
| Mint Energie | Original PDF from the monthly contract ZIP | 1 new, then 0; multiple PDFs per month fail closed |
| CC Genevois | All offered invoices by invoice number | 5 new, then 0 |
| Octopus Energy | Invoice preparation only | Experimental: account has no issued invoices |
| Bourse Direct | Operation notices up to 13 months; all offered monthly account statements | Experimental: changed recipe has synthetic proof only |

Read `playwright/<provider>/metadata.yaml` before use. Free, Mint Energie and
CC Genevois retain qualification baseline `45e530b7d6240abb308810183dbe4f65aae5b6dc`.
Fulli was requalified on 2026-11-01 against
`4d2a893be89a83c47b940c174bad3fa75bbf2ade`. Its available set decreased from
15 to 14 periods; only April 2025 disappeared. See the
[Fulli navigation regression](docs/fulli-login-navigation.md).
Octopus payment schedules do not qualify as invoices.
Bourse Direct's old PEA proof covers October 2026 only; PEA-PME is simulated.
See [Bourse Direct scope and bounds](docs/bourse-direct.md).

The Selenium catalog, root Selenium schemas and Selenium exporter are retired.
Use Git history or the `v0.9.0` tag for the previous catalog layout. Removing
these public paths is an incompatible catalog contract change. It does not
remove deployed files, convert historical state or stop a runtime.

## Validate and export

```sh
uv venv .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
PYTHON=.venv/bin/python ./scripts/export-playwright-recipes.sh . ./export/playwright \
  --engine-revision 3be39481c93f41fbc3e4e109b52cd738ce0595b1
```

Export contains six runtime recipes, their schema and an ownership manifest.
It excludes catalog metadata. Schema SHA256:
`cebc9c7c6fb09f5d171f322a0cce92dd33a66d519478437c02559b16ef222b07`.
The exporter rejects mixed, unmanaged or symlink destinations and restores the
previous set after a caught write failure. Prepare releases in a disposable
directory. Infra installs the export under its operation plan.

Synthetic probes use isolated state and loopback fixtures. Run each probe in
the matching engine's Python/browser environment. The Bourse Direct probe
requires an engine checkout at the exact catalog pin:

```sh
/path/to/engine/apps/.venv/bin/python tests/bourse_direct_engine_probe.py /path/to/engine
```

`tests/unattended_engine_probe.py` covers the five invoice providers.
`tests/engine_probe.py` and the source assessments in `docs/research/` retain
historical snapshot evidence. See the [qualification plan](docs/plans/playwright-migration.md)
for evidence boundaries. A synthetic pass does not qualify a real account.

## Contribute

Follow [AGENTS.md](AGENTS.md) for provider intake, public data boundaries and
qualification. A provider change needs an explicit scope, stable source keys,
complete offered-list collection or declared bounds, and isolated first/repeat
proof. Bounded recipes need an Infra control run. Publish only public selectors,
synthetic fixtures and sanitized aggregate evidence. Keep credentials, account
identifiers, authenticated URLs and downloaded documents outside Git.

Use the [PR template](.github/pull_request_template.md). Pullfrog is the sole
reviewer. Markdown-only PRs need lightweight CI; code, YAML and workflows run
full validation and security checks. See [.github/README.md](.github/README.md).

## Releases and recovery

Pin a catalog tag and the exact compatible engine image. Patch releases fix
selectors or documentation. Minor releases add compatible recipes or metadata.
Major releases change public layout or contracts incompatibly. Provider status
remains explicit: a major catalog version does not qualify experimental recipes.
Each release needs schema/export checks and the applicable isolated lab proof.
Reuse an existing exact-image proof only when its runtime inputs are identical.

Infra keeps task service/user identities, DB, profiles, journal and original-byte
archive intact. Selenium history does not populate Playwright state. Deployment,
legacy-data reconciliation and rollback belong to Infra. Source recovery uses the
previous catalog tag or a revert; it never resets deduplication.

Recipes and documentation use the [repository license](LICENSE).
