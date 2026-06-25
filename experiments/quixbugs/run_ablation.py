"""Run ablation experiments on QuixBugs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow importing from experiments/ when running the script directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.quixbugs.common import (
    create_backend,
    load_dataset,
    run_configuration,
    save_results,
    setup_logging,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MACR ablation study on QuixBugs")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of bugs per config")
    parser.add_argument("--language", type=str, default="python", help="Language subset")
    parser.add_argument("--max-steps", type=int, default=5, help="Max ReAct steps per bug")
    parser.add_argument("--workers", type=int, default=1, help="Concurrent bugs per config")
    args = parser.parse_args()

    setup_logging()
    backend = create_backend()
    dataset = load_dataset(language=args.language)

    configurations = [
        ("Baseline", False, False),
        ("MACR", False, False),  # ReAct loop without sub-agents or KG
        ("MACR + Sub-Agent", False, True),
        ("MACR + KG", True, False),
        ("MACR + Sub-Agent + KG", True, True),
    ]

    summary: list[dict] = []
    for name, use_kg, use_sub in configurations:
        data = run_configuration(
            name,
            dataset,
            backend,
            use_kg=use_kg,
            use_sub_agents=use_sub,
            limit=args.limit,
            max_steps=args.max_steps,
            workers=args.workers,
        )
        save_results(name, data)
        summary.append(data["metrics"])

    output_dir = Path("outputs/quixbugs")
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "ablation_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\nAblation Summary")
    print("-" * 70)
    print(f"{'Configuration':<30} {'Plausible':>12} {'Generated':>12} {'Avg Steps':>12}")
    print("-" * 70)
    for metrics in summary:
        print(
            f"{metrics['configuration']:<30} "
            f"{metrics['plausible']:>5}/{metrics['total']:<6} "
            f"{metrics['patch_generated']:>5}/{metrics['total']:<6} "
            f"{metrics['average_attempts']:>12.2f}"
        )


if __name__ == "__main__":
    main()
