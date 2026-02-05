"""Renderer for the map viewer.

Draws cities, roads, and other map elements to the Pyxel screen.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
import pyxel

from ..models import MapState, City, Road
from .camera import Camera


class Renderer:
    """Renders the map to the Pyxel screen.

    Draws cities as circles and roads as lines, with colors
    based on nation ownership.
    """

    def __init__(self, camera: Camera, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the renderer.

        Args:
            camera: Camera for coordinate transformation.
            config: Configuration dictionary with color settings.
        """
        self.camera = camera
        config = config or {}
        colors = config.get("colors", {})

        # Colors (Pyxel palette indices)
        self.bg_color: int = colors.get("background", 0)
        self.player_city_color: int = colors.get("player_city", 12)
        self.enemy_city_color: int = colors.get("enemy_city", 8)
        self.road_color: int = colors.get("road", 5)
        self.text_color: int = colors.get("ui_text", 7)

        # Rendering settings
        self.city_radius: int = 5
        self.show_labels: bool = True

    def clear(self) -> None:
        """Clear the screen."""
        pyxel.cls(self.bg_color)

    def draw_map(self, state: MapState) -> None:
        """Draw the entire map.

        Args:
            state: Map state to render.
        """
        # Draw roads first (below cities)
        self._draw_roads(state)

        # Draw cities on top
        self._draw_cities(state)

    def _draw_roads(self, state: MapState) -> None:
        """Draw all roads.

        Args:
            state: Map state containing roads.
        """
        for road in state.roads:
            city_a = state.get_city_by_id(road.city_a_id)
            city_b = state.get_city_by_id(road.city_b_id)

            if city_a is None or city_b is None:
                continue

            # Convert to screen coordinates
            ax, ay = self.camera.world_to_screen(city_a.x, city_a.y)
            bx, by = self.camera.world_to_screen(city_b.x, city_b.y)

            # Draw line
            pyxel.line(ax, ay, bx, by, self.road_color)

    def _draw_cities(self, state: MapState) -> None:
        """Draw all cities.

        Args:
            state: Map state containing cities.
        """
        for city in state.cities:
            self._draw_city(city, state)

    def _draw_city(self, city: City, state: MapState) -> None:
        """Draw a single city.

        Args:
            city: City to draw.
            state: Map state for nation lookup.
        """
        # Convert to screen coordinates
        sx, sy = self.camera.world_to_screen(city.x, city.y)

        # Determine color based on nation
        nation = state.get_nation_by_id(city.owner_nation_id)
        if nation and nation.is_player:
            color = self.player_city_color
        else:
            color = self.enemy_city_color

        # Calculate scaled radius
        radius = max(2, int(self.city_radius * self.camera.zoom))

        # Draw filled circle
        pyxel.circ(sx, sy, radius, color)

        # Draw border
        pyxel.circb(sx, sy, radius, self.text_color)

        # Draw label
        if self.show_labels and self.camera.zoom >= 0.5:
            label = city.name or f"C{city.id}"
            # Truncate label if too long
            if len(label) > 8:
                label = label[:7] + "."

            text_x = sx - len(label) * 2
            text_y = sy - radius - 8
            pyxel.text(text_x, text_y, label, self.text_color)

    def get_city_at_screen_pos(
        self,
        state: MapState,
        screen_x: int,
        screen_y: int,
    ) -> Optional[City]:
        """Find a city at the given screen position.

        Args:
            state: Map state containing cities.
            screen_x: Screen X position.
            screen_y: Screen Y position.

        Returns:
            City at position, or None if no city found.
        """
        for city in state.cities:
            cx, cy = self.camera.world_to_screen(city.x, city.y)
            radius = max(2, int(self.city_radius * self.camera.zoom))

            # Check if point is within city circle
            dx = screen_x - cx
            dy = screen_y - cy
            if dx * dx + dy * dy <= radius * radius:
                return city

        return None

    def get_map_bounds(self, state: MapState) -> tuple[float, float, float, float]:
        """Get the bounding box of all cities.

        Args:
            state: Map state containing cities.

        Returns:
            Tuple of (min_x, min_y, max_x, max_y).
        """
        if not state.cities:
            return (-100, -100, 100, 100)

        min_x = min(c.x for c in state.cities)
        max_x = max(c.x for c in state.cities)
        min_y = min(c.y for c in state.cities)
        max_y = max(c.y for c in state.cities)

        return (min_x, min_y, max_x, max_y)
