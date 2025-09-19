from __future__ import annotations

import numpy as np
import pytest

from parser.blueprint import Line, lines_to_world


def test_lines_to_world_converts_segments() -> None:
    lines = np.array([
        [[0.0, 0.0], [3.0, 4.0]],
        [[1.0, 1.0], [1.0, 1.0]],
    ], dtype=float)
    blueprint_lines = lines_to_world(lines)
    assert len(blueprint_lines) == 2
    assert isinstance(blueprint_lines[0], Line)
    assert pytest.approx(blueprint_lines[0].length) == 5.0
    assert blueprint_lines[1].length == 0.0
    assert blueprint_lines[1].rotation["w"] == 1.0
    assert blueprint_lines[1].rotation["z"] == 0.0


def test_lines_to_world_validates_shape() -> None:
    with pytest.raises(ValueError):
        lines_to_world(np.zeros((2, 3, 2)))
