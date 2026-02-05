"""Main Pyxel application for the map viewer.

Integrates all viewer components and provides the main game loop.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
import random
import pyxel

from ..models import MapState, MapHistory
from ..generation import CityPlacer, RoadGenerator
from .camera import Camera
from .renderer import Renderer
from .input_handler import InputHandler
from .ui import UIManager


class App:
    """Main application for the map viewer.

    Provides the Pyxel game loop with map generation visualization,
    camera controls, and generation history navigation.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the application.

        Args:
            config: Configuration dictionary.
        """
        self.config = config or {}
        viewer_config = self.config.get("viewer", {})

        self.screen_width: int = viewer_config.get("width", 480)
        self.screen_height: int = viewer_config.get("height", 360)

        # Initialize RNG
        seed = self.config.get("rng_seed")
        if seed is not None:
            self.rng = random.Random(seed)
        else:
            self.rng = random.Random()

        # Initialize components
        self.camera = Camera.from_config(self.config)
        self.renderer = Renderer(self.camera, self.config)
        self.input_handler = InputHandler(self.camera)
        self.ui = UIManager(self.screen_width, self.screen_height)

        # Initialize generators
        self.city_placer = CityPlacer(self.config)
        self.road_generator = RoadGenerator(self.config)

        # Initialize map state and history
        self.map_state = MapState()
        self.history = MapHistory()

        # Flag to track if we're viewing history or current state
        self._viewing_history = False

        # Create initial map
        self._create_initial_map()

        # Setup UI buttons
        self.ui.create_default_buttons(
            on_prev=self._on_prev_generation,
            on_next=self._on_next_generation,
            on_add_city=self._on_add_city,
            on_reset=self._on_reset,
            on_fit=self._on_fit_view,
        )
        self._update_ui_state()

    def _create_initial_map(self) -> None:
        """Create the initial map with 3 cities."""
        self.map_state = MapState()

        # Create initial triangle
        self.city_placer.create_initial_triangle(self.map_state)
        self.road_generator.create_initial_roads(self.map_state)

        # Save initial state to history
        self.history.clear()
        self.history.save_snapshot(self.map_state)

        # Fit view to initial map
        self._on_fit_view()

    def _on_prev_generation(self) -> None:
        """Go to previous generation in history."""
        prev_state = self.history.prev()
        if prev_state:
            self.map_state = prev_state
            self._viewing_history = True
            self._update_ui_state()

    def _on_next_generation(self) -> None:
        """Go to next generation in history."""
        next_state = self.history.next()
        if next_state:
            self.map_state = next_state
            self._viewing_history = self.history.current_index < self.history.total_snapshots - 1
            self._update_ui_state()

    def _on_add_city(self) -> None:
        """Add a new city to the map."""
        # If viewing history, go to latest first
        if self._viewing_history:
            latest = self.history.go_to(self.history.total_snapshots - 1)
            if latest:
                self.map_state = latest
            self._viewing_history = False

        # Alternate between player and enemy nations
        # Simple logic: add enemy cities more often as game progresses
        if len(self.map_state.cities) % 3 == 0:
            nation_id = 1  # Enemy
        else:
            nation_id = 0  # Player

        # Add new city
        new_city = self.city_placer.add_city(
            self.map_state,
            nation_id=nation_id,
            rng=self.rng,
        )

        if new_city:
            # Generate roads for the new city
            self.road_generator.generate_roads_for_city(new_city, self.map_state)

            # Save to history
            self.history.save_snapshot(self.map_state)

        self._update_ui_state()

    def _on_reset(self) -> None:
        """Reset to initial map state."""
        self._create_initial_map()
        self._viewing_history = False
        self._update_ui_state()

    def _on_fit_view(self) -> None:
        """Fit the camera to show all cities."""
        bounds = self.renderer.get_map_bounds(self.map_state)
        self.camera.fit_to_bounds(*bounds)

    def _update_ui_state(self) -> None:
        """Update UI elements based on current state."""
        # Update generation counter
        self.ui.set_generation_text(
            self.history.current_index + 1,
            self.history.total_snapshots,
        )

        # Update button states
        self.ui.set_button_enabled("< Prev", self.history.can_go_prev())
        self.ui.set_button_enabled("Next >", self.history.can_go_next())

        # Update status
        city_count = len(self.map_state.cities)
        road_count = len(self.map_state.roads)
        self.ui.set_status_text(f"Cities:{city_count} Roads:{road_count}")

    def run(self) -> None:
        """Start the Pyxel application."""
        pyxel.init(
            self.screen_width,
            self.screen_height,
            title="Map Generation Viewer",
        )
        pyxel.mouse(True)
        pyxel.run(self.update, self.draw)

    def update(self) -> None:
        """Update game state each frame."""
        # Handle input
        self.input_handler.update()

        # Handle UI clicks
        if self.input_handler.is_left_click():
            self.ui.handle_click(
                self.input_handler.mouse_x,
                self.input_handler.mouse_y,
            )

        # Keyboard shortcuts
        if self.input_handler.is_key_pressed(pyxel.KEY_R):
            self._on_reset()
        if self.input_handler.is_key_pressed(pyxel.KEY_F):
            self._on_fit_view()
        if self.input_handler.is_key_pressed(pyxel.KEY_SPACE):
            self._on_add_city()
        if self.input_handler.is_key_pressed(pyxel.KEY_LEFT):
            self._on_prev_generation()
        if self.input_handler.is_key_pressed(pyxel.KEY_RIGHT):
            self._on_next_generation()
        if self.input_handler.is_key_pressed(pyxel.KEY_Q):
            pyxel.quit()

    def draw(self) -> None:
        """Draw the frame."""
        # Clear screen
        self.renderer.clear()

        # Draw map
        self.renderer.draw_map(self.map_state)

        # Draw UI
        self.ui.draw(
            self.input_handler.mouse_x,
            self.input_handler.mouse_y,
        )
