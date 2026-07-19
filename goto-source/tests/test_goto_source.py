import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from goto_source import main

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "project"
CASES = json.loads((Path(__file__).parent / "cases.json").read_text())


def abs_expected(relative: str) -> str:
    path, line = relative.rsplit(":", 1)
    return f"{(FIXTURE_DIR / path).resolve()}:{line}"


@pytest.mark.parametrize("case", CASES, ids=[c["description"] for c in CASES])
def test_goto_source(case):
    result = CliRunner().invoke(main, [case["selector"], str(FIXTURE_DIR)])
    assert result.exit_code == 0, f"stderr: {result.output}"
    actual = sorted(result.output.strip().splitlines())
    expected = sorted(abs_expected(e) for e in case["expected"])
    assert actual == expected
