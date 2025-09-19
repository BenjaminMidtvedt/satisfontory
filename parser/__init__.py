"""Public API for the sat_sav_parse glyph processing toolkit."""
from __future__ import annotations

from .blueprint import Line, lines_to_world
from .contours import FTContour, freetype_outline_to_contours
from .fill import fill_polygon_with_rectangles, intersect_spans, iter_line_segments_from_intersection
from .geometry import (
    Point,
    add,
    norm,
    polygon_is_ccw,
    rotate90_ccw,
    rotate90_cw,
    scale,
    subtract,
    unit_vector,
)
from .glyph import GlyphOutline, get_glyph_outline, outline_to_polygon
from .pipeline import build_rectangles_for_glyph
from .rectangles import (
    extend_backward,
    extend_forward,
    extend_rectangles,
    rectangles_along_polyline,
    remove_narrow_areas,
)

__all__ = [
    "FTContour",
    "GlyphOutline",
    "Line",
    "Point",
    "add",
    "build_rectangles_for_glyph",
    "extend_backward",
    "extend_forward",
    "extend_rectangles",
    "fill_polygon_with_rectangles",
    "freetype_outline_to_contours",
    "get_glyph_outline",
    "intersect_spans",
    "iter_line_segments_from_intersection",
    "lines_to_world",
    "norm",
    "outline_to_polygon",
    "polygon_is_ccw",
    "rectangles_along_polyline",
    "remove_narrow_areas",
    "rotate90_ccw",
    "rotate90_cw",
    "scale",
    "subtract",
    "unit_vector",
]
