#/bin/bash
# Script to call for MIDAS alarms.
# Sends notifications to users.

python /home/ucn/online/ucn-alarms-notification/send_alerts.py alarm "$1"
