from __future__ import annotations

import json
from pathlib import Path

from .models import CheckResult, ItemResult, Verdict
from .parser import parse_spec_items
from .scanner import evidence_for_tokens, load_repo_blobs
from .tokenizer import tokenize


def coverage_verdict(coverage: float, min_verified: float, min_item: float) -> Verdict:
    if coverage >= min_verified:
        return Verdict.VERIFIED
    if coverage >= min_item:
        return Verdict.PARTIAL
    return Verdict.MISSING


def aggregate_verdict(items: list[ItemResult], min_verified: float, min_item: float) -> Verdict:
    if not items:
        return Verdict.MISSING
    if any(item.coverage < min_item for item in items):
        return Verdict.MISSING
    if any(item.coverage < min_verified for item in items):
        return Verdict.PARTIAL
    average = sum(item.coverage for item in items) / len(items)
    if average < min_verified:
        return Verdict.PARTIAL
    return Verdict.VERIFIED


def run_check(
    spec_path: Path,
    repo_path: Path,
    *,
    section: str | None = None,
    min_verified: float = 0.7,
    min_item: float = 0.3,
    evidence_paths: list[Path] | None = None,
) -> CheckResult:
    text = spec_path.read_text(encoding="utf-8")
    items = parse_spec_items(text, section=section)
    blobs = load_repo_blobs(
        repo_path,
        evidence_paths=evidence_paths,
        exclude_paths={spec_path},
    )

    item_results: list[ItemResult] = []
    for item in items:
        tokens = tokenize(item)
        coverage, matched_paths = evidence_for_tokens(tokens, blobs)
        item_results.append(
            ItemResult(
                text=item,
                tokens=tokens,
                coverage=coverage,
                verdict=coverage_verdict(coverage, min_verified, min_item),
                evidence_paths=matched_paths,
            )
        )

    average = (
        sum(item.coverage for item in item_results) / len(item_results)
        if item_results
        else 0.0
    )
    verdict = aggregate_verdict(item_results, min_verified, min_item)
    return CheckResult(
        spec_path=str(spec_path),
        repo_path=str(repo_path),
        files_scanned=len(blobs),
        items=item_results,
        average_coverage=average,
        verdict=verdict,
        min_verified=min_verified,
        min_item=min_item,
        evidence_roots=[
            str(path.resolve().relative_to(repo_path.resolve()))
            if path.resolve() != repo_path.resolve()
            else "."
            for path in evidence_paths or [repo_path]
        ],
    )


def to_json(result: CheckResult) -> str:
    return json.dumps(
        {
            "spec_path": result.spec_path,
            "repo_path": result.repo_path,
            "signal_kind": "lexical_scope_coverage",
            "acceptance_authority": False,
            "evidence_roots": result.evidence_roots,
            "files_scanned": result.files_scanned,
            "average_coverage": round(result.average_coverage, 3),
            "verdict": result.verdict.value,
            "thresholds": {
                "min_verified": result.min_verified,
                "min_item": result.min_item,
            },
            "items": [
                {
                    "text": item.text,
                    "tokens": item.tokens,
                    "coverage": round(item.coverage, 3),
                    "verdict": item.verdict.value,
                    "evidence_paths": item.evidence_paths,
                }
                for item in result.items
            ],
        },
        indent=2,
    )


def to_coverage_map_json(result: CheckResult) -> str:
    verdict = {
        Verdict.VERIFIED: "covered",
        Verdict.PARTIAL: "partial",
        Verdict.MISSING: "gap",
    }[result.verdict]
    payload = json.loads(to_json(result))
    payload.update(
        {
            "schema_version": "intent-verify.coverage-map.v1",
            "verdict": verdict,
            "decision": "inspect" if verdict != "covered" else "review",
        }
    )
    for item in payload["items"]:
        item["verdict"] = {
            "verified": "covered",
            "partial": "partial",
            "missing": "gap",
        }[item["verdict"]]
    return json.dumps(payload, indent=2)


def to_text(result: CheckResult) -> str:
    lines = [
        f"intent-verify: {Path(result.spec_path).name} vs "
        f"{result.repo_path} ({result.files_scanned} files)"
    ]
    for item in result.items:
        label = {
            Verdict.VERIFIED: "OK   ",
            Verdict.PARTIAL: "PART ",
            Verdict.MISSING: "LOW  ",
        }[item.verdict]
        lines.append(f"  [{label}{item.coverage:.0%}] {item.text}")
    if result.verdict is Verdict.MISSING:
        low_count = sum(1 for item in result.items if item.coverage < result.min_item)
        lines.append(
            f"intent-verify: MISSING — {low_count}/{len(result.items)} "
            f"items below {result.min_item:.0%} "
            f"(avg {result.average_coverage:.0%})"
        )
    elif result.verdict is Verdict.PARTIAL:
        lines.append(f"intent-verify: PARTIAL — avg coverage {result.average_coverage:.0%}")
    else:
        lines.append(f"intent-verify: VERIFIED — avg coverage {result.average_coverage:.0%}")
    return "\n".join(lines)
