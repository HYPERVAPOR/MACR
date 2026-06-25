"""QuixBugs dataset adapter."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib import request
from zipfile import ZipFile

from macr.datasets.base import BugDataset, BugSample

logger = logging.getLogger(__name__)

QUIXBUGS_URL = "https://github.com/jkoppel/QuixBugs/archive/refs/heads/master.zip"


@dataclass
class QuixBugsSample(BugSample):
    """A QuixBugs sample with pytest testcase information."""

    test_file_path: str | None = None


class QuixBugsDataset(BugDataset):
    """Adapter for the QuixBugs benchmark."""

    def __init__(self, root_dir: str | Path | None = None, language: str = "python") -> None:
        if language not in {"python", "java"}:
            raise ValueError(f"Unsupported language: {language}")
        self._language = language
        self._root = Path(root_dir) if root_dir else Path("data/quixbugs")
        self._samples: dict[str, QuixBugsSample] = {}  # type: ignore[assignment]

    @property
    def name(self) -> str:
        return f"QuixBugs-{self._language}"

    def load(self, *, verify_correct: bool = True) -> None:
        """Ensure QuixBugs data is available and parse samples.

        Args:
            verify_correct: If True, run each testcase against the correct
                version before adding the sample. This can be slow.
        """
        if not self._root.exists():
            self._download()

        buggy_dir = self._root / f"{self._language}_programs"
        correct_dir = self._root / f"correct_{self._language}_programs"
        testcases_dir = self._root / f"{self._language}_testcases"

        if not buggy_dir.exists():
            raise FileNotFoundError(f"Buggy directory not found: {buggy_dir}")

        suffix = ".py" if self._language == "python" else ".java"
        for buggy_file in sorted(buggy_dir.iterdir()):
            if buggy_file.suffix != suffix or buggy_file.name.endswith("_test" + suffix):
                continue
            bug_id = buggy_file.stem
            testcase_file = testcases_dir / f"test_{bug_id}.py"
            if not testcase_file.exists():
                # Files like node.py are helpers, not bugs; skip silently.
                logger.debug("Skipping %s: no testcase file found", bug_id)
                continue
            if self._language == "python":
                self._load_python_sample(buggy_file, correct_dir, testcases_dir, verify_correct)
            else:
                self._load_java_sample(buggy_file, correct_dir)

    def _download(self) -> None:
        """Download QuixBugs from GitHub into a temporary zip and extract."""
        logger.info("Downloading QuixBugs from %s", QUIXBUGS_URL)
        self._root.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            request.urlretrieve(QUIXBUGS_URL, tmp.name)
            tmp_path = tmp.name

        try:
            with ZipFile(tmp_path, "r") as zf:
                prefixes = [
                    "QuixBugs-master/python_programs/",
                    "QuixBugs-master/correct_python_programs/",
                    "QuixBugs-master/python_testcases/",
                    "QuixBugs-master/json_testcases/",
                    "QuixBugs-master/conftest.py",
                    "QuixBugs-master/java_programs/",
                    "QuixBugs-master/correct_java_programs/",
                    "QuixBugs-master/java_testcases/",
                ]
                for member in zf.namelist():
                    if any(member.startswith(prefix) for prefix in prefixes):
                        zf.extract(member, self._root)

            extracted = self._root / "QuixBugs-master"
            if extracted.exists():
                for child in extracted.iterdir():
                    target = self._root / child.name
                    if target.exists():
                        if target.is_dir():
                            shutil.rmtree(target)
                        else:
                            target.unlink()
                    child.rename(target)
                extracted.rmdir()
        finally:
            os.unlink(tmp_path)

    def _load_python_sample(
        self,
        buggy_file: Path,
        correct_dir: Path,
        testcases_dir: Path,
        verify_correct: bool,
    ) -> None:
        bug_id = buggy_file.stem
        correct_file = correct_dir / buggy_file.name
        testcase_file = testcases_dir / f"test_{bug_id}.py"

        if not correct_file.exists():
            logger.warning("Missing correct version for %s", bug_id)
            return
        if not testcase_file.exists():
            logger.warning("Missing testcase file for %s", bug_id)
            return

        buggy_code = buggy_file.read_text(encoding="utf-8")
        correct_code = correct_file.read_text(encoding="utf-8")

        if verify_correct:
            # Verify the correct version passes its pytest testcase.
            correct_passed = self._run_pytest(
                bug_id=bug_id,
                program_code=correct_code,
                testcase_file=testcase_file,
                use_correct=True,
            )
            if not correct_passed:
                logger.warning(
                    "Correct version for %s does not pass its testcase; skipping", bug_id
                )
                return

        sample = QuixBugsSample(
            bug_id=bug_id,
            language="python",
            buggy_code=buggy_code,
            correct_code=correct_code,
            test_code=None,
            file_path=str(buggy_file),
            test_file_path=str(testcase_file),
            metadata={"correct_code": correct_code, "expected_output": "PASS"},
        )
        self._samples[bug_id] = sample

    def _load_java_sample(self, buggy_file: Path, correct_dir: Path) -> None:
        # Java evaluation requires compilation; placeholder for future extension.
        bug_id = buggy_file.stem
        buggy_code = buggy_file.read_text(encoding="utf-8")
        sample = QuixBugsSample(
            bug_id=bug_id,
            language="java",
            buggy_code=buggy_code,
            correct_code="",
            test_code=None,
            file_path=str(buggy_file),
            test_file_path=None,
            metadata={"correct_code": None, "expected_output": None},
        )
        self._samples[bug_id] = sample

    def _run_pytest(
        self,
        bug_id: str,
        program_code: str,
        testcase_file: Path,
        *,
        use_correct: bool,
        timeout: int = 60,
    ) -> tuple[bool, str]:
        """Run a pytest testcase using the provided program code.

        Creates a temporary copy of the QuixBugs root, overwrites the target
        program file, then invokes pytest on the testcase file.
        """
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            # Copy the whole QuixBugs tree so imports and JSON testdata resolve.
            shutil.copytree(self._root, work_dir / "quixbugs")
            work_root = work_dir / "quixbugs"

            program_file = work_root / "python_programs" / f"{bug_id}.py"
            program_file.write_text(program_code, encoding="utf-8")

            target_test = work_root / "python_testcases" / testcase_file.name
            if not target_test.exists():
                logger.warning("Testcase %s missing in temp copy", testcase_file.name)
                return False, ""

            cmd = [
                sys.executable,
                "-m",
                "pytest",
                str(target_test),
                "-q",
                "--tb=no",
            ]
            if use_correct:
                cmd.append("--correct")

            try:
                result = subprocess.run(
                    cmd,
                    cwd=work_root,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                passed = result.returncode == 0
                output = (result.stdout + "\n" + result.stderr).strip()
                if not passed:
                    logger.debug(
                        "Pytest for %s failed (correct=%s):\n%s",
                        bug_id,
                        use_correct,
                        output,
                    )
                return passed, output
            except subprocess.TimeoutExpired:
                logger.warning("Pytest for %s timed out", bug_id)
                return False, "Timeout"
            except Exception as exc:
                logger.warning("Failed to run pytest for %s: %s", bug_id, exc)
                return False, str(exc)

    def evaluate_patch(self, sample: BugSample, patched_code: str) -> bool:
        """Evaluate a patched version of a Python QuixBugs sample."""
        passed, _ = self.evaluate_patch_with_output(sample, patched_code)
        return passed

    def evaluate_patch_with_output(
        self, sample: BugSample, patched_code: str
    ) -> tuple[bool, str]:
        """Evaluate a patch and return test output."""
        if not isinstance(sample, QuixBugsSample):
            return False, ""
        if sample.test_file_path is None:
            return False, ""
        testcase_file = Path(sample.test_file_path)
        return self._run_pytest(
            bug_id=sample.bug_id,
            program_code=patched_code,
            testcase_file=testcase_file,
            use_correct=False,
            timeout=60,
        )
