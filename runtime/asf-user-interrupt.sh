#!/usr/bin/env bash
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"

RUNTIME_DIR="$(cd "$(dirname "$0")" && pwd)"
INPUT="$(cat)"
STATE="$(printf '%s' "$INPUT" | python3 "$RUNTIME_DIR/asf-find-state.py" 2>/dev/null || true)"
[ -n "$STATE" ] || exit 0

STATUS="$(jq -r '.control.status // ""' "$STATE" 2>/dev/null)" || exit 0
[ "$STATUS" = "running" ] || exit 0

CURRENT="$(jq -r '.control.current_step // ""' "$STATE" 2>/dev/null)" || exit 0
[ -z "$CURRENT" ] && exit 0

TMP="${STATE}.tmp.$$"
jq '.control.interrupted = true' "$STATE" > "$TMP" && mv "$TMP" "$STATE"

RUN_SH="$RUNTIME_DIR/asf-run.sh"
jq -n --arg step "$CURRENT" --arg run "$RUN_SH" '{
  hookSpecificOutput: {
    hookEventName: "UserPromptSubmit",
    additionalContext: "[asf] Workflow is paused at step \($step). Resolve the user interaction. When returning to the workflow, run `bash \($run) resume`."
  }
}'
