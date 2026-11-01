# Bourse Direct recipe and adapter

This candidate implements the accepted issue #51 contribution boundary for
`infra-zlth.52`.

The exact engine revision is
`89a89cc2c55c7dfc53ffb07acd73630621f2911b` from
`flowcool/BillCollector#89`. The recipe uses one native `goto`, one native
login block with final-session proof, and one standalone `bourse_direct` step.
The step binds the notice identity fields `nc`, `type`, `year`, `month`, and
`day`, and bounds the run to 13 months, 100 offered items, and 7,200,000 ms.

`playwright/bourse_direct/bourse_direct_adapter.py` is trusted catalog code.
It declares only literal C3-validated Playwright chains. It parses the offered
account and month, requires explicit empty-month proof, follows the offered
notice link, checks the unique `Format PDF` link and source identity, and sends
original bytes through the engine authenticated request context. The engine
owns task history, notice revisions, at-least-once delivery, login state and
run results.

The catalog exporter includes the adapter beside the recipe and records the
engine revision in its ownership manifest. No credentials, account values,
session material, private URLs or documents are committed. The retained
recipe `3110157` and historical five-original/five-duplicate proof remain
historical evidence only.

## Offline proof

The catalog suite passes with:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

This run reports 13 passing tests, including direct adapter fixtures for
offered identity, original-link handling and source-path fail-closed behavior.

The exact-engine probe uses a detached `89a89cc` worktree, the matching
Playwright browser cache and loopback fixtures only:

```sh
PLAYWRIGHT_BROWSERS_PATH=/data/cache/flow/ms-playwright \
BC_BROWSER_DIR=/data/cache/flow/ms-playwright \
tmp/venv/bin/python tests/bourse_direct_engine_probe.py tmp/engine89-work
```

The probe result is 80 engine tests passed, the recipe and adapter pass the
engine C3 load/save/run-start validation, and the reported schema hash is
`f3b92edaa352d29c794581b8ff67a5a3b7e6066a608c354e6d4799eabaafc523`.
The probe performs no provider login, vault access, archive write or
Paperless action. Real-provider qualification remains outside this candidate.

Recovery is a focused revert of the candidate commit. Upstream publication,
deployment and archive receipt agreement remain separate work.
