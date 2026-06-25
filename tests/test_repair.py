"""Tests for patch application and evaluation."""

from __future__ import annotations

from macr.agents.protocol import PatchCandidate
from macr.evaluation.runner import EvaluationRunner
from macr.repair.patch import apply_patch

BUGGY = """\
def add(a, b):
    return a - b

if __name__ == "__main__":
    print(add(1, 2))
"""

PATCHED_FUNCTION = """\
def add(a, b):
    return a + b
"""

PATCHED_FULL = """\
def add(a, b):
    return a + b

if __name__ == "__main__":
    print(add(1, 2))
"""


def test_apply_function_level_patch() -> None:
    patch = PatchCandidate(buggy_code=BUGGY, patched_code=PATCHED_FUNCTION)
    result = apply_patch(BUGGY, patch)
    assert "return a + b" in result
    assert "if __name__" in result


def test_apply_full_file_patch() -> None:
    patch = PatchCandidate(buggy_code=BUGGY, patched_code=PATCHED_FULL)
    result = apply_patch(BUGGY, patch)
    assert "return a + b" in result


def test_evaluation_runner_passes() -> None:
    runner = EvaluationRunner(timeout=10)
    patch = PatchCandidate(buggy_code=BUGGY, patched_code=PATCHED_FUNCTION)
    result = runner.evaluate(
        bug_id="add",
        buggy_code=BUGGY,
        patch=patch,
        expected_output="3\n",
        language="python",
    )
    assert result.passed
    assert result.stdout.strip() == "3"


def test_evaluation_runner_fails() -> None:
    runner = EvaluationRunner(timeout=10)
    patch = PatchCandidate(buggy_code=BUGGY, patched_code=PATCHED_FUNCTION)
    result = runner.evaluate(
        bug_id="add",
        buggy_code=BUGGY,
        patch=patch,
        expected_output="99\n",
        language="python",
    )
    assert not result.passed
