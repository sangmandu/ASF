# Runtime State and Hooks

ASF separates skill declaration from runtime enforcement.

`SKILL.md` declares the skill. The host runtime manages the live state of a skill run.

## Principle

Runtime state is session-scoped.

It belongs to the active terminal or agent session because hooks execute in the context of that session. The same workspace can have multiple terminals, and the same skill files can be read by multiple sessions. Therefore the skill artifact cannot own mutable runtime state.

## State Root

The host hook configuration should define where ASF state is stored.

Recommended defaults:

```text
Claude Code: ~/.claude/state/asf/
Codex:       ~/.codex/state/asf/
OpenCode:    ~/.local/share/opencode/state/asf/
Custom:      user-configured path
```

The state root should be configurable.

## Why Not Store State in SKILL.md

`SKILL.md` is shared source material. It may be installed globally, committed to a repository, or reused by many terminals. Writing runtime state into it would mix source and execution state.

## Why Not Modify Host Session Files

Host transcript and session files are owned by the host harness. Their format may change, and direct mutation can break resume, import, or indexing behavior.

ASF runtimes should store sidecar state, not custom keys inside host-owned session files.

## Minimal Snapshot

ASF v0.1 uses a small snapshot shape:

```json
{
  "activeSkill": "fix",
  "currentPath": ["fix", "diagnosis", "001-capture-classify.md"],
  "status": "running",
  "stopPolicy": "block_until_step_complete"
}
```

Fields:

- `activeSkill`: root skill currently being managed.
- `currentPath`: nested skill/step path.
- `status`: current run status.
- `stopPolicy`: runtime hint used by Stop hooks.

## Hook Responsibilities

Hooks should:

- resolve the session
- load the session state
- read the relevant skill metadata
- decide whether to allow stop
- decide whether to allow user interruption
- inject resume instructions when useful

Hooks should not:

- store state in `SKILL.md`
- require workspace-global ownership
- mutate host transcript files
- assume all hosts expose the same hook payload

## Host Differences

Claude Code exposes session-oriented hook fields such as session identity and transcript path.

Codex stores thread and goal state in its own local state database. ASF should not write into that internal database. It should use a separate state root under `~/.codex/state/asf/`.

OpenCode has its own data directory conventions and can be configured differently. ASF should default to `~/.local/share/opencode/state/asf/` but allow override.

## Failure Behavior

If a host cannot resolve a stable session id, ASF enforcement should degrade gracefully.

Recommended fallback:

```text
no stable session id -> prompt-only mode or ephemeral state
```

Prompt-only mode means the skill can still be read, but hooks cannot reliably enforce stop/resume behavior.
