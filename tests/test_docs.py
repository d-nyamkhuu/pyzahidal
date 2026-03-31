from __future__ import annotations

import json
import re
import subprocess
import sys
import types
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pyzahidal
from scripts.capture_docs_screenshots import (
    README_SCREENSHOT_SPECS,
    VIEWPORT,
    build_curated_visual_report,
    capture_screenshots,
    capture_tight_screenshot,
    readme_screenshot_targets,
    _visible_bounds_clip,
)
from scripts import docs as docs_cli
from scripts.generate_docs import (
    ALIASES,
    EXAMPLES,
    SKIPPED_EXPORTS,
    _build_curated_component,
    _curated_code_snippet,
    curated_examples,
    generate,
    infer_preview_theme,
    make_inventory,
    published_asset_path,
    screenshot_markup,
)


def canonical_exports() -> set[str]:
    return {name for name in pyzahidal.__all__ if name not in SKIPPED_EXPORTS}


def test_docs_inventory_covers_public_components_and_templates():
    inventory_names = {entry["name"] for entry in make_inventory()}
    assert inventory_names == canonical_exports()


def test_docs_examples_exist_for_every_documented_item():
    assert set(EXAMPLES) == canonical_exports()


def test_docs_generation_writes_pages_and_assets(tmp_path: Path):
    inventory = generate(tmp_path)
    assert inventory

    components_page = tmp_path / "generated" / "components.md"
    examples_page = tmp_path / "generated" / "examples.md"
    templates_page = tmp_path / "generated" / "templates.md"
    themes_page = tmp_path / "generated" / "themes.md"
    inventory_path = tmp_path / "generated" / "api-inventory.json"

    for path in (components_page, examples_page, templates_page, themes_page, inventory_path):
        assert path.exists()
        assert path.read_text(encoding="utf-8")

    sample_entry = inventory[0]
    preview_path = tmp_path / sample_entry["example_path"]
    assert preview_path.exists()
    assert "<!doctype html>" in preview_path.read_text(encoding="utf-8")

    parsed_inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    assert parsed_inventory[0]["signature"]
    assert parsed_inventory[0]["options"]


def test_authored_guide_pages_exist_and_cover_beginner_flow():
    index_page = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    quickstart_page = (ROOT / "docs" / "quickstart.md").read_text(encoding="utf-8")
    concepts_page = (ROOT / "docs" / "core-concepts.md").read_text(encoding="utf-8")
    recipes_page = (ROOT / "docs" / "recipes.md").read_text(encoding="utf-8")
    mkdocs_config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")

    assert "# Start Here" in index_page
    assert "[Quickstart](quickstart.md)" in index_page
    assert "# Quickstart" in quickstart_page
    assert "EmailDocument" in quickstart_page
    assert "# Core Concepts" in concepts_page
    assert "document shell" in concepts_page.lower()
    assert "# Recipes" in recipes_page
    assert "marketing email" in recipes_page.lower()
    assert "Start Here: index.md" in mkdocs_config
    assert "Reference:" in mkdocs_config


def test_components_page_contains_signature_code_and_preview(tmp_path: Path):
    generate(tmp_path)
    page = (tmp_path / "generated" / "components.md").read_text(encoding="utf-8")
    assert "Signature:" in page
    assert "Best for: custom composition" in page
    assert "```python" in page
    assert '<iframe class="docs-preview-frame" src="../../assets/examples/' in page
    assert 'srcdoc="&lt;!doctype html&gt;' in page
    assert "Screenshot:" not in page
    assert "Screenshot asset not generated yet." not in page


def test_theme_showcase_assets_are_generated(tmp_path: Path):
    generate(tmp_path)
    showcase = tmp_path / "assets" / "examples" / "theme-hero-default.html"
    assert showcase.exists()
    assert "<!doctype html>" in showcase.read_text(encoding="utf-8")


