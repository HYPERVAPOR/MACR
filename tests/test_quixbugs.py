"""Tests for the QuixBugs dataset adapter."""

from __future__ import annotations

from pathlib import Path

from macr.datasets.quixbugs import QuixBugsDataset

BUGGY_ADD = """\
def add(a, b):
    return a - b
"""

CORRECT_ADD = """\
def add(a, b):
    return a + b
"""

TEST_ADD = """\
import pytest
from load_testdata import load_json_testcases

if pytest.use_correct:
    from correct_python_programs.add import add
else:
    from python_programs.add import add


testdata = load_json_testcases(add.__name__)


@pytest.mark.parametrize("input_data,expected", testdata)
def test_add(input_data, expected):
    assert add(*input_data) == expected
"""

CONFTEST = """\
import pytest


def pytest_addoption(parser):
    parser.addoption("--correct", action="store_true")


def pytest_configure(config):
    pytest.use_correct = config.getoption("--correct")
"""

LOAD_TESTDATA = """\
import json
from pathlib import Path


def load_json_testcases(algorithm):
    quixbugs_root = Path(__file__).parent / ".."
    testdata_path = quixbugs_root / f"json_testcases/{algorithm}.json"
    with open(testdata_path) as data_file:
        testdata = [json.loads(line) for line in data_file]
    return testdata
"""


def test_load_python_samples(tmp_path: Path) -> None:
    root = tmp_path / "quixbugs"
    (root / "python_programs").mkdir(parents=True)
    (root / "correct_python_programs").mkdir(parents=True)
    (root / "python_testcases").mkdir(parents=True)
    (root / "json_testcases").mkdir(parents=True)

    (root / "python_programs" / "add.py").write_text(BUGGY_ADD)
    (root / "correct_python_programs" / "add.py").write_text(CORRECT_ADD)
    (root / "python_testcases" / "test_add.py").write_text(TEST_ADD)
    (root / "python_testcases" / "load_testdata.py").write_text(LOAD_TESTDATA)
    (root / "json_testcases" / "add.json").write_text('[[1, 2], 3]\n[[0, 0], 0]\n')
    (root / "conftest.py").write_text(CONFTEST)

    dataset = QuixBugsDataset(root_dir=root, language="python")
    dataset.load()

    assert len(dataset) == 1
    sample = dataset.get("add")
    assert sample is not None
    assert sample.language == "python"
    assert sample.test_file_path is not None


def test_evaluate_patch_with_real_data() -> None:
    """Evaluate a correct version against the downloaded QuixBugs data."""
    dataset = QuixBugsDataset(language="python")
    dataset.load(verify_correct=False)
    if len(dataset) == 0:
        return

    sample = dataset.get("bitcount")
    if sample is None:
        return

    correct_code = sample.metadata["correct_code"]
    assert dataset.evaluate_patch(sample, correct_code)
    assert not dataset.evaluate_patch(sample, sample.buggy_code)
