'''!
* @file 04.any_motion_interrupt.py
* @brief Demonstrates BMI323 any-motion (slope) interrupt on INT1/INT2.
* @details Connect INT1/INT2 of BMI323 to the MCU pin defined by gpio_interrupt. Whenever the
* @n sensor detects motion exceeding the configured threshold for the specified
* @n duration, an interrupt will fire and the script will log the event.
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


def onAnyMotionISR(channel):
  global interrupt_flag
  interrupt_flag = True


def setup():
  global sensor

  print("BMI323 Any-Motion Interrupt Demo")
  print("Move the board to trigger an interrupt.\n")

  sensor = DFRobot_BMI323(bus=1, i2c_addr=BMI323_I2C_ADDR)

  while sensor.begin() != ERR_OK:
    print("IMU init failed, retrying...")
    time.sleep(1)

  sensor.config_accel(eAccelODR_t.eAccelODR50Hz, eAccelRange_t.eAccelRange8G, eAccelMode_t.eAccelModeNormal)

  anyMotionCfg = bmi3_any_motion_config(
    duration=9,
    slope_thres=9,
    acc_ref_up=1,
    hysteresis=5,
    wait_time=4,
  )

  if not sensor.enable_any_motion_int(anyMotionCfg, eInt_t.eINT1, eAxis_t.eAxisXYZ):
    raise RuntimeError("Failed to enable any-motion interrupt!")

  GPIO.setwarnings(False)
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(gpio_interrupt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
  GPIO.add_event_detect(gpio_interrupt, GPIO.RISING, callback=onAnyMotionISR)


def loop():
  global interrupt_flag

  if interrupt_flag:
    interrupt_flag = False

    status = sensor.get_int_status()
    if status & BMI3_INT_STATUS_ANY_MOTION:
      print("Any-motion detected at %d ms" % (int(time.time() * 1000)))

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
