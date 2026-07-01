"""Figure generation package for the MACR mid-term paper."""

import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def ensure_output_dir() -> None:
    """Create the figure output directory if it does not exist."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
