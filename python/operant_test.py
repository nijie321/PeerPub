#!/usr/bin/env python3

import pigpio
from PigpioStepperMotor import StepperMotor
import sys
import argparse
import time
from threading import Timer
import RPi.GPIO as gpio
from datalogger import LickLogger
import subprocess
import os
import random
import board # MPR121
import busio # MPR121
import adafruit_mpr121
import ids
from pump_move import PumpMove
# from gpiozero import DigitalInputDevice
import RPi.GPIO as GPIO
from RatActivityCouter import RatActivityCounter
import logging
from slackbot import send_message
from utils import reload_syringe, get_ratid_scantime #, houselight_check


# logger
logger = logging.getLogger('operant_log')
logger.setLevel(logging.DEBUG)

# handler (output all log to a file and if the log is error, also output to console)
fh = logging.FileHandler('/home/pi/operant.log')
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

# formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# add handlers
logger.addHandler(fh)
logger.addHandler(ch)

parser=argparse.ArgumentParser()
parser.add_argument('-schedule',  type=str, default="vr")
parser.add_argument('-ratio',  type=int, default=10)
parser.add_argument('-sessionLength',  type=int, default=3600)
parser.add_argument('-timeout',  type=int, default=20)
parser.add_argument('-rat1ID',  type=str, default="rat1")
parser.add_argument('-rat2ID',  type=str, default="rat2")
parser.add_argument('-rfidFile',  type=str)
parser.add_argument('-devID', type=str)
parser.add_argument('-sesID', type=int)
parser.add_argument('-step', type=int)
args=parser.parse_args()

# exp setting
schedule=args.schedule
ratio=args.ratio
sessionLength=args.sessionLength
timeout=args.timeout
rat1ID=args.rat1ID
rat2ID=args.rat2ID
rat0ID="ratUnknown"
step=args.step

devID = args.devID
sesID = args.sesID

rfid_file=args.rfidFile

## initiate pump motor
pi = pigpio.pi()

# Create I2C bus.
i2c = busio.I2C(board.SCL, board.SDA)
# Create MPR121 object.
mpr121 = adafruit_mpr121.MPR121(i2c)

# Initialize GPIO
gpio.setwarnings(False)
gpio.setmode(gpio.BCM)

# GPIO usage 
TIR = int(16) # Pin 36
SW1 = int(26) # Pin 37
SW2 = int(20) # Pin 38
TOUCHLED = int(12) #pin 32
MOTIONLED= int(6) #pin 31

# Setup switch pins
gpio.setup(SW1, gpio.IN, pull_up_down=gpio.PUD_DOWN)
gpio.setup(SW2, gpio.IN, pull_up_down=gpio.PUD_DOWN)
gpio.setup(TIR, gpio.IN, pull_up_down=gpio.PUD_DOWN)
gpio.setup(TOUCHLED, gpio.OUT)

# get date and time 
datetime=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
date=time.strftime("%Y-%m-%d", time.localtime())

# Initialize data logger 
dlogger = LickLogger(devID, sesID)
dlogger.createDataFile(schedule="{}{}TO{}".format(schedule,str(ratio),str(timeout)) , ratIDs=rat1ID+"_"+rat2ID, sessLen=sessionLength)

# Get start time
sTime = time.time()

# GLOBAL VARIABLES
FORWARD_LIMIT_BTN = 24
FORWARD_LIMIT_REACHED = False
# BACKWARD_LIMIT_BTN = 23
FORWARD_COUNTER = 0
touchcounter={rat0ID:0,rat1ID:0, rat2ID:0}
nextratio={rat0ID:0,rat1ID:ratio, rat2ID:ratio}
rew={rat0ID:0, rat1ID:0, rat2ID:0}
act={rat0ID:0, rat1ID:0, rat2ID:0}
ina={rat0ID:0, rat1ID:0, rat2ID:0}

