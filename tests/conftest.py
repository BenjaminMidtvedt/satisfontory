from __future__ import annotations

from pathlib import Path

import freetype
import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def font_path(project_root: Path) -> Path:
    return project_root / "fonts" / "Roboto-Medium.ttf"


@pytest.fixture()
def font_face(font_path: Path) -> freetype.Face:
    return freetype.Face(str(font_path))
