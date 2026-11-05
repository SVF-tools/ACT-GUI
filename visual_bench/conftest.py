"""Fixtures shared by the workbench HTTP tests: a fresh app with its own records root per test."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from visual_bench.server import create_app


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(tmp_path / "records"))
