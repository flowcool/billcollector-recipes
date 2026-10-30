# Migrate five providers to unattended Playwright

Florent approved unattended migration of Free, Fulli, Mint Energie, Octopus
Energy and CC Genevois on 2026-10-30. Use the existing Selenium selectors as the
starting point. Preserve the Selenium catalog. Its deployed scheduler remains
available until Infra completes each provider cutover.

## Mechanism

The exact qualification baseline is fork revision
`b401f801c9184f6b0c8917fb8d06a79fa0f0e917`. Its schema is vendored unchanged.
Recipes use engine credential placeholders, native Playwright navigation,
optional cookie dismissal and bounded `download_all`. Fulli also uses
`click_until_absent` with invoice rows as its progress check. Free expands all
invoice-year panels before collecting the links. No recipe stores credentials,
account identifiers or authenticated download URLs.

## Acceptance

For each provider, use a fresh private database, browser profile and download
root. Disable consumers. Read credentials directly into memory from the existing
vault item. Run the exact recipe twice with the actual engine. The first run
must succeed and download every available invoice. Verify each new file has a
PDF signature. The second run must succeed with zero new publications. Retain
private originals and browser evidence outside Git. Record aggregate counts,
recipe SHA256 and exact engine revision in metadata and the owning issue.
Octopus must collect issued invoices; a payment schedule is insufficient.

A failed provider remains unqualified. Record its exact blocker and continue
independent providers. Do not deploy, alter the live database or recipe mount,
write to staging or Paperless consume, or disable Selenium during qualification.
Production delivery and scheduling remain Infra responsibilities.

## Catalog and publication

`playwright/<provider>/` contains the recipe and separate metadata. The catalog
exporter validates every recipe and its metadata before writing. Qualified
metadata must match the actual recipe hash and two-pass counts. A stale proof or
human-login pause cannot qualify an unattended recipe.

Run `python -m unittest discover -s tests -v` and the isolated browser probe.
Keep the existing Selenium export checks. Export Playwright only into a
disposable directory with `scripts/export-playwright-recipes.sh SOURCE DEST
--engine-revision b401f801c9184f6b0c8917fb8d06a79fa0f0e917`. The exporter retains
its ownership manifest, mixed-directory refusal and caught-error rollback.
Never use it directly against the live daemon recipe directory.

Publish one reviewed recipe PR and a versioned release. Infra pins that release
under `infra-1lr1.4` through `.8`. The source qualification owner is
`infra-u4hbm`. The older single-document synthetic report describes its original
snapshot and is historical evidence.

## Recovery

Revert the scoped recipe release commit. Retain private proof and originals.
An Infra rollout uses its own versioned operation plan and rollback; this
catalog change does not perform that rollout.
