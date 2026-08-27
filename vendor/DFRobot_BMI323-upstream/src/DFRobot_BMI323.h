/*!
 * @file DFRobot_BMI323.h
 * @brief Define the basic structure of DFRobot_BMI323 class
 * @details This is a 6-axis IMU sensor (accelerometer + gyroscope) that can be controlled via I2C interface.
 * @n BMI323 features multiple motion detection capabilities, such as step counter, any-motion detection, no-motion detection, tap detection, etc.
 * @n These features make BMI323 sensor very useful in wearable devices, smart devices and other applications.
 * @n BMI323 also has interrupt pins that can be used in an energy-efficient manner without software algorithms.
 * @copyright Copyright (c) 2025 DFRobot Co.Ltd (http://www.dfrobot.com)
 * @license The MIT License (MIT)
 * @author [Martin](Martin@dfrobot.com)
 * @version V1.0.0
 * @date 2025-12-08
 * @url https://github.com/DFRobot/DFRobot_BMI323
 */
#ifndef __DFRobot_BMI323_H
#define __DFRobot_BMI323_H

#include "Arduino.h"
#include "Wire.h"
#include "bmi323.h"
#include "stdint.h"

class DFRobot_BMI323 {
public:
  /**
   * @enum eAccelRange_t
   * @brief Accelerometer range enumeration
   * @details Define the measurement range of accelerometer, unit: g (gravity acceleration)
   */
  typedef enum {
    eAccelRange2G  = BMI3_ACC_RANGE_2G,    ///< ±2g range
    eAccelRange4G  = BMI3_ACC_RANGE_4G,    ///< ±4g range
    eAccelRange8G  = BMI3_ACC_RANGE_8G,    ///< ±8g range
    eAccelRange16G = BMI3_ACC_RANGE_16G    ///< ±16g range
  } eAccelRange_t;

  /**
   * @enum eGyroRange_t
   * @brief Gyroscope range enumeration
   * @details Define the measurement range of gyroscope, unit: dps (degrees per second)
   */
  typedef enum {
    eGyroRange125DPS  = BMI3_GYR_RANGE_125DPS,     ///< ±125dps range
    eGyroRange250DPS  = BMI3_GYR_RANGE_250DPS,     ///< ±250dps range
    eGyroRange500DPS  = BMI3_GYR_RANGE_500DPS,     ///< ±500dps range
    eGyroRange1000DPS = BMI3_GYR_RANGE_1000DPS,    ///< ±1000dps range
    eGyroRange2000DPS = BMI3_GYR_RANGE_2000DPS     ///< ±2000dps range
  } eGyroRange_t;

  /**
   * @enum eAccelODR_t
   * @brief Accelerometer output data rate enumeration
   * @details Define the sampling frequency of accelerometer, unit: Hz
   * @note Values are defined based on 0x00U
   */
  typedef enum {
    eAccelODR0_78125Hz = BMI3_ACC_ODR_0_78HZ,     ///< 0.78125 Hz
    eAccelODR1_5625Hz  = BMI3_ACC_ODR_1_56HZ,     ///< 1.5625 Hz
    eAccelODR3_125Hz   = BMI3_ACC_ODR_3_125HZ,    ///< 3.125 Hz
    eAccelODR6_25Hz    = BMI3_ACC_ODR_6_25HZ,     ///< 6.25 Hz
    eAccelODR12_5Hz    = BMI3_ACC_ODR_12_5HZ,     ///< 12.5 Hz
    eAccelODR25Hz      = BMI3_ACC_ODR_25HZ,       ///< 25 Hz
    eAccelODR50Hz      = BMI3_ACC_ODR_50HZ,       ///< 50 Hz
    eAccelODR100Hz     = BMI3_ACC_ODR_100HZ,      ///< 100 Hz
    eAccelODR200Hz     = BMI3_ACC_ODR_200HZ,      ///< 200 Hz
    eAccelODR400Hz     = BMI3_ACC_ODR_400HZ,      ///< 400 Hz
    eAccelODR800Hz     = BMI3_ACC_ODR_800HZ,      ///< 800 Hz
    eAccelODR1600Hz    = BMI3_ACC_ODR_1600HZ,     ///< 1600 Hz
    eAccelODR3200Hz    = BMI3_ACC_ODR_3200HZ,     ///< 3200 Hz
    eAccelODR6400Hz    = BMI3_ACC_ODR_6400HZ      ///< 6400 Hz
  } eAccelODR_t;