lastActiveLick={rat0ID:{"time":float(sTime), "scantime": 0}, rat1ID:{"time":float(sTime), "scantime":0}, rat2ID:{"time":float(sTime), "scantime":0}}
lastInactiveLick={rat0ID:{"time":float(sTime), "scantime": 0}, rat1ID:{"time":float(sTime), "scantime":0}, rat2ID:{"time":float(sTime), "scantime":0}}

##############################################################
rats = {
    rat1ID: RatActivityCounter(rat1ID,ratio , "rat1"),
    rat2ID: RatActivityCounter(rat2ID,ratio, "rat2"),
    rat0ID: RatActivityCounter(rat0ID, 0),
}
##############################################################

FORWARD_LIMIT = GPIO.setup(FORWARD_LIMIT_BTN, GPIO.IN, pull_up_down= GPIO.PUD_DOWN)

pumptimedout={rat0ID:False, rat1ID:False, rat2ID:False}
lapsed=0  # time since program start
updateTime=0 # time since last data print out 
vreinstate=0
minInterLickInterval=0.15 # minimal interlick interval (about 6-7 licks per second)
maxISI = 15  # max lapse between RFID scan and first lick in a cluster 
maxILI = 3 # max interval between licks used to turn an RFID into unknown.   

def resetPumpTimeout(rat):
    # don't delete this line
    pumptimedout[rat] = False
    rats[rat].pumptimedout = False

houselight_on = False
def houselight_check():
    global houselight_on
    blink_light_command = "sudo python ./blinkenlights.py &"
    if not FORWARD_LIMIT_REACHED:
        if (time.localtime().tm_hour >= 21 and houselight_on is False) or (time.localtime().tm_hour >= 9 and time.localtime().tm_hour < 21) and houselight_on:
            houselight_on = True
            subprocess.call(blink_light_command, shell=True)

