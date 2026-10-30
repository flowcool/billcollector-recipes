# Migrate five providers to unattended Playwright

Florent approved unattended migration of Free, Fulli, Mint Energie, Octopus
Energy and CC Genevois on 2026-10-30. The original migration used Selenium
selectors as a starting point. Florent
approved catalog retirement on the same date. Git history and v0.9.0 preserve
the old files; runtime cutover remains an independent Infra operation.

## Mechanism

The exact qualification baseline is fork revision
`45e530b7d6240abb308810183dbe4f65aae5b6dc`. Its schema is vendored unchanged.
Recipes use engine credential placeholders, native Playwright navigation,
optional cookie dismissal and bounded `download_all` with `incremental: true`.
Source invoice numbers or billing periods identify documents across sessions.
Known keys are skipped before clicking. Mint selects each contract month through
the portal's native filters and uses `unpack: pdf` to retain the one original PDF
member byte-for-byte. Multiple invoices in one contract month fail closed.
Fulli also uses
`click_until_absent` with invoice rows as its progress check. Free expands all
invoice-year panels before collecting the links. No recipe stores credentials,
account identifiers or authenticated download URLs.

## Acceptance

For each provider, use a fresh private database, browser profile and download
root. Disable consumers. Read credentials directly into memory from the existing
vault item. Run the exact recipe twice with the actual engine. The first run
must succeed and download every available invoice. Verify each new file has a
PDF signature. Use a second independent browser profile with the same task DB.
Its source key set must match the first session. The second run must succeed
with zero clicks, zero download events and zero new publications. Retain
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
The retired Selenium export has no CI gate. Export Playwright only into a
disposable directory with `scripts/export-playwright-recipes.sh SOURCE DEST
--engine-revision c87f980b985d526dac95760e477cec95f280896d`. The exporter retains
its ownership manifest, mixed-directory refusal and caught-error rollback.
Never use it directly against the live daemon recipe directory.

Publish one reviewed recipe PR and a versioned release. Infra pins that release
under `infra-1lr1.4` through `.8`. The source qualification owner is
`infra-u4hbm`; incremental delivery is tracked by `infra-25goi`. The older single-document synthetic report describes its original
snapshot and is historical evidence.

## Recovery

Revert the scoped recipe release commit. Retain private proof and originals.
An Infra rollout uses its own versioned operation plan and rollback; this
catalog change does not perform that rollout.

## Current ownership and Bourse Direct

The catalog now owns all six recipes. The four qualified invoice providers keep
the original qualification baseline above. The export pin is c87f980; its schema
is vendored unchanged. Bourse Direct remains experimental with synthetic proof
only for the changed recipe. Its approved intake is in metadata scope and
`docs/bourse-direct.md`. GetAll scans at most 13 offered months; incremental
keeps its recent task window. Infra owns the periodic full-window control run.
No statements, IFU, new portal login or production action is part of this cleanup.
