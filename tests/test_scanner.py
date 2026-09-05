from pathlib import Path

from intent_verify.scanner import coverage_for_tokens, evidence_for_tokens, load_repo_blobs


def test_load_repo_blobs_skips_non_source_files():
    fixture = Path(__file__).parent / "fixtures" / "repo_ok"
    blobs = load_repo_blobs(fixture)
    assert any(path.endswith("service.py") for path, _ in blobs)
    assert all(not path.endswith(".png") for path, _ in blobs)


def test_load_repo_blobs_rejects_symlink_escaping_evidence_root(tmp_path):
    evidence_root = tmp_path / "src"
    evidence_root.mkdir()
    (evidence_root / "service.py").write_text("allowed evidence", encoding="utf-8")
    outside = tmp_path / "outside.py"
    outside.write_text("escaped evidence", encoding="utf-8")
    (evidence_root / "linked.py").symlink_to(outside)

    blobs = load_repo_blobs(tmp_path, evidence_paths=[evidence_root])

    assert blobs == [("src/service.py", "allowed evidence")]


def test_coverage_for_tokens():
    blobs = [("a.py", "uploads pdf invoices and retries timeout")]
    assert coverage_for_tokens(["uploads", "pdf", "timeout"], blobs) == 1.0


def test_evidence_for_tokens_returns_only_contributing_paths():
    blobs = [
        ("src/a.py", "uploads pdf invoices"),
        ("src/b.py", "retries timeout"),
        ("README.md", "unrelated prose"),
    ]
    coverage, paths = evidence_for_tokens(["uploads", "pdf", "timeout"], blobs)
    assert coverage == 1.0
    assert paths == ["src/a.py", "src/b.py"]
