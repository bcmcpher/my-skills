"""Each sweep script finds the pattern planted for it in ``fixture/``.

Run from the repo root:

    uv run --python 3.12 --with pytest --with pytest-cov pytest plugins/codebase-audit/tests
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).parent
FIXTURE = HERE / "fixture"
SCRIPTS = HERE.parent / "skills" / "codebase-audit" / "scripts"


def run(script: str, *args: str) -> dict:
    out = subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args, "--json"],
        cwd=FIXTURE, capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


def test_inventory_outlines_a_module_by_line_range():
    data = run("inventory.py", "src/demo", "--outline-min", "10", "--class-min", "5")
    items = data["outlines"]["src/demo/core.py"]
    names = {i["name"]: (i["start"], i["end"]) for i in items}
    assert "load" in names and "Widget.size" in names
    assert names["load"][0] < names["load"][1]


def test_dup_logic_finds_the_renamed_copy_and_the_guard():
    data = run("dup_logic.py", "src/demo", "--min-nodes", "10")
    clusters = [{s["name"] for s in c} for c in data["functions"]]
    assert {"_clip", "_bound"} in clusters
    assert "networkx" in data["guards"]


def test_public_callers_reports_the_test_only_method():
    data = run("public_callers.py", "src/demo", "--tests", "tests")
    assert {r["name"] for r in data["test_only"]} == {"Widget.only_tests_call_this", "Widget.size"}
    unused = {r["name"]: r["exported"] for r in data["unused"]}
    assert unused == {"load": True, "Widget.dense_size": False}


def test_raise_taxonomy_flags_the_mixed_mode_refusals():
    data = run("raise_taxonomy.py", "src/demo")
    kinds = {s["kind"]: s["types"] for s in data["summary"]}
    assert kinds["unsupported mode"] == {"NotImplementedError": 1, "ValueError": 1}
    assert kinds["missing state"] == {"RuntimeError": 1}


def test_docstring_signature_finds_the_bad_value_and_the_phantom_param():
    data = run("docstring_signature.py", "src/demo")
    checks = {(i["param"], i["check"]) for i in data["issues"]}
    assert ("policy", "documented value not accepted") in checks
    assert ("extra", "documented, not in signature") in checks


def test_near_dupes_finds_the_argument_cluster_and_the_class_pair():
    data = run("test_near_dupes.py", "tests", "--min-nodes", "5")
    clusters = [{s["name"] for s in c} for c in data["argument"]]
    assert {"test_clip_low", "test_clip_high", "test_clip_none"} in clusters
    pairs = {(p["a"].split()[-1], p["b"].split()[-1]) for p in data["class_pairs"]}
    assert ("TestEdgeWidget", "TestNodeWidget") in pairs


def test_private_access_counts_the_private_import_and_attribute():
    data = run("test_private_access.py", "tests", "--src", "src/demo", "--package", "demo")
    uses = {u for s in data["sites"] for u in s["uses"]}
    assert "_clip" in uses and "._cache" in uses
    assert data["files"]["tests/test_core.py"]["imports"] == 1


def test_spec_inventory_pairs_the_sibling_requirements():
    data = run("spec_inventory.py", "specs", "--tests", "tests")
    pairs = [(d["a"][0], d["b"][0]) for d in data["duplicates"]]
    assert ("widget-edge", "widget-node") in pairs
    assert any("_cache" in line for _, _, line in data["implementation"])
    assert data["unmarked"] == []


def test_coverage_subsets_reads_a_context_database(tmp_path):
    pytest.importorskip("pytest_cov")
    work = tmp_path / "fixture"
    shutil.copytree(FIXTURE, work)
    (work / "conftest.py").write_text(
        "import sys, pytest\nsys.path.insert(0, 'src')\n"
        "def pytest_configure(config):\n    config.addinivalue_line('markers', 'spec(cap, req): requirement')\n"
    )
    subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--cov=demo", "--cov-branch",
         "--cov-context=test", "tests"],
        cwd=work, check=True, capture_output=True,
    )
    out = subprocess.run(
        [sys.executable, str(SCRIPTS / "coverage_subsets.py"), ".coverage", "--min-covered", "1", "--json"],
        cwd=work, capture_output=True, text=True, check=True,
    )
    pairs = json.loads(out.stdout)["pairs"]
    assert pairs, "the two size tests in one class share coverage"


# Regressions from the branch review. Each writes a small tree of its own, so the shared
# fixture's counts stay as they are.


def write(root: Path, files: dict[str, str]) -> Path:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return root


def run_in(cwd: Path, script: str, *args: str) -> dict:
    out = subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args, "--json"],
        cwd=cwd, capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


def test_docstring_signature_checks_constructors_and_shared_names(tmp_path):
    write(tmp_path, {"pkg/m.py": '''
from typing import Literal

class Widget:
    """A widget.

    Parameters
    ----------
    mode : {'a', 'b'}
        The mode.
    """

    def __init__(self, mode: Literal["a", "c"]):
        self.mode = mode


def f(a=6, b=5, c=5):
    """F.

    Parameters
    ----------
    a, b, c : int
        Sizes, default 5.
    """
'''})
    data = run_in(tmp_path, "docstring_signature.py", "pkg")
    checks = {(i["function"], i["param"], i["check"]) for i in data["issues"]}
    assert ("Widget.__init__", "mode", "documented value not accepted") in checks
    assert ("f", "a", "default differs") in checks
    assert data["checked"]["public"] == 2


def test_public_callers_keeps_a_same_named_call_on_another_object(tmp_path):
    write(tmp_path, {"pkg/m.py": '''
class Node:
    def summary(self):
        return 1


class Edge:
    def __init__(self, node):
        self.node = node

    def summary(self):
        return self.node.summary()


def countdown(n):
    return countdown(n - 1) if n else 0
''', "tests/test_m.py": "from pkg.m import Edge\n\ndef test_e():\n    Edge(None)\n"})
    data = run_in(tmp_path, "public_callers.py", "pkg", "--tests", "tests")
    reported = {r["name"] for r in data["unused"] + data["test_only"]}
    unused = {r["name"] for r in data["unused"]}
    assert "Node.summary" not in reported  # Edge.summary calls it
    assert "countdown" in unused  # its only use is its own recursion
    assert "Edge.summary" in unused  # nothing calls the wrapper


def test_dup_logic_separates_same_named_methods_of_sibling_classes(tmp_path):
    block = '''
        if size < 0:
            raise ValueError(f"size must be >= 0, got {size}")
        self.size = int(size) * scale + offset
        self.label = str(label).strip().lower()
'''
    write(tmp_path, {"pkg/m.py": (
        "class EdgeSummary:\n    def __init__(self, size, scale, offset, label):" + block
        + "\n\nclass NodeSummary:\n    def __init__(self, size, scale, offset, label):" + block
    )})
    data = run_in(tmp_path, "dup_logic.py", "pkg", "--block-min-nodes", "10", "--min-nodes", "1000")
    assert data["blocks"], "the copied constructor block spans two functions"


def test_collapse_overlaps_orders_lines_numerically():
    sys.path.insert(0, str(SCRIPTS))
    try:
        from dup_logic import _collapse_overlaps
    finally:
        sys.path.remove(str(SCRIPTS))
    clusters = {
        str(line): [{"site": f"a.py:{line}"}, {"site": f"b.py:{line + 500}"}] for line in (98, 99, 100, 101)
    }
    kept = _collapse_overlaps(clusters, window=3)
    assert [c[0]["site"] for c in kept] == ["a.py:98"]


def test_private_access_needs_the_marker_in_pytestmark(tmp_path):
    write(tmp_path, {
        "pkg/m.py": "def _helper():\n    return 1\n",
        "tests/test_m.py": "import inspect\nimport pytest\nfrom pkg.m import _helper\n\n"
                           "pytestmark = pytest.mark.slow\n\n\ndef test_h():\n    assert _helper() == 1\n",
    })
    data = run_in(tmp_path, "test_private_access.py", "tests", "--src", "pkg")
    assert [s["marked"] for s in data["sites"]] == [False]
    assert data["files"]["tests/test_m.py"]["imports"] == 1


def test_raise_taxonomy_takes_project_mode_terms(tmp_path):
    write(tmp_path, {"pkg/m.py": "def f(x):\n    if x:\n        raise ValueError('dense matrix must be square')\n"})
    kinds = {s["kind"] for s in run_in(tmp_path, "raise_taxonomy.py", "pkg")["summary"] if s["sites"]}
    assert "unsupported mode" not in kinds
    kinds = {s["kind"] for s in run_in(tmp_path, "raise_taxonomy.py", "pkg", "--mode-terms", "dense")["summary"] if s["sites"]}
    assert kinds == {"unsupported mode"}


def test_public_callers_excludes_planning_files_from_extra(tmp_path):
    write(tmp_path, {"pkg/m.py": "def helper():\n    return 1\n",
                     "examples/audit.md": "`helper` has no caller.\n"})
    hidden = run_in(tmp_path, "public_callers.py", "pkg", "--extra", "examples")
    assert hidden["unused"] == []
    found = run_in(tmp_path, "public_callers.py", "pkg", "--extra", "examples", "--exclude", "*.md")
    assert [r["name"] for r in found["unused"]] == ["helper"]
