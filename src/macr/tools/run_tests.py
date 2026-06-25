"""Run tests tool for the ReAct agent."""

from __future__ import annotations

from typing import Any

from macr.datasets.base import BugDataset, BugSample
from macr.tools.base import Observation, Tool


class RunTestsTool(Tool):
    """Run the test suite against a patched version of the code."""

    def __init__(self, dataset: BugDataset, sample: BugSample) -> None:
        self._dataset = dataset
        self._sample = sample

    @property
    def name(self) -> str:
        return "run_tests"

    @property
    def description(self) -> str:
        return (
            "Run the official test suite for this bug against a proposed patch. "
            "Returns whether the patch passes all tests and any failure output. "
            "Use this to observe the environment and decide next steps."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "patched_code": "str: the proposed fixed source code",
        }

    def run(self, inputs: dict[str, Any]) -> Observation:
        patched_code = inputs.get("patched_code", "")
        if not patched_code:
            return Observation(
                success=False,
                error_message="No patched_code provided.",
            )

        try:
            if hasattr(self._dataset, "evaluate_patch_with_output"):
                passed, output = self._dataset.evaluate_patch_with_output(
                    self._sample, patched_code
                )
            else:
                passed = self._dataset.evaluate_patch(self._sample, patched_code)
                output = "All tests passed." if passed else "Some tests failed."

            return Observation(
                success=passed,
                output=output[:2000] if output else ("All tests passed." if passed else "Some tests failed."),
                terminal=passed,
            )
        except Exception as exc:  # pragma: no cover
            return Observation(
                success=False,
                output=str(exc),
                error_message=f"Test execution failed: {exc}",
            )
