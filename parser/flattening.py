"""Contour flattening utilities for FreeType outlines."""
from __future__ import annotations

import math
from collections.abc import Sequence

import bezier
import numpy as np

from .contours import FTContour
from .geometry import Point


def flatten_contour(
    contour: FTContour,
    tags: Sequence[int],
    min_segment_length: float = 1.0,
) -> list[Point]:
    """Sample a FreeType contour into a dense polyline.

    Parameters
    ----------
    contour : FTContour
        Contour definition with control points and on-curve flags.
    tags : sequence of int
        FreeType point tags for the contour. Only the lowest two bits are used.
    min_segment_length : float, optional
        Minimum distance between successive samples along the curve, by default ``1.0``.

    Returns
    -------
    list of Point
        Polyline approximating the contour. The contour is closed when the input is closed.
    """
    if not contour.points:
        return []

    ft_curve_tag_conic = 0
    ft_curve_tag_on = 1
    ft_curve_tag_cubic = 2

    def is_on(tag: int) -> bool:
        return (tag & 3) == ft_curve_tag_on

    def is_conic(tag: int) -> bool:
        return (tag & 3) == ft_curve_tag_conic

    def is_cubic(tag: int) -> bool:
        return (tag & 3) == ft_curve_tag_cubic

    points: list[Point] = contour.points
    size = len(points)
    if len(tags) != size:
        msg = "Tags length must match contour point count."
        raise ValueError(msg)

    if is_on(tags[0]):
        current_anchor = points[0]
        start_index = 1
    else:
        if is_conic(tags[0]) and is_conic(tags[-1]):
            implicit = ((points[-1][0] + points[0][0]) * 0.5, (points[-1][1] + points[0][1]) * 0.5)
            current_anchor = implicit
            start_index = 0
        elif len(points) >= 2 and is_cubic(tags[-1]) and is_on(tags[-2]):
            current_anchor = points[-2]
            start_index = 0
        elif is_on(tags[-1]):
            current_anchor = points[-1]
            start_index = 0
        else:
            current_anchor = points[0]
            start_index = 1

    segments: list[tuple[str, list[Point]]] = []
    consumed = 0
    index = start_index % size
    iterations = 0
    max_iterations = 3 * size + 8

    while consumed < size and iterations < max_iterations:
        iterations += 1
        tag = tags[index % size]
        point = points[index % size]

        if is_on(tag):
            if point != current_anchor:
                segments.append(("line", [current_anchor, point]))
                current_anchor = point
            consumed += 1
            index = (index + 1) % size
            continue

        if is_conic(tag):
            next_index = (index + 1) % size
            next_tag = tags[next_index]
            next_point = points[next_index]
            if is_on(next_tag):
                segments.append(("quadratic", [current_anchor, point, next_point]))
                current_anchor = next_point
                consumed += 2
                index = (index + 2) % size
            elif is_conic(next_tag):
                midpoint = ((point[0] + next_point[0]) * 0.5, (point[1] + next_point[1]) * 0.5)
                segments.append(("quadratic", [current_anchor, point, midpoint]))
                current_anchor = midpoint
                consumed += 1
                index = (index + 1) % size
            else:
                consumed += 1
                index = (index + 1) % size
            continue

        if is_cubic(tag):
            next_1 = (index + 1) % size
            next_2 = (index + 2) % size
            if size >= 3 and is_cubic(tags[next_1]) and is_on(tags[next_2]):
                p1 = points[next_1]
                p2 = points[next_2]
                segments.append(("cubic", [current_anchor, point, p1, p2]))
                current_anchor = p2
                consumed += 3
                index = (index + 3) % size
            else:
                consumed += 1
                index = (index + 1) % size
            continue

        consumed += 1
        index = (index + 1) % size

    if segments:
        first_point = segments[0][1][0]
        if current_anchor != first_point:
            segments.append(("line", [current_anchor, first_point]))

    polyline: list[Point] = []
    if not segments:
        return polyline

    start_point = segments[0][1][0]
    polyline.append((float(start_point[0]), float(start_point[1])))

    for segment_type, control_points in segments:
        if segment_type == "line":
            nodes = np.asfortranarray(
                [
                    [control_points[0][0], control_points[1][0]],
                    [control_points[0][1], control_points[1][1]],
                ],
                dtype=float,
            )
            curve = bezier.Curve(nodes, degree=1)
        elif segment_type == "quadratic":
            nodes = np.asfortranarray(
                [
                    [control_points[0][0], control_points[1][0], control_points[2][0]],
                    [control_points[0][1], control_points[1][1], control_points[2][1]],
                ],
                dtype=float,
            )
            curve = bezier.Curve(nodes, degree=2)
        elif segment_type == "cubic":
            nodes = np.asfortranarray(
                [
                    [
                        control_points[0][0],
                        control_points[1][0],
                        control_points[2][0],
                        control_points[3][0],
                    ],
                    [
                        control_points[0][1],
                        control_points[1][1],
                        control_points[2][1],
                        control_points[3][1],
                    ],
                ],
                dtype=float,
            )
            curve = bezier.Curve(nodes, degree=3)
        else:
            continue

        length = float(curve.length)
        segments_count = max(1, int(math.floor(length / max(1e-12, min_segment_length))))

        for piece_index in range(1, segments_count + 1):
            t_value = piece_index / segments_count
            point_value = curve.evaluate(t_value).flatten()
            polyline.append((float(point_value[0]), float(point_value[1])))

    return polyline


__all__ = ["flatten_contour"]
