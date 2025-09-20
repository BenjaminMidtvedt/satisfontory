"""Helpers for extracting FreeType glyph contours."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import freetype
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

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


def fonttools_outline_to_contours(
    font: TTFont,
    char: str,
    pixel_height: int,
) -> tuple[list[FTContour], list[list[int]]]:
    """Convert a FontTools glyph into contour objects and point tags.

    Parameters
    ----------
    font : fontTools.ttLib.TTFont
        Loaded font used to source the glyph geometry.
    char : str
        Character whose glyph should be extracted.
    pixel_height : int
        Requested pixel height for the glyph.

    Returns
    -------
    list of FTContour
        Extracted glyph contours scaled to ``pixel_height``.
    list of list of int
        Point tags compatible with :func:`parser.flattening.flatten_contour`.
    """
    if not char:
        msg = "Character must be a single codepoint."
        raise ValueError(msg)

    cmap = font.getBestCmap()
    glyph_name = cmap.get(ord(char))
    if glyph_name is None:
        msg = f"Glyph for character {char!r} not found in font."
        raise ValueError(msg)

    units_per_em = font["head"].unitsPerEm
    if units_per_em <= 0:
        msg = "Font reports non-positive units per em."
        raise ValueError(msg)

    scale = float(pixel_height) / float(units_per_em)

    glyph_set = font.getGlyphSet()
    pen = DecomposingRecordingPen(glyph_set)
    glyph_set[glyph_name].draw(pen)

    contours: list[FTContour] = []
    tags_per_contour: list[list[int]] = []

    current_points: list[Point] = []
    current_tags: list[int] = []
    current_on_curve: list[bool] = []

    def flush_contour() -> None:
        nonlocal current_points, current_tags, current_on_curve
        if current_points:
            contours.append(FTContour(points=current_points, on_curve=current_on_curve))
            tags_per_contour.append(current_tags)
            current_points = []
            current_tags = []
            current_on_curve = []

    for command, args in pen.value:
        if command == "moveTo":
            flush_contour()
            x, y = args[0]
            current_points = [(float(x) * scale, float(y) * scale)]
            current_tags = [1]
            current_on_curve = [True]
        elif command == "lineTo":
            for x, y in args:
                current_points.append((float(x) * scale, float(y) * scale))
                current_tags.append(1)
                current_on_curve.append(True)
        elif command == "qCurveTo":
            arg_length = len(args)
            for index, point in enumerate(args):
                if point is None:
                    continue
                x, y = point
                is_last = index == arg_length - 1
                current_points.append((float(x) * scale, float(y) * scale))
                current_on_curve.append(is_last)
                current_tags.append(1 if is_last else 0)
        elif command == "curveTo":
            for index, (x, y) in enumerate(args):
                is_last = (index % 3) == 2
                current_points.append((float(x) * scale, float(y) * scale))
                current_on_curve.append(is_last)
                current_tags.append(1 if is_last else 2)
        elif command == "closePath":
            flush_contour()
        else:
            msg = f"Unsupported drawing command encountered: {command}"
            raise ValueError(msg)

    flush_contour()

    return contours, tags_per_contour


__all__ = [
    "FTContour",
    "fonttools_outline_to_contours",
    "freetype_outline_to_contours",
]
