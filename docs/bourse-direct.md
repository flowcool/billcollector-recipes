# Bourse Direct notices and monthly statements

Monthly account statements use the same task and session as operation notices.
Read the [statement controls and proof](bourse-direct-statements.md).

Catalog owner: `infra-22l0n`; delivered history: `infra-5iqmw`; engine pacing: `infra-36zv1`.
Install the catalog recipe at `/apps/recipes_playwright/recipe-pw__bourse_direct.yaml`
and use an explicit recipe_file for the existing task. Keep its service/user
identity, DB path, profile, journal and archive policy. Do not create a new task
to reset deduplication. The legacy bundled filename has changed; Infra must set
the exact exported path before loading this catalog.

Download All traverses at most 13 offered months, including the current month.
For an October 2026 run it starts at October 2025. Incremental keeps the task's
recent window (`date_window_days`, default 90), including the first partial
month; it does not rescan 13 months automatically. An explicit recovery start
wins in either mode, within max_months and max_items. A calendar reset to the
current month fails closed. The source revision tracker remains active for both
modes; unchanged notices do not create new output, corrected originals do.

The recipe remains `incremental: true`, max_months13, max_items100,
timeout_ms7200000. Monthly statements use `collect_statements: true` and read
every offered period in both modes. The item/deadline bounds cover both families.
Annual, securities and tax statements remain outside the recipe.

The engine uses generic Settings login_request_interval_seconds (default60,
minimum60 for this adapter) and document_request_interval_seconds (default5).
They use separate durable clocks and share the run deadline. No credentials
or authenticated URLs belong in this catalog.

Qualification: `python tests/bourse_direct_engine_probe.py /path/to/exact/engine`.
Use that engine's test/runtime environment and matching Chromium. The probe
runs its native recipe/adapter tests against loopback synthetic fixtures and
isolated DB/profile/output. It checks 13-month GetAll, recent incremental,
explicit overrides, boundary reset refusal and configured gates. It bypasses
real vault preflight, real provider and Paperless; no new live run is claimed.
Preserve the old provider proof with its original artifact and limits.

Export into an unused release directory, never the live recipe mount. Infra
owns image/schema/recipe pins, rollout and original-byte archive readback under
its operation plan. Revert the catalog release for source rollback; deployment
recovery must retain DB, journal, profiles and originals.

## Approved intake

Florent approved operation notices only on 2026-10-30, without a new portal
connection for this P1. The structured intake lives in `metadata.yaml` under
`scope`. The retained PEA proof covers five October 2026 notices, then zero new
files, on an older artifact. The current recipe remains experimental. PEA-PME
has synthetic coverage only. Monthly statements were approved on 2026-11-08.
Their retained controls are qualified offline in the linked statement document;
the pinned engine implements collection in the existing source transaction. IFU and other families still need inventory
and a scope decision.
The retained 2025-10 calendar boundary is an October 2026 observation. It is not
a fresh measurement or proof of 13 live months.

Notice identity uses nc, type, year, month and day within the existing selected
account task. Runtime revisions remain distinct. GetAll and incremental have
different bounds. A periodic full-window control run is required to detect late
or changed notices outside the recent incremental window. Infra owns its cadence
and alerts under `infra-1lr1.3`; this catalog does not change a schedule.
