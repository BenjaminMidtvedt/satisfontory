from __future__ import annotations

from parser.glyph import GlyphOutline, get_glyph_outline, outline_to_polygon


def test_get_glyph_outline_returns_rdp_filtered_data(font_face) -> None:
    outline = get_glyph_outline(font_face, "A", pixel_height=96, min_segment_length=0.5, rdp_epsilon=0.1)
    assert outline.exteriors
    assert isinstance(outline.reversed_fill, bool)

    holes_outline = get_glyph_outline(font_face, "O", pixel_height=96, min_segment_length=0.5)
    assert holes_outline.holes


def test_get_glyph_outline_requires_exterior(font_face) -> None:
    try:
        get_glyph_outline(font_face, " ", pixel_height=96)
    except ValueError as exc:
        assert "exterior" in str(exc)
    else:
        raise AssertionError("Expected glyph without exteriors to raise ValueError")


def test_outline_to_polygon_handles_holes_and_multipolygons() -> None:
    outline = GlyphOutline(
        exteriors=[
            [(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)],
            [(10.0, 0.0), (14.0, 0.0), (14.0, 2.0), (10.0, 2.0)],
        ],
        holes=[[(1.0, 1.0), (3.0, 1.0), (3.0, 3.0), (1.0, 3.0)]],
        reversed_fill=False,
    )
    polygon = outline_to_polygon(outline)
    assert polygon.geom_type == "Polygon"
    assert polygon.area == 16.0 - 4.0


    the_outline = GlyphOutline(exteriors=[], holes=[], reversed_fill=False)
    try:
        outline_to_polygon(the_outline)
    except ValueError as exc:
        assert "Outline" in str(exc)
    else:
        raise AssertionError("Expected ValueError when no exterior polygons exist")
