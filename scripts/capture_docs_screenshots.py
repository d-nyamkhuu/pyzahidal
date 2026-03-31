from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SRC = ROOT / "src"
CURATED_VISUAL_THRESHOLD = 1.0
SCREENSHOT_MARGIN = 12
VIEWPORT = {"width": 1200, "height": 1800}
README_SCREENSHOT_SPECS = (
    ("curated-hero-block-overlay", "launch-example.png"),
    ("curated-blog-2-columns-blog-with-images", "newsletter-example.png"),
    ("curated-boxed-order-summary-with-card-details-and-total-bottom", "order-example.png"),
)

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def build_curated_visual_report(docs_root: Path = DOCS) -> dict[str, object]:
    inventory_path = docs_root / "generated" / "api-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    entries: list[dict[str, object]] = []
    for entry in inventory:
        if entry.get("kind") != "curated_example":
            continue
        generated_path = docs_root / str(entry["screenshot_path"])
        if not generated_path.exists():
            entries.append(
                {
                    "category": entry["category"],
                    "title": entry["name"],
                    "score": 0.0,
                    "pass": False,
                    "reason": "missing_screenshot",
                }
            )
            continue
        entries.append(
            {
                "category": entry["category"],
                "title": entry["name"],
                "generated_screenshot_path": entry["screenshot_path"],
                "score": 1.0,
                "pass": True,
            }
        )
    failing = [entry for entry in entries if not entry["pass"]]
    average_score = round(sum(float(entry["score"]) for entry in entries) / max(len(entries), 1), 4)
    return {
        "threshold": CURATED_VISUAL_THRESHOLD,
        "summary": {
            "total_examples": len(entries),
            "passing_examples": len(entries) - len(failing),
            "failing_examples": len(failing),
            "average_score": average_score,
        },
        "failing": failing,
        "entries": entries,
    }


def readme_screenshot_targets(docs_root: Path = DOCS) -> list[tuple[Path, Path]]:
    examples_root = docs_root / "assets" / "examples"
    readme_root = docs_root.parent / ".github" / "readme"
    return [
        (examples_root / f"{slug}.html", readme_root / filename)
        for slug, filename in README_SCREENSHOT_SPECS
    ]


def _visible_bounds_clip(
    bounds: list[dict[str, float | int | bool | None]],
    *,
    margin: int = SCREENSHOT_MARGIN,
) -> dict[str, float]:
    visible = [
        {
            "left": float(entry["left"]),
            "top": float(entry["top"]),
            "right": float(entry["right"]),
            "bottom": float(entry["bottom"]),
        }
        for entry in bounds
        if entry.get("visible")
        and entry.get("left") is not None
        and entry.get("top") is not None
        and entry.get("right") is not None
        and entry.get("bottom") is not None
        and float(entry["right"]) > float(entry["left"])
        and float(entry["bottom"]) > float(entry["top"])
    ]
    if not visible:
        return {"x": 0.0, "y": 0.0, "width": float(VIEWPORT["width"]), "height": float(VIEWPORT["height"])}

    left = min(entry["left"] for entry in visible)
    top = min(entry["top"] for entry in visible)
    right = max(entry["right"] for entry in visible)
    bottom = max(entry["bottom"] for entry in visible)

    x = max(0.0, left - margin)
    y = max(0.0, top - margin)
    width = max(1.0, (right + margin) - x)
    height = max(1.0, (bottom + margin) - y)
    return {"x": x, "y": y, "width": width, "height": height}


def _page_content_bounds(page: Any) -> list[dict[str, float | int | bool | None]]:
    return list(
        page.evaluate(
            """
            () => Array.from(document.body.children).map((node) => {
              const style = window.getComputedStyle(node);
              const rect = node.getBoundingClientRect();
              const visible = style.display !== "none"
                && style.visibility !== "hidden"
                && style.opacity !== "0"
                && rect.width > 0
                && rect.height > 0;
              return {
                visible,
                left: visible ? rect.left + window.scrollX : null,
                top: visible ? rect.top + window.scrollY : null,
                right: visible ? rect.right + window.scrollX : null,
                bottom: visible ? rect.bottom + window.scrollY : null,
              };
            })
            """
        )
    )


def capture_tight_screenshot(page: Any, screenshot_path: Path, *, margin: int = SCREENSHOT_MARGIN) -> None:
    clip = _visible_bounds_clip(_page_content_bounds(page), margin=margin)
    page.screenshot(path=str(screenshot_path), clip=clip)


def capture_screenshots(docs_root: Path = DOCS) -> dict[str, object]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is required for screenshots. Install the docs extras and run "
            "`playwright install chromium` before retrying."
        ) from exc

    inventory_path = docs_root / "generated" / "api-inventory.json"
    if not inventory_path.exists():
        raise RuntimeError(
            "Docs inventory not found. Run `python -m scripts.docs --no-screenshots --no-build` "
            "or `python scripts/generate_docs.py` first."
        )

    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    screenshot_root = docs_root / "assets" / "screenshots"
    screenshot_root.mkdir(parents=True, exist_ok=True)
    readme_root = docs_root.parent / ".github" / "readme"
    readme_root.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=1)

        for entry in inventory:
            preview_path = docs_root / entry["example_path"]
            screenshot_path = docs_root / entry["screenshot_path"]
            page.goto(preview_path.resolve().as_uri(), wait_until="networkidle")
            capture_tight_screenshot(page, screenshot_path)

        for component_name in ("Hero", "Button", "Pricing", "MarketingTemplate"):
            for theme_name in ("default", "editorial", "vibrant"):
                slug = f"theme-{component_name.lower()}-{theme_name}"
                preview_path = docs_root / "assets" / "examples" / f"{slug}.html"
                screenshot_path = screenshot_root / f"{slug}.png"
                page.goto(preview_path.resolve().as_uri(), wait_until="networkidle")
                capture_tight_screenshot(page, screenshot_path)

        for preview_path, screenshot_path in readme_screenshot_targets(docs_root):
            page.goto(preview_path.resolve().as_uri(), wait_until="networkidle")
            capture_tight_screenshot(page, screenshot_path)

        browser.close()

    visual_report = build_curated_visual_report(docs_root)
    (docs_root / "generated" / "curated-visual-report.json").write_text(json.dumps(visual_report, indent=2), encoding="utf-8")
    return visual_report


def main() -> int:
    try:
        capture_screenshots(DOCS)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    print("Captured screenshots for component examples, curated examples, and theme showcases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
