#!/usr/bin/python3
# Script stolen from Ben Smith and DEAP-3600.
# sends email, SMS messages for errors...
# T. Lindner
# June 2017

# Sep 2025 - D Fujimoto
# 	Added pagerduty support
#	Removed unused imports
# 	Updated to python3 syntax

import sys
import json
import subprocess
import requests

from subprocess import Popen, PIPE
import smtplib
from email.mime.text import MIMEText

def get_json_alarms():

    command = "curl 'http://localhost:8082/?cmd=jcopy&odb=/Alarms/Alarms&encoding=json'"
    p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    #print(stdout)
    return json.loads(stdout)#, "ISO-8859-1")

if len(sys.argv) < 2:
    print("Incorrect number of arguments.  Usage: ")
    print("send_alerts.py <runstop or alarm> [msg]")
    sys.exit()

alert_type = sys.argv[1]
message = ("" if len(sys.argv) == 2 else sys.argv[2])

json_alarms = get_json_alarms()

alarm_message = ""

# Loop over the alarms.  Find active, triggered alarms...
for alarm in json_alarms:

    if json_alarms[alarm]["Active"] == 0:
        continue

    if json_alarms[alarm]["Triggered"] == 0:
        continue

    alarm_message += "Alarm " + alarm + " is active and triggered\n"
    alarm_message += "Condition: " + json_alarms[alarm]["Condition"] + "\n"
    alarm_message += "Message: " + json_alarms[alarm]["Alarm Message"] + "\n"
    alarm_message += "\n"

print('message:\n', alarm_message, flush=True)

#smses = ["sms:16042509160@sms.rogers.com"]
smses = []
slacks = []
emails = ["lindner@triumf.ca","rpicker@triumf.ca","dfujimoto@triumf.ca","shinsuke.kawasaki@kek.jp","giampapietro@gmail.com"]
# emails = []
pagerduty_routingkey = ['03fc38a2dd234d08d0b1f896b6165e5d']

me = "UCN DAQ <auto-notifications@daq01.ucn.triumf.ca>"

if len(smses):
    subject = "Run " + str(run_number)
    text = ""
    if (alert_type == "alarm"):
        text += "A UCN alarm has been raised!"
    elif (alert_type == "runstop"):
        text += "The run has stopped!"
    elif (alert_type == "test"):
        subject = "Hello!"
        text += "This is a test message from the UCN DAQ."
    text += " Check https://daq01.ucn.triumf.ca/ for more details."
    msg = MIMEText(text)
    msg['Subject'] = subject
    msg['From'] = me
    msg['To'] = ", ".join(smses)

    s = smtplib.SMTP('localhost')
    s.sendmail(me, smses, msg.as_string())
    s.quit()

    print("Sent", alert_type, "SMSes to", ", ".join(smses))

if len(emails):
    text = ""
    subject = "UCN DAQ "
    if (alert_type == "alarm"):
        text += "An alarm has been raised! Please check https://daq01.ucn.triumf.ca/ for full details.\n\n" + message
        subject += " - an alarm has been raised!"
    if (alert_type == "criticalalarm"):
        text += "A critical alarm has been raised! Equipment is being shutdown. "
        text += "Please check https://daq01.ucn.triumf.ca/ for full details.\n\n" + message
        subject += " - a critical temperature alarm has been raised!"
        text += alarm_message
    if (alert_type == "emergency"):
        text += "An emergency alarm has been raised! Please check https://daq01.ucn.triumf.ca/ for full details.\n\n" + message
        subject += " - an alarm has been raised!"

    msg = MIMEText(text)
    msg['Subject'] = subject
    msg['From'] = me
    msg['To'] = ", ".join(emails)

    s = smtplib.SMTP('localhost')
    s.sendmail(me, emails, msg.as_string())
    s.quit()

    print("Sent", alert_type, "email to", ", ".join(emails))

if len(pagerduty_routingkey):
    if (alert_type == "emergency"):
        for key in pagerduty_routingkey:
            url = 'https://events.pagerduty.com/v2/enqueue'
            header = {'content-type': 'application/json'}
            data = {'payload': {'summary': alarm,
                                'severity': 'critical',
                                'source': 'MIDAS Alarm'},
                    'routing_key': key,
                    'event_action': 'trigger'
                    }
            print(requests.post(url, data=json.dumps(data), headers=header))

print()
