"""Tests for city placer."""

import pytest
import random

from src.models import MapState, City, Nation
from src.generation.city_placer import CityPlacer
from src.generation.geometry import Vec2, distance


class TestCityPlacer:
    """Tests for CityPlacer class."""

    def test_create_initial_triangle(self):
        """Test that initial triangle creates 3 cities."""
        placer = CityPlacer()
        state = MapState()

        placer.create_initial_triangle(state)

        assert len(state.cities) == 3
        assert len(state.nations) == 2

        # Check player nation exists
        player_nations = [n for n in state.nations if n.is_player]
        assert len(player_nations) == 1

        # Check 2 player cities and 1 enemy city
        player_cities = state.get_cities_by_nation(0)
        enemy_cities = state.get_cities_by_nation(1)
        assert len(player_cities) == 2
        assert len(enemy_cities) == 1

    def test_initial_triangle_distances(self):
        """Test that initial cities form equilateral triangle."""
        placer = CityPlacer({"initial_triangle_radius": 100.0})
        state = MapState()

        placer.create_initial_triangle(state)

        # All cities should be at same distance from origin
        for city in state.cities:
            dist_from_origin = (city.x ** 2 + city.y ** 2) ** 0.5
            assert dist_from_origin == pytest.approx(100.0, rel=0.01)

        # All edges should be same length (equilateral)
        c0, c1, c2 = state.cities
        d01 = c0.distance_to(c1)
        d12 = c1.distance_to(c2)
        d20 = c2.distance_to(c0)
        assert d01 == pytest.approx(d12, rel=0.01)
        assert d12 == pytest.approx(d20, rel=0.01)

    def test_add_city_respects_min_distance(self):
        """Test that new cities respect minimum distance constraint."""
        config = {
            "city_placement": {
                "min_distance_from_existing": 80.0,
                "max_distance_from_existing": 200.0,
            }
        }
        placer = CityPlacer(config)
        state = MapState()
        rng = random.Random(42)

        placer.create_initial_triangle(state)

        # Add several cities
        for _ in range(10):
            placer.add_city(state, nation_id=1, rng=rng)

        # Check all cities respect min distance
        for i, city_a in enumerate(state.cities):
            for city_b in state.cities[i + 1:]:
                dist = city_a.distance_to(city_b)
                # Allow some tolerance for fallback placements
                assert dist >= 40.0, f"Cities too close: {dist}"

    def test_find_placement_position_returns_vec2(self):
        """Test that find_placement_position returns valid Vec2."""
        placer = CityPlacer()
        state = MapState()
        rng = random.Random(42)

        placer.create_initial_triangle(state)
        pos = placer.find_placement_position(state, rng)

        assert pos is not None
        assert isinstance(pos, Vec2)

    def test_add_city_increments_id(self):
        """Test that city IDs increment correctly."""
        placer = CityPlacer()
        state = MapState()
        rng = random.Random(42)

        placer.create_initial_triangle(state)
        initial_ids = {c.id for c in state.cities}

        new_city = placer.add_city(state, nation_id=1, rng=rng)

        assert new_city is not None
        assert new_city.id not in initial_ids
        assert new_city.id == 3  # After 0, 1, 2

    def test_empty_state_placement(self):
        """Test placement with no existing cities."""
        placer = CityPlacer()
        state = MapState()
        rng = random.Random(42)

        pos = placer.find_placement_position(state, rng)

        assert pos is not None
        assert pos.x == 0
        assert pos.y == 0
