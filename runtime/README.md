# ASF Reference Runtime

This directory contains a small shell/Python reference runtime for ASF v0.1.

It is intentionally narrow:

- reads `SKILL.md` frontmatter
- supports `execution.calls`
- expands nested `skill` calls into ordered `step` calls
- honors `ask_user: true` as a user-confirmation stop hint
- stores repo-bound workflow state in `.workflow/state.json`
- stores non-repo state under `~/.codex/state/asf/`

Skills do not depend on this runtime. A host or agent can still read `SKILL.md` and follow the Markdown instructions manually. The runtime does not know what a skill means; it only expands ASF calls, tracks the current step, and prints step files.

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
