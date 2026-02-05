"""City placement algorithm for procedural map generation.

Implements the Centroid-based Radial Placement + Random Variance algorithm
as defined in ADR-001.
"""

from __future__ import annotations
import math
import random
from typing import Optional, Dict, Any

from ..models import City, Nation, MapState
from .geometry import Vec2, distance, centroid, angle_between


class CityPlacer:
    """Handles placement of new cities in the map.

    Uses a centroid-based radial placement algorithm with random variance
    to ensure cities expand outward from the center of mass.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the city placer with configuration.

        Args:
            config: Configuration dictionary with placement parameters.
        """
        config = config or {}
        city_config = config.get("city_placement", {})

        self.initial_triangle_radius: float = config.get("initial_triangle_radius", 100.0)
        self.min_distance: float = city_config.get("min_distance_from_existing", 80.0)
        self.max_distance: float = city_config.get("max_distance_from_existing", 200.0)
        self.angle_variance: float = city_config.get("placement_angle_variance", 30.0)
        self.max_attempts: int = city_config.get("placement_max_attempts", 100)

        # Convert angle variance to radians
        self.angle_variance_rad: float = math.radians(self.angle_variance)

    def create_initial_triangle(self, state: MapState) -> None:
        """Create the initial 3-city equilateral triangle.

        Places 2 player cities and 1 enemy city in an equilateral triangle
        centered at the origin.

        Args:
            state: The map state to add cities to.
        """
        # Create nations if they don't exist
        if not state.nations:
            player_nation = Nation(id=0, name="Player Kingdom", is_player=True)
            enemy_nation = Nation(id=1, name="Enemy Empire", is_player=False)
            state.add_nation(player_nation)
            state.add_nation(enemy_nation)

        # Calculate positions for equilateral triangle
        # First city at top (90 degrees / π/2 radians)
        angles = [
            math.pi / 2,           # Top (Player 1)
            math.pi / 2 + 2 * math.pi / 3,  # Bottom-left (Player 2)
            math.pi / 2 + 4 * math.pi / 3,  # Bottom-right (Enemy)
        ]

        # Player cities (indices 0, 1), Enemy city (index 2)
        nation_ids = [0, 0, 1]
        names = ["Capital", "Frontier", "Enemy Base"]

        for i, (angle, nation_id, name) in enumerate(zip(angles, nation_ids, names)):
            x = self.initial_triangle_radius * math.cos(angle)
            y = self.initial_triangle_radius * math.sin(angle)

            city = City(
                id=state.next_city_id(),
                x=x,
                y=y,
                owner_nation_id=nation_id,
                name=name,
            )
            state.add_city(city)

    def find_placement_position(
        self,
        state: MapState,
        rng: Optional[random.Random] = None,
    ) -> Optional[Vec2]:
        """Find a valid position for a new city.

        Uses the centroid-based radial placement algorithm:
        1. Calculate centroid of all existing cities
        2. Select a random base city
        3. Compute outward direction (away from centroid)
        4. Add angular variance
        5. Place at random distance from base city
        6. Validate minimum distance constraints

        Args:
            state: Current map state.
            rng: Random number generator (uses default if None).

        Returns:
            Valid position as Vec2, or None if no valid position found.
        """
        if rng is None:
            rng = random.Random()

        if not state.cities:
            # No cities yet - place at origin
            return Vec2(0, 0)

        # Calculate centroid of all cities
        city_positions = [Vec2(c.x, c.y) for c in state.cities]
        center = centroid(city_positions)

        for _ in range(self.max_attempts):
            # Select a random base city
            base_city = rng.choice(state.cities)
            base_pos = Vec2(base_city.x, base_city.y)

            # Calculate outward direction (away from centroid)
            if distance(base_pos, center) < 1e-6:
                # Base city is at centroid - pick random direction
                base_angle = rng.uniform(0, 2 * math.pi)
            else:
                base_angle = angle_between(center, base_pos)

            # Add angular variance
            angle = base_angle + rng.uniform(-self.angle_variance_rad, self.angle_variance_rad)

            # Random distance from base city
            dist = rng.uniform(self.min_distance, self.max_distance)

            # Calculate new position
            new_pos = Vec2(
                base_pos.x + dist * math.cos(angle),
                base_pos.y + dist * math.sin(angle),
            )

            # Validate position
            if self._is_valid_position(new_pos, state):
                return new_pos

        return None

    def _is_valid_position(self, pos: Vec2, state: MapState) -> bool:
        """Check if a position is valid for placing a new city.

        Args:
            pos: Proposed position.
            state: Current map state.

        Returns:
            True if position is valid.
        """
        for city in state.cities:
            dist = distance(pos, Vec2(city.x, city.y))
            if dist < self.min_distance:
                return False
        return True

    def add_city(
        self,
        state: MapState,
        nation_id: int,
        name: Optional[str] = None,
        rng: Optional[random.Random] = None,
    ) -> Optional[City]:
        """Add a new city to the map.

        Args:
            state: Map state to modify.
            nation_id: Nation that will own the new city.
            name: Optional name for the city.
            rng: Random number generator.

        Returns:
            The new City if placement succeeded, None otherwise.
        """
        position = self.find_placement_position(state, rng)

        if position is None:
            # Fallback: place at random position further out
            position = self._fallback_position(state, rng or random.Random())
            if position is None:
                return None

        city = City(
            id=state.next_city_id(),
            x=position.x,
            y=position.y,
            owner_nation_id=nation_id,
            name=name,
        )
        state.add_city(city)
        return city

    def _fallback_position(
        self,
        state: MapState,
        rng: random.Random,
    ) -> Optional[Vec2]:
        """Generate a fallback position when normal placement fails.

        Places the city at a larger distance with less constraints.

        Args:
            state: Current map state.
            rng: Random number generator.

        Returns:
            A position Vec2, or None if even fallback fails.
        """
        if not state.cities:
            return Vec2(0, 0)

        city_positions = [Vec2(c.x, c.y) for c in state.cities]
        center = centroid(city_positions)

        # Try placing further out from centroid
        for _ in range(50):
            angle = rng.uniform(0, 2 * math.pi)
            # Use 2x max distance for fallback
            dist = self.max_distance * 2 + rng.uniform(0, self.max_distance)

            new_pos = Vec2(
                center.x + dist * math.cos(angle),
                center.y + dist * math.sin(angle),
            )

            # Only check minimum distance (relaxed validation)
            valid = True
            for city in state.cities:
                if distance(new_pos, Vec2(city.x, city.y)) < self.min_distance * 0.5:
                    valid = False
                    break

            if valid:
                return new_pos

        return None
