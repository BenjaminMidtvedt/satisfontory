"""Helpers to convert rectangle strips into blueprint line primitives."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class Line:
    """Pose and length of a straight segment in world space.

    Parameters
    ----------
    length : float
        Length of the segment.
    rotation : dict of str to float
        Quaternion describing the segment orientation.
    translation : dict of str to float
        Translation vector for the start of the segment.
    """

    length: float
    rotation: dict[str, float]
    translation: dict[str, float]


def lines_to_world(lines: np.ndarray) -> list[Line]:
    """Convert 2D line segments into 3D poses for the blueprint format.

    Parameters
    ----------
    lines : ndarray, shape (N, 2, 2)
        ``lines[i, 0]`` is the start point and ``lines[i, 1]`` is the end point of segment *i*.

    Returns
    -------
    list of Line
        Blueprint-compatible line descriptors.

    Raises
    ------
    ValueError
        If ``lines`` does not have shape ``(N, 2, 2)``.
    """
    if lines.ndim != 3 or lines.shape[1:] != (2, 2):
        raise ValueError("Expected an array of shape (N, 2, 2).")

    starts = lines[:, 0, :].astype(float)
    ends = lines[:, 1, :].astype(float)

    deltas = ends - starts
    dx = deltas[:, 0]
    dy = deltas[:, 1]

    lengths = np.hypot(dx, dy)
    thetas = np.arctan2(dy, dx)

    half_angles = 0.5 * thetas
    sin_half = np.sin(half_angles)
    cos_half = np.cos(half_angles)

    zero_mask = lengths == 0.0
    z_component = sin_half.copy()
    w_component = cos_half.copy()
    z_component[zero_mask] = 0.0
    w_component[zero_mask] = 1.0

    blueprint_lines: list[Line] = []
    for index in range(lines.shape[0]):
        blueprint_lines.append(
            Line(
                length=float(lengths[index]),
                rotation={"x": 0.0, "y": 0.0, "z": float(z_component[index]), "w": float(w_component[index])},
                translation={"x": float(starts[index, 0]), "y": float(starts[index, 1]), "z": 0.0},
            ),
        )
    return blueprint_lines


__all__ = ["Line", "lines_to_world"]
