# Isolated Playwright catalog proof

Date: 2026-10-21. Synthetic data only. No provider account or vault access.

## Test environment

Engine: fork `501898cade0b9981092db2011fb3fc02812af8b3`.
Schema: upstream `c539b3420d0495ee6c4133e88e3a74e6e98740ad`, byte-identical
in the fork. Python 3.14.6. Test client: Playwright 1.58.0, Chromium build 1208.
The source archive, SQLite, profiles, output and engine helper paths are temporary.
The launcher uses an exact Git archive, regardless of checkout changes.

The actual engine `_run_recipe`, method dispatcher, step retry, guarded
`wait_user` handling, nested download handler, tracker and Database execute.
The test adapter launches Chromium headless and simulates operator resume.
Browser requests are fulfilled from synthetic fixtures; other hosts are rejected.
No scheduling, display allocation, vault lookup or real credential submission runs.
This is source-level engine proof, not a deployed image or real portal validation.

## Commands and results

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tests/engine_probe.py /path/to/engine-repository
.venv/bin/python tests/engine_probe.py /path/to/engine-repository \
  --revision c539b3420d0495ee6c4133e88e3a74e6e98740ad --crash-only
```

The unit suite passes 11 tests: four existing Selenium tests and seven catalog
and exporter tests. It checks five recipe/metadata pairs, rejected source
contracts, wrong revision, mixed/unmanaged destinations, schema preservation,
symlinks, stale owned files, unrelated files and rollback after a write failure.

Both export commands also run in disposable directories. Selenium exports five
recipes and five metadata files. Playwright exports five recipes, the exact
runtime schema and its ownership manifest. It exports no catalog metadata.

| Recipe | First run | Repeat, same task and database | Fixture coverage |
|---|---|---|---|
| CC Genevois | One tracked PDF | Success; zero new files or consumer calls | Two download controls; first selected |
| Free | One tracked PDF | Success; zero new files or consumer calls | Two PDF links; first selected |
| Fulli | One tracked PDF | Success; zero new files or consumer calls | Two links and an unused load-more control |
| Mint Energie | One tracked PDF | Success; zero new files or consumer calls | Direct invoice navigation, two PDF links |
| Octopus Energy | One tracked PDF | Success; zero new files or consumer calls | Bills page, one agreement, payment schedule |

The multi-item fixture places older content first. The bytes prove that the
recipe selects that item. This deliberately gives no newest-document guarantee.
Fresh browser contexts reuse the isolated profile path. This alone does not prove
real session reuse or authentication behavior.

Negative cases use a dedicated synthetic Free task. An empty list and an aborted
download reach the engine pause path; simulated cancellation returns `cancelled`
and records no successful downloads. Operator cancellation at login also returns
`cancelled`. The engine result function returns `failure` for a completed run
with zero download events. The negative fixtures shorten click/event timeouts
and omit account navigation only for the empty-list case.

## Interrupted publication

The test exits a child process with `os._exit(73)` from the actual Database
insertion boundary. The published file and a synthetic consumer marker already
exist. SQLite contains zero Download rows. Retry uses the same task and database.

| Baseline | Files after interruption | Files after retry | SQLite rows after retry | Consumer calls |
|---|---|---|---|---|
| Public upstream `c539b342` | 1 | 1, rewritten | 1 | 2 |
| Selected fork `501898ca` | 1 | 2, identical SHA-256 | 1 | 2 |

The expected vulnerable behavior is reproduced. The test passing does not mean
that interrupted publication is safe. The normal persisted-hash duplicate test
passes separately. [Upstream issue #24](https://github.com/s-t-e-f-a-n/BillCollector/issues/24)
contains the self-contained reproduction. The engine owns the recovery contract.

## Remaining limits

Each provider metadata file records the port limits. All ports require supervised
login, consent and account selection. Four providers select only the first listed
document. Fulli has no pagination. Octopus supports the payment schedule only.
Real selectors, private start URLs, multiple agreements, popup downloads and
real profile/session behavior remain unverified. No real account or Paperless
cutover is authorized by this evidence.
