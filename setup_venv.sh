#!/bin/bash
# Set up the virtual environment shared by all scripts in this directory.
#
# Creates a .venv next to this script, installs the PyPI dependencies listed in
# requirements.txt, and installs the MIDAS python client (editable) from
# $MIDASSYS/python. Safe to re-run: an existing .venv is reused.

set -euo pipefail

# Resolve the directory this script lives in, so it works from any CWD.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

# The MIDAS python client is not on PyPI; it comes from the MIDAS install.
if [[ -z "${MIDASSYS:-}" ]]; then
    echo "Error: MIDASSYS is not set. Set it to your MIDAS installation and retry." >&2
    exit 1
fi
if [[ ! -f "$MIDASSYS/python/setup.py" ]]; then
    echo "Error: '$MIDASSYS/python/setup.py' not found. Is MIDASSYS correct?" >&2
    exit 1
fi

# Create the venv only if it does not already exist (idempotent re-runs).
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating virtual environment at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

# Activate the venv for the remaining install steps.
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# Install dependencies: pip itself, the PyPI packages, then MIDAS (editable).
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements.txt"
pip install -e "$MIDASSYS/python"

echo "Done. Use the environment via: $VENV_DIR/bin/python"
