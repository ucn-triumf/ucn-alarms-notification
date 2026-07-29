# ucn-alarms-notification

## Overview

Notification tooling for the TRIUMF UCN MIDAS DAQ. When a MIDAS alarm triggers,
these scripts read the active/triggered alarms from the ODB and notify the
people on shift through multiple channels: email, PagerDuty, and automated phone
calls (via the Bird voice API). The scripts are invoked by MIDAS alarm hooks
through the `.sh` launchers in this directory.

## Python scripts

- **`send_alerts.py`** — Sends email/SMS/PagerDuty notifications for an alarm.
  Fetches the triggered alarms from the ODB (via the mhttpd JSON interface),
  builds a message, and dispatches it to the configured recipient lists.
  Usage: `send_alerts.py <alarm|runstop|...> [message]`.

- **`bird_schedule.py`** — Escalating phone-call notifier (current version). Reads
  the on-shift people and their per-shift notification delays from the ODB, then
  calls each in turn (in parallel) until the alarm clears, falling back to a
  last-resort VIP contact. Also supports a manual test call:
  `bird_schedule.py --testcall --name=<name>`. Has `DEBUG`/`DRY_RUN` flags.

- **`bird.py`** — Earlier, simpler version of the phone-call notifier. Calls the
  shift/urc/vip contacts sequentially with fixed per-level delays. Largely
  superseded by `bird_schedule.py`.

## Shell scripts

- **`setup_venv.sh`** — Creates the shared `.venv`, installs the PyPI
  dependencies from `requirements.txt`, and installs the MIDAS client from
  `$MIDASSYS/python`. Run this once before using the scripts.
- **`Alarm.sh` / `AlarmAndShutdown.sh`** — MIDAS alarm hook entry points.
- **`send_alerts.sh` / `bird.sh` / `bird_schedule.sh`** — Wrappers that activate
  the venv and run the matching Python script, forwarding any arguments.
