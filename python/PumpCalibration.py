
from gpiozero import Button
from gpiozero import DigitalInputDevice
from pump_move import PumpMove
import board
import busio
import adafruit_mpr121
from ids import IDS
import time
import math
import os
file_dir = "/home/pi/SocialDrinking/{}"


def pump_calibration(step_size, fname):
    old_step = step_size
    step = step_size
    # command = input("Please scan the ") 
    act_count = 0
    i2c = busio.I2C(board.SCL, board.SDA)
    mpr121 = adafruit_mpr121.MPR121(i2c)

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

    print("current step size = " + str(step_size)) 
    print("please prepare to measure the solution.")

    while True:
        time.sleep(0.050)
        act = mpr121.touched_pins[1]

        if act:
            if act_count % 5 == 0:
                for i in range(5):
                    mover.move("forward", step)

            act_count += 1
            print("count" + str(act_count))
            if act_count == 15:
                response = input("please enter the amount measured (numeric value) or scan the command id again to exit: ").strip()
                # if the same command RFID is scanned again, exit the while loop
                if response[-2:] == '6b' or response[-2:] == '8e' or response[-2:] == 'ba':
                    break
                else:
                    try:
                        response = int(response)
                    except ValueError:
                        response = int(input("please re-enter the amount measured: ").strip())

                avg_measured_value = response / 3
                print("average value: {}".format(avg_measured_value))
                
                if (avg_measured_value < (300-10) or avg_measured_value > (300+10)):
                    # update step size
                    print("previous step: {}".format(step))
                    step = math.ceil( (step / (avg_measured_value / 5)) *60  )
                    
                    print("modified step: {}".format(step))
                    print("Touch spout to measure again")
                
                act_count = 0

    del(mover)

    date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    record = "{}\t"*3

    ids = IDS()
    # print out the old/new steps after the calibration
    print("old step size: {}".format(old_step))
    print("new step size: {}".format(step))

    # overwrite the old step size in 'peerpub_config.json' file
    ids.change_step(step)

    f_specifiers = ""
    file_path = file_dir.format(fname)
    print("Update stepsize in " +fname)
    if os.path.isfile(file_path):
        f_specifiers = "a"
    else:
        f_specifiers = "a"

    with open(file_path, f_specifiers) as f:
        f.write((record+"\n").format(date, old_step, step))
