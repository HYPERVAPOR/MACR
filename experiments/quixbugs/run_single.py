"""Run MACR on a single QuixBugs sample."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.quixbugs.common import create_backend, load_dataset, setup_logging
from macr.repair.pipeline import RepairPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MACR on one QuixBugs sample")
    parser.add_argument("bug_id", help="Bug identifier, e.g. bitcount")
    parser.add_argument("--use-kg", action="store_true", help="Enable knowledge graph")
    parser.add_argument("--use-sub-agents", action="store_true", help="Enable sub-agent tools")
    parser.add_argument("--max-steps", type=int, default=5, help="Max ReAct steps")
    parser.add_argument("--language", type=str, default="python", help="Language subset")
    args = parser.parse_args()

    setup_logging()
    backend = create_backend()
    dataset = load_dataset(language=args.language)

    pipeline = RepairPipeline(
        backend,
        dataset=dataset,
        use_knowledge_graph=args.use_kg,
        use_sub_agents=args.use_sub_agents,
        max_steps=args.max_steps,
    )

    sample = dataset.get(args.bug_id)
    if sample is None:
        available = sorted(s.bug_id for s in dataset)
        print(f"Unknown bug_id '{args.bug_id}'. Available IDs: {available}")
        return

    result = pipeline.run(sample)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result.get("patch"):
        passed = dataset.evaluate_patch(sample, result["patch"]["patched_code"])
        print(f"\nPatch passes tests: {passed}")


if __name__ == "__main__":
    main()
