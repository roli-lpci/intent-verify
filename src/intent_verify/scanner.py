from __future__ import annotations

import os
from pathlib import Path

DEFAULT_EXTENSIONS = {
    ".cfg",
    ".go",
    ".ini",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".py",
    ".rs",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}

DEFAULT_SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "target",
    "venv",
}


def load_repo_blobs(
    repo_path: Path,
    evidence_paths: list[Path] | None = None,
    extensions: set[str] | None = None,
    exclude_paths: set[Path] | None = None,
) -> list[tuple[str, str]]:
    exts = extensions or DEFAULT_EXTENSIONS
    excluded = {path.resolve() for path in (exclude_paths or set())}
    blobs: list[tuple[str, str]] = []
    roots = evidence_paths or [repo_path]
    candidates: list[tuple[Path, Path]] = []
    for root_path in roots:
        resolved_root = root_path.resolve()
        if root_path.is_file():
            candidates.append((root_path, resolved_root.parent))
            continue
        for root, dirs, files in os.walk(root_path):
            dirs[:] = [
                name
                for name in dirs
                if name not in DEFAULT_SKIP_DIRS and not name.startswith(".")
            ]
            candidates.extend((Path(root) / name, resolved_root) for name in files)

    seen: set[Path] = set()
    for path, evidence_root in candidates:
        resolved = path.resolve()
        try:
            resolved.relative_to(evidence_root)
        except ValueError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved in excluded:
            continue
        suffix = path.suffix.lower()
        if suffix not in exts:
            continue
        try:
            display_path = str(path.resolve().relative_to(repo_path.resolve()))
        except ValueError:
            display_path = str(path)
        try:
            blobs.append((display_path, path.read_text(encoding="utf-8", errors="ignore").lower()))
        except OSError:
            continue
    return blobs


def coverage_for_tokens(tokens: list[str], blobs: list[tuple[str, str]]) -> float:
    coverage, _ = evidence_for_tokens(tokens, blobs)
    return coverage


def evidence_for_tokens(
    tokens: list[str], blobs: list[tuple[str, str]]
) -> tuple[float, list[str]]:
    if not tokens:
        return 0.0, []
    found: set[str] = set()
    evidence_paths: list[str] = []
    for path, blob in blobs:
        matched_here = False
        for token in tokens:
            if token in found:
                continue
            if token in blob:
                found.add(token)
                matched_here = True
        if matched_here:
            evidence_paths.append(path)
        if len(found) == len(tokens):
            break
    return len(found) / len(tokens), evidence_paths
