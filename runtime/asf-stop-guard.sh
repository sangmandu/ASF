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

INTERRUPTED="$(jq -r '.control.interrupted // false' "$STATE" 2>/dev/null)" || INTERRUPTED="false"
[ "$INTERRUPTED" = "true" ] && exit 0

MODE="$(jq -r --arg step "$CURRENT" '.control.steps[$step].mode // "automatic"' "$STATE" 2>/dev/null)" || MODE="automatic"
if [ "$MODE" = "user_confirmation" ]; then
  TMP="${STATE}.tmp.$$"
  jq --arg step "$CURRENT" '.control.interrupted = true | .control.interrupt_reason = "awaiting user confirmation at " + $step' "$STATE" > "$TMP" && mv "$TMP" "$STATE"
  exit 0
fi

TOTAL="$(jq -r '.control.steps | length' "$STATE" 2>/dev/null)" || TOTAL="?"
COMPLETED="$(jq -r '[.control.steps[] | select(.status=="completed")] | length' "$STATE" 2>/dev/null)" || COMPLETED="?"
POSITION=$((COMPLETED + 1))
WORKFLOW="$(jq -r '.control.workflow // "workflow"' "$STATE" 2>/dev/null)" || WORKFLOW="workflow"
RUN_SH="$RUNTIME_DIR/asf-run.sh"

cat <<EOF
{
  "decision": "block",
  "reason": "[asf guard] $WORKFLOW is still running — step [$POSITION/$TOTAL] $CURRENT.\\nChoose one of the following:\\n  1. Step is complete → bash $RUN_SH complete $CURRENT\\n  2. Continue working → proceed with the workflow instructions\\n  3. Need user input → bash $RUN_SH interrupt \\\"<reason>\\\""
}
EOF
