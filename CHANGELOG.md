# Changelog

## 0.2.0 - 2026-09-05

- Added the advisory `intent-verify map` contract for orchestration and CI.
- Required explicit implementation evidence paths for coverage maps, preventing
  unrelated repository documentation from satisfying the signal by default.
- Added per-item evidence paths, a versioned JSON schema identifier, and an
  explicit `acceptance_authority: false` boundary.
- Added a root composite GitHub Action with covered, partial, and
  documentation-only gap fixtures.

## 0.1.2 - 2026-08-04

- Clarified the README and the boundary between lexical coverage and semantic
  verification without changing checker behavior.
- Added canonical package links and modernized license metadata.
- Added a tag-bound OIDC Trusted Publishing workflow for PyPI.

## 0.1.1 - 2026-05-30

- Added citation and Zenodo metadata.
- Aligned the public repository and Hermes Labs identity surfaces.

## 0.1.0

- Initial public release.
- Added markdown spec parsing for inline and section-style acceptance items.
- Added deterministic lexical coverage scoring.
- Added CLI output in text and JSON modes.
- Added fixture-based tests and CI examples.