  /**
   * @enum eGyroODR_t
   * @brief Gyroscope output data rate enumeration
   * @details Define the sampling frequency of gyroscope, unit: Hz
   * @note Values are defined based on 0x00U
   */
  typedef enum {
    eGyroODR0_78125Hz = BMI3_GYR_ODR_0_78HZ,     ///< 0.78125 Hz
    eGyroODR1_5625Hz  = BMI3_GYR_ODR_1_56HZ,     ///< 1.5625 Hz
    eGyroODR3_125Hz   = BMI3_GYR_ODR_3_125HZ,    ///< 3.125 Hz
    eGyroODR6_25Hz    = BMI3_GYR_ODR_6_25HZ,     ///< 6.25 Hz
    eGyroODR12_5Hz    = BMI3_GYR_ODR_12_5HZ,     ///< 12.5 Hz
    eGyroODR25Hz      = BMI3_GYR_ODR_25HZ,       ///< 25 Hz
    eGyroODR50Hz      = BMI3_GYR_ODR_50HZ,       ///< 50 Hz
    eGyroODR100Hz     = BMI3_GYR_ODR_100HZ,      ///< 100 Hz
    eGyroODR200Hz     = BMI3_GYR_ODR_200HZ,      ///< 200 Hz
    eGyroODR400Hz     = BMI3_GYR_ODR_400HZ,      ///< 400 Hz
    eGyroODR800Hz     = BMI3_GYR_ODR_800HZ,      ///< 800 Hz
    eGyroODR1600Hz    = BMI3_GYR_ODR_1600HZ,     ///< 1600 Hz
    eGyroODR3200Hz    = BMI3_GYR_ODR_3200HZ,     ///< 3200 Hz
    eGyroODR6400Hz    = BMI3_GYR_ODR_6400HZ      ///< 6400 Hz
  } eGyroODR_t;

  /**
   * @enum eAccelMode_t
   * @brief Accelerometer operating mode enumeration
   * @details Define the operating mode of accelerometer, affects power consumption and performance
   */
  typedef enum {
    eAccelModeLowPower = BMI3_ACC_MODE_LOW_PWR,     ///< Low power mode
    eAccelModeNormal   = BMI3_ACC_MODE_NORMAL,      ///< Normal mode
    eAccelModeHighPerf = BMI3_ACC_MODE_HIGH_PERF    ///< High performance mode
  } eAccelMode_t;

  /**
   * @enum eGyroMode_t
   * @brief Gyroscope operating mode enumeration
   * @details Define the operating mode of gyroscope, affects power consumption and performance
   */
  typedef enum {
    eGyroModeLowPower = BMI3_GYR_MODE_LOW_PWR,     ///< Low power mode
    eGyroModeNormal   = BMI3_GYR_MODE_NORMAL,      ///< Normal mode
    eGyroModeHighPerf = BMI3_GYR_MODE_HIGH_PERF    ///< High performance mode
  } eGyroMode_t;

  /**
   * @fn  eInt_t
   * @brief  Interrupt pin selection
   */
  typedef enum {
    eINT1 = BMI3_INT1, /**<int1 >*/
    eINT2 = BMI3_INT2  /**<int2>*/
  } eInt_t;

  /**
   * @enum eAxis_t
   * @brief Axis selection mask
   */
  typedef enum {
    eAxisX   = 0x01,    ///< X axis
    eAxisY   = 0x02,    ///< Y axis
    eAxisZ   = 0x04,    ///< Z axis
    eAxisXYZ = 0x07     ///< All XYZ axes
  } eAxis_t;

  /**
   * @struct sSensorData
   * @brief Sensor data structure
   * @details Used to store three-axis sensor data (X, Y, Z axes)
   */
  typedef struct {
    float x;    ///< X axis data
    float y;    ///< Y axis data
    float z;    ///< Z axis data
  } sSensorData;
  /**
   * @fn DFRobot_BMI323
   * @brief Constructor
   * @details Constructor - I2C interface
   * @param wire TwoWire object pointer, default &Wire
   * @param i2cAddr I2C address, default 0x69
   * @return None
   */
  DFRobot_BMI323(TwoWire *wire = &Wire, uint8_t i2cAddr = 0x69);
  ~DFRobot_BMI323();

