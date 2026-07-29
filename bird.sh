#!/bin/bash
# Activate the shared venv, then run bird.py, forwarding all arguments.

set -euo pipefail

# Resolve the directory this script lives in, so it works from any CWD.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck disable=SC1091
source "$SCRIPT_DIR/.venv/bin/activate"

python "$SCRIPT_DIR/bird.py" "$@"
