# BillCollector Recipes

Community recipes for
[flowcool/BillCollector](https://github.com/flowcool/BillCollector), a
maintained fork of
[s-t-e-f-a-n/BillCollector](https://github.com/s-t-e-f-a-n/BillCollector).

Recipes describe how BillCollector navigates a provider portal and downloads
documents. They contain selectors and actions, never credentials or customer
data.

The Selenium catalog remains available. A separate experimental Playwright
catalog provides supervised navigation and one tracked document per provider.
See the [migration plan](docs/plans/playwright-migration.md) and the
[engine source assessment](docs/research/upstream-playwright-contract.md).
The validation dates below apply only to Selenium.

> [!WARNING]
> This repository is beta. Provider portals can change without notice. Pin a
> release, test updates manually, and keep the previous release for rollback.

## Experimental Playwright ports

| Service | Coverage | Limit |
|---|---|---|
| `octopus_energy` | One payment schedule | No issued invoices; select the intended agreement. |
| `free` | First listed invoice | No collection loop or latest-order guarantee. |
| `mint_energie` | First listed PDF | Public login only; requires a browser download event. |
| `cc_genevois` | First listed download control | No collection loop or popup support. |
| `fulli` | First listed invoice | Initial list only; no load-more or pagination. |

All five ports require operator login, consent and account selection through
`wait_user`. They do not submit credentials. Real-provider validation has not run.
See each `playwright/<service>/metadata.yaml` for exact limits.

Export to a fresh release directory with the exact selected engine revision:

```bash
uv pip install --python .venv/bin/python -r requirements-dev.txt
PYTHON=.venv/bin/python ./scripts/export-playwright-recipes.sh . ./export/playwright \
  --engine-revision 501898cade0b9981092db2011fb3fc02812af8b3
```

The export includes the runtime schema and five recipes. It excludes catalog
metadata. It refuses mixed or unmanaged recipe directories. Use it only for
release preparation. Import and real runs require the infrastructure operation
plan. Do not point it at a live daemon recipe directory.
Keep the task identity stable. Selenium history does not populate SQLite.
The file-publication/SQLite interruption window is not safe for Paperless cutover.

Run isolated engine proof with an existing Git repository containing the pinned
engine revision. The launcher archives it into a temporary directory. It uses
synthetic browser routes and separate database, output and profile paths.

```bash
uv pip install --python .venv/bin/python -r requirements-engine-tests.txt
.venv/bin/python -m playwright install chromium
.venv/bin/python tests/engine_probe.py /path/to/BillCollector
```

This exercises actual daemon dispatch and download tracking with headless
Chromium. The launcher and operator resume are test adapters. It does not prove
headful display allocation, vault lookup or real login behavior. Playwright
1.58.0 is the test client, not evidence for the deployed image dependency set.

## Available Selenium recipes

| Provider | Service | Status | Authentication | Last real validation |
|---|---|---|---|---|
| Freebox Internet | `free` | Beta | Username/password, no MFA observed | 2026-07-27 |
| Fulli Toll | `fulli` | Beta | Username/password, no MFA observed | 2026-09-27 |
| Mint Energie | `mint_energie` | Beta | Username/password, no MFA observed | 2026-09-27 |
| Octopus Energy France | `octopus_energy` | Beta | Username/password, no MFA observed | 2026-09-27 |
| CC Genevois Water | `cc_genevois` | Beta | Username/password, no MFA observed | 2026-09-27 |

The Free recipe downloaded 19 historical invoices during its initial
end-to-end validation. That result does not guarantee that Free's portal is
unchanged today.

The Fulli recipe completed an isolated end-to-end validation against the real
account: 14 PDF invoices were published on the first run, and the second run
published no new files while skipping all 14 known documents. This validation
does not deploy or schedule the recipe.

The Mint Energie recipe completed an isolated end-to-end validation against
the real account: one PDF invoice was published on the first run, and the
second run skipped the known document and published nothing new.

The Octopus Energy recipe completed an isolated end-to-end validation: the
first run published one PDF payment schedule, and the second run recognized
the same document and published nothing new.

## Installation

### Recommended: pin a release with Git

Choose a release from GitHub, then clone that exact tag:

```bash
git clone --depth 1 --branch v0.1.0 \
  https://github.com/flowcool/billcollector-recipes.git
```

Copy the deployable recipes into your deployment directory:

```bash
./billcollector-recipes/scripts/export-recipes.sh \
  ./billcollector-recipes \
  ./recipes
```

The export is explicit: updating this Git checkout does not silently replace
the recipes used in production.

Mount the resulting directory read-only:

```yaml
services:
  billcollector:
    volumes:
      - ./recipes:/config/recipes:ro
      - ./config/billcollector.ini:/config/billcollector.ini:ro
      - ./downloads:/apps/Downloads
    entrypoint: ["/bin/bash", "-euc"]
    command:
      - |
        cp /config/recipes/bc-*.yaml /apps/bc-recipes/
        exec python3 ./BillCollector.py /config/billcollector.ini
```

### Updating

Inspect and fetch the desired tag:

```bash
git -C billcollector-recipes fetch --tags
git -C billcollector-recipes checkout v0.1.1
./billcollector-recipes/scripts/export-recipes.sh \
  ./billcollector-recipes \
  ./recipes
```

Then run BillCollector manually and inspect the result. Do not follow `main`
automatically in production.

Rollback is the reverse operation:

```bash
git -C billcollector-recipes checkout v0.1.0
./billcollector-recipes/scripts/export-recipes.sh \
  ./billcollector-recipes \
  ./recipes
```

### Update policies

| Policy | Result | Recommended use |
|---|---|---|
| Fixed tag | No change until explicitly selected | Production |
| Compatible patch series | Update proposal for `v1.1.x` | Future automation |
| `main` | Every repository change | Development only |

Renovate or Dependabot can eventually propose tagged updates. Automatic
deployment of a moving branch is intentionally unsupported.

## Configure a provider

For the Free recipe, create a Bitwarden login item:

```text
Name: Free Home
Username: your Freebox identifier
Password: your Freebox password
URI: https://subscribe.free.fr/login/
```

Then add this line to `billcollector.ini`:

```ini
Free [Home]
```

BillCollector derives:

- recipe filename: `bc-recipe__free.yaml`;
- exact Bitwarden item name: `Free Home`.

For Fulli, use the stable customer portal URL in the Bitwarden item:

```text
Name: Fulli Toll
Username: your Fulli email address or customer number
Password: your Fulli password
URI: https://www.fulli.com/customer/login
```

Then select the beta recipe with:

```ini
Fulli [Toll]
```

The Fulli login page may present a FriendlyCaptcha challenge. BillCollector
does not bypass it; authenticated validation must stop if human interaction is
required.

For Mint Energie, name the Bitwarden item exactly `Mint Energie`. Keep the
account-specific activation or creation URL only in Bitwarden; do not commit it
to the recipe repository.

```text
Name: Mint Energie
Username: your Mint Energie email address
Password: your Mint Energie password
URI: your account-specific Mint Energie URL
```

Then add this line to `billcollector.ini`:

```ini
Mint Energie
```

For Octopus Energy France, name the Bitwarden item exactly `Octopus Energy`
and set its URI to `https://octopusenergy.fr/espace-client/comptes/`. The
recipe navigates to **Factures et paiements** without storing private account,
property, or agreement identifiers. Then add this line to
`billcollector.ini`:

```ini
Octopus Energy
```

The initial recipe downloads the payment schedule currently exposed by the
account. Invoice collection can be added after an issued invoice is available
for selector validation.

For CC Genevois, name the Bitwarden item exactly `CC Genevois` and set its URI
to `https://abonnes.cc-genevois.fr`. Then add this line to
`billcollector.ini`:

```ini
CC Genevois
```

The recipe signs in, opens the invoice list, and downloads every available PDF.
Its isolated validation published five PDF invoices; the second run recognized
all five documents and published nothing new.

The suffix is only a local account label. It must not be added to the recipe.

## Repository structure

```text
recipes/
└── free/
    ├── bc-recipe__free.yaml
    └── metadata.yaml
schema/
├── recipe.schema.json
└── metadata.schema.json
scripts/
└── export-recipes.sh
tests/
└── test_recipes.py
```

`metadata.yaml` documents compatibility and validation. It is not interpreted
directly from the provider directory. The export command renames it to
`bc-metadata__<service>.yaml`; current BillCollector images validate that
runtime contract before opening the provider portal.

## Compatibility

Every recipe declares:

- its own version;
- its recipe format version;
- its lifecycle status;
- the minimum BillCollector revision or release;
- required engine actions;
- its authentication characteristics;
- the date and scope of its last validation.

`recipeFormatVersion` and `requiredActions` are enforced at runtime by current
BillCollector images. Until BillCollector has stable semantic releases,
`minimumRevision` remains the human-readable image baseline. For the first Free
recipe, use an image containing revision `06f1d27` or later.
The Fulli recipe requires revision `5353ec5` or later for bounded pagination.

An incompatible recipe must fail CI before release and stop explicitly at
runtime before any provider login is attempted.

## Contributing a recipe

1. Copy an existing provider directory.
2. Use a lowercase normalized service name.
3. Name the recipe `bc-recipe__<service>.yaml`.
4. Fill in `metadata.yaml`.
5. Remove all credentials, subscriber labels, invoice data, cookies, and HTML
   captured from authenticated pages.
6. Run the test suite.
7. Describe the manual validation without publishing personal data.

Install validation dependencies and run:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests -v
```

Selectors should be as stable and specific as possible. Prefer semantic IDs or
attributes over page position. For the legacy Selenium catalog, engine actions belong in BillCollector.
Playwright recipes may use reviewed DOM-only evaluation to expose existing
invoice rows or bind controls to their source invoice number. Never embed
credentials, private identifiers, network calls or document transformations.

## Release policy

- Patch release: selector or documentation fix without new engine capability.
- Minor release: new recipe or backward-compatible metadata extension.
- Major release: incompatible layout or contract change.

Each release must pass schema validation. Release notes list every changed
provider and the required BillCollector version.

## Security

Never commit:

- usernames, passwords, OTP seeds, API keys, or Bitwarden exports;
- real customer or subscriber names;
- invoice PDFs, authenticated HTML, cookies, screenshots, or download URLs;
- private infrastructure names or paths.

Use placeholders in examples. Report a sensitive disclosure privately rather
than opening a public issue containing the data.

## License

Recipes and repository documentation are released under the
[MIT License](LICENSE).

## Unattended Playwright qualification

The runtime baseline is `45e530b7d6240abb308810183dbe4f65aae5b6dc`.
Read each provider metadata before use. `qualified` means complete real-provider
two-pass proof bound to that recipe SHA256. Both sessions use independent browser
profiles. The second session skips known source invoice keys: zero clicks,
zero download events and zero new files. Free, Fulli, Mint Energie and
CC Genevois pass this check. Octopus Energy has no issued invoices on the
configured account and remains unqualified. `experimental` recipes may be
blocked and must not be enabled as unattended production collectors.
The current source work is tracked by `infra-u4hbm`; Infra owns deployment.
Synthetic proof: `PLAYWRIGHT_BROWSERS_PATH=/path/to/cache python
tests/unattended_engine_probe.py /path/to/exact/engine`.
Install that exact engine's `apps/requirements.txt` and this catalog's
`requirements-dev.txt` in the isolated test environment first. The historical
`requirements-engine-tests.txt` belongs to the older single-document probe.

## Bourse Direct history candidate

The catalog now owns the [Bourse Direct operation-notice recipe](docs/bourse-direct.md).
It is experimental: up to 13 months for GetAll, the task window for incremental.
Use engine `c87f980b985d526dac95760e477cec95f280896d` and its packaged schema. The six-recipe
export keeps historical provider proof distinct from this synthetic candidate.
No new real provider qualification or deployment is claimed.
