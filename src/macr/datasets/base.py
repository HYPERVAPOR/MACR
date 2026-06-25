"""Base interface for bug datasets."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any


@dataclass
class BugSample:
    """A single buggy program sample."""

    bug_id: str
    language: str
    buggy_code: str
    correct_code: str
    test_code: str | None
    file_path: str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "bug_id": self.bug_id,
            "language": self.language,
            "buggy_code": self.buggy_code,
            "correct_code": self.correct_code,
            "test_code": self.test_code,
            "file_path": self.file_path,
            "metadata": self.metadata,
        }


class BugDataset(ABC):
    """Abstract dataset of buggy programs."""

    def __init__(self) -> None:
        self._samples: dict[str, BugSample] = {}

    @abstractmethod
    def load(self) -> None:
        """Load all samples into memory."""

    def __len__(self) -> int:
        return len(self._samples)

    def __iter__(self) -> Iterator[BugSample]:
        return iter(self._samples.values())

    def get(self, bug_id: str) -> BugSample | None:
        """Retrieve a sample by its identifier."""
        return self._samples.get(bug_id)

    @abstractmethod
    def evaluate_patch(self, sample: BugSample, patched_code: str) -> bool:
        """Return True if patched code passes the held-out tests."""

    def evaluate_patch_with_output(
        self, sample: BugSample, patched_code: str
    ) -> tuple[bool, str]:
        """Return (passed, output) for a patched code sample.

        Subclasses may override this to provide detailed test output.
        """
        return self.evaluate_patch(sample, patched_code), ""
