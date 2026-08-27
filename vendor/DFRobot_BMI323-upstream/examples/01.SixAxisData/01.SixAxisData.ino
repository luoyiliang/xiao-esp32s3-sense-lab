/*!
 * @file 01.SixAxisData.ino
 * @brief Read 6-axis data (accelerometer + gyroscope) from BMI323
 * @details This example demonstrates how to read raw accelerometer and gyroscope data from BMI323 sensor.
 * @copyright Copyright (c) 2025 DFRobot Co.Ltd (http://www.dfrobot.com)
 * @license The MIT License (MIT)
 * @author [Martin](Martin@dfrobot.com)
 * @version V1.0.0
 * @date 2025-12-08
 * @url https://github.com/DFRobot/DFRobot_BMI323
 */

#include "DFRobot_BMI323.h"

#define BMI323_I2C_ADDR 0x69    // When SDO is pulled low, the I2C address is 0x68

DFRobot_BMI323 bmi323(&Wire, BMI323_I2C_ADDR);

void setup()
{
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  }

  Serial.println("BMI323 Six-Axis Data");
  Serial.println("====================");

  while (!bmi323.begin()) {
    Serial.println("Sensor init failed, please check wiring. Retry in 1s.");
    delay(1000);
  }

  if (!bmi323.configAccel(bmi323.eAccelODR50Hz, bmi323.eAccelRange8G, bmi323.eAccelModeNormal)) {
    Serial.println("Accel config failed!");
    while (1) {
      delay(1000);
    }
  }

  if (!bmi323.configGyro(bmi323.eGyroODR800Hz, bmi323.eGyroRange2000DPS, bmi323.eGyroModeNormal)) {
    Serial.println("Gyro config failed!");
    while (1) {
      delay(1000);
    }
  }

  delay(1000);
  Serial.println("Setup complete!\n");
}

void loop()
{
  DFRobot_BMI323::sSensorData accel;
  DFRobot_BMI323::sSensorData gyro;

  if (bmi323.getAccelGyroData(&accel, &gyro)) {
    Serial.print("Accel (g)  : ");
    Serial.print(accel.x, 3);
    Serial.print(", ");
    Serial.print(accel.y, 3);
    Serial.print(", ");
    Serial.println(accel.z, 3);

    Serial.print("Gyro (dps) : ");
    Serial.print(gyro.x, 2);
    Serial.print(", ");
    Serial.print(gyro.y, 2);
    Serial.print(", ");
    Serial.println(gyro.z, 2);
    Serial.println("---");
  } else {
    Serial.println("Failed to read sensor data.");
  }

  delay(200);
}
