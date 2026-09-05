from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .models import Verdict
from .report import run_check, to_coverage_map_json, to_json, to_text


def add_check_arguments(parser: argparse.ArgumentParser, *, coverage_map: bool = False) -> None:
    parser.add_argument(
        "--spec",
        required=True,
        help="path to markdown spec, intent, or handoff file",
    )
    parser.add_argument("--repo", required=True, help="path to repo or source tree to scan")
    parser.add_argument(
        "--evidence-path",
        action="append",
        required=coverage_map,
        help=(
            "repo-relative implementation file or directory to scan; repeat for multiple roots"
        ),
    )
    parser.add_argument(
        "--section",
        help="optional markdown heading to target, for example Requirements",
    )
    if not coverage_map:
        parser.add_argument("--json", action="store_true", help="emit machine-readable JSON output")
    parser.add_argument(
        "--min-verified",
        type=float,
        default=0.7,
        help="coverage threshold an item must clear to count as verified",
    )
    parser.add_argument(
        "--min-item",
        type=float,
        default=0.3,
        help="minimum per-item threshold before the result becomes missing",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="intent-verify",
        description="Check a markdown spec or handoff doc against a repo to catch spec drift.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser(
        "check",
        help="run repo intent verification against a markdown spec",
    )
    add_check_arguments(check)

    coverage_map = subparsers.add_parser(
        "map",
        help="map spec items to explicit implementation evidence for advisory orchestration",
        description=(
            "Map lexical spec coverage to explicit implementation paths. A covered result "
            "supports review but never authorizes acceptance, merge, or release."
        ),
    )
    add_check_arguments(coverage_map, coverage_map=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    spec_path = Path(args.spec)
    repo_path = Path(args.repo).resolve()
    if not spec_path.exists():
        print(f"intent-verify: spec not found: {spec_path}", file=sys.stderr)
        return 2
    if not spec_path.is_file():
        print(f"intent-verify: spec path is not a file: {spec_path}", file=sys.stderr)
        return 2
    if not repo_path.exists() or not repo_path.is_dir():
        print(f"intent-verify: repo path is not a directory: {repo_path}", file=sys.stderr)
        return 2
    if not 0 < args.min_item <= args.min_verified <= 1:
        print(
            "intent-verify: thresholds must satisfy 0 < min-item <= min-verified <= 1",
            file=sys.stderr,
        )
        return 2

    evidence_paths: list[Path] | None = None
    if args.evidence_path:
        evidence_paths = []
        for raw_path in args.evidence_path:
            candidate = (repo_path / raw_path).resolve()
            try:
                candidate.relative_to(repo_path)
            except ValueError:
                print(
                    f"intent-verify: evidence path escapes repo: {raw_path}",
                    file=sys.stderr,
                )
                return 2
            if not candidate.exists():
                print(
                    f"intent-verify: evidence path not found: {raw_path}",
                    file=sys.stderr,
                )
                return 2
            evidence_paths.append(candidate)

    result = run_check(
        spec_path,
        repo_path,
        section=args.section,
        min_verified=args.min_verified,
        min_item=args.min_item,
        evidence_paths=evidence_paths,
    )
    if args.command == "map":
        print(to_coverage_map_json(result))
    else:
        print(to_json(result) if args.json else to_text(result))
    return {
        Verdict.VERIFIED: 0,
        Verdict.PARTIAL: 1,
        Verdict.MISSING: 2,
    }[result.verdict]


if __name__ == "__main__":
    raise SystemExit(main())
