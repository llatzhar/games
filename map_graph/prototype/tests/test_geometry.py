"""Tests for geometry utilities."""

import pytest
import math

from src.generation.geometry import (
    Vec2,
    distance,
    angle_between,
    ccw,
    segments_intersect,
    centroid,
    EPSILON,
)


class TestVec2:
    """Tests for Vec2 class."""

    def test_addition(self):
        v1 = Vec2(1, 2)
        v2 = Vec2(3, 4)
        result = v1 + v2
        assert result.x == 4
        assert result.y == 6

    def test_subtraction(self):
        v1 = Vec2(5, 7)
        v2 = Vec2(2, 3)
        result = v1 - v2
        assert result.x == 3
        assert result.y == 4

    def test_scalar_multiplication(self):
        v = Vec2(2, 3)
        result = v * 2
        assert result.x == 4
        assert result.y == 6

    def test_length(self):
        v = Vec2(3, 4)
        assert v.length() == pytest.approx(5.0)

    def test_normalized(self):
        v = Vec2(3, 4)
        n = v.normalized()
        assert n.length() == pytest.approx(1.0)
        assert n.x == pytest.approx(0.6)
        assert n.y == pytest.approx(0.8)

    def test_dot_product(self):
        v1 = Vec2(1, 2)
        v2 = Vec2(3, 4)
        assert v1.dot(v2) == 11

    def test_cross_product(self):
        v1 = Vec2(1, 0)
        v2 = Vec2(0, 1)
        assert v1.cross(v2) == 1

    def test_rotate(self):
        v = Vec2(1, 0)
        rotated = v.rotate(math.pi / 2)  # 90 degrees
        assert rotated.x == pytest.approx(0, abs=1e-6)
        assert rotated.y == pytest.approx(1, abs=1e-6)

    def test_from_angle(self):
        v = Vec2.from_angle(0, 5)
        assert v.x == pytest.approx(5)
        assert v.y == pytest.approx(0)

        v2 = Vec2.from_angle(math.pi / 2, 3)
        assert v2.x == pytest.approx(0, abs=1e-6)
        assert v2.y == pytest.approx(3, abs=1e-6)


class TestDistance:
    """Tests for distance function."""

    def test_simple_distance(self):
        p1 = Vec2(0, 0)
        p2 = Vec2(3, 4)
        assert distance(p1, p2) == pytest.approx(5.0)

    def test_same_point(self):
        p = Vec2(5, 5)
        assert distance(p, p) == pytest.approx(0.0)


class TestCCW:
    """Tests for CCW orientation function."""

    def test_counter_clockwise(self):
        a = Vec2(0, 0)
        b = Vec2(1, 0)
        c = Vec2(1, 1)
        assert ccw(a, b, c) > 0

    def test_clockwise(self):
        a = Vec2(0, 0)
        b = Vec2(1, 0)
        c = Vec2(1, -1)
        assert ccw(a, b, c) < 0

    def test_collinear(self):
        a = Vec2(0, 0)
        b = Vec2(1, 1)
        c = Vec2(2, 2)
        assert abs(ccw(a, b, c)) < EPSILON


class TestSegmentsIntersect:
    """Tests for segment intersection function."""

    def test_crossing_segments(self):
        seg1 = (Vec2(0, 0), Vec2(2, 2))
        seg2 = (Vec2(0, 2), Vec2(2, 0))
        assert segments_intersect(seg1, seg2) is True

    def test_parallel_segments(self):
        seg1 = (Vec2(0, 0), Vec2(2, 0))
        seg2 = (Vec2(0, 1), Vec2(2, 1))
        assert segments_intersect(seg1, seg2) is False

    def test_non_crossing_segments(self):
        seg1 = (Vec2(0, 0), Vec2(1, 0))
        seg2 = (Vec2(2, 0), Vec2(3, 0))
        assert segments_intersect(seg1, seg2) is False

    def test_shared_endpoint(self):
        # Shared endpoints should NOT count as intersection
        seg1 = (Vec2(0, 0), Vec2(1, 1))
        seg2 = (Vec2(1, 1), Vec2(2, 0))
        assert segments_intersect(seg1, seg2) is False

    def test_t_intersection(self):
        # T intersection (one endpoint on the other segment)
        seg1 = (Vec2(0, 0), Vec2(2, 0))
        seg2 = (Vec2(1, -1), Vec2(1, 1))
        assert segments_intersect(seg1, seg2) is True

    def test_collinear_overlapping(self):
        # Overlapping collinear segments
        seg1 = (Vec2(0, 0), Vec2(2, 0))
        seg2 = (Vec2(1, 0), Vec2(3, 0))
        assert segments_intersect(seg1, seg2) is True

    def test_collinear_non_overlapping(self):
        # Non-overlapping collinear segments
        seg1 = (Vec2(0, 0), Vec2(1, 0))
        seg2 = (Vec2(2, 0), Vec2(3, 0))
        assert segments_intersect(seg1, seg2) is False


class TestCentroid:
    """Tests for centroid function."""

    def test_single_point(self):
        points = [Vec2(5, 5)]
        c = centroid(points)
        assert c.x == pytest.approx(5)
        assert c.y == pytest.approx(5)

    def test_two_points(self):
        points = [Vec2(0, 0), Vec2(10, 10)]
        c = centroid(points)
        assert c.x == pytest.approx(5)
        assert c.y == pytest.approx(5)

    def test_triangle(self):
        points = [Vec2(0, 0), Vec2(3, 0), Vec2(0, 3)]
        c = centroid(points)
        assert c.x == pytest.approx(1)
        assert c.y == pytest.approx(1)

    def test_empty_list(self):
        c = centroid([])
        assert c.x == 0
        assert c.y == 0
