# ASF Reference Runtime

This directory contains a small shell/Python reference runtime for ASF v0.1.

It is intentionally narrow:

- reads `SKILL.md` frontmatter
- supports `execution.calls`
- expands nested `skill` calls into ordered `step` calls
- honors `ask_user: true` as a user-confirmation stop hint
- stores repo-bound workflow state in `.workflow/state.json`
- stores non-repo state under `~/.codex/state/asf/`
- provides an optional `Read */SKILL.md` hook helper for hosts whose normal file-read tool supports hooks

Skills do not depend on this runtime. A host or agent can still read `SKILL.md` and follow the Markdown instructions manually. The runtime does not know what a skill means; it only expands ASF calls, tracks the current step, and prints step files.

## Explicit Adapter

The portable entrypoint is an explicit adapter such as `/asf <skill> <task>`.

The adapter should:

1. normalize the target skill name, so `fix` and `/fix` resolve to the same skill;
2. run `asf-run.sh inspect <skill>`;
3. report whether the skill exists and is ASF-runnable;
4. call `asf-run.sh init <skill> "<task>"` only when `inspect` returns `executable: true`.

This avoids depending on harness-specific `Read` tool behavior. Some hosts read `SKILL.md` through an internal skill loader that does not trigger normal tool hooks.

## Skill Read Hook

`asf-skill-read-hook.py` is optional. It is intended only for `PreToolUse` hooks on hosts where `SKILL.md` reads go through a normal `Read` tool. It does not start the runtime. It only injects guidance when the agent reads a `*/SKILL.md` file whose frontmatter contains `execution.calls`.

Do not treat this hook as the portable ASF activation mechanism. Prefer an explicit adapter command or skill.

## Usage

```bash
ASF_SKILLS_ROOT=/path/to/skills bash runtime/asf-run.sh init fix "Fix the bug"
```

Inspect a target before starting:

```bash
ASF_SKILLS_ROOT=/path/to/skills bash runtime/asf-run.sh inspect fix
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
