# Bourse Direct monthly account statements

The catalog enables monthly account statements with `collect_statements: true`.
Qualification remains synthetic and offline.
Retained observations establish the controls below. They do not prove the current
live portal. Credentials, private captures and account documents stay outside Git.
The engine capability request is tracked by `infra-gc1q3`; the collector owner is
`infra-h9a7l`.

## Offered source controls

The public menu links to `/fr/page/releves`. Its statement frame uses
`/priv/new/releves.php`. The selected account is in `select#nc` inside
`form#frmCompte` (GET). Keep its account identity separate from the notice
calendar identity until the selected account label proves the mapping. Do not
assume identical numeric account values across the two pages.

`form#frmRlv` contains `input[name=nc]` and `select[name=RlvCombo]`.
Changing the period submits this form by POST through its existing `onchange`
handler. Its action is `?`. The option value is a position in the offered list,
not a durable document key. Labels are French month names and four-digit years.
Read the full offered list on each run. A new or late month can appear without
changing an existing option position reliably.

The selected period offers an anchor with this structural form:

```text
javascript:ouvrePopup('releveCompte.php?nc=<account>&dt=<YYYYMMDD>&type=RE','encours')
```

The returned HTML offers exactly one `Format PDF` anchor. Its target is
`/priv/new/releveCompte.php` with exactly `nc`, `dt`, `type=RE`,
`trash=/avis.pdf`, and `pdf=1`. Resolve relative links against the observed
same-origin page. Verify account, family and period before requesting a PDF.
Do not construct an unoffered document URL.

The `dt` date can be the last business day. Synthetic fixtures include
`Novembre 2025` with `dt=20251128`. Do not calculate a calendar month-end date.
The retained list contains 21 monthly periods. This is retained history, not a
live guarantee or a 21-month limit. The annual section and `releveTitres.php`
are separate families. Do not collect them as monthly account statements.

## Identity and delivery contract

Within the existing selected-account task, the statement source key must include
the account, `type=RE`, and the offered period. Keep the original SHA-256 as the
byte-level proof. Preserve a changed original as a new revision. Reuse the
engine's conservative PDF revision check if the provider regenerates metadata.
Never use a month or filename alone to prove equal content. An unchanged repeat
must create no publication and no consumer call.

Use `BourseDirect_Statement_<account-kind>_<YYYY-MM>_<offered-date>.pdf`.
The existing `BourseDirect_*.pdf` Paperless consumption workflow then covers the
same owner, correspondent, document type, `Source=Bourse Direct` field and
reader grant as notices. Add no tag. The importer classifies statements by
their content. Infra must verify the actual type and access on original-byte
readback before accepting production delivery.

## Historical engine blockers

The catalog exports YAML and schema files. It does not export
`bourse_direct_adapter.py`. Editing that reference file alone cannot change
the running collector.

The catalog engine pin `c87f980b985d526dac95760e477cec95f280896d` and the
deployed-engine contract `515155f4e87fa6968ff899946787a0ee5284851a` both have a
native notice-only action:

- `validate_options` rejects additional statement options.
- The single source action requires the notice identity fields
  `nc,type,year,month,day`. Statement URLs have `nc,type,dt`.
- The target validator accepts only `releveOpe.php` and `type=RO`.
- The request guard rejects non-login POST requests. It therefore rejects the
  observed period form submission.

The statement-capable pin in catalog metadata extends this boundary. Keep one authenticated session, the existing task and delivery
journal, request pacing, failure budget, and uncertain-delivery inhibition.
Do not weaken the POST guard for unrelated routes. Run notice and statement
collection under one source transaction without another login.

Reproduce the historical compatibility gap with the engine runtime dependencies:

```sh
python tests/bourse_direct_statements_gate_probe.py /path/to/engine/repository
```

The probe archives both exact revisions into isolated temporary directories.
It validates the unchanged notice recipe as a positive control. It then checks
that statement options, identity and the synthetic original target are refused.
It blocks socket connections and opens no browser or vault. It does not prove
statement acquisition, notice collection behavior or Paperless delivery.

## Required acceptance

Use synthetic portal fixtures and isolated DB, profile and output. Invoke the
actual exported recipe through its exact engine. Prove all offered periods,
unchanged repeat, a late month, a corrected PDF, wrong account, wrong family,
ambiguous period and PDF links, a stalled period selector, and interrupted
delivery with no automatic resend. Compare notice counts and original hashes
with the unchanged recipe on the same synthetic inputs. Require one login
transaction at most for the combined collection.

Real-provider proof and production deployment require Florent's GO. Infra's
full-window guard currently accepts operation notices only and pins the old
recipe hash. Infra must qualify its statement scope and pin changes before
deployment. A merged catalog PR alone does not make that guard compatible.

## Current candidate qualification

Read `engineRevision` in provider metadata for the exact qualified pin. The
exporter and vendored schema use that pin. Statement identity is supplied per
original by the engine; the recipe keeps its existing notice identity policy.
The request guard permits one exact native period-form POST at a time.

Run the positive compatibility gate against the exact pin:

```sh
python tests/bourse_direct_statements_gate_probe.py /path/to/engine --candidate-revision <engineRevision>
python tests/bourse_direct_engine_probe.py /path/to/exact/engine
```

The first command archives the selected commit, blocks sockets and checks the
notice control, statement option, source identity and last-business-day target.
It does not prove acquisition. The second command exports the catalog into an
isolated directory. It runs a notice-only control with the statement flag removed,
then runs the unchanged exported candidate through the exact engine on synthetic
browser fixtures. Both modes cover full offered periods, new/late months,
corrections, source refusal and uncertainty without resend. The engine's combined
control also compares notice counts and original hashes before and after opt-in.
Run the exported recipe on the exact immutable image with saved receipts:

```sh
python tests/bourse_direct_engine_probe.py /path/to/exact/engine \
  --image ghcr.io/flowcool/billcollector-playwright@sha256:<digest> \
  --proof-dir tmp/statement-image-proof
```

The image must already be pulled. The tool checks its revision label, uses
network isolation and UID 1003, and retains the log and result in the new proof
directory. The one-shot container uses `--rm`; its evidence lives in those files.

Credentials/TOTP and consumers are synthetic. Vault transport, scheduling, live
portal controls, Infra consume mounts and Paperless readback remain unqualified.

Statements always read the complete offered list, including months older than
the notice window. The engine refuses more than 120 unique statement periods.
`max_items: 100` counts both families; `timeout_ms: 7200000` bounds the whole
source transaction. Form submissions, statement HTML reads and original reads
share the configured document gate. No second login or separate task is added.
Infra must promote the exact packaged schema before enabling this recipe.
