"""Helpers shared by the engine_bridge parity tests: the pinned catalog and native ACT loading."""
from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

import pytest

from engine_bridge.engine_session import act_imports, act_root

logging.disable(logging.WARNING)
CATALOG = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "catalog.json").read_text())
MODELS = {m["id"]: m for m in CATALOG["models"]}


def model_path(model_id: str) -> Path:
    return act_root() / MODELS[model_id]["act_path"]


def native_net(model_id: str):
    with act_imports():
        from act.back_end.serialization.serialization import load_net_from_file
        return load_net_from_file(str(model_path(model_id)))


def fake_act_remote(root: Path) -> tuple[str, dict[str, str]]:
    """Synthetic git remote (not ACT): branch `feature` has an importable stub `act` package that
    records its branch name, branch `broken` has one that fails to import. Returns (url, branch -> commit)."""
    def git(*args: str) -> str:
        return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout.strip()

    root.mkdir(parents=True)
    git("init", "-q", "-b", "main")
    commits: dict[str, str] = {}
    for branch, body in (("feature", "BRANCH = 'feature'\n"), ("broken", "raise ImportError('stub branch is broken')\n")):
        git("checkout", "-q", "--orphan", branch)
        (root / "act").mkdir(exist_ok=True)
        (root / "act" / "__init__.py").write_text(body)
        git("add", "act")
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", branch)
        commits[branch] = git("rev-parse", "HEAD")
    return root.as_uri(), commits


def require_sources() -> None:
    from engine_bridge.model_spec import sources

    if not sources.classifier_sources() or not sources.vnnlib_instances():
        pytest.skip("ACT checkout has no literature/ ONNX classifiers or data/vnnlib benchmarks")

