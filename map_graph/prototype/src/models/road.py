"""Road model - represents an edge in the map graph."""

from dataclasses import dataclass


@dataclass
class Road:
    """A road (edge) connecting two cities in the map graph.

    Attributes:
        city_a_id: ID of the first city.
        city_b_id: ID of the second city.
    """

    city_a_id: int
    city_b_id: int

    def __post_init__(self) -> None:
        """Ensure consistent ordering (smaller ID first)."""
        if self.city_a_id > self.city_b_id:
            self.city_a_id, self.city_b_id = self.city_b_id, self.city_a_id

    def connects(self, city_id: int) -> bool:
        """Check if this road connects to a given city."""
        return city_id == self.city_a_id or city_id == self.city_b_id

    def other_city(self, city_id: int) -> int:
        """Get the ID of the other city connected by this road."""
        if city_id == self.city_a_id:
            return self.city_b_id
        elif city_id == self.city_b_id:
            return self.city_a_id
        else:
            raise ValueError(f"City {city_id} is not connected by this road")

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON export."""
        return {
            "city_a": self.city_a_id,
            "city_b": self.city_b_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Road":
        """Deserialize from dictionary."""
        return cls(
            city_a_id=data["city_a"],
            city_b_id=data["city_b"],
        )

    def __eq__(self, other: object) -> bool:
        """Roads are equal if they connect the same cities."""
        if not isinstance(other, Road):
            return NotImplemented
        return self.city_a_id == other.city_a_id and self.city_b_id == other.city_b_id

    def __hash__(self) -> int:
        """Hash for use in sets and dicts."""
        return hash((self.city_a_id, self.city_b_id))
