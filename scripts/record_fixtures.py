"""BASE-03: record the real-fixture catalog from direct (native) ACT calls.

Writes fixtures/catalog.json: the pinned ACT commit, each model's path relative
to ACT_ROOT with its sha256, and ACT's native verdicts. ACT network files are not
copied (ACT is AGPL-3.0); they are pinned by commit + hash instead.

    ACT_ROOT=/data1/guanqin/ACT CUDA_VISIBLE_DEVICES= .venv/bin/python scripts/record_fixtures.py
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACT_ROOT = Path(os.environ.get("ACT_ROOT", "/data1/guanqin/ACT")).resolve()
sys.path.insert(0, str(ACT_ROOT))
logging.disable(logging.WARNING)

MODELS = [
    ("bab_deep_mlp", "act/back_end/examples/nets/layer_testing_bab_deep.json", ["interval", "bab"],
     "4-8-4-2 ReLU MLP, box input; interval is inconclusive, BaB certifies"),
    ("unsafe_linear", "act/back_end/examples/nets/layer_testing_unsafe_linear.json", ["interval", "bab"],
     "Linear network whose property is violated; BaB finds a counterexample"),
    ("range_check", "act/back_end/examples/nets/layer_testing_range.json", ["interval", "bab"],
     "Range output property certified by interval analysis"),
    ("cnn_1x8x8", "act/back_end/examples/nets/cnn2d_plain_1x8x8_8_322351658.json", ["interval"],
     "Small CNN (conv/relu/avgpool/flatten/dense); BaB is not recorded (exceeds a 15 s budget)"),
]
BAB_BUDGET_S = 15.0


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    from act.back_end.bab.bab import verify_bab_batched
    from act.back_end.serialization.serialization import load_net_from_file
    from act.back_end.solver.solver_torchlp import TorchLPSolver
    from act.back_end.verifier import verify_once
    from act.config.config import BackendConfig, PipelineConfig
    import torch

    commit = subprocess.run(["git", "-C", str(ACT_ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    models = []
    for model_id, rel, methods, note in MODELS:
        path = ACT_ROOT / rel
        native: dict[str, dict] = {}
        for method in methods:
            net = load_net_from_file(str(path))
            t = time.perf_counter()
            if method == "interval":
                res = verify_once(net)[0]
            else:
                pc = PipelineConfig.from_yaml()
                res = verify_bab_batched(net, solver_factory=TorchLPSolver, config=pc.bab,
                                         max_batch_size=BackendConfig.from_yaml().bab_max_batch_size,
                                         time_budget_s=BAB_BUDGET_S, dual_config=pc.dual)
            native[method] = {"status": res.status.name, "elapsed_s": round(time.perf_counter() - t, 3),
                              "nodes": res.metadata.get("nodes") if method == "bab" else None}
            print(model_id, method, native[method], flush=True)
        models.append({"id": model_id, "act_path": rel, "sha256": sha256(path), "methods": methods,
                       "description": note, "native": native})
    catalog = {
        "kind": "act-gui-fixture-catalog", "version": 1,
        "act": {"repo": "https://github.com/SVF-tools/ACT", "commit": commit},
        "environment": {"python": platform.python_version(), "torch": torch.__version__, "device": "cpu",
                        "env": "conda act-py312", "bab_budget_s": BAB_BUDGET_S,
                        "bab_entry": "verify_bab_batched(TorchLPSolver, PipelineConfig.from_yaml().bab)"},
        "recorded_by": "scripts/record_fixtures.py",
        "models": models,
    }
    out = ROOT / "fixtures" / "catalog.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(catalog, indent=2) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
