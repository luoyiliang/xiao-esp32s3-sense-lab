/*!
 * @file 11.TiltInterrupt.ino
 * @brief Demonstrates BMI323 tilt detection interrupt.
 * @details Connect INT1 (or INT2) of BMI323 to the MCU pin defined by intPin.
 * @n Tilt the board; when the tilt angle exceeds the configured threshold, an
 * @n interrupt fires and the sketch prints a log.
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
volatile bool  gTiltDetected = false;

#if defined(ESP8266)
void IRAM_ATTR interrupt()
#else
void interrupt()
#endif
{
  gTiltDetected = true;
}

void setup()
{
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  }

  Serial.println("BMI323 Tilt Interrupt Demo");
  Serial.println("Tilt the board to trigger the interrupt.\n");

  while (!bmi323.begin()) {
    Serial.println("IMU init failed, retrying...");
    delay(1000);
  }

  bmi323.configAccel(bmi323.eAccelODR50Hz, bmi323.eAccelRange8G, bmi323.eAccelModeNormal);

  // Use official example parameter configuration
  struct bmi3_tilt_config tiltCfg;
  tiltCfg.segment_size   = 90;        // Averaging window (0-255)
  tiltCfg.min_tilt_angle = 200;       // Minimum tilt angle (0-255, value = 256 * cos(angle))
  tiltCfg.beta_acc_mean  = 0x00FF;    // Low-pass smoothing coefficient

  if (!bmi323.enableTiltInt(tiltCfg, bmi323.eINT1)) {
    Serial.println("Failed to enable tilt interrupt!");
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
  if (gTiltDetected) {
    gTiltDetected = false;

    uint16_t status = bmi323.getIntStatus();
    if (status & BMI3_INT_STATUS_TILT) {
      Serial.print("Tilt detected at ");
      Serial.print(millis());
      Serial.println(" ms");
    }
  }
}
