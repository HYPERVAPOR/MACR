"""Shared helpers for QuixBugs experiments."""

from __future__ import annotations

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from macr.datasets.base import BugDataset, BugSample
from macr.datasets.quixbugs import QuixBugsDataset
from macr.evaluation.metrics import Metrics
from macr.llm.base import LLMBackend
from macr.llm.openai_backend import OpenAIBackend
from macr.repair.pipeline import RepairPipeline

load_dotenv()

logger = logging.getLogger(__name__)


def setup_logging(level: str | None = None) -> None:
    level = level or os.getenv("MACR_LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def create_backend() -> LLMBackend:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Please copy .env.example to .env and fill in your key."
        )
    return OpenAIBackend(
        api_key=api_key,
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )


def load_dataset(language: str = "python") -> QuixBugsDataset:
    dataset = QuixBugsDataset(language=language)
    dataset.load()
    logger.info("Loaded %d %s samples from QuixBugs", len(dataset), language)
    return dataset


def _repair_one(
    pipeline: RepairPipeline,
    dataset: BugDataset | None,
    sample: BugSample,
) -> dict[str, Any]:
    """Repair and optionally evaluate a single sample."""
    logger.info("Repairing %s", sample.bug_id)
    result = pipeline.run(sample)

    if result.get("patch") and dataset is not None:
        patched_code = result["patch"].get("patched_code", "")
        try:
            passed = dataset.evaluate_patch(sample, patched_code)
        except Exception as exc:
            logger.warning("Evaluation failed for %s: %s", sample.bug_id, exc)
            passed = False
        result["evaluation"] = {"bug_id": sample.bug_id, "passed": passed}

    return result


def run_configuration(
    name: str,
    dataset: BugDataset,
    backend: LLMBackend,
    *,
    use_kg: bool,
    use_sub_agents: bool,
    limit: int | None = None,
    max_steps: int = 5,
    workers: int = 1,
) -> dict[str, Any]:
    """Run a single experimental configuration.

    Args:
        name: Configuration display name.
        dataset: Dataset to repair.
        backend: LLM backend.
        use_kg: Enable the knowledge-graph query tool.
        use_sub_agents: Enable the sub-agent tools (localize/generate/validate).
        limit: If set, repair only the first N samples.
        max_steps: Maximum ReAct steps per bug.
        workers: Number of concurrent bugs to repair. Default 1 (sequential).
            Values > 1 use a thread pool; be mindful of API rate limits.
    """
    logger.info("Running configuration: %s", name)

    pipeline = RepairPipeline(
        backend,
        dataset=dataset,
        use_knowledge_graph=use_kg,
        use_sub_agents=use_sub_agents,
        max_steps=max_steps,
        configuration=name,
    )

    samples = list(dataset)[:limit] if limit else list(dataset)
    results: list[dict[str, Any]]

    if workers <= 1:
        results = [_repair_one(pipeline, dataset, sample) for sample in samples]
    else:
        logger.info("Using %d workers to repair %d bugs", workers, len(samples))
        indexed_results: list[tuple[int, dict[str, Any]]] = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_repair_one, pipeline, dataset, sample): idx
                for idx, sample in enumerate(samples)
            }
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    indexed_results.append((idx, future.result()))
                except Exception as exc:
                    logger.exception("Repair failed for sample %s: %s", samples[idx].bug_id, exc)
                    indexed_results.append(
                        (
                            idx,
                            {
                                "bug_id": samples[idx].bug_id,
                                "status": "failure",
                                "patch_generated": False,
                                "patch": None,
                                "attempts": 0,
                                "steps": [],
                                "evaluation": {"bug_id": samples[idx].bug_id, "passed": False},
                                "error_message": str(exc),
                            },
                        )
                    )
        indexed_results.sort(key=lambda item: item[0])
        results = [r for _, r in indexed_results]

    metrics = Metrics(results).compute()
    metrics["configuration"] = name
    metrics["use_kg"] = use_kg
    metrics["use_sub_agents"] = use_sub_agents

    return {"results": results, "metrics": metrics}


def save_results(name: str, data: dict[str, Any], output_dir: Path | str = "outputs/quixbugs") -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_name = name.replace(" ", "_").lower()
    result_path = output_dir / f"{safe_name}_results.json"
    metrics_path = output_dir / f"{safe_name}_metrics.json"

    result_path.write_text(json.dumps(data["results"], indent=2, ensure_ascii=False), encoding="utf-8")
    metrics_path.write_text(json.dumps(data["metrics"], indent=2, ensure_ascii=False), encoding="utf-8")

    logger.info("Saved results to %s", result_path)
    logger.info("Saved metrics to %s", metrics_path)
    return result_path


def print_metrics(metrics: dict[str, Any]) -> None:
    print("\n" + Metrics.format_table(metrics))
