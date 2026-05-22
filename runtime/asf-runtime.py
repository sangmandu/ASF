#!/usr/bin/env python3
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def fail(message: str, code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root(cwd: Path) -> Path | None:
    try:
        output = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(cwd),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return None
    return Path(output).resolve() if output else None


def default_state_path(skill: str, cwd: Path) -> Path:
    root = repo_root(cwd)
    if root is not None:
        return root / ".workflow" / "state.json"

    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    digest = hashlib.sha256(str(cwd.resolve()).encode("utf-8")).hexdigest()[:16]
    return codex_home / "state" / "asf" / digest / f"{skill}.json"


def skills_root() -> Path:
    env_root = os.environ.get("ASF_SKILLS_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    runtime_dir = Path(__file__).resolve().parent
    candidate = (runtime_dir / ".." / "skills").resolve()
    if candidate.exists():
        return candidate

    candidate = (runtime_dir / ".." / "examples").resolve()
    if candidate.exists():
        return candidate

    fail("ASF_SKILLS_ROOT is not set and no sibling skills/examples directory exists")


def extract_frontmatter(path: Path) -> list[str]:
    text = path.read_text()
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        fail(f"missing YAML frontmatter: {path}")

    end = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = index
            break
    if end is None:
        fail(f"unterminated YAML frontmatter: {path}")
    return lines[1:end]


def parse_skill(path: Path) -> dict:
    lines = extract_frontmatter(path)
    data: dict[str, object] = {"calls": []}
    calls: list[dict[str, object]] = []

    in_calls = False
    current_call: dict[str, object] | None = None
    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            continue

        if re.match(r"^name:\s*", stripped):
            data["name"] = stripped.split(":", 1)[1].strip().strip("'\"")
            continue

        if stripped.startswith("execution:") and stripped != "execution:":
            fail(f"unsupported inline execution declaration in {path}: {stripped}")

        if stripped == "execution:":
            continue

        if stripped.startswith("calls:") and stripped != "calls:":
            fail(f"unsupported inline calls declaration in {path}: {stripped}")

        if stripped == "calls:":
            in_calls = True
            continue

        if not in_calls:
            continue

        match = re.match(r"^-\s+(skill|step):\s*(.+)$", stripped)
        if match:
            current_call = {match.group(1): match.group(2).strip().strip("'\"")}
            calls.append(current_call)
            continue

        if current_call is not None:
            ask_match = re.match(r"^ask_user:\s*(true|false)$", stripped, re.IGNORECASE)
            if ask_match:
                current_call["ask_user"] = ask_match.group(1).lower() == "true"
                continue

    data["calls"] = calls
    return data


def step_key(skill: str, step_file: str, used: set[str]) -> str:
    stem = Path(step_file).stem
    raw = f"{skill}_{stem}"
    key = re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_").upper()
    if not key:
        key = "STEP"
    base = key
    suffix = 2
    while key in used:
        key = f"{base}_{suffix}"
        suffix += 1
    used.add(key)
    return key


def flatten_skill(root: Path, skill: str, used: set[str] | None = None) -> list[dict]:
    skill = normalize_skill_name(skill)
    used = used if used is not None else set()
    skill_path = root / skill / "SKILL.md"
    if not skill_path.exists():
        fail(f"skill not found: {skill_path}")

    parsed = parse_skill(skill_path)
    calls = parsed.get("calls", [])
    if not calls:
        return []

    steps: list[dict] = []
    for call in calls:
        if "skill" in call:
            steps.extend(flatten_skill(root, str(call["skill"]), used))
        elif "step" in call:
            file_name = str(call["step"])
            step_path = root / skill / file_name
            if not step_path.exists():
                fail(f"step file not found: {step_path}")
            key = step_key(skill, file_name, used)
            steps.append(
                {
                    "key": key,
                    "skill": skill,
                    "file": f"{skill}/{file_name}",
                    "mode": "user_confirmation" if call.get("ask_user") is True else "automatic",
                }
            )
        else:
            fail(f"invalid execution call in {skill_path}: {call}")
    return steps


def normalize_skill_name(value: str) -> str:
    name = value.strip().lstrip("/")
    if not name:
        fail("missing skill name")
    if "/" in name or "\\" in name:
        fail(f"invalid skill name: {value}")
    return name


def load_state(path: Path) -> dict:
    return json.loads(path.read_text())


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n")


def state_path_from_args(skill: str | None = None) -> Path:
    env_path = os.environ.get("ASF_STATE")
    if env_path:
        return Path(env_path).expanduser().resolve()
    return default_state_path(skill or "asf", Path.cwd())


def init(skill: str, task_description: str) -> None:
    skill = normalize_skill_name(skill)
    root = skills_root()
    steps = flatten_skill(root, skill)
    if not steps:
        fail(f"skill has no execution steps: {skill}")

    state_path = state_path_from_args(skill)
    timestamp = now()
    step_state = {
        item["key"]: {
            "status": "running" if index == 0 else "pending",
            "mode": item["mode"],
            "skill": item["skill"],
            "file": item["file"],
        }
        for index, item in enumerate(steps)
    }

    state = {
        "control": {
            "runtime": "asf",
            "runtime_version": "0.1",
            "workflow_id": str(uuid4()),
            "workflow": skill,
            "status": "running",
            "current_step": steps[0]["key"],
            "order": [item["key"] for item in steps],
            "interrupted": False,
            "interrupt_reason": "",
            "steps": step_state,
            "created_at": timestamp,
            "updated_at": timestamp,
        },
        "runtime": {
            "skills_root": str(root),
            "workspace": str(Path.cwd().resolve()),
            "state_path": str(state_path),
        },
        "data": {
            "task_description": task_description,
        },
    }
    save_state(state_path, state)
    print_current(state_path, "Follow the instructions below exactly.")


def inspect(skill: str) -> None:
    skill = normalize_skill_name(skill)
    root = skills_root()
    skill_path = root / skill / "SKILL.md"
    run_sh = Path(__file__).resolve().with_name("asf-run.sh")
    result = {
        "skill": skill,
        "skillPath": str(skill_path),
        "exists": skill_path.exists(),
        "asf": False,
        "executable": False,
        "reason": "",
        "runtimeCommand": f'bash {run_sh} init {skill} "<task>"',
    }

    if not skill_path.exists():
        result["reason"] = "skill not found"
        print(json.dumps(result, indent=2))
        return

    parsed = parse_skill(skill_path)
    calls = parsed.get("calls", [])
    result["asf"] = bool(calls)
    if not calls:
        result["reason"] = "SKILL.md does not declare execution.calls"
        print(json.dumps(result, indent=2))
        return

    steps = flatten_skill(root, skill)
    if not steps:
        result["reason"] = "execution.calls did not resolve to any runnable steps"
        print(json.dumps(result, indent=2))
        return

    result["executable"] = True
    result["reason"] = f"resolved {len(steps)} step(s)"
    result["steps"] = steps
    print(json.dumps(result, indent=2))


def current_position(ctrl: dict) -> tuple[int, int]:
    completed = sum(1 for value in ctrl["steps"].values() if value["status"] == "completed")
    return completed + 1, len(ctrl["steps"])


def render_step(state: dict, step_key_value: str) -> None:
    step = state["control"]["steps"].get(step_key_value)
    if step is None:
        fail(f"step not found in state: {step_key_value}")

    root = Path(state["runtime"]["skills_root"])
    step_path = root / step["file"]
    if not step_path.exists():
        fail(f"step file not found: {step_path}")

    print(step_path.read_text(), end="")
    print()
    print("━━━ ASF Runtime ━━━")
    print()
    print("When this step is complete, run:")
    print()
    run_sh = Path(__file__).resolve().with_name("asf-run.sh")
    print(f"```bash\nbash {run_sh} complete {step_key_value}\n```")
    print()
    print("The runtime will print the next step. Follow it immediately unless the step asks for user confirmation.")


def print_current(state_path: Path, message: str) -> None:
    state = load_state(state_path)
    ctrl = state["control"]
    current = ctrl["current_step"]
    position, total = current_position(ctrl)
    print()
    print(f"[{position}/{total}] {current}")
    print("━" * 41)
    print(message)
    print("━" * 41)
    print()
    render_step(state, current)


def complete(step: str) -> None:
    state_path = state_path_from_args()
    state = load_state(state_path)
    ctrl = state["control"]
    order = ctrl["order"]
    if step not in ctrl["steps"]:
        fail(f"step not found: {step}")

    ctrl["steps"][step]["status"] = "completed"
    ctrl["interrupted"] = False
    ctrl["interrupt_reason"] = ""
    ctrl["updated_at"] = now()

    if step in order:
        index = order.index(step)
        for previous in order[:index]:
            if ctrl["steps"][previous]["status"] == "running":
                ctrl["steps"][previous]["status"] = "completed"

    next_step = None
    for key in order:
        if ctrl["steps"][key]["status"] == "pending":
            next_step = key
            break

    if next_step is None:
        ctrl["status"] = "completed"
        ctrl["current_step"] = ""
    else:
        ctrl["steps"][next_step]["status"] = "running"
        ctrl["current_step"] = next_step

    save_state(state_path, state)
    if next_step is None:
        print("ALL STEPS COMPLETED - workflow done.")
    else:
        print_current(state_path, "Next step exists. Follow the instructions below exactly.")


def rewind(step: str) -> None:
    state_path = state_path_from_args()
    state = load_state(state_path)
    ctrl = state["control"]
    order = ctrl["order"]
    if step not in ctrl["steps"]:
        fail(f"step not found: {step}")
    target_index = order.index(step)

    for index, key in enumerate(order):
        if index < target_index:
            ctrl["steps"][key]["status"] = "completed"
        elif index == target_index:
            ctrl["steps"][key]["status"] = "running"
        else:
            ctrl["steps"][key]["status"] = "pending"

    ctrl["status"] = "running"
    ctrl["current_step"] = step
    ctrl["interrupted"] = False
    ctrl["interrupt_reason"] = ""
    ctrl["updated_at"] = now()
    save_state(state_path, state)
    print_current(state_path, "Workflow rewound. Follow the instructions below exactly.")


def resume() -> None:
    state_path = state_path_from_args()
    state = load_state(state_path)
    state["control"]["interrupted"] = False
    state["control"]["interrupt_reason"] = ""
    state["control"]["updated_at"] = now()
    save_state(state_path, state)
    print_current(state_path, "Resuming workflow. Follow the instructions below exactly.")


def interrupt(reason: str) -> None:
    state_path = state_path_from_args()
    state = load_state(state_path)
    state["control"]["interrupted"] = True
    state["control"]["interrupt_reason"] = reason
    state["control"]["updated_at"] = now()
    save_state(state_path, state)
    print(f"Workflow interrupted: {reason}")


def validate(skills: list[str]) -> None:
    root = skills_root()
    targets = skills or [path.parent.name for path in sorted(root.glob("*/SKILL.md"))]
    for skill in targets:
        flatten_skill(root, skill)
    print("ASF validation passed")


def usage() -> None:
    print(
        """Usage: asf-run.sh <command> [args]

Commands:
  init <skill> "<task description>"
  inspect <skill>
  complete <STEP_KEY>
  rewind <STEP_KEY>
  resume
  interrupt "<reason>"
  current
  validate [skill...]
""",
        file=sys.stderr,
    )


def main() -> int:
    if len(sys.argv) < 2:
        usage()
        return 2

    command = sys.argv[1]
    args = sys.argv[2:]
    if command == "init":
        if len(args) < 2:
            usage()
            return 2
        init(args[0], args[1])
    elif command == "inspect":
        if len(args) != 1:
            usage()
            return 2
        inspect(args[0])
    elif command == "complete":
        if len(args) != 1:
            usage()
            return 2
        complete(args[0])
    elif command == "rewind":
        if len(args) != 1:
            usage()
            return 2
        rewind(args[0])
    elif command == "resume":
        resume()
    elif command == "interrupt":
        interrupt(args[0] if args else "needs user input")
    elif command == "current":
        print_current(state_path_from_args(), "Current step. Follow the instructions below exactly.")
    elif command == "validate":
        validate(args)
    else:
        usage()
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
