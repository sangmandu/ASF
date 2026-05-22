# ASF Reference Runtime

This directory contains a small shell/Python reference runtime for ASF v0.1.

It is intentionally narrow:

- reads `SKILL.md` frontmatter
- supports `execution.calls`
- expands nested `skill` calls into ordered `step` calls
- honors `ask_user: true` as a user-confirmation stop hint
- stores repo-bound workflow state in `.workflow/state.json`
- stores non-repo state under `~/.codex/state/asf/`
- provides a `Read */SKILL.md` hook helper that tells the agent when a skill is ASF-formatted and how to start the runtime

Skills do not depend on this runtime. A host or agent can still read `SKILL.md` and follow the Markdown instructions manually. The runtime does not know what a skill means; it only expands ASF calls, tracks the current step, and prints step files.

## Skill Read Hook

`asf-skill-read-hook.py` is intended for `PreToolUse` hooks on the `Read` tool. It does not start the runtime. It only injects guidance when the agent reads a `*/SKILL.md` file whose frontmatter contains `execution.calls`.

The guidance tells the agent to use `asf-run.sh init <skill> "<task>"` by default when the user requested that skill, unless the user explicitly asked for manual execution.

## Usage

```bash
ASF_SKILLS_ROOT=/path/to/skills bash runtime/asf-run.sh init fix "Fix the bug"
```

Continue a step:

```bash
bash runtime/asf-run.sh complete DIAGNOSIS_001_CAPTURE_CLASSIFY
```

## State Policy

When the runtime is launched inside a Git worktree, state is stored in:

```text
<repo>/.workflow/state.json
```

Outside a Git worktree, state is stored in a host-owned Codex location:

```text
~/.codex/state/asf/<workspace-hash>/<skill>.json
```

Workflow artifacts are still skill-defined. The runtime only manages step state.