def test_curated_examples_are_generated_without_local_asset_dependencies(tmp_path: Path):
    inventory = generate(tmp_path)
    curated_entries = [entry for entry in inventory if entry.get("kind") == "curated_example"]
    assert len(curated_entries) == 32

    examples_page = (tmp_path / "generated" / "examples.md").read_text(encoding="utf-8")
    assert "# Examples" in examples_page
    assert "## Product announcement" in examples_page
    assert "## Newsletter and editorial" in examples_page
    assert "## Promotion and campaigns" in examples_page
    assert "## Ecommerce and order flows" in examples_page
    assert examples_page.count("Rendered result:") == 32
    assert "CURATED_HTML" not in examples_page
    assert "raw(CURATED_HTML)" not in examples_page
    assert "curated_components_export.json" not in examples_page
    assert "Source: [" not in examples_page
    assert "logos-basic-logo-cloud-basic-logo-cloud" not in examples_page
    assert "heroes-hero-block-overlay-hero-block-overlay" not in examples_page
    assert "assets/curated-images/" not in examples_page
    assert "../curated-images/" not in examples_page

    for entry in curated_entries:
        preview = tmp_path / entry["example_path"]
        html = preview.read_text(encoding="utf-8")
        assert "assets.example.com" not in html
        assert "CURATED_HTML" not in html
        assert "assets/curated-images/" not in html
        assert "../curated-images/" not in html
        assert "source_example_path" not in entry


def test_generated_docs_examples_use_explicit_code_no_placeholders(tmp_path: Path):
    generate(tmp_path)
    components_page = (tmp_path / "generated" / "components.md").read_text(encoding="utf-8")
    templates_page = (tmp_path / "generated" / "templates.md").read_text(encoding="utf-8")
    examples_page = (tmp_path / "generated" / "examples.md").read_text(encoding="utf-8")
    themes_page = (tmp_path / "generated" / "themes.md").read_text(encoding="utf-8")

    for page in (components_page, templates_page, examples_page, themes_page):
        assert "data:image/svg+xml;utf8,..." not in page
        assert not re.search(r"\b(component|doc)\s*=\s*[A-Za-z_]+\(\s*\.\.\.", page)
        assert "Screenshot:" not in page
        assert "Screenshot asset not generated yet." not in page


def test_curated_logos_example_code_matches_rendered_logo_strip(tmp_path: Path):
    generate(tmp_path)
    examples_page = (tmp_path / "generated" / "examples.md").read_text(encoding="utf-8")
    assert "Inline(" in examples_page
    assert "Supported payment services" in examples_page
    assert "Category: `Logos`" in examples_page
    assert "curated-logo-" not in examples_page


def test_generated_docs_examples_do_not_reference_local_curated_asset_paths(tmp_path: Path):
    generate(tmp_path)
    components_page = (tmp_path / "generated" / "components.md").read_text(encoding="utf-8")
    templates_page = (tmp_path / "generated" / "templates.md").read_text(encoding="utf-8")
    examples_page = (tmp_path / "generated" / "examples.md").read_text(encoding="utf-8")

    for page in (components_page, templates_page, examples_page):
        assert "assets/curated-images/" not in page
        assert "../curated-images/" not in page


def test_themes_page_omits_screenshot_notes(tmp_path: Path):
    generate(tmp_path)
    themes_page = (tmp_path / "generated" / "themes.md").read_text(encoding="utf-8")
    assert "Screenshot blocks appear automatically" not in themes_page


def test_curated_examples_page_avoids_generic_fallback_snippets(tmp_path: Path):
    generate(tmp_path)
    examples_page = (tmp_path / "generated" / "examples.md").read_text(encoding="utf-8")
    assert not re.search(
        r"from pyzahidal import Button, Heading, Section, Stack, Text.*?Button\('Learn more'",
        examples_page,
        flags=re.DOTALL,
    )


def test_curated_generator_category_coverage_stays_in_sync():
    source = {
        "headings": ["Title", "Secondary"],
        "paragraphs": ["Body copy", "Supporting copy"],
        "links": [{"href": "#", "label": "Open"}, {"href": "#details", "label": "Details"}],
        "images": [{"src": "assets/curated-images/example.png", "alt": "Example"}],
        "prices": ["$29"],
        "percents": ["42%"],
        "versions": ["v1.0.0"],
        "dates": ["19 Jan"],
        "table_headers": ["Name", "Status", "Action"],
        "table_rows": [["Record", "Healthy", "Manage"]],
        "groups": [{"heading": "Card", "paragraphs": ["Body copy"]}],
        "layout": "grid",
        "layout_flags": {"button_count": 2, "card_count": 3, "has_split_columns": False, "has_grid": True, "has_table": True, "small_image_count": 1, "table_columns": 3, "table_rows": 1},
    }
    build_component = _build_curated_component("Data Tables", "With logos and action links", "default", source)
    snippet = _curated_code_snippet("Data Tables", "With logos and action links", "default", source)
    assert build_component.render()
    assert "DataTable(" in snippet


