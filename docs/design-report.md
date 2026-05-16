# ASF v0.1 Design Report

This report explains the reasoning behind ASF v0.1, the current weaknesses, and the path to broader adoption.

## Executive Summary

ASF should standardize the skill artifact first.

It should not start as a workflow engine, a runtime protocol, or a new agent orchestrator. Existing harnesses such as Codex, Claude Code, and OpenCode already orchestrate agent work. ASF should give those harnesses a clearer skill artifact to read.

The correct boundary is:

```text
SKILL.md declares the skill.
Host hooks and session state enforce execution.
```

## Why YAML Frontmatter Plus Markdown

YAML frontmatter plus Markdown is a good foundation because it is already the emerging common shape of agent skills:

- `SKILL.md` is readable by humans and agents.
- YAML frontmatter gives hosts machine-readable metadata.
- Markdown body keeps procedural instructions easy to write.
- Files are easy to commit, review, diff, publish, and copy.
- The format can degrade gracefully in hosts that only understand plain Markdown.

The base shape is not enough for composed skills. Without execution metadata, the order of sub-skills and confirmation points gets hidden in prose. ASF v0.1 adds only the smallest missing piece: `execution.calls`.

## Why Not "Skill Flow"

"Flow" sounds like a runtime or orchestrator.

The current goal is not to create a new program that runs skills. The goal is to define the artifact format that lets existing harnesses manage skills more reliably.

Flow can emerge later from the standard. It should not be the name of the standard itself.

## Why `execution.calls`

`execution.calls` solves one immediate problem: composed skills need a machine-readable order.

Example:

```yaml
execution:
  calls:
    - skill: diagnosis
    - skill: code
```

This is better than prose because a host can parse it. It is better than a separate `flow.json` because it avoids a second source of truth.

ASF v0.1 keeps the model narrow:

- `skill` calls invoke another skill.
- `step` calls invoke a local Markdown step file.
- order is list order.
- `ask_user` is an optional step-level hint.

## Why Runtime State Is Separate

Mutable runtime state cannot live in the skill file.

The same skill may be used by many sessions. A shared `SKILL.md` should not say which terminal is currently running which step.

Mutable runtime state also should not be inserted into host-owned transcript files. Those files are private implementation details of the harness.

ASF therefore recommends sidecar state owned by the host or ASF runtime adapter:

```text
Claude Code: ~/.claude/state/asf/
Codex:       ~/.codex/state/asf/
OpenCode:    ~/.local/share/opencode/state/asf/
Custom:      user-configured path
```

## Current Implementation Risk

A workflow-like skill implementation is not production-ready just because it has Markdown steps and a state file.

The main risks to avoid are:

- duplicate truth between `SKILL.md` and separate workflow JSON
- state stored at workspace scope when the real owner is the agent session
- hooks mutating ad hoc state without a clear runtime contract
- step completion based only on agent self-report
- user confirmation hidden in prose
- file paths treated as forever-stable public IDs before that tradeoff is proven

ASF v0.1 deliberately avoids over-solving these. It defines the artifact contract and leaves stronger runtime semantics to later reference implementations.

## What Would Make ASF Stronger

The biggest improvements after v0.1 are:

1. Conformance tests for valid and invalid `SKILL.md` frontmatter.
2. A reference parser for `execution.calls`.
3. A reference hook adapter for one host.
4. Typed user gates that are richer than `ask_user: true`.
5. Optional output artifact contracts.
6. A session-state event journal for crash recovery.
7. A compatibility matrix across Codex, Claude Code, OpenCode, Cursor, and other hosts.

## README Plan

The GitHub README should be short and example-first.

Recommended first screen:

1. One-sentence definition.
2. One-sentence boundary: ASF is not a runtime.
3. Minimal `SKILL.md` example.
4. Link to the v0.1 spec.

Readers should understand in under one minute that ASF is a file format proposal for portable agent skills.

## Adoption Plan

The adoption path should be staged.

### Stage 1: Publish the Draft

Publish this repo as a clear v0.1 draft. Avoid claiming official standard status.

### Stage 2: Collect Review

Ask skill authors and agent-tool maintainers to review four questions:

- Is `execution.calls` clear?
- Is `skill` versus `step` clear?
- Is `ask_user` useful enough for v0.1?
- Is session-scoped state the right runtime ownership model?

### Stage 3: Build a Reference Parser

Create a tiny parser and validator. It should reject invalid frontmatter and print useful diagnostics.

### Stage 4: Build One Host Adapter

Start with one host. Prove the hook/state model works before claiming cross-host runtime behavior.

### Stage 5: Publish Examples

Publish examples for common workflows:

- fix
- feature
- ship
- research
- document editing

### Stage 6: Write Public Explanation

Suggested article title:

> Agent Skill Format: a small execution extension for SKILL.md

Suggested message:

- Agent skills are becoming portable Markdown artifacts.
- Basic metadata is not enough for composed skills.
- ASF adds a minimal execution declaration.
- Runtime state remains host-owned.

## References

- Claude Code Skills: https://code.claude.com/docs/en/skills
- Claude Code Hooks: https://code.claude.com/docs/en/hooks
- Claude Code Goal: https://code.claude.com/docs/en/goal
- OpenCode Skills: https://opencode.ai/docs/skills
- AG-UI Events: https://docs.ag-ui.com/concepts/events
