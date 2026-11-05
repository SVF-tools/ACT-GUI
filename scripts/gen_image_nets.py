"""BASE-03: generate the MNIST/CIFAR-10 catalog nets with the bridge's classifier source builder.

Each net is an L-inf box around one test image with a TOP1_ROBUST assertion on the label the model
predicts for it (engine_bridge.model_spec.sources.build_classifier_net, target="prediction"), saved
into ACT's git-ignored examples/nets/ directory next to the other catalog nets. Run
scripts/record_fixtures.py afterwards.

    ACT_ROOT=/data1/guanqin/ACT CUDA_VISIBLE_DEVICES= .venv/bin/python scripts/gen_image_nets.py
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
logging.disable(logging.WARNING)

from engine_bridge.engine_session import act_root  # noqa: E402
from engine_bridge.model_spec.sources import build_classifier_net  # noqa: E402

OUT_DIR = "act/back_end/examples/nets"
# (output file stem, classifier source id, eps, test-set index)
NETS = [
    ("gui_mnist_relu_6_100", "mnist_relu_6_100", 0.03, 0),
    ("gui_mnist_relu_6_100_eps015", "mnist_relu_6_100", 0.15, 0),
    ("gui_mnist_conv_small", "mnist_conv_small", 0.05, 0),
    ("gui_cifar10_conv_med", "cifar10_conv_med", 2.0 / 255.0, 0),
]


def main() -> None:
    os.chdir(act_root())  # ACT resolves its config relative to the project root
    for stem, source_id, eps, index in NETS:
        out = act_root() / OUT_DIR / f"{stem}.json"
        built = build_classifier_net(source_id, index, eps, out, target="prediction")
        p = built.params
        print(f"{OUT_DIR}/{out.name}: {p['dataset']}[{index}] label={p['label']} predicted={p['predicted']} eps={eps:g}",
              flush=True)


if __name__ == "__main__":
    main()
