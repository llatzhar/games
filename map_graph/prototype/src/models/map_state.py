"""MapState and MapHistory models - core game state containers."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
import copy

from .city import City
from .road import Road
from .nation import Nation


@dataclass
class MapState:
    """The complete state of the map at a point in time.

    Attributes:
        cities: List of all cities in the map.
        roads: List of all roads connecting cities.
        nations: List of all nations in the game.
        current_turn: The current game turn number.
    """

    cities: List[City] = field(default_factory=list)
    roads: List[Road] = field(default_factory=list)
    nations: List[Nation] = field(default_factory=list)
    current_turn: int = 0

    def add_city(self, city: City) -> None:
        """Add a city to the map."""
        self.cities.append(city)

    def add_road(self, road: Road) -> None:
        """Add a road to the map if it doesn't already exist."""
        if road not in self.roads:
            self.roads.append(road)

    def add_nation(self, nation: Nation) -> None:
        """Add a nation to the game."""
        self.nations.append(nation)

    def get_city_by_id(self, city_id: int) -> Optional[City]:
        """Get a city by its ID."""
        for city in self.cities:
            if city.id == city_id:
                return city
        return None

    def get_nation_by_id(self, nation_id: int) -> Optional[Nation]:
        """Get a nation by its ID."""
        for nation in self.nations:
            if nation.id == nation_id:
                return nation
        return None

    def get_neighbors(self, city_id: int) -> List[City]:
        """Get all cities connected to a given city by roads."""
        neighbor_ids = []
        for road in self.roads:
            if road.connects(city_id):
                neighbor_ids.append(road.other_city(city_id))

        return [c for c in self.cities if c.id in neighbor_ids]

    def get_roads_for_city(self, city_id: int) -> List[Road]:
        """Get all roads connected to a given city."""
        return [road for road in self.roads if road.connects(city_id)]

    def get_cities_by_nation(self, nation_id: int) -> List[City]:
        """Get all cities owned by a nation."""
        return [c for c in self.cities if c.owner_nation_id == nation_id]

    def next_city_id(self) -> int:
        """Get the next available city ID."""
        if not self.cities:
            return 0
        return max(c.id for c in self.cities) + 1

    def next_nation_id(self) -> int:
        """Get the next available nation ID."""
        if not self.nations:
            return 0
        return max(n.id for n in self.nations) + 1

    def deep_copy(self) -> "MapState":
        """Create a deep copy of this map state."""
        return copy.deepcopy(self)

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON export."""
        return {
            "cities": [c.to_dict() for c in self.cities],
            "roads": [r.to_dict() for r in self.roads],
            "nations": [n.to_dict() for n in self.nations],
            "current_turn": self.current_turn,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MapState":
        """Deserialize from dictionary."""
        state = cls()
        state.cities = [City.from_dict(c) for c in data.get("cities", [])]
        state.roads = [Road.from_dict(r) for r in data.get("roads", [])]
        state.nations = [Nation.from_dict(n) for n in data.get("nations", [])]
        state.current_turn = data.get("current_turn", 0)
        return state


class MapHistory:
    """Stores snapshots of MapState for generation history navigation.

    Allows stepping forward and backward through the evolution of the map.
    """

    def __init__(self) -> None:
        """Initialize empty history."""
        self._snapshots: List[MapState] = []
        self._current_index: int = -1

    def save_snapshot(self, state: MapState) -> None:
        """Save a deep copy of the current state as a new snapshot.

        If we're not at the end of history, truncate future snapshots.
        """
        # Truncate any "future" snapshots if we're in the middle of history
        if self._current_index < len(self._snapshots) - 1:
            self._snapshots = self._snapshots[: self._current_index + 1]

        self._snapshots.append(state.deep_copy())
        self._current_index = len(self._snapshots) - 1

    def get_current(self) -> Optional[MapState]:
        """Get the current snapshot."""
        if 0 <= self._current_index < len(self._snapshots):
            return self._snapshots[self._current_index].deep_copy()
        return None

    def go_to(self, index: int) -> Optional[MapState]:
        """Go to a specific snapshot index."""
        if 0 <= index < len(self._snapshots):
            self._current_index = index
            return self.get_current()
        return None

    def prev(self) -> Optional[MapState]:
        """Go to the previous snapshot."""
        if self._current_index > 0:
            self._current_index -= 1
            return self.get_current()
        return None

    def next(self) -> Optional[MapState]:
        """Go to the next snapshot."""
        if self._current_index < len(self._snapshots) - 1:
            self._current_index += 1
            return self.get_current()
        return None

    def can_go_prev(self) -> bool:
        """Check if we can go to a previous snapshot."""
        return self._current_index > 0

    def can_go_next(self) -> bool:
        """Check if we can go to a next snapshot."""
        return self._current_index < len(self._snapshots) - 1

    @property
    def current_index(self) -> int:
        """Get the current snapshot index."""
        return self._current_index

    @property
    def total_snapshots(self) -> int:
        """Get the total number of snapshots."""
        return len(self._snapshots)

    def clear(self) -> None:
        """Clear all snapshots."""
        self._snapshots.clear()
        self._current_index = -1