  /**
   * @fn begin
   * @brief Initialization function
   * @details Initialize I2C interface, chip registers and feature context
   * @param None
   * @return bool type, indicates the initialization status
   * @retval true Initialization successful
   * @retval false Initialization failed
   */
  bool begin(void);

  /**
   * @fn configAccel
   * @brief Configure accelerometer
   * @param odr Output data rate selection (see: eAccelODR_t)
   * @n Available rates:
   * @n - eAccelODR0_78125Hz:  0.78125 Hz
   * @n - eAccelODR1_5625Hz:   1.5625 Hz
   * @n - eAccelODR3_125Hz:    3.125 Hz
   * @n - eAccelODR6_25Hz:     6.25 Hz
   * @n - eAccelODR12_5Hz:     12.5 Hz
   * @n - eAccelODR25Hz:       25 Hz
   * @n - eAccelODR50Hz:       50 Hz
   * @n - eAccelODR100Hz:      100 Hz
   * @n - eAccelODR200Hz:      200 Hz
   * @n - eAccelODR400Hz:      400 Hz
   * @n - eAccelODR800Hz:      800 Hz
   * @n - eAccelODR1600Hz:     1600 Hz
   * @n - eAccelODR3200Hz:     3200 Hz
   * @n - eAccelODR6400Hz:     6400 Hz
   * @n @note ODR range limitations (based on operating mode):
   * @n - Low power mode: 0.78Hz ~ 400Hz
   * @n - Normal mode:    12.5Hz ~ 6400Hz
   * @n - High performance mode: 12.5Hz ~ 6400Hz
   * @param range Range selection (see: eAccelRange_t)
   * @n Available ranges:
   * @n - eAccelRange2G:   ±2g
   * @n - eAccelRange4G:   ±4g
   * @n - eAccelRange8G:   ±8g
   * @n - eAccelRange16G:  ±16g
   * @param mode Operating mode selection (see: eAccelMode_t), default eAccelModeNormal
   * @n Available modes:
   * @n - eAccelModeLowPower:  Low power mode
   * @n - eAccelModeNormal:    Normal mode (default)
   * @n - eAccelModeHighPerf:  High performance mode
   * @return bool type, indicates the configuration status
   * @retval true Configuration successful
   * @retval false Configuration failed
   */
  bool configAccel(eAccelODR_t odr, eAccelRange_t range, eAccelMode_t mode = eAccelModeNormal);

  /**
   * @fn configGyro
   * @brief Configure gyroscope
   * @param odr Output data rate selection (see: eGyroODR_t)
   * @n Available rates:
   * @n - eGyroODR0_78125Hz: 0.78125 Hz
   * @n - eGyroODR1_5625Hz:  1.5625 Hz
   * @n - eGyroODR3_125Hz:   3.125 Hz
   * @n - eGyroODR6_25Hz:    6.25 Hz
   * @n - eGyroODR12_5Hz:    12.5 Hz
   * @n - eGyroODR25Hz:      25 Hz
   * @n - eGyroODR50Hz:      50 Hz
   * @n - eGyroODR100Hz:     100 Hz
   * @n - eGyroODR200Hz:     200 Hz
   * @n - eGyroODR400Hz:     400 Hz
   * @n - eGyroODR800Hz:     800 Hz
   * @n - eGyroODR1600Hz:    1600 Hz
   * @n - eGyroODR3200Hz:    3200 Hz
   * @n - eGyroODR6400Hz:    6400 Hz
   * @n @note ODR range limitations (based on operating mode):
   * @n - Low power mode: 0.78Hz ~ 400Hz
   * @n - Normal mode:    12.5Hz ~ 6400Hz
   * @n - High performance mode: 12.5Hz ~ 6400Hz
   * @param range Range selection (see: eGyroRange_t)
   * @n Available ranges:
   * @n - eGyroRange125DPS:   ±125dps
   * @n - eGyroRange250DPS:   ±250dps
   * @n - eGyroRange500DPS:   ±500dps
   * @n - eGyroRange1000DPS:  ±1000dps
   * @n - eGyroRange2000DPS:  ±2000dps
   * @param mode Operating mode selection (see: eGyroMode_t), default eGyroModeNormal
   * @n Available modes:
   * @n - eGyroModeLowPower:  Low power mode
   * @n - eGyroModeNormal:    Normal mode (default)
   * @n - eGyroModeHighPerf:  High performance mode
   * @return bool type, indicates the configuration status
   * @retval true Configuration successful
   * @retval false Configuration failed
   */
  bool configGyro(eGyroODR_t odr, eGyroRange_t range, eGyroMode_t mode = eGyroModeNormal);

