from __future__ import annotations

from typing import Any

import pytest
from shapely.geometry import MultiPolygon, Polygon

from parser.glyph import GlyphOutline
from parser import pipeline


def _square(x0: float, y0: float, size: float) -> Polygon:
    return Polygon(
        [
            (x0, y0),
            (x0 + size, y0),
            (x0 + size, y0 + size),
            (x0, y0 + size),
            (x0, y0),
        ],
    )


def test_build_rectangles_for_glyph_combines_geometry(monkeypatch: pytest.MonkeyPatch) -> None:
    outline = GlyphOutline(
        exteriors=[[(0.0, 0.0), (5.0, 0.0), (5.0, 5.0), (0.0, 5.0), (0.0, 0.0)]],
        holes=[],
        reversed_fill=False,
    )
    glyph_polygon = _square(0.0, 0.0, 5.0)
    boundary_rectangle = Polygon([(0.0, 0.0), (5.0, 0.0), (5.0, 1.0), (0.0, 1.0), (0.0, 0.0)])
    interior_rectangle = Polygon([(1.0, 1.0), (4.0, 1.0), (4.0, 2.5), (1.0, 2.5), (1.0, 1.0)])

    def fake_get_glyph_outline(*args: Any, **kwargs: Any) -> GlyphOutline:
        return outline

    def fake_outline_to_polygon(arg: GlyphOutline) -> Polygon:
        assert arg is outline
        return glyph_polygon

    def fake_rectangles_along_polyline(polyline, *args: Any, **kwargs: Any):
        assert polyline == outline.exteriors[0]
        return [boundary_rectangle]

    def fake_extend_rectangles(glyph_poly, rectangles, extension):
        assert glyph_poly == glyph_polygon
        assert rectangles == [boundary_rectangle]
        assert extension == pytest.approx(2.0)
        return rectangles

    def fake_fill_polygon_with_rectangles(**kwargs: Any):
        assert kwargs["glyph_polygon"] == glyph_polygon
        assert kwargs["existing_geometry"].covers(boundary_rectangle)
        return [interior_rectangle]

    monkeypatch.setattr(pipeline, "get_glyph_outline", fake_get_glyph_outline)
    monkeypatch.setattr(pipeline, "outline_to_polygon", fake_outline_to_polygon)
    monkeypatch.setattr(pipeline, "rectangles_along_polyline", fake_rectangles_along_polyline)
    monkeypatch.setattr(pipeline, "extend_rectangles", fake_extend_rectangles)
    monkeypatch.setattr(pipeline, "fill_polygon_with_rectangles", fake_fill_polygon_with_rectangles)

    combined, rectangles = pipeline.build_rectangles_for_glyph(
        face=None,
        char="A",
        pixel_height=32,
        thickness=2.0,
        overlap=0.5,
        fill_orientation="horizontal",
    )

    assert rectangles == [boundary_rectangle, interior_rectangle]
    expected_area = boundary_rectangle.union(interior_rectangle).area
    assert pytest.approx(combined.area) == expected_area


def test_build_rectangles_for_glyph_handles_multipolygons(monkeypatch: pytest.MonkeyPatch) -> None:
    outline = GlyphOutline(
        exteriors=[[(0.0, 0.0), (3.0, 0.0), (3.0, 3.0), (0.0, 3.0)]],
        holes=[],
        reversed_fill=True,
    )
    glyph_polygon = MultiPolygon([_square(0.0, 0.0, 3.0), _square(5.0, 0.0, 2.0)])
    boundary_rectangle = _square(0.0, 0.0, 1.0)

    def fake_get_glyph_outline(*args: Any, **kwargs: Any) -> GlyphOutline:
        return outline

    def fake_outline_to_polygon(arg: GlyphOutline):
        return glyph_polygon

    def fake_rectangles_along_polyline(polyline, *args: Any, **kwargs: Any):
        return [boundary_rectangle]

    def fake_extend_rectangles(glyph_poly, rectangles, extension):
        return rectangles

    def fake_fill_polygon_with_rectangles(**kwargs: Any):
        return []

    monkeypatch.setattr(pipeline, "get_glyph_outline", fake_get_glyph_outline)
    monkeypatch.setattr(pipeline, "outline_to_polygon", fake_outline_to_polygon)
    monkeypatch.setattr(pipeline, "rectangles_along_polyline", fake_rectangles_along_polyline)
    monkeypatch.setattr(pipeline, "extend_rectangles", fake_extend_rectangles)
    monkeypatch.setattr(pipeline, "fill_polygon_with_rectangles", fake_fill_polygon_with_rectangles)

    combined, rectangles = pipeline.build_rectangles_for_glyph(
        face=None,
        char="B",
        pixel_height=64,
        thickness=1.0,
        overlap=0.0,
        fill_orientation="horizontal",
    )

    assert rectangles == [boundary_rectangle]
    assert combined.intersects(_square(0.0, 0.0, 1.0))


def test_build_rectangles_for_glyph_returns_polygon_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    outline = GlyphOutline(
        exteriors=[[(0.0, 0.0), (2.0, 0.0), (2.0, 2.0)]],
        holes=[],
        reversed_fill=False,
    )
    glyph_polygon = _square(0.0, 0.0, 2.0)

    def fake_get_glyph_outline(*args: Any, **kwargs: Any) -> GlyphOutline:
        return outline

    def fake_outline_to_polygon(arg: GlyphOutline):
        return glyph_polygon

    def fake_rectangles_along_polyline(*args: Any, **kwargs: Any):
        return []

    def fake_extend_rectangles(*args: Any, **kwargs: Any):
        return []

    def fail_fill(**kwargs: Any):
        raise AssertionError("fill_polygon_with_rectangles should not be called when boundary is empty")

    monkeypatch.setattr(pipeline, "get_glyph_outline", fake_get_glyph_outline)
    monkeypatch.setattr(pipeline, "outline_to_polygon", fake_outline_to_polygon)
    monkeypatch.setattr(pipeline, "rectangles_along_polyline", fake_rectangles_along_polyline)
    monkeypatch.setattr(pipeline, "extend_rectangles", fake_extend_rectangles)
    monkeypatch.setattr(pipeline, "fill_polygon_with_rectangles", fail_fill)

    combined, rectangles = pipeline.build_rectangles_for_glyph(
        face=None,
        char="C",
        pixel_height=64,
        thickness=2.0,
        overlap=0.0,
    )

    assert rectangles == []
    assert combined.equals(glyph_polygon)