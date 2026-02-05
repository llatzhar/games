"""Nation model - represents a faction in the game."""

from dataclasses import dataclass


@dataclass
class Nation:
    """A nation (faction) that owns cities.

    Attributes:
        id: Unique identifier for the nation.
        name: Display name for the nation.
        is_player: True if this is the player's nation.
    """

    id: int
    name: str
    is_player: bool = False

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON export."""
        return {
            "id": self.id,
            "name": self.name,
            "is_player": self.is_player,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Nation":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            is_player=data.get("is_player", False),
        )
