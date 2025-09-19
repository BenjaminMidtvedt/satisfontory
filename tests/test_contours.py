from __future__ import annotations

import math

from parser.contours import FTContour, freetype_outline_to_contours


def test_freetype_outline_to_contours_scaling(font_face) -> None:
    contours_small, flags_small = freetype_outline_to_contours(font_face, "g", 64)
    contours_large, flags_large = freetype_outline_to_contours(font_face, "g", 128)

    assert contours_small
    assert flags_small == flags_large
    assert isinstance(contours_small[0], FTContour)

    small_x_values = [point[0] for contour in contours_small for point in contour.points]
    large_x_values = [point[0] for contour in contours_large for point in contour.points]
    assert max(large_x_values) > max(small_x_values)

    bools = [value for contour in contours_small for value in contour.on_curve]
    assert bools
    assert all(isinstance(value, bool) for value in bools)
    assert any(value is False for value in bools)


def test_freetype_outline_to_contours_returns_ordered_points(font_face) -> None:
    contours, _ = freetype_outline_to_contours(font_face, "B", 96)
    assert contours
    first = contours[0]
    distances = []
    for current, nxt in zip(first.points, first.points[1:]):
        dx = nxt[0] - current[0]
        dy = nxt[1] - current[1]
        distances.append(math.hypot(dx, dy))
    assert all(distance >= 0.0 for distance in distances)
