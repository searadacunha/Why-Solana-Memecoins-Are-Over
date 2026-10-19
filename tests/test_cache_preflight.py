"""Missing private inputs must stop a reproduction before it publishes new results."""

import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def economic_lib(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(ROOT / "economic_mechanics" / "code"))
    module = importlib.import_module("em_lib")
    monkeypatch.setattr(module.FB, "GEN_HOP", str(tmp_path / "missing_hops"))
    return module


def test_absent_hop_is_not_an_empty_history(economic_lib):
    with pytest.raises(economic_lib.MissingCacheError, match="required genesis_hop cache is missing"):
        economic_lib.hop("synthetic_funder")


def test_explicit_empty_collection_remains_valid(economic_lib):
    # Synthetic test input, kept outside the repository's collection directories.
    folder = Path(economic_lib.FB.GEN_HOP)
    folder.mkdir()
    (folder / "synthetic_funder.json").write_text("{}", encoding="utf8")
    assert economic_lib.hop("synthetic_funder") == {}


def test_frozen_table_can_be_read_without_private_cache(economic_lib):
    rows = economic_lib.load()
    expected = json.loads(Path(economic_lib.FREEZE).read_text())["rows"]
    assert len(rows) == expected
    assert economic_lib.sniper_lifecycle(rows[0], rows[0]["snipers"][0])["tok_bought"] > 0


def run_isolated(code, *args):
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run(
        [sys.executable, "-c", code, str(ROOT), *map(str, args)],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


@pytest.mark.parametrize("script", [
    "economic_mechanics/code/em_20_analysis.py",
    "funder_network/code/fn_30_analysis.py",
])
def test_analysis_stops_before_any_write_when_cache_is_missing(script, tmp_path):
    result = run_isolated(
        """
import os
from pathlib import Path
import runpy
import sys

root, rel, absent = map(Path, sys.argv[1:])
sys.path.insert(0, str(root / "economic_mechanics" / "code"))
import em_lib
em_lib.FB.GEN_HOP = str(absent)

def forbid_writes(event, args):
    if event == "open":
        mode, flags = args[1], args[2]
        if (isinstance(mode, str) and any(c in mode for c in "wax+")) or flags & (os.O_WRONLY | os.O_RDWR):
            raise AssertionError("unexpected write before input preflight")

sys.addaudithook(forbid_writes)
script = root / rel
sys.path.insert(0, str(script.parent))
runpy.run_path(str(script), run_name="__main__")
""",
        script,
        tmp_path / "absent_hops",
    )
    assert result.returncode != 0
    assert "required genesis_hop cache is missing" in result.stderr
    assert "unexpected write before input preflight" not in result.stderr


@pytest.mark.parametrize("study,module", [
    ("exit_destination", "ed_20_build"),
    ("funder_network", "fn_20_build"),
])
def test_build_does_not_replace_a_frozen_table_with_partial_input(study, module, tmp_path):
    # Exercise the entry point with synthetic collection metadata and a changed
    # in-memory build. No private inputs are invented in the real study folders.
    result = run_isolated(
        """
import importlib
import json
from pathlib import Path
import sys

root, fixture = Path(sys.argv[1]), Path(sys.argv[4])
sys.path.insert(0, str(root / sys.argv[2] / "code"))
build = importlib.import_module(sys.argv[3])
(fixture / "budget.json").write_text('{"calls": 0, "fails": 0}')
(fixture / "collect.log").write_text("stopped: synthetic test fixture\\n")
(fixture / "selection.json").write_text("{}")
build.L.CACHE = str(fixture)
build.L.SELECTION = str(fixture / "selection.json")
build.C.run = lambda *args: {"partial_synthetic_input": True}
if sys.argv[2] == "exit_destination":
    build.E.load = lambda: []
    build.T.Roles = lambda rows: None
build.TABLE = str(fixture / "table.json.gz")
build.FREEZE = str(fixture / "freeze.json")
build.INTEGRITY = str(fixture / "integrity.json")
Path(build.TABLE).write_bytes(b"original frozen table")
Path(build.FREEZE).write_text(json.dumps({"sha256_table": "original frozen digest"}))
Path(build.INTEGRITY).write_text("original integrity report")
paths = [Path(build.TABLE), Path(build.FREEZE), Path(build.INTEGRITY)]
before = [p.read_bytes() for p in paths]
try:
    build.main()
except SystemExit as exc:
    assert "differs from the frozen one" in str(exc), str(exc)
else:
    raise AssertionError("partial input was allowed to replace the frozen table")
assert [p.read_bytes() for p in paths] == before
""",
        study,
        module,
        tmp_path,
    )
    assert result.returncode == 0, result.stderr