def test_curated_examples_render_without_component_repr_leaks(tmp_path: Path):
    inventory = generate(tmp_path)
    curated_entries = [entry for entry in inventory if entry.get("kind") == "curated_example"]
    for entry in curated_entries:
        html = (tmp_path / entry["example_path"]).read_text(encoding="utf-8")
        assert "Button(tag=" not in html
        assert "AvatarGroup(" not in html


def test_curated_richest_grid_variant_selected(tmp_path: Path):
    inventory = generate(tmp_path)
    grid_entries = [entry for entry in inventory if entry.get("kind") == "curated_example" and entry.get("category") == "Grids"]
    assert len(grid_entries) == 1
    assert grid_entries[0]["name"] == "One column grid"
    assert grid_entries[0]["example_slug"] == "curated-one-column-grid"


def test_curated_examples_page_uses_richer_components_for_complex_examples(tmp_path: Path):
    generate(tmp_path)
    page = (tmp_path / "generated" / "examples.md").read_text(encoding="utf-8")
    assert "curated-hero-block-overlay" in page and "Surface(" in page
    assert "curated-split-product-detail" in page and "ProductDetail(" in page
    assert "curated-avatar-with-details" in page and "Avatar(" in page
    assert "curated-data-tables-basic" in page and "DataTable(" in page
    assert "Related docs:" in page


def test_curated_static_examples_render_expected_layout_markers(tmp_path: Path):
    generate(tmp_path)

    header_html = (tmp_path / "assets" / "examples" / "curated-header-with-logo-and-menu.html").read_text(encoding="utf-8")
    assert 'width:52%' in header_html
    assert 'width:48%' in header_html
    assert "Purpose-built email components" in header_html

    social_html = (tmp_path / "assets" / "examples" / "curated-social-simple-social-logos-row.html").read_text(encoding="utf-8")
    assert "LinkedIn" in social_html
    assert "GitHub" in social_html

    team_html = (tmp_path / "assets" / "examples" / "curated-team-2-column-team-cards.html").read_text(encoding="utf-8")
    assert "Team member" not in team_html
    assert "border-radius" in team_html
    assert "Product Design" in team_html

    bento_html = (tmp_path / "assets" / "examples" / "curated-bento-grid-with-images-and-details.html").read_text(encoding="utf-8")
    assert "font-size:48px" not in bento_html
    assert "Live dashboards" in bento_html
    assert "Flow control" in bento_html


