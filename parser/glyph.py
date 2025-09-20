"""Glyph outline helpers built on top of FreeType."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from fontTools.ttLib import TTFont
from shapely.geometry import Polygon

from .contours import FTContour, fonttools_outline_to_contours
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


FontInput = TTFont | str | Path | None


def _resolve_ttfont(font_path: str | Path | None) -> tuple[TTFont, bool]:
    if isinstance(font_path, TTFont):
        return font_path, False
    if isinstance(font_path, (str, Path)):
        return TTFont(font_path), True
    if font_path is None:
        if font_path is None:
            msg = "font or font_path must be provided when backend='fonttools'."
            raise ValueError(msg)
        return TTFont(font_path), True
    msg = f"Unsupported font argument type: {type(font).__name__}"
    raise TypeError(msg)


def _build_outline(
    contours: Sequence[FTContour],
    tags_per_contour: Sequence[Sequence[int]],
    reversed_fill: bool,
    min_segment_length: float,
) -> GlyphOutline:
    if len(contours) != len(tags_per_contour):
        msg = "Contour and tag counts must match."
        raise ValueError(msg)

    exteriors: list[list[Point]] = []
    holes: list[list[Point]] = []

    for contour, tags in zip(contours, tags_per_contour):
        if len(contour.points) != len(tags):
            msg = "Contour points and tag lengths do not match."
            raise ValueError(msg)
        polyline = flatten_contour(contour, tags, min_segment_length=min_segment_length)
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


def _infer_reversed_fill(contours: Sequence[FTContour]) -> bool:
    for contour in contours:
        if len(contour.points) >= 3:
            return not polygon_is_ccw(contour.points)
    return True


def get_glyph_outline(
    face_path: str,
    char: str,
    pixel_height: int,
    min_segment_length: float = 1.0,
    *,
    backend: Literal["freetype", "fonttools"] = "freetype",
    font: FontInput = None,
    rdp_epsilon: float = 0.0,
) -> GlyphOutline:
    """Extract a glyph as polylines suitable for geometric processing.

    Parameters
    ----------
    face : freetype.Face or None
        FreeType face providing the glyph. Required when ``backend`` is ``"freetype"``.
    char : str
        Character code to load from ``face``.
    pixel_height : int
        Desired glyph height in pixels.
    min_segment_length : float, optional
        Minimum sampling distance during flattening, by default ``1.0``.
    backend : {"freetype", "fonttools"}, optional
        Outline extraction backend. ``"freetype"`` uses the existing FreeType pipeline,
        while ``"fonttools"`` extracts contours via FontTools, by default ``"freetype"``.
    font : TTFont or path-like, optional
        Pre-loaded FontTools ``TTFont`` instance or path used when ``backend`` is ``"fonttools"``.
    font_path : str or Path, optional
        Alternate path to the font file used when ``backend`` is ``"fonttools"`` and
        ``font`` is not supplied.
    rdp_epsilon : float, optional
        Placeholder for Ramer–Douglas–Peucker simplification tolerance, currently unused.

    Returns
    -------
    GlyphOutline
        Glyph boundaries separated into exterior and hole polylines.
    """
    backend_value = backend.lower()

    # if backend_value == "freetype":
    #     face = freetype.Face(face_path)

    #     contours, flags = freetype_outline_to_contours(face, char, pixel_height)
    #     outline = face.glyph.outline

    #     tags_per_contour: list[list[int]] = []
    #     start_index = 0
    #     for contour in contours:
    #         count = len(contour.points)
    #         tags_per_contour.append(outline.tags[start_index : start_index + count])
    #         start_index += count

    #     reversed_fill = flags & freetype.FT_OUTLINE_FLAGS["FT_OUTLINE_REVERSE_FILL"] == 0
    #     return _build_outline(contours, tags_per_contour, reversed_fill, min_segment_length)

    if backend_value == "fonttools":
        ttfont, close_after = _resolve_ttfont(face_path)
        try:
            contours, tags_per_contour = fonttools_outline_to_contours(ttfont, char, pixel_height)
        finally:
            if close_after:
                ttfont.close()

        reversed_fill = _infer_reversed_fill(contours)
        return _build_outline(contours, tags_per_contour, reversed_fill, min_segment_length)

    msg = f"Unsupported backend value: {backend}"
    raise ValueError(msg)


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
