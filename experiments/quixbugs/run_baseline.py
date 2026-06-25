"""Run the single-Agent baseline on QuixBugs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow importing from experiments/ when running the script directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.quixbugs.common import (
    create_backend,
    load_dataset,
    print_metrics,
    run_configuration,
    save_results,
    setup_logging,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run single-Agent baseline on QuixBugs")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of bugs to repair")
    parser.add_argument("--language", type=str, default="python", help="Language subset")
    parser.add_argument("--max-steps", type=int, default=5, help="Max ReAct steps per bug")
    parser.add_argument("--workers", type=int, default=1, help="Concurrent bugs per config")
    args = parser.parse_args()

    setup_logging()
    backend = create_backend()
    dataset = load_dataset(language=args.language)

    data = run_configuration(
        "Baseline",
        dataset,
        backend,
        use_kg=False,
        use_sub_agents=False,
        limit=args.limit,
        max_steps=args.max_steps,
        workers=args.workers,
    )

    save_results("Baseline", data)
    print_metrics(data["metrics"])


if __name__ == "__main__":
    main()
