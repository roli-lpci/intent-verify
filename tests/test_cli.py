import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "intent_verify.cli", *args],
        cwd=ROOT,
        env={"PYTHONPATH": str(ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_verified_fixture():
    fixture = ROOT / "tests" / "fixtures" / "repo_ok"
    result = run_cli("check", "--spec", str(fixture / "INTENT.md"), "--repo", str(fixture))
    assert result.returncode == 0
    assert "VERIFIED" in result.stdout


def test_cli_partial_fixture_json():
    fixture = ROOT / "tests" / "fixtures" / "repo_partial"
    result = run_cli(
        "check",
        "--spec",
        str(fixture / "INTENT.md"),
        "--repo",
        str(fixture),
        "--json",
    )
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["verdict"] == "partial"


def test_cli_missing_fixture():
    fixture = ROOT / "tests" / "fixtures" / "repo_missing"
    result = run_cli("check", "--spec", str(fixture / "INTENT.md"), "--repo", str(fixture))
    assert result.returncode == 2
    assert "MISSING" in result.stdout


@pytest.mark.parametrize("command", ["check", "map"])
def test_cli_rejects_directory_spec_without_traceback(command: str):
    fixture = ROOT / "tests" / "fixtures" / "repo_ok"
    args = [command, "--spec", str(fixture), "--repo", str(fixture)]
    if command == "map":
        args.extend(["--evidence-path", "src"])

    result = run_cli(*args)

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == f"intent-verify: spec path is not a file: {fixture}\n"
    assert "Traceback" not in result.stderr


def test_map_emits_provenance_and_non_authoritative_contract():
    fixture = ROOT / "tests" / "fixtures" / "repo_ok"
    result = run_cli(
        "map",
        "--spec",
        str(fixture / "INTENT.md"),
        "--repo",
        str(fixture),
        "--evidence-path",
        "src",
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "intent-verify.coverage-map.v1"
    assert payload["signal_kind"] == "lexical_scope_coverage"
    assert payload["acceptance_authority"] is False
    assert payload["evidence_roots"] == ["src"]
    assert payload["verdict"] == "covered"
    assert payload["decision"] == "review"
    assert payload["items"][0]["evidence_paths"] == ["src/app/service.py"]


def test_map_does_not_credit_matching_readme_outside_evidence_paths():
    fixture = ROOT / "tests" / "fixtures" / "repo_docs_only"
    result = run_cli(
        "map",
        "--spec",
        str(fixture / "INTENT.md"),
        "--repo",
        str(fixture),
        "--evidence-path",
        "src",
    )
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["verdict"] == "gap"
    assert payload["decision"] == "inspect"
    assert payload["items"][0]["evidence_paths"] == []


def test_map_rejects_evidence_path_outside_repo():
    fixture = ROOT / "tests" / "fixtures" / "repo_ok"
    result = run_cli(
        "map",
        "--spec",
        str(fixture / "INTENT.md"),
        "--repo",
        str(fixture),
        "--evidence-path",
        "../repo_missing",
    )
    assert result.returncode == 2
    assert "escapes repo" in result.stderr
