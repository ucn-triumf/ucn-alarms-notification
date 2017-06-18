#/bin/bash
# Script to notify user in case of serious problems and shutdown stuff
# T. Lindner
# June 2017

# Send warning
python /home/ucn/online/ucn-alarms-notification/send_alerts.py alarm "$1"

# Shutdown stuff... currently not used
#odbedit -c "msg CriticalAlarm 'Shutting down HV'"
#odbedit -c "set /Equipment/PtfWiener/Settings/outputSwitch[*] 0"
#sleep 20