  /**
   * @fn getAccelGyroData
   * @brief Read accelerometer and gyroscope simultaneously and return physical units
   * @details Read accelerometer and gyroscope raw data at once, convert to g/dps and return
   * @param accel Accelerometer output
   * @param gyro Gyroscope output
   * @return bool type, indicates the read status
   * @retval true Read successful
   * @retval false Read failed
   */
  bool getAccelGyroData(sSensorData *accel, sSensorData *gyro);

  /**
   * @fn getTemperature
   * @brief Read die temperature in degrees Celsius
   * @details Reads raw temperature from the sensor and converts it using the official formula:
   * temperature (°C) = (int16_t)raw / 512.0 + 23.0. Accelerometer or gyroscope must be configured first.
   * @return float Temperature in °C, or 0.0f if the sensor is not initialized or the read fails
   */
  float getTemperature(void);

  /**
   * @fn enableStepCounterInt
   * @brief Enable step counter interrupt function
   * @details Configure step counter function and map to specified interrupt pin, interrupt will be triggered when step count changes
   * @param pin Bound interrupt pin (eINT1 or eINT2)
   * @return bool type, indicates the configuration status
   * @retval true Configuration successful
   * @retval false Configuration failed
   */
  bool enableStepCounterInt(eInt_t pin);

  /**
   * @fn readStepCounter
   * @brief Read step counter data
   * @param stepVal Step count output pointer, the read step count will be written to the memory pointed by this pointer
   * @return int8_t BMI3_OK indicates success, other values indicate failure
   */
  int8_t readStepCounter(uint16_t *stepVal);

  /**
   * @fn getIntStatus
   * @brief Get interrupt status
   * @details Read and combine interrupt status from both INT1 and INT2 pins. The return value is the OR combination of INT1 and INT2 status registers.
   * @return uint16_t Combined interrupt status register value (INT1 | INT2). Each bit represents a different interrupt type:
   * @n - BMI3_INT_STATUS_ANY_MOTION: Any motion detected
   * @n - BMI3_INT_STATUS_NO_MOTION: No motion detected
   * @n - BMI3_INT_STATUS_FLAT: Flat detection
   * @n - BMI3_INT_STATUS_ORIENTATION: Orientation change
   * @n - BMI3_INT_STATUS_STEP_DETECTOR: Step detected
   * @n - BMI3_INT_STATUS_SIG_MOTION: Significant motion detected
   * @n - BMI3_INT_STATUS_TILT: Tilt detected
   * @n - BMI3_INT_STATUS_TAP: Tap detected
   */
  uint16_t getIntStatus(void);

  /**
   * @fn enableAnyMotionInt
   * @brief Configure any-motion threshold interrupt (using official structure parameters)
   * @param config Any-motion configuration structure (see bmi3_any_motion_config)
   * @n Parameter description:
   * @n - slope_thres: Acceleration slope threshold, range
   * 0-4095, unit 1.953mg/LSB (official example: 9 ≈ 17.6mg)
   * @n - hysteresis: Hysteresis value, range 0-1023, unit 1.953mg/LSB (official example: 5
   * ≈ 9.8mg)
   * @n - duration: Duration, range 0-8191, unit 20ms (official example: 9 = 180ms)
   * @n - acc_ref_up: Acceleration reference update mode, 0=OnEvent, 1=Always (official example: 1)
   * @n - wait_time: Wait time, range 0-7, unit 20ms (official example: 4-5 = 80-100ms)
   * @param pin Bound interrupt pin
   * @param axisMask Axis selection mask (default: eAxisXYZ)
   * @return bool type, indicates the configuration status
   * @retval true Configuration successful
   * @retval false Configuration failed
   */
  bool enableAnyMotionInt(const struct bmi3_any_motion_config &config, eInt_t pin, uint8_t axisMask = eAxisXYZ);

