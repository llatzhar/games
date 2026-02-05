"""Geometry utilities for map generation.

Provides 2D vector operations, line segment intersection detection,
and distance/angle calculations.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
import math

# Epsilon for floating-point comparisons
EPSILON = 1e-9


@dataclass
class Vec2:
    """A 2D vector/point.

    Attributes:
        x: X coordinate.
        y: Y coordinate.
    """

    x: float
    y: float

    def __add__(self, other: Vec2) -> Vec2:
        """Vector addition."""
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec2) -> Vec2:
        """Vector subtraction."""
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vec2:
        """Scalar multiplication."""
        return Vec2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> Vec2:
        """Scalar multiplication (reversed)."""
        return self * scalar

    def __truediv__(self, scalar: float) -> Vec2:
        """Scalar division."""
        return Vec2(self.x / scalar, self.y / scalar)

    def __eq__(self, other: object) -> bool:
        """Check equality with epsilon tolerance."""
        if not isinstance(other, Vec2):
            return NotImplemented
        return abs(self.x - other.x) < EPSILON and abs(self.y - other.y) < EPSILON

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((round(self.x, 6), round(self.y, 6)))

    def length(self) -> float:
        """Get the length (magnitude) of the vector."""
        return math.sqrt(self.x * self.x + self.y * self.y)

    def length_squared(self) -> float:
        """Get the squared length (avoids sqrt for comparisons)."""
        return self.x * self.x + self.y * self.y

    def normalized(self) -> Vec2:
        """Get a unit vector in the same direction."""
        length = self.length()
        if length < EPSILON:
            return Vec2(0, 0)
        return self / length

    def dot(self, other: Vec2) -> float:
        """Dot product with another vector."""
        return self.x * other.x + self.y * other.y

    def cross(self, other: Vec2) -> float:
        """2D cross product (returns scalar z-component)."""
        return self.x * other.y - self.y * other.x

    def rotate(self, angle_rad: float) -> Vec2:
        """Rotate the vector by an angle (in radians)."""
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        return Vec2(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a,
        )

    def angle(self) -> float:
        """Get the angle of this vector from the positive X axis (in radians)."""
        return math.atan2(self.y, self.x)

    def to_tuple(self) -> Tuple[float, float]:
        """Convert to tuple."""
        return (self.x, self.y)

    @classmethod
    def from_tuple(cls, t: Tuple[float, float]) -> Vec2:
        """Create from tuple."""
        return cls(t[0], t[1])

    @classmethod
    def from_angle(cls, angle_rad: float, length: float = 1.0) -> Vec2:
        """Create a vector from an angle and length."""
        return cls(math.cos(angle_rad) * length, math.sin(angle_rad) * length)


def distance(p1: Vec2, p2: Vec2) -> float:
    """Calculate Euclidean distance between two points."""
    return (p2 - p1).length()


def distance_squared(p1: Vec2, p2: Vec2) -> float:
    """Calculate squared distance between two points (faster than distance)."""
    return (p2 - p1).length_squared()


def angle_between(p1: Vec2, p2: Vec2) -> float:
    """Calculate the angle from p1 to p2 (in radians)."""
    delta = p2 - p1
    return math.atan2(delta.y, delta.x)


def ccw(a: Vec2, b: Vec2, c: Vec2) -> float:
    """Counter-clockwise orientation test.

    Returns:
        Positive if a->b->c is counter-clockwise.
        Negative if clockwise.
        Zero if collinear.
    """
    return (b - a).cross(c - a)


def segments_intersect(
    seg1: Tuple[Vec2, Vec2],
    seg2: Tuple[Vec2, Vec2],
    allow_endpoint_touch: bool = False,
) -> bool:
    """Check if two line segments intersect.

    Uses the CCW (counter-clockwise) algorithm for robust intersection detection.

    Args:
        seg1: First segment as (start, end) tuple.
        seg2: Second segment as (start, end) tuple.
        allow_endpoint_touch: If True, segments sharing exactly one endpoint
                              are not considered intersecting.

    Returns:
        True if the segments intersect, False otherwise.
    """
    a, b = seg1
    c, d = seg2

    # Check for shared endpoints
    if not allow_endpoint_touch:
        if a == c or a == d or b == c or b == d:
            return False

    d1 = ccw(a, b, c)
    d2 = ccw(a, b, d)
    d3 = ccw(c, d, a)
    d4 = ccw(c, d, b)

    # General case: segments cross each other
    if ((d1 > EPSILON and d2 < -EPSILON) or (d1 < -EPSILON and d2 > EPSILON)) and \
       ((d3 > EPSILON and d4 < -EPSILON) or (d3 < -EPSILON and d4 > EPSILON)):
        return True

    # Collinear cases - check if segments overlap
    if abs(d1) < EPSILON and _on_segment(a, c, b):
        return True
    if abs(d2) < EPSILON and _on_segment(a, d, b):
        return True
    if abs(d3) < EPSILON and _on_segment(c, a, d):
        return True
    if abs(d4) < EPSILON and _on_segment(c, b, d):
        return True

    return False


def _on_segment(p: Vec2, q: Vec2, r: Vec2) -> bool:
    """Check if point q lies on segment p-r (assuming collinear points)."""
    return (
        min(p.x, r.x) - EPSILON <= q.x <= max(p.x, r.x) + EPSILON
        and min(p.y, r.y) - EPSILON <= q.y <= max(p.y, r.y) + EPSILON
    )


def point_to_segment_distance(point: Vec2, seg_start: Vec2, seg_end: Vec2) -> float:
    """Calculate the minimum distance from a point to a line segment."""
    seg = seg_end - seg_start
    seg_len_sq = seg.length_squared()

    if seg_len_sq < EPSILON:
        # Segment is a point
        return distance(point, seg_start)

    # Project point onto the line, clamped to segment
    t = max(0, min(1, (point - seg_start).dot(seg) / seg_len_sq))
    projection = seg_start + seg * t

    return distance(point, projection)


def centroid(points: list[Vec2]) -> Vec2:
    """Calculate the centroid (average position) of a list of points."""
    if not points:
        return Vec2(0, 0)

    total_x = sum(p.x for p in points)
    total_y = sum(p.y for p in points)
    n = len(points)

    return Vec2(total_x / n, total_y / n)
