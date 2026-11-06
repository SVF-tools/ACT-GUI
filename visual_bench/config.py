"""Workbench service configuration: repository paths and environment settings.

Environment variables (all optional):
  ACT_GUI_RECORDS  run records root (default <repo>/var/records)
  ACT_GUI_SECRETS  uploaded solver licenses (default <records>/../secrets)
  ACT_GUI_MODELS   nets built from model sources (default <records>/../models)
  ACT_GUI_DEVICE   torch device requested for run workers: cpu (default) or cuda
  ACT_GUI_ENGINES  staged ACT branch checkouts and the active choice (default <records>/../engines)
  ACT_GUI_ACT_REMOTES  ACT repositories offered for branch switching, as name=url,name=url
  ACT_GUI_ALLOW_CUSTOM_REMOTES  0 forbids users to enter their own https repository URL (default 1)
ACT_ROOT (the baseline ACT checkout) is read by engine_bridge.engine_session; the engine service
sets ACT_CODE_ROOT when a branch is selected.
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


def engines_root(records: Path) -> Path:
    return Path(os.environ.get("ACT_GUI_ENGINES", records.parent / "engines"))


DEFAULT_ACT_REMOTES = "SVF-tools=https://github.com/SVF-tools/ACT.git,guanqin-123=https://github.com/guanqin-123/ACT.git"


def act_remotes() -> dict[str, str]:
    """Operator-configured remotes, always offered; users may add others unless allow_custom_remotes() is off."""
    pairs = (p.split("=", 1) for p in os.environ.get("ACT_GUI_ACT_REMOTES", DEFAULT_ACT_REMOTES).split(",") if "=" in p)
    return {name.strip(): url.strip() for name, url in pairs if name.strip() and url.strip()}


def allow_custom_remotes() -> bool:
    return os.environ.get("ACT_GUI_ALLOW_CUSTOM_REMOTES", "1") != "0"


def requested_device() -> str:
    return os.environ.get("ACT_GUI_DEVICE", "cpu")