  /**
   * @fn enableNoMotionInt
   * @brief Configure no-motion threshold interrupt (using official structure parameters)
   * @param config No-motion detection configuration structure (see bmi3_no_motion_config)
   * @n Parameter description:
   * @n - slope_thres: Acceleration slope threshold, range
   * 0-4095, unit 1.953mg/LSB (official example: 9 ≈ 17.6mg)
   * @n - hysteresis: Hysteresis value, range 0-1023, unit 1.953mg/LSB (official example: 5
   * ≈ 9.8mg)
   * @n - duration: Duration, range 0-8191, unit 20ms (official example: 9 = 180ms)
   * @n - acc_ref_up: Acceleration reference update mode, 0=OnEvent, 1=Always (official example: 1)
   * @n - wait_time: Wait time, range 0-7, unit 20ms (official example: 5 = 100ms)
   * @param pin Bound interrupt pin
   * @param axisMask Axis selection mask (default: eAxisXYZ)
   * @return bool type, indicates the configuration status
   * @retval true Configuration successful
   * @retval false Configuration failed
   */
  bool enableNoMotionInt(const struct bmi3_no_motion_config &config, eInt_t pin, uint8_t axisMask = eAxisXYZ);

  /**
   * @fn enableSigMotionInt
   * @brief Configure significant motion detection interrupt (using official structure parameters)
   * @param config Significant motion configuration structure (see bmi3_sig_motion_config)
   * @n Parameter description:
   * @n - block_size: Detection segment size, range 0-65535 (official example: 200)
   * @n - peak_2_peak_min: Peak-to-peak acceleration minimum, range 0-1023 (official example: 30)
   * @n - peak_2_peak_max: Peak-to-peak acceleration maximum, range 0-1023 (official example: 30)
   * @n - mcr_min: Mean crossing rate per second minimum, range 0-62 (official example: 0x10 = 16)
   * @n - mcr_max: Mean crossing rate per second maximum, range 0-62 (official example: 0x10 = 16)
   * @param pin Bound interrupt pin
   * @return bool type, indicates the configuration status
   * @retval true Configuration successful
   * @retval false Configuration failed
   */
  bool enableSigMotionInt(const struct bmi3_sig_motion_config &config, eInt_t pin);

  /**
   * @fn enableFlatInt
   * @brief Configure flat detection interrupt (using official structure parameters)
   * @param config Flat detection configuration structure (see bmi3_flat_config)
   * @n Parameter description:
   * @n - theta: Maximum allowed tilt angle, range 0-63, angle calculated as 64 *
   * (tan(angle)^2) (official example: 9)
   * @n - blocking: Blocking mode, 0=MODE_0(disabled), 1=MODE_1(>1.5g),
   * 2=MODE_2(>1.5g or slope>half threshold), 3=MODE_3(>1.5g or slope>threshold) (official example: 3)
   * @n - hold_time: Minimum duration for device to maintain flat state, range 0-255, unit
   * 20ms (official example: 50 = 1000ms)
   * @n - hysteresis: Hysteresis angle for flat detection, range 0-255 (official example: 9)
   * @n - slope_thres: Minimum slope between consecutive acceleration samples, range 0-255 (official example: 0xCD
   * = 205)
   * @param pin Bound interrupt pin
   * @return bool type, indicates the configuration status
   * @retval true Configuration successful
   * @retval false Configuration failed
   */
  bool enableFlatInt(const struct bmi3_flat_config &config, eInt_t pin);

