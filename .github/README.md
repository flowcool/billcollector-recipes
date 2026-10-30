# GitHub validation and maintenance

CI validates recipes and the export bundle on pull requests, main pushes and
release tags. Security checks audit Python development dependencies and run
CodeQL for Python and GitHub Actions on PRs, main pushes and weekly schedules.
GitHub schedules use UTC and execute the default branch's workflow.

Dependabot groups weekly Python and Actions updates. Dependency alerting and
security-update pull requests are enabled in repository settings. Merges remain
manual and required checks must pass; a second human approval is not required.

Actions are pinned to immutable commits and use read-only contents permissions.
Only CodeQL jobs receive security-events write access for analysis uploads.
Future GitHub releases are immutable. Configure a release as a draft, attach its
assets, then publish; published tags/assets cannot be replaced in place.


## Documentation-only checks

Markdown-only pull requests and branch pushes run lightweight classification
and the required `Catalog CI` / `Catalog security` gates. Catalog tests,
dependency audit and CodeQL jobs report skipped. YAML recipes, metadata,
workflow or code changes run every check. Tags, schedules and manual runs use
full validation. A classification failure blocks both gates.

The required security gate verifies successful Python and Actions CodeQL
analyses for the exact commit and rejects open error-level or high/critical
security alerts. GitHub's unconditional code-scanning rule is replaced by this
required conditional gate. Existing required check names remain configured;
they report skipped on Markdown changes. No code change gets a scan bypass.
