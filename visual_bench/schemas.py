"""Workbench wire schemas: aggregation point of the per-module payload models.

Pydantic models in visual_bench/<module>/schemas.py are the single handwritten source
for REST/SSE payloads; shared primitives live in visual_bench/wire.py. This module
re-exports them under one namespace (`from visual_bench import schemas as S`) and lists
WIRE_MODELS, the roots that scripts/gen_types.mjs turns into visual_bench/generated/wire.ts
(npm run gen:types; npm run check:types fails on drift).

Adding a payload: define it in the owning module's schemas.py, re-export it here, and add it
to WIRE_MODELS if no listed model already references it.
"""
from __future__ import annotations

from pydantic import BaseModel

from visual_bench.wire import *  # noqa: F403
from visual_bench.wire import ErrorResponse, HealthOut
from visual_bench.engine.schemas import *  # noqa: F403
from visual_bench.model_spec.schemas import *  # noqa: F403
from visual_bench.fuzzing.schemas import *  # noqa: F403
from visual_bench.verification.schemas import *  # noqa: F403
from visual_bench.analysis.schemas import *  # noqa: F403
from visual_bench.bab.schemas import *  # noqa: F403
from visual_bench.assistant.schemas import *  # noqa: F403
from visual_bench.engine.schemas import EngineInfoOut, SolverLicenseUpload, SolverStatusOut
from visual_bench.model_spec.schemas import LoadModelBody, ModelDescriptionOut, ModelSummary, SampleOut, SourcesOut
from visual_bench.fuzzing.schemas import FuzzingOut, SaveCounterexampleRequest, SavedCounterexampleOut
from visual_bench.verification.schemas import RunEvent, RunList, RunOut, RunRequest
from visual_bench.analysis.schemas import LayerStatesOut
from visual_bench.bab.schemas import CoverageOut
from visual_bench.assistant.schemas import ExplainRequest, ExplainResponse, ProviderList

WIRE_MODELS: tuple[type[BaseModel], ...] = (
    ErrorResponse, HealthOut, EngineInfoOut, ModelSummary, ModelDescriptionOut, RunRequest, RunOut, RunList,
    LayerStatesOut, RunEvent, CoverageOut, FuzzingOut, ExplainRequest, ExplainResponse, ProviderList, SolverLicenseUpload,
    SolverStatusOut, SourcesOut, SampleOut, LoadModelBody, SaveCounterexampleRequest, SavedCounterexampleOut,
)
