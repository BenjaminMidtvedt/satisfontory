"""Interior tiling helpers for glyph polygons."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from shapely.geometry import GeometryCollection, LineString, MultiLineString, Polygon

if TYPE_CHECKING:
    from collections.abc import Sequence


def iter_line_segments_from_intersection(geometry) -> list[tuple[float, float]]:
    """Convert a shapely intersection result into sorted spans.

    Parameters
    ----------
    geometry : shapely geometry
        Geometry returned by intersecting a polygon with a line.

    Returns
    -------
    list of tuple of float
        Sorted list of coordinate intervals where the line penetrates the polygon.
    """
    spans: list[tuple[float, float]] = []
    if isinstance(geometry, LineString):
        coordinates = list(geometry.coords)
        xs, ys = zip(*coordinates)
        if abs(xs[0] - xs[-1]) < 1e-12:
            spans.append((min(ys), max(ys)))
        else:
            spans.append((min(xs), max(xs)))
    elif isinstance(geometry, MultiLineString):
        for line in geometry.geoms:
            spans.extend(iter_line_segments_from_intersection(line))
    elif isinstance(geometry, GeometryCollection):
        for element in geometry.geoms:
            spans.extend(iter_line_segments_from_intersection(element))

    spans = [span for span in spans if (span[1] - span[0]) > 1e-9]
    spans.sort()
    return spans


def intersect_spans(
    first: Sequence[tuple[float, float]],
    second: Sequence[tuple[float, float]],
    tolerance: float = 1e-12,
) -> list[tuple[float, float]]:
    """Intersect two ordered lists of spans.

    Parameters
    ----------
    first : sequence of tuple of float
        First ordered list of half-open intervals.
    second : sequence of tuple of float
        Second ordered list of half-open intervals.
    tolerance : float, optional
        Numerical tolerance used when comparing endpoints, by default ``1e-12``.

    Returns
    -------
    list of tuple of float
        Overlapping intervals from the two input sequences.
    """
    index_a = 0
    index_b = 0
    overlaps: list[tuple[float, float]] = []
    while index_a < len(first) and index_b < len(second):
        start = max(first[index_a][0], second[index_b][0])
        end = min(first[index_a][1], second[index_b][1])
        if end - start > tolerance:
            overlaps.append((start, end))
        if first[index_a][1] <= second[index_b][1] + tolerance:
            index_a += 1
        else:
            index_b += 1
    return overlaps


def fill_polygon_with_rectangles(
    glyph_polygon: Polygon,
    existing_geometry,
    rect_width: float,
    orientation: str = "vertical",
    safety_inset: float = 0.0,
) -> list[Polygon]:
    """Fill a polygon interior using axis-aligned rectangles.

    Parameters
    ----------
    glyph_polygon : Polygon
        Polygon to fill.
    existing_geometry : shapely geometry
        Geometry already occupied (rectangles placed along the boundary).
    rect_width : float
        Width of the rectangles.
    orientation : {"vertical", "horizontal"}, optional
        Orientation of the fill stripes, by default ``"vertical"``.
    safety_inset : float, optional
        Optional inward offset applied before scanning, by default ``0.0``.

    Returns
    -------
    list of Polygon
        Axis-aligned rectangles covering uncovered interior areas.
    """
    if glyph_polygon.is_empty:
        return []

    polygons = [glyph_polygon] if isinstance(glyph_polygon, Polygon) else list(glyph_polygon.geoms)
    rectangles: list[Polygon] = []
    tolerance = 1e-9
    margin = 10.0 * max(1.0, rect_width)

    for polygon in polygons:
        if polygon.is_empty:
            continue
        if safety_inset > 0.0:
            safe_polygon = polygon.buffer(-safety_inset)
            if safe_polygon.is_empty:
                continue
        else:
            safe_polygon = polygon

        min_x, min_y, max_x, max_y = safe_polygon.bounds

        if orientation.lower() == "vertical":
            raise NotImplementedError("Vertical fill not implemented yet.")
        for offset in _generate_subdivisions(4):
            y = min_y + offset * rect_width
            while y < max_y - tolerance:
                y0 = y
                y1 = min(y + rect_width, max_y)
                bottom_line = LineString([(min_x - margin, y0 + tolerance), (max_x + margin, y0 + tolerance)])
                top_line = LineString([(min_x - margin, y1 - tolerance), (max_x + margin, y1 - tolerance)])
                spans_bottom = iter_line_segments_from_intersection(safe_polygon.intersection(bottom_line))
                spans_top = iter_line_segments_from_intersection(safe_polygon.intersection(top_line))
                spans = intersect_spans(spans_bottom, spans_top, tolerance=tolerance)
                for start, end in spans:
                    start += 0.01
                    end -= 0.01
                    if end - start <= tolerance:
                        continue
                    candidate = Polygon([(start, y0), (end, y0), (end, y1), (start, y1), (start, y0)])
                    if safe_polygon.contains(candidate) and not existing_geometry.covers(candidate):
                        rectangles.append(candidate)
                        existing_geometry = existing_geometry.union(candidate)
                y += rect_width

    return rectangles


def _generate_subdivisions(iterations: int) -> Iterable[float]:
    """Generate a list of fractional subdivisions for jittering."""
    for iteration in range(iterations):
        divisor = 2 ** (iteration + 1)
        for numerator in range(1, divisor, 2):
            yield numerator / divisor


__all__ = [
    "fill_polygon_with_rectangles",
    "intersect_spans",
    "iter_line_segments_from_intersection",
]
