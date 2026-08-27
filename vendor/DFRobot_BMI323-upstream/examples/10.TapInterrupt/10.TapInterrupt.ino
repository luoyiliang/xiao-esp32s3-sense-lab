/*!
 * @file 10.TapInterrupt.ino
 * @brief Demonstrates BMI323 tap detection (single/double/triple) interrupt.
 * @details Connect INT1 (or INT2) of BMI323 to the MCU pin defined by intPin.
 * @n Tap the sensor gently to trigger single/double/triple tap events.
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
volatile bool  gTapPending = false;

#if defined(ESP8266)
void IRAM_ATTR interrupt()
#else
void interrupt()
#endif
{
  gTapPending = true;
}

static void printTap(uint8_t mask)
{
  if (mask & BMI3_TAP_DET_STATUS_SINGLE) {
    Serial.println("Single tap detected.");
  }
  if (mask & BMI3_TAP_DET_STATUS_DOUBLE) {
    Serial.println("Double tap detected.");
  }
  if (mask & BMI3_TAP_DET_STATUS_TRIPLE) {
    Serial.println("Triple tap detected.");
  }
  if (mask == 0) {
    Serial.println("Tap interrupt, but no tap flag set.");
  }
}

void setup()
{
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  }

  Serial.println("BMI323 Tap Interrupt Demo");
  Serial.println("Tap the sensor to trigger single/double/triple tap.\n");

  while (!bmi323.begin()) {
    Serial.println("IMU init failed, retrying...");
    delay(1000);
  }

  // Note: If low power mode is selected, ODR must be at least 200Hz
  bmi323.configAccel(bmi323.eAccelODR50Hz, bmi323.eAccelRange8G, bmi323.eAccelModeNormal);

  // Use official example parameter configuration
  struct bmi3_tap_detector_config tapCfg;
  tapCfg.axis_sel                   = 1;    // Use Y-axis
  tapCfg.max_dur_between_peaks      = 5;
  tapCfg.max_gest_dur               = 0x11;
  tapCfg.max_peaks_for_tap          = 5;
  tapCfg.min_quite_dur_between_taps = 7;
  tapCfg.mode                       = 1;    // Normal
  tapCfg.quite_time_after_gest      = 5;
  tapCfg.tap_peak_thres             = 0x2C;
  tapCfg.tap_shock_settling_dur     = 5;
  tapCfg.wait_for_timeout           = 1;    // Gesture confirmation

  if (!bmi323.enableTapInt(tapCfg, bmi323.eINT1)) {
    Serial.println("Failed to enable tap interrupt!");
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
  if (gTapPending) {
    gTapPending = false;

    uint16_t status = bmi323.getIntStatus();
    if (status & BMI3_INT_STATUS_TAP) {
      uint8_t tapMask = 0;
      if (bmi323.readTapStatus(&tapMask)) {
        printTap(tapMask);
      } else {
        Serial.println("Failed to read tap status.");
      }
    }
  }
}