while lapsed < sessionLength:
    try:
        houselight_check()

        time.sleep(0.05) # allow 20 licks per sec
        ina0 = mpr121.touched_pins[0]
        act1 = mpr121.touched_pins[1]
        lapsed = time.time() - sTime

        if GPIO.input(FORWARD_LIMIT_BTN):
            # payload to send to slack
            payload = {'text': '{} SYRINGE EMPTIED!!! PLEASE RELOAD'.format(devID)}
            send_message(payload)

            reload_syringe()
            FORWARD_LIMIT_REACHED = True

        if act1 == 1:
            thisActiveLick=time.time()
            
            (ratid, scantime) = get_ratid_scantime(rats, "/home/pi/_active", thisActiveLick, True, maxILI, maxISI)
            
            try:
              rat = rats[ratid] 
            except KeyError:
              logger.exception("unable to retrive key %s", ratid)
              
            print("pumptimeout = {}".format(rat.pumptimedout))

            if(thisActiveLick - rat.last_act_licks["time"] > 1):
                rat.update_last_licks(thisActiveLick, scantime, act=True)
            else:
                rat.incr_active_licks()

                if FORWARD_LIMIT_REACHED:
                    dlogger.logEvent(rat.ratid, time.time(), "syringe empty", time.time() - sTime) 
                    rat.increase_syringe_empty()
                    FORWARD_LIMIT_REACHED = False
                else:
                    dlogger.logEvent(rat.ratid, time.time() - rat.last_act_licks["scantime"], "ACTIVE", lapsed, rat.next_ratio) # add next ratio

                rat.update_last_licks(thisActiveLick, scantime, act=True)
                
                RatActivityCounter.show_data(devID, sesID, sessionLength, schedule, lapsed, \
                                            rats[rat1ID],rats[rat2ID],rats[rat0ID])

                updateTime = time.time()

                # if not rat.pumptimedout:
                if not pumptimedout[ratid]:
                    rat.incr_touch_counter()
                    if rat.touch_counter >= rat.next_ratio and rat.ratid != "ratUnknown":
                        rat.incr_rewards()
                        rat.reset_touch_counter()
                        # don't delete this line
                        pumptimedout[ratid] = True

                        pumpTimer = Timer(timeout, resetPumpTimeout, [ratid] )
                        print("timeout on " + rat.ratid)
                        pumpTimer.start()

                        subprocess.call('sudo python ' + './blinkenlights.py -reward_happened True&', shell=True)

                        dlogger.logEvent(rat.ratid, time.time()- scantime, "REWARD", time.time() - sTime)
                        mover = PumpMove()
                        mover.move("forward", step)                            
                        del(mover)

                        RatActivityCounter.show_data(devID, sesID, sessionLength, schedule, lapsed, \
                                                rats[rat1ID],rats[rat2ID],rats[rat0ID])

                        updateTime = time.time()

                        if schedule == "fr":
                            rat.next_ratio = ratio
                        elif schedule == "vr":
                            rat.next_ratio = random.randint(1,ratio*2)
                        elif schedule == "pr":
                            breakpoint += 1.0
                            rat.next_ratop = int(5*2.72**(breakpoint/5)-5)
        elif ina0 == 1:
            thisInactiveLick = time.time()

            (ratid, scantime) = get_ratid_scantime(rats, "/home/pi/_inactive", thisInactiveLick, False, maxILI, maxISI)

            rat = rats[ratid] 

            if thisInactiveLick - rat.last_inact_licks["time"] > 1:
                rat.update_last_licks(thisInactiveLick, scantime, act=False)
            else:
                rat.incr_inactive_licks()
                dlogger.logEvent(rat.ratid,time.time() - rat.last_inact_licks["scantime"], "INACTIVE", lapsed)
                rat.update_last_licks(thisInactiveLick, scantime, act=False)

                RatActivityCounter.show_data(devID, sesID, sessionLength, schedule, lapsed, \
                                        rats[rat1ID],rats[rat2ID],rats[rat0ID])

                updateTime = time.time()

        # keep this here so that the PR data file will record lapse from sesion start 
        if schedule=="pr":
            lapsed = time.time() - lastActiveLick
        #show data if idle more than 1 min 
        if time.time()-updateTime > 60*1:
            RatActivityCounter.show_data(devID, sesID, sessionLength, schedule, lapsed, \
                                    rats[rat1ID],rats[rat2ID],rats[rat0ID])
            updateTime = time.time()
    except:
        logger.exception("while loop error")

dlogger.logEvent("", time.time(), "SessionEnd", time.time()-sTime)

date=time.strftime("%Y-%m-%d", time.localtime())
d_time = time.strftime("%H_%M_%S", time.localtime())

formatted_schedule = schedule+str(ratio)+'TO'+str(timeout)+"_"+ rat1ID+"_"+rat2ID
schedule_to = schedule+str(ratio)+'TO'+str(timeout)
finallog_fname = "Soc_{}_{}_{}_S{}_{}_{}_summary.tab".format(date,d_time,devID,sesID,formatted_schedule,sessionLength)

data_dict = {}
for rat_key, rat_rfid in zip(["ratID1","ratID2","ratID0"], [rat1ID, rat2ID, rat0ID]):
    rat = rats[rat_rfid]
    data_dict[rat_key] = [rat_rfid, date, d_time, devID, sesID, schedule_to, \
                            sessionLength, rat.active_licks, rat.inactive_licks, \
                                rat.rewards,rat.syringe_empty]

LickLogger.finalLog(finallog_fname, data_dict, rfid_file)

print(str(devID) +  "Session" + str(sesID) + " Done!\n")
RatActivityCounter.show_data(devID, sesID, sessionLength, schedule, lapsed, \
                        rats[rat1ID],rats[rat2ID],rats[rat0ID], "final")

subprocess.call('/home/pi/openbehavior/PeerPub/wifi-network/rsync.sh &', shell=True)
print(devID+  "Session"+ str(sesID) + " Done!\n")
