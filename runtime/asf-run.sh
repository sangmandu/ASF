#!/usr/bin/env bash
set -euo pipefail

RUNTIME_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$RUNTIME_DIR/asf-runtime.py" "$@"
