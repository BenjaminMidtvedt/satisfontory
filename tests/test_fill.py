from __future__ import annotations

from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiLineString,
    Point,
    Polygon,
)

from parser.fill import (
    fill_polygon_with_rectangles,
    intersect_spans,
    iter_line_segments_from_intersection,
    _generate_subdivisions,
)


def test_iter_line_segments_handles_various_geometries() -> None:
    square = Polygon([(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)])

    vertical = iter_line_segments_from_intersection(square.intersection(LineString([(2.0, -1.0), (2.0, 5.0)])))
    assert vertical == [(0.0, 4.0)]

    horizontal = iter_line_segments_from_intersection(square.intersection(LineString([(-1.0, 2.0), (5.0, 2.0)])))
    assert horizontal == [(0.0, 4.0)]

    multiline = MultiLineString([[(0.0, 1.0), (4.0, 1.0)], [(1.0, 0.0), (1.0, 4.0)]])
    spans = iter_line_segments_from_intersection(multiline)
    assert spans == [(0.0, 4.0), (0.0, 4.0)]

    collection = GeometryCollection([LineString([(0.0, 0.0), (4.0, 0.0)]), Point(0.0, 0.0)])
    assert iter_line_segments_from_intersection(collection) == [(0.0, 4.0)]


def test_intersect_spans_combines_overlaps() -> None:
    overlaps = intersect_spans([(0.0, 5.0), (6.0, 8.0)], [(1.0, 3.0), (4.0, 7.0)])
    assert overlaps == [(1.0, 3.0), (4.0, 5.0), (6.0, 7.0)]


def test_intersect_spans_respects_tolerance() -> None:
    almost_touching = intersect_spans([(0.0, 1.0)], [(1.0 - 5e-13, 2.0)], tolerance=1e-12)
    assert almost_touching == []


def test_fill_polygon_with_rectangles_horizontal() -> None:
    polygon = Polygon([(0.0, 0.0), (6.0, 0.0), (6.0, 4.0), (0.0, 4.0)])
    rectangles = fill_polygon_with_rectangles(
        glyph_polygon=polygon,
        existing_geometry=Polygon(),
        rect_width=1.0,
        orientation="horizontal",
        safety_inset=0.0,
    )
    assert rectangles
    combined_area = sum(rectangle.area for rectangle in rectangles)
    assert combined_area > 0.0

    inset_rectangles = fill_polygon_with_rectangles(
        glyph_polygon=polygon,
        existing_geometry=Polygon(),
        rect_width=1.0,
        orientation="horizontal",
        safety_inset=10.0,
    )
    assert inset_rectangles == []


def test_fill_polygon_with_rectangles_skips_empty_components() -> None:
    full = Polygon([(0.0, 0.0), (3.0, 0.0), (3.0, 3.0), (0.0, 3.0)])
    rectangles = fill_polygon_with_rectangles(
        glyph_polygon=GeometryCollection([Polygon(), full]),
        existing_geometry=Polygon(),
        rect_width=1.0,
        orientation="horizontal",
        safety_inset=0.0,
    )
    assert rectangles


def test_fill_polygon_with_rectangles_skips_thin_spans() -> None:
    very_thin = Polygon([(0.0, 0.0), (0.018, 0.0), (0.018, 1.0), (0.0, 1.0)])
    rectangles = fill_polygon_with_rectangles(
        glyph_polygon=very_thin,
        existing_geometry=Polygon(),
        rect_width=0.5,
        orientation="horizontal",
        safety_inset=0.0,
    )
    assert rectangles == []


def test_fill_polygon_with_rectangles_handles_empty_and_vertical() -> None:
    empty = Polygon()
    assert fill_polygon_with_rectangles(empty, Polygon(), rect_width=1.0) == []

    polygon = Polygon([(0.0, 0.0), (3.0, 0.0), (3.0, 3.0), (0.0, 3.0)])
    try:
        fill_polygon_with_rectangles(polygon, Polygon(), rect_width=1.0, orientation="vertical")
    except NotImplementedError as exc:
        assert "Vertical fill" in str(exc)
    else:
        raise AssertionError("Vertical orientation should raise NotImplementedError")


def test_generate_subdivisions() -> None:
    values = list(_generate_subdivisions(3))
    assert values == [0.5, 0.25, 0.75, 0.125, 0.375, 0.625, 0.875]
