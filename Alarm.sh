#!/bin/bash
# Script to call for MIDAS alarms.
# Sends notifications to users.

date >> /home/ucn/tmp/testlog
echo "$1" >> /home/ucn/tmp/testlog

python3 /home/ucn/online/ucn-alarms-notification/send_alerts.py alarm "$1" >> /home/ucn/tmp/testlog

python3 /home/ucn/online/ucn-alarms-notification/bird_schedule.py
# python3 /home/ucn/online/ucn-alarms-notification/bird.py
