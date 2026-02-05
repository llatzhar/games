"""Road generation algorithm for procedural map generation.

Implements the Nearest-First + Intersection Check + Fallback algorithm
as defined in ADR-002.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any, Tuple

from ..models import City, Road, MapState
from .geometry import Vec2, distance, segments_intersect


class RoadGenerator:
    """Handles generation of roads connecting cities.

    Uses a nearest-first approach with intersection avoidance
    to create a connected graph without crossing roads.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the road generator with configuration.

        Args:
            config: Configuration dictionary with road generation parameters.
        """
        config = config or {}
        road_config = config.get("road_generation", {})

        self.min_roads: int = road_config.get("min_roads_per_city", 1)
        self.max_roads: int = road_config.get("max_roads_per_city", 3)
        self.max_road_length: float = road_config.get("max_road_length", 150.0)
        self.check_intersections: bool = road_config.get("intersection_check", True)

    def create_initial_roads(self, state: MapState) -> None:
        """Create roads for the initial triangle of cities.

        Connects all three initial cities to each other.

        Args:
            state: Map state with initial cities.
        """
        if len(state.cities) < 3:
            return

        # Connect all initial cities in a triangle
        for i in range(3):
            for j in range(i + 1, 3):
                road = Road(
                    city_a_id=state.cities[i].id,
                    city_b_id=state.cities[j].id,
                )
                state.add_road(road)

    def generate_roads_for_city(
        self,
        city: City,
        state: MapState,
    ) -> List[Road]:
        """Generate roads connecting a new city to existing cities.

        Uses the nearest-first algorithm with intersection checking:
        1. Sort existing cities by distance
        2. For each candidate (nearest first):
           - Check road length <= max
           - Check no intersection with existing roads
        3. Add road if valid
        4. Continue until min-max roads created

        Args:
            city: The new city to connect.
            state: Current map state (may be modified).

        Returns:
            List of roads that were created.
        """
        created_roads: List[Road] = []

        # Get all other cities sorted by distance
        other_cities = [c for c in state.cities if c.id != city.id]
        if not other_cities:
            return created_roads

        # Sort by distance (nearest first)
        other_cities.sort(key=lambda c: city.distance_to(c))

        city_pos = Vec2(city.x, city.y)

        for candidate in other_cities:
            if len(created_roads) >= self.max_roads:
                break

            candidate_pos = Vec2(candidate.x, candidate.y)

            # Check road length
            road_length = distance(city_pos, candidate_pos)
            if road_length > self.max_road_length:
                continue

            # Check if road already exists
            potential_road = Road(city_a_id=city.id, city_b_id=candidate.id)
            if potential_road in state.roads:
                continue

            # Check for intersections
            if self.check_intersections:
                new_segment = (city_pos, candidate_pos)

                # Check against existing roads
                intersects_existing = self._intersects_existing_roads(
                    new_segment, state, city.id, candidate.id
                )
                if intersects_existing:
                    continue

                # Check against roads created in this batch
                intersects_new = self._intersects_roads_in_list(
                    new_segment, created_roads, city, state
                )
                if intersects_new:
                    continue

            # Road is valid - add it
            state.add_road(potential_road)
            created_roads.append(potential_road)

        # Fallback: if no roads created, force-connect to nearest
        if len(created_roads) < self.min_roads and other_cities:
            self._fallback_connect(city, other_cities[0], state, created_roads)

        return created_roads

    def _intersects_existing_roads(
        self,
        new_segment: Tuple[Vec2, Vec2],
        state: MapState,
        new_city_id: int,
        target_city_id: int,
    ) -> bool:
        """Check if a new road segment intersects any existing roads.

        Args:
            new_segment: The proposed road segment.
            state: Current map state.
            new_city_id: ID of the new city.
            target_city_id: ID of the target city.

        Returns:
            True if there's an intersection.
        """
        for road in state.roads:
            # Roads sharing an endpoint don't count as intersecting
            if road.connects(new_city_id) or road.connects(target_city_id):
                continue

            city_a = state.get_city_by_id(road.city_a_id)
            city_b = state.get_city_by_id(road.city_b_id)

            if city_a is None or city_b is None:
                continue

            existing_segment = (Vec2(city_a.x, city_a.y), Vec2(city_b.x, city_b.y))

            if segments_intersect(new_segment, existing_segment):
                return True

        return False

    def _intersects_roads_in_list(
        self,
        new_segment: Tuple[Vec2, Vec2],
        roads: List[Road],
        new_city: City,
        state: MapState,
    ) -> bool:
        """Check if a new road segment intersects roads in a list.

        Args:
            new_segment: The proposed road segment.
            roads: List of roads to check against.
            new_city: The new city being connected.
            state: Map state for city lookups.

        Returns:
            True if there's an intersection.
        """
        for road in roads:
            # Roads sharing the new city don't count as intersecting
            if road.connects(new_city.id):
                continue

            city_a = state.get_city_by_id(road.city_a_id)
            city_b = state.get_city_by_id(road.city_b_id)

            if city_a is None or city_b is None:
                continue

            existing_segment = (Vec2(city_a.x, city_a.y), Vec2(city_b.x, city_b.y))

            if segments_intersect(new_segment, existing_segment):
                return True

        return False

    def _fallback_connect(
        self,
        city: City,
        nearest: City,
        state: MapState,
        created_roads: List[Road],
    ) -> None:
        """Force-connect a city to its nearest neighbor.

        This may create an intersecting road, but ensures connectivity.

        Args:
            city: The city to connect.
            nearest: The nearest city.
            state: Map state to modify.
            created_roads: List to append the new road to.
        """
        road = Road(city_a_id=city.id, city_b_id=nearest.id)
        if road not in state.roads:
            state.add_road(road)
            created_roads.append(road)
