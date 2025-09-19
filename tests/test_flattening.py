from __future__ import annotations

import math

from parser.contours import FTContour
from parser.flattening import flatten_contour


def _has_point(points, target, *, tol=1e-9):
    return any(abs(point[0] - target[0]) <= tol and abs(point[1] - target[1]) <= tol for point in points)


def test_flatten_contour_with_line_segments() -> None:
    contour = FTContour(points=[(0.0, 0.0), (3.0, 0.0)], on_curve=[True, True])
    result = flatten_contour(contour, tags=[1, 1], min_segment_length=0.5)
    assert result[0] == result[-1] == (0.0, 0.0)
    assert _has_point(result, (3.0, 0.0))
    assert len(result) > 5


def test_flatten_contour_with_quadratics_and_midpoints() -> None:
    contour = FTContour(points=[(0.0, 0.0), (1.0, 2.0), (2.0, 0.0), (3.0, 2.0)], on_curve=[True, False, False, True])
    tags = [1, 0, 0, 1]
    result = flatten_contour(contour, tags, min_segment_length=0.5)
    assert result[0] == result[-1] == (0.0, 0.0)
    assert _has_point(result, (3.0, 2.0))
    assert len(result) > 10


def test_flatten_contour_with_implicit_anchor() -> None:
    contour = FTContour(points=[(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)], on_curve=[False, False, False])
    tags = [0, 0, 0]
    result = flatten_contour(contour, tags, min_segment_length=0.5)
    assert result[0] == result[-1] == (1.0, 0.0)
    assert len(result) > 3


def test_flatten_contour_with_cubic_segments() -> None:
    contour = FTContour(points=[(0.0, 0.0), (1.0, 1.5), (2.0, 0.0), (3.0, 1.5), (4.0, 0.0)], on_curve=[True, False, False, False, True])
    tags = [1, 2, 2, 2, 1]
    result = flatten_contour(contour, tags, min_segment_length=0.4)
    assert result[0] == result[-1] == (0.0, 0.0)
    assert _has_point(result, (4.0, 0.0))
    assert len(result) > 10


def test_flatten_contour_handles_cubic_starting_control_point() -> None:
    contour = FTContour(points=[(1.0, 1.0), (0.0, 0.0), (2.0, 0.0)], on_curve=[False, True, False])
    tags = [2, 1, 2]
    result = flatten_contour(contour, tags, min_segment_length=0.5)
    assert result[0] == result[-1] == (0.0, 0.0)
    assert len(result) >= 2


def test_flatten_contour_rejects_invalid_tags() -> None:
    contour = FTContour(points=[(0.0, 0.0)], on_curve=[True])
    try:
        flatten_contour(contour, tags=[], min_segment_length=1.0)
    except ValueError as exc:
        assert "Tags length" in str(exc)
    else:
        raise AssertionError("Expected ValueError for mismatched tags")


def test_flatten_contour_handles_empty_input() -> None:
    contour = FTContour(points=[], on_curve=[])
    assert flatten_contour(contour, tags=[], min_segment_length=1.0) == []


def test_min_segment_length_controls_sampling_density() -> None:
    contour = FTContour(points=[(0.0, 0.0), (3.0, 0.0)], on_curve=[True, True])
    dense = flatten_contour(contour, tags=[1, 1], min_segment_length=0.5)
    sparse = flatten_contour(contour, tags=[1, 1], min_segment_length=2.0)
    assert len(dense) > len(sparse)
    assert dense[0] == dense[-1] == (0.0, 0.0)
    assert sparse[0] == sparse[-1] == (0.0, 0.0)
    assert _has_point(dense, (3.0, 0.0))
    assert _has_point(sparse, (3.0, 0.0))
    assert math.isclose(sum(point[0] for point in dense), sum(point[0] for point in reversed(dense)))
