"""Helpers for extracting FreeType glyph contours."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import freetype

if TYPE_CHECKING:
    from .geometry import Point


@dataclass(slots=True)
class FTContour:
    """Representation of a single glyph contour.

    Parameters
    ----------
    points : list of Point
        Control points that define the contour in font units.
    on_curve : list of bool
        Flags indicating whether each point lies on the contour curve.
    """

    points: list[Point]
    on_curve: list[bool]


def freetype_outline_to_contours(
    face: freetype.Face,
    char: str,
    pixel_height: int,
) -> tuple[list[FTContour], int]:
    """Convert a FreeType outline into contour objects.

    Parameters
    ----------
    face : freetype.Face
        FreeType face containing the glyph.
    char : str
        Character whose glyph should be extracted.
    pixel_height : int
        Requested pixel height for the glyph.

    Returns
    -------
    list of FTContour
        The glyph contours in drawing order.
    int
        Outline flag bits reported by FreeType.
    """
    face.set_pixel_sizes(0, pixel_height)
    face.load_char(char, freetype.FT_LOAD_NO_BITMAP)
    outline: freetype.Outline = face.glyph.outline

    scale = 1.0 / 64.0
    contours: list[FTContour] = []
    start_index = 0

    for end_index in outline.contours:
        points = outline.points[start_index : end_index + 1]
        tags = outline.tags[start_index : end_index + 1]
        scaled_points = [(float(x) * scale, float(y) * scale) for (x, y) in points]
        on_curve = [bool(tag & 1) for tag in tags]
        contours.append(FTContour(points=scaled_points, on_curve=on_curve))
        start_index = end_index + 1

    return contours, outline.flags


__all__ = ["FTContour", "freetype_outline_to_contours"]
