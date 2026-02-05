"""City model - represents a node in the map graph."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class City:
    """A city (node) in the map graph.

    Attributes:
        id: Unique identifier for the city.
        x: X coordinate in world space.
        y: Y coordinate in world space.
        owner_nation_id: ID of the nation that owns this city.
        name: Optional display name for the city.
    """

    id: int
    x: float
    y: float
    owner_nation_id: int
    name: Optional[str] = None

    def __post_init__(self) -> None:
        """Generate default name if not provided."""
        if self.name is None:
            self.name = f"City_{self.id}"

    def distance_to(self, other: "City") -> float:
        """Calculate Euclidean distance to another city."""
        dx = self.x - other.x
        dy = self.y - other.y
        return (dx * dx + dy * dy) ** 0.5

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON export."""
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "owner_nation_id": self.owner_nation_id,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "City":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            x=data["x"],
            y=data["y"],
            owner_nation_id=data["owner_nation_id"],
            name=data.get("name"),
        )
