/*!
 * @file 05.NoMotionInterrupt.ino
 * @brief Demonstrates BMI323 no-motion (stillness) interrupt.
 * @details Connect INT1 (or INT2) of BMI323 to the MCU pin defined by intPin.
 * @n When the board remains still (below the configured threshold) for the
 * @n specified duration, the interrupt will trigger and the sketch prints a log.
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
volatile bool  gNoMotionDetected = false;

#if defined(ESP8266)
void IRAM_ATTR interrupt()
#else
void interrupt()
#endif
{
  gNoMotionDetected = true;
}

void setup()
{
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  }

  Serial.println("BMI323 No-Motion Interrupt Demo");
  Serial.println("Keep the board still to trigger no-motion.\n");

  while (!bmi323.begin()) {
    Serial.println("IMU init failed, retrying...");
    delay(1000);
  }

  bmi323.configAccel(bmi323.eAccelODR50Hz, bmi323.eAccelRange8G, bmi323.eAccelModeNormal);

  // Use official example parameter configuration
  // Structure field order: duration, slope_thres, acc_ref_up, hysteresis, wait_time
  struct bmi3_no_motion_config noMotionCfg;
  noMotionCfg.duration    = 9;    // 9 * 20ms = 180ms
  noMotionCfg.slope_thres = 9;    // 9 * 1.953mg ≈ 17.6mg
  noMotionCfg.acc_ref_up  = 1;    // Always update reference
  noMotionCfg.hysteresis  = 5;    // 5 * 1.953mg ≈ 9.8mg
  noMotionCfg.wait_time   = 5;    // 5 * 20ms = 100ms

  if (!bmi323.enableNoMotionInt(noMotionCfg, bmi323.eINT1, bmi323.eAxisXYZ)) {
    Serial.println("Failed to enable no-motion interrupt!");
    while (1) {
      delay(1000);
    }
  }

#if defined(ESP32)
  // D6 pin is used as interrupt pin by default, other non-conflicting pins can also be selected as external interrupt pins.
  attachInterrupt(digitalPinToInterrupt(14 /*D6*/) /* Query the interrupt number of the D6 pin */, interrupt, RISING);
#elif defined(ESP8266)
  attachInterrupt(digitalPinToInterrupt(13), interrupt, RISING);
#elif defined(ARDUINO_SAM_ZERO)
  // Pin 6 is used as interrupt pin by default, other non-conflicting pins can also be selected as external interrupt pins.
  attachInterrupt(digitalPinToInterrupt(6) /* Query the interrupt number of the 6 pin */, interrupt, RISING);
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
  attachInterrupt(/*Interrupt No*/ 0, interrupt, RISING);    // Open the external interrupt 0, connect INT1/2 to the digital pin of the main control:
                                                             // UNO(2), Mega2560(2), Leonardo(3), microbit(P0).
#endif
}

void loop()
{
  if (gNoMotionDetected) {
    gNoMotionDetected = false;

    uint16_t status = bmi323.getIntStatus();
    if (status & BMI3_INT_STATUS_NO_MOTION) {
      Serial.print("No-motion detected at ");
      Serial.print(millis());
      Serial.println(" ms");
    }
  }
}
