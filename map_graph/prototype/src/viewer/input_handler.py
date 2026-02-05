"""Input handler for the map viewer.

Processes mouse and keyboard input for camera control and UI interaction.
"""

from __future__ import annotations
from typing import Optional, Callable
import pyxel

from .camera import Camera


class InputHandler:
    """Handles input for the map viewer.

    Processes mouse wheel for zoom, mouse drag for pan,
    and mouse clicks for UI buttons.
    """

    def __init__(self, camera: Camera) -> None:
        """Initialize the input handler.

        Args:
            camera: The camera to control.
        """
        self.camera = camera
        self._prev_mouse_x: int = 0
        self._prev_mouse_y: int = 0
        self._mouse_wheel_delta: int = 0

    def update(self) -> None:
        """Update input state each frame.

        Should be called at the start of each update cycle.
        """
        # Handle zoom (mouse wheel)
        wheel = pyxel.mouse_wheel
        if wheel != 0:
            self.camera.apply_zoom(wheel, pyxel.mouse_x, pyxel.mouse_y)

        # Handle pan (right mouse button drag or middle mouse button)
        if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT) or pyxel.btnp(pyxel.MOUSE_BUTTON_MIDDLE):
            self.camera.start_drag(pyxel.mouse_x, pyxel.mouse_y)

        if pyxel.btn(pyxel.MOUSE_BUTTON_RIGHT) or pyxel.btn(pyxel.MOUSE_BUTTON_MIDDLE):
            self.camera.update_drag(pyxel.mouse_x, pyxel.mouse_y)

        if pyxel.btnr(pyxel.MOUSE_BUTTON_RIGHT) or pyxel.btnr(pyxel.MOUSE_BUTTON_MIDDLE):
            self.camera.end_drag()

        # Store current mouse position for next frame
        self._prev_mouse_x = pyxel.mouse_x
        self._prev_mouse_y = pyxel.mouse_y

    def is_left_click(self) -> bool:
        """Check if left mouse button was just pressed."""
        return pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)

    def is_left_held(self) -> bool:
        """Check if left mouse button is held."""
        return pyxel.btn(pyxel.MOUSE_BUTTON_LEFT)

    def is_left_released(self) -> bool:
        """Check if left mouse button was just released."""
        return pyxel.btnr(pyxel.MOUSE_BUTTON_LEFT)

    @property
    def mouse_x(self) -> int:
        """Get current mouse X position."""
        return pyxel.mouse_x

    @property
    def mouse_y(self) -> int:
        """Get current mouse Y position."""
        return pyxel.mouse_y

    def is_key_pressed(self, key: int) -> bool:
        """Check if a key was just pressed.

        Args:
            key: Pyxel key constant.

        Returns:
            True if key was just pressed.
        """
        return pyxel.btnp(key)

    def is_key_held(self, key: int) -> bool:
        """Check if a key is held.

        Args:
            key: Pyxel key constant.

        Returns:
            True if key is held.
        """
        return pyxel.btn(key)
