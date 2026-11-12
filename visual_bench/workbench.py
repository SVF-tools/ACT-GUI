"""Composition of the workbench services: the single object that wires modules together.

Services depend on each other only through constructor arguments built here, so a module's
service can be tested or replaced without importing the HTTP layer. Both the HTTP routes
(server.py) and the assistant use these services as their application entry points.
"""
from __future__ import annotations

import json
from pathlib import Path

from visual_bench import config
from visual_bench.analysis.service import AnalysisService
from visual_bench.bab.service import BabService
from visual_bench.engine.service import EngineService
from visual_bench.fuzzing.live import FuzzLive
from visual_bench.fuzzing.service import FuzzingService
from visual_bench.model_spec.service import ModelService
from visual_bench.records import RecordStore
from visual_bench.verification.service import RunService


class Workbench:
    def __init__(self, records_root: Path, catalog_path: Path | None = None, secrets_root: Path | None = None) -> None:
        catalog = json.loads((catalog_path or config.CATALOG_PATH).read_text())
        self.records = RecordStore(records_root)
        self.engine = EngineService(catalog["act"]["commit"], secrets_root or config.secrets_root(records_root),
                                    config.engines_root(records_root), config.act_remotes(),
                                    config.allow_custom_remotes())
        self.models = ModelService(catalog, config.models_root(records_root), self.engine)
        live = FuzzLive()
        self.runs = RunService(self.records, self.models, self.engine, live)
        self.engine.active_runs = self.runs.active_count
        self.fuzzing = FuzzingService(self.runs, self.records, self.models, live)
        self.analysis = AnalysisService(self.runs, self.records)
        self.bab = BabService(self.runs, self.records)
