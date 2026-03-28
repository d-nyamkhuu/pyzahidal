from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.capture_docs_screenshots import capture_screenshots
from scripts.generate_docs import generate


def build_mkdocs_site(root: Path = ROOT) -> None:
    subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "-f", str(root / "mkdocs.yml")],
        check=True,
        cwd=root,
    )


def run_docs_pipeline(*, screenshots: bool = True, build: bool = True, root: Path = ROOT) -> int:
    docs_root = root / "docs"

    print("[docs] Generating docs content...")
    inventory = generate(docs_root)
    print(f"[docs] Generated docs for {len(inventory)} public items.")

    if screenshots:
        print("[docs] Capturing screenshots...")
        capture_screenshots(docs_root)
        print("[docs] Captured screenshots.")

    if build:
        print("[docs] Building MkDocs site...")
        build_mkdocs_site(root)
        print("[docs] Built MkDocs site.")

    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the docs site in the correct order: content, screenshots, then MkDocs build."
    )
    parser.add_argument(
        "--no-screenshots",
        action="store_true",
        help="Skip Playwright screenshot capture.",
    )
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="Skip the final `mkdocs build` step.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return run_docs_pipeline(
            screenshots=not args.no_screenshots,
            build=not args.no_build,
        )
    except subprocess.CalledProcessError as exc:
        print(f"[docs] MkDocs build failed with exit code {exc.returncode}.", file=sys.stderr)
        return exc.returncode or 1
    except RuntimeError as exc:
        print(f"[docs] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
