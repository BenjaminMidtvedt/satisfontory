from __future__ import annotations

from shapely.geometry import Polygon

from parser.rectangles import (
    extend_backward,
    extend_forward,
    extend_rectangles,
    rectangles_along_polyline,
    remove_narrow_areas,
)


def build_rectangle() -> Polygon:
    return Polygon([(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0), (0.0, 0.0)])


def test_rectangles_along_polyline_basic() -> None:
    polyline = [(0.0, 0.0), (4.0, 0.0), (4.0, 3.0), (0.0, 3.0), (0.0, 0.0)]
    rectangles = rectangles_along_polyline(
        polyline,
        thickness=0.5,
        overlap=0.2,
        interior_is_right=False,
    )
    assert rectangles
    for rectangle in rectangles:
        assert rectangle.is_valid
        assert rectangle.area > 0.0


def test_rectangles_along_polyline_returns_empty_for_short_path() -> None:
    assert rectangles_along_polyline([(0.0, 0.0)], 0.5, 0.1, interior_is_right=True) == []


def test_remove_narrow_areas_flags_vertices() -> None:
    small_polyline = [(0.0, 0.0), (1.0, 0.0), (1.05, 0.3), (1.1, 0.0), (2.0, 0.0)]
    polygon = Polygon(small_polyline)
    updated, removed = remove_narrow_areas(
        small_polyline,
        polygon,
        thickness=0.6,
        overlap=0.5,
        interior_is_right=True,
    )
    assert removed
    for index in removed:
        assert 0 <= index < len(small_polyline)
    assert len(updated) < len(small_polyline)

    no_change, untouched = remove_narrow_areas(
        [(0.0, 0.0), (1.0, 0.0)],
        Polygon([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]),
        thickness=0.2,
        overlap=0.1,
        interior_is_right=False,
    )
    assert untouched == {0, 1}
    assert no_change == []


def test_extend_forward_and_backward() -> None:
    rectangle = build_rectangle()
    forward = extend_forward(rectangle, 1.0)
    backward = extend_backward(rectangle, 1.0)
    assert forward.bounds[2] > rectangle.bounds[2]
    assert backward.bounds[0] < rectangle.bounds[0]


def test_extend_rectangles_clips_to_glyph() -> None:
    glyph_polygon = Polygon([(-2.0, -1.0), (6.0, -1.0), (6.0, 2.0), (-2.0, 2.0)])
    base_rect = build_rectangle()
    shifted = Polygon([(5.0, 0.0), (6.0, 0.0), (6.0, 1.0), (5.0, 1.0), (5.0, 0.0)])
    extended = extend_rectangles(glyph_polygon, [base_rect, shifted], 1.0)
    assert extended[0].bounds[0] < base_rect.bounds[0]
    assert extended[0].bounds[2] > base_rect.bounds[2]

    assert abs(extended[1].bounds[2] - shifted.bounds[2]) <= 1e-9
    assert extended[1].bounds[0] < shifted.bounds[0]

    for rectangle in extended:
        assert glyph_polygon.covers(rectangle)
