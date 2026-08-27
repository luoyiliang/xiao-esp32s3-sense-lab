/*!
 * @file DFRobot_BMI323.cpp
 * @brief Define the basic structure of DFRobot_BMI323 class, implementation of basic methods
 * @copyright Copyright (c) 2025 DFRobot Co.Ltd (http://www.dfrobot.com)
 * @license The MIT License (MIT)
 * @author [Martin](Martin@dfrobot.com)
 * @version V1.0.0
 * @date 2025-12-08
 * @url https://github.com/DFRobot/DFRobot_BMI323
 */

#include "DFRobot_BMI323.h"

#include <string.h>

// The bus is shared, while each instance supplies its own address through
// intf_ptr. This keeps the callback stateless with respect to sensor identity.
static TwoWire *g_bmi323_wire = NULL;

// ========== Constructor and Destructor ==========

DFRobot_BMI323::DFRobot_BMI323(TwoWire *wire, uint8_t i2cAddr)
{
  _wire                 = wire;
  _initialized          = false;
  _featureAccConfigFlag = false;
  _accelRange           = 2.0f;
  _gyroRange            = 250.0f;
  _i2cAddr              = i2cAddr;
  memset(&_dev, 0, sizeof(_dev));
  memset(&_intMapConfig, 0, sizeof(_intMapConfig));
  memset(&_featureEnable, 0, sizeof(_featureEnable));
  _intPinConfigured[0] = false;
  _intPinConfigured[1] = false;
  g_bmi323_wire       = wire;
}

DFRobot_BMI323::~DFRobot_BMI323()
{
}

// ========== Initialization Functions ==========

