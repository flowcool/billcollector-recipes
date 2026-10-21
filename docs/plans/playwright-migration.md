# Migrate the recipe catalog to Playwright

Proposal date: 2026-10-21. Approval is pending.
Scope: the five existing providers. This document proposes local catalog work.
It does not authorize provider access, task creation, publication or deployment.

## Recommendation

Keep the Selenium catalog usable. Add Playwright recipes in a separate directory.
Port one complete provider flow first. Then port the other four.
Keep the existing production schedule until each replacement passes its gates.

Use the maintainer's recipe syntax and runtime. Keep engine features in the engine.
Do not create a second browser runner or translate recipes at runtime.
This reduces maintenance and keeps upstream contribution possible.

Confidence is high for the format mismatch and engine gaps. Confidence is medium
for the provider order. Current portal behavior has not been tested in this study.

## Evidence and boundaries

Three engine baselines have different guarantees:

| Baseline | Evidence | Meaning |
|---|---|---|
| Existing catalog | [Catalog at `b29234f`](https://github.com/flowcool/billcollector-recipes/tree/b29234f), deployed release `v0.6.0` at `8c2d2d6` | Five Selenium recipes. Historical portal checks do not validate Playwright. |
| Public maintainer | [Upstream `c539b3420d0495ee6c4133e88e3a74e6e98740ad`](https://github.com/s-t-e-f-a-n/BillCollector/tree/c539b3420d0495ee6c4133e88e3a74e6e98740ad) | Playwright daemon with persistent profiles, SQLite, UI and download tracking. |
| Installed candidate | [Fork `501898cade0b9981092db2011fb3fc02812af8b3`](https://github.com/flowcool/BillCollector/tree/501898cade0b9981092db2011fb3fc02812af8b3) | Derived daemon with additional runtime fixes. This is not an unmodified upstream image. |

The infrastructure owner records a healthy empty daemon beside the active legacy
scheduler. Its deployment uses the existing stack and vault sidecar. The earlier
separate-stack draft was rejected. This study read that deployment evidence and
the merged configuration. It did not query the live host or live database.
Runtime facts must be checked again before an operation.

The [source assessment](../research/upstream-playwright-contract.md) gives the
method, vault, schema and download contracts with immutable source links.
Beads owns deployment proof and task state. This public document omits private
infrastructure paths, endpoints and account labels.

## What can be reused

Reuse the provider names, public selectors and documented navigation intent.
Keep credentials in the existing vault. Verify exact item-name resolution with a
synthetic vault before using real credentials.

The new syntax uses `services[].steps[].methods[]`. It replaces the old
`services[].actions[]` syntax. Credentials use `{{USERNAME}}`, `{{PASSWORD}}`
and `{{OTP}}`. A selector followed by `fill` or `click` maps well to the new
method chain. A download requires the runner's tracked download path.

The daemon now provides persistent browser profiles and per-task content hashes.
Do not rebuild those features from the older transition assessment.
The installed candidate also stages files before deduplication and publishes
without overwriting an existing filename. Public upstream differs here.
Check the exact target image, not only the latest public source.

## Gaps that gate delivery

1. **Complete collection.** Free, Mint and CC Genevois use `DownloadAll`.
   Fulli also uses bounded `ClickUntilAbsent`. Neither engine baseline above
   supports those declarative collection methods. Fork analysis PR
   [#41](https://github.com/flowcool/BillCollector/pull/41) is a prototype.
   Its existence is not upstream agreement or deployment evidence.
   The engine owner must deliver the accepted contract and its regression proof.
2. **Safe login.** Persistent profiles do not prevent repeated credential
   submission. The deployed runner can retry an entire failed step three times.
   Keep submission in a distinct step. Before any real run, prove its retry and
   resume behavior. Use a proven safe-login implementation or an approved
   supervised interaction path. A three-attempt submission is not acceptable by
   default. The shared contract is [issue #20](https://github.com/s-t-e-f-a-n/BillCollector/issues/20).
3. **Download attribution.** Browser downloads can be tracked. A method-chain
   API request does not automatically create a tracked file. Use the engine's
   supported download path. Do not replace collection with embedded JavaScript,
   raw HTTP writes or a fixed number of `nth()` calls.
4. **Empty results.** A completed run with zero download events is currently a
   failure. A repeat download of known bytes is different: it can succeed while
   publishing zero new files. Test both cases. Agree any changed result semantics
   with the engine owner before relying on an empty invoice list as success.
5. **History continuity.** Legacy JSON stores account-scoped URL, filename and
   content hashes. Playwright SQLite stores downloads per task ID. No automatic
   conversion between those histories was found. A fresh task can publish an
   entire historical catalog again.
6. **Interrupted publication.** The installed tracker publishes the file before
   it inserts the SQLite row. A crash between those steps can leave a file
   without a dedup record. Consumer failures also do not fail the run. Before
   Paperless integration, prove recovery across that boundary and verify actual
   ingestion. A successful collection result alone is not delivery proof.

These gates do not prevent repository layout work or synthetic fixtures.
They do prevent claiming a full port or a safe Paperless cutover.

## Provider order and acceptance

The order below is a proposal based on existing recipe complexity.
Invoice counts describe old observations. They are not fixed test expectations
for a live portal. Synthetic fixtures have deterministic counts.

| Order | Provider | Existing behavior | Port risk and required proof |
|---|---|---|---|
| 1 | Octopus Energy | Login, bills page, agreement page, one payment schedule | Smallest complete flow. Prove one tracked PDF, duplicate suppression, profile reuse and account selection. An invoice port still needs an issued invoice and verified selectors. |
| 2 | Free | Login, full invoice history, every PDF link | Good first collection fixture. Prove all visible documents, no positional selection, and stable behavior after navigation. Old validation found 19 files. |
| 3 | Mint Energie | Login, direct invoice-page navigation, all PDF links | Prove a public login URL works without exposing the private activation URL. Vault URI is not a runtime navigation variable. Prove all matching files, not just one. |
| 4 | CC Genevois | Optional consent, login, invoice list, clickable PDF controls | Prove generated downloads from controls, attribution of each file, and optional-banner behavior. Old validation found five files. |
| 5 | Fulli | Two-stage login, optional consent, load-more loop, all invoices | Highest risk: captcha, cumulative pagination, progress detection, duplicate controls and partial failures. Preserve the explicit pagination bound. Stop when human action is required. Old validation found 14 files. |

Octopus first proves the catalog-to-daemon path without waiting for collection.
It does not prove the collection capability needed by the other providers.
Move Free first if the collection contract is delivered before the pilot starts.
Bourse Direct is outside this five-provider migration. Its separate date and
login gates must not become an artificial prerequisite for every existing recipe.

## Proposed repository contract

Preserve `recipes/`, `schema/` and the existing export command during the overlap.
Add the following only after agreement on this proposal:

```text
playwright/<provider>/recipe-pw__<service>.yaml
playwright/<provider>/metadata.yaml
schema/playwright/recipe.schema.yaml
schema/playwright/metadata.schema.json
scripts/export-playwright-recipes.sh
tests/fixtures/playwright/<provider>/
```

The file layout is a catalog choice. The recipe body stays upstream-compatible.
Copy the exact engine schema with its source SHA and license provenance.
Add catalog checks for the method subset that each recipe actually needs.
The upstream schema accepts free-form method names. Schema validity alone cannot
prove that a method exists or that a download reaches the tracked path.

Keep metadata outside the runtime recipe contract. Include the engine family,
tested revision, required capabilities and separate synthetic and real validation
evidence. Mark each new port experimental until real validation succeeds.
Do not carry Selenium `requiredActions` or old validation dates into Playwright
as proof. Reuse facts only when their meaning remains valid.

Use a separate exporter to avoid changing the existing two-argument command.
It exports only Playwright runtime recipes. It rejects a mixed or unmanaged
destination before writing. It prepares and validates the complete export before
replacing the owned set. It preserves the runtime schema and unrelated files.
The command must have fixture-based tests for refusal and partial failure.

The daemon can edit recipes through its UI. A release artifact must have one
owner: export to a release directory, then import through a controlled infra
step. Capture and review UI repairs before promoting them to this catalog.
Do not overwrite a mutable runtime directory from an unattended Git update.

No branch or release name alone identifies an engine contract. Keep the current
Selenium tag usable. Select the Playwright release policy when its exporter and
metadata contract are accepted. Keep runtime recipes free of catalog-only keys.

## Delivery phases

### 1. Add the catalog contract and an Octopus fixture

Implement the separate schema, metadata, exporter and synthetic portal fixture.
Keep all production inputs unchanged. Test missing metadata, unsupported methods,
wrong engine selection, duplicate filenames and export refusal.

Completion proof: the existing suite passes; Playwright contract tests pass;
the exact target engine executes the synthetic Octopus recipe and tracks one PDF.
Rollback: revert the focused catalog commit. The old exporter remains usable.

### 2. Complete the synthetic pilot

Run the actual recipe through the exact daemon runner. Use a temporary database,
browser profile, vault fixture and output directory. Disable scheduling and use
one display and one concurrent task. Restrict browser traffic to the fixture.

Prove a fresh login, valid-session reuse, an expired session and a failed login.
Prove one credential submission per approved phase. Prove a failed download,
explicit resume, same-name different-content files and restart persistence.
Interrupt between file publication and database recording. Verify that recovery
does not publish the same document again. Keep this engine proof with its owner.

Run twice. The first run publishes one synthetic PDF. The second creates no new
public file and no new consumer call. It must have an understood result status.
Prove the empty-list case separately. Scan retained logs and evidence for the
synthetic secret markers. Keep task identity stable across recipe updates.

Completion proof: named tests and sanitized counts on an exact image digest.
Rollback: discard the isolated test environment; revert the pilot recipe commit.

### 3. Port the collection recipes

Use the engine owner's accepted collection and pagination implementation.
Verify that it exists in the chosen image and schema. Port each provider as one
focused change. Use synthetic lists with zero, one and several documents.
Test reordered items, re-render, navigation away and return, missing controls,
pagination without progress, bounds, and failure after a partial download.

Completion proof: every fixture is complete, bounded and repeatable. Resume does
not replay persisted items or publish duplicates. Fulli cannot loop indefinitely.
Rollback: revert one provider commit. Keep the preceding recipe release pinned.

### 4. Validate real providers in quarantine

This is an infrastructure operation. It needs a separate validated operation plan
and Florent's GO. Before adding real tasks, prove database/profile backup and
restore, UI access, vault resolution, retained-log handling and bounded login.
Disable task cron and keep output disconnected from Paperless.

Run one provider under supervision. Use private isolated output and the intended
stable task identity. Compare files and coverage with the expected provider
history. Run again and prove zero new publications. Do not publish PDFs, profile
files, URLs or screenshots in this repository.

Completion proof: sanitized provider evidence, exact recipe commit and image
digest, complete coverage, no duplicate publication and an approved restart path.
Rollback: disable that task; retain private evidence and the legacy state.

### 5. Prove history continuity, then cut over

Prefer building genuine Playwright history in quarantine. Do not fabricate
SQLite download rows from unmatched legacy hashes. The default avoids an importer
and its schema maintenance. It costs one controlled historical collection.

This choice is conditional. If the history is too large, inaccessible or incomplete,
design a separate tested migration tool before cutover. Filename hashes alone do
not prove document identity. Content hashes can differ when a portal regenerates
a PDF. Resolve every mismatch before publishing it to Paperless.

The infrastructure plan must record the final legacy run and the exact per-provider
schedule handoff. Freeze the selected legacy provider before the final comparison.
Use the same Playwright task identity that owns the quarantined history.
Confirm that historical bytes remain suppressed when output switches to the
approved publication path. Prove one new document is published exactly once.

Also prove reverse continuity before re-enabling Selenium after a Playwright
publication. The old JSON does not know about new SQLite downloads. Preserve both
histories. Treat rollback as a data operation, not just an image or recipe revert.
Do not enable both schedulers for the same provider during recovery.

Completion proof: offline bidirectional state tests, approved real-data
reconciliation, one active schedule per provider, one new document ingested, no
historical duplicate, and verified backup/restore. Keep retirement separate until
the replacement schedule has run successfully.

## Responsibility and next step

The catalog epic is `infra-spee`. Shared engine features stay with `infra-zlth`.
Production configuration, backups, quarantine and cutover stay with `infra-1lr1`.
Do not reopen the old closed migration beads as if their criteria were delivered.

After proposal agreement, start phase 1: the separate catalog contract and the
synthetic Octopus pilot. Prepare one focused deliverable at a time. Create the
per-provider implementation work when its engine prerequisites are known.
No new schema agreement request or maintainer message is authorized by this plan.

## Evidence that changes this plan

- A new public schema delivers collection and pagination: recheck it and remove
  the corresponding engine gate.
- The target image changes: repeat the contract checks against its exact source.
- Octopus needs unavailable private selectors: use Free after collection is ready.
- A supported upstream history importer appears: compare its guarantees with the
  quarantine approach before selecting it.
- The first supervised portal run shows changed navigation or protection: revise
  that provider's flow and keep the others independent.
