"""Low-level 2D geometry helpers used across the glyph pipeline."""
from __future__ import annotations

from collections.abc import Iterable
from typing import TypeAlias

Point: TypeAlias = tuple[float, float]


def subtract(first: Point, second: Point) -> Point:
    """Compute the vector ``first - second``.

    Parameters
    ----------
    first : Point
        Point representing the vector minuend.
    second : Point
        Point representing the vector subtrahend.

    Returns
    -------
    Point
        Component-wise difference between ``first`` and ``second``.
    """
    return (first[0] - second[0], first[1] - second[1])


def add(first: Point, second: Point) -> Point:
    """Compute the vector ``first + second``.

    Parameters
    ----------
    first : Point
        First operand.
    second : Point
        Second operand.

    Returns
    -------
    Point
        Component-wise sum of the input vectors.
    """
    return (first[0] + second[0], first[1] + second[1])


def scale(vector: Point, scalar: float) -> Point:
    """Scale a 2D vector by a scalar factor.

    Parameters
    ----------
    vector : Point
        Vector to scale.
    scalar : float
        Scaling factor.

    Returns
    -------
    Point
        Scaled vector ``vector * scalar``.
    """
    return (vector[0] * scalar, vector[1] * scalar)


def norm(vector: Point) -> float:
    """Compute the Euclidean norm of a 2D vector.

    Parameters
    ----------
    vector : Point
        Vector whose magnitude should be returned.

    Returns
    -------
    float
        Euclidean length of ``vector``.
    """
    return float((vector[0] ** 2 + vector[1] ** 2) ** 0.5)


def unit_vector(vector: Point) -> Point:
    """Return a unit vector pointing in the same direction as ``vector``.

    Parameters
    ----------
    vector : Point
        Vector to normalise.

    Returns
    -------
    Point
        Normalised vector. ``(0.0, 0.0)`` is returned when ``vector`` has zero length.
    """
    magnitude = norm(vector)
    if magnitude == 0.0:
        return (0.0, 0.0)
    return (vector[0] / magnitude, vector[1] / magnitude)


def rotate90_ccw(vector: Point) -> Point:
    """Rotate a vector by +90° (counter-clockwise).

    Parameters
    ----------
    vector : Point
        Vector to rotate.

    Returns
    -------
    Point
        Vector rotated by +90° in the XY plane.
    """
    return (-vector[1], vector[0])


def rotate90_cw(vector: Point) -> Point:
    """Rotate a vector by -90° (clockwise).

    Parameters
    ----------
    vector : Point
        Vector to rotate.

    Returns
    -------
    Point
        Vector rotated by -90° in the XY plane.
    """
    return (vector[1], -vector[0])


def polygon_is_ccw(coords: Iterable[Point]) -> bool:
    """Check whether a closed polygon loop is counter-clockwise oriented.

    Parameters
    ----------
    coords : Iterable[Point]
        Ordered polygon vertices. The polygon is assumed to be closed, but the
        final repeated vertex is optional.

    Returns
    -------
    bool
        ``True`` when the polygon has positive signed area, ``False`` otherwise.
    """
    points = list(coords)
    if len(points) < 3:
        return False
    signed_area = 0.0
    for index in range(len(points)):
        x0, y0 = points[index]
        x1, y1 = points[(index + 1) % len(points)]
        signed_area += x0 * y1 - x1 * y0
    return signed_area > 0.0


__all__ = [
    "Point",
    "add",
    "norm",
    "polygon_is_ccw",
    "rotate90_ccw",
    "rotate90_cw",
    "scale",
    "subtract",
    "unit_vector",
]
