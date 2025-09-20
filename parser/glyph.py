"""Glyph outline helpers built on top of FreeType."""

from __future__ import annotations

from dataclasses import dataclass

import freetype
from shapely.geometry import Polygon

from .contours import freetype_outline_to_contours
from .flattening import flatten_contour
from .geometry import Point, polygon_is_ccw


@dataclass(slots=True)
class GlyphOutline:
    """Polyline representation of a glyph.

    Parameters
    ----------
    exteriors : list of list of Point
        Closed polylines describing outer boundaries.
    holes : list of list of Point
        Closed polylines describing holes.
    reversed_fill : bool
        Flag indicating whether the outline uses the reversed fill rule.
    """

    exteriors: list[list[Point]]
    holes: list[list[Point]]
    reversed_fill: bool


def get_glyph_outline(
    face: freetype.Face,
    char: str,
    pixel_height: int,
    min_segment_length: float = 1.0,
    rdp_epsilon: float = 0.0,
) -> GlyphOutline:
    """Extract a glyph as polylines suitable for geometric processing.

    Parameters
    ----------
    face : freetype.Face
        FreeType face providing the glyph.
    char : str
        Character code to load from ``face``.
    pixel_height : int
        Desired glyph height in pixels.
    min_segment_length : float, optional
        Minimum sampling distance during flattening, by default ``1.0``.
    rdp_epsilon : float, optional
        Ramer–Douglas–Peucker tolerance applied to the flattened curves, by default ``0.0`` (disabled).

    Returns
    -------
    GlyphOutline
        Glyph boundaries separated into exterior and hole polylines.
    """
    contours, flags = freetype_outline_to_contours(face, char, pixel_height)
    outline = face.glyph.outline

    exteriors: list[list[Point]] = []
    holes: list[list[Point]] = []

    reversed_fill = flags & freetype.FT_OUTLINE_FLAGS["FT_OUTLINE_REVERSE_FILL"] == 0

    start_index = 0
    for contour in contours:
        tags = outline.tags[start_index : start_index + len(contour.points)]
        polyline = flatten_contour(contour, tags, min_segment_length=min_segment_length)
        start_index += len(contour.points)
        if len(polyline) < 4:
            continue
        if polygon_is_ccw(polyline) ^ reversed_fill:
            exteriors.append(polyline)
        else:
            holes.append(polyline)

    if not exteriors:
        msg = "Glyph does not contain an exterior contour."
        raise ValueError(msg)

    return GlyphOutline(exteriors=exteriors, holes=holes, reversed_fill=reversed_fill)


def outline_to_polygon(outline: GlyphOutline) -> Polygon:
    """Convert a glyph outline into a shapely polygon (with holes).

    Parameters
    ----------
    outline : GlyphOutline
        Polyline representation produced by :func:`get_glyph_outline`.

    Returns
    -------
    Polygon
        Polygon geometry describing the glyph.
    """
    exterior_polygons = [Polygon(ring) for ring in outline.exteriors if len(ring) >= 3]
    if not exterior_polygons:
        msg = "Outline does not contain any exterior polygons."
        raise ValueError(msg)

    union = exterior_polygons[0].buffer(0)
    for polygon in exterior_polygons[1:]:
        union = union.union(polygon.buffer(0))

    for hole in outline.holes:
        if len(hole) >= 3:
            union = union.difference(Polygon(hole))

    if union.geom_type == "Polygon":
        return union

    if union.geom_type == "MultiPolygon":
        # ``buffer(0)`` cleans up geometry but may split components. Keep the largest component.
        polygons = sorted(union.geoms, key=lambda geom: geom.area, reverse=True)
        return Polygon(polygons[0].exterior.coords, [list(interior.coords) for interior in polygons[0].interiors])

    msg = f"Unexpected geometry type produced from outline: {union.geom_type}"
    raise ValueError(msg)


__all__ = ["GlyphOutline", "get_glyph_outline", "outline_to_polygon"]
