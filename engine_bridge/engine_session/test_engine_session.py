"""Engine binding and solver probe tests against the real pinned ACT checkout.

Expectations come from direct native ACT calls or from fixtures/catalog.json (recorded by
scripts/record_fixtures.py from direct ACT calls); no synthetic fixtures.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from engine_bridge.contracts import BridgeError
from engine_bridge.engine_session import act_imports, fetch_checkout, list_branches, probe, probe_gurobi, probe_isolated
from engine_bridge.engine_session.parity import Requirement, _check
from engine_bridge.testing import CATALOG, fake_act_remote

REPO = Path(__file__).resolve().parents[2]


def test_probe_reports_pinned_commit_and_unsupported_hooks():
    info = probe(CATALOG["act"]["commit"])
    assert info.usable and info.commit == CATALOG["act"]["commit"]
    caps = {c.name: c.availability for c in info.capabilities}
    assert caps["verify.bab"] == "available"
    assert caps["events.bab_nodes"] == "unsupported"

def test_probe_missing_act_is_a_deterministic_error(tmp_path):
    info = probe(CATALOG["act"]["commit"], root=tmp_path / "no-act")
    assert not info.usable
    assert [d.code for d in info.diagnostics] == ["act_missing"]
    assert all(c.availability == "unsupported" for c in info.capabilities)

def test_probe_version_mismatch_is_a_warning():
    info = probe("0" * 40)
    assert info.usable
    assert "version_mismatch" in [d.code for d in info.diagnostics]
    assert {d.severity for d in info.diagnostics} == {"warning"}

def test_branch_checkout_is_staged_reused_and_linked_to_baseline_assets(tmp_path):
    url, commits = fake_act_remote(tmp_path / "remote")
    assets = tmp_path / "baseline"
    (assets / "data").mkdir(parents=True)
    assert list_branches(url) == ("broken", "feature")
    co = fetch_checkout(url, "feature", tmp_path / "engines", assets)
    assert co.commit == commits["feature"] and co.path.name == co.commit
    assert (co.path / "act" / "__init__.py").read_text() == "BRANCH = 'feature'\n"
    assert (co.path / "data").resolve() == (assets / "data").resolve()
    assert not (co.path / "literature").exists()
    assert fetch_checkout(url, "feature", tmp_path / "engines", assets).path == co.path
    with pytest.raises(BridgeError) as err:
        fetch_checkout(url, "nope", tmp_path / "engines", assets)
    assert err.value.code == "branch_not_found"

def test_staged_checkout_is_imported_via_act_code_root_and_probed_in_isolation(tmp_path):
    url, commits = fake_act_remote(tmp_path / "remote")
    engines = tmp_path / "engines"
    stub = fetch_checkout(url, "feature", engines, tmp_path).path
    script = "from engine_bridge.engine_session import act_imports\nwith act_imports():\n import act; print('@@', act.BRANCH)\n"
    out = subprocess.run([sys.executable, "-c", script], env=dict(os.environ, ACT_CODE_ROOT=str(stub), PYTHONPATH=str(REPO)),
                         capture_output=True, text=True, timeout=120)
    assert [l for l in out.stdout.splitlines() if l.startswith("@@ ")] == ["@@ feature"], out.stderr
    info = probe_isolated(CATALOG["act"]["commit"], stub)
    assert info.usable and info.commit == commits["feature"] and info.act_root == str(stub)
    assert [d.code for d in info.diagnostics] == ["version_mismatch", "api_mismatch"]
    caps = {c.name: c.availability for c in info.capabilities}
    assert caps["verify.interval"] == "unsupported" and caps["fuzz.actfuzzer"] == "unsupported"
    assert info.api_checks and not any(c.ok for c in info.api_checks)
    broken = probe_isolated(CATALOG["act"]["commit"], fetch_checkout(url, "broken", engines, tmp_path).path)
    assert not broken.usable and [d.code for d in broken.diagnostics] == ["act_import_failed"]

def test_pinned_baseline_passes_every_api_check():
    info = probe(CATALOG["act"]["commit"])
    # ACT-06 and ACT-07 are deliberately optional on this pinned baseline. Keep every existing
    # adapter check mandatory and assert the precise missing observation surface.
    assert info.api_checks
    required = [c for c in info.api_checks if c.capability not in ("observe.propagation", "verify.dual.options", "fuzz.control")]
    assert required and [c for c in required if not c.ok] == []
    observation = [c for c in info.api_checks if c.capability == "observe.propagation"]
    assert {c.symbol for c in observation if not c.ok} == {
        *(f"act.pipeline.gui.common_gui:{name}" for name in ("observe", "emit")),
        *(f"act.pipeline.gui.verifier_gui:{name}" for name in
          ("RecordKey", "LayerBounds", "Relaxation", "DualBackward", "SpecBound"))}
    assert next(c for c in info.capabilities if c.name == "observe.propagation").availability == "unsupported"
    assert next(c for c in info.capabilities if c.name == "verify.dual.options").availability == "unsupported"
    assert next(c for c in info.capabilities if c.name == "fuzz.control").availability == "unsupported"
    assert {c.capability for c in info.api_checks} <= {c.name for c in info.capabilities}

def test_api_check_reports_missing_symbols_and_signature_mismatches():
    with act_imports():
        assert _check(Requirement("act.back_end.verifier:verify_once", positional=1)) is None
        assert "has no no_such_fn" in _check(Requirement("act.back_end.verifier:no_such_fn"))
        assert "cannot import" in _check(Requirement("act.no_such_module:x"))
        assert "does not accept no_such_param" in _check(
            Requirement("act.back_end.bab.bab:verify_bab_batched", ("net", "no_such_param")))
        assert "positional arguments" in _check(Requirement("act.back_end.analyze:analyze", positional=9))


def test_capability_availability_is_cached_per_checkout(monkeypatch, tmp_path):
    """Synthetic requirement: cache mechanics only, not evidence of native ACT capability."""
    from contextlib import nullcontext
    from engine_bridge.engine_session import parity, session

    checked = []
    monkeypatch.setattr(parity, "requirements", lambda: {"test.control": (Requirement("fake:control"),)})
    monkeypatch.setattr(parity, "_check", lambda req: checked.append(req.symbol))
    monkeypatch.setattr(session, "act_imports", lambda root: nullcontext(root))
    monkeypatch.setattr(session, "act_code_root", lambda: tmp_path / "first")
    assert parity.capability_available("test.control")
    assert parity.capability_available("test.control")
    assert checked == ["fake:control"]
    monkeypatch.setattr(session, "act_code_root", lambda: tmp_path / "second")
    assert parity.capability_available("test.control")
    assert checked == ["fake:control", "fake:control"]
    assert not parity.capability_available("unknown")

def test_gurobi_probe_reports_gurobi_license_rejection(tmp_path):
    lic = tmp_path / "gurobi.lic"
    lic.write_text("TYPE=ACADEMIC\nVERSION=13\nHOSTID=deadbeef\nUSERNAME=nobody\nKEY=ABCDEFGH\n")
    status = probe_gurobi(lic)
    if status.license_state == "not_installed":
        pytest.skip("gurobipy is not installed in this environment")
    assert status.license_state == "invalid" and "HostID mismatch" in status.message
    assert status.version is not None
    missing = probe_gurobi(tmp_path / "absent.lic")
    assert missing.license_state == "invalid" and "absent.lic" in missing.message
