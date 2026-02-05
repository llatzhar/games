"""Tests for road generator."""

import pytest
import random

from src.models import MapState, City, Nation, Road
from src.generation.city_placer import CityPlacer
from src.generation.road_generator import RoadGenerator
from src.generation.geometry import Vec2, segments_intersect


class TestRoadGenerator:
    """Tests for RoadGenerator class."""

    def test_create_initial_roads(self):
        """Test that initial roads connect all 3 cities."""
        placer = CityPlacer()
        generator = RoadGenerator()
        state = MapState()

        placer.create_initial_triangle(state)
        generator.create_initial_roads(state)

        # Should have 3 roads (triangle)
        assert len(state.roads) == 3

        # Each city should have 2 connections
        for city in state.cities:
            roads = state.get_roads_for_city(city.id)
            assert len(roads) == 2

    def test_generate_roads_for_city(self):
        """Test road generation for a new city."""
        config = {
            "road_generation": {
                "min_roads_per_city": 1,
                "max_roads_per_city": 3,
                "max_road_length": 150.0,
            }
        }
        placer = CityPlacer()
        generator = RoadGenerator(config)
        state = MapState()
        rng = random.Random(42)

        # Create initial map
        placer.create_initial_triangle(state)
        generator.create_initial_roads(state)

        # Add a new city
        new_city = placer.add_city(state, nation_id=1, rng=rng)
        assert new_city is not None

        # Generate roads for new city
        new_roads = generator.generate_roads_for_city(new_city, state)

        # Should have at least 1 road
        assert len(new_roads) >= 1

        # New city should be connected
        city_roads = state.get_roads_for_city(new_city.id)
        assert len(city_roads) >= 1

    def test_road_length_constraint(self):
        """Test that roads respect max length constraint."""
        config = {
            "road_generation": {
                "max_road_length": 100.0,
            }
        }
        generator = RoadGenerator(config)
        state = MapState()

        # Create nations
        state.add_nation(Nation(0, "Player", True))

        # Create cities far apart
        state.add_city(City(0, 0, 0, 0))
        state.add_city(City(1, 200, 0, 0))  # Too far
        state.add_city(City(2, 50, 0, 0))   # Close enough

        # Add a city near city 0
        new_city = City(3, 30, 30, 0)
        state.add_city(new_city)

        # Generate roads
        new_roads = generator.generate_roads_for_city(new_city, state)

        # Check all roads are within max length
        for road in new_roads:
            city_a = state.get_city_by_id(road.city_a_id)
            city_b = state.get_city_by_id(road.city_b_id)
            assert city_a is not None
            assert city_b is not None
            dist = city_a.distance_to(city_b)
            assert dist <= config["road_generation"]["max_road_length"]

    def test_no_duplicate_roads(self):
        """Test that duplicate roads are not created."""
        placer = CityPlacer()
        generator = RoadGenerator()
        state = MapState()

        placer.create_initial_triangle(state)
        generator.create_initial_roads(state)

        initial_road_count = len(state.roads)

        # Try to create initial roads again
        generator.create_initial_roads(state)

        # Should have same number of roads
        assert len(state.roads) == initial_road_count

    def test_fallback_connection(self):
        """Test that fallback ensures at least one connection."""
        config = {
            "road_generation": {
                "min_roads_per_city": 1,
                "max_roads_per_city": 1,
                "max_road_length": 10.0,  # Very short
                "intersection_check": True,
            }
        }
        generator = RoadGenerator(config)
        state = MapState()

        # Create nations
        state.add_nation(Nation(0, "Player", True))

        # Create cities far apart
        state.add_city(City(0, 0, 0, 0))
        state.add_city(City(1, 100, 0, 0))

        # Add a city
        new_city = City(2, 200, 0, 0)
        state.add_city(new_city)

        # Generate roads - should fallback to nearest
        new_roads = generator.generate_roads_for_city(new_city, state)

        # Should have at least 1 road due to fallback
        assert len(new_roads) >= 1

    def test_intersection_avoidance(self):
        """Test that roads avoid intersections when possible."""
        config = {
            "road_generation": {
                "min_roads_per_city": 1,
                "max_roads_per_city": 3,
                "max_road_length": 200.0,
                "intersection_check": True,
            }
        }
        placer = CityPlacer()
        generator = RoadGenerator(config)
        state = MapState()
        rng = random.Random(42)

        # Create initial map
        placer.create_initial_triangle(state)
        generator.create_initial_roads(state)

        # Add several cities
        for _ in range(10):
            new_city = placer.add_city(state, nation_id=1, rng=rng)
            if new_city:
                generator.generate_roads_for_city(new_city, state)

        # Count intersections (excluding shared endpoints)
        intersection_count = 0
        for i, road_a in enumerate(state.roads):
            city_a1 = state.get_city_by_id(road_a.city_a_id)
            city_a2 = state.get_city_by_id(road_a.city_b_id)
            assert city_a1 is not None
            assert city_a2 is not None
            seg_a = (Vec2(city_a1.x, city_a1.y), Vec2(city_a2.x, city_a2.y))

            for road_b in state.roads[i + 1:]:
                # Skip roads that share an endpoint
                if (road_a.city_a_id in (road_b.city_a_id, road_b.city_b_id) or
                    road_a.city_b_id in (road_b.city_a_id, road_b.city_b_id)):
                    continue

                city_b1 = state.get_city_by_id(road_b.city_a_id)
                city_b2 = state.get_city_by_id(road_b.city_b_id)
                assert city_b1 is not None
                assert city_b2 is not None
                seg_b = (Vec2(city_b1.x, city_b1.y), Vec2(city_b2.x, city_b2.y))

                if segments_intersect(seg_a, seg_b):
                    intersection_count += 1

        # Some intersections may occur due to fallback, but should be minimal
        # Allow up to 2 for fallback cases
        assert intersection_count <= 2, f"Too many intersections: {intersection_count}"
