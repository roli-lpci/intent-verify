from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Verdict(str, Enum):
    VERIFIED = "verified"
    PARTIAL = "partial"
    MISSING = "missing"


@dataclass(frozen=True)
class ItemResult:
    text: str
    tokens: list[str]
    coverage: float
    verdict: Verdict
    evidence_paths: list[str]


@dataclass(frozen=True)
class CheckResult:
    spec_path: str
    repo_path: str
    files_scanned: int
    items: list[ItemResult]
    average_coverage: float
    verdict: Verdict
    min_verified: float
    min_item: float
    evidence_roots: list[str]
