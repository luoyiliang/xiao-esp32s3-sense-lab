#include <Wire.h>
#include "DFRobot_BMI323.h"

static constexpr uint8_t SDA_PIN = 5;
static constexpr uint8_t SCL_PIN = 6;
static constexpr uint8_t ADDR_LOW = 0x68;
static constexpr uint8_t ADDR_HIGH = 0x69;

DFRobot_BMI323 imuLow(&Wire, ADDR_LOW);
DFRobot_BMI323 imuHigh(&Wire, ADDR_HIGH);

static bool initOne(DFRobot_BMI323 &imu, uint8_t address) {
  Serial.printf("INIT 0x%02X\n", address);
  if (!imu.begin()) {
    Serial.printf("CHIP_FAIL 0x%02X\n", address);
    return false;
  }
  if (!imu.configAccel(imu.eAccelODR50Hz, imu.eAccelRange8G, imu.eAccelModeNormal)) {
    Serial.printf("ACCEL_CONFIG_FAIL 0x%02X\n", address);
    return false;
  }
  if (!imu.configGyro(imu.eGyroODR50Hz, imu.eGyroRange500DPS, imu.eGyroModeNormal)) {
    Serial.printf("GYRO_CONFIG_FAIL 0x%02X\n", address);
    return false;
  }
  Serial.printf("BMI323_OK 0x%02X\n", address);
  return true;
}

void setup() {
  Serial.begin(115200);
  delay(1200);
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000);
  Serial.println("READY BMI323_DUAL SDA=GPIO5 SCL=GPIO6");

  bool lowOk = initOne(imuLow, ADDR_LOW);
  bool highOk = initOne(imuHigh, ADDR_HIGH);
  Serial.printf("SETUP low=%s high=%s\n", lowOk ? "OK" : "FAIL", highOk ? "OK" : "FAIL");
}

void loop() {
  DFRobot_BMI323::sSensorData accelLow, gyroLow;
  DFRobot_BMI323::sSensorData accelHigh, gyroHigh;
  bool lowRead = imuLow.getAccelGyroData(&accelLow, &gyroLow);
  bool highRead = imuHigh.getAccelGyroData(&accelHigh, &gyroHigh);

  if (lowRead) {
    Serial.printf("DATA 0x%02X A %.3f %.3f %.3f G %.2f %.2f %.2f T %.2f\n",
                  ADDR_LOW, accelLow.x, accelLow.y, accelLow.z,
                  gyroLow.x, gyroLow.y, gyroLow.z, imuLow.getTemperature());
  } else {
    Serial.printf("READ_FAIL 0x%02X\n", ADDR_LOW);
  }
  if (highRead) {
    Serial.printf("DATA 0x%02X A %.3f %.3f %.3f G %.2f %.2f %.2f T %.2f\n",
                  ADDR_HIGH, accelHigh.x, accelHigh.y, accelHigh.z,
                  gyroHigh.x, gyroHigh.y, gyroHigh.z, imuHigh.getTemperature());
  } else {
    Serial.printf("READ_FAIL 0x%02X\n", ADDR_HIGH);
  }
  delay(200);
}
