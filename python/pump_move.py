import signal
import sys
from time import sleep

import RPi.GPIO as GPIO
from gpiozero import InputDevice
from gpiozero import Servo
import pigpio

rotate_dir = 1

GPIO.setwarnings(False)


class PumpMove:
    def __init__(self):
        # GPIO pins numbers
        self.DIR = 26
        self.STEP = 6
        self.SLEEP = 25
        self.MODE = (17, 22)

        # clock-wise and counter clock-wise
        self.CW = 1
        self.CCW = 0

        # GPIO setup
        self.GPIO = GPIO
        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setup(self.DIR, self.GPIO.OUT, initial=self.GPIO.HIGH)
        self.GPIO.setup(self.STEP, self.GPIO.OUT, initial=self.GPIO.HIGH)
        self.GPIO.output(self.DIR, self.CW)

        self.GPIO.setup(self.MODE, self.GPIO.OUT)

        self.RESOLUTION = {
            'Full': (0, 0),
            'Half': (1, 0),
            '1/8': (0, 1),
            '1/16': (1, 1),
        }

        self.delayforward = .0209 / 40
        self.delaybackward = .0209 / 1000
        self.rotate_dir = rotate_dir

    # move forward and backward by providing the direction
    def move(self, direction, steps=150):
        direction_dict = {"forward": self.CW, "backward": self.CCW}

        try:
            self.GPIO.output(self.MODE, self.RESOLUTION['1/8'])
            self.GPIO.output(self.DIR, direction_dict[direction])

            for _ in range(steps):
                self.GPIO.output(self.STEP, self.GPIO.HIGH)
                sleep(self.delayforward)
                self.GPIO.output(self.STEP, self.GPIO.LOW)
                sleep(self.delaybackward)

            self.GPIO.output(self.STEP, self.GPIO.HIGH)
        except KeyError:
            print("please enter a correct direction")

    # release resource. hack for avoid motor driver board overheating issue
    def __del__(self):
        self.GPIO.cleanup(self.MODE)
