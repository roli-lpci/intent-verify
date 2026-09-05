# AGENTS.md

## What this tool does

- Checks a markdown spec or intent document against a repo.
- Extracts acceptance items from the spec.
- Scans the repo for lexical evidence of those items.
- Returns one of: `verified`, `partial`, `missing`.

## When to use it

- Post-change advisory mapping from stated scope to explicit source/test roots
- Repo intent verification
- Spec drift checks
- Handoff verification
- CI guardrail before merge or release

## When not to use it

- Do not install it as an always-on or per-turn orchestration hook.
- Do not let `covered` authorize acceptance, merge, release, or a public effect.
- Do not use it as proof of correctness.
- Do not use it when there is no markdown spec file.
- Do not use it when you need semantic analysis rather than lexical coverage.

## Minimal invocation

```bash
intent-verify map --spec INTENT.md --repo . --evidence-path src --evidence-path tests
intent-verify check --spec INTENT.md --repo .
intent-verify check --spec SPEC.md --repo . --json
```

## Expected output shape

Coverage-map JSON:

- `schema_version: intent-verify.coverage-map.v1`
- `signal_kind: lexical_scope_coverage`
- `acceptance_authority: false`
- `evidence_roots[]`
- `decision: review|inspect`
- `items[].evidence_paths[]`

Text mode:

- one header line with spec path, repo path, files scanned
- one line per item with `OK`, `PART`, or `LOW`
- one summary verdict line

JSON mode:

- `spec_path`
- `repo_path`
- `files_scanned`
- `average_coverage`
- `verdict`
- `thresholds`
- `items[]`

## Known limitations

- lexical only
- may over-credit token overlap
- may under-credit different wording

## Common failure cases

- spec file path is wrong
- repo path is wrong
- thresholds are invalid
- spec language is too abstract for lexical matching
- the only matching text is inside the spec itself, not the implementation

## What counts as success

- `map` `covered` (exit 0) permits review, not acceptance.
- `map` `partial` or `gap` (exit 1 or 2) blocks only a claim that scope is covered.
- A documentation-only match outside the named evidence paths must not pass.

- `verified` (exit code 0) means every parsed item cleared the verified threshold
- `partial` (exit code 1) means at least one item is only partly covered
- `missing` (exit code 2) means at least one item fell below the minimum per-item threshold

## Where this fits

Part of the Hermes Labs reliability stack: https://github.com/hermes-labs-ai
