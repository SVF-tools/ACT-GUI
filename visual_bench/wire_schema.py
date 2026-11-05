"""Emit the JSON Schema of every workbench wire model (input for scripts/gen_types.mjs)."""
from __future__ import annotations

import json

from pydantic.json_schema import models_json_schema

from visual_bench.schemas import WIRE_MODELS


def main() -> None:
    _, schema = models_json_schema([(m, "serialization") for m in WIRE_MODELS], title="ActGuiWire")
    print(json.dumps(schema, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
