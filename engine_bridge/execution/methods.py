"""Which run methods the bridge can execute on a JSON ACT net (EXE-05).

The workbench asks here instead of encoding ACT entry-point limits itself.
"""
from __future__ import annotations

from engine_bridge.contracts import Domain, Method

VERIFY_METHODS: tuple[Method, ...] = ("interval", "bab")
# ACTFuzzer runs on every JSON ACT net that ACTToTorch rebuilds, including nets with batched INPUT rows.
UNIVERSAL_METHODS: tuple[Method, ...] = ("fuzz",)


def required_capability(method: Method, domain: Domain | None = None) -> str:
    """The engine_session capability whose API checks the adapter for this run needs."""
    if method == "fuzz":
        return "fuzz.actfuzzer"
    return "verify.bab" if method == "bab" else f"verify.{domain or 'interval'}"


def verify_methods(input_rows: int) -> tuple[Method, ...]:
    """verify_once checks every INPUT row (one verdict per lane); BaB takes a single-instance net only."""
    return VERIFY_METHODS if input_rows == 1 else ("interval",)
