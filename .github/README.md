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
