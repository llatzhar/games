"""Main entry point for the map generation viewer.

Run this script to launch the Pyxel-based map viewer:
    python -m src.main
or:
    python src/main.py
"""

from pathlib import Path
from typing import Any, Dict, Optional
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml

from src.viewer.app import App


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. Defaults to config/map_generation.yaml.

    Returns:
        Configuration dictionary.
    """
    if config_path is None:
        # Default config path relative to project root
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config" / "map_generation.yaml"

    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    # Return defaults if no config file
    return {}


def main() -> None:
    """Main entry point."""
    # Load configuration
    config = load_config()

    # Create and run the application
    app = App(config)
    app.run()


if __name__ == "__main__":
    main()
