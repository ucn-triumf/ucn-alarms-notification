#!/usr/bin/python3

import json, re
import requests
import time
import midas
import midas.client
import numpy as np

# settings for rpicker messagebird
workspaceId = 'd11bd41d-22ce-4e9a-9dd1-98e90c015029'
channelId = 'b923a1b8-b002-52c8-aa9d-f460d606227d'
APIKEY = "vB50EVCJnDxWc3lLdM69JkZHN8w2Sgw4pnuC"
outgoing = "12264588892" # outgoing number

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

    return data3['status']

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
    t0 = time.time()
    while True:

        status = check_incall(callId)

        # call was answered
        if status == 'ongoing':
            break

        # not answered
        elif status == 'no-answer':
            client.msg('Recipient did not pick up the phone')
            return

        # timeout
        if time.time() - t0 > 60:
            client.msg('Call timeout (60s)')
            return

        # check again later
        time.sleep(1)

    time.sleep(0.5)

    # play the message
    play_message(callId, message+',')

# get all triggered alarms
def get_triggered_alarms(client):
    all_alarms = client.odb_get('Alarms/Alarms')
    alarming = [(key, val['Alarm Message']) for key, val in all_alarms.items() if val['Triggered']]
    return alarming

def call_shifter(client, name, number):

    # notify shifter
    alarming = get_triggered_alarms(client)
    if len(alarming) > 0:
        client.msg(f'Calling {name} due to alarm')
        message = [a[1] for a in alarming]
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

    # setup who called list
    need_to_call = np.full(len(onshift_name), True)

    # wait for alarm clear
    t0 = time.monotonic()
    while any(need_to_call):

        # stop if all alarms cleaned
        if len(get_triggered_alarms(client)) == 0:
            return

        # else check if we need to call someone
        for i in range(len(onshift_name)):

            # if we called them already, skip
            if not need_to_call[i]:
                continue

            # get time delay
            delay  = delays[shiftid.index(onshift_id[i])]

            # check if need to call
            if time.monotonic()-t0 > delay:
                need_to_call[i] = False
                number = client.odb_get(f'Shifts/ContactInfo/{onshift_name[i]}/phone_call')
                call_shifter(client, onshift_name[i], number)

        # wait
        time.sleep(1)

if __name__ == "__main__":
    alarm()
