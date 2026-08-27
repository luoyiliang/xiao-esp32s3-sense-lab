'''!
* @file 02.motion_state_detector.py
* @brief Motion state detection example - Combining any-motion and no-motion detection
* @details This example demonstrates how to use any-motion and no-motion detection simultaneously to determine device motion state:
* @n - INT1: Any-motion detection - Triggers when device starts moving
* @n - INT2: No-motion detection - Triggers when device remains still
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

# I2C address (0x68 if SDO low, 0x69 if high/floating)
BMI323_I2C_ADDR = 0x69

# GPIO pins for interrupts (BCM)
gpio_any_motion = 20
gpio_no_motion = 21

any_motion_flag = False
no_motion_flag = False

STATE_UNKNOWN = 0
STATE_MOVING = 1
STATE_STILL = 2
current_state = STATE_UNKNOWN

sensor = None


def onAnyMotionISR(channel):
  global any_motion_flag
  any_motion_flag = True


def onNoMotionISR(channel):
  global no_motion_flag
  no_motion_flag = True


def setup():
  global sensor

  print("BMI323 Motion State Detector")
  print("============================")
  print("INT1: Any-Motion  | INT2: No-Motion")
  print("Move / stop the board to see state changes.\n")

  sensor = DFRobot_BMI323(bus=1, i2c_addr=BMI323_I2C_ADDR)

  while sensor.begin() != ERR_OK:
    print("IMU init failed, retrying...")
    time.sleep(1)

  sensor.config_accel(eAccelODR_t.eAccelODR50Hz, eAccelRange_t.eAccelRange8G, eAccelMode_t.eAccelModeNormal)

  any_cfg = bmi3_any_motion_config(
    duration=9,
    slope_thres=9,
    acc_ref_up=1,
    hysteresis=5,
    wait_time=4,
  )
  if not sensor.enable_any_motion_int(any_cfg, eInt_t.eINT1, eAxis_t.eAxisXYZ):
    raise RuntimeError("Failed to enable any-motion interrupt!")

  no_cfg = bmi3_no_motion_config(
    duration=9,
    slope_thres=9,
    acc_ref_up=1,
    hysteresis=5,
    wait_time=5,
  )
  if not sensor.enable_no_motion_int(no_cfg, eInt_t.eINT2, eAxis_t.eAxisXYZ):
    raise RuntimeError("Failed to enable no-motion interrupt!")

  GPIO.setwarnings(False)
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(gpio_any_motion, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
  GPIO.setup(gpio_no_motion, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
  GPIO.add_event_detect(gpio_any_motion, GPIO.RISING, callback=onAnyMotionISR)
  GPIO.add_event_detect(gpio_no_motion, GPIO.RISING, callback=onNoMotionISR)

  print("Ready to detect motion state.\n")


def loop():
  global any_motion_flag, no_motion_flag, current_state

  if any_motion_flag:
    any_motion_flag = False
    status = sensor.get_int_status()
    if status & BMI3_INT_STATUS_ANY_MOTION and current_state != STATE_MOVING:
      current_state = STATE_MOVING
      print("[%d ms] I'm moving" % int(time.time() * 1000))

  if no_motion_flag:
    no_motion_flag = False
    status = sensor.get_int_status()
    if status & BMI3_INT_STATUS_NO_MOTION and current_state != STATE_STILL:
      current_state = STATE_STILL
      print("[%d ms] I've stopped" % int(time.time() * 1000))

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
