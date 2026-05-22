#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path


def find_path(value):
    if isinstance(value, dict):
        for key in ("file_path", "path", "absolute_file_path"):
            found = value.get(key)
            if isinstance(found, str):
                return found
        for item in value.values():
            found = find_path(item)
            if found:
                return found
    if isinstance(value, str):
        try:
            return find_path(json.loads(value))
        except Exception:
            return None
    return None


def extract_frontmatter(path: Path) -> list[str] | None:
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:index]
    return None


def parse_asf_skill(path: Path) -> tuple[str, bool]:
    lines = extract_frontmatter(path)
    if lines is None:
        return path.parent.name, False

    skill_name = path.parent.name
    has_execution = False
    has_calls = False
    for raw in lines:
        stripped = raw.strip()
        if re.match(r"^name:\s*", stripped):
            skill_name = stripped.split(":", 1)[1].strip().strip("'\"") or skill_name
        if stripped == "execution:":
            has_execution = True
        if stripped == "calls:":
            has_calls = True
    return skill_name, has_execution and has_calls


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0

    tool_name = str(payload.get("tool_name") or payload.get("toolName") or "")
    if tool_name.lower() != "read":
        return 0

    raw_path = find_path(payload.get("tool_input") or payload.get("toolInput") or payload)
    if not raw_path:
        return 0

    path = Path(raw_path).expanduser()
    if path.name != "SKILL.md":
        return 0

    skill_name, is_asf = parse_asf_skill(path)
    if not is_asf:
        return 0

    runtime = Path(__file__).resolve().with_name("asf-run.sh")
    context = f"""ASF skill detected.

The file just read is an ASF-formatted skill: `{skill_name}`.

If the user asked you to use this skill, or you are beginning work under this skill, use the ASF runtime by default unless the user explicitly requested manual execution:

```bash
bash {runtime} init {skill_name} "<user task>"
```

Then follow the printed step instructions exactly. Do not skip steps.

If the runtime is unavailable, follow this skill's `execution.calls` manually from `SKILL.md`.

Do not start the runtime merely because you are inspecting this skill file; start it only when it matches the user's requested work."""

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": context,
                },
                "systemMessage": f"ASF skill detected: {skill_name}",
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