def test_curated_visual_report_uses_generated_screenshots(tmp_path: Path):
    generate(tmp_path)
    inventory = json.loads((tmp_path / "generated" / "api-inventory.json").read_text(encoding="utf-8"))
    curated_entries = [entry for entry in inventory if entry.get("kind") == "curated_example"]
    screenshot_root = tmp_path / "assets" / "screenshots"
    screenshot_root.mkdir(parents=True, exist_ok=True)

    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0cIDATx\x9cc```\xf8\xff\xff?\x00\x05\xfe\x02\xfeA^\x1b\xe7\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    for entry in curated_entries:
        (tmp_path / entry["screenshot_path"]).write_bytes(png)

    report = build_curated_visual_report(tmp_path)
    assert report["summary"]["total_examples"] == 32
    assert report["summary"]["failing_examples"] == 0
    assert not report["failing"]
    assert report["entries"][0]["generated_screenshot_path"].startswith("assets/screenshots/")


def test_readme_screenshot_targets_point_to_curated_examples(tmp_path: Path):
    generate(tmp_path)
    targets = readme_screenshot_targets(tmp_path)

    assert [path.name for _, path in targets] == [filename for _, filename in README_SCREENSHOT_SPECS]
    for preview_path, screenshot_path in targets:
        assert preview_path.exists()
        assert preview_path.name.startswith("curated-")
        assert screenshot_path.parent == tmp_path.parent / ".github" / "readme"


def test_visible_bounds_clip_ignores_hidden_nodes():
    clip = _visible_bounds_clip(
        [
            {"visible": False, "left": 10, "top": 10, "right": 120, "bottom": 40},
            {"visible": True, "left": 20, "top": 30, "right": 200, "bottom": 180},
        ]
    )

    assert clip == {
        "x": 8.0,
        "y": 18.0,
        "width": 204.0,
        "height": 174.0,
    }


def test_visible_bounds_clip_applies_margin_and_clamps_to_origin():
    clip = _visible_bounds_clip(
        [
            {"visible": True, "left": 6, "top": 7, "right": 45, "bottom": 70},
            {"visible": True, "left": 40, "top": 55, "right": 100, "bottom": 125},
        ]
    )

    assert clip == {
        "x": 0.0,
        "y": 0.0,
        "width": 112.0,
        "height": 137.0,
    }


def test_visible_bounds_clip_falls_back_to_viewport_when_nothing_visible():
    assert _visible_bounds_clip([{"visible": False, "left": None, "top": None, "right": None, "bottom": None}]) == {
        "x": 0.0,
        "y": 0.0,
        "width": float(VIEWPORT["width"]),
        "height": float(VIEWPORT["height"]),
    }


def test_capture_tight_screenshot_uses_clip():
    page = mock.Mock()
    page.evaluate.return_value = [
        {"visible": True, "left": 20, "top": 30, "right": 200, "bottom": 180},
        {"visible": False, "left": None, "top": None, "right": None, "bottom": None},
    ]
    destination = Path("/tmp/sample.png")

    capture_tight_screenshot(page, destination)

    page.screenshot.assert_called_once_with(
        path=str(destination),
        clip={
            "x": 8.0,
            "y": 18.0,
            "width": 204.0,
            "height": 174.0,
        },
    )
    screenshot_kwargs = page.screenshot.call_args.kwargs
    assert "full_page" not in screenshot_kwargs


def test_capture_screenshots_routes_all_calls_through_shared_helper(tmp_path: Path):
    generate(tmp_path)
    inventory = json.loads((tmp_path / "generated" / "api-inventory.json").read_text(encoding="utf-8"))
    expected_count = len(inventory) + 12 + len(README_SCREENSHOT_SPECS)

    page = mock.Mock()
    browser = mock.Mock()
    browser.new_page.return_value = page
    chromium = mock.Mock()
    chromium.launch.return_value = browser

    class _PlaywrightContext:
        def __enter__(self):
            return types.SimpleNamespace(chromium=chromium)

        def __exit__(self, exc_type, exc, tb):
            return False

    with (
        mock.patch.dict(sys.modules, {"playwright.sync_api": types.SimpleNamespace(sync_playwright=lambda: _PlaywrightContext())}),
        mock.patch("scripts.capture_docs_screenshots.capture_tight_screenshot") as capture_mock,
    ):
        report = capture_screenshots(tmp_path)

    assert report["summary"]["total_examples"] == 32
    browser.new_page.assert_called_once_with(viewport=VIEWPORT, device_scale_factor=1)
    assert page.goto.call_count == expected_count
    assert capture_mock.call_count == expected_count
    assert not page.screenshot.called
    browser.close.assert_called_once()


def test_curated_examples_are_defined_statically():
    specs = curated_examples()
    assert len(specs) == 32
    assert len({spec.category for spec in specs}) == 32
    assert all(spec.slug.startswith("curated-") for spec in specs)
    assert all("assets.example.com" not in spec.code for spec in specs)


def test_themed_component_preview_uses_matching_document_theme(tmp_path: Path):
    generate(tmp_path)
    hero_preview = tmp_path / "assets" / "examples" / f"{EXAMPLES['Hero'].slug}.html"
    html = hero_preview.read_text(encoding="utf-8")
    assert f"background:{pyzahidal.THEMES['modern']['body_background']}" in html


def test_preview_theme_inference_reads_theme_from_example_code():
    assert infer_preview_theme(EXAMPLES["Button"].code) == "editorial"


def test_screenshot_markup_returns_image_when_asset_exists():
    docs_relative = "assets/screenshots/sample-test-docs.png"
    actual = ROOT / "docs" / docs_relative
    actual.parent.mkdir(parents=True, exist_ok=True)
    actual.write_bytes(b"png")
    try:
        assert screenshot_markup(docs_relative, "sample") == '<img alt="sample" src="assets/screenshots/sample-test-docs.png" />'
    finally:
        actual.unlink(missing_ok=True)


def test_published_asset_path_returns_root_relative_url():
    assert published_asset_path("assets/examples/hero.html") == "assets/examples/hero.html"
    assert published_asset_path("assets/examples/hero.html", page_depth=2) == "../../assets/examples/hero.html"
    assert published_asset_path("/assets/screenshots/hero.png", page_depth=2) == "../../assets/screenshots/hero.png"


def test_aliases_map_to_existing_canonical_entries():
    inventory_names = {entry["name"] for entry in make_inventory()}
    for target in ALIASES.values():
        assert target in inventory_names


def test_docs_pipeline_runs_generate_then_screenshots_then_build(tmp_path: Path):
    events: list[object] = []

    def fake_generate(output_root: Path):
        events.append(("generate", output_root))
        return [{"name": "Button"}]

    def fake_capture(output_root: Path):
        events.append(("screenshots", output_root))
        return {"summary": {"total_examples": 0}}

    def fake_build(root: Path):
        events.append(("build", root))

    with (
        mock.patch.object(docs_cli, "generate", side_effect=fake_generate),
        mock.patch.object(docs_cli, "capture_screenshots", side_effect=fake_capture),
        mock.patch.object(docs_cli, "build_mkdocs_site", side_effect=fake_build),
    ):
        code = docs_cli.run_docs_pipeline(root=tmp_path)

    assert code == 0
    assert events == [
        ("generate", tmp_path / "docs"),
        ("screenshots", tmp_path / "docs"),
        ("build", tmp_path),
    ]


def test_docs_pipeline_skips_screenshots_when_requested(tmp_path: Path):
    events: list[object] = []

    with (
        mock.patch.object(docs_cli, "generate", side_effect=lambda output_root: events.append(("generate", output_root)) or []),
        mock.patch.object(docs_cli, "capture_screenshots", side_effect=lambda output_root: events.append(("screenshots", output_root))),
        mock.patch.object(docs_cli, "build_mkdocs_site", side_effect=lambda root: events.append(("build", root))),
    ):
        code = docs_cli.run_docs_pipeline(root=tmp_path, screenshots=False)

    assert code == 0
    assert events == [
        ("generate", tmp_path / "docs"),
        ("build", tmp_path),
    ]


def test_docs_pipeline_skips_build_when_requested(tmp_path: Path):
    events: list[object] = []

    with (
        mock.patch.object(docs_cli, "generate", side_effect=lambda output_root: events.append(("generate", output_root)) or []),
        mock.patch.object(docs_cli, "capture_screenshots", side_effect=lambda output_root: events.append(("screenshots", output_root)) or {}),
        mock.patch.object(docs_cli, "build_mkdocs_site", side_effect=lambda root: events.append(("build", root))),
    ):
        code = docs_cli.run_docs_pipeline(root=tmp_path, build=False)

    assert code == 0
    assert events == [
        ("generate", tmp_path / "docs"),
        ("screenshots", tmp_path / "docs"),
    ]


def test_docs_pipeline_stops_on_screenshot_failure(tmp_path: Path):
    events: list[object] = []

    with (
        mock.patch.object(docs_cli, "generate", side_effect=lambda output_root: events.append(("generate", output_root)) or []),
        mock.patch.object(docs_cli, "capture_screenshots", side_effect=RuntimeError("missing playwright")),
        mock.patch.object(docs_cli, "build_mkdocs_site", side_effect=lambda root: events.append(("build", root))),
    ):
        code = docs_cli.main(["--no-build"])

    assert code == 1
    assert events == [("generate", ROOT / "docs")]


def test_docs_pipeline_stops_on_build_failure(tmp_path: Path):
    events: list[object] = []

    with (
        mock.patch.object(docs_cli, "generate", side_effect=lambda output_root: events.append(("generate", output_root)) or []),
        mock.patch.object(docs_cli, "capture_screenshots", side_effect=lambda output_root: events.append(("screenshots", output_root)) or {}),
        mock.patch.object(docs_cli, "build_mkdocs_site", side_effect=subprocess.CalledProcessError(3, ["mkdocs", "build"])),
    ):
        code = docs_cli.main([])

    assert code == 3
    assert events == [
        ("generate", ROOT / "docs"),
        ("screenshots", ROOT / "docs"),
    ]
