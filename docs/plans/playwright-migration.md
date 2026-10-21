# Migrate the recipe catalog to Playwright

Scope approved by Florent on 2026-10-21: implement every useful path supported
by the selected engine. Keep Selenium. Test with synthetic data only.
Real accounts and Paperless cutover require a validated operation plan.

## Mechanism and baselines

The runtime consumes `services[].steps[].methods[]`. It tracks one browser
Download per `expect_download` step. It does not provide collection or pagination.
Use the unchanged upstream schema at `c539b3420d0495ee6c4133e88e3a74e6e98740ad`.
Validate runtime behavior against fork `501898cade0b9981092db2011fb3fc02812af8b3`.
The [source assessment](../research/upstream-playwright-contract.md) records
source links and the differences between these baselines.

The fork stages files and suppresses known content before publication.
It publishes before SQLite insertion. Reproduce interruption at this boundary.
Check existing upstream issues. Open one focused issue with synthetic evidence.
Do not claim crash recovery is safe until the engine fixes and tests this case.

## Ports available now

All ports are experimental. Synthetic proof validates recipe execution against
constructed pages. It does not validate current provider pages or credentials.

| Provider | Available scope | Explicit limit |
|---|---|---|
| Octopus Energy | Bills page, agreement page, one payment schedule | No issued invoice flow. Multiple agreements require operator selection. |
| Free | History page, first matching PDF control | One DOM match. No newest-order guarantee or complete collection. |
| Mint Energie | Public login page, invoice page, first matching PDF link | No private activation URL. A link must emit a current-page download event. |
| CC Genevois | Invoice list, first matching download control | One current-page download. No popup or complete collection proof. |
| Fulli | Invoice list, first matching download link | Initial visible list only. No load-more. Captcha requires operator action. |

Use `wait_user` for supervised login, consent and account selection. Guard resume
with a visible account-page selector. Do not automate credential submission with
the current three-attempt runner. Profile reuse does not skip this pause.
These are supervised ports. Unattended authentication remains separate engine work.

Historical invoices were already collected with Selenium. Complete historical
collection is not a prerequisite for these ports. First-listed selection must
never be described as latest, complete, or sufficient for unattended catch-up.
Selenium remains available where wider coverage is required.

## Catalog and export

Keep `recipes/`, `schema/recipe.schema.json` and `scripts/export-recipes.sh`.
Add `playwright/<provider>/recipe-pw__<service>.yaml` with separate metadata.
Copy the exact upstream schema and its MIT notice under `schema/playwright/`.
Metadata records revision, coverage, limitations and separate validation evidence.
Do not export metadata into the runtime recipe body.

Use `scripts/export-playwright-recipes.sh SOURCE DEST --engine-revision SHA`.
Validate the full source before writing. Refuse mixed Selenium destinations,
unmanaged Playwright recipes, symlinks and a conflicting runtime schema.
Use an ownership manifest to replace only the owned set. Preserve unrelated files.
Restore the prior set after caught write errors. A process death during export
can leave a partial release: discard it and export again into a fresh directory.
This exporter targets a disposable release directory, never a live mutable daemon.

## Isolated acceptance

1. Existing Selenium tests and export still pass.
2. Validate five recipe/metadata pairs and supported method chains.
3. Test export refusal, invalid sources, repeat export, stale owned files,
   unrelated files, and restoration after an injected write failure.
4. Archive the exact engine revision into a temporary directory. Override every
   mutable runtime path. Use a temporary SQLite database, profile and output.
   Never import engine helpers from the operational checkout.
5. Execute the actual engine step dispatch and download handler with Chromium.
   Route every browser request to synthetic responses. Reject other traffic.
   Simulate operator resume only in this fixture. Do not contact a vault.
6. For every recipe, prove one tracked file from a multi-item fixture where
   applicable. Repeat with stable task identity and prove no new publication.
   Test empty lists and download failure separately. Assert engine result status.
7. Reproduce process death after publication and before SQLite insertion.
   Restart against the same temporary SQLite database. Record files, hashes,
   tracking rows and consumer calls. Publish only sanitized evidence upstream.

Completion proof is the local commit plus the commands and counts in the
[isolated validation report](../research/playwright-isolated-validation.md).
Rollback is `git revert <catalog-commit>` and disposal of isolated test output.
No provider schedule, credentials or production state changes in this phase.

## Work that remains separate

The collection prototype remains our work under `infra-zlth.65` and fork PR #41.
Continue its development and review in the engine project. Maintainer agreement
for upstream contribution does not gate independent catalog ports. Once a target
engine includes the proven contract, extend each recipe and its fixtures with
bounded complete collection. Fulli also needs progress-aware pagination.

Shared engine contracts remain under `infra-zlth`. Catalog work belongs to
`infra-spee`. Real-account verification and cutover belong to `infra-1lr1`.
Use quarantine output disconnected from Paperless during approved real tests.
Reconcile historical content and stable task identity before enabling publication.
Existing Selenium history does not automatically populate Playwright SQLite.
Keep reverse continuity and a single active scheduler in the cutover plan.

## Evidence that changes the plan

- New engine source: repeat exact-revision contract checks.
- Proven collection or pagination: remove only the corresponding coverage limit.
- Changed portal selectors or download transport: revise that provider only.
- Proven safe unattended login: replace the supervised pause with that contract.
- Proven interrupted-publication recovery: repeat crash tests before cutover.
