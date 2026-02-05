"""Camera system for the map viewer.

Handles panning, zooming, and coordinate transformations between
world space and screen space.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict, Any


@dataclass
class Camera:
    """Camera for 2D map viewing with pan and zoom.

    Attributes:
        offset_x: Horizontal offset (pan) in world units.
        offset_y: Vertical offset (pan) in world units.
        zoom: Zoom level (1.0 = 100%, 2.0 = 200%, etc.).
        screen_width: Width of the viewport in pixels.
        screen_height: Height of the viewport in pixels.
    """

    offset_x: float = 0.0
    offset_y: float = 0.0
    zoom: float = 1.0
    screen_width: int = 480
    screen_height: int = 360

    # Zoom constraints
    zoom_min: float = 0.25
    zoom_max: float = 4.0
    zoom_step: float = 0.1

    # Drag state
    _dragging: bool = field(default=False, repr=False)
    _drag_start_x: float = field(default=0.0, repr=False)
    _drag_start_y: float = field(default=0.0, repr=False)
    _offset_at_drag_start_x: float = field(default=0.0, repr=False)
    _offset_at_drag_start_y: float = field(default=0.0, repr=False)

    @classmethod
    def from_config(cls, config: Optional[Dict[str, Any]] = None) -> Camera:
        """Create a camera from configuration dictionary.

        Args:
            config: Configuration dictionary with viewer settings.

        Returns:
            Configured Camera instance.
        """
        if config is None:
            return cls()

        viewer_config = config.get("viewer", {})
        return cls(
            screen_width=viewer_config.get("width", 480),
            screen_height=viewer_config.get("height", 360),
            zoom=viewer_config.get("initial_zoom", 1.0),
            zoom_min=viewer_config.get("zoom_min", 0.25),
            zoom_max=viewer_config.get("zoom_max", 4.0),
            zoom_step=viewer_config.get("zoom_step", 0.1),
        )

    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates.

        Args:
            world_x: X position in world space.
            world_y: Y position in world space.

        Returns:
            Tuple of (screen_x, screen_y) as integers.
        """
        # Apply offset (camera position)
        x = world_x - self.offset_x
        y = world_y - self.offset_y

        # Apply zoom (scale around center)
        x *= self.zoom
        y *= self.zoom

        # Translate to screen center
        screen_x = int(x + self.screen_width / 2)
        screen_y = int(-y + self.screen_height / 2)  # Flip Y axis

        return (screen_x, screen_y)

    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates.

        Args:
            screen_x: X position on screen (pixels).
            screen_y: Y position on screen (pixels).

        Returns:
            Tuple of (world_x, world_y) as floats.
        """
        # Translate from screen center
        x = screen_x - self.screen_width / 2
        y = -(screen_y - self.screen_height / 2)  # Flip Y axis

        # Remove zoom
        x /= self.zoom
        y /= self.zoom

        # Remove offset
        world_x = x + self.offset_x
        world_y = y + self.offset_y

        return (world_x, world_y)

    def apply_zoom(self, delta: int, mouse_x: int, mouse_y: int) -> None:
        """Apply zoom centered on the mouse position.

        Args:
            delta: Positive for zoom in, negative for zoom out.
            mouse_x: Mouse X position on screen.
            mouse_y: Mouse Y position on screen.
        """
        # Get world position under mouse before zoom
        world_x, world_y = self.screen_to_world(mouse_x, mouse_y)

        # Apply zoom
        old_zoom = self.zoom
        self.zoom += delta * self.zoom_step
        self.zoom = max(self.zoom_min, min(self.zoom_max, self.zoom))

        if self.zoom == old_zoom:
            return

        # Adjust offset to keep world position under mouse
        # After zoom, the screen position of the world point changes
        # We need to adjust offset to compensate
        new_screen_x, new_screen_y = self.world_to_screen(world_x, world_y)

        # Calculate the screen offset that occurred
        dx = new_screen_x - mouse_x
        dy = new_screen_y - mouse_y

        # Convert screen offset back to world offset
        self.offset_x += dx / self.zoom
        self.offset_y -= dy / self.zoom  # Flip Y

    def start_drag(self, mouse_x: float, mouse_y: float) -> None:
        """Start a drag operation.

        Args:
            mouse_x: Starting mouse X position.
            mouse_y: Starting mouse Y position.
        """
        self._dragging = True
        self._drag_start_x = mouse_x
        self._drag_start_y = mouse_y
        self._offset_at_drag_start_x = self.offset_x
        self._offset_at_drag_start_y = self.offset_y

    def update_drag(self, mouse_x: float, mouse_y: float) -> None:
        """Update the camera position during a drag.

        Args:
            mouse_x: Current mouse X position.
            mouse_y: Current mouse Y position.
        """
        if not self._dragging:
            return

        # Calculate mouse delta in screen space
        dx = mouse_x - self._drag_start_x
        dy = mouse_y - self._drag_start_y

        # Convert to world space offset (flip Y)
        self.offset_x = self._offset_at_drag_start_x - dx / self.zoom
        self.offset_y = self._offset_at_drag_start_y + dy / self.zoom

    def end_drag(self) -> None:
        """End the current drag operation."""
        self._dragging = False

    @property
    def is_dragging(self) -> bool:
        """Check if currently dragging."""
        return self._dragging

    def reset(self) -> None:
        """Reset camera to default position and zoom."""
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.zoom = 1.0

    def fit_to_bounds(
        self,
        min_x: float,
        min_y: float,
        max_x: float,
        max_y: float,
        padding: float = 50.0,
    ) -> None:
        """Adjust camera to fit given world bounds in view.

        Args:
            min_x: Minimum X coordinate.
            min_y: Minimum Y coordinate.
            max_x: Maximum X coordinate.
            max_y: Maximum Y coordinate.
            padding: Padding in pixels around the content.
        """
        # Calculate center of bounds
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        # Calculate required zoom to fit bounds
        width = max_x - min_x
        height = max_y - min_y

        if width > 0 and height > 0:
            zoom_x = (self.screen_width - 2 * padding) / width
            zoom_y = (self.screen_height - 2 * padding) / height
            self.zoom = max(self.zoom_min, min(self.zoom_max, min(zoom_x, zoom_y)))

        # Center on bounds
        self.offset_x = center_x
        self.offset_y = center_y
