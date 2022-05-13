#!/usr/bin/env python3

# standard libraries
import sys
import time
import subprocess
import argparse
import logging
import os
import glob

# third-party libraries
from gpiozero import Button
from pump_move import PumpMove
from gpiozero import DigitalInputDevice

# self-define libraries
from config import DATA_DIR, DATA_PREFIX, ROOT, get_sessioninfo
from PumpCalibration import pump_calibration
from ids import IDS

# logging config
logger = logging.getLogger('main_log')
logger.setLevel(logging.DEBUG)

# handler (output all log to a file and if the log is error, also output to console)
fh = logging.FileHandler('/home/pi/main.log')
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

# formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# add handlers
logger.addHandler(fh)
logger.addHandler(ch)
# --------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument('-test',  type=bool, default=False)

args = parser.parse_args()

# get date and time
datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
date = time.strftime("%Y-%m-%d", time.localtime())

# get device and session ids
ids = IDS()
#ids.sessionIncrement()

# speed for the stepper motor
motor_step = ids.step

sTime = time.time()

# get software version from lastest update
filepath = '/home/pi/SocialDrinking/*_update'
if glob.glob(filepath):
  for update in glob.glob(filepath):
      if os.path.getsize(update) > 0:
        with open(update, 'r') as f:
            for line in f:
                pass
            last_line = line
        print("Latest update: \n" + last_line)
      else: print("Empty update_file")
else:
    print("update_file does not exist")
    
# constant for pump calibration program and update github chip
PUMP_CALIBRATION = False
UPDATE_REPO = False

# the inactive and active antenna scan the RFID in different format
# inactive scans 10 alpha-numeric characters, active scans 8
# here, we only get the last 8 characters
RatID = input("please scan a command RFID\n")[-8:]

# sync data
if RatID[-2:] == "94" or RatID[-2:] == "fa":
    subprocess.call(
        "bash /home/pi/openbehavior/PeerPub/wifi-network/rsync.sh", shell=True)
    # exit the program
    #sys.exit()
    
# check the last 2 characters
if RatID[-2:] == "6b" or RatID[-2:] == "ba" or RatID[-2:] == "8e":
    PUMP_CALIBRATION = True

if RatID[-2:] == "0c" or RatID[-2:] == "fe":
    UPDATE_REPO = True

# update github repo. see 'update_repo.sh' for details
if UPDATE_REPO:
    # after update, the pi will restart within 1 minutes
    subprocess.call(
        "bash /home/pi/openbehavior/PeerPub/utility_script/update_repo.sh &", shell=True)
    # exit the program
    sys.exit()

if not PUMP_CALIBRATION:
    # get the session information (timeout, ratio, nexratio, etc...) from 'session_configuration.csv' file under python directory
    sessioninfo = get_sessioninfo(RatID)

    while(len(sessioninfo) == 0):
        RatID = input("command ID not found please rescan the id: ")[-8:]
        sessioninfo = get_sessioninfo(RatID)

    sessioninfo = sessioninfo[0]

    mover = PumpMove()
    forwardbtn = Button("GPIO5")
    backwardbtn = Button("GPIO27")

    BACKWARD_LIMIT_BTN = "GPIO23"
    BACKWARD_LIMIT = DigitalInputDevice(BACKWARD_LIMIT_BTN)

    def forward():
        while forwardbtn.value == 1:
            mover.move("forward")

    def backward():
        while BACKWARD_LIMIT.value != 1:
            mover.move("backward")

    forwardbtn.when_pressed = forward
    backwardbtn.when_pressed = backward
    
    #push syringe to wet spout
    mover.move("forward")
    mover.move("forward")

    # ignore the if part (for test)
    if args.test:
        schedule = "fr"
        timeout = 10
        ratio = 10
        sessionLength = 60
    else:
        schedule = sessioninfo[0]
        timeout = sessioninfo[1]
        ratio = sessioninfo[2]
        sessionLength = int(sessioninfo[4])

    # file to store RFID scann times
    ids.sessionIncrement()
    RFIDFILE = DATA_DIR + DATA_PREFIX + date + "_" + \
        str(ids.devID) + "_S"+str(ids.sesID) + \
        "_" + str(sessionLength) + "_RFID.csv"

    print("Run {} {} for {} hour \n".format(
        schedule, str(ratio), str(int(sessionLength/3600))))


