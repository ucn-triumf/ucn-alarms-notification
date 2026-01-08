#!/usr/bin/python3

import json, re
import requests
import time
import midas
import midas.client
import numpy as np
from multiprocessing import Process
import sys

# settings for rpicker messagebird
workspaceId = 'd11bd41d-22ce-4e9a-9dd1-98e90c015029'
channelId = 'b923a1b8-b002-52c8-aa9d-f460d606227d'
APIKEY = "vB50EVCJnDxWc3lLdM69JkZHN8w2Sgw4pnuC"
outgoing = "12264588892" # outgoing number

DEBUG = False
DRY_RUN = False

# place a call
def place_call(number):

    # clean input number
    number = str(number).strip()
    number = re.sub('[^0-9a-zA-Z]+', '', number)

    # place the call
    response = requests.post(
        f"https://api.bird.com/workspaces/{workspaceId}/channels/{channelId}/calls",
        headers={"Authorization":f"AccessKey {APIKEY}","Content-Type":"application/json"},
        data=json.dumps({
        "from": outgoing,
        "to": number,
        "ringTimeout": 60,
        "maxDuration": 120,
        "record": False,
        })
    )

    data = response.json()
    callId = data['id']
    return callId

# check if call answered
def check_incall(callId):
    response3 = requests.get(
        f"https://api.bird.com/workspaces/{workspaceId}/channels/{channelId}/calls/{callId}/insights",
        headers={"Authorization":f"AccessKey {APIKEY}","Accept":"*/*"},
    )
    data3 = response3.json()
    if DEBUG:
        print(f'check in call response:')
        for key, val in data3.items():
            print(f'\t{key}: {val}')

    return data3

# play message
def play_message(callId, message):
    response2 = requests.post(
        f"https://api.bird.com/workspaces/{workspaceId}/channels/{channelId}/calls/{callId}/say",
        headers={"Authorization":f"AccessKey {APIKEY}","Content-Type":"application/json"},
        data=json.dumps({
        "text": message,
        "locale": "en-US",
        "voice": "text",
        "loop": 10,
        "timeout": 30
        })
    )
    return response2.json()

# notify user
def notify(number, message, client):

    # place call
    callId = place_call(number)

    # wait until call is answered
    t0 = time.monotonic()
    while True:

        response = check_incall(callId)
        status = response['status']

        # call was answered
        if status == 'ongoing':
            client.msg('Recipient answered the phone')
            break

        # not answered
        elif status == 'no-answer':
            client.msg('Recipient did not pick up the phone')
            return

        # failed
        elif status == 'failed':
            client.msg(f'Call failed (SIP code {response["hangupSipCode"]}, see https://www.rfc-editor.org/rfc/rfc3261 section 21)')
            return

        # cancelled
        elif status == 'cancelled':
            client.msg('Call cancelled')
            return

        # timeout
        if time.monotonic() - t0 > 60:
            client.msg('No response call timeout (60s)')
            return

        # check again later
        time.sleep(1)

    time.sleep(0.5)

    # play the message
    if DEBUG:
        print(f'Playing message in call')
    play_message(callId, message+',')

# get all triggered alarms
def get_triggered_alarms(client):
    all_alarms = client.odb_get('Alarms/Alarms')
    alarming = [(key, val['Alarm Message']) for key, val in all_alarms.items() if val['Triggered']]
    return alarming

def call_shifter(client, name, number):

    # notify shifter
    alarming = get_triggered_alarms(client)
    if len(alarming) > 0 or DEBUG:
        client.msg(f'Calling {name} due to alarm')
        message = [a[1] for a in alarming]

        if DEBUG: 
            message = ['phone notify debugging test']
            print(f'call shifter {name} at {number}')

        notify(number, ', '.join(message), client)
    return True

# check for midas alarms and call shifter if one or more are active
def alarm():

    # setup midas client
    client = midas.client.MidasClient("messagebird")

    # get names, shiftids of those on shift
    onshift_name = client.odb_get('Shifts/Settings/onshift_names')
    onshift_id = client.odb_get('Shifts/Settings/onshift_shiftid')

    # ensure is a list
    if isinstance(onshift_id, int):
        onshift_id = [onshift_id]
    if isinstance(onshift_name, str):
        onshift_name = [onshift_name]

    # get delays
    shiftid = np.array(client.odb_get('Shifts/ShiftSetup/shiftids'))
    delays = np.array(client.odb_get('Shifts/ShiftSetup/notify_delay_mins'))

    # trim to shiftids > 0
    keep_idx = shiftid > 0
    shiftid = shiftid[keep_idx].tolist()
    delays = delays[keep_idx]

    # get last resort person
    last_name = client.odb_get('Shifts/messagebird/vip')
    last_delay = client.odb_get('Shifts/messagebird/vip_delay_min')
    onshift_name = list(onshift_name) + [last_name]
    delays = list(delays) + [last_delay]
    shiftid = list(shiftid) + [999]
    onshift_id = list(onshift_id) + [999]

    # setup who called list
    need_to_call = np.full(len(onshift_name), True)

    if DEBUG: 
        print(f'onshift_name: {onshift_name}')
        print(f'delays: {delays}')
        print(f'shiftid: {shiftid}')
        print(f'onshift_id: {onshift_id}')

    # wait for alarm clear
    t0 = time.monotonic()
    while any(need_to_call):

        if DEBUG:
            print('='*50)

        # stop if all alarms cleaned
        if len(get_triggered_alarms(client)) == 0 and not DEBUG:
            return

        # else check if we need to call someone
        for i in range(len(onshift_name)):

            # if we called them already, skip
            if not need_to_call[i]:
                continue

            # get time delay
            delay  = delays[shiftid.index(onshift_id[i])]
            name = onshift_name[i]
            
            if DEBUG:
                print(f'Time elpased: {time.monotonic()-t0:.0f} ({name} delay: {delay*60})')

            # check if need to call
            if time.monotonic()-t0 > delay*60:
                need_to_call[i] = False
                number = client.odb_get(f'Shifts/ContactInfo/{onshift_name[i]}/phone_call')

                if not DRY_RUN:
                    p = Process(target=call_shifter, args=(client, name, number))
                    p.start()
                    # call_shifter(client, name, number)

        # wait
        time.sleep(1)

if __name__ == "__main__":
    
    # get commandline args
    args = sys.argv[1:]

    # defaults
    do_testcall = False
    name = ''

    # if no additional args, run full alarm
    if len(args) == 0:
        alarm()
        
    else:

        # setup midas client
        client = midas.client.MidasClient("messagebird")
    
        # eval args
        for arg in args:

            if '--name' in arg:
                name = arg.split('=')[1]
            elif '--testcall' in arg:
                do_testcall = True

        # make test call
        if do_testcall:

            # get number
            try:
                number = client.odb_get(f'/Shifts/ContactInfo/{name}/phone_call')
            except KeyError as err:
                client.msg(str(err), is_error=True)
            
            # make the call
            client.msg(f'Placing test call to {name} at {number}')
            notify(number, "test call from MIDAS", client)        