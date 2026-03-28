(() => {
  const requestedHash = location.hash.replace(/^#/, "");
  const pageHeading = document.querySelector("h1")?.textContent?.trim() || document.title;
  const headings = Array.from(document.querySelectorAll("h2"));
  const iframes = Array.from(document.querySelectorAll("iframe"));

  const sections = headings
    .map((heading, index) => {
      const link = heading.querySelector("a[href]");
      const iframe = iframes[index] || null;

      let html = null;
      try {
        const doc = iframe?.contentDocument || null;
        html = doc ? `${doc.head?.innerHTML || ""}${doc.body?.innerHTML || ""}` : null;
      } catch {
        html = null;
      }

      const href = link?.getAttribute("href") || null;
      const slug = href && href.includes("#") ? href.split("#")[1] : null;

      return {
        heading: heading.textContent.replace(/\s+Preview$/, "").trim(),
        previewHeading: heading.textContent.trim(),
        slug,
        linkHref: href,
        iframeHtml: html,
      };
    })
    .filter((section) => section.iframeHtml);

  const filtered = requestedHash
    ? sections.filter((section) => section.slug === requestedHash)
    : sections;

  return JSON.stringify({
    pageUrl: location.href,
    pageHeading,
    requestedHash: requestedHash || null,
    sectionCount: filtered.length,
    sections: filtered,
  });
})();
