import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from goto_source import main

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "project"
CASES = json.loads((Path(__file__).parent / "cases.json").read_text())


def abs_expected(relative: str) -> str:
    label, sep, location = relative.rpartition("\t")
    path, line = location.rsplit(":", 1)
    return f"{label}{sep}{(FIXTURE_DIR / path).resolve()}:{line}"


@pytest.mark.parametrize("case", CASES, ids=[c["description"] for c in CASES])
def test_goto_source(case):
    args = case.get("flags", []) + [case["selector"], str(FIXTURE_DIR)]
    result = CliRunner().invoke(main, args)
    assert result.exit_code == 0, f"stderr: {result.output}"
    actual = result.output.strip().splitlines()
    expected = [abs_expected(e) for e in case["expected"]]
    assert actual == expected
