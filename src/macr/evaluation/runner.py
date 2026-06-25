"""Test execution and patch validation."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import tempfile
from typing import Any

from macr.agents.protocol import PatchCandidate
from macr.repair.patch import apply_patch

logger = logging.getLogger(__name__)


class EvaluationResult:
    """Result of evaluating a patched program."""

    def __init__(
        self,
        bug_id: str,
        passed: bool,
        stdout: str = "",
        stderr: str = "",
        runtime: float | None = None,
        error_message: str | None = None,
    ) -> None:
        self.bug_id = bug_id
        self.passed = passed
        self.stdout = stdout
        self.stderr = stderr
        self.runtime = runtime
        self.error_message = error_message

    def to_dict(self) -> dict[str, Any]:
        return {
            "bug_id": self.bug_id,
            "passed": self.passed,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "runtime": self.runtime,
            "error_message": self.error_message,
        }


class EvaluationRunner:
    """Run tests against patched code."""

    def __init__(self, timeout: int = 30) -> None:
        self._timeout = timeout

    def evaluate(
        self,
        bug_id: str,
        buggy_code: str,
        patch: PatchCandidate,
        expected_output: str | None,
        language: str = "python",
    ) -> EvaluationResult:
        """Evaluate a patch by running the patched code and comparing output."""
        if language != "python":
            return EvaluationResult(
                bug_id=bug_id,
                passed=False,
                error_message=f"Language {language} not yet supported",
            )

        patched_code = apply_patch(buggy_code, patch)

        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(patched_code)
            tmp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
            stdout = result.stdout
            stderr = result.stderr

            if result.returncode != 0:
                return EvaluationResult(
                    bug_id=bug_id,
                    passed=False,
                    stdout=stdout,
                    stderr=stderr,
                    error_message=f"Runtime error (exit code {result.returncode})",
                )

            if expected_output is not None:
                passed = stdout.strip() == expected_output.strip()
            else:
                passed = True

            return EvaluationResult(
                bug_id=bug_id,
                passed=passed,
                stdout=stdout,
                stderr=stderr,
            )

        except subprocess.TimeoutExpired:
            return EvaluationResult(
                bug_id=bug_id,
                passed=False,
                error_message=f"Execution timed out after {self._timeout}s",
            )
        except Exception as exc:
            logger.exception("Evaluation failed for %s", bug_id)
            return EvaluationResult(
                bug_id=bug_id,
                passed=False,
                error_message=str(exc),
            )
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
