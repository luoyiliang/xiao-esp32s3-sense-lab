'''!
* @file 09.orientation_interrupt.py
* @brief Demonstrates BMI323 orientation detection interrupt.
* @details Connect INT1 (or INT2) of BMI323 to the MCU pin defined by gpio_interrupt.
* @n When the board changes orientation (portrait/landscape, face up/down), the
* @n interrupt will trigger and the script prints the new state.
* @copyright Copyright (c) 2025 DFRobot Co.Ltd (http://www.dfrobot.com)
* @license The MIT License (MIT)
* @author [Martin](Martin@dfrobot.com)
* @version V1.0.0
* @date 2025-12-08
* @url https://github.com/DFRobot/DFRobot_BMI323
'''

import os
import sys
import time
import RPi.GPIO as GPIO

# Add library path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from DFRobot_BMI323 import *

# I2C address definition (0x68 if SDO is low, 0x69 if SDO is high or floating)
BMI323_I2C_ADDR = 0x69

# GPIO pin for interrupt (BCM mode)
gpio_interrupt = 20

interrupt_flag = False
sensor = None


def onOrientationISR(channel):
  global interrupt_flag
  interrupt_flag = True


def printOrientation(portraitLandscape, faceUpDown):
  if portraitLandscape == BMI3_LANDSCAPE_LEFT:
    print("Landscape Left", end="")
  elif portraitLandscape == BMI3_LANDSCAPE_RIGHT:
    print("Landscape Right", end="")
  elif portraitLandscape == BMI3_PORTRAIT_UP_DOWN:
    print("Portrait Upside Down", end="")
  elif portraitLandscape == BMI3_PORTRAIT_UP_RIGHT:
    print("Portrait Upright", end="")
  else:
    print("Unknown", end="")

  print(" / ", end="")

  if faceUpDown == BMI3_FACE_UP:
    print("Face Up")
  elif faceUpDown == BMI3_FACE_DOWN:
    print("Face Down")
  else:
    print("Unknown Face Orientation")


def setup():
  global sensor

  print("BMI323 Orientation Interrupt Demo")
  print("Rotate the board to see orientation updates.\n")

  sensor = DFRobot_BMI323(bus=1, i2c_addr=BMI323_I2C_ADDR)

  while sensor.begin() != ERR_OK:
    print("IMU init failed, retrying...")
    time.sleep(1)

  sensor.config_accel(eAccelODR_t.eAccelODR50Hz, eAccelRange_t.eAccelRange8G, eAccelMode_t.eAccelModeNormal)

  orientCfg = bmi3_orientation_config(
    ud_en=BMI3_ENABLE,
    hold_time=4,
    hysteresis=5,
    theta=16,
    mode=1,
    slope_thres=30,
    blocking=3,
  )

  if not sensor.enable_orientation_int(orientCfg, eInt_t.eINT1):
    raise RuntimeError("Failed to enable orientation interrupt!")

  GPIO.setwarnings(False)
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(gpio_interrupt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
  GPIO.add_event_detect(gpio_interrupt, GPIO.RISING, callback=onOrientationISR)


def loop():
  global interrupt_flag

  if interrupt_flag:
    interrupt_flag = False

    status = sensor.get_int_status()
    if status & BMI3_INT_STATUS_ORIENTATION:
      pl, fud = sensor.read_orientation()
      if pl is not None and fud is not None:
        print("Orientation: ", end="")
        printOrientation(pl, fud)

  time.sleep(0.01)


if __name__ == "__main__":
  try:
    setup()
    while True:
      loop()
  except KeyboardInterrupt:
    print("\nExit.")
  finally:
    GPIO.cleanup()