  /**
   * @fn enableOrientationInt
   * @brief Configure orientation detection interrupt (using official structure parameters)
   * @param config Orientation detection configuration structure (see bmi3_orientation_config)
   * @n Parameter description:
   * @n - ud_en: Whether to detect flip (face up/down), 0=disabled, 1=enabled (official example: 1)
   * @n - hold_time: Required duration for orientation change detection, range 0-255, unit 20ms (official example: 4 = 80ms)
   * @n - hysteresis: Hysteresis for orientation detection, range 0-255 (official example: 5)
   * @n - theta: Maximum allowed tilt angle, range 0-63, angle=64*(tan(angle)^2) (official example: 16)
   * @n - mode: Orientation detection mode, 0/3=symmetric, 1=high asymmetric, 2=low asymmetric (official example: 1)
   * @n - slope_thres: Slope threshold to prevent false detection due to violent motion, range 0-255 (official example: 30)
   * @n - blocking: Blocking mode, 0-3 (official example: 3)
   * @param pin Bound interrupt pin
   * @return bool type, indicates the configuration status
   * @retval true Configuration successful
   * @retval false Configuration failed
   */
  bool enableOrientationInt(const struct bmi3_orientation_config &config, eInt_t pin);

  /**
   * @fn readOrientation
   * @brief Read orientation detection output
   * @param portraitLandscape Portrait/Landscape status output pointer, can be NULL
   * @param faceUpDown Face up/down status output pointer, can be NULL
   * @return bool type, indicates the read status
   * @retval true Read successful
   * @retval false Read failed or feature not enabled
   */
  bool readOrientation(uint8_t *portraitLandscape, uint8_t *faceUpDown);

  /**
   * @fn enableTapInt
   * @brief Configure tap detection interrupt (using official structure parameters)
   * @param config Tap detection configuration structure (see bmi3_tap_detector_config)
   * @n Key parameters (refer to tap.c):
   * @n - axis_sel: Select axis for tap detection (0=X, 1=Y, 2=Z)
   * @n - mode: Detection mode (0=sensitive, 1=normal, 2=robust)
   * @n - tap_peak_thres / tap_shock_settling_dur etc. for timing/amplitude thresholds to determine tap
   * @param pin Bound interrupt pin
   * @param enableSingle Whether to enable single tap detection (default true)
   * @param enableDouble Whether to enable double tap detection (default true)
   * @param enableTriple Whether to enable triple tap detection (default true)
   * @return bool type, indicates the configuration status
   * @retval true Configuration successful
   * @retval false Configuration failed
   */
  bool enableTapInt(const struct bmi3_tap_detector_config &config, eInt_t pin, bool enableSingle = true, bool enableDouble = true, bool enableTriple = true);

  /**
   * @fn readTapStatus
   * @brief Read tap detection status (single/double/triple tap)
   * @param tapMask Output mask (can combine BMI3_TAP_DET_STATUS_SINGLE/DOUBLE/TRIPLE)
   * @return bool type, indicates the read status
   * @retval true Read successful
   * @retval false Read failed
   */
  bool readTapStatus(uint8_t *tapMask);

  /**
   * @fn enableTiltInt
   * @brief Configure tilt detection interrupt (using official structure parameters)
   * @param config Tilt detection configuration structure (see bmi3_tilt_config)
   * @n Key parameters (refer to tilt.c):
   * @n - segment_size: Time window for averaging reference vector, range 0-255
   * @n - min_tilt_angle: Minimum tilt angle to exceed, range 0-255, angle=256*cos(angle)
   * @n - beta_acc_mean: Low-pass averaging coefficient, range 0-65535
   * @param pin Bound interrupt pin
   * @return bool type, indicates the configuration status
   * @retval true Configuration successful
   * @retval false Configuration failed
   */
  bool enableTiltInt(const struct bmi3_tilt_config &config, eInt_t pin);

private:
  /** I2C related */
  uint8_t  _i2cAddr = 0x69;    ///< I2C device address fixed at 0x69
  TwoWire *_wire;              ///< TwoWire object pointer

  /** Device structure */
  struct bmi3_dev _dev;    ///< BMI3 device structure

  /** Internal flags */
  bool _initialized;             ///< Initialization flag
  bool _featureAccConfigFlag;    ///< Accelerometer configuration flag for advanced features

  /** Current accelerometer range (for unit conversion) */
  float _accelRange;    ///< Accelerometer range (unit: g)

  /** Current gyroscope range (for unit conversion) */
  float _gyroRange;    ///< Gyroscope range (unit: dps)

  /** Interrupt pin configuration status */
  bool _intPinConfigured[2];

  /** Interrupt mapping cache */
  struct bmi3_map_int _intMapConfig;

