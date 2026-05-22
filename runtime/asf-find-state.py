#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


def candidate_paths(payload: object) -> list[str]:
    paths: list[str] = []
    if isinstance(payload, dict):
        for key in ("cwd", "workingDirectory", "workspaceRoot"):
            value = payload.get(key)
            if isinstance(value, str):
                paths.append(value)
        for value in payload.values():
            if isinstance(value, (dict, list)):
                paths.extend(candidate_paths(value))
    elif isinstance(payload, list):
        for value in payload:
            paths.extend(candidate_paths(value))
    return paths


def running_state(path: Path) -> bool:
    try:
        state = json.loads(path.read_text())
    except Exception:
        return False
    return state.get("control", {}).get("runtime") == "asf" and state.get("control", {}).get("status") == "running"


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}

    seen: set[Path] = set()
    for base in [os.getcwd(), *candidate_paths(payload)]:
        if not base:
            continue
        path = Path(base).resolve()
        while True:
            state = path / ".workflow" / "state.json"
            if state not in seen and state.exists() and running_state(state):
                print(state)
                return 0
            seen.add(state)
            if path.parent == path:
                break
            path = path.parent

    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    state_root = codex_home / "state" / "asf"
    if state_root.exists():
        candidates = sorted(state_root.glob("**/*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for state in candidates:
            if running_state(state):
                print(state)
                return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
