"""High-level glyph pipeline orchestration."""
from __future__ import annotations

import freetype
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

from .fill import fill_polygon_with_rectangles
from .glyph import GlyphOutline, get_glyph_outline, outline_to_polygon
from .rectangles import extend_rectangles, rectangles_along_polyline


def build_rectangles_for_glyph(
    face: freetype.Face,
    char: str,
    pixel_height: int = 512,
    thickness: float = 6.0,
    overlap: float = 2.0,
    min_segment_length: float = 1.0,
    rdp_epsilon: float = 0.0,
    fill_orientation: str = "horizontal",
    safety_inset: float = 1.0,
) -> tuple[Polygon | MultiPolygon, list[Polygon]]:
    """Run the full glyph processing pipeline.

    Parameters
    ----------
    face : freetype.Face
        Loaded FreeType face containing the glyph.
    char : str
        Glyph character to process.
    pixel_height : int, optional
        Height used when loading the glyph, by default ``512``.
    thickness : float, optional
        Rectangle depth measured inward from the outline, by default ``6.0``.
    overlap : float, optional
        Overlap distance applied along the boundary, by default ``2.0``.
    min_segment_length : float, optional
        Minimum sampling length when flattening contours, by default ``1.0``.
    rdp_epsilon : float, optional
        Ramer–Douglas–Peucker simplification tolerance, by default ``0.0`` (disabled).
    fill_orientation : {"vertical", "horizontal"}, optional
        Orientation of the interior fill rectangles, by default ``"horizontal"``.
    safety_inset : float, optional
        Optional safety inset applied before interior filling, by default ``1.0``.

    Returns
    -------
    Polygon or MultiPolygon
        Union of the rectangles clipped to the glyph outline.
    list of Polygon
        Individual rectangles used to approximate the glyph.
    """
    outline: GlyphOutline = get_glyph_outline(
        face,
        char,
        pixel_height,
        min_segment_length=min_segment_length,
        rdp_epsilon=rdp_epsilon,
    )

    glyph_polygon = outline_to_polygon(outline)

    boundary_rectangles: list[Polygon] = []
    for ring in outline.exteriors:
        boundary_rectangles.extend(
            rectangles_along_polyline(ring, thickness, overlap, interior_is_right=outline.reversed_fill),
        )
    for ring in outline.holes:
        boundary_rectangles.extend(
            rectangles_along_polyline(
                ring,
                thickness,
                overlap,
                interior_is_right=outline.reversed_fill,
                remove_narrow=False,
            ),
        )

    boundary_rectangles = extend_rectangles(glyph_polygon, boundary_rectangles, thickness)

    if not boundary_rectangles:
        return glyph_polygon, []

    boundary_union = unary_union(boundary_rectangles)
    interior_rectangles = fill_polygon_with_rectangles(
        glyph_polygon=glyph_polygon,
        existing_geometry=boundary_union,
        rect_width=thickness,
        orientation=fill_orientation,
        safety_inset=safety_inset,
    )

    all_rectangles = boundary_rectangles + interior_rectangles
    combined = unary_union(all_rectangles)

    if glyph_polygon.geom_type == "Polygon":
        combined = combined.intersection(glyph_polygon)
    else:
        combined = combined.intersection(MultiPolygon(glyph_polygon.geoms))

    return combined, all_rectangles


__all__ = ["build_rectangles_for_glyph"]
