'''!
* @file 01.six_axis_data.py
* @brief Read 6-axis data (accelerometer + gyroscope) from BMI323
* @details This example demonstrates how to read raw accelerometer and gyroscope data from BMI323 sensor.
* @copyright Copyright (c) 2025 DFRobot Co.Ltd (http://www.dfrobot.com)
* @license The MIT License (MIT)
* @author [Martin](Martin@dfrobot.com)
* @version V1.0.0
* @date 2025-12-08
* @url https://github.com/DFRobot/DFRobot_BMI323
'''

import sys
import os
import time

# Add library path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from DFRobot_BMI323 import *

sensor = None
accel = sSensorData()
gyro = sSensorData()


def setup():
  global sensor

  print("BMI323 Six-Axis Data")
  print("=" * 60)

  BMI323_I2C_ADDR = 0x69
  sensor = DFRobot_BMI323(bus=1, i2c_addr=BMI323_I2C_ADDR)

  print("Initializing sensor...")
  while sensor.begin() != ERR_OK:
    print("Sensor init failed, please check wiring. Retry in 1s.")
    time.sleep(1)

  print("Configuring accelerometer: 50Hz, ±8g, normal mode")
  if not sensor.config_accel(
    eAccelODR_t.eAccelODR50Hz,
    eAccelRange_t.eAccelRange8G,
    eAccelMode_t.eAccelModeNormal,
  ):
    raise RuntimeError("Accel config failed!")

  print("Configuring gyroscope: 800Hz, ±2000dps, normal mode")
  if not sensor.config_gyro(
    eGyroODR_t.eGyroODR800Hz,
    eGyroRange_t.eGyroRange2000DPS,
    eGyroMode_t.eGyroModeNormal,
  ):
    raise RuntimeError("Gyro config failed!")

  time.sleep(1)
  print("Setup complete, streaming data...\n")


def loop():
  if sensor.get_accel_gyro_data(accel, gyro):
    print("Accel (g)  : %8.3f, %8.3f, %8.3f" % (accel.x, accel.y, accel.z))
    print("Gyro (dps) : %8.2f, %8.2f, %8.2f" % (gyro.x, gyro.y, gyro.z))
    print("---")
  else:
    print("Failed to read sensor data.")

  time.sleep(0.2)


if __name__ == "__main__":
  try:
    setup()
    while True:
      loop()
  except KeyboardInterrupt:
    print("\nProgram interrupted by user.")
  except Exception as e:
    print("\nProgram error: %s" % str(e))
    import traceback

    traceback.print_exc()
