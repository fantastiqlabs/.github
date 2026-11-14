# Public-site quality workflow

Public static product sites can opt in with a short caller workflow:

```yaml
name: Public site quality

on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

jobs:
  site-quality:
    uses: fantastiqlabs/.github/.github/workflows/public-site-quality.yml@main
    with:
      site_dir: .
```

Set `site_dir` to the generated site directory when the repository builds into a folder such as `dist/`. The workflow scans HTML files under that directory, checks local links and fragments without requesting external hosts, serves the same directory locally, and runs axe-core's WCAG 2.1 A/AA rules in headless Chromium.

## Thresholds and exclusions

- Local paths from `href`, `src`, `action`, and `poster`, plus same-page and local HTML fragments, must resolve. External HTTP(S) links, `mailto:`, `tel:`, `javascript:`, and `data:` URLs are excluded; this required check does not depend on third-party availability.
- Accessibility runs on at most 100 HTML pages in sorted path order. The full HTML tree still receives the local-link check. Sites over the accessibility cap get an Actions warning so the owner can raise the cap deliberately if needed.
- Axe violations are uploaded as a 14-day artifact and are report-only during the initial rollout. This captures the existing baseline without blocking unrelated releases. Review the artifact and fix new issues; if a known issue needs a temporary exception, record the exact page, axe rule, reason, owner, and removal condition in the repository before adding suppressions.
- Browser requests to hosts other than the local test server are blocked. External link status and remote services are not tested.
- Reports are generated in the pull request workflow only; the check never publishes or deploys site content.

The initial callers are `fantastiq-labs`, `fantastiqmusic`, and `fantastiq-net`. Run each caller workflow on a sample pull request and inspect its report artifact before treating the check as operational.
