'''!
* @file 07.step_counter.py
* @brief Simple BMI323 pedometer example
* @details The BMI323 integrates a hardware step counter. This script shows how to
* @n enable the feature and poll the accumulated step count once per second.
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


def onStepInterrupt(channel):
  global interrupt_flag
  interrupt_flag = True


def setup():
  global sensor

  print("BMI323 Step Counter Demo")
  print("========================")

  sensor = DFRobot_BMI323(bus=1, i2c_addr=BMI323_I2C_ADDR)

  while sensor.begin() != ERR_OK:
    print("I2C init failed, retry in 1s")
    time.sleep(1)

  # Note: If low power mode is selected, ODR must be at least 50Hz
  sensor.config_accel(eAccelODR_t.eAccelODR50Hz, eAccelRange_t.eAccelRange8G, eAccelMode_t.eAccelModeNormal)

  if not sensor.enable_step_counter_int(eInt_t.eINT1):
    raise RuntimeError("Enable step counter interrupt failed!")

  GPIO.setwarnings(False)
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(gpio_interrupt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
  GPIO.add_event_detect(gpio_interrupt, GPIO.RISING, callback=onStepInterrupt)

  print("Connect BMI323 INT1 to the defined MCU pin.")
  print("Every step will trigger an interrupt and update the counter.\n")


def loop():
  global interrupt_flag

  if interrupt_flag:
    interrupt_flag = False

    status = sensor.get_int_status()
    if status & BMI3_INT_STATUS_STEP_DETECTOR:
      steps = sensor.read_step_counter()
      if steps > 0:
        print("Steps: %d" % steps)

  time.sleep(0.05)


if __name__ == "__main__":
  try:
    setup()
    while True:
      loop()
  except KeyboardInterrupt:
    print("\nExit.")
  finally:
    GPIO.cleanup()
