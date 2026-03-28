from __future__ import annotations

import pytest

from scripts.check_release import project_version, validate_tag


def test_project_version_matches_current_pyproject() -> None:
    assert project_version() == "0.1.2"


def test_validate_tag_returns_stripped_version() -> None:
    assert validate_tag("v0.1.2") == "0.1.2"


def test_validate_tag_rejects_invalid_tags() -> None:
    with pytest.raises(ValueError):
        validate_tag("0.1.0")
