# Agent Skill Format

Agent Skill Format (ASF) is a portable YAML + Markdown format for defining agent skills.

ASF standardizes the skill artifact, not the agent runtime. A skill can declare what it is, when it should be used, and how its instruction files compose. The host harness, such as Codex, Claude Code, OpenCode, Cursor, or another agent runtime, remains responsible for discovery, execution, hooks, session state, permissions, and tool enforcement.

## Why ASF

Agent skills are converging on a simple shape:

- a directory per skill
- a `SKILL.md` entry file
- YAML frontmatter for machine-readable metadata
- Markdown body for agent-readable instructions
- optional local files such as step documents, scripts, templates, and references

That shape is good because it is inspectable, editable, versionable, and easy for many agent harnesses to load. The gap is that basic `name` and `description` metadata is not enough to express multi-step skills, sub-skill composition, or user-confirmation gates without hiding critical behavior in prose.

ASF v0.1 fills that gap with a small execution declaration:

```yaml
---
name: fix
description: Diagnosis-first bug fix workflow.
execution:
  calls:
    - skill: diagnosis
    - skill: code
---
```

ASF does not make this declaration powerful by itself. The power comes from a host harness or reference runtime that reads ASF metadata, keeps session-scoped state, and uses hooks to block, resume, or inject instructions at the right time.

## What ASF Is Not

ASF is not a workflow engine, daemon, package manager, or replacement for existing agent harnesses.

It does not require a new orchestrator process. The host agent remains the orchestrator. ASF gives that host a clearer contract for reading and managing skills.

## v0.1 Scope

ASF v0.1 defines:

- the `SKILL.md` artifact boundary
- required base metadata
- the `execution.calls` extension
- `skill` calls versus `step` calls
- `ask_user` as a minimal user-interaction hint
- session-scoped runtime state as a host responsibility
- recommended state roots for common harnesses

ASF v0.1 intentionally does not define:

- a full workflow DSL
- branch, retry, parallel, or conditional execution
- a canonical database format
- a universal hook payload
- package distribution
- tool permission enforcement

See [spec/asf-v0.1.md](spec/asf-v0.1.md) for the draft specification.

## Minimal Example

```text
fix/
  SKILL.md
diagnosis/
  SKILL.md
  001-capture-classify.md
  002-reference-check.md
  007-explain-confirm.md
code/
  SKILL.md
```

`fix/SKILL.md`:

```yaml
---
name: fix
description: Diagnosis-first fix workflow.
execution:
  calls:
    - skill: diagnosis
    - skill: code
---
```

`diagnosis/SKILL.md`:

```yaml
---
name: diagnosis
description: Evidence-first diagnosis workflow.
execution:
  calls:
    - step: 001-capture-classify.md
    - step: 002-reference-check.md
    - step: 007-explain-confirm.md
      ask_user: true
---
```

## Runtime Model

ASF state should be scoped to the active agent session, not to the skill file and not only to the workspace.

Recommended default state roots:

```text
Claude Code: ~/.claude/state/asf/
Codex:       ~/.codex/state/asf/
OpenCode:    ~/.local/share/opencode/state/asf/
Custom:      user-configured path
```

For repo-bound coding workflows, a host may store state in the active worktree instead:

```text
<repo>/.workflow/state.json
```

This keeps workflow state next to workflow artifacts such as specs, reproduction notes, and test results. Non-repo skills should use the host-owned state roots above.

The runtime state belongs next to the host harness, not inside `SKILL.md`. A simple v0.1 state snapshot can be as small as:

```json
{
  "activeSkill": "fix",
  "currentPath": ["fix", "diagnosis", "001-capture-classify.md"],
  "status": "running",
  "stopPolicy": "block_until_step_complete"
}
```

See [docs/runtime-state.md](docs/runtime-state.md) for the runtime-state design.

## Reference Runtime

ASF includes a small reference runtime in [`runtime/`](runtime/):

```bash
ASF_SKILLS_ROOT=/path/to/skills bash runtime/asf-run.sh init fix "Fix the bug"
```

The runtime reads `execution.calls` from `SKILL.md`, expands nested skill calls into ordered step calls, prints the current step, and records progress in `.workflow/state.json` when run inside a Git worktree.

ASF also includes a `Read */SKILL.md` hook helper. The hook does not start execution. It only tells the agent that the read skill is ASF-formatted and shows the standard runtime command to use when the user requested that skill.

## Documents

- [ASF v0.1 Specification](spec/asf-v0.1.md)
- [Runtime State and Hooks](docs/runtime-state.md)
- [Design Report](docs/design-report.md)
- [Weaknesses and Roadmap](docs/gaps-and-roadmap.md)
- [README and Adoption Strategy](docs/readme-and-adoption.md)
- [Reference Runtime](runtime/)
- [Examples](examples/)

## Status

ASF is an early v0.1 draft. It is designed to be small enough to implement in existing harnesses and strict enough to avoid hiding execution order in prose.

## License

MIT
