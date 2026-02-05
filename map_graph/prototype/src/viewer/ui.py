"""UI components for the map viewer.

Provides buttons and other UI elements.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, List, Optional, Dict, Any
import pyxel


@dataclass
class Button:
    """A clickable button in the UI.

    Attributes:
        x: X position on screen.
        y: Y position on screen.
        width: Button width in pixels.
        height: Button height in pixels.
        label: Text label to display.
        on_click: Callback function when clicked.
        enabled: Whether the button is enabled.
    """

    x: int
    y: int
    width: int
    height: int
    label: str
    on_click: Optional[Callable[[], None]] = None
    enabled: bool = True

    # Colors (Pyxel palette indices)
    bg_color: int = 1       # Dark blue
    hover_color: int = 2    # Purple
    text_color: int = 7     # White
    disabled_color: int = 5  # Gray

    def contains(self, mouse_x: int, mouse_y: int) -> bool:
        """Check if a point is inside the button.

        Args:
            mouse_x: X position to check.
            mouse_y: Y position to check.

        Returns:
            True if point is inside button bounds.
        """
        return (
            self.x <= mouse_x < self.x + self.width
            and self.y <= mouse_y < self.y + self.height
        )

    def draw(self, mouse_x: int, mouse_y: int) -> None:
        """Draw the button.

        Args:
            mouse_x: Current mouse X for hover detection.
            mouse_y: Current mouse Y for hover detection.
        """
        # Determine background color
        if not self.enabled:
            bg = self.disabled_color
        elif self.contains(mouse_x, mouse_y):
            bg = self.hover_color
        else:
            bg = self.bg_color

        # Draw background
        pyxel.rect(self.x, self.y, self.width, self.height, bg)

        # Draw border
        pyxel.rectb(self.x, self.y, self.width, self.height, self.text_color)

        # Draw label (centered)
        text_width = len(self.label) * 4  # Approximate width
        text_x = self.x + (self.width - text_width) // 2
        text_y = self.y + (self.height - 5) // 2
        pyxel.text(text_x, text_y, self.label, self.text_color)

    def handle_click(self, mouse_x: int, mouse_y: int) -> bool:
        """Handle a click event.

        Args:
            mouse_x: Mouse X at click.
            mouse_y: Mouse Y at click.

        Returns:
            True if the button was clicked.
        """
        if self.enabled and self.contains(mouse_x, mouse_y):
            if self.on_click:
                self.on_click()
            return True
        return False


class UIManager:
    """Manages UI elements for the viewer.

    Handles button layout, drawing, and click detection.
    """

    def __init__(self, screen_width: int, screen_height: int) -> None:
        """Initialize the UI manager.

        Args:
            screen_width: Width of the screen.
            screen_height: Height of the screen.
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.buttons: List[Button] = []

        # Status text
        self._status_text: str = ""
        self._generation_text: str = "Gen: 0/0"

    def add_button(self, button: Button) -> None:
        """Add a button to the UI.

        Args:
            button: Button to add.
        """
        self.buttons.append(button)

    def clear_buttons(self) -> None:
        """Remove all buttons."""
        self.buttons.clear()

    def create_default_buttons(
        self,
        on_prev: Callable[[], None],
        on_next: Callable[[], None],
        on_add_city: Callable[[], None],
        on_reset: Callable[[], None],
        on_fit: Callable[[], None],
    ) -> None:
        """Create the default set of navigation buttons.

        Args:
            on_prev: Callback for previous generation.
            on_next: Callback for next generation.
            on_add_city: Callback for adding a city.
            on_reset: Callback for resetting the map.
            on_fit: Callback for fitting view to map.
        """
        button_height = 16
        button_y = self.screen_height - button_height - 4
        margin = 4
        button_width = 40

        # Previous button
        self.add_button(Button(
            x=margin,
            y=button_y,
            width=button_width,
            height=button_height,
            label="< Prev",
            on_click=on_prev,
        ))

        # Next button
        self.add_button(Button(
            x=margin + button_width + margin,
            y=button_y,
            width=button_width,
            height=button_height,
            label="Next >",
            on_click=on_next,
        ))

        # Add City button
        self.add_button(Button(
            x=margin + (button_width + margin) * 2,
            y=button_y,
            width=button_width + 10,
            height=button_height,
            label="Add City",
            on_click=on_add_city,
        ))

        # Reset button
        self.add_button(Button(
            x=margin + (button_width + margin) * 2 + button_width + 10 + margin,
            y=button_y,
            width=button_width,
            height=button_height,
            label="Reset",
            on_click=on_reset,
        ))

        # Fit View button
        self.add_button(Button(
            x=self.screen_width - button_width - margin,
            y=button_y,
            width=button_width,
            height=button_height,
            label="Fit",
            on_click=on_fit,
        ))

    def set_button_enabled(self, label: str, enabled: bool) -> None:
        """Enable or disable a button by label.

        Args:
            label: Button label to find.
            enabled: Whether to enable the button.
        """
        for button in self.buttons:
            if button.label == label:
                button.enabled = enabled
                break

    def set_generation_text(self, current: int, total: int) -> None:
        """Set the generation counter text.

        Args:
            current: Current generation index (1-based for display).
            total: Total number of generations.
        """
        self._generation_text = f"Gen: {current}/{total}"

    def set_status_text(self, text: str) -> None:
        """Set status text to display.

        Args:
            text: Status message.
        """
        self._status_text = text

    def handle_click(self, mouse_x: int, mouse_y: int) -> bool:
        """Handle a click event.

        Args:
            mouse_x: Mouse X at click.
            mouse_y: Mouse Y at click.

        Returns:
            True if any button was clicked.
        """
        for button in self.buttons:
            if button.handle_click(mouse_x, mouse_y):
                return True
        return False

    def draw(self, mouse_x: int, mouse_y: int) -> None:
        """Draw all UI elements.

        Args:
            mouse_x: Current mouse X for hover effects.
            mouse_y: Current mouse Y for hover effects.
        """
        # Draw buttons
        for button in self.buttons:
            button.draw(mouse_x, mouse_y)

        # Draw generation counter (top-left)
        pyxel.text(4, 4, self._generation_text, 7)

        # Draw status text (top-right)
        if self._status_text:
            text_width = len(self._status_text) * 4
            pyxel.text(self.screen_width - text_width - 4, 4, self._status_text, 7)

        # Draw help text
        help_text = "Wheel:Zoom  RightDrag:Pan"
        pyxel.text(4, 14, help_text, 5)
