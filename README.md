# BillCollector Recipes

Community recipes for
[flowcool/BillCollector](https://github.com/flowcool/BillCollector), a
maintained fork of
[s-t-e-f-a-n/BillCollector](https://github.com/s-t-e-f-a-n/BillCollector).

Recipes describe how BillCollector navigates a provider portal and downloads
documents. They contain selectors and actions, never credentials or customer
data.

> [!WARNING]
> This repository is beta. Provider portals can change without notice. Pin a
> release, test updates manually, and keep the previous release for rollback.

## Available recipes

| Provider | Service | Status | Authentication | Last real validation |
|---|---|---|---|---|
| Freebox Internet | `free` | Beta | Username/password, no MFA observed | 2026-07-27 |
| Fulli Toll | `fulli` | Experimental | Username/password, no MFA reported | Not yet validated |

The Free recipe downloaded 19 historical invoices during its initial
end-to-end validation. That result does not guarantee that Free's portal is
unchanged today.

The Fulli recipe currently covers only the public two-step login flow. It does
not yet include authenticated invoice navigation or downloads and must not be
scheduled.

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

Then select the experimental recipe with:

```ini
Fulli [Toll]
```

The Fulli login page may present a FriendlyCaptcha challenge. BillCollector
does not bypass it; authenticated validation must stop if human interaction is
required.

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
attributes over page position. A recipe must not execute arbitrary JavaScript;
engine actions belong in BillCollector itself.

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