bool DFRobot_BMI323::begin(void)
{
  if (_initialized) {
    return true;
  }

  // Initialize interface
  int8_t rslt = _initInterface();
  if (rslt != BMI323_OK) {
    return false;
  }

  // Initialize BMI323
  rslt = bmi323_init(&_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  _initialized = true;

  // Set axis remap
  if (!_setAxisRemap()) {
    return false;
  }

  return true;
}

int8_t DFRobot_BMI323::_initInterface(void)
{
  // The application owns I2C pin selection and clock configuration. Calling
  // Wire.begin() here without pins can silently move an ESP32 bus back to its
  // board defaults, which breaks custom GPIO5/GPIO6 wiring.
  if (_wire == NULL) {
    return BMI323_E_NULL_PTR;
  }

  _dev.intf           = BMI3_I2C_INTF;
  _dev.read           = _i2cReadCallback;
  _dev.write          = _i2cWriteCallback;
  _dev.intf_ptr       = &_i2cAddr;
  _dev.read_write_len = 8;

  // Set delay function
  _dev.delay_us = _delayUsCallback;

  return BMI323_OK;
}

// ========== I2C Read/Write Functions ==========

int8_t DFRobot_BMI323::_i2cRead(uint8_t reg_addr, uint8_t *reg_data, uint32_t len, void *intf_ptr)
{
  (void)intf_ptr;

  _wire->beginTransmission(_i2cAddr);
  _wire->write(reg_addr);
  if (_wire->endTransmission() != 0) {
    return BMI323_E_COM_FAIL;
  }

  _wire->requestFrom(_i2cAddr, (uint8_t)len);
  uint32_t index = 0;
  while (_wire->available() && index < len) {
    reg_data[index++] = _wire->read();
  }

  if (index != len) {
    return BMI323_E_COM_FAIL;
  }

  return BMI323_OK;
}

int8_t DFRobot_BMI323::_i2cWrite(uint8_t reg_addr, const uint8_t *reg_data, uint32_t len, void *intf_ptr)
{
  (void)intf_ptr;

  _wire->beginTransmission(_i2cAddr);
  _wire->write(reg_addr);
  for (uint32_t i = 0; i < len; i++) {
    _wire->write(reg_data[i]);
  }

  if (_wire->endTransmission() != 0) {
    return BMI323_E_COM_FAIL;
  }

  return BMI323_OK;
}

// ========== Delay Functions ==========

void DFRobot_BMI323::_delayUs(uint32_t period, void *intf_ptr)
{
  (void)intf_ptr;
  delayMicroseconds(period);
}

// ========== Static Callback Functions ==========

int8_t DFRobot_BMI323::_i2cReadCallback(uint8_t reg_addr, uint8_t *reg_data, uint32_t len, void *intf_ptr)
{
  if (intf_ptr == NULL || reg_data == NULL) {
    return BMI323_E_NULL_PTR;
  }

  // Route by the instance-specific address pointer. This allows two BMI323
  // objects to share one TwoWire bus without a global-instance collision.
  uint8_t address = *static_cast<uint8_t *>(intf_ptr);
  if (g_bmi323_wire == NULL) {
    return BMI323_E_NULL_PTR;
  }
  g_bmi323_wire->beginTransmission(address);
  g_bmi323_wire->write(reg_addr);
  if (g_bmi323_wire->endTransmission() != 0) {
    return BMI323_E_COM_FAIL;
  }

  g_bmi323_wire->requestFrom(address, static_cast<uint8_t>(len));
  uint32_t index = 0;
  while (g_bmi323_wire->available() && index < len) {
    reg_data[index++] = g_bmi323_wire->read();
  }
  return index == len ? BMI323_OK : BMI323_E_COM_FAIL;
}

int8_t DFRobot_BMI323::_i2cWriteCallback(uint8_t reg_addr, const uint8_t *reg_data, uint32_t len, void *intf_ptr)
{
  if (intf_ptr == NULL || reg_data == NULL) {
    return BMI323_E_NULL_PTR;
  }

  if (g_bmi323_wire == NULL) {
    return BMI323_E_NULL_PTR;
  }

  uint8_t address = *static_cast<uint8_t *>(intf_ptr);
  g_bmi323_wire->beginTransmission(address);
  g_bmi323_wire->write(reg_addr);
  for (uint32_t i = 0; i < len; ++i) {
    g_bmi323_wire->write(reg_data[i]);
  }
  return g_bmi323_wire->endTransmission() == 0 ? BMI323_OK : BMI323_E_COM_FAIL;
}

void DFRobot_BMI323::_delayUsCallback(uint32_t period, void *intf_ptr)
{
  (void)intf_ptr;
  delayMicroseconds(period);
}

// ========== Accelerometer Functions ==========

bool DFRobot_BMI323::configAccel(eAccelODR_t odr, eAccelRange_t range, eAccelMode_t mode)
{
  if (!_initialized) {
    return false;
  }

  struct bmi3_sens_config config;
  config.type = BMI323_ACCEL;

  int8_t rslt = bmi323_get_sensor_config(&config, 1, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  switch (mode) {
    case eAccelModeLowPower:
      config.cfg.acc.acc_mode = BMI3_ACC_MODE_LOW_PWR;
      config.cfg.acc.avg_num  = BMI3_ACC_AVG2;
      config.cfg.acc.bwp      = BMI3_ACC_BW_ODR_HALF;
      break;
    case eAccelModeNormal:
      config.cfg.acc.acc_mode = BMI3_ACC_MODE_NORMAL;
      config.cfg.acc.avg_num  = BMI3_ACC_AVG1;
      config.cfg.acc.bwp      = BMI3_ACC_BW_ODR_HALF;
      break;
    case eAccelModeHighPerf:
      config.cfg.acc.acc_mode = BMI3_ACC_MODE_HIGH_PERF;
      config.cfg.acc.avg_num  = BMI3_ACC_AVG1;
      config.cfg.acc.bwp      = BMI3_ACC_BW_ODR_QUARTER;
      break;
    default:
      config.cfg.acc.acc_mode = BMI3_ACC_MODE_NORMAL;
      config.cfg.acc.avg_num  = BMI3_ACC_AVG1;
      config.cfg.acc.bwp      = BMI3_ACC_BW_ODR_HALF;
      break;
  }

  config.cfg.acc.odr   = (uint8_t)odr;
  config.cfg.acc.range = (uint8_t)range;

  rslt = bmi323_set_sensor_config(&config, 1, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  // Save range for unit conversion
  switch (range) {
    case eAccelRange2G:
      _accelRange = 2.0f;
      break;
    case eAccelRange4G:
      _accelRange = 4.0f;
      break;
    case eAccelRange8G:
      _accelRange = 8.0f;
      break;
    case eAccelRange16G:
      _accelRange = 16.0f;
      break;
    default:
      _accelRange = 2.0f;
      break;
  }

  // Set accelerometer configuration flag for advanced features
  _featureAccConfigFlag = true;

  return true;
}

bool DFRobot_BMI323::configGyro(eGyroODR_t odr, eGyroRange_t range, eGyroMode_t mode)
{
  if (!_initialized) {
    return false;
  }

  struct bmi3_sens_config config;
  config.type = BMI323_GYRO;

  int8_t rslt = bmi323_get_sensor_config(&config, 1, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  switch (mode) {
    case eGyroModeLowPower:
      config.cfg.gyr.gyr_mode = BMI3_GYR_MODE_LOW_PWR;
      config.cfg.gyr.avg_num  = BMI3_GYR_AVG2;
      config.cfg.gyr.bwp      = BMI3_GYR_BW_ODR_HALF;
      break;
    case eGyroModeNormal:
      config.cfg.gyr.gyr_mode = BMI3_GYR_MODE_NORMAL;
      config.cfg.gyr.avg_num  = BMI3_GYR_AVG1;
      config.cfg.gyr.bwp      = BMI3_GYR_BW_ODR_HALF;
      break;
    case eGyroModeHighPerf:
      config.cfg.gyr.gyr_mode = BMI3_GYR_MODE_HIGH_PERF;
      config.cfg.gyr.avg_num  = BMI3_GYR_AVG1;
      config.cfg.gyr.bwp      = BMI3_GYR_BW_ODR_QUARTER;
      break;
    default:
      config.cfg.gyr.gyr_mode = BMI3_GYR_MODE_NORMAL;
      config.cfg.gyr.avg_num  = BMI3_GYR_AVG1;
      config.cfg.gyr.bwp      = BMI3_GYR_BW_ODR_HALF;
      break;
  }

  config.cfg.gyr.odr   = (uint8_t)odr;
  config.cfg.gyr.range = (uint8_t)range;

  rslt = bmi323_set_sensor_config(&config, 1, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  // Save range for unit conversion
  switch (range) {
    case eGyroRange125DPS:
      _gyroRange = 125.0f;
      break;
    case eGyroRange250DPS:
      _gyroRange = 250.0f;
      break;
    case eGyroRange500DPS:
      _gyroRange = 500.0f;
      break;
    case eGyroRange1000DPS:
      _gyroRange = 1000.0f;
      break;
    case eGyroRange2000DPS:
      _gyroRange = 2000.0f;
      break;
    default:
      _gyroRange = 250.0f;
      break;
  }

  return true;
}

bool DFRobot_BMI323::getAccelGyroData(sSensorData *accel, sSensorData *gyro)
{
  if (!_initialized || accel == NULL || gyro == NULL) {
    return false;
  }

  int16_t raw[6] = { 0 };
  if (getSensorRawData(raw) != BMI3_OK) {
    return false;
  }

  gyro->x = _lsbToDps(raw[0], _gyroRange);
  gyro->y = _lsbToDps(raw[1], _gyroRange);
  gyro->z = _lsbToDps(raw[2], _gyroRange);

  accel->x = _lsbToG(raw[3], _accelRange);
  accel->y = _lsbToG(raw[4], _accelRange);
  accel->z = _lsbToG(raw[5], _accelRange);

  return true;
}

float DFRobot_BMI323::getTemperature(void)
{
  if (!_initialized) {
    return 0.0f;
  }

  struct bmi3_sensor_data sensor_data;
  memset(&sensor_data, 0, sizeof(sensor_data));
  sensor_data.type = BMI323_TEMP;

  int8_t rslt = bmi323_get_sensor_data(&sensor_data, 1, &_dev);
  if (rslt != BMI323_OK) {
    return 0.0f;
  }

  int16_t raw_temp = (int16_t)sensor_data.sens_data.temp.temp_data;
  return ((float)raw_temp / 512.0f) + 23.0f;
}

// ========== Motion Detection Functions ==========

int8_t DFRobot_BMI323::readStepCounter(uint16_t *stepVal)
{
  if (stepVal == NULL) {
    return BMI3_E_NULL_PTR;
  }

  if (!_initialized) {
    *stepVal = 0;
    return BMI3_E_COM_FAIL;
  }

  struct bmi3_sensor_data sensor_data;
  sensor_data.type = BMI323_STEP_COUNTER;

  int8_t rslt = bmi323_get_sensor_data(&sensor_data, 1, &_dev);
  if (rslt != BMI323_OK) {
    *stepVal = 0;
    return rslt;
  }

  uint32_t steps = sensor_data.sens_data.step_counter_output;
  *stepVal       = (steps > 0xFFFFU) ? 0xFFFFU : (uint16_t)steps;

  return BMI3_OK;
}

bool DFRobot_BMI323::enableStepCounterInt(eInt_t pin)
{
  if (!_initialized) {
    return false;
  }

  // Check if accelerometer has been configured
  if (!_featureAccConfigFlag) {
    return false;
  }

  // Check accelerometer configuration: in low power mode, ODR must be >= 50Hz for step counter
  // This validation is normally done in set_step_config, but we need to check it here
  // since we need to ensure compatibility before enabling step counter
  struct bmi3_sens_config accelConfig;
  accelConfig.type = BMI323_ACCEL;
  int8_t rslt      = bmi323_get_sensor_config(&accelConfig, 1, &_dev);
  if (rslt != BMI323_OK) {
    // Cannot read accelerometer configuration
    return false;
  }

  // Get and set step counter configuration to trigger validation
  // This ensures compatibility checks are performed even if using default config
  struct bmi3_sens_config stepConfig;
  stepConfig.type = BMI323_STEP_COUNTER;
  rslt            = bmi323_get_sensor_config(&stepConfig, 1, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  // Set step counter configuration (this will validate ODR requirements)
  rslt = bmi323_set_sensor_config(&stepConfig, 1, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  // Enable step counter and step detector features
  _featureEnable.step_counter_en  = BMI3_ENABLE;
  _featureEnable.step_detector_en = BMI3_ENABLE;
  if (!_applyFeatureEnable()) {
    return false;
  }

  // Configure interrupt pin
  if (!_configureIntPin(pin)) {
    return false;
  }

  // Map interrupt to specified pin
  uint8_t mapValue                = _encodeIntPin(pin);
  _intMapConfig.step_detector_out = mapValue;
  if (bmi323_map_interrupt(_intMapConfig, &_dev) != BMI323_OK) {
    return false;
  }

  return true;
}

int8_t DFRobot_BMI323::getAccelData(int16_t *data)
{
  if ((data == NULL) || !_initialized) {
    return BMI3_E_NULL_PTR;
  }

  struct bmi3_sensor_data sensor_data;
  memset(&sensor_data, 0, sizeof(sensor_data));
  sensor_data.type = BMI323_ACCEL;

  int8_t rslt = bmi323_get_sensor_data(&sensor_data, 1, &_dev);
  if (rslt == BMI323_OK) {
    data[0] = sensor_data.sens_data.acc.x;
    data[1] = sensor_data.sens_data.acc.y;
    data[2] = sensor_data.sens_data.acc.z;
  }

  return rslt;
}

int8_t DFRobot_BMI323::getGyroData(int16_t *data)
{
  if ((data == NULL) || !_initialized) {
    return BMI3_E_NULL_PTR;
  }

  struct bmi3_sensor_data sensor_data;
  memset(&sensor_data, 0, sizeof(sensor_data));
  sensor_data.type = BMI323_GYRO;

  int8_t rslt = bmi323_get_sensor_data(&sensor_data, 1, &_dev);
  if (rslt == BMI323_OK) {
    data[0] = sensor_data.sens_data.gyr.x;
    data[1] = sensor_data.sens_data.gyr.y;
    data[2] = sensor_data.sens_data.gyr.z;
  }

  return rslt;
}

int8_t DFRobot_BMI323::getSensorRawData(int16_t *data)
{
  if ((data == NULL) || !_initialized) {
    return BMI3_E_NULL_PTR;
  }

  int8_t rslt = getGyroData(data);
  if (rslt != BMI323_OK) {
    return rslt;
  }

  rslt = getAccelData(data + 3);
  return rslt;
}

// ========== Interrupt Functions ==========

uint16_t DFRobot_BMI323::getIntStatus(void)
{
  if (!_initialized) {
    return 0;
  }

  uint16_t int_status  = 0;
  uint16_t int1_status = 0;
  uint16_t int2_status = 0;

  // Read INT1 status
  int8_t rslt1 = bmi323_get_int1_status(&int1_status, &_dev);
  // Read INT2 status
  int8_t rslt2 = bmi323_get_int2_status(&int2_status, &_dev);

  // Merge status of both interrupt pins (using OR operation)
  // This ensures correct status reading regardless of which pin the interrupt is mapped to
  if (rslt1 == BMI323_OK || rslt2 == BMI323_OK) {
    int_status = int1_status | int2_status;
  }

  return int_status;
}

bool DFRobot_BMI323::enableAnyMotionInt(const struct bmi3_any_motion_config &config, eInt_t pin, uint8_t axisMask)
{
  return _configureMotionInterrupt(true, &config, nullptr, pin, axisMask);
}

bool DFRobot_BMI323::enableNoMotionInt(const struct bmi3_no_motion_config &config, eInt_t pin, uint8_t axisMask)
{
  return _configureMotionInterrupt(false, nullptr, &config, pin, axisMask);
}

bool DFRobot_BMI323::enableSigMotionInt(const struct bmi3_sig_motion_config &config, eInt_t pin)
{
  if (!_initialized) {
    return false;
  }

  // Check if accelerometer has been configured
  if (!_featureAccConfigFlag) {
    return false;
  }

  if (!_configureIntPin(pin)) {
    return false;
  }

  struct bmi3_sens_config sensConfig = { 0 };
  sensConfig.type                    = BMI323_SIG_MOTION;

  int8_t rslt = bmi323_get_sensor_config(&sensConfig, 1, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  // Directly use user-provided configuration structure
  sensConfig.cfg.sig_motion = config;

  rslt = bmi323_set_sensor_config(&sensConfig, 1, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  // Enable significant motion detection feature
  _featureEnable.sig_motion_en = BMI3_ENABLE;
  if (!_applyFeatureEnable()) {
    return false;
  }

  // Map interrupt to specified pin
  uint8_t mapValue             = _encodeIntPin(pin);
  _intMapConfig.sig_motion_out = mapValue;

  if (bmi323_map_interrupt(_intMapConfig, &_dev) != BMI323_OK) {
    return false;
  }

  return true;
}

bool DFRobot_BMI323::enableFlatInt(const struct bmi3_flat_config &config, eInt_t pin)
{
  if (!_initialized) {
    return false;
  }

  // Check if accelerometer has been configured
  if (!_featureAccConfigFlag) {
    return false;
  }

  if (!_configureIntPin(pin)) {
    return false;
  }

  struct bmi3_sens_config sensConfig = { 0 };
  sensConfig.type                    = BMI323_FLAT;

  int8_t rslt = bmi323_get_sensor_config(&sensConfig, 1, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  // Directly use user-provided configuration structure
  sensConfig.cfg.flat = config;

  rslt = bmi323_set_sensor_config(&sensConfig, 1, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  // Enable flat detection feature
  _featureEnable.flat_en = BMI3_ENABLE;
  if (!_applyFeatureEnable()) {
    return false;
  }

  // Map interrupt to specified pin
  uint8_t mapValue       = _encodeIntPin(pin);
  _intMapConfig.flat_out = mapValue;

  if (bmi323_map_interrupt(_intMapConfig, &_dev) != BMI323_OK) {
    return false;
  }

  return true;
}

bool DFRobot_BMI323::enableOrientationInt(const struct bmi3_orientation_config &config, eInt_t pin)
{
  if (!_initialized) {
    return false;
  }

  // Check if accelerometer has been configured
  if (!_featureAccConfigFlag) {
    return false;
  }

  if (!_configureIntPin(pin)) {
    return false;
  }

  struct bmi3_sens_config sensConfig = { 0 };
  sensConfig.type                    = BMI323_ORIENTATION;

  int8_t rslt = bmi323_get_sensor_config(&sensConfig, 1, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  // Directly use user-provided configuration structure
  sensConfig.cfg.orientation = config;

  rslt = bmi323_set_sensor_config(&sensConfig, 1, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  // Enable orientation detection feature
  _featureEnable.orientation_en = BMI3_ENABLE;
  if (!_applyFeatureEnable()) {
    return false;
  }

  // Map interrupt to specified pin
  uint8_t mapValue              = _encodeIntPin(pin);
  _intMapConfig.orientation_out = mapValue;

  if (bmi323_map_interrupt(_intMapConfig, &_dev) != BMI323_OK) {
    return false;
  }

  return true;
}

bool DFRobot_BMI323::readOrientation(uint8_t *portraitLandscape, uint8_t *faceUpDown)
{
  if (!_initialized) {
    return false;
  }

  struct bmi3_sensor_data sensorData;
  memset(&sensorData, 0, sizeof(sensorData));
  sensorData.type = BMI323_ORIENTATION;

  int8_t rslt = bmi323_get_sensor_data(&sensorData, 1, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  if (portraitLandscape != NULL) {
    *portraitLandscape = sensorData.sens_data.orient_output.orientation_portrait_landscape;
  }

  if (faceUpDown != NULL) {
    *faceUpDown = sensorData.sens_data.orient_output.orientation_faceup_down;
  }

  return true;
}

bool DFRobot_BMI323::enableTapInt(const struct bmi3_tap_detector_config &config, eInt_t pin, bool enableSingle, bool enableDouble, bool enableTriple)
{
  if (!_initialized) {
    return false;
  }

  // Check if accelerometer has been configured
  if (!_featureAccConfigFlag) {
    return false;
  }

  if (!_configureIntPin(pin)) {
    return false;
  }

  struct bmi3_sens_config sensConfig = { 0 };
  sensConfig.type                    = BMI323_TAP;

  int8_t rslt = bmi323_get_sensor_config(&sensConfig, 1, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  sensConfig.cfg.tap = config;

  rslt = bmi323_set_sensor_config(&sensConfig, 1, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  _featureEnable.tap_detector_s_tap_en = enableSingle ? BMI3_ENABLE : BMI3_DISABLE;
  _featureEnable.tap_detector_d_tap_en = enableDouble ? BMI3_ENABLE : BMI3_DISABLE;
  _featureEnable.tap_detector_t_tap_en = enableTriple ? BMI3_ENABLE : BMI3_DISABLE;

  if (!_applyFeatureEnable()) {
    return false;
  }

  uint8_t mapValue      = _encodeIntPin(pin);
  _intMapConfig.tap_out = mapValue;

  if (bmi323_map_interrupt(_intMapConfig, &_dev) != BMI323_OK) {
    return false;
  }

  return true;
}

bool DFRobot_BMI323::readTapStatus(uint8_t *tapMask)
{
  if (!_initialized || (tapMask == NULL)) {
    return false;
  }

  uint8_t data[2] = { 0 };
  int8_t  rslt    = bmi323_get_regs(BMI3_REG_FEATURE_EVENT_EXT, data, 2, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  *tapMask = data[0] & (BMI3_TAP_DET_STATUS_SINGLE | BMI3_TAP_DET_STATUS_DOUBLE | BMI3_TAP_DET_STATUS_TRIPLE);
  return true;
}

bool DFRobot_BMI323::enableTiltInt(const struct bmi3_tilt_config &config, eInt_t pin)
{
  if (!_initialized) {
    return false;
  }

  // Check if accelerometer has been configured
  if (!_featureAccConfigFlag) {
    return false;
  }

  if (!_configureIntPin(pin)) {
    return false;
  }

  struct bmi3_sens_config sensConfig = { 0 };
  sensConfig.type                    = BMI323_TILT;

  int8_t rslt = bmi323_get_sensor_config(&sensConfig, 1, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  sensConfig.cfg.tilt = config;

  rslt = bmi323_set_sensor_config(&sensConfig, 1, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  _featureEnable.tilt_en = BMI3_ENABLE;
  if (!_applyFeatureEnable()) {
    return false;
  }

  uint8_t mapValue       = _encodeIntPin(pin);
  _intMapConfig.tilt_out = mapValue;
  if (bmi323_map_interrupt(_intMapConfig, &_dev) != BMI323_OK) {
    return false;
  }

  return true;
}

// ========== Unit Conversion Functions ==========

float DFRobot_BMI323::_lsbToG(int16_t val, float g_range)
{
  // 16-bit resolution
  float half_scale = 32768.0f;
  return (val * g_range) / half_scale;
}

float DFRobot_BMI323::_lsbToDps(int16_t val, float dps_range)
{
  // 16-bit resolution
  float half_scale = 32768.0f;
  return (val * dps_range) / half_scale;
}

bool DFRobot_BMI323::_readVector(uint8_t sensor_type, sSensorData *data, float range, bool isAccel)
{
  struct bmi3_sensor_data sensor_data = { 0 };
  sensor_data.type                    = sensor_type;

  int8_t rslt = bmi323_get_sensor_data(&sensor_data, 1, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  if (isAccel) {
    data->x = _lsbToG(sensor_data.sens_data.acc.x, range);
    data->y = _lsbToG(sensor_data.sens_data.acc.y, range);
    data->z = _lsbToG(sensor_data.sens_data.acc.z, range);
  } else {
    data->x = _lsbToDps(sensor_data.sens_data.gyr.x, range);
    data->y = _lsbToDps(sensor_data.sens_data.gyr.y, range);
    data->z = _lsbToDps(sensor_data.sens_data.gyr.z, range);
  }

  return true;
}

bool DFRobot_BMI323::_configureMotionInterrupt(bool anyMotion, const struct bmi3_any_motion_config *anyConfig, const struct bmi3_no_motion_config *noConfig, eInt_t pin, uint8_t axisMask)
{
  if (!_initialized) {
    return false;
  }

  // Check if accelerometer has been configured
  if (!_featureAccConfigFlag) {
    return false;
  }

  if (!_configureIntPin(pin)) {
    return false;
  }

  struct bmi3_sens_config config = { 0 };
  config.type                    = anyMotion ? BMI323_ANY_MOTION : BMI323_NO_MOTION;

  int8_t rslt = bmi323_get_sensor_config(&config, 1, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  if (anyMotion) {
    if (anyConfig == nullptr) {
      return false;
    }
    // Directly use user-provided configuration structure
    config.cfg.any_motion = *anyConfig;
  } else {
    if (noConfig == nullptr) {
      return false;
    }
    // Directly use user-provided configuration structure
    config.cfg.no_motion = *noConfig;
  }

  rslt = bmi323_set_sensor_config(&config, 1, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  auto maskX = (axisMask & eAxisX) ? BMI3_ENABLE : BMI3_DISABLE;
  auto maskY = (axisMask & eAxisY) ? BMI3_ENABLE : BMI3_DISABLE;
  auto maskZ = (axisMask & eAxisZ) ? BMI3_ENABLE : BMI3_DISABLE;

  if (anyMotion) {
    _featureEnable.any_motion_x_en = maskX;
    _featureEnable.any_motion_y_en = maskY;
    _featureEnable.any_motion_z_en = maskZ;
  } else {
    _featureEnable.no_motion_x_en = maskX;
    _featureEnable.no_motion_y_en = maskY;
    _featureEnable.no_motion_z_en = maskZ;
  }

  if (!_applyFeatureEnable()) {
    return false;
  }

  uint8_t mapValue = _encodeIntPin(pin);
  if (anyMotion) {
    _intMapConfig.any_motion_out = mapValue;
  } else {
    _intMapConfig.no_motion_out = mapValue;
  }

  if (bmi323_map_interrupt(_intMapConfig, &_dev) != BMI323_OK) {
    return false;
  }

  return true;
}

bool DFRobot_BMI323::_configureIntPin(eInt_t pin)
{
  uint8_t idx = (pin == eINT1) ? 0 : 1;
  if (_intPinConfigured[idx]) {
    return true;
  }

  struct bmi3_int_pin_config config;
  memset(&config, 0, sizeof(config));
  config.pin_type  = (pin == eINT1) ? BMI3_INT1 : BMI3_INT2;
  config.int_latch = BMI3_DISABLE;

  if (pin == eINT1) {
    config.pin_cfg[0].lvl       = BMI3_ENABLE;     // Active high
    config.pin_cfg[0].od        = BMI3_DISABLE;    // Push-pull
    config.pin_cfg[0].output_en = BMI3_ENABLE;     // Enable output
  } else {
    config.pin_cfg[1].lvl       = BMI3_ENABLE;
    config.pin_cfg[1].od        = BMI3_DISABLE;
    config.pin_cfg[1].output_en = BMI3_ENABLE;
  }

  int8_t rslt = bmi3_set_int_pin_config(&config, &_dev);
  if (rslt == BMI323_OK) {
    _intPinConfigured[idx] = true;
    return true;
  }

  return false;
}

uint8_t DFRobot_BMI323::_encodeIntPin(eInt_t pin) const
{
  return (pin == eINT1) ? 0x01 : 0x02;
}

uint16_t DFRobot_BMI323::_mgToSlope(float threshold_mg) const
{
  const float step = 1.953125f;
  if (threshold_mg < 0.0f) {
    threshold_mg = 0.0f;
  }

  uint32_t value = (uint32_t)((threshold_mg / step) + 0.5f);
  if (value > 4095U) {
    value = 4095U;
  }

  return (uint16_t)value;
}

uint16_t DFRobot_BMI323::_msToDuration(uint16_t duration_ms) const
{
  uint32_t ticks = duration_ms / 20;
  if (ticks == 0) {
    ticks = 1;
  }
  if (ticks > 0x1FFFU) {
    ticks = 0x1FFFU;
  }

  return (uint16_t)ticks;
}

uint8_t DFRobot_BMI323::_msToWait(uint16_t duration_ms) const
{
  if (duration_ms == 0) {
    return 0;
  }

  uint32_t ticks = duration_ms / 20;
  if (ticks > 7U) {
    ticks = 7U;
  }

  return (uint8_t)ticks;
}

bool DFRobot_BMI323::_applyFeatureEnable(void)
{
  if (!_initialized) {
    return false;
  }

  return (bmi323_select_sensor(&_featureEnable, &_dev) == BMI323_OK);
}

bool DFRobot_BMI323::_setAxisRemap(void)
{
  if (!_initialized) {
    return false;
  }

  struct bmi3_axes_remap remap = { 0 };
  int8_t                 rslt  = bmi323_get_remap_axes(&remap, &_dev);
  if (rslt != BMI323_OK) {
    return false;
  }

  /* @note: XYZ axis denotes x = x, y = y, z = z
   * Similarly,
   *    ZYX, x = z, y = y, z = x
   */
  remap.axis_map = BMI3_MAP_YXZ_AXIS;

  /* Invert the x, y, z axis of accelerometer and gyroscope */
  remap.invert_x = BMI3_MAP_NEGATIVE;
  remap.invert_y = BMI3_MAP_NEGATIVE;
  remap.invert_z = BMI3_MAP_NEGATIVE;

  rslt = bmi323_set_remap_axes(remap, &_dev);
  return (rslt == BMI323_OK);
}
