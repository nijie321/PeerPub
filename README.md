# PeerPub 
 Tracking two rats independently during oral operant self-administration of solutions (e.g. sucrose, alcohol, opioids).

## Program Structure

   Main Program: main.py (main_test.py) is the entry program. This program handles session command and rat ID
   scanning, adjusting the pump position, and finally calling the operant.py as a subprocess.
   Note that this program does not exit after calling the subprocess. It it kept alive, as the
   main thread, to record rat's ID when they poke their head near the antenna. Rat's ID are
   stored in _active and _inactive files located in the /home/pi/ directory.
   
   Operant Program: operant.py (operant_test.py) is the program which main invoke at the end of it's executation.
   This program handles saving each data point to corresponding data files.

   Pump Driver Program: pump_move.py is the program that is used, as a higher level abstraction, to drive the stepper motor using underlying gpiozero/RPi.GPIO library. This program mainly consist of the PumpMove class which contains a move() class for "rotating" the motor (forward and backward). The __del__ method need to be call at the end of each use to 'shutoff' the motor. This prevent the motor driver from overheating (there are more efficient ways to do this).
   
   Activity Counter Program: Rat's activity (inactive lick, active lick, and etc) are being represent as an instance of RatActivityCounter.

   PumpCalibration Program: Currently, the motor step size is not accurate enough. The pump's step need to be modified from time to time. This program prompt the user to measure the amount of solution the pump push out and enter that amount. Then the program will automatically re-adjust the step size.
   

## Configuration
   - Files

     - /home/pi/peerpub_config.json
        This file stores 3 information: device ID, session number/ID, and stepper motor step size. (The session number is increament by 1 each time the program start)

     - /home/pi/openbehavior/PeerPub/python/session_configuration.csv
        This file is used by the program to read in the session information. 

     - /home/pi/openbehavior/PeerPub/python/config.py
        This file stores different directory paths. Note that these path are all absolute paths. There's a "get_sessioninfo" function which takes in a argument "sessionid" to retrive session information from "session_configuration.csv" mentioned above. A good practice is to put related configuration functions in this file and import then when needed.

## Utility Scripts

   **check_empty_program.sh**: a script that check the size of every python file in the python/ directory. If one or more files are empty the script then reclone the entire repository.

   **check_network.sh**: a script that check the network connection right after the device boots up and ask user for action when the device was not able to connect to network.

## Program Overview
The main (main_test.py) program is used to read/scan the pre-configured command RFID stored in 'session_configuration.csv' file under python directory. After the command ID is scaned, the program proceed to ask for scanning rat's ID. The time between scanning rat's ID and command ID is the time for adjusting the pump position (e.g. after the rat's ID are scanned, the pump adjustment are disabled to avoid driver board overheating). After the rat's ID are scanned, the main program spawns a new operant (operant_test.py) program by passing in the necessary arguments and run it in the background. Note that because the operant program is a thread, the main program is kept alive (e.g. running in parallel with the operant program). The main program is tasked with reading the rat's ID when they poke their head into the active or inactve spout (disctinguished by the length of characters: 10 for inactive poke and 8 for active poke).

## Parts and GPIO Pin Connections Table

   [DRV8834 Low-Voltage Stepper Motor Driver](https://www.pololu.com/product/2134), [Stepper Motor](https://www.pololu.com/product/2267), [Belker Universal AC Adapter 3-12V](https://www.amazon.com/Belker-Adjustable-Universal-Household-Electronics/dp/B07NKZCWT1/ref=asc_df_B07NKZCWT1/?tag=hyprod-20&linkCode=df0&hvadid=366402536789&hvpos=&hvnetw=g&hvrand=9548953669677245441&hvpone=&hvptwo=&hvqmt=&hvdev=c&hvdvcmdl=&hvlocint=&hvlocphy=9013532&hvtargid=pla-800552094134&psc=1&tag=&ref=&adgrpid=75347436439&hvpone=&hvptwo=&hvadid=366402536789&hvpos=&hvnetw=g&hvrand=9548953669677245441&hvqmt=&hvdev=c&hvdvcmdl=&hvlocint=&hvlocphy=9013532&hvtargid=pla-800552094134)
   | Pins on the driver | GPIO pin slot on the Pi, external power supply, and the stepper motor|
   |--------------------|------------------------|
   |      VMOT         |      **AC Adapter** - positive end of LED Terminal Adapter    |
   |     GND |   **AC Adapter** - negative end of LED Terminal Adapter |
   | B2, B1, A1, A2 |    **Stepper Motor** - Black, Green, Red, and Blue wire respectively      |
   |      GND |    **Pi** - Any GND pin                |
   |      M0, M1 | **Pi** - GPIO 17 and 22       |
   |     SLP | **Pi** - Any 3v3 pin          |
   |      STEP | **Pi** - GPIO 6            |
   |      DIR | **Pi** - GPIO 26 |
   
   [Adafruit 12-Key Capacitive Touch Sensor - MPR121](https://www.adafruit.com/product/1982)
   | Pins on the driver | GPIO pin slot on the Pi and external wires|
   |--------------------|------------------------|
   |  SCL, SDA | **Pi** - GPIO 3 and 2 respectively |
   |  3Vo | **Pi** - Any 3v3 pin|
   |  GND | **Pi** - Any GND pin|
   |  0 | **external wire** - inactive wire|
   |  1 | **external wire** - active wire|
   
   
   [Limit Switch](https://www.amazon.com/MXRS-Hinge-Momentary-Button-Switch/dp/B07MW2RPJY/ref=lp_5739467011_1_7)
   | Pins on the driver | GPIO pin slot on the Pi and external wires|
   |--------------------|------------------------|
   |  Normally Open (NO) | **Pi** - any 5V pin|
   |  Forward Limit - Contact Point (C) | **Pi** - GPIO 24|
   |  Backward Limit - Contact Point (C) | **Pi** - GPIO 23|

   [Push Button](https://www.amazon.com/DAOKI-Miniature-Momentary-Tactile-Quality/dp/B01CGMP9GY/ref=asc_df_B01CGMP9GY/?tag=hyprod-20&linkCode=df0&hvadid=309774137275&hvpos=&hvnetw=g&hvrand=7843520885449353644&hvpone=&hvptwo=&hvqmt=&hvdev=c&hvdvcmdl=&hvlocint=&hvlocphy=9013532&hvtargid=pla-640514760452&psc=1)
   | Pins on the driver | GPIO pin slot on the Pi|
   |--------------------|------------------------|
   | Forward Button | **Pi** - GPIO 5|
   | Backward Button | **Pi** - GPIO 27|
   **Connect resistor and GND correspondingly**
   
   [Pixel Ring](https://www.adafruit.com/product/1643)
   | Pins on the driver | GPIO pin slot on the Pi|
   |--------------------|------------------------|
   | IN | **Pi** - GPIO 18|
   | GND | **Pi** - any GND pin |
   | 5V DC | **Pi** - any 5V pin |

## Resources
   [Raspberry Pi Stepper Motor Tutorial](https://www.rototron.info/raspberry-pi-stepper-motor-tutorial/)  
   [Raspberry Pi Stepper Motor Control with nema17](https://makersportal.com/blog/raspberry-pi-stepper-motor-control-with-nema-17)  
   [OpenSourceSyringePump](http://cavarnon.com/syringepump)  
   [How to Control a stepper motor with DRV8825 driver and Arduino](https://www.makerguides.com/drv8825-stepper-motor-driver-arduino-tutorial/)  
