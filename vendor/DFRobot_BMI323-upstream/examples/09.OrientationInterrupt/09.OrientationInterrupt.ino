/*!
 * @file 09.OrientationInterrupt.ino
 * @brief Demonstrates BMI323 orientation detection interrupt.
 * @details Connect INT1 (or INT2) of BMI323 to the MCU pin defined by intPin.
 * @n When the board changes orientation (portrait/landscape, face up/down), the
 * @n interrupt will trigger and the sketch prints the new state.
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
volatile bool  gOrientationChanged = false;

#if defined(ESP8266)
void IRAM_ATTR interrupt()
#else
void interrupt()
#endif
{
  gOrientationChanged = true;
}

static void printOrientation(uint8_t portraitLandscape, uint8_t faceUpDown)
{
  switch (portraitLandscape) {
    case BMI3_LANDSCAPE_LEFT:
      Serial.print("Landscape Left");
      break;
    case BMI3_LANDSCAPE_RIGHT:
      Serial.print("Landscape Right");
      break;
    case BMI3_PORTRAIT_UP_DOWN:
      Serial.print("Portrait Upside Down");
      break;
    case BMI3_PORTRAIT_UP_RIGHT:
      Serial.print("Portrait Upright");
      break;
    default:
      Serial.print("Unknown");
      break;
  }

  Serial.print(" / ");

  if (faceUpDown == BMI3_FACE_UP) {
    Serial.println("Face Up");
  } else if (faceUpDown == BMI3_FACE_DOWN) {
    Serial.println("Face Down");
  } else {
    Serial.println("Unknown Face Orientation");
  }
}

void setup()
{
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  }

  Serial.println("BMI323 Orientation Interrupt Demo");
  Serial.println("Rotate the board to see orientation updates.\n");

  while (!bmi323.begin()) {
    Serial.println("IMU init failed, retrying...");
    delay(1000);
  }

  bmi323.configAccel(bmi323.eAccelODR50Hz, bmi323.eAccelRange8G, bmi323.eAccelModeNormal);

  // Use official example parameter configuration
  struct bmi3_orientation_config orientCfg;
  orientCfg.ud_en       = BMI3_ENABLE;    // Enable face up/down detection
  orientCfg.hold_time   = 4;              // 4 * 20ms = 80ms
  orientCfg.hysteresis  = 5;              // Accel hysteresis
  orientCfg.theta       = 16;             // Max tilt angle
  orientCfg.mode        = 1;              // High-asymmetrical
  orientCfg.slope_thres = 30;             // Slope threshold
  orientCfg.blocking    = 3;              // Block when movement is large

  if (!bmi323.enableOrientationInt(orientCfg, bmi323.eINT1)) {
    Serial.println("Failed to enable orientation interrupt!");
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
  if (gOrientationChanged) {
    gOrientationChanged = false;

    uint16_t status = bmi323.getIntStatus();
    if (status & BMI3_INT_STATUS_ORIENTATION) {
      uint8_t pl  = 0;
      uint8_t fud = 0;
      if (bmi323.readOrientation(&pl, &fud)) {
        Serial.print("Orientation: ");
        printOrientation(pl, fud);
      } else {
        Serial.println("Failed to read orientation data.");
      }
    }
  }
}
