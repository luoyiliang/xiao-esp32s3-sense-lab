'''!
* @file 03.smart_wake_sleep.py
* @brief Smart wake/sleep example - Combining significant motion detection and flat detection
* @details This example demonstrates how to use significant motion detection and flat detection simultaneously to implement smart wake/sleep functionality:
* @n - INT1: Significant motion detection - Wakes when device is picked up or moved
* @n - INT2: Flat detection - Enters sleep mode when device is placed flat on a surface
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
gpio_sig_motion = 20
gpio_flat = 21

# Interrupt flags
sig_motion_flag = False
flat_flag = False

STATE_SLEEP = 0
STATE_AWAKE = 1
device_state = STATE_SLEEP

sensor = None


def onSigMotionISR(channel):
  global sig_motion_flag
  sig_motion_flag = True


def onFlatISR(channel):
  global flat_flag
  flat_flag = True


def setup():
  global sensor

  print("BMI323 Smart Wake/Sleep Demo")
  print("============================")
  print("INT1: Significant Motion (Wake)")
  print("INT2: Flat Detection (Sleep)\n")

  sensor = DFRobot_BMI323(bus=1, i2c_addr=BMI323_I2C_ADDR)

  while sensor.begin() != ERR_OK:
    print("IMU init failed, retrying...")
    time.sleep(1)

  sensor.config_accel(eAccelODR_t.eAccelODR50Hz, eAccelRange_t.eAccelRange8G, eAccelMode_t.eAccelModeNormal)

  sig_cfg = bmi3_sig_motion_config(
    block_size=200,
    peak_2_peak_min=30,
    peak_2_peak_max=30,
    mcr_min=0x10,
    mcr_max=0x10,
  )
  if not sensor.enable_sig_motion_int(sig_cfg, eInt_t.eINT1):
    raise RuntimeError("Failed to enable sig-motion interrupt!")

  flat_cfg = bmi3_flat_config(
    theta=9,
    blocking=3,
    hold_time=50,
    hysteresis=9,
    slope_thres=0xCD,
  )
  if not sensor.enable_flat_int(flat_cfg, eInt_t.eINT2):
    raise RuntimeError("Failed to enable flat interrupt!")

  GPIO.setwarnings(False)
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(gpio_sig_motion, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
  GPIO.setup(gpio_flat, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
  GPIO.add_event_detect(gpio_sig_motion, GPIO.RISING, callback=onSigMotionISR)
  GPIO.add_event_detect(gpio_flat, GPIO.RISING, callback=onFlatISR)

  print("Device starts in SLEEP mode.\n")


def loop():
  global sig_motion_flag, flat_flag, device_state

  if sig_motion_flag:
    sig_motion_flag = False
    status = sensor.get_int_status()
    if status & BMI3_INT_STATUS_SIG_MOTION and device_state == STATE_SLEEP:
      device_state = STATE_AWAKE
      print("[%d ms] >>> Device Woke Up <<<" % int(time.time() * 1000))

  if flat_flag:
    flat_flag = False
    status = sensor.get_int_status()
    if status & BMI3_INT_STATUS_FLAT and device_state == STATE_AWAKE:
      device_state = STATE_SLEEP
      print("[%d ms] >>> Device Entered Sleep Mode <<<" % int(time.time() * 1000))

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
