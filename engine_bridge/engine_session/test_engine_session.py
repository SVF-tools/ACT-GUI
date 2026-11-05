"""Engine binding and solver probe tests against the real pinned ACT checkout.

Expectations come from direct native ACT calls or from fixtures/catalog.json (recorded by
scripts/record_fixtures.py from direct ACT calls); no synthetic fixtures.
"""
from __future__ import annotations

import pytest

from engine_bridge.engine_session import probe, probe_gurobi
from engine_bridge.testing import CATALOG


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
    assert [d.code for d in info.diagnostics] == ["version_mismatch"]

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
