# Fulli login navigation

## Failure and correction

A retained browser profile can reach the public homepage when visiting
`https://www.fulli.com/customer/login`. The page has no `#identifier` field.
The old recipe then retries credential entry and pauses without downloading.
The failure was reproduced on 2026-11-01 with a private copy of a profile from
prior isolated qualification. A subsequent visit reached the SSO form.
This proves a session-dependent navigation state. It does not establish which
server-side session condition caused the redirect in the production run.

The recipe now clicks `.UserAccountMenu a[href="/customer/login"]` once before
credential entry. The click is optional and has a three-second timeout. A direct
SSO landing has no account menu, so execution continues to the existing form.
An unexpected page still fails at the required credential field. There is no
credential retry loop in the new step. Credential submission, invoice history,
source keys and incremental downloads retain their previous behavior.

## Synthetic regression

Use an isolated engine checkout at
`45e530b7d6240abb308810183dbe4f65aae5b6dc` and its Python/browser dependencies:

```sh
PLAYWRIGHT_BROWSERS_PATH=/path/to/browser-cache /path/to/python \
  tests/unattended_engine_probe.py /path/to/engine --provider fulli --fulli-homepage
PLAYWRIGHT_BROWSERS_PATH=/path/to/browser-cache /path/to/python \
  tests/unattended_engine_probe.py /path/to/engine --provider fulli
```

The first scenario serves a public homepage on the first login visit. Its native
account link leads to the synthetic login form on the second visit. The fixture
changes its URL with browser history instead of an HTTP redirect, because a
redirect following a routed request can bypass Playwright interception.
The second scenario reaches the form directly. Both must collect three synthetic
PDFs, then succeed with zero clicks, events and new records from a fresh profile.
Source keys must stay equal. External requests must be empty. The homepage case
also requires exactly two login-page visits per run. The old recipe fails this
case at credential entry with zero downloads.

## Real-provider proof and recovery

Fulli was requalified on engine `4d2a893be89a83c47b940c174bad3fa75bbf2ade`.
The first pass obtained 14 PDFs. The independent repeat made zero clicks,
zero download events and zero new records. Both source-key sets matched. Only
April 2025 was absent from the earlier 15-period set. All 14 PDFs had the same
page counts, extracted text and decoded page content as the prior originals.
Their byte hashes changed; the portal regenerated the PDF creation date.
The collector retains the downloaded originals without rewriting them.

The interrupted second attempt stopped before credential entry. Its isolated DB
copy retained the known 14 keys and recorded that attempt as cancelled. The
repeat used this copy and a new browser root. No original downloads were resent.

Fulli metadata binds qualification to the exact recipe hash and engine revision.
Private originals, profiles and run records remain outside Git. Infra owns
production installation and its provider-only rollback. Source rollback reverts
the scoped recipe change and restores its matching metadata. Retain all proof.
