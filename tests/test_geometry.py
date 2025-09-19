from __future__ import annotations

import math

from parser.geometry import (
    add,
    norm,
    polygon_is_ccw,
    rotate90_ccw,
    rotate90_cw,
    scale,
    subtract,
    unit_vector,
)


def test_basic_vector_arithmetic() -> None:
    assert subtract((3.0, -2.0), (1.0, 4.0)) == (2.0, -6.0)
    assert add((1.5, -0.5), (0.5, 2.0)) == (2.0, 1.5)
    assert scale((3.0, -4.0), 0.5) == (1.5, -2.0)


def test_norm_and_unit_vector() -> None:
    vector = (3.0, 4.0)
    assert norm(vector) == 5.0
    unit = unit_vector(vector)
    assert unit == (3.0 / 5.0, 4.0 / 5.0)
    assert unit_vector((0.0, 0.0)) == (0.0, 0.0)


def test_rotations_and_orientation() -> None:
    assert rotate90_ccw((1.0, 2.0)) == (-2.0, 1.0)
    assert rotate90_cw((1.0, 2.0)) == (2.0, -1.0)

    ccw_square = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    assert polygon_is_ccw(ccw_square)
    cw_square = list(reversed(ccw_square))
    assert not polygon_is_ccw(cw_square)
    assert not polygon_is_ccw([(0.0, 0.0), (1.0, 0.0)])

    # Degenerate polygons with collinear points should still report orientation consistently.
    degenerate = [(0.0, 0.0), (2.0, 0.0), (4.0, 0.0)]
    assert not polygon_is_ccw(degenerate)

    # A rotated unit vector should retain unit length.
    rotated = rotate90_ccw(unit_vector((1.0, 0.0)))
    assert math.isclose(norm(rotated), 1.0)