  /** Feature enable cache */
  struct bmi3_feature_enable _featureEnable;

  /**
   * @fn _initInterface
   * @brief Initialize I2C interface
   * @return int8_t 0 indicates success, negative value indicates failure
   */
  int8_t _initInterface(void);

  /**
   * @fn _i2cRead
   * @brief I2C read function
   * @param reg_addr Register address
   * @param reg_data Data buffer
   * @param len Data length
   * @param intf_ptr Interface pointer
   * @return int8_t 0 indicates success, negative value indicates failure
   */
  int8_t _i2cRead(uint8_t reg_addr, uint8_t *reg_data, uint32_t len, void *intf_ptr);

  /**
   * @fn _i2cWrite
   * @brief I2C write function
   * @param reg_addr Register address
   * @param reg_data Data buffer
   * @param len Data length
   * @param intf_ptr Interface pointer
   * @return int8_t 0 indicates success, negative value indicates failure
   */
  int8_t _i2cWrite(uint8_t reg_addr, const uint8_t *reg_data, uint32_t len, void *intf_ptr);

  /**
   * @fn _delayUs
   * @brief Microsecond delay function
   * @param period Delay time (microseconds)
   * @param intf_ptr Interface pointer
   */
  void _delayUs(uint32_t period, void *intf_ptr);

  /** Static callback functions (for low-level driver) */
  static int8_t _i2cReadCallback(uint8_t reg_addr, uint8_t *reg_data, uint32_t len, void *intf_ptr);
  static int8_t _i2cWriteCallback(uint8_t reg_addr, const uint8_t *reg_data, uint32_t len, void *intf_ptr);
  static void   _delayUsCallback(uint32_t period, void *intf_ptr);

  /**
   * @fn _lsbToG
   * @brief Convert LSB value to G value
   * @param val Raw LSB value
   * @param g_range Range (g)
   * @return float G value
   */
  float _lsbToG(int16_t val, float g_range);

  /**
   * @fn _lsbToDps
   * @brief Convert LSB value to degrees per second value
   * @param val Raw LSB value
   * @param dps_range Range (dps)
   * @return float Degrees per second value
   */
  float _lsbToDps(int16_t val, float dps_range);

  bool     _readVector(uint8_t sensor_type, sSensorData *data, float range, bool isAccel);
  bool     _configureMotionInterrupt(bool anyMotion, const struct bmi3_any_motion_config *anyConfig, const struct bmi3_no_motion_config *noConfig, eInt_t pin, uint8_t axisMask);
  bool     _configureIntPin(eInt_t pin);
  uint8_t  _encodeIntPin(eInt_t pin) const;
  uint16_t _mgToSlope(float threshold_mg) const;
  uint16_t _msToDuration(uint16_t duration_ms) const;
  uint8_t  _msToWait(uint16_t duration_ms) const;
  bool     _applyFeatureEnable(void);

  /**
   * @fn getAccelData
   * @brief Internal function: Get raw accelerometer LSB (used by getSensorRawData)
   * @param data int16_t[3] buffer
   * @return int8_t BMI3_OK indicates success
   */
  int8_t getAccelData(int16_t *data);

  /**
   * @fn getGyroData
   * @brief Internal function: Get raw gyroscope LSB (used by getSensorRawData)
   * @param data int16_t[3] buffer
   * @return int8_t BMI3_OK indicates success
   */
  int8_t getGyroData(int16_t *data);

  /**
   * @fn getSensorRawData
   * @brief Internal function: Synchronously read gyroscope and accelerometer raw data (first 3 are gyroscope, last 3 are accelerometer)
   * @param data int16_t[6] buffer
   * @return int8_t BMI3_OK indicates success
   */
  int8_t getSensorRawData(int16_t *data);

  /**
   * @fn _setAxisRemap
   * @brief Internal function: Set axis remap configuration (ZYX axis mapping with inverted Z axis)
   * @details This function configures the axis remapping as: ZYX axis mapping with inverted Z axis
   * @n @note: XYZ axis denotes x = x, y = y, z = z
   * @n Similarly, ZYX means x = z, y = y, z = x
   * @return bool type, indicates the configuration status
   * @retval true Configuration successful
   * @retval false Configuration failed
   */
  bool _setAxisRemap(void);
};

#endif
