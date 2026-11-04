"""Workbench service configuration: repository paths and environment settings.

Environment variables (all optional):
  ACT_GUI_RECORDS  run records root (default <repo>/var/records)
  ACT_GUI_SECRETS  uploaded solver licenses (default <records>/../secrets)
  ACT_GUI_MODELS   nets built from model sources (default <records>/../models)
  ACT_GUI_DEVICE   torch device requested for run workers: cpu (default) or cuda
ACT_ROOT (the ACT checkout) is read by engine_bridge.engine_session.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = REPO_ROOT / "fixtures" / "catalog.json"
WEB_DIST = REPO_ROOT / "dist" / "web"


def records_root() -> Path:
    return Path(os.environ.get("ACT_GUI_RECORDS", REPO_ROOT / "var" / "records"))


def secrets_root(records: Path) -> Path:
    env = os.environ.get("ACT_GUI_SECRETS")
    return Path(env) if env else records.parent / "secrets"


def models_root(records: Path) -> Path:
    return Path(os.environ.get("ACT_GUI_MODELS", records.parent / "models"))


def requested_device() -> str:
    return os.environ.get("ACT_GUI_DEVICE", "cpu")
