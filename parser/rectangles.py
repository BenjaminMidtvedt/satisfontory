"""Rectangle placement utilities along glyph boundaries."""
from __future__ import annotations

from collections.abc import Sequence

from shapely.geometry import Point as ShapelyPoint
from shapely.geometry import Polygon

from .geometry import Point, add, norm, rotate90_ccw, rotate90_cw, scale, subtract, unit_vector


def rectangles_along_polyline(
    polyline: Sequence[Point],
    thickness: float,
    overlap: float,
    interior_is_right: bool,
    remove_narrow: bool = True,
) -> list[Polygon]:
    """Place rectangles flush against a polygonal boundary.

    Parameters
    ----------
    polyline : sequence of Point
        Ordered vertices describing the boundary.
    thickness : float
        Inward rectangle depth.
    overlap : float
        Overlap distance used to avoid gaps between consecutive rectangles.
    interior_is_right : bool
        ``True`` when the interior is located to the right-hand side of the polyline.
    remove_narrow : bool, optional
        When ``True`` repeatedly prunes narrow regions before tiling, by default ``True``.

    Returns
    -------
    list of Polygon
        Rectangles aligned with the boundary segments.
    """
    if len(polyline) < 2:
        return []

    polygon = Polygon(polyline)
    polygon = polygon.segmentize(1.0)
    working_polyline: list[Point] = list(polygon.exterior.coords)

    while len(working_polyline) > 4 and remove_narrow:
        polygon = Polygon(working_polyline)
        working_polyline, removed_indices = remove_narrow_areas(
            working_polyline, polygon, thickness, overlap, interior_is_right,
        )
        if not removed_indices:
            break
        working_polyline = [working_polyline[-1], *working_polyline[:-1]]

    if len(working_polyline) > 4:
        polygon = Polygon(working_polyline)
        polygon = polygon.simplify(0.01)
        working_polyline = list(polygon.exterior.coords)

    rectangles: list[Polygon] = []
    for start, end in zip(working_polyline[:-1], working_polyline[1:]):
        segment = subtract(end, start)
        length = norm(segment)
        if length == 0.0:
            continue
        direction = unit_vector(segment)
        normal = rotate90_cw(direction) if interior_is_right else rotate90_ccw(direction)

        extended_start = start
        extended_end = end
        inner_start = add(extended_start, scale(normal, thickness))
        inner_end = add(extended_end, scale(normal, thickness))

        rectangle_coords = [extended_start, extended_end, inner_end, inner_start, extended_start]
        rectangle = Polygon(rectangle_coords)
        if rectangle.is_valid and not rectangle.is_empty:
            rectangles.append(rectangle)

    return rectangles


def remove_narrow_areas(
    polyline: Sequence[Point],
    polygon: Polygon,
    thickness: float,
    overlap: float,
    interior_is_right: bool,
) -> tuple[list[Point], set[int]]:
    """Prune vertices that would generate invalid inward rectangles.

    Parameters
    ----------
    polyline : sequence of Point
        Boundary vertices to inspect.
    polygon : Polygon
        Polygon constructed from ``polyline``; used to test coverage.
    thickness : float
        Inward rectangle depth.
    overlap : float
        Overlap distance between neighbours.
    interior_is_right : bool
        ``True`` if the polygon interior lies to the right of each edge.

    Returns
    -------
    list of Point
        Updated polyline after removing problematic vertices.
    set of int
        Indices that were removed from the original polyline.
    """
    if len(polyline) < 2:
        return list(polyline), set()

    removed: set[int] = set()
    updated: list[Point] = list(polyline)

    for index in range(len(polyline) - 1):
        start = polyline[index]
        end = polyline[index + 1]
        segment = subtract(end, start)
        length = norm(segment)
        if length == 0.0:
            continue
        direction = unit_vector(segment)
        normal = rotate90_cw(direction) if interior_is_right else rotate90_ccw(direction)
        extension = min(overlap, length * 0.5)
        a = subtract(start, scale(direction, extension))
        b = add(end, scale(direction, extension))
        inner_a = add(a, scale(normal, thickness))
        inner_b = add(b, scale(normal, thickness))

        if not polygon.covers(ShapelyPoint(*inner_b)):
            removed.add(index + 1)
        if not polygon.covers(ShapelyPoint(*inner_a)):
            removed.add(index)

    if not removed:
        return updated, removed

    updated = [point for idx, point in enumerate(polyline) if idx not in removed]
    return updated, removed


def extend_rectangles(
    glyph_polygon: Polygon,
    rectangles: Sequence[Polygon],
    extension: float,
) -> list[Polygon]:
    """Extend rectangles forward and backward while staying inside the glyph.

    Parameters
    ----------
    glyph_polygon : Polygon
        Glyph geometry used to clip the rectangles.
    rectangles : sequence of Polygon
        Rectangles to extend.
    extension : float
        Additional distance to extend in both tangential directions.

    Returns
    -------
    list of Polygon
        Extended rectangles.
    """
    extended: list[Polygon] = []
    for rectangle in rectangles:
        forward = extend_forward(rectangle, extension)
        candidate = forward if glyph_polygon.covers(forward) else rectangle
        backward = extend_backward(candidate, extension)
        candidate = backward if glyph_polygon.covers(backward) else candidate
        extended.append(candidate)
    return extended


def extend_forward(rectangle: Polygon, extension: float) -> Polygon:
    """Extend a rectangle along its forward edge.

    Parameters
    ----------
    rectangle : Polygon
        Rectangle to extend.
    extension : float
        Extra distance to add along the edge aligned with the rectangle's
        direction of travel.

    Returns
    -------
    Polygon
        Extended rectangle.
    """
    a, b, inner_b, inner_a, _ = list(rectangle.exterior.coords)
    direction = unit_vector(subtract(b, a))
    new_b = add(b, scale(direction, extension))
    new_inner_b = add(inner_b, scale(direction, extension))
    coords = [a, new_b, new_inner_b, inner_a, a]
    return Polygon(coords)


def extend_backward(rectangle: Polygon, extension: float) -> Polygon:
    """Extend a rectangle along its backward edge.

    Parameters
    ----------
    rectangle : Polygon
        Rectangle to extend.
    extension : float
        Extra distance to add opposite the rectangle's direction of travel.

    Returns
    -------
    Polygon
        Extended rectangle.
    """
    a, b, inner_b, inner_a, _ = list(rectangle.exterior.coords)
    direction = unit_vector(subtract(a, b))
    new_a = add(a, scale(direction, extension))
    new_inner_a = add(inner_a, scale(direction, extension))
    coords = [new_a, b, inner_b, new_inner_a, new_a]
    return Polygon(coords)


__all__ = [
    "extend_backward",
    "extend_forward",
    "extend_rectangles",
    "rectangles_along_polyline",
    "remove_narrow_areas",
]
