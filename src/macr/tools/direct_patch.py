"""Direct patch generation tool."""

from __future__ import annotations

from typing import Any

from macr.llm.base import LLMBackend
from macr.repair.patch import PatchCandidate, extract_first_code_block
from macr.tools.base import Observation, Tool


class DirectPatchTool(Tool):
    """Generate a patch directly using the LLM."""

    def __init__(self, backend: LLMBackend) -> None:
        self._backend = backend

    @property
    def name(self) -> str:
        return "direct_patch"

    @property
    def description(self) -> str:
        return (
            "Generate a minimal patch for the buggy code directly. "
            "Use this when you want to propose a fix in one shot."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "buggy_code": "str: the original buggy source code",
            "test_code": "str (optional): test cases that the fix must pass",
            "issue_description": "str (optional): natural language bug description",
            "hint": "str (optional): additional hints for generating the patch",
        }

    def run(self, inputs: dict[str, Any]) -> Observation:
        buggy_code = inputs.get("buggy_code", "")
        test_code = inputs.get("test_code", "")
        issue_description = inputs.get("issue_description", "")
        hint = inputs.get("hint", "")

        system = (
            "You are an automated program repair expert. Generate a minimal patch that fixes "
            "the bug while preserving existing behavior. Output ONLY the repaired code block "
            "inside triple backticks, followed by a brief explanation."
        )
        user_parts = [
            f"Buggy code:\n```\n{buggy_code}\n```",
        ]
        if issue_description:
            user_parts.append(f"Issue description:\n{issue_description}")
        if test_code:
            user_parts.append(f"Test code:\n```\n{test_code}\n```")
        if hint:
            user_parts.append(f"Hint:\n{hint}")

        try:
            output = self._backend.chat(
                [{"role": "system", "content": system}, {"role": "user", "content": "\n\n".join(user_parts)}]
            )
            text = output if isinstance(output, str) else str(output)
            patched_code = extract_first_code_block(text)

            if patched_code is None:
                return Observation(
                    success=False,
                    output=text,
                    error_message="No code block could be extracted from the response.",
                )

            patch = PatchCandidate(buggy_code=buggy_code, patched_code=patched_code)
            return Observation(
                success=True,
                output=text,
                structured_output=patch.model_dump(),
            )
        except Exception as exc:  # pragma: no cover
            return Observation(
                success=False,
                error_message=f"Direct patch generation failed: {exc}",
            )
