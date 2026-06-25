"""Metrics computation for APR experiments."""

from __future__ import annotations

from typing import Any


class Metrics:
    """Aggregate metrics from a list of repair-evaluation results."""

    def __init__(self, results: list[dict[str, Any]]) -> None:
        self._results = results

    def compute(self) -> dict[str, Any]:
        total = len(self._results)
        if total == 0:
            return {"total": 0}

        generated = sum(1 for r in self._results if r.get("patch_generated"))
        plausible = sum(
            1
            for r in self._results
            if r.get("evaluation") and r["evaluation"].get("passed")
        )
        total_attempts = sum(r.get("attempts", 0) for r in self._results)

        return {
            "total": total,
            "patch_generated": generated,
            "patch_generated_rate": generated / total,
            "plausible": plausible,
            "plausible_rate": plausible / total,
            "average_attempts": total_attempts / total,
            "by_bug": [
                {
                    "bug_id": r["bug_id"],
                    "status": r["status"],
                    "patch_generated": r.get("patch_generated", False),
                    "passed": r.get("evaluation", {}).get("passed", False)
                    if r.get("evaluation")
                    else False,
                }
                for r in self._results
            ],
        }

    @staticmethod
    def format_table(metrics: dict[str, Any]) -> str:
        """Render metrics as a simple text table."""
        lines = [
            "Metric                Value",
            "------------------------------",
            f"Total bugs            {metrics['total']}",
            f"Patch generated       {metrics['patch_generated']} ({metrics.get('patch_generated_rate', 0):.2%})",
            f"Plausible patches     {metrics['plausible']} ({metrics.get('plausible_rate', 0):.2%})",
            f"Average attempts      {metrics.get('average_attempts', 0):.2f}",
        ]
        return "\n".join(lines)
