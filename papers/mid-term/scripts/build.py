#!/usr/bin/env python3
"""Python wrapper around the Makefile-based paper build.

Usage:
    python scripts/build.py all
    python scripts/build.py ieee
    python scripts/build.py acm
    python scripts/build.py acl
    python scripts/build.py figures
    python scripts/build.py clean
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = ["all", "ieee", "acm", "acl", "figures", "clean"]


def run_make(target: str) -> int:
    """Invoke make for the requested target."""
    cmd = ["make", "-C", str(ROOT), target]
    print("$", " ".join(cmd))
    return subprocess.call(cmd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build MACR mid-term paper PDFs")
    parser.add_argument(
        "target",
        choices=TARGETS,
        default="all",
        nargs="?",
        help="Build target (default: all)",
    )
    args = parser.parse_args(argv)
    return run_make(args.target)


if __name__ == "__main__":
    sys.exit(main())
