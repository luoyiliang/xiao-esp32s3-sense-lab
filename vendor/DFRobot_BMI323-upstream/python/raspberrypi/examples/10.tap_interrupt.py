'''!
* @file 10.tap_interrupt.py
* @brief Demonstrates BMI323 tap detection (single/double/triple) interrupt.
* @details Connect INT1 (or INT2) of BMI323 to the MCU pin defined by gpio_interrupt.
* @n Tap the sensor gently to trigger single/double/triple tap events.
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


def onTapISR(channel):
  global interrupt_flag
  interrupt_flag = True


def printTap(mask):
  if mask & BMI3_TAP_DET_STATUS_SINGLE:
    print("Single tap detected.")
  if mask & BMI3_TAP_DET_STATUS_DOUBLE:
    print("Double tap detected.")
  if mask & BMI3_TAP_DET_STATUS_TRIPLE:
    print("Triple tap detected.")
  if mask == 0:
    print("Tap interrupt, but no tap flag set.")


def setup():
  global sensor

  print("BMI323 Tap Interrupt Demo")
  print("Tap the sensor to trigger single/double/triple tap.\n")

  sensor = DFRobot_BMI323(bus=1, i2c_addr=BMI323_I2C_ADDR)

  while sensor.begin() != ERR_OK:
    print("IMU init failed, retrying...")
    time.sleep(1)

  # Note: If low power mode is selected, ODR must be at least 200Hz
  sensor.config_accel(eAccelODR_t.eAccelODR50Hz, eAccelRange_t.eAccelRange8G, eAccelMode_t.eAccelModeNormal)

  tapCfg = bmi3_tap_detector_config(
    axis_sel=1,
    max_dur_between_peaks=5,
    max_gest_dur=0x11,
    max_peaks_for_tap=5,
    min_quite_dur_between_taps=7,
    mode=1,
    quite_time_after_gest=5,
    tap_peak_thres=0x2C,
    tap_shock_settling_dur=5,
    wait_for_timeout=1,
  )

  if not sensor.enable_tap_int(tapCfg, eInt_t.eINT1):
    raise RuntimeError("Failed to enable tap interrupt!")

  GPIO.setwarnings(False)
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(gpio_interrupt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
  GPIO.add_event_detect(gpio_interrupt, GPIO.RISING, callback=onTapISR)


def loop():
  global interrupt_flag

  if interrupt_flag:
    interrupt_flag = False

    status = sensor.get_int_status()
    if status & BMI3_INT_STATUS_TAP:
      tapMask = sensor.read_tap_status()
      if tapMask > 0:
        printTap(tapMask)
      else:
        print("Tap interrupt, but no tap flag set.")

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
