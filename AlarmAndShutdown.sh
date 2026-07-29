#!/bin/bash
# Script to notify user in case of serious problems and shutdown stuff
# T. Lindner
# June 2017

set -euo pipefail

# Resolve the directory this script lives in, so it works from any CWD.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck disable=SC1091
source "$SCRIPT_DIR/.venv/bin/activate"

# Send warning
date >> /home/ucn/tmp/testlog
echo "$1" >> /home/ucn/tmp/testlog
echo "Bla" >> /home/ucn/tmp/testlog
python "$SCRIPT_DIR/send_alerts.py" alarm "$1" >> /home/ucn/tmp/testlog

# Shutdown stuff... currently not used
#odbedit -c "msg CriticalAlarm 'Shutting down HV'"
#odbedit -c "set /Equipment/PtfWiener/Settings/outputSwitch[*] 0"
#sleep 20
