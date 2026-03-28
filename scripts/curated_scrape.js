const { execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const defaultHrefs = [
  "/components/marketing/logos#basic-logo-cloud",
  "/components/marketing/heroes#hero-block-overlay",
  "/components/marketing/coupons#card-coupons",
  "/components/marketing/cta#cta-with-background-image",
  "/components/marketing/bento-grids#bento-grid-with-images-and-details",
  "/components/marketing/footers#footer-with-top-background-image-and-content-bottom",
  "/components/marketing/heroes#hero-with-overlay-gradient",
  "/components/marketing/headers#header-with-logo-and-menu",
  "/components/marketing/bento-grids#bento-grid-with-3-columns-and-padded-images",
  "/components/marketing/feature#feature-with-double-tall-background-images",
  "/components/marketing/heroes#hero-with-overlapped-image",
  "/components/marketing/heroes",
  "/components/marketing/bento-grids",
  "/components/marketing/cta",
  "/components/marketing/images",
  "/components/marketing/feature",
  "/components/marketing/coupons",
  "/components/marketing/stats",
  "/components/marketing/logos",
  "/components/marketing/headers",
  "/components/marketing/footers",
  "/components/marketing/social",
  "/components/marketing/blog",
  "/components/marketing/content",
  "/components/marketing/faq",
  "/components/marketing/team",
  "/components/marketing/testimonials",
  "/components/marketing/timelines",
  "/components/marketing/pricing",
  "/components/ecommerce/product-lists",
  "/components/ecommerce/product-detail",
  "/components/ecommerce/product-features",
  "/components/ecommerce/category-previews",
  "/components/ecommerce/shopping-cart",
  "/components/ecommerce/reviews",
  "/components/ecommerce/order-summary",
  "/components/ui-elements/containers",
  "/components/ui-elements/grids",
  "/components/ui-elements/spacing",
  "/components/ui-elements/buttons",
  "/components/ui-elements/pills",
  "/components/ui-elements/avatars",
  "/components/ui-elements/alerts",
  "/components/ui-elements/navigation",
  "/components/ui-elements/progress-bars",
  "/components/ui-elements/data-tables",
];

const cliHrefs = process.argv.slice(2);
const hrefs = cliHrefs.length > 0 ? cliHrefs : defaultHrefs;
const uniqueHrefs = [...new Set(hrefs)];
const sourceBaseUrl = process.env.SOURCE_BASE_URL || "https://example.com";
const sessionArgs = ["--session", "curated-scrape"];
const env = {
  ...process.env,
  AGENT_BROWSER_SOCKET_DIR: "/tmp/agent-browser-curated",
  AGENT_BROWSER_DEFAULT_TIMEOUT: "60000",
};
const evalScript = fs.readFileSync(path.join(__dirname, "curated_eval.js"), "utf8");

function runAgent(args, input) {
  return execFileSync("agent-browser", [...sessionArgs, ...args], {
    input,
    encoding: "utf8",
    maxBuffer: 100 * 1024 * 1024,
    env,
    stdio: ["pipe", "pipe", "pipe"],
  });
}

function tryRun(args, input) {
  try {
    return { ok: true, output: runAgent(args, input) };
  } catch (error) {
    return { ok: false, error };
  }
}

function normalizeJsonOutput(output) {
  const parsed = JSON.parse(output);
  return typeof parsed === "string" ? JSON.parse(parsed) : parsed;
}

function sanitizeFilePart(value) {
  return value.replace(/[^a-z0-9._-]+/gi, "-").replace(/^-+|-+$/g, "").toLowerCase();
}

tryRun(["close"]);

const results = [];
for (const [index, href] of uniqueHrefs.entries()) {
  const url = `${sourceBaseUrl}${href}`;
  console.error(`[${index + 1}/${uniqueHrefs.length}] ${url}`);

  let opened = tryRun(["open", url]);
  if (!opened.ok) {
    console.error(`retry open for ${url}`);
    tryRun(["close"]);
    opened = tryRun(["open", url]);
  }

  if (!opened.ok) {
    results.push({
      href,
      pageUrl: url,
      error: opened.error.stderr || opened.error.message,
      sections: [],
    });
    continue;
  }

  tryRun(["wait", "--load", "networkidle"]);
  tryRun(["wait", "1200"]);

  const extracted = tryRun(["eval", "--stdin"], evalScript);
  if (!extracted.ok) {
    results.push({
      href,
      pageUrl: url,
      error: extracted.error.stderr || extracted.error.message,
      sections: [],
    });
    continue;
  }

  try {
    const normalized = normalizeJsonOutput(extracted.output);
    normalized.sections = (normalized.sections || []).map((section) => ({
      ...section,
      fileSlug: sanitizeFilePart(
        `${href.split("/").pop() || "component"}-${section.slug || section.heading || "section"}`,
      ),
    }));
    results.push({ href, ...normalized });
  } catch (error) {
    results.push({
      href,
      pageUrl: url,
      parseError: error.message,
      raw: extracted.output,
      sections: [],
    });
  }
}

tryRun(["close"]);

const output = {
  scrapedAt: new Date().toISOString(),
  source: sourceBaseUrl,
  requestedCount: hrefs.length,
  uniqueHrefCount: uniqueHrefs.length,
  pages: results,
};

const outPath = path.join(process.cwd(), "curated_components_export.json");
fs.writeFileSync(outPath, JSON.stringify(output, null, 2));
console.log(JSON.stringify({ outPath, uniqueHrefCount: uniqueHrefs.length, pagesSaved: results.length }, null, 2));
