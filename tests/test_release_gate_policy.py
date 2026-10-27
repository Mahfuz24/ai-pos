import importlib.util
import json
import os
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_release.py"
spec = importlib.util.spec_from_file_location("release_verify", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

BASE = {
    "schema_version": 1,
    "repository": "Mahfuz24/ai-pos",
    "target_branch": "main",
    "candidate_sha": "a" * 40,
    "approved_sha": "a" * 40,
    "approved_by": "Mahfuz24",
    "approved_at": "2026-10-27T00:00:00Z",
    "approval_source": "repository-json",
    "release_authorized": True,
}

@pytest.fixture(autouse=True)
def env(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_REPOSITORY", "Mahfuz24/ai-pos")
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    (tmp_path / "governance").mkdir()

def run_case(data):
    Path("governance/release-approval.json").write_text(json.dumps(data))
    with pytest.raises(SystemExit) as exc:
        gate.main()
    assert exc.value.code == 1

def test_missing_approval():
    with pytest.raises(SystemExit) as exc:
        gate.main()
    assert exc.value.code == 1

def test_unapproved():
    run_case({**BASE, "release_authorized": False})

def test_forged_founder():
    run_case({**BASE, "approved_by": "attacker"})

def test_stale_candidate():
    run_case({**BASE, "candidate_sha": "b" * 40})

def test_stale_approval():
    run_case({**BASE, "approved_sha": "b" * 40})

def test_self_asserted_approval_rejected():
    run_case(BASE)

def test_invalid_event(monkeypatch):
    monkeypatch.setenv("GITHUB_EVENT_NAME", "unknown")
    run_case(BASE)

def test_wrong_repository(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "other/repo")
    run_case(BASE)

def test_missing_timestamp():
    run_case({**BASE, "approved_at": "UNSET"})
