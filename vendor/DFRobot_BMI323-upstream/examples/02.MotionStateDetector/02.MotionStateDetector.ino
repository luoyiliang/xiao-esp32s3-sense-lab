/*!
 * @file 02.MotionStateDetector.ino
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
 */

#include "DFRobot_BMI323.h"

#define BMI323_I2C_ADDR 0x69    // When SDO is pulled low, the I2C address is 0x68

DFRobot_BMI323 bmi323(&Wire, BMI323_I2C_ADDR);

// Interrupt flags
volatile bool gAnyMotionFlag = false;
volatile bool gNoMotionFlag  = false;

// Current motion state
enum MotionState {
  STATE_UNKNOWN,
  STATE_MOVING,
  STATE_STILL
};
MotionState currentState = STATE_UNKNOWN;

#if defined(ESP8266)
void IRAM_ATTR interruptAnyMotion()
#else
void interruptAnyMotion()
#endif
{
  gAnyMotionFlag = true;
}

#if defined(ESP8266)
void IRAM_ATTR interruptNoMotion()
#else
void interruptNoMotion()
#endif
{
  gNoMotionFlag = true;
}

void setup()
{
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  }

  Serial.println("BMI323 Motion State Detector");
  Serial.println("============================");
  Serial.println("INT1: Any-Motion Detection");
  Serial.println("INT2: No-Motion Detection");
  Serial.println("Move the board to see state changes.\n");

  while (!bmi323.begin()) {
    Serial.println("IMU init failed, retrying...");
    delay(1000);
  }

  // Configure accelerometer: 50Hz sampling rate, ±8g range, normal mode
  bmi323.configAccel(bmi323.eAccelODR50Hz, bmi323.eAccelRange8G, bmi323.eAccelModeNormal);

  // Configure any-motion detection (INT1)
  struct bmi3_any_motion_config anyMotionCfg;
  anyMotionCfg.duration    = 9;    // 9 * 20ms = 180ms
  anyMotionCfg.slope_thres = 9;    // 9 * 1.953mg ≈ 17.6mg
  anyMotionCfg.acc_ref_up  = 1;    // Always update reference
  anyMotionCfg.hysteresis  = 5;    // 5 * 1.953mg ≈ 9.8mg
  anyMotionCfg.wait_time   = 4;    // 4 * 20ms = 80ms

  if (!bmi323.enableAnyMotionInt(anyMotionCfg, bmi323.eINT1, bmi323.eAxisXYZ)) {
    Serial.println("Failed to enable any-motion interrupt!");
    while (1) {
      delay(1000);
    }
  }

  // Configure no-motion detection (INT2)
  struct bmi3_no_motion_config noMotionCfg;
  noMotionCfg.duration    = 9;    // 9 * 20ms = 180ms
  noMotionCfg.slope_thres = 9;    // 9 * 1.953mg ≈ 17.6mg
  noMotionCfg.acc_ref_up  = 1;    // Always update reference
  noMotionCfg.hysteresis  = 5;    // 5 * 1.953mg ≈ 9.8mg
  noMotionCfg.wait_time   = 5;    // 5 * 20ms = 100ms

  if (!bmi323.enableNoMotionInt(noMotionCfg, bmi323.eINT2, bmi323.eAxisXYZ)) {
    Serial.println("Failed to enable no-motion interrupt!");
    while (1) {
      delay(1000);
    }
  }

  // Configure INT1 interrupt pin (any-motion)
#if defined(ESP32)
  // D6 pin is used as interrupt pin by default, other non-conflicting pins can also be selected as external interrupt pins.
  attachInterrupt(digitalPinToInterrupt(14 /*D6*/) /* Query the interrupt number of the D6 pin */, interruptAnyMotion, RISING);
#elif defined(ESP8266)
  attachInterrupt(digitalPinToInterrupt(13), interruptAnyMotion, RISING);
#elif defined(ARDUINO_SAM_ZERO)
  // Pin 6 is used as interrupt pin by default, other non-conflicting pins can also be selected as external interrupt pins.
  attachInterrupt(digitalPinToInterrupt(6) /* Query the interrupt number of the 6 pin */, interruptAnyMotion, RISING);
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
  attachInterrupt(/*Interrupt No*/ 0, interruptAnyMotion, RISING);    // Open the external interrupt 0, connect INT1 to the digital pin of the main control:
                                                                      // UNO(2), Mega2560(2), Leonardo(3), microbit(P0).
#endif

  // Configure INT2 interrupt pin (no-motion detection)
#if defined(ESP32)
  attachInterrupt(digitalPinToInterrupt(13 /*D7*/), interruptNoMotion, RISING);
#elif defined(ESP8266)
  attachInterrupt(digitalPinToInterrupt(15), interruptNoMotion, RISING);
#elif defined(ARDUINO_SAM_ZERO)
  attachInterrupt(digitalPinToInterrupt(7), interruptNoMotion, RISING);
#else
  attachInterrupt(/*Interrupt No*/ 1, interruptNoMotion, RISING);
#endif

  Serial.println("Ready to detect motion state!\n");
}

void loop()
{
  // Handle any-motion interrupt
  if (gAnyMotionFlag) {
    gAnyMotionFlag  = false;
    uint16_t status = bmi323.getIntStatus();
    if (status & BMI3_INT_STATUS_ANY_MOTION) {
      if (currentState != STATE_MOVING) {
        currentState = STATE_MOVING;
        Serial.print("[");
        Serial.print(millis());
        Serial.print("] ");
        Serial.println("I'm moving");
      }
    }
  }

  // Handle no-motion interrupt
  if (gNoMotionFlag) {
    gNoMotionFlag   = false;
    uint16_t status = bmi323.getIntStatus();
    if (status & BMI3_INT_STATUS_NO_MOTION) {
      if (currentState != STATE_STILL) {
        currentState = STATE_STILL;
        Serial.print("[");
        Serial.print(millis());
        Serial.print("] ");
        Serial.println("I've stopped");
      }
    }
  }
}
