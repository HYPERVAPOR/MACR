#!/usr/bin/env python3
"""Generate all figures for the MACR mid-term paper.

Usage:
    python figures/generate_all.py
    python -m figures.generate_all
"""

import importlib
import os
import sys

# Ensure the paper root is on PYTHONPATH so 'figures' imports resolve
# regardless of how this script is invoked.
_PAPER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PAPER_ROOT not in sys.path:
    sys.path.insert(0, _PAPER_ROOT)

FIGURE_SCRIPTS = [
    "figures.figure_architecture",
    "figures.figure_ablation",
    "figures.figure_tikz_example",
    "figures.tikz_network",
    "figures.report_results",
    "figures.report_tokens",
    "figures.report_failure_heatmap",
    "figures.report_timeline",
]


def main() -> int:
    """Run all figure generation scripts."""
    for module_name in FIGURE_SCRIPTS:
        print(f"Running {module_name}...")
        module = importlib.import_module(module_name)
        if hasattr(module, "main"):
            module.main()
    print("All figures generated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
