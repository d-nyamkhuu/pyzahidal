from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
TAG_PATTERN = re.compile(r"^v(?P<version>\d+\.\d+\.\d+(?:[A-Za-z0-9.\-_]+)?)$")


def project_version(pyproject_path: Path = PYPROJECT) -> str:
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def validate_tag(tag: str) -> str:
    match = TAG_PATTERN.fullmatch(tag)
    if not match:
        raise ValueError("release tags must look like vX.Y.Z")
    return match.group("version")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate that a git tag matches the package version.")
    parser.add_argument("tag", help="Release tag, for example v0.1.0")
    args = parser.parse_args(argv)

    package_version = project_version()
    tag_version = validate_tag(args.tag)
    if package_version != tag_version:
        print(
            f"Tag version {tag_version!r} does not match pyproject version {package_version!r}.",
            file=sys.stderr,
        )
        return 1

    print(f"Release tag {args.tag} matches package version {package_version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
