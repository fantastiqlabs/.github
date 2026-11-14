#!/usr/bin/env node
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

const root = process.env.AXE_MODULES;
if (!root) throw new Error('AXE_MODULES must point to the installed audit packages.');
const requireFromPackages = require('node:module').createRequire(pathToFileURL(path.join(root, 'package.json')));
const { chromium } = requireFromPackages('playwright');
const AxeBuilder = requireFromPackages('@axe-core/playwright').default;

function argument(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

async function main() {
  const baseUrl = argument('--base-url');
  const pageList = argument('--pages');
  const reportPath = argument('--report');
  if (!baseUrl || !pageList || !reportPath) throw new Error('Usage: scan_accessibility.cjs --base-url URL --pages FILE --report FILE');
  const pages = fs.readFileSync(pageList, 'utf8').split(/\r?\n/).filter(Boolean);
  if (!pages.length) throw new Error('No HTML pages were provided.');

  const browser = await chromium.launch({ headless: true });
  const results = [];
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    await page.route('**/*', (route) => {
      const url = new URL(route.request().url());
      return url.origin === new URL(baseUrl).origin ? route.continue() : route.abort();
    });
    for (const route of pages) {
      const response = await page.goto(new URL(route, baseUrl).href, { waitUntil: 'networkidle', timeout: 20000 });
      if (!response || !response.ok()) throw new Error(`Could not load ${route}: HTTP ${response?.status() ?? 'no response'}`);
      const audit = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();
      results.push({ route, violations: audit.violations.map(({ id, impact, description, help, helpUrl, nodes }) => ({
        id, impact, description, help, helpUrl,
        nodes: nodes.map(({ target, failureSummary }) => ({ target, failureSummary })),
      })) });
    }
  } finally {
    await browser.close();
  }
  const summary = {
    standard: 'WCAG 2.1 A/AA axe-core rules',
    pagesScanned: results.length,
    violationCount: results.reduce((count, item) => count + item.violations.length, 0),
    results,
  };
  fs.mkdirSync(path.dirname(reportPath), { recursive: true });
  fs.writeFileSync(reportPath, `${JSON.stringify(summary, null, 2)}\n`);
  console.log(`Scanned ${summary.pagesScanned} pages; found ${summary.violationCount} accessibility violations.`);
  if (summary.violationCount) console.log('::warning::Review the accessibility report artifact; findings are report-only during initial rollout.');
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
