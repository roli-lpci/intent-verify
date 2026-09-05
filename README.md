# intent-verify

[![CI](https://github.com/hermes-labs-ai/intent-verify/actions/workflows/ci.yml/badge.svg)](https://github.com/hermes-labs-ai/intent-verify/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/intent-verify.svg)](https://pypi.org/project/intent-verify/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

intent-verify is a deterministic, zero-LLM coverage mapper for markdown specs,
`INTENT.md` files, and handoff documents. Its orchestration contract maps each
acceptance item to explicit implementation files and returns `covered`,
`partial`, or `gap` with provenance.

Use it after code changes and before review when you need to see whether stated
scope is visibly represented in the exact source and test roots you name. A gap
can stop a claim that scope is covered. A covered result sends work to review;
it never authorizes acceptance, merge, or release.

## How it works

intent-verify is intentionally simple and fully deterministic — no model, no network:

1. Parse acceptance items from the spec (inline `Accepts:`/`Requirements:`/`Scope:` lines and bullet/numbered lists under matching headings).
2. Tokenize each item, dropping common stop words.
3. For each item, compute the fraction of its tokens that appear as substrings in the selected evidence files (the spec file itself is excluded).
4. Score each item against two thresholds and roll up to a single verdict.

Coverage is a lexical token-overlap signal, not a semantic judgment.

## Orchestration coverage map

Name implementation evidence explicitly. This prevents a matching README
elsewhere in the repository from satisfying the map:

```bash
intent-verify map \
  --spec INTENT.md \
  --repo . \
  --evidence-path src \
  --evidence-path tests
```

The command emits only JSON using the versioned
`intent-verify.coverage-map.v1` contract. Each item includes the files that
contributed matching terms. The top-level `acceptance_authority` is always
`false`; `decision` is `review` for covered scope and `inspect` for partial or
gap results.

| Map verdict | Exit | Orchestration meaning |
| --- | ---: | --- |
| `covered` | `0` | Continue to tests and review; do not accept automatically. |
| `partial` | `1` | Inspect the weak items before claiming scope coverage. |
| `gap` | `2` | Stop the scope-covered claim and inspect missing evidence. |

For Hermes Cloud Lane packets, pass the map command through the existing
`--verify` field. This keeps the signal post-change and explicit instead of
turning it into an always-on hook.

### GitHub Action

The root composite Action applies the same contract. After an immutable `v1`
release, a workflow can use:

```yaml
- name: Map intent to changed implementation surfaces
  uses: hermes-labs-ai/intent-verify@v1
  with:
    spec: INTENT.md
    repo: .
    evidence-paths: |
      src
      tests
```

Pin the full release commit when your supply-chain policy requires it. Upload
the path returned by the Action's `receipt` output when the JSON should remain
as a build artifact.

## Install

```bash
pip install intent-verify
```

For local development:

```bash
pip install -e ".[dev]"
```

## 60-second quickstart

Given a spec like:

```markdown
# Intent

## Accepts
- uploads PDF invoices
- retries provider timeout
```

run:

```bash
intent-verify check --spec INTENT.md --repo .
```

You get a per-item breakdown and a single verdict:

```text
intent-verify: INTENT.md vs . (12 files)
  [OK   100%] uploads PDF invoices
  [PART  50%] retries provider timeout
  [LOW   20%] writes audit log for rejected invoices
intent-verify: MISSING — 1/3 items below 30% (avg 57%)
```

(The file count, percentages, and items above are illustrative — your numbers depend on your spec and repo.)

The exit code mirrors the verdict, so it drops straight into CI or a pre-commit hook:

| Verdict | Meaning | Exit code |
| --- | --- | --- |
| `verified` | every parsed item cleared the verified threshold | `0` |
| `partial` | at least one item is only partly covered | `1` |
| `missing` | at least one item fell below the per-item minimum | `2` |

![intent-verify preview](assets/preview.png)

## Usage

```bash
intent-verify check --spec INTENT.md --repo .
intent-verify check --spec SPEC.md --repo . --json
intent-verify check --spec docs/handoff.md --repo src --min-verified 0.75 --min-item 0.35
```

Flags:

- `--spec` — path to the markdown spec, intent, or handoff file (required).
- `--repo` — path to the repo or source tree to scan (required).
- `--section` — target a specific markdown heading, for example `Requirements`.
- `--json` — emit machine-readable JSON instead of text.
- `--min-verified` — coverage an item must clear to count as verified (default `0.7`).
- `--min-item` — minimum per-item coverage before an item is treated as missing (default `0.3`).

### What it parses

By default it extracts items from:

- inline lines such as `Accepts: upload PDF invoices, retry on timeout`
- markdown sections such as `## Accepts` with bullet or numbered items (`Accepts`, `Requirements`, `Scope` headings, or a custom one via `--section`)

### JSON output

```bash
intent-verify check --spec INTENT.md --repo . --json
```

The JSON object includes `spec_path`, `repo_path`, `files_scanned`,
`average_coverage`, `verdict`, the thresholds used, and an `items[]` array with
each item's parsed text, tokens, coverage, verdict, and contributing evidence
paths. Legacy `check` output remains compatible and now includes the explicit
non-authority metadata.

## Limitations / what it does NOT do

- **Not runtime agent intent verification.** It does not authorize or monitor AI-agent actions, MCP/tool calls, or permissions; it checks static repository source against a markdown spec.
- **Lexical, not semantic.** It matches tokens as substrings; it does not understand meaning, control flow, or behavior.
- **It can over-credit.** A token appearing anywhere in any scanned file counts, even if it is in a comment, a string, or an unrelated context.
- **It can under-credit.** A correct implementation written with different vocabulary than the spec will score low.
- **It is not proof of correctness** and does not replace tests or code review. It answers "does the implementation visibly cover the stated scope?" — not "is the software correct?"
- **It needs a human-readable spec.** With no `INTENT.md`/`SPEC.md`/requirements/handoff file there is nothing to check against.
- **Source-file scope only.** It scans a fixed set of source extensions (Python, JS/TS, Go, Rust, shell, config, markdown, etc.) and skips common build/vendor directories.
- **Evidence paths are not behavioral proof.** `map` prevents unrelated paths
  from contributing, but comments, docstrings, and dead code inside selected
  paths can still match. Tests and review remain authoritative.

## Development

```bash
ruff check .
python3 -m pytest -q
python3 -m py_compile src/intent_verify/*.py
```

## Repository layout

```text
src/intent_verify/
tests/
examples/
```

---

Part of the [Hermes Labs reliability stack](https://github.com/hermes-labs-ai). Complementary siblings, not duplicates: [rule-audit](https://github.com/hermes-labs-ai/rule-audit) analyzes logical contradictions in system prompts, and [lintlang](https://github.com/hermes-labs-ai/lintlang) lints agent-config structure — intent-verify instead checks spec-vs-code drift.

## About Hermes Labs

[Hermes Labs](https://hermes-labs.ai) is an AI reliability engineering studio for product and engineering teams shipping production agents and LLM applications. We find the structural AI failures standard evals miss, then harden retrieval, memory, agents, and the language layers around production AI systems with runtime controls and defensible evidence.

Browse the [open-source catalog](https://hermes-labs.ai/open-source) or contact [roli@hermes-labs.ai](mailto:roli@hermes-labs.ai).
