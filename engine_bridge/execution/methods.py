"""Which run methods the bridge can execute on a JSON ACT net (EXE-05).

The workbench asks here instead of encoding ACT entry-point limits itself.
"""
from __future__ import annotations

from engine_bridge.contracts import Method

VERIFY_METHODS: tuple[Method, ...] = ("interval", "bab")
# ACTFuzzer runs on every JSON ACT net that ACTToTorch rebuilds, including nets with batched INPUT rows.
UNIVERSAL_METHODS: tuple[Method, ...] = ("fuzz",)


def verify_methods(input_rows: int) -> tuple[Method, ...]:
    """verify_once and BaB check a single input lane, so a net with several INPUT rows is fuzz-only."""
    return VERIFY_METHODS if input_rows == 1 else ()