def scan_rats():
    rat1 = input("please scan rat1\n")[-8:]
    time.sleep(1)  # delay for time to get the next rat
    rat2 = input("please scan rat2\n")[-8:]

    while(rat1 == rat2):
        rat2 = input(
            "The IDs of rat1 and rat2 are identical, please scan rat2 again\n")[-8:]

    return rat1, rat2


def record_data(fname, mode, record):
    try:
        with open(fname, mode) as f:
            f.write(record)
    except:
        logger.exception("unable to open filename %s", fname)


print(datetime)
# overwrite the id files before the program start
# this will remove the rfid from previous sessions


def overwrite_id_file(rat1, rat2, poke_counts):
    with open("/home/pi/_inactive", "w") as f:
        record = file_format.format(rat1, str(time.time()), "inactive", str(
            time.time()-sTime), str(poke_counts[rat1]["inact"]))
        f.write(record)

    with open("/home/pi/_active", "w") as f:
        record = file_format.format(rat2, str(time.time()), "active", str(
            time.time()-sTime), str(poke_counts[rat2]["act"]))
        f.write(record)


file_format = "{}\t{}\t{}\t{}\t{}\n"

if PUMP_CALIBRATION:
    logger.info("pump test started")
    pump_calibration(motor_step, "{}_steps".format(ids.devID))
else:
    # get rats RFID
    rat1, rat2 = scan_rats()

    print("Session started\nSchedule:{}{}TO{}\nSession Length:{}sec\n",
          schedule, str(ratio), str(timeout), str(sessionLength))

    # start time
    sTime = time.time()
    lapsed = 0

    # delete mover to prevent overheating
    del(mover)

    logger.info("called operant")
    subprocess.call("python3 operant_test.py " +
                    "-schedule " + schedule +
                    " -ratio " + str(ratio) +
                    " -sessionLength " + str(sessionLength) +
                    " -rat1ID " + str(rat1) +
                    " -rat2ID " + str(rat2) +
                    " -timeout " + str(timeout) +
                    " -rfidFile " + RFIDFILE +
                    " -devID " + ids.devID +
                    " -sesID " + str(ids.sesID) +
                    " -step " + str(motor_step) +
                    " &",
                    shell=True
                    )

    # initialize poke counts
    poke_counts = {rat1: {"act": 0, "inact": 0}, rat2: {"act": 0, "inact": 0}}

    # empty the information from previous session
    overwrite_id_file(rat1, rat2, poke_counts)

    logger.info("while loop started")

    while lapsed < sessionLength:
        lapsed = time.time()-sTime
        try:
            rfid = input("rfid waiting\n")
        except EOFError:
            # when the input encounter an end of line before reading any input
            continue
        try:
            # if the length of id is 10, then it's a inactive poke
            if (len(rfid) == 10):
                temp_rfid = rfid[-8:]
                poke_counts[temp_rfid]["inact"] = poke_counts[temp_rfid]["inact"] + 1
                record = file_format.format(temp_rfid, str(time.time()), "inactive", str(
                    lapsed), str(poke_counts[temp_rfid]["inact"]))
                print(record)
                # write the poke information to file
                record_data(fname=ROOT+"/_inactive", mode="w+", record=record)
                record_data(fname=RFIDFILE, mode="a+", record=record)

            # if the length of id is 8, then it's a active poke
            if (len(rfid) == 8):
                poke_counts[rfid]["act"] = poke_counts[rfid]["act"] + 1
                record = file_format.format(rfid, str(time.time()), "active", str(
                    lapsed), str(poke_counts[rfid]["act"]))
                print(record)
                # write the poke information to file
                record_data(fname=ROOT+"/_active", mode="w+", record=record)
                record_data(fname=RFIDFILE, mode="a+", record=record)
        except:
            logger.exception("maybe KeyError?")
