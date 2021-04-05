#!/usr/bin/env python3

import sys
import time
import subprocess
import os
from ids import IDS
from gpiozero import Button
from pump_move import PumpMove
from gpiozero import DigitalInputDevice

from config import DATA_DIR, DATA_PREFIX, COMMAND_IDS, ROOT, get_sessioninfo

import argparse

parser=argparse.ArgumentParser()
parser.add_argument('-test',  type=bool, default=False)

args=parser.parse_args()





# get date and time 
datetime=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
date=time.strftime("%Y-%m-%d", time.localtime())

# get device and session ids
ids = IDS()
ids.sessionIncrement()


# file to store RFID scann times
RFIDFILE = DATA_DIR + DATA_PREFIX + date + "_" + str(ids.devID)+ "_S"+str(ids.sesID)+ "_RFID.csv"

if args.test:
    # RatID = "ef"
    RatID = "002cd652"
else:
    RatID = input("please scan a command RFID\n")[-8:]

# rat_id = input("please scan a  RFID\n")[-8:]

sessioninfo = get_sessioninfo(RatID)

while(len(sessioninfo) == 0):
    RatID = input("command ID not found please rescan the id: ")[-8:]
    sessioninfo = get_sessioninfo(RatID)

    
sessioninfo = sessioninfo[0]

# class SessionInfo():
#     def __init__(self, schedule, timeout, nextratio, sessionLength, ratio):
#         self.schedule = schedule
#         self.timeout = timeout
#         self.nextratio = nextratio
#         self.sessionLength = sessionLength
#         self.ratio = ratio
#         self.nextratio = nextratio


# command_ids = {
#     ('3c', '88'): SessionInfo(schedule="pr", timeout=10, nextratio=int(5*2.72**(2/5)-5), sessionLength=20*60, ratio=""), # PR
#     ('52', '8f'): SessionInfo(schedule="fr", timeout=10, nextratio=5, sessionLength=60, ratio=5), # FR5 1h
#     ('6f', 'b9'): SessionInfo(schedule="fr", timeout=10, nextratio=5, sessionLength=60*60*16, ratio=5), # FR5 16h
#     ('65', '8c'): SessionInfo(schedule="ext", timeout=0, nextratio=1000000, sessionLength=60*60*1, ratio=1000000), # extinction
#     ('ef', 'a7'): SessionInfo(schedule="vr", timeout=10, nextratio=10, sessionLength=60*60*1, ratio=10), # VR10, 1h
#     ('b8', '7e'): SessionInfo(schedule="vr", timeout=10, nextratio=10, sessionLength=60*60*2, ratio=10), # VR10, 2h
#     ('9a', '2f'): SessionInfo(schedule="vr", timeout=10, nextratio=10, sessionLength=60*60*4, ratio=10), # VR10, 4h
#     ('ff', '2d'): SessionInfo(schedule="vr", timeout=1, nextratio=5, sessionLength=60*60*4, ratio=5), # VRreinstate, 4h
#     ('8e', 'c3'): SessionInfo(schedule="vr", timeout=10, nextratio=10, sessionLength=60*60*16, ratio=10), # VR10 16h
# }

# while RatID not in COMMAND_IDS:
#     RatID = input("command ID not found, please rescan the id: ")[-8:]

# for key in command_ids.keys():
#     if RatID[-2:] in key:
#         sess_info = command_ids[key]
    


# ----------------------------------------------------------------------------------------------------


# mover = PumpMove()
# forwardbtn = Button("GPIO5")
# backwardbtn = Button("GPIO27")

# BACKWARD_LIMIT_BTN = "GPIO23"
# BACKWARD_LIMIT = DigitalInputDevice(BACKWARD_LIMIT_BTN)

# def forward():
#     while forwardbtn.value == 1:
#         mover.move("forward")

# def backward():
#     while BACKWARD_LIMIT.value != 1:
#         mover.move("backward")

# forwardbtn.when_pressed = forward
# backwardbtn.when_pressed = backward


schedule = sessioninfo[0]
timeout = sessioninfo[1]
ratio = sessioninfo[2]
sessionLength = sessioninfo[4]

# sessionLength = sess_info.sessionLength
# ratio = sess_info.ratio
# timeout = sess_info.timeout
# schedule = sess_info.schedule


print("Run {} {} for {} hour \n".format(schedule, str(ratio), str(int(sessionLength/3600))))


def scan_rats():
    rat1 = input("please scan rat1\n")[-8:]
    time.sleep(1) # delay for time to get the next rat
    rat2 = input("please scan rat2\n")[-8:]

    while(rat1 == rat2):
        rat2 = input("The IDs of rat1 and rat2 are identical, please scan rat2 again\n")[-8:]

    return rat1, rat2

rat1, rat2 = scan_rats()

print("Session started\nSchedule:{}{}TO{}\nSession Length:{}sec\n",schedule, str(ratio), str(timeout), str(sessionLength))

# start time
sTime=time.time()
lapsed=0

# delete mover to prevent overheating
# del(mover)

subprocess.call("python3 operant_test.py " + \
                "-schedule " + schedule + \
                " -ratio " + str(ratio)  + \
                " -sessionLength " + str(sessionLength) + \
                " -rat1ID " + str(rat1) + \
                " -rat2ID " + str(rat2) + \
                " -timeout " + str(timeout) + \
                " -rfidFile " + RFIDFILE + \
                " &",
                shell=True
                )
# subprocess.call("python3 operant_test.py -schedule {} -ratio {} -sessionLength {} -rat1ID {} -rat2ID {} -timeout {} &".format(schedule, str(ratio), str(sessionLength), rat1, rat2, str(timeout), shell=True))

poke_counts = {rat1:{"act": 0, "inact": 0}, rat2:{"act":0, "inact":0}}


def record_data(fname, mode ,record):
    with open(fname, mode) as f:
        f.write(record)


file_format = "{}\t{}\t{}\t{}\t{}\n"
def write_header():
    with open(RFIDFILE, "w+") as f:
        f.write(file_format.format("rfid", "time", "act_inact", "lapsed", "poke_count"))

write_header()

while lapsed < sessionLength:
    lapsed=time.time()-sTime
    try:
        rfid=input("rfid waiting\n")
    except EOFError:
        break
    if (len(rfid)==10):
        temp_rfid = rfid[-8:]
        poke_counts[temp_rfid]["inact"] = poke_counts[temp_rfid]["inact"] + 1
        record = file_format.format(temp_rfid, str(time.time()), "inactive", str(lapsed), str(poke_counts[temp_rfid]["inact"]))
        print(record)
        record_data(fname=ROOT+"/_inactive",mode="w+",record=record)
        record_data(fname=RFIDFILE, mode="a+", record=record)
            

    if (len(rfid)==8):
        try:
            poke_counts[rfid]["act"] = poke_counts[rfid]["act"] + 1
        except KeyError as e:
            print("error occured: {}".format(e))

        record = file_format.format(rfid, str(time.time()), "active", str(lapsed), str(poke_counts[rfid]["act"]))
        print(record)
        record_data(fname=ROOT+"/_active",mode="w+",record=record)
        record_data(fname=RFIDFILE,mode="a+", record=record)
