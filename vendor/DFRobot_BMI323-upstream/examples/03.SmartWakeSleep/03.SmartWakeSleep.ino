/*!
 * @file 03.SmartWakeSleep.ino
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
 */

#include "DFRobot_BMI323.h"

#define BMI323_I2C_ADDR 0x69    // When SDO is pulled low, the I2C address is 0x68

DFRobot_BMI323 bmi323(&Wire, BMI323_I2C_ADDR);

// Interrupt flags
volatile bool gSigMotionFlag = false;
volatile bool gFlatFlag      = false;

// Device state
enum DeviceState {
  STATE_SLEEP,
  STATE_AWAKE
};
DeviceState deviceState = STATE_SLEEP;

#if defined(ESP8266)
void IRAM_ATTR interruptSigMotion()
#else
void interruptSigMotion()
#endif
{
  gSigMotionFlag = true;
}

#if defined(ESP8266)
void IRAM_ATTR interruptFlat()
#else
void interruptFlat()
#endif
{
  gFlatFlag = true;
}

void setup()
{
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  }

  Serial.println("BMI323 Smart Wake/Sleep Demo");
  Serial.println("============================");
  Serial.println("INT1: Significant Motion (Wake)");
  Serial.println("INT2: Flat Detection (Sleep)");
  Serial.println("\nPick up the board to wake, place flat to sleep.\n");

  while (!bmi323.begin()) {
    Serial.println("IMU init failed, retrying...");
    delay(1000);
  }

  // Configure accelerometer: 50Hz sampling rate, ±8g range, normal mode
  bmi323.configAccel(bmi323.eAccelODR50Hz, bmi323.eAccelRange8G, bmi323.eAccelModeNormal);

  // Configure significant motion detection (INT1) - for wake
  struct bmi3_sig_motion_config sigMotionCfg;
  sigMotionCfg.block_size      = 200;
  sigMotionCfg.peak_2_peak_min = 30;
  sigMotionCfg.peak_2_peak_max = 30;
  sigMotionCfg.mcr_min         = 0x10;    // 16
  sigMotionCfg.mcr_max         = 0x10;    // 16

  if (!bmi323.enableSigMotionInt(sigMotionCfg, bmi323.eINT1)) {
    Serial.println("Failed to enable sig-motion interrupt!");
    while (1) {
      delay(1000);
    }
  }

  // Configure flat detection (INT2) - for sleep
  struct bmi3_flat_config flatCfg;
  flatCfg.theta       = 9;       // Max tilt angle
  flatCfg.blocking    = 3;       // Blocking mode
  flatCfg.hold_time   = 50;      // 50 * 20ms = 1000ms
  flatCfg.hysteresis  = 9;       // Hysteresis
  flatCfg.slope_thres = 0xCD;    // Slope threshold

  if (!bmi323.enableFlatInt(flatCfg, bmi323.eINT2)) {
    Serial.println("Failed to enable flat interrupt!");
    while (1) {
      delay(1000);
    }
  }

  // Configure INT1 interrupt pin (significant motion)
#if defined(ESP32)
  // D6 pin is used as interrupt pin by default, other non-conflicting pins can also be selected as external interrupt pins.
  attachInterrupt(digitalPinToInterrupt(14 /*D6*/) /* Query the interrupt number of the D6 pin */, interruptSigMotion, RISING);
#elif defined(ESP8266)
  attachInterrupt(digitalPinToInterrupt(13), interruptSigMotion, RISING);
#elif defined(ARDUINO_SAM_ZERO)
  // Pin 6 is used as interrupt pin by default, other non-conflicting pins can also be selected as external interrupt pins.
  attachInterrupt(digitalPinToInterrupt(6) /* Query the interrupt number of the 6 pin */, interruptSigMotion, RISING);
#else
  /* The Correspondence Table of AVR Series Arduino Interrupt Pins And Terminal Numbers
     * ---------------------------------------------------------------------------------------
     * |                                        |  DigitalPin  | 2  | 3  |                   |
     * |    Uno, Nano, Mini, other 328-based    |--------------------------------------------|
     * |                                        | Interrupt No | 0  | 1  |                   |
     * |-------------------------------------------------------------------------------------|
     * |                                        |    Pin       | 2  | 3  | 21 | 20 | 19 | 18 |
     * |               Mega2560                 |--------------------------------------------|
     * |                                        | Interrupt No | 0  | 1  | 2  | 3  | 4  | 5  |
     * |-------------------------------------------------------------------------------------|
     * |                                        |    Pin       | 3  | 2  | 0  | 1  | 7  |    |
     * |    Leonardo, other 32u4-based          |--------------------------------------------|
     * |                                        | Interrupt No | 0  | 1  | 2  | 3  | 4  |    |
     * |--------------------------------------------------------------------------------------
     * ---------------------------------------------------------------------------------------------------------------------------------------------
     *                      The Correspondence Table of micro:bit Interrupt Pins And Terminal Numbers
     * ---------------------------------------------------------------------------------------------------------------------------------------------
     * |             micro:bit                       | DigitalPin |P0-P20 can be used as an external interrupt                                     |
     * |  (When using as an external interrupt,      |---------------------------------------------------------------------------------------------|
     * |no need to set it to input mode with pinMode)|Interrupt No|Interrupt number is a pin digital value, such as P0 interrupt number 0, P1 is 1 |
     * |-------------------------------------------------------------------------------------------------------------------------------------------|
     */
  attachInterrupt(/*Interrupt No*/ 0, interruptSigMotion, RISING);    // Open the external interrupt 0, connect INT1 to the digital pin of the main control:
                                                                      // UNO(2), Mega2560(2), Leonardo(3), microbit(P0).
#endif

  // Configure INT2 interrupt pin (flat detection)
#if defined(ESP32)
  attachInterrupt(digitalPinToInterrupt(13 /*D7*/), interruptFlat, RISING);
#elif defined(ESP8266)
  attachInterrupt(digitalPinToInterrupt(15), interruptFlat, RISING);
#elif defined(ARDUINO_SAM_ZERO)
  attachInterrupt(digitalPinToInterrupt(7), interruptFlat, RISING);
#else
  attachInterrupt(/*Interrupt No*/ 1, interruptFlat, RISING);
#endif

  Serial.println("Device starts in SLEEP mode.\n");
}

void loop()
{
  // Handle significant motion interrupt (wake)
  if (gSigMotionFlag) {
    gSigMotionFlag  = false;
    uint16_t status = bmi323.getIntStatus();
    if (status & BMI3_INT_STATUS_SIG_MOTION) {
      if (deviceState == STATE_SLEEP) {
        deviceState = STATE_AWAKE;
        Serial.print("[");
        Serial.print(millis());
        Serial.print("] ");
        Serial.println(">>> Device Woke Up <<<");
        // Here you can add actual wake operations, such as turning on screen, starting sensors, etc.
      }
    }
  }

  // Handle flat detection interrupt (sleep)
  if (gFlatFlag) {
    gFlatFlag       = false;
    uint16_t status = bmi323.getIntStatus();
    if (status & BMI3_INT_STATUS_FLAT) {
      if (deviceState == STATE_AWAKE) {
        deviceState = STATE_SLEEP;
        Serial.print("[");
        Serial.print(millis());
        Serial.print("] ");
        Serial.println(">>> Device Entered Sleep Mode <<<");
        // Here you can add actual sleep operations, such as turning off screen, reducing power consumption, etc.
      }
    }
  }

  // In awake state, can perform other tasks
  if (deviceState == STATE_AWAKE) {
    // For example: read sensor data, update display, etc.
    // delay(100); // Avoid too frequent operations
  }
}
