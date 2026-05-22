# Agent Skill Format v0.1

Status: Draft  
Version: 0.1

## 1. Purpose

Agent Skill Format (ASF) defines a portable artifact format for agent skills.

ASF standardizes how a skill declares its identity, description, instruction entrypoint, and minimal execution composition. ASF does not define a standalone orchestrator. Existing agent harnesses remain responsible for activation, execution, hooks, state, tool permissions, and user interaction.

## 2. Design Goals

ASF v0.1 is designed to be:

- **Portable**: usable across agent harnesses that can read files and parse YAML frontmatter.
- **Inspectable**: understandable as plain text.
- **Small**: limited to fields that solve current skill-composition problems.
- **Host-owned**: execution state is owned by the host harness, not by the skill artifact.
- **Composable**: a skill can call another skill or local step documents without creating a separate workflow file.
- **Progressive**: hosts can support base skills first, then ASF execution fields later.

## 3. Non-Goals

ASF v0.1 does not define:

- a full workflow language
- a daemon or process model
- a package registry
- branching, retries, loops, or parallelism
- a canonical hook payload shared by all hosts
- a canonical storage engine
- direct mutation of host transcript/session files
- model-specific prompting strategy

## 4. Skill Artifact

An ASF skill is a directory containing a `SKILL.md` file.

```text
my-skill/
  SKILL.md
  001-first-step.md
  002-second-step.md
  references/
  scripts/
```

`SKILL.md` contains:

1. YAML frontmatter.
2. Markdown body.

The frontmatter is machine-readable. The Markdown body is agent-readable.

## 5. Base Frontmatter

The following fields are required:

```yaml
---
name: my-skill
description: Short activation-oriented description.
---
```

### 5.1 `name`

`name` is the local skill name.

Requirements:

- lowercase letters, numbers, and hyphens are recommended
- stable within the skill collection
- human-readable

### 5.2 `description`

`description` explains when the host should activate the skill.

Good descriptions are specific and activation-oriented. They should help the host decide whether the skill applies to a user request.

## 6. ASF Execution Extension

ASF v0.1 adds an optional `execution` object.

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

If `execution` is absent, the skill is a normal instruction skill. The host reads `SKILL.md` and follows its Markdown body.

If `execution.calls` is present, the host can treat the skill as a composed skill.

## 7. Calls

`execution.calls` is an ordered list.

Each call must be one of:

- a `skill` call
- a `step` call

### 7.1 Skill Call

A `skill` call invokes another skill by name.

```yaml
execution:
  calls:
    - skill: diagnosis
    - skill: code
```

The called skill owns its own internal execution declaration. A parent skill should not duplicate the child skill's steps.

### 7.2 Step Call

A `step` call points to a Markdown instruction file inside the same skill directory.

```yaml
execution:
  calls:
    - step: 001-capture-classify.md
    - step: 002-reference-check.md
```

The step file is agent-readable instruction content. In ASF v0.1, step files do not need their own frontmatter.

### 7.3 Order

The order of `execution.calls` is the execution order.

ASF v0.1 does not define separate `id` or `order` fields. The call path is derived from the parent skill name and the called `skill` or `step` value.

Example call path:

```json
["fix", "diagnosis", "001-capture-classify.md"]
```

## 8. User Interaction Hint

Step calls may declare `ask_user: true`.

```yaml
execution:
  calls:
    - step: 007-explain-confirm.md
      ask_user: true
```

Default:

```yaml
ask_user: false
```

Meaning:

- `ask_user: false`: the host should prefer uninterrupted execution through this step.
- `ask_user: true`: the host may allow the agent to stop and request user input at this step.

In ASF v0.1, `ask_user` is only defined on `step` calls. A `skill` call should not override the child skill's internal user-interaction policy.

## 9. Runtime Responsibility

ASF declarations have no enforcement power by themselves.

A host that enforces `execution.calls` must provide runtime behavior:

- parse `SKILL.md`
- resolve `skill` and `step` calls
- keep session-scoped execution state
- expose an explicit adapter or command that starts ASF execution for a named skill
- render the current instruction to the agent
- decide whether Stop is allowed
- decide whether user input interrupts or resumes the active skill
- avoid storing mutable runtime state inside the skill artifact

A host should not rely on a skill-read hook as its only activation mechanism. Different harnesses may read `SKILL.md` through internal loaders rather than a normal tool call.

A portable host adapter should accept a named target skill, normalize command-like names such as `/fix` to `fix`, verify that the target skill exists, verify that it declares runnable `execution.calls`, and only then start ASF execution.

A host may also provide a skill-read hook. When an agent reads a `*/SKILL.md` file that contains `execution.calls`, the hook can inject guidance that the skill is ASF-formatted and can be run through the host's ASF runtime interface. The hook should not start the runtime by itself.

## 10. Session-Scoped State

Runtime state must be scoped to the active agent session.

It should not be stored in:

- `SKILL.md`
- step Markdown files
- shared skill directories
- host transcript/session files owned by the harness

It may be stored in a sidecar state store owned by the ASF runtime or host adapter.

Recommended default roots:

```text
Claude Code: ~/.claude/state/asf/
Codex:       ~/.codex/state/asf/
OpenCode:    ~/.local/share/opencode/state/asf/
Custom:      user-configured path
```

Repo-bound coding workflows may use a worktree-local state path when the active task is scoped to a repository:

```text
<repo>/.workflow/state.json
```

This is useful when workflow artifacts are also stored in `.workflow/`. Non-repo skills should use a host-owned state root.

Minimal state snapshot:

```json
{
  "activeSkill": "fix",
  "currentPath": ["fix", "diagnosis", "001-capture-classify.md"],
  "status": "running",
  "stopPolicy": "block_until_step_complete"
}
```

This snapshot is intentionally small. ASF v0.1 does not require `runId`, `revision`, locking, event journals, or leases.

## 11. Hook Integration

ASF v0.1 expects hosts to map their native hook system onto ASF state.

The generic shape is:

```text
hook event
-> resolve state root from hook settings
-> resolve active session id from host event
-> load ASF session state
-> load current skill's SKILL.md
-> apply execution policy
-> allow, block, resume, or inject context
```

The hook setting should store the state root, not the state itself.

Example:

```json
{
  "asf": {
    "stateRoot": "~/.codex/state/asf"
  }
}
```

## 12. Compatibility

Hosts may support ASF at different levels:

- **Level 0**: read `SKILL.md` frontmatter and Markdown body.
- **Level 1**: parse `execution.calls`.
- **Level 2**: keep session-scoped state and render current calls.
- **Level 3**: enforce stop and user-interaction policy with hooks.

ASF v0.1 is useful at Level 1, but production workflow behavior requires Level 3.

## 13. Example

`feature/SKILL.md`:

```yaml
---
name: feature
description: Agreement-first feature development workflow.
execution:
  calls:
    - skill: agreement
    - skill: code
    - skill: ship
---
```

`agreement/SKILL.md`:

```yaml
---
name: agreement
description: Confirm specification, architecture, and E2E contract before coding.
execution:
  calls:
    - step: 001-specification.md
    - step: 002-system-architecture.md
    - step: 003-e2e-contract.md
    - step: 004-explain-confirm.md
      ask_user: true
---
```

## 14. Open Questions

ASF v0.1 leaves these unresolved:

- Should future versions add stable call IDs?
- Should future versions define output artifacts?
- Should `ask_user` become a richer gate type?
- Should hosts expose a common hook adapter contract?
- Should state move from snapshots to event journals?
- Should sub-skill calls be modeled as stack frames in a future runtime spec?

These are intentionally excluded from v0.1 to keep the first version implementable.
