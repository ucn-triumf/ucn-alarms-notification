#!/bin/bash
# Script to call for MIDAS alarms.
# Sends notifications to users.

set -euo pipefail

# Resolve the directory this script lives in, so it works from any CWD.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck disable=SC1091
source "$SCRIPT_DIR/.venv/bin/activate"

date >> /home/ucn/tmp/testlog
echo "$1" >> /home/ucn/tmp/testlog

python "$SCRIPT_DIR/send_alerts.py" alarm "$1" >> /home/ucn/tmp/testlog

python "$SCRIPT_DIR/bird_schedule.py"
# python "$SCRIPT_DIR/bird.py"
