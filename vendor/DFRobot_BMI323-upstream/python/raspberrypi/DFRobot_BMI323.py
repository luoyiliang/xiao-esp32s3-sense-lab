'''!
@file DFRobot_BMI323.py
@brief Defines core structures and basic methods for DFRobot_BMI323.
@details BMI323 is a 6-axis IMU (accelerometer + gyroscope) controllable over I2C.
@n It supports motion features such as step counter, any-motion, no-motion, tap, etc.
@n These features suit wearables, smart devices, and other motion-aware applications.
@n BMI323 exposes interrupt pins to enable low-power use without heavy host processing.
@copyright Copyright (c) 2025 DFRobot Co.Ltd (http://www.dfrobot.com)
@license The MIT License (MIT)
@author [Martin](Martin@dfrobot.com)
@version V1.0.0
@date 2025-12-08
@url https://github.com/DFRobot/DFRobot_BMI323
'''

import sys
import smbus
import logging
import time
from ctypes import *

logger = logging.getLogger()
logger.setLevel(logging.INFO)  # show all log output
# logger.setLevel(logging.FATAL)  # enable only fatal logs if noise is an issue
ph = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - [%(filename)s %(funcName)s]:%(lineno)d - %(levelname)s: %(message)s")
ph.setFormatter(formatter)
logger.addHandler(ph)

## Default chip I2C address
DFRobot_BMI323_IIC_ADDR = 0x69
## Chip ID
DFRobot_BMI323_CHIP_ID = 0x43

## Error codes
ERR_OK = 0  ## no error
ERR_DATA_BUS = -1  ## data bus error
ERR_IC_VERSION = -2  ## chip version mismatch

## Register map (from bmi3_defs.h)
BMI3_REG_CHIP_ID = 0x00
BMI3_REG_ERR_REG = 0x01
BMI3_REG_STATUS = 0x02
BMI3_REG_ACC_DATA_X = 0x03
BMI3_REG_ACC_DATA_Y = 0x04
BMI3_REG_ACC_DATA_Z = 0x05
BMI3_REG_GYR_DATA_X = 0x06
BMI3_REG_GYR_DATA_Y = 0x07
BMI3_REG_GYR_DATA_Z = 0x08
BMI3_REG_TEMP_DATA = 0x09
BMI3_REG_CMD = 0x7E
BMI3_REG_FEATURE_IO0 = 0x10
BMI3_REG_FEATURE_IO1 = 0x11
BMI3_REG_FEATURE_IO2 = 0x12
BMI3_REG_FEATURE_IO3 = 0x13
BMI3_REG_FEATURE_IO_STATUS = 0x14
BMI3_REG_ACC_CONF = 0x20
BMI3_REG_GYR_CONF = 0x21
BMI3_REG_IO_INT_CTRL = 0x38
BMI3_REG_INT_CONF = 0x39
BMI3_REG_INT_MAP1 = 0x3A
BMI3_REG_INT_MAP2 = 0x3B
BMI3_REG_INT_STATUS_INT1 = 0x0D
BMI3_REG_INT_STATUS_INT2 = 0x0E
BMI3_REG_FEATURE_CTRL = 0x40
BMI3_REG_FEATURE_DATA_ADDR = 0x41
BMI3_REG_FEATURE_DATA_TX = 0x42
BMI3_REG_FEATURE_DATA_STATUS = 0x43
BMI3_REG_FEATURE_EVENT_EXT = 0x47

## Interface types
BMI3_I2C_INTF = 1
BMI3_SPI_INTF = 2

## Dummy-byte count (I2C needs 2 bytes, SPI needs 1 byte)
BMI3_I2C_DUMMY_BYTE = 2

## Return codes
BMI323_OK = 0
BMI323_E_NULL_PTR = -1
BMI323_E_COM_FAIL = -2
BMI323_E_DEV_NOT_FOUND = -3
BMI323_E_FEATURE_ENGINE_STATUS = -4

## Command definitions
BMI3_CMD_SOFT_RESET = 0xDEAF  # soft-reset command (16-bit: low 0xAF, high 0xDE)
BMI3_CMD_AXIS_MAP_UPDATE = 0x0300  # axis map update command (16-bit: low 0x00, high 0x03)
BMI3_SOFT_RESET_DELAY_US = 1500  # soft-reset delay in microseconds

## Masks
BMI3_REV_ID_MASK = 0xF0
BMI3_REV_ID_POS = 4
BMI3_FEATURE_ENGINE_ENABLE_MASK = 0x0001
BMI3_CHIP_ID_MASK = 0x00FF

## Accelerometer config bitfields
BMI3_ACC_ODR_MASK = 0x000F
BMI3_ACC_RANGE_MASK = 0x0070
BMI3_ACC_RANGE_POS = 4
BMI3_ACC_BW_MASK = 0x0080
BMI3_ACC_BW_POS = 7
BMI3_ACC_AVG_NUM_MASK = 0x0700
BMI3_ACC_AVG_NUM_POS = 8
BMI3_ACC_MODE_MASK = 0x7000
BMI3_ACC_MODE_POS = 12

## Gyroscope config bitfields
BMI3_GYR_ODR_MASK = 0x000F
BMI3_GYR_RANGE_MASK = 0x0070
BMI3_GYR_RANGE_POS = 4
BMI3_GYR_BW_MASK = 0x0080
BMI3_GYR_BW_POS = 7
BMI3_GYR_AVG_NUM_MASK = 0x0700
BMI3_GYR_AVG_NUM_POS = 8
BMI3_GYR_MODE_MASK = 0x7000
BMI3_GYR_MODE_POS = 12

## Accelerometer mode constants
BMI3_ACC_MODE_LOW_PWR = 0x03
BMI3_ACC_MODE_NORMAL = 0x04
BMI3_ACC_MODE_HIGH_PERF = 0x07

## Gyroscope mode constants
BMI3_GYR_MODE_LOW_PWR = 0x03
BMI3_GYR_MODE_NORMAL = 0x04
BMI3_GYR_MODE_HIGH_PERF = 0x07

## Bandwidth definitions
BMI3_ACC_BW_ODR_HALF = 0
BMI3_ACC_BW_ODR_QUARTER = 1
BMI3_GYR_BW_ODR_HALF = 0
BMI3_GYR_BW_ODR_QUARTER = 1

## Averaging definitions
BMI3_ACC_AVG1 = 0x00
BMI3_ACC_AVG2 = 0x01
BMI3_GYR_AVG1 = 0x00
BMI3_GYR_AVG2 = 0x01

## Data read length
BMI3_READ_REG_DATA_LEN = 26

## Feature Engine base addresses
BMI3_BASE_ADDR_ANY_MOTION = 0x05
BMI3_BASE_ADDR_NO_MOTION = 0x08
BMI3_BASE_ADDR_SIG_MOTION = 0x0D
BMI3_BASE_ADDR_FLAT = 0x0B
BMI3_BASE_ADDR_ORIENT = 0x1C
BMI3_BASE_ADDR_TAP = 0x1E
BMI3_BASE_ADDR_TILT = 0x21
BMI3_BASE_ADDR_AXIS_REMAP = 0x03

## Any/No-motion bitfields
BMI3_ANY_NO_SLOPE_THRESHOLD_MASK = 0x0FFF
BMI3_ANY_NO_ACC_REF_UP_MASK = 0x1000
BMI3_ANY_NO_ACC_REF_UP_POS = 12
BMI3_ANY_NO_HYSTERESIS_MASK = 0x03FF
BMI3_ANY_NO_DURATION_MASK = 0x1FFF
BMI3_ANY_NO_WAIT_TIME_MASK = 0xE000
BMI3_ANY_NO_WAIT_TIME_POS = 13

## Feature enable bitfields
BMI3_ANY_MOTION_X_EN_MASK = 0x0008
BMI3_ANY_MOTION_X_EN_POS = 3
BMI3_ANY_MOTION_Y_EN_MASK = 0x0010
BMI3_ANY_MOTION_Y_EN_POS = 4
BMI3_ANY_MOTION_Z_EN_MASK = 0x0020
BMI3_ANY_MOTION_Z_EN_POS = 5
BMI3_NO_MOTION_X_EN_MASK = 0x0001
BMI3_NO_MOTION_X_EN_POS = 0
BMI3_NO_MOTION_Y_EN_MASK = 0x0002
BMI3_NO_MOTION_Y_EN_POS = 1
BMI3_NO_MOTION_Z_EN_MASK = 0x0004
BMI3_NO_MOTION_Z_EN_POS = 2
BMI3_STEP_DETECTOR_EN_MASK = 0x0100
BMI3_STEP_DETECTOR_EN_POS = 8
BMI3_STEP_COUNTER_EN_MASK = 0x0200
BMI3_STEP_COUNTER_EN_POS = 9
BMI3_SIG_MOTION_EN_MASK = 0x0400
BMI3_SIG_MOTION_EN_POS = 10
BMI3_FLAT_EN_MASK = 0x0040
BMI3_FLAT_EN_POS = 6
BMI3_ORIENTATION_EN_MASK = 0x0080
BMI3_ORIENTATION_EN_POS = 7
BMI3_TILT_EN_MASK = 0x0800
BMI3_TILT_EN_POS = 11
BMI3_TAP_DETECTOR_S_TAP_EN_MASK = 0x1000
BMI3_TAP_DETECTOR_S_TAP_EN_POS = 12
BMI3_TAP_DETECTOR_D_TAP_EN_MASK = 0x2000
BMI3_TAP_DETECTOR_D_TAP_EN_POS = 13
BMI3_TAP_DETECTOR_T_TAP_EN_MASK = 0x4000
BMI3_TAP_DETECTOR_T_TAP_EN_POS = 14

## Significant-motion bitfields
BMI3_SIG_BLOCK_SIZE_MASK = 0xFFFF
BMI3_SIG_P2P_MIN_MASK = 0x03FF
BMI3_SIG_MCR_MIN_MASK = 0xFC00
BMI3_SIG_MCR_MIN_POS = 10
BMI3_SIG_P2P_MAX_MASK = 0x03FF
BMI3_MCR_MAX_MASK = 0xFC00
BMI3_MCR_MAX_POS = 10

## Interrupt mapping bitfields
BMI3_ANY_MOTION_OUT_MASK = 0x000C
BMI3_ANY_MOTION_OUT_POS = 2
BMI3_NO_MOTION_OUT_MASK = 0x0003
BMI3_NO_MOTION_OUT_POS = 0
BMI3_STEP_DETECTOR_OUT_MASK = 0x0300
BMI3_STEP_DETECTOR_OUT_POS = 8
BMI3_STEP_COUNTER_OUT_MASK = 0x0C00
BMI3_STEP_COUNTER_OUT_POS = 10
BMI3_SIG_MOTION_OUT_MASK = 0x3000
BMI3_SIG_MOTION_OUT_POS = 12
BMI3_FLAT_OUT_MASK = 0x0030
BMI3_FLAT_OUT_POS = 4
BMI3_ORIENTATION_OUT_MASK = 0x00C0
BMI3_ORIENTATION_OUT_POS = 6
BMI3_TAP_OUT_MASK = 0x0003
BMI3_TAP_OUT_POS = 0
BMI3_TILT_OUT_MASK = 0xC000
BMI3_TILT_OUT_POS = 14

## Interrupt pin config bitfields
BMI3_INT1_LVL_MASK = 0x0001
BMI3_INT1_OD_MASK = 0x0002
BMI3_INT1_OD_POS = 1
BMI3_INT1_OUTPUT_EN_MASK = 0x0004
BMI3_INT1_OUTPUT_EN_POS = 2
BMI3_INT2_LVL_MASK = 0x0100
BMI3_INT2_LVL_POS = 8
BMI3_INT2_OD_MASK = 0x0200
BMI3_INT2_OD_POS = 9
BMI3_INT2_OUTPUT_EN_MASK = 0x0400
BMI3_INT2_OUTPUT_EN_POS = 10

## Interrupt status bits
BMI3_INT_STATUS_ANY_MOTION = 0x0002
BMI3_INT_STATUS_NO_MOTION = 0x0001
BMI3_INT_STATUS_FLAT = 0x0004
BMI3_INT_STATUS_ORIENTATION = 0x0008
BMI3_INT_STATUS_STEP_DETECTOR = 0x0010
BMI3_INT_STATUS_STEP_COUNTER = 0x0020
BMI3_INT_STATUS_SIG_MOTION = 0x0040
BMI3_INT_STATUS_TILT = 0x0080
BMI3_INT_STATUS_TAP = 0x0100
BMI3_INT_STATUS_ACC_DRDY = 0x2000
BMI3_INT_STATUS_GYR_DRDY = 0x1000

## Interrupt pin type
BMI3_INT1 = 0x01
BMI3_INT2 = 0x02
BMI3_INT_NONE = 0x00

## Enable/Disable
BMI3_ENABLE = 0x01
BMI3_DISABLE = 0x00

## Axis remap definitions
BMI3_MAP_YXZ_AXIS = 0x01
BMI3_MAP_NEGATIVE = 0x01
BMI3_XYZ_AXIS_MASK = 0x07
BMI3_X_AXIS_SIGN_MASK = 0x08
BMI3_Y_AXIS_SIGN_MASK = 0x10
BMI3_Z_AXIS_SIGN_MASK = 0x20
BMI3_X_AXIS_SIGN_POS = 3
BMI3_Y_AXIS_SIGN_POS = 4
BMI3_Z_AXIS_SIGN_POS = 5
BMI3_ACC_MODE_DISABLE = 0x00
BMI3_NO_ERROR_MASK = 0x05
BMI3_AXIS_MAP_COMPLETE_MASK = 0x0400

## Context selection
BMI323_SMART_PHONE_SEL = 0
BMI323_WEARABLE_SEL = 1
BMI323_HEARABLE_SEL = 2

## Flat config bitfields
BMI3_FLAT_THETA_MASK = 0x003F
BMI3_FLAT_BLOCKING_MASK = 0x00C0
BMI3_FLAT_BLOCKING_POS = 6
BMI3_FLAT_HOLD_TIME_MASK = 0xFF00
BMI3_FLAT_HOLD_TIME_POS = 8
BMI3_FLAT_SLOPE_THRES_MASK = 0x00FF
BMI3_FLAT_HYST_MASK = 0xFF00
BMI3_FLAT_HYST_POS = 8

## Tilt config bitfields
BMI3_TILT_SEGMENT_SIZE_MASK = 0x00FF
BMI3_TILT_MIN_TILT_ANGLE_MASK = 0xFF00
BMI3_TILT_MIN_TILT_ANGLE_POS = 8
BMI3_TILT_BETA_ACC_MEAN_MASK = 0xFFFF

## Orientation config bitfields
BMI3_ORIENT_UD_EN_MASK = 0x0001
BMI3_ORIENT_MODE_MASK = 0x0006
BMI3_ORIENT_MODE_POS = 1
BMI3_ORIENT_BLOCKING_MASK = 0x0018
BMI3_ORIENT_BLOCKING_POS = 3
BMI3_ORIENT_THETA_MASK = 0x07E0
BMI3_ORIENT_THETA_POS = 5
BMI3_ORIENT_HOLD_TIME_MASK = 0xF800
BMI3_ORIENT_HOLD_TIME_POS = 11
BMI3_ORIENT_SLOPE_THRES_MASK = 0x00FF
BMI3_ORIENT_HYST_MASK = 0xFF00
BMI3_ORIENT_HYST_POS = 8

## Orientation output bitfields
BMI3_ORIENTATION_PORTRAIT_LANDSCAPE_MASK = 0x0003
BMI3_ORIENTATION_FACEUP_DOWN_MASK = 0x0004
BMI3_ORIENTATION_FACEUP_DOWN_POS = 2

## Orientation constants
BMI3_FACE_UP = 0x00
BMI3_FACE_DOWN = 0x01
BMI3_PORTRAIT_UP_RIGHT = 0x00
BMI3_LANDSCAPE_LEFT = 0x01
BMI3_PORTRAIT_UP_DOWN = 0x02
BMI3_LANDSCAPE_RIGHT = 0x03

## Tap config bitfields
BMI3_TAP_AXIS_SEL_MASK = 0x0003
BMI3_TAP_WAIT_FR_TIME_OUT_MASK = 0x0004
BMI3_TAP_WAIT_FR_TIME_OUT_POS = 2
BMI3_TAP_MAX_PEAKS_MASK = 0x0038
BMI3_TAP_MAX_PEAKS_POS = 3
BMI3_TAP_MODE_MASK = 0x00C0
BMI3_TAP_MODE_POS = 6
BMI3_TAP_PEAK_THRES_MASK = 0x03FF
BMI3_TAP_MAX_GEST_DUR_MASK = 0xFC00
BMI3_TAP_MAX_GEST_DUR_POS = 10
BMI3_TAP_MAX_DUR_BW_PEAKS_MASK = 0x000F
BMI3_TAP_SHOCK_SETT_DUR_MASK = 0x00F0
BMI3_TAP_SHOCK_SETT_DUR_POS = 4
BMI3_TAP_MIN_QUITE_DUR_BW_TAPS_MASK = 0x0F00
BMI3_TAP_MIN_QUITE_DUR_BW_TAPS_POS = 8
BMI3_TAP_QUITE_TIME_AFTR_GEST_MASK = 0xF000
BMI3_TAP_QUITE_TIME_AFTR_GEST_POS = 12

## Tap status bits
BMI3_TAP_DET_STATUS_SINGLE = 0x0008
BMI3_TAP_DET_STATUS_DOUBLE = 0x0010
BMI3_TAP_DET_STATUS_TRIPLE = 0x0020

## Sensor data types
BMI323_ACCEL = 1
BMI323_GYRO = 2
BMI323_ANY_MOTION = 3
BMI323_NO_MOTION = 4
BMI323_SIG_MOTION = 2
BMI323_STEP_COUNTER = 5
BMI323_TILT = 6
BMI323_ORIENTATION = 8
BMI323_FLAT = 9
BMI323_TAP = 10


## Interrupt pin selection enum
class eInt_t:
  eINT1 = BMI3_INT1  ## INT1 pin
  eINT2 = BMI3_INT2  ## INT2 pin


## Axis selection mask
class eAxis_t:
  eAxisX = 0x01  ## X axis
  eAxisY = 0x02  ## Y axis
  eAxisZ = 0x04  ## Z axis
  eAxisXYZ = 0x07  ## all axes


## Any-motion configuration
class bmi3_any_motion_config:
  """Any-motion configuration."""

  def __init__(self, duration=9, slope_thres=9, acc_ref_up=1, hysteresis=5, wait_time=4):
    self.duration = duration  # duration in 20 ms units
    self.slope_thres = slope_thres  # slope threshold
    self.acc_ref_up = acc_ref_up  # reference update mode
    self.hysteresis = hysteresis  # hysteresis
    self.wait_time = wait_time  # wait time


## No-motion configuration
class bmi3_no_motion_config:
  """No-motion configuration."""

  def __init__(self, duration=9, slope_thres=9, acc_ref_up=1, hysteresis=5, wait_time=5):
    self.duration = duration  # duration in 20 ms units
    self.slope_thres = slope_thres  # slope threshold
    self.acc_ref_up = acc_ref_up  # reference update mode
    self.hysteresis = hysteresis  # hysteresis
    self.wait_time = wait_time  # wait time


## Significant-motion configuration
class bmi3_sig_motion_config:
  """Significant-motion configuration."""

  def __init__(self, block_size=200, peak_2_peak_min=30, peak_2_peak_max=30, mcr_min=0x10, mcr_max=0x10):
    self.block_size = block_size  # segment size
    self.peak_2_peak_min = peak_2_peak_min  # min peak-to-peak accel
    self.peak_2_peak_max = peak_2_peak_max  # max peak-to-peak accel
    self.mcr_min = mcr_min  # min mean crossing rate
    self.mcr_max = mcr_max  # max mean crossing rate


## Flat detection configuration
class bmi3_flat_config:
  """Flat detection configuration."""

  def __init__(self, theta=9, blocking=3, hold_time=50, hysteresis=9, slope_thres=0xCD):
    self.theta = theta  # max tilt angle
    self.blocking = blocking  # blocking mode
    self.hold_time = hold_time  # min flat duration
    self.hysteresis = hysteresis  # hysteresis
    self.slope_thres = slope_thres  # slope threshold


## Tilt configuration
class bmi3_tilt_config:
  """Tilt configuration."""

  def __init__(self, segment_size=90, min_tilt_angle=200, beta_acc_mean=0x00FF):
    self.segment_size = segment_size
    self.min_tilt_angle = min_tilt_angle
    self.beta_acc_mean = beta_acc_mean


## Orientation configuration
class bmi3_orientation_config:
  """Orientation configuration."""

  def __init__(self, ud_en=1, hold_time=4, hysteresis=5, theta=16, mode=1, slope_thres=30, blocking=3):
    self.ud_en = ud_en  # face-up/down enable
    self.hold_time = hold_time  # hold time (20 ms units)
    self.hysteresis = hysteresis  # hysteresis
    self.theta = theta  # max tilt angle
    self.mode = mode  # detection mode
    self.slope_thres = slope_thres  # slope threshold
    self.blocking = blocking  # blocking mode


## Tap configuration
class bmi3_tap_detector_config:
  """Tap detector configuration."""

  def __init__(
    self,
    axis_sel=1,
    wait_for_timeout=1,
    max_peaks_for_tap=5,
    mode=1,
    tap_peak_thres=0x2C,
    max_gest_dur=0x11,
    max_dur_between_peaks=5,
    tap_shock_settling_dur=5,
    min_quite_dur_between_taps=7,
    quite_time_after_gest=5,
  ):
    self.axis_sel = axis_sel  # axis selection
    self.wait_for_timeout = wait_for_timeout  # gesture confirmation
    self.max_peaks_for_tap = max_peaks_for_tap  # max expected peaks
    self.mode = mode  # detection mode
    self.tap_peak_thres = tap_peak_thres  # peak threshold
    self.max_gest_dur = max_gest_dur  # max gesture duration
    self.max_dur_between_peaks = max_dur_between_peaks  # max duration between peaks
    self.tap_shock_settling_dur = tap_shock_settling_dur  # shock settling duration
    self.min_quite_dur_between_taps = min_quite_dur_between_taps  # min quiet time between taps
    self.quite_time_after_gest = quite_time_after_gest  # quiet time after gesture


## Accelerometer range enum
class eAccelRange_t:
  eAccelRange2G = 0x00  ## +/- 2g range
  eAccelRange4G = 0x01  ## +/- 4g range
  eAccelRange8G = 0x02  ## +/- 8g range
  eAccelRange16G = 0x03  ## +/- 16g range


## Gyroscope range enum
class eGyroRange_t:
  eGyroRange125DPS = 0x00  ## +/- 125 dps range
  eGyroRange250DPS = 0x01  ## +/- 250 dps range
  eGyroRange500DPS = 0x02  ## +/- 500 dps range
  eGyroRange1000DPS = 0x03  ## +/- 1000 dps range
  eGyroRange2000DPS = 0x04  ## +/- 2000 dps range


## Accelerometer ODR enum
class eAccelODR_t:
  eAccelODR0_78125Hz = 0x01  ## 0.78125 Hz
  eAccelODR1_5625Hz = 0x02  ## 1.5625 Hz
  eAccelODR3_125Hz = 0x03  ## 3.125 Hz
  eAccelODR6_25Hz = 0x04  ## 6.25 Hz
  eAccelODR12_5Hz = 0x05  ## 12.5 Hz
  eAccelODR25Hz = 0x06  ## 25 Hz
  eAccelODR50Hz = 0x07  ## 50 Hz
  eAccelODR100Hz = 0x08  ## 100 Hz
  eAccelODR200Hz = 0x09  ## 200 Hz
  eAccelODR400Hz = 0x0A  ## 400 Hz
  eAccelODR800Hz = 0x0B  ## 800 Hz
  eAccelODR1600Hz = 0x0C  ## 1600 Hz
  eAccelODR3200Hz = 0x0D  ## 3200 Hz
  eAccelODR6400Hz = 0x0E  ## 6400 Hz


## Gyroscope ODR enum
class eGyroODR_t:
  eGyroODR0_78125Hz = 0x01  ## 0.78125 Hz
  eGyroODR1_5625Hz = 0x02  ## 1.5625 Hz
  eGyroODR3_125Hz = 0x03  ## 3.125 Hz
  eGyroODR6_25Hz = 0x04  ## 6.25 Hz
  eGyroODR12_5Hz = 0x05  ## 12.5 Hz
  eGyroODR25Hz = 0x06  ## 25 Hz
  eGyroODR50Hz = 0x07  ## 50 Hz
  eGyroODR100Hz = 0x08  ## 100 Hz
  eGyroODR200Hz = 0x09  ## 200 Hz
  eGyroODR400Hz = 0x0A  ## 400 Hz
  eGyroODR800Hz = 0x0B  ## 800 Hz
  eGyroODR1600Hz = 0x0C  ## 1600 Hz
  eGyroODR3200Hz = 0x0D  ## 3200 Hz
  eGyroODR6400Hz = 0x0E  ## 6400 Hz


## Accelerometer mode enum
class eAccelMode_t:
  eAccelModeLowPower = 0  ## low power mode
  eAccelModeNormal = 1  ## normal mode
  eAccelModeHighPerf = 2  ## high performance mode


## Gyroscope mode enum
class eGyroMode_t:
  eGyroModeLowPower = 0  ## low power mode
  eGyroModeNormal = 1  ## normal mode
  eGyroModeHighPerf = 2  ## high performance mode


## Sensor data structure
class sSensorData(Structure):
  _pack_ = 1
  _fields_ = [('x', c_float), ('y', c_float), ('z', c_float)]

  def __init__(self, x=0.0, y=0.0, z=0.0):
    self.x = x
    self.y = y
    self.z = z

  def __str__(self):
    return f"x={self.x:.3f}, y={self.y:.3f}, z={self.z:.3f}"


class DFRobot_BMI323:
  """BMI323 sensor class (I2C interface)."""

  def __init__(self, bus=1, i2c_addr=DFRobot_BMI323_IIC_ADDR):
    """Constructor."""
    self.i2cbus = smbus.SMBus(bus)
    self.i2c_addr = i2c_addr
    self._initialized = False
    self._accel_range = 2.0  # default +/-2g
    self._gyro_range = 250.0  # default +/-250 dps
    self._dummy_byte = BMI3_I2C_DUMMY_BYTE  # I2C uses 2 dummy bytes
    self._chip_id = 0
    self._resolution = 16  # 16-bit resolution

  def begin(self):
    """Initialization function.
    @details Initialize I2C interface, chip registers and feature context
    @return bool type, indicates the initialization status
    @retval ERR_OK Initialization successful
    @retval ERR_DATA_BUS or ERR_IC_VERSION Initialization failed
    """
    try:
      logger.info("Soft reset...")
      rslt = self._soft_reset()
      if rslt != BMI323_OK:
        logger.error("Soft reset failed")
        return ERR_DATA_BUS

      logger.info("Reading chip ID...")
      chip_id_data = self._read_regs(BMI3_REG_CHIP_ID, 2)
      if chip_id_data is None or len(chip_id_data) < 2:
        logger.error("ERR_DATA_BUS: failed to read chip ID")
        return ERR_DATA_BUS

      self._chip_id = chip_id_data[0] & BMI3_CHIP_ID_MASK
      rev_id = (chip_id_data[1] & BMI3_REV_ID_MASK) >> BMI3_REV_ID_POS

      logger.info("chip_id=0x%02X, rev_id=0x%02X", self._chip_id, rev_id)

      if self._chip_id != DFRobot_BMI323_CHIP_ID:
        logger.warning("ERR_IC_VERSION: chip id mismatch, expect 0x%02X, got 0x%02X", DFRobot_BMI323_CHIP_ID, self._chip_id)
        return ERR_IC_VERSION

      self._accel_bit_width = 14 if rev_id == 1 else 13

      logger.info("Enabling feature engine...")
      rslt = self._enable_feature_engine()
      if rslt != BMI323_OK:
        logger.error("Enable feature engine failed")
        return ERR_DATA_BUS

      # Context selection (wearable) skipped; requires extra feature settings.
      logger.info("Configuring context selection (wearable mode)... skipped")

      self._initialized = True

      rslt = self._setAxisRemap()
      if not rslt:
        logger.error("Set axis remap failed")
        return ERR_DATA_BUS

      logger.info("BMI323 init ok")
      return ERR_OK

    except Exception as e:
      logger.error("Initialization failed: %s", str(e))
      import traceback

      traceback.print_exc()
      return ERR_DATA_BUS

  def config_accel(self, odr, range_val, mode=eAccelMode_t.eAccelModeNormal):
    """Configure accelerometer.
    @param odr Output data rate selection (see: eAccelODR_t)
    @n Available rates:
    @n - eAccelODR0_78125Hz:  0.78125 Hz
    @n - eAccelODR1_5625Hz:   1.5625 Hz
    @n - eAccelODR3_125Hz:    3.125 Hz
    @n - eAccelODR6_25Hz:     6.25 Hz
    @n - eAccelODR12_5Hz:     12.5 Hz
    @n - eAccelODR25Hz:       25 Hz
    @n - eAccelODR50Hz:       50 Hz
    @n - eAccelODR100Hz:      100 Hz
    @n - eAccelODR200Hz:      200 Hz
    @n - eAccelODR400Hz:      400 Hz
    @n - eAccelODR800Hz:      800 Hz
    @n - eAccelODR1600Hz:     1600 Hz
    @n - eAccelODR3200Hz:     3200 Hz
    @n - eAccelODR6400Hz:     6400 Hz
    @n @note ODR range limitations (based on operating mode):
    @n - Low power mode: 0.78Hz ~ 400Hz
    @n - Normal mode:    12.5Hz ~ 6400Hz
    @n - High performance mode: 12.5Hz ~ 6400Hz
    @param range_val Range selection (see: eAccelRange_t)
    @n Available ranges:
    @n - eAccelRange2G:   ±2g
    @n - eAccelRange4G:   ±4g
    @n - eAccelRange8G:   ±8g
    @n - eAccelRange16G:  ±16g
    @param mode Operating mode selection (see: eAccelMode_t), default eAccelModeNormal
    @n Available modes:
    @n - eAccelModeLowPower:  Low power mode
    @n - eAccelModeNormal:    Normal mode (default)
    @n - eAccelModeHighPerf:  High performance mode
    @return bool type, indicates the configuration status
    @retval True Configuration successful
    @retval False Configuration failed
    """
    if not self._initialized:
      logger.error("Sensor not initialized")
      return False

    # Validate ODR range based on operating mode
    is_valid, error_msg = self._validate_odr_range(odr, mode, 'accel')
    if not is_valid:
      logger.error("Accel ODR validation failed: %s", error_msg)
      return False

    try:
      reg_data = self._read_regs(BMI3_REG_ACC_CONF, 2)
      if reg_data is None or len(reg_data) < 2:
        logger.error("Read accel config failed")
        return False

      if mode == eAccelMode_t.eAccelModeLowPower:
        acc_mode = BMI3_ACC_MODE_LOW_PWR
        avg_num = BMI3_ACC_AVG2
        bwp = BMI3_ACC_BW_ODR_HALF
      elif mode == eAccelMode_t.eAccelModeNormal:
        acc_mode = BMI3_ACC_MODE_NORMAL
        avg_num = BMI3_ACC_AVG1
        bwp = BMI3_ACC_BW_ODR_HALF
      elif mode == eAccelMode_t.eAccelModeHighPerf:
        acc_mode = BMI3_ACC_MODE_HIGH_PERF
        avg_num = BMI3_ACC_AVG1
        bwp = BMI3_ACC_BW_ODR_QUARTER
      else:
        acc_mode = BMI3_ACC_MODE_NORMAL
        avg_num = BMI3_ACC_AVG1
        bwp = BMI3_ACC_BW_ODR_HALF

      reg_byte0 = 0
      reg_byte1 = 0

      reg_byte0 = (reg_byte0 & ~BMI3_ACC_ODR_MASK) | (odr & BMI3_ACC_ODR_MASK)
      reg_byte0 = (reg_byte0 & ~BMI3_ACC_RANGE_MASK) | ((range_val << BMI3_ACC_RANGE_POS) & BMI3_ACC_RANGE_MASK)
      reg_byte0 = (reg_byte0 & ~BMI3_ACC_BW_MASK) | ((bwp << BMI3_ACC_BW_POS) & BMI3_ACC_BW_MASK)

      reg_byte1_temp = 0
      reg_byte1_temp = (reg_byte1_temp & ~BMI3_ACC_AVG_NUM_MASK) | ((avg_num << BMI3_ACC_AVG_NUM_POS) & BMI3_ACC_AVG_NUM_MASK)
      reg_byte1_temp = (reg_byte1_temp & ~BMI3_ACC_MODE_MASK) | ((acc_mode << BMI3_ACC_MODE_POS) & BMI3_ACC_MODE_MASK)
      reg_byte1 = (reg_byte1_temp >> 8) & 0xFF

      config_data = [reg_byte0, reg_byte1]
      rslt = self._write_regs(BMI3_REG_ACC_CONF, config_data)
      if rslt != BMI323_OK:
        logger.error("Write accel config failed")
        return False

      if range_val == eAccelRange_t.eAccelRange2G:
        self._accel_range = 2.0
      elif range_val == eAccelRange_t.eAccelRange4G:
        self._accel_range = 4.0
      elif range_val == eAccelRange_t.eAccelRange8G:
        self._accel_range = 8.0
      elif range_val == eAccelRange_t.eAccelRange16G:
        self._accel_range = 16.0
      else:
        self._accel_range = 2.0

      logger.info("Accel configured: ODR=0x%02X, Range=0x%02X, Mode=0x%02X", odr, range_val, acc_mode)
      return True

    except Exception as e:
      logger.error("Configure accel failed: %s", str(e))
      return False

  def config_gyro(self, odr, range_val, mode=eGyroMode_t.eGyroModeNormal):
    """Configure gyroscope.
    @param odr Output data rate selection (see: eGyroODR_t)
    @n Available rates:
    @n - eGyroODR0_78125Hz: 0.78125 Hz
    @n - eGyroODR1_5625Hz:  1.5625 Hz
    @n - eGyroODR3_125Hz:   3.125 Hz
    @n - eGyroODR6_25Hz:    6.25 Hz
    @n - eGyroODR12_5Hz:    12.5 Hz
    @n - eGyroODR25Hz:      25 Hz
    @n - eGyroODR50Hz:      50 Hz
    @n - eGyroODR100Hz:     100 Hz
    @n - eGyroODR200Hz:     200 Hz
    @n - eGyroODR400Hz:     400 Hz
    @n - eGyroODR800Hz:     800 Hz
    @n - eGyroODR1600Hz:    1600 Hz
    @n - eGyroODR3200Hz:    3200 Hz
    @n - eGyroODR6400Hz:    6400 Hz
    @n @note ODR range limitations (based on operating mode):
    @n - Low power mode: 0.78Hz ~ 400Hz
    @n - Normal mode:    12.5Hz ~ 6400Hz
    @n - High performance mode: 12.5Hz ~ 6400Hz
    @param range_val Range selection (see: eGyroRange_t)
    @n Available ranges:
    @n - eGyroRange125DPS:   ±125dps
    @n - eGyroRange250DPS:   ±250dps
    @n - eGyroRange500DPS:   ±500dps
    @n - eGyroRange1000DPS:  ±1000dps
    @n - eGyroRange2000DPS:  ±2000dps
    @param mode Operating mode selection (see: eGyroMode_t), default eGyroModeNormal
    @n Available modes:
    @n - eGyroModeLowPower:  Low power mode
    @n - eGyroModeNormal:    Normal mode (default)
    @n - eGyroModeHighPerf:  High performance mode
    @return bool type, indicates the configuration status
    @retval True Configuration successful
    @retval False Configuration failed
    """
    if not self._initialized:
      logger.error("Sensor not initialized")
      return False

    # Validate ODR range based on operating mode
    is_valid, error_msg = self._validate_odr_range(odr, mode, 'gyro')
    if not is_valid:
      logger.error("Gyro ODR validation failed: %s", error_msg)
      return False

    try:
      reg_data = self._read_regs(BMI3_REG_GYR_CONF, 2)
      if reg_data is None or len(reg_data) < 2:
        logger.error("Read gyro config failed")
        return False

      if mode == eGyroMode_t.eGyroModeLowPower:
        gyr_mode = BMI3_GYR_MODE_LOW_PWR
        avg_num = BMI3_GYR_AVG2
        bwp = BMI3_GYR_BW_ODR_HALF
      elif mode == eGyroMode_t.eGyroModeNormal:
        gyr_mode = BMI3_GYR_MODE_NORMAL
        avg_num = BMI3_GYR_AVG1
        bwp = BMI3_GYR_BW_ODR_HALF
      elif mode == eGyroMode_t.eGyroModeHighPerf:
        gyr_mode = BMI3_GYR_MODE_HIGH_PERF
        avg_num = BMI3_GYR_AVG1
        bwp = BMI3_GYR_BW_ODR_QUARTER
      else:
        gyr_mode = BMI3_GYR_MODE_NORMAL
        avg_num = BMI3_GYR_AVG1
        bwp = BMI3_GYR_BW_ODR_HALF

      reg_byte0 = 0
      reg_byte1 = 0

      reg_byte0 = (reg_byte0 & ~BMI3_GYR_ODR_MASK) | (odr & BMI3_GYR_ODR_MASK)
      reg_byte0 = (reg_byte0 & ~BMI3_GYR_RANGE_MASK) | ((range_val << BMI3_GYR_RANGE_POS) & BMI3_GYR_RANGE_MASK)
      reg_byte0 = (reg_byte0 & ~BMI3_GYR_BW_MASK) | ((bwp << BMI3_GYR_BW_POS) & BMI3_GYR_BW_MASK)

      reg_byte1_temp = 0
      reg_byte1_temp = (reg_byte1_temp & ~BMI3_GYR_AVG_NUM_MASK) | ((avg_num << BMI3_GYR_AVG_NUM_POS) & BMI3_GYR_AVG_NUM_MASK)
      reg_byte1_temp = (reg_byte1_temp & ~BMI3_GYR_MODE_MASK) | ((gyr_mode << BMI3_GYR_MODE_POS) & BMI3_GYR_MODE_MASK)
      reg_byte1 = (reg_byte1_temp >> 8) & 0xFF

      config_data = [reg_byte0, reg_byte1]
      rslt = self._write_regs(BMI3_REG_GYR_CONF, config_data)
      if rslt != BMI323_OK:
        logger.error("Write gyro config failed")
        return False

      if range_val == eGyroRange_t.eGyroRange125DPS:
        self._gyro_range = 125.0
      elif range_val == eGyroRange_t.eGyroRange250DPS:
        self._gyro_range = 250.0
      elif range_val == eGyroRange_t.eGyroRange500DPS:
        self._gyro_range = 500.0
      elif range_val == eGyroRange_t.eGyroRange1000DPS:
        self._gyro_range = 1000.0
      elif range_val == eGyroRange_t.eGyroRange2000DPS:
        self._gyro_range = 2000.0
      else:
        self._gyro_range = 250.0

      logger.info("Gyro configured: ODR=0x%02X, Range=0x%02X, Mode=0x%02X", odr, range_val, gyr_mode)
      return True

    except Exception as e:
      logger.error("Configure gyro failed: %s", str(e))
      return False

  def get_accel_gyro_data(self, accel, gyro):
    """Read accelerometer and gyroscope simultaneously and return physical units.
    @details Read accelerometer and gyroscope raw data at once, convert to g/dps and return
    @param accel Accelerometer output
    @param gyro Gyroscope output
    @return bool type, indicates the read status
    @retval True Read successful
    @retval False Read failed
    """
    if not self._initialized:
      logger.error("Sensor not initialized")
      return False

    if accel is None or gyro is None:
      logger.error("Output parameter is None")
      return False

    try:
      reg_data = self._read_regs(BMI3_REG_ACC_DATA_X, 19)
      if reg_data is None or len(reg_data) < 19:
        logger.error("Read sensor data failed")
        return False

      accel_x_raw = self._int16_from_bytes(reg_data[0], reg_data[1])
      accel_y_raw = self._int16_from_bytes(reg_data[2], reg_data[3])
      accel_z_raw = self._int16_from_bytes(reg_data[4], reg_data[5])

      gyro_x_raw = self._int16_from_bytes(reg_data[6], reg_data[7])
      gyro_y_raw = self._int16_from_bytes(reg_data[8], reg_data[9])
      gyro_z_raw = self._int16_from_bytes(reg_data[10], reg_data[11])

      accel.x = self._lsb_to_g(accel_x_raw, self._accel_range)
      accel.y = self._lsb_to_g(accel_y_raw, self._accel_range)
      accel.z = self._lsb_to_g(accel_z_raw, self._accel_range)

      gyro.x = self._lsb_to_dps(gyro_x_raw, self._gyro_range)
      gyro.y = self._lsb_to_dps(gyro_y_raw, self._gyro_range)
      gyro.z = self._lsb_to_dps(gyro_z_raw, self._gyro_range)

      return True

    except Exception as e:
      logger.error("Read sensor data failed: %s", str(e))
      return False

  def get_temperature(self):
    """Read die temperature in degrees Celsius.
    @details Reads raw temperature from the sensor and converts it using the official formula:
    temperature (°C) = (int16_t)raw / 512.0 + 23.0. Accelerometer or gyroscope must be configured first.
    @return float Temperature in °C, or 0.0 if the sensor is not initialized or the read fails
    """
    if not self._initialized:
      logger.error("Sensor not initialized")
      return 0.0

    try:
      reg_data = self._read_regs(BMI3_REG_TEMP_DATA, 2)
      if reg_data is None or len(reg_data) < 2:
        logger.error("Read temperature failed")
        return 0.0

      raw_temp = self._int16_from_bytes(reg_data[0], reg_data[1])
      return (float(raw_temp) / 512.0) + 23.0

    except Exception as e:
      logger.error("Read temperature failed: %s", str(e))
      return 0.0

  def enable_step_counter_int(self, pin):
    """Enable step counter interrupt function.
    @details Configure step counter function and map to specified interrupt pin, interrupt will be triggered when step count changes
    @param pin Bound interrupt pin (eINT1 or eINT2)
    @return bool type, indicates the configuration status
    @retval True Configuration successful
    @retval False Configuration failed
    """
    if not self._initialized:
      logger.error("Sensor not initialized")
      return False

    # Validate ODR requirement: at least 50Hz in low power mode
    is_valid, error_msg = self._validate_feature_odr_requirement('step_counter', 50.0)
    if not is_valid:
      logger.error("Step counter ODR validation failed: %s", error_msg)
      return False

    try:
      if not self._enableStepCounterFeature():
        logger.error("Enable step_counter feature failed")
        return False

      if not self._configureIntPin(pin):
        logger.error("Configure interrupt pin failed")
        return False

      if not self._mapInterrupt(pin, 'step_detector'):
        logger.error("Map interrupt failed")
        return False

      logger.info("Step counter interrupt enabled: pin=%d", pin)
      return True

    except Exception as e:
      logger.error("Enable step counter interrupt failed: %s", str(e))
      return False

  def read_step_counter(self):
    """Read step counter data.
    @return uint16_t Step count value (16-bit, saturated at 0xFFFF).
    @retval 0 Step counter read failed
    """
    if not self._initialized:
      logger.error("Sensor not initialized")
      return 0

    try:
      reg_data = self._read_regs(BMI3_REG_FEATURE_IO2, 4)
      if reg_data is None or len(reg_data) < 4:
        logger.error("Read step counter failed")
        return 0

      step_count = (reg_data[3] << 24) | (reg_data[2] << 16) | (reg_data[1] << 8) | reg_data[0]

      if step_count > 0xFFFF:
        step_count = 0xFFFF

      return step_count

    except Exception as e:
      logger.error("Read step counter failed: %s", str(e))
      return 0

  def get_int_status(self):
    """Get interrupt status.
    @details Read and combine interrupt status from both INT1 and INT2 pins. The return value is the OR combination of INT1 and INT2 status registers, allowing you to check all interrupt events regardless of which pin they are mapped to.
    @return uint16_t Combined interrupt status register value (INT1 | INT2). Each bit represents a different interrupt type:
    @n - BMI3_INT_STATUS_ANY_MOTION: Any motion detected
    @n - BMI3_INT_STATUS_NO_MOTION: No motion detected
    @n - BMI3_INT_STATUS_FLAT: Flat detection
    @n - BMI3_INT_STATUS_ORIENTATION: Orientation change
    @n - BMI3_INT_STATUS_STEP_DETECTOR: Step detected
    @n - BMI3_INT_STATUS_SIG_MOTION: Significant motion detected
    @n - BMI3_INT_STATUS_TILT: Tilt detected
    @n - BMI3_INT_STATUS_TAP: Tap detected
    """
    if not self._initialized:
      return 0

    try:
      int_status = 0

      int1_data = self._read_regs(BMI3_REG_INT_STATUS_INT1, 2)
      if int1_data and len(int1_data) >= 2:
        int1_status = (int1_data[1] << 8) | int1_data[0]
        int_status |= int1_status

      int2_data = self._read_regs(BMI3_REG_INT_STATUS_INT2, 2)
      if int2_data and len(int2_data) >= 2:
        int2_status = (int2_data[1] << 8) | int2_data[0]
        int_status |= int2_status

      return int_status

    except Exception as e:
      logger.error("Failed to read interrupt status: %s", str(e))
      return 0

  def enable_any_motion_int(self, config, pin, axisMask=eAxis_t.eAxisXYZ):
    """Configure any-motion threshold interrupt (using official structure parameters).
    @param config Any-motion configuration structure (see bmi3_any_motion_config)
    @n Parameter description:
    @n - slope_thres: Acceleration slope threshold, range
    @n 0-4095, unit 1.953mg/LSB (official example: 9 ≈ 17.6mg)
    @n - hysteresis: Hysteresis value, range 0-1023, unit 1.953mg/LSB (official example: 5
    @n ≈ 9.8mg)
    @n - duration: Duration, range 0-8191, unit 20ms (official example: 9 = 180ms)
    @n - acc_ref_up: Acceleration reference update mode, 0=OnEvent, 1=Always (official example: 1)
    @n - wait_time: Wait time, range 0-7, unit 20ms (official example: 4-5 = 80-100ms)
    @param pin Bound interrupt pin
    @param axisMask Axis selection mask (default: eAxisXYZ)
    @return bool type, indicates the configuration status
    @retval True Configuration successful
    @retval False Configuration failed
    """
    if not self._initialized:
      logger.error("Sensor not initialized")
      return False

    if config is None:
      logger.error("Config is None")
      return False

    try:
      if not self._configureIntPin(pin):
        logger.error("Configure interrupt pin failed")
        return False

      if not self._setAnyMotionConfig(config):
        logger.error("Set any-motion config failed")
        return False

      if not self._enableAnyMotionFeature(axisMask):
        logger.error("Enable any-motion feature failed")
        return False

      if not self._mapInterrupt(pin, 'any_motion'):
        logger.error("Map interrupt failed")
        return False

      logger.info("Any motion interrupt enabled: pin=%d, axisMask=0x%02X", pin, axisMask)
      return True

    except Exception as e:
      logger.error("Enable any-motion interrupt failed: %s", str(e))
      return False

  def enable_no_motion_int(self, config, pin, axisMask=eAxis_t.eAxisXYZ):
    """Configure no-motion threshold interrupt (using official structure parameters).
    @param config No-motion detection configuration structure (see bmi3_no_motion_config)
    @n Parameter description:
    @n - slope_thres: Acceleration slope threshold, range
    @n 0-4095, unit 1.953mg/LSB (official example: 9 ≈ 17.6mg)
    @n - hysteresis: Hysteresis value, range 0-1023, unit 1.953mg/LSB (official example: 5
    @n ≈ 9.8mg)
    @n - duration: Duration, range 0-8191, unit 20ms (official example: 9 = 180ms)
    @n - acc_ref_up: Acceleration reference update mode, 0=OnEvent, 1=Always (official example: 1)
    @n - wait_time: Wait time, range 0-7, unit 20ms (official example: 5 = 100ms)
    @param pin Bound interrupt pin
    @param axisMask Axis selection mask (default: eAxisXYZ)
    @return bool type, indicates the configuration status
    @retval True Configuration successful
    @retval False Configuration failed
    """
    if not self._initialized:
      logger.error("Sensor not initialized")
      return False

    if config is None:
      logger.error("Config is None")
      return False

    try:
      if not self._configureIntPin(pin):
        logger.error("Configure interrupt pin failed")
        return False

      if not self._setNoMotionConfig(config):
        logger.error("Set no-motion config failed")
        return False

      if not self._enableNoMotionFeature(axisMask):
        logger.error("Enable no-motion feature failed")
        return False

      if not self._mapInterrupt(pin, 'no_motion'):
        logger.error("Map interrupt failed")
        return False

      logger.info("No-motion interrupt enabled: pin=%d, axisMask=0x%02X", pin, axisMask)
      return True

    except Exception as e:
      logger.error("Enable no-motion interrupt failed: %s", str(e))
      return False

  def enable_sig_motion_int(self, config, pin):
    """Configure significant motion detection interrupt (using official structure parameters).
    @param config Significant motion configuration structure (see bmi3_sig_motion_config)
    @n Parameter description:
    @n - block_size: Detection segment size, range 0-65535 (official example: 200)
    @n - peak_2_peak_min: Peak-to-peak acceleration minimum, range 0-1023 (official example: 30)
    @n - peak_2_peak_max: Peak-to-peak acceleration maximum, range 0-1023 (official example: 30)
    @n - mcr_min: Mean crossing rate per second minimum, range 0-62 (official example: 0x10 = 16)
    @n - mcr_max: Mean crossing rate per second maximum, range 0-62 (official example: 0x10 = 16)
    @param pin Bound interrupt pin
    @return bool type, indicates the configuration status
    @retval True Configuration successful
    @retval False Configuration failed
    """
    if not self._initialized:
      logger.error("Sensor not initialized")
      return False

    if config is None:
      logger.error("Config is None")
      return False

    # Validate ODR requirement: at least 50Hz in low power mode
    is_valid, error_msg = self._validate_feature_odr_requirement('sig_motion', 50.0)
    if not is_valid:
      logger.error("Sig-motion ODR validation failed: %s", error_msg)
      return False

    try:
      if not self._configureIntPin(pin):
        logger.error("Configure interrupt pin failed")
        return False

      if not self._setSigMotionConfig(config):
        logger.error("Set sig-motion config failed")
        return False

      if not self._enableSigMotionFeature():
        logger.error("Enable sig-motion feature failed")
        return False

      if not self._mapInterrupt(pin, 'sig_motion'):
        logger.error("Map interrupt failed")
        return False

      logger.info("Sig-motion interrupt enabled: pin=%d", pin)
      return True

    except Exception as e:
      logger.error("Enable sig-motion interrupt failed: %s", str(e))
      return False

  def enable_flat_int(self, config, pin):
    """Configure flat detection interrupt (using official structure parameters).
    @param config Flat detection configuration structure (see bmi3_flat_config)
    @n Parameter description:
    @n - theta: Maximum allowed tilt angle, range 0-63, angle calculated as 64 *
    @n (tan(angle)^2) (official example: 9)
    @n - blocking: Blocking mode, 0=MODE_0(disabled), 1=MODE_1(>1.5g),
    @n 2=MODE_2(>1.5g or slope>half threshold), 3=MODE_3(>1.5g or slope>threshold) (official example: 3)
    @n - hold_time: Minimum duration for device to maintain flat state, range 0-255, unit
    @n 20ms (official example: 50 = 1000ms)
    @n - hysteresis: Hysteresis angle for flat detection, range 0-255 (official example: 9)
    @n - slope_thres: Minimum slope between consecutive acceleration samples, range 0-255 (official example: 0xCD
    @n = 205)
    @param pin Bound interrupt pin
    @return bool type, indicates the configuration status
    @retval True Configuration successful
    @retval False Configuration failed
    """
    if not self._initialized:
      logger.error("Sensor not initialized")
      return False

    if config is None:
      logger.error("Config is None")
      return False

    try:
      if not self._configureIntPin(pin):
        logger.error("Configure interrupt pin failed")
        return False

      if not self._setFlatConfig(config):
        logger.error("Set flat config failed")
        return False

      if not self._enableFlatFeature():
        logger.error("Enable flat feature failed")
        return False

      if not self._mapInterrupt(pin, 'flat'):
        logger.error("Map interrupt failed")
        return False

      logger.info("Flat interrupt enabled: pin=%d", pin)
      return True

    except Exception as e:
      logger.error("Enable flat interrupt failed: %s", str(e))
      return False

  def enable_orientation_int(self, config, pin):
    """Configure orientation detection interrupt (using official structure parameters).
    @param config Orientation detection configuration structure (see bmi3_orientation_config)
    @n Parameter description:
    @n - ud_en: Whether to detect flip (face up/down), 0=disabled, 1=enabled (official example: 1)
    @n - hold_time: Required duration for orientation change detection, range 0-255, unit 20ms (official example: 4 = 80ms)
    @n - hysteresis: Hysteresis for orientation detection, range 0-255 (official example: 5)
    @n - theta: Maximum allowed tilt angle, range 0-63, angle=64*(tan(angle)^2) (official example: 16)
    @n - mode: Orientation detection mode, 0/3=symmetric, 1=high asymmetric, 2=low asymmetric (official example: 1)
    @n - slope_thres: Slope threshold to prevent false detection due to violent motion, range 0-255 (official example: 30)
    @n - blocking: Blocking mode, 0-3 (official example: 3)
    @param pin Bound interrupt pin
    @return bool type, indicates the configuration status
    @retval True Configuration successful
    @retval False Configuration failed
    """
    if not self._initialized:
      logger.error("Sensor not initialized")
      return False

    if config is None:
      logger.error("Config is None")
      return False

    try:
      if not self._configureIntPin(pin):
        logger.error("Configure interrupt pin failed")
        return False

      if not self._setOrientationConfig(config):
        logger.error("Set orientation config failed")
        return False

      if not self._enableOrientationFeature():
        logger.error("Enable orientation feature failed")
        return False

      if not self._mapInterrupt(pin, 'orientation'):
        logger.error("Map interrupt failed")
        return False

      logger.info("Orientation interrupt enabled: pin=%d", pin)
      return True

    except Exception as e:
      logger.error("Enable orientation interrupt failed: %s", str(e))
      return False

  def read_orientation(self):
    """Read orientation detection output.
    @return tuple (portraitLandscape, faceUpDown) or (None, None) on failure
    @n portraitLandscape: Portrait/Landscape status
    @n - 0: Portrait Upright
    @n - 1: Landscape Left
    @n - 2: Portrait Upside Down
    @n - 3: Landscape Right
    @n faceUpDown: Face up/down status
    @n - 0: Face Up
    @n - 1: Face Down
    @retval (portraitLandscape, faceUpDown) Read successful
    @retval (None, None) Read failed or feature not enabled
    """
    if not self._initialized:
      logger.error("Sensor not initialized")
      return (None, None)

    try:
      reg_data = self._read_regs(BMI3_REG_FEATURE_EVENT_EXT, 2)
      if reg_data is None or len(reg_data) < 2:
        logger.error("Read orientation data failed")
        return (None, None)

      portrait_landscape = reg_data[0] & BMI3_ORIENTATION_PORTRAIT_LANDSCAPE_MASK

      face_up_down = (reg_data[0] & BMI3_ORIENTATION_FACEUP_DOWN_MASK) >> BMI3_ORIENTATION_FACEUP_DOWN_POS

      return (portrait_landscape, face_up_down)

    except Exception as e:
      logger.error("Read orientation data failed: %s", str(e))
      return (None, None)

  def enable_tap_int(self, config, pin, enableSingle=True, enableDouble=True, enableTriple=True):
    """Configure tap detection interrupt (using official structure parameters).
    @param config Tap detection configuration structure (see bmi3_tap_detector_config)
    @n Key parameters (refer to tap.c):
    @n - axis_sel: Select axis for tap detection (0=X, 1=Y, 2=Z)
    @n - mode: Detection mode (0=sensitive, 1=normal, 2=robust)
    @n - tap_peak_thres / tap_shock_settling_dur etc. for timing/amplitude thresholds to determine tap
    @param pin Bound interrupt pin
    @param enableSingle Whether to enable single tap detection (default true)
    @param enableDouble Whether to enable double tap detection (default true)
    @param enableTriple Whether to enable triple tap detection (default true)
    @return bool type, indicates the configuration status
    @retval True Configuration successful
    @retval False Configuration failed
    """
    if not self._initialized:
      logger.error("Sensor not initialized")
      return False

    if config is None:
      logger.error("Config is None")
      return False

    # Validate ODR requirement: at least 200Hz in low power mode
    is_valid, error_msg = self._validate_feature_odr_requirement('tap', 200.0)
    if not is_valid:
      logger.error("Tap ODR validation failed: %s", error_msg)
      return False

    try:
      if not self._configureIntPin(pin):
        logger.error("Configure interrupt pin failed")
        return False

      if not self._setTapConfig(config):
        logger.error("Set tap config failed")
        return False

      if not self._enableTapFeature(enableSingle, enableDouble, enableTriple):
        logger.error("Enable tap feature failed")
        return False

      if not self._mapInterrupt(pin, 'tap'):
        logger.error("Map interrupt failed")
        return False

      logger.info("Tap interrupt enabled: pin=%d, single=%d, double=%d, triple=%d", pin, enableSingle, enableDouble, enableTriple)
      return True

    except Exception as e:
      logger.error("Enable tap interrupt failed: %s", str(e))
      return False

  def read_tap_status(self):
    """Read tap detection status (single/double/triple tap).
    @return uint8_t Output mask (can combine BMI3_TAP_DET_STATUS_SINGLE/DOUBLE/TRIPLE), 0 on failure
    @retval Bitmask Read successful
    @retval 0 Read failed
    """
    if not self._initialized:
      logger.error("Sensor not initialized")
      return 0

    try:
      reg_data = self._read_regs(BMI3_REG_FEATURE_EVENT_EXT, 2)
      if reg_data is None or len(reg_data) < 2:
        logger.error("Read tap status failed")
        return 0

      tap_mask = reg_data[0] & (BMI3_TAP_DET_STATUS_SINGLE | BMI3_TAP_DET_STATUS_DOUBLE | BMI3_TAP_DET_STATUS_TRIPLE)

      return tap_mask

    except Exception as e:
      logger.error("Read tap status failed: %s", str(e))
      return 0

  def enable_tilt_int(self, config, pin):
    """Configure tilt detection interrupt (using official structure parameters).
    @param config Tilt detection configuration structure (see bmi3_tilt_config)
    @n Key parameters (refer to tilt.c):
    @n - segment_size: Time window for averaging reference vector, range 0-255
    @n - min_tilt_angle: Minimum tilt angle to exceed, range 0-255, angle=256*cos(angle)
    @n - beta_acc_mean: Low-pass averaging coefficient, range 0-65535
    @param pin Bound interrupt pin
    @return bool type, indicates the configuration status
    @retval True Configuration successful
    @retval False Configuration failed
    """
    if not self._initialized:
      logger.error("Sensor not initialized")
      return False

    if config is None:
      logger.error("Config is None")
      return False

    try:
      if not self._configureIntPin(pin):
        logger.error("Configure interrupt pin failed")
        return False

      if not self._setTiltConfig(config):
        logger.error("Set tilt config failed")
        return False

      if not self._enableTiltFeature():
        logger.error("Enable tilt feature failed")
        return False

      if not self._mapInterrupt(pin, 'tilt'):
        logger.error("Map interrupt failed")
        return False

      logger.info("Tilt interrupt enabled: pin=%d", pin)
      return True

    except Exception as e:
      logger.error("Enable tilt interrupt failed: %s", str(e))
      return False

  def write_reg(self, reg, value):
    """Write data to register (public helper)."""
    try:
      if isinstance(value, list):
        self.i2cbus.write_i2c_block_data(self.i2c_addr, reg, value)
      else:
        self.i2cbus.write_byte_data(self.i2c_addr, reg, value)
      self._delay_us(2)
    except Exception as e:
      logger.error("Write reg failed: reg=0x%02X, error=%s", reg, str(e))
      raise

  def read_reg(self, reg, length=1):
    """Read register (public helper)."""
    return self._read_regs(reg, length)

  def _write_regs(self, reg_addr, data):
    """Internal: write one or more bytes."""
    try:
      if len(data) == 1:
        self.i2cbus.write_byte_data(self.i2c_addr, reg_addr, data[0])
      else:
        self.i2cbus.write_i2c_block_data(self.i2c_addr, reg_addr, data)
      self._delay_us(2)
      return BMI323_OK
    except Exception as e:
      logger.error("Write regs failed: reg=0x%02X, error=%s", reg_addr, str(e))
      return BMI323_E_COM_FAIL

  def _read_regs(self, reg_addr, length):
    """Internal: read registers (handles I2C dummy bytes)."""
    try:
      total_length = length + self._dummy_byte
      data = self.i2cbus.read_i2c_block_data(self.i2c_addr, reg_addr, total_length)
      self._delay_us(2)
      if len(data) >= total_length:
        return data[self._dummy_byte : self._dummy_byte + length]
      elif len(data) >= length:
        logger.warning("Short read (expect %d, got %d), assuming no dummy bytes", total_length, len(data))
        return data[:length]
      else:
        logger.error("Read length too short: expect >=%d, got %d", length, len(data))
        return None
    except Exception as e:
      logger.error("Read regs failed: reg=0x%02X, error=%s", reg_addr, str(e))
      return None

  def _delay_us(self, period):
    """Delay in microseconds."""
    time.sleep(period / 1000000.0)

  def _delay_ms(self, period):
    """Delay in milliseconds."""
    time.sleep(period / 1000.0)

  def _odr_to_hz(self, odr):
    """Convert ODR enum value to frequency in Hz.
    @param odr ODR enum value (eAccelODR_t or eGyroODR_t)
    @return float Frequency in Hz, or None if invalid
    """
    # ODR values are the same for both accelerometer and gyroscope
    odr_map = {
      0x01: 0.78125,  # eAccelODR0_78125Hz / eGyroODR0_78125Hz
      0x02: 1.5625,  # eAccelODR1_5625Hz / eGyroODR1_5625Hz
      0x03: 3.125,  # eAccelODR3_125Hz / eGyroODR3_125Hz
      0x04: 6.25,  # eAccelODR6_25Hz / eGyroODR6_25Hz
      0x05: 12.5,  # eAccelODR12_5Hz / eGyroODR12_5Hz
      0x06: 25.0,  # eAccelODR25Hz / eGyroODR25Hz
      0x07: 50.0,  # eAccelODR50Hz / eGyroODR50Hz
      0x08: 100.0,  # eAccelODR100Hz / eGyroODR100Hz
      0x09: 200.0,  # eAccelODR200Hz / eGyroODR200Hz
      0x0A: 400.0,  # eAccelODR400Hz / eGyroODR400Hz
      0x0B: 800.0,  # eAccelODR800Hz / eGyroODR800Hz
      0x0C: 1600.0,  # eAccelODR1600Hz / eGyroODR1600Hz
      0x0D: 3200.0,  # eAccelODR3200Hz / eGyroODR3200Hz
      0x0E: 6400.0,  # eAccelODR6400Hz / eGyroODR6400Hz
    }
    return odr_map.get(odr)

  def _validate_odr_range(self, odr, mode, sensor_type='accel'):
    """Validate ODR range based on operating mode.
    @param odr ODR enum value
    @param mode Operating mode (eAccelMode_t or eGyroMode_t)
    @param sensor_type 'accel' or 'gyro'
    @return tuple (is_valid, error_message)
    """
    odr_hz = self._odr_to_hz(odr)
    if odr_hz is None:
      return (False, f"Invalid ODR value: 0x{odr:02X}")

    # Define ODR range limits based on mode
    if mode == eAccelMode_t.eAccelModeLowPower or mode == eGyroMode_t.eGyroModeLowPower:
      min_odr = 0.78
      max_odr = 400.0
      mode_name = "Low power"
    elif mode == eAccelMode_t.eAccelModeNormal or mode == eGyroMode_t.eGyroModeNormal:
      min_odr = 12.5
      max_odr = 6400.0
      mode_name = "Normal"
    elif mode == eAccelMode_t.eAccelModeHighPerf or mode == eGyroMode_t.eGyroModeHighPerf:
      min_odr = 12.5
      max_odr = 6400.0
      mode_name = "High performance"
    else:
      return (False, f"Invalid mode value: {mode}")

    if odr_hz < min_odr or odr_hz > max_odr:
      return (False, f"{sensor_type.capitalize()} ODR {odr_hz}Hz is out of range for {mode_name} mode (allowed: {min_odr}Hz ~ {max_odr}Hz)")

    return (True, None)

  def _get_accel_config(self):
    """Read current accelerometer configuration (ODR and mode).
    @return tuple (odr, mode) or (None, None) on failure
    """
    try:
      reg_data = self._read_regs(BMI3_REG_ACC_CONF, 2)
      if reg_data is None or len(reg_data) < 2:
        return (None, None)

      # Extract ODR (bits 0-3 of byte 0)
      odr = reg_data[0] & BMI3_ACC_ODR_MASK

      # Extract mode (bits 12-14 of byte 1, which is the high byte)
      mode_raw = (reg_data[1] << 8) | reg_data[0]
      mode_bits = (mode_raw & BMI3_ACC_MODE_MASK) >> BMI3_ACC_MODE_POS

      # Convert mode bits to enum value
      if mode_bits == BMI3_ACC_MODE_LOW_PWR:
        mode = eAccelMode_t.eAccelModeLowPower
      elif mode_bits == BMI3_ACC_MODE_NORMAL:
        mode = eAccelMode_t.eAccelModeNormal
      elif mode_bits == BMI3_ACC_MODE_HIGH_PERF:
        mode = eAccelMode_t.eAccelModeHighPerf
      else:
        mode = None

      return (odr, mode)
    except Exception as e:
      logger.error("Failed to read accel config: %s", str(e))
      return (None, None)

  def _validate_feature_odr_requirement(self, feature_name, min_odr_hz_low_power):
    """Validate ODR requirement for specific features.
    @param feature_name Name of the feature (e.g., 'sig_motion', 'step_counter', 'tap')
    @param min_odr_hz_low_power Minimum ODR in Hz required for low power mode
    @return tuple (is_valid, error_message)
    """
    odr, mode = self._get_accel_config()
    if odr is None or mode is None:
      return (False, f"Failed to read accelerometer configuration for {feature_name} feature")

    odr_hz = self._odr_to_hz(odr)
    if odr_hz is None:
      return (False, f"Invalid ODR value (0x{odr:02X}) for {feature_name} feature")

    # Check ODR requirement based on mode
    if mode == eAccelMode_t.eAccelModeLowPower:
      if odr_hz < min_odr_hz_low_power:
        return (False, f"{feature_name} feature requires ODR >= {min_odr_hz_low_power}Hz in low power mode, but current ODR is {odr_hz}Hz")
    # For normal and high performance modes, no additional ODR requirement beyond the basic range

    return (True, None)

  def _lsb_to_g(self, val, g_range):
    half_scale = 32768.0
    return (val * g_range) / half_scale

  def _lsb_to_dps(self, val, dps_range):
    half_scale = 32768.0
    return (val * dps_range) / half_scale

  def _int16_from_bytes(self, low_byte, high_byte):
    """Build int16 from two bytes (little endian)."""
    value = (high_byte << 8) | low_byte
    if value & 0x8000:
      value = value - 0x10000
    return value

  def _soft_reset(self):
    """Internal: perform soft reset and enable feature engine."""
    try:
      # Step 1: send soft-reset command (0xDEAF, low byte first)
      cmd_data = [0xAF, 0xDE]
      rslt = self._write_regs(BMI3_REG_CMD, cmd_data)
      if rslt != BMI323_OK:
        return rslt

      # Step 2: wait for reset
      self._delay_us(BMI3_SOFT_RESET_DELAY_US)

      # Step 3: configure feature engine registers
      feature_io2_data = [0x2C, 0x01]
      rslt = self._write_regs(BMI3_REG_FEATURE_IO2, feature_io2_data)
      if rslt != BMI323_OK:
        return rslt

      feature_io_status_data = [0x01, 0x00]
      rslt = self._write_regs(BMI3_REG_FEATURE_IO_STATUS, feature_io_status_data)
      if rslt != BMI323_OK:
        return rslt

      # Enable feature engine
      feature_ctrl_data = [0x01, 0x00]
      rslt = self._write_regs(BMI3_REG_FEATURE_CTRL, feature_ctrl_data)
      if rslt != BMI323_OK:
        return rslt

      # Step 4: poll until feature engine enabled (max 10 attempts)
      loop = 0
      max_loops = 10
      while loop < max_loops:
        self._delay_us(100000)  # 100 ms
        reg_data = self._read_regs(BMI3_REG_FEATURE_IO1, 2)
        if reg_data is None or len(reg_data) < 2:
          loop += 1
          continue

        if (reg_data[0] & BMI3_FEATURE_ENGINE_ENABLE_MASK) != 0:
          logger.info("Feature engine enabled (loop %d)", loop + 1)
          return BMI323_OK

        loop += 1

      logger.error("Feature engine enable timeout")
      return BMI323_E_FEATURE_ENGINE_STATUS

    except Exception as e:
      logger.error("Soft reset failed: %s", str(e))
      return BMI323_E_COM_FAIL

  def _enable_feature_engine(self):
    """Internal: feature engine already enabled in _soft_reset."""
    return BMI323_OK

  def is_initialized(self):
    """Return True if sensor is initialized."""
    return self._initialized

  def get_chip_id(self):
    """Return chip ID."""
    return self._chip_id

  def _configureIntPin(self, pin):
    """Internal: configure interrupt pin."""
    try:
      reg_data = self._read_regs(BMI3_REG_IO_INT_CTRL, 3)
      if reg_data is None or len(reg_data) < 3:
        logger.error("Read int pin config failed")
        return False

      if pin == eInt_t.eINT1:
        reg_data[0] = (reg_data[0] & ~BMI3_INT1_LVL_MASK) | (BMI3_ENABLE & BMI3_INT1_LVL_MASK)
        reg_data[0] = (reg_data[0] & ~BMI3_INT1_OD_MASK) | ((BMI3_DISABLE << BMI3_INT1_OD_POS) & BMI3_INT1_OD_MASK)
        reg_data[0] = (reg_data[0] & ~BMI3_INT1_OUTPUT_EN_MASK) | ((BMI3_ENABLE << BMI3_INT1_OUTPUT_EN_POS) & BMI3_INT1_OUTPUT_EN_MASK)
      elif pin == eInt_t.eINT2:
        reg_value = (reg_data[1] << 8) | reg_data[0]
        reg_value = (reg_value & ~BMI3_INT2_LVL_MASK) | ((BMI3_ENABLE << BMI3_INT2_LVL_POS) & BMI3_INT2_LVL_MASK)
        reg_value = (reg_value & ~BMI3_INT2_OD_MASK) | ((BMI3_DISABLE << BMI3_INT2_OD_POS) & BMI3_INT2_OD_MASK)
        reg_value = (reg_value & ~BMI3_INT2_OUTPUT_EN_MASK) | ((BMI3_ENABLE << BMI3_INT2_OUTPUT_EN_POS) & BMI3_INT2_OUTPUT_EN_MASK)
        reg_data[1] = (reg_value >> 8) & 0xFF
        reg_data[0] = reg_value & 0xFF
      else:
        logger.error("Invalid interrupt pin: %d", pin)
        return False

      rslt = self._write_regs(BMI3_REG_IO_INT_CTRL, reg_data[:2])
      if rslt != BMI323_OK:
        return False

      return True

    except Exception as e:
      logger.error("Configure interrupt pin failed: %s", str(e))
      return False

  def _setAnyMotionConfig(self, config):
    """Internal: set any-motion config via feature engine."""
    try:
      base_addr = [BMI3_BASE_ADDR_ANY_MOTION, 0x00]
      rslt = self._write_regs(BMI3_REG_FEATURE_DATA_ADDR, base_addr)
      if rslt != BMI323_OK:
        return False

      any_mot_config = [0] * 6

      any_mot_config[0] = config.slope_thres & 0xFF

      threshold_16bit = (any_mot_config[1] << 8) | any_mot_config[0]
      threshold_16bit = (threshold_16bit & ~BMI3_ANY_NO_SLOPE_THRESHOLD_MASK) | (config.slope_thres & BMI3_ANY_NO_SLOPE_THRESHOLD_MASK)
      any_mot_config[1] = (threshold_16bit & BMI3_ANY_NO_SLOPE_THRESHOLD_MASK) >> 8

      acc_ref_up_16bit = any_mot_config[1] << 8
      acc_ref_up_16bit = (acc_ref_up_16bit & ~BMI3_ANY_NO_ACC_REF_UP_MASK) | ((config.acc_ref_up << BMI3_ANY_NO_ACC_REF_UP_POS) & BMI3_ANY_NO_ACC_REF_UP_MASK)
      any_mot_config[1] |= (acc_ref_up_16bit & BMI3_ANY_NO_ACC_REF_UP_MASK) >> 8

      any_mot_config[2] = config.hysteresis & 0xFF

      hysteresis_16bit = (any_mot_config[3] << 8) | any_mot_config[2]
      hysteresis_16bit = (hysteresis_16bit & ~BMI3_ANY_NO_HYSTERESIS_MASK) | (config.hysteresis & BMI3_ANY_NO_HYSTERESIS_MASK)
      any_mot_config[3] = (hysteresis_16bit & BMI3_ANY_NO_HYSTERESIS_MASK) >> 8

      any_mot_config[4] = config.duration & 0xFF

      duration_16bit = (any_mot_config[5] << 8) | any_mot_config[4]
      duration_16bit = (duration_16bit & ~BMI3_ANY_NO_DURATION_MASK) | (config.duration & BMI3_ANY_NO_DURATION_MASK)
      any_mot_config[5] = (duration_16bit & BMI3_ANY_NO_DURATION_MASK) >> 8

      wait_time_16bit = any_mot_config[5] << 8
      wait_time_16bit = (wait_time_16bit & ~BMI3_ANY_NO_WAIT_TIME_MASK) | ((config.wait_time << BMI3_ANY_NO_WAIT_TIME_POS) & BMI3_ANY_NO_WAIT_TIME_MASK)
      any_mot_config[5] |= (wait_time_16bit & BMI3_ANY_NO_WAIT_TIME_MASK) >> 8

      rslt = self._write_regs(BMI3_REG_FEATURE_DATA_TX, any_mot_config)
      return rslt == BMI323_OK

    except Exception as e:
      logger.error("Set any-motion config failed: %s", str(e))
      return False

  def _enableAnyMotionFeature(self, axisMask):
    """Internal: enable any-motion feature."""
    try:
      reg_data = self._read_regs(BMI3_REG_FEATURE_IO0, 2)
      if reg_data is None or len(reg_data) < 2:
        logger.error("Read Feature IO0 failed")
        return False

      feature_value = (reg_data[1] << 8) | reg_data[0]
      feature_value &= ~(BMI3_ANY_MOTION_X_EN_MASK | BMI3_ANY_MOTION_Y_EN_MASK | BMI3_ANY_MOTION_Z_EN_MASK)
      if axisMask & eAxis_t.eAxisX:
        feature_value |= BMI3_ENABLE << BMI3_ANY_MOTION_X_EN_POS
      if axisMask & eAxis_t.eAxisY:
        feature_value |= BMI3_ENABLE << BMI3_ANY_MOTION_Y_EN_POS
      if axisMask & eAxis_t.eAxisZ:
        feature_value |= BMI3_ENABLE << BMI3_ANY_MOTION_Z_EN_POS

      feature_data = [feature_value & 0xFF, (feature_value >> 8) & 0xFF]
      rslt = self._write_regs(BMI3_REG_FEATURE_IO0, feature_data)
      if rslt != BMI323_OK:
        return False

      gp_status = [0x01, 0x00]
      rslt = self._write_regs(BMI3_REG_FEATURE_IO_STATUS, gp_status)
      return rslt == BMI323_OK

    except Exception as e:
      logger.error("Enable any-motion feature failed: %s", str(e))
      return False

  def _mapInterrupt(self, pin, interrupt_type):
    """Internal: map interrupt to pin."""
    try:
      reg_data = self._read_regs(BMI3_REG_INT_MAP1, 4)
      if reg_data is None or len(reg_data) < 4:
        logger.error("Read interrupt map failed")
        return False

      pin_value = BMI3_INT1 if (pin == eInt_t.eINT1) else BMI3_INT2

      if interrupt_type == 'any_motion':
        reg_data[0] = (reg_data[0] & ~BMI3_ANY_MOTION_OUT_MASK) | ((pin_value << BMI3_ANY_MOTION_OUT_POS) & BMI3_ANY_MOTION_OUT_MASK)
      elif interrupt_type == 'no_motion':
        reg_data[0] = (reg_data[0] & ~BMI3_NO_MOTION_OUT_MASK) | ((pin_value << BMI3_NO_MOTION_OUT_POS) & BMI3_NO_MOTION_OUT_MASK)
      elif interrupt_type == 'step_detector':
        temp_value = (reg_data[1] << 8) | reg_data[0]
        temp_value = (temp_value & ~BMI3_STEP_DETECTOR_OUT_MASK) | ((pin_value << BMI3_STEP_DETECTOR_OUT_POS) & BMI3_STEP_DETECTOR_OUT_MASK)
        reg_data[1] = (temp_value >> 8) & 0xFF
        reg_data[0] = temp_value & 0xFF
      elif interrupt_type == 'flat':
        reg_data[0] = (reg_data[0] & ~BMI3_FLAT_OUT_MASK) | ((pin_value << BMI3_FLAT_OUT_POS) & BMI3_FLAT_OUT_MASK)
      elif interrupt_type == 'orientation':
        reg_data[0] = (reg_data[0] & ~BMI3_ORIENTATION_OUT_MASK) | ((pin_value << BMI3_ORIENTATION_OUT_POS) & BMI3_ORIENTATION_OUT_MASK)
      elif interrupt_type == 'tilt':
        temp_value = (reg_data[1] << 8) | reg_data[0]
        temp_value = (temp_value & ~BMI3_TILT_OUT_MASK) | ((pin_value << BMI3_TILT_OUT_POS) & BMI3_TILT_OUT_MASK)
        reg_data[1] = (temp_value >> 8) & 0xFF
        reg_data[0] = temp_value & 0xFF
      elif interrupt_type == 'tap':
        reg_data[2] = (reg_data[2] & ~BMI3_TAP_OUT_MASK) | ((pin_value << BMI3_TAP_OUT_POS) & BMI3_TAP_OUT_MASK)
      elif interrupt_type == 'sig_motion':
        temp_value = (reg_data[1] << 8) | reg_data[0]
        temp_value = (temp_value & ~BMI3_SIG_MOTION_OUT_MASK) | ((pin_value << BMI3_SIG_MOTION_OUT_POS) & BMI3_SIG_MOTION_OUT_MASK)
        reg_data[1] = (temp_value >> 8) & 0xFF
        reg_data[0] = temp_value & 0xFF

      rslt = self._write_regs(BMI3_REG_INT_MAP1, reg_data)
      return rslt == BMI323_OK

    except Exception as e:
      logger.error("Map interrupt failed: %s", str(e))
      return False

  def _setNoMotionConfig(self, config):
    """Internal: set no-motion config via feature engine."""
    try:
      base_addr = [BMI3_BASE_ADDR_NO_MOTION, 0x00]
      rslt = self._write_regs(BMI3_REG_FEATURE_DATA_ADDR, base_addr)
      if rslt != BMI323_OK:
        return False

      no_mot_config = [0] * 6

      no_mot_config[0] = config.slope_thres & 0xFF

      threshold_16bit = (no_mot_config[1] << 8) | no_mot_config[0]
      threshold_16bit = (threshold_16bit & ~BMI3_ANY_NO_SLOPE_THRESHOLD_MASK) | (config.slope_thres & BMI3_ANY_NO_SLOPE_THRESHOLD_MASK)
      no_mot_config[1] = (threshold_16bit & BMI3_ANY_NO_SLOPE_THRESHOLD_MASK) >> 8

      acc_ref_up_16bit = no_mot_config[1] << 8
      acc_ref_up_16bit = (acc_ref_up_16bit & ~BMI3_ANY_NO_ACC_REF_UP_MASK) | ((config.acc_ref_up << BMI3_ANY_NO_ACC_REF_UP_POS) & BMI3_ANY_NO_ACC_REF_UP_MASK)
      no_mot_config[1] |= (acc_ref_up_16bit & BMI3_ANY_NO_ACC_REF_UP_MASK) >> 8

      no_mot_config[2] = config.hysteresis & 0xFF

      hysteresis_16bit = (no_mot_config[3] << 8) | no_mot_config[2]
      hysteresis_16bit = (hysteresis_16bit & ~BMI3_ANY_NO_HYSTERESIS_MASK) | (config.hysteresis & BMI3_ANY_NO_HYSTERESIS_MASK)
      no_mot_config[3] = (hysteresis_16bit & BMI3_ANY_NO_HYSTERESIS_MASK) >> 8

      no_mot_config[4] = config.duration & 0xFF

      duration_16bit = (no_mot_config[5] << 8) | no_mot_config[4]
      duration_16bit = (duration_16bit & ~BMI3_ANY_NO_DURATION_MASK) | (config.duration & BMI3_ANY_NO_DURATION_MASK)
      no_mot_config[5] = (duration_16bit & BMI3_ANY_NO_DURATION_MASK) >> 8

      wait_time_16bit = no_mot_config[5] << 8
      wait_time_16bit = (wait_time_16bit & ~BMI3_ANY_NO_WAIT_TIME_MASK) | ((config.wait_time << BMI3_ANY_NO_WAIT_TIME_POS) & BMI3_ANY_NO_WAIT_TIME_MASK)
      no_mot_config[5] |= (wait_time_16bit & BMI3_ANY_NO_WAIT_TIME_MASK) >> 8

      rslt = self._write_regs(BMI3_REG_FEATURE_DATA_TX, no_mot_config)
      return rslt == BMI323_OK

    except Exception as e:
      logger.error("Set no-motion config failed: %s", str(e))
      return False

  def _enableNoMotionFeature(self, axisMask):
    """Internal: enable no-motion feature."""
    try:
      reg_data = self._read_regs(BMI3_REG_FEATURE_IO0, 2)
      if reg_data is None or len(reg_data) < 2:
        logger.error("Read Feature IO0 failed")
        return False

      feature_value = (reg_data[1] << 8) | reg_data[0]
      feature_value &= ~(BMI3_NO_MOTION_X_EN_MASK | BMI3_NO_MOTION_Y_EN_MASK | BMI3_NO_MOTION_Z_EN_MASK)
      if axisMask & eAxis_t.eAxisX:
        feature_value |= BMI3_ENABLE << BMI3_NO_MOTION_X_EN_POS
      if axisMask & eAxis_t.eAxisY:
        feature_value |= BMI3_ENABLE << BMI3_NO_MOTION_Y_EN_POS
      if axisMask & eAxis_t.eAxisZ:
        feature_value |= BMI3_ENABLE << BMI3_NO_MOTION_Z_EN_POS

      feature_data = [feature_value & 0xFF, (feature_value >> 8) & 0xFF]
      rslt = self._write_regs(BMI3_REG_FEATURE_IO0, feature_data)
      if rslt != BMI323_OK:
        return False

      gp_status = [0x01, 0x00]
      rslt = self._write_regs(BMI3_REG_FEATURE_IO_STATUS, gp_status)
      return rslt == BMI323_OK

    except Exception as e:
      logger.error("Enable no-motion feature failed: %s", str(e))
      return False

  def _setSigMotionConfig(self, config):
    """Internal: set significant-motion config via feature engine."""
    try:
      base_addr = [BMI3_BASE_ADDR_SIG_MOTION, 0x00]
      rslt = self._write_regs(BMI3_REG_FEATURE_DATA_ADDR, base_addr)
      if rslt != BMI323_OK:
        return False

      sig_mot_config = [0] * 6

      sig_mot_config[0] = config.block_size & 0xFF
      sig_mot_config[1] = (config.block_size >> 8) & 0xFF

      sig_mot_config[2] = config.peak_2_peak_min & 0xFF

      p2p_min_16bit = (sig_mot_config[3] << 8) | sig_mot_config[2]
      p2p_min_16bit = (p2p_min_16bit & ~BMI3_SIG_P2P_MIN_MASK) | (config.peak_2_peak_min & BMI3_SIG_P2P_MIN_MASK)
      sig_mot_config[3] = (p2p_min_16bit & BMI3_SIG_P2P_MIN_MASK) >> 8

      mcr_min_16bit = sig_mot_config[3] << 8
      mcr_min_16bit = (mcr_min_16bit & ~BMI3_SIG_MCR_MIN_MASK) | ((config.mcr_min << BMI3_SIG_MCR_MIN_POS) & BMI3_SIG_MCR_MIN_MASK)
      sig_mot_config[3] |= (mcr_min_16bit & BMI3_SIG_MCR_MIN_MASK) >> 8

      sig_mot_config[4] = config.peak_2_peak_max & 0xFF

      p2p_max_16bit = (sig_mot_config[5] << 8) | sig_mot_config[4]
      p2p_max_16bit = (p2p_max_16bit & ~BMI3_SIG_P2P_MAX_MASK) | (config.peak_2_peak_max & BMI3_SIG_P2P_MAX_MASK)
      sig_mot_config[5] = (p2p_max_16bit & BMI3_SIG_P2P_MAX_MASK) >> 8

      mcr_max_16bit = sig_mot_config[5] << 8
      mcr_max_16bit = (mcr_max_16bit & ~BMI3_MCR_MAX_MASK) | ((config.mcr_max << BMI3_MCR_MAX_POS) & BMI3_MCR_MAX_MASK)
      sig_mot_config[5] |= (mcr_max_16bit & BMI3_MCR_MAX_MASK) >> 8

      rslt = self._write_regs(BMI3_REG_FEATURE_DATA_TX, sig_mot_config)
      return rslt == BMI323_OK

    except Exception as e:
      logger.error("Set sig-motion config failed: %s", str(e))
      return False

  def _enableSigMotionFeature(self):
    """Internal: enable sig-motion feature."""
    try:
      reg_data = self._read_regs(BMI3_REG_FEATURE_IO0, 2)
      if reg_data is None or len(reg_data) < 2:
        logger.error("Read Feature IO0 failed")
        return False

      feature_value = (reg_data[1] << 8) | reg_data[0]
      feature_value &= ~BMI3_SIG_MOTION_EN_MASK
      feature_value |= (BMI3_ENABLE << BMI3_SIG_MOTION_EN_POS) & BMI3_SIG_MOTION_EN_MASK

      feature_data = [feature_value & 0xFF, (feature_value >> 8) & 0xFF]
      rslt = self._write_regs(BMI3_REG_FEATURE_IO0, feature_data)
      if rslt != BMI323_OK:
        return False

      gp_status = [0x01, 0x00]
      rslt = self._write_regs(BMI3_REG_FEATURE_IO_STATUS, gp_status)
      return rslt == BMI323_OK

    except Exception as e:
      logger.error("Enable sig-motion feature failed: %s", str(e))
      return False

  def _setFlatConfig(self, config):
    """Internal: set flat config via feature engine."""
    try:
      base_addr = [BMI3_BASE_ADDR_FLAT, 0x00]
      rslt = self._write_regs(BMI3_REG_FEATURE_DATA_ADDR, base_addr)
      if rslt != BMI323_OK:
        return False

      flat_config = [0] * 4

      flat_config[0] = config.theta & BMI3_FLAT_THETA_MASK

      flat_config[0] |= (config.blocking << BMI3_FLAT_BLOCKING_POS) & BMI3_FLAT_BLOCKING_MASK

      holdtime_16bit = flat_config[1] << 8
      holdtime_16bit = (holdtime_16bit & ~BMI3_FLAT_HOLD_TIME_MASK) | ((config.hold_time << BMI3_FLAT_HOLD_TIME_POS) & BMI3_FLAT_HOLD_TIME_MASK)
      flat_config[1] = (holdtime_16bit & BMI3_FLAT_HOLD_TIME_MASK) >> 8

      flat_config[2] = config.slope_thres & BMI3_FLAT_SLOPE_THRES_MASK

      hyst_16bit = flat_config[3] << 8
      hyst_16bit = (hyst_16bit & ~BMI3_FLAT_HYST_MASK) | ((config.hysteresis << BMI3_FLAT_HYST_POS) & BMI3_FLAT_HYST_MASK)
      flat_config[3] = (hyst_16bit & BMI3_FLAT_HYST_MASK) >> 8

      rslt = self._write_regs(BMI3_REG_FEATURE_DATA_TX, flat_config)
      return rslt == BMI323_OK

    except Exception as e:
      logger.error("Set flat config failed: %s", str(e))
      return False

  def _enableFlatFeature(self):
    """Internal: enable flat feature."""
    try:
      reg_data = self._read_regs(BMI3_REG_FEATURE_IO0, 2)
      if reg_data is None or len(reg_data) < 2:
        logger.error("Read Feature IO0 failed")
        return False

      feature_value = (reg_data[1] << 8) | reg_data[0]
      feature_value &= ~BMI3_FLAT_EN_MASK
      feature_value |= (BMI3_ENABLE << BMI3_FLAT_EN_POS) & BMI3_FLAT_EN_MASK

      feature_data = [feature_value & 0xFF, (feature_value >> 8) & 0xFF]
      rslt = self._write_regs(BMI3_REG_FEATURE_IO0, feature_data)
      if rslt != BMI323_OK:
        return False

      gp_status = [0x01, 0x00]
      rslt = self._write_regs(BMI3_REG_FEATURE_IO_STATUS, gp_status)
      return rslt == BMI323_OK

    except Exception as e:
      logger.error("Enable flat feature failed: %s", str(e))
      return False

  def _setOrientationConfig(self, config):
    """Internal: set orientation config via feature engine."""
    try:
      base_addr = [BMI3_BASE_ADDR_ORIENT, 0x00]
      rslt = self._write_regs(BMI3_REG_FEATURE_DATA_ADDR, base_addr)
      if rslt != BMI323_OK:
        return False

      orient_config = [0] * 4

      orient_config[0] = config.ud_en & BMI3_ORIENT_UD_EN_MASK

      orient_config[0] |= (config.mode << BMI3_ORIENT_MODE_POS) & BMI3_ORIENT_MODE_MASK

      orient_config[0] |= (config.blocking << BMI3_ORIENT_BLOCKING_POS) & BMI3_ORIENT_BLOCKING_MASK

      orient_config[0] |= (config.theta << BMI3_ORIENT_THETA_POS) & 0xE0

      theta_16bit = orient_config[1] << 8
      theta_16bit = (theta_16bit & ~BMI3_ORIENT_THETA_MASK) | ((config.theta << BMI3_ORIENT_THETA_POS) & BMI3_ORIENT_THETA_MASK)
      orient_config[1] = (theta_16bit & BMI3_ORIENT_THETA_MASK) >> 8

      hold_time_16bit = orient_config[1] << 8
      hold_time_16bit = (hold_time_16bit & ~BMI3_ORIENT_HOLD_TIME_MASK) | ((config.hold_time << BMI3_ORIENT_HOLD_TIME_POS) & BMI3_ORIENT_HOLD_TIME_MASK)
      orient_config[1] |= (hold_time_16bit & BMI3_ORIENT_HOLD_TIME_MASK) >> 8

      orient_config[2] = config.slope_thres & BMI3_ORIENT_SLOPE_THRES_MASK

      hyst_16bit = orient_config[3] << 8
      hyst_16bit = (hyst_16bit & ~BMI3_ORIENT_HYST_MASK) | ((config.hysteresis << BMI3_ORIENT_HYST_POS) & BMI3_ORIENT_HYST_MASK)
      orient_config[3] = (hyst_16bit & BMI3_ORIENT_HYST_MASK) >> 8

      rslt = self._write_regs(BMI3_REG_FEATURE_DATA_TX, orient_config)
      return rslt == BMI323_OK

    except Exception as e:
      logger.error("Set orientation config failed: %s", str(e))
      return False

  def _enableOrientationFeature(self):
    """Internal: enable orientation feature."""
    try:
      reg_data = self._read_regs(BMI3_REG_FEATURE_IO0, 2)
      if reg_data is None or len(reg_data) < 2:
        logger.error("Read Feature IO0 failed")
        return False

      feature_value = (reg_data[1] << 8) | reg_data[0]
      feature_value &= ~BMI3_ORIENTATION_EN_MASK
      feature_value |= (BMI3_ENABLE << BMI3_ORIENTATION_EN_POS) & BMI3_ORIENTATION_EN_MASK

      feature_data = [feature_value & 0xFF, (feature_value >> 8) & 0xFF]
      rslt = self._write_regs(BMI3_REG_FEATURE_IO0, feature_data)
      if rslt != BMI323_OK:
        return False

      gp_status = [0x01, 0x00]
      rslt = self._write_regs(BMI3_REG_FEATURE_IO_STATUS, gp_status)
      return rslt == BMI323_OK

    except Exception as e:
      logger.error("Enable orientation feature failed: %s", str(e))
      return False

  def _setTapConfig(self, config):
    """Internal: set tap config via feature engine."""
    try:
      base_addr = [BMI3_BASE_ADDR_TAP, 0x00]
      rslt = self._write_regs(BMI3_REG_FEATURE_DATA_ADDR, base_addr)
      if rslt != BMI323_OK:
        return False

      tap_config = [0] * 6

      tap_config[0] = config.axis_sel & BMI3_TAP_AXIS_SEL_MASK

      tap_config[0] |= (config.wait_for_timeout << BMI3_TAP_WAIT_FR_TIME_OUT_POS) & BMI3_TAP_WAIT_FR_TIME_OUT_MASK

      tap_config[0] |= (config.max_peaks_for_tap << BMI3_TAP_MAX_PEAKS_POS) & BMI3_TAP_MAX_PEAKS_MASK

      tap_config[0] |= (config.mode << BMI3_TAP_MODE_POS) & BMI3_TAP_MODE_MASK

      tap_config[2] = config.tap_peak_thres & 0xFF

      peak_thres_16bit = (tap_config[3] << 8) | tap_config[2]
      peak_thres_16bit = (peak_thres_16bit & ~BMI3_TAP_PEAK_THRES_MASK) | (config.tap_peak_thres & BMI3_TAP_PEAK_THRES_MASK)
      tap_config[3] = (peak_thres_16bit & BMI3_TAP_PEAK_THRES_MASK) >> 8

      max_gest_dur_16bit = tap_config[3] << 8
      max_gest_dur_16bit = (max_gest_dur_16bit & ~BMI3_TAP_MAX_GEST_DUR_MASK) | ((config.max_gest_dur << BMI3_TAP_MAX_GEST_DUR_POS) & BMI3_TAP_MAX_GEST_DUR_MASK)
      tap_config[3] |= (max_gest_dur_16bit & BMI3_TAP_MAX_GEST_DUR_MASK) >> 8

      tap_config[4] = config.max_dur_between_peaks & BMI3_TAP_MAX_DUR_BW_PEAKS_MASK

      tap_config[4] |= (config.tap_shock_settling_dur << BMI3_TAP_SHOCK_SETT_DUR_POS) & BMI3_TAP_SHOCK_SETT_DUR_MASK

      min_quite_16bit = tap_config[5] << 8
      min_quite_16bit = (min_quite_16bit & ~BMI3_TAP_MIN_QUITE_DUR_BW_TAPS_MASK) | ((config.min_quite_dur_between_taps << BMI3_TAP_MIN_QUITE_DUR_BW_TAPS_POS) & BMI3_TAP_MIN_QUITE_DUR_BW_TAPS_MASK)
      tap_config[5] = (min_quite_16bit & BMI3_TAP_MIN_QUITE_DUR_BW_TAPS_MASK) >> 8

      quite_time_16bit = tap_config[5] << 8
      quite_time_16bit = (quite_time_16bit & ~BMI3_TAP_QUITE_TIME_AFTR_GEST_MASK) | ((config.quite_time_after_gest << BMI3_TAP_QUITE_TIME_AFTR_GEST_POS) & BMI3_TAP_QUITE_TIME_AFTR_GEST_MASK)
      tap_config[5] |= (quite_time_16bit & BMI3_TAP_QUITE_TIME_AFTR_GEST_MASK) >> 8

      rslt = self._write_regs(BMI3_REG_FEATURE_DATA_TX, tap_config)
      return rslt == BMI323_OK

    except Exception as e:
      logger.error("Set tap config failed: %s", str(e))
      return False

  def _enableTapFeature(self, enableSingle, enableDouble, enableTriple):
    """Internal: enable tap feature (single/double/triple)."""
    try:
      reg_data = self._read_regs(BMI3_REG_FEATURE_IO0, 2)
      if reg_data is None or len(reg_data) < 2:
        logger.error("Read Feature IO0 failed")
        return False

      feature_16bit = (reg_data[1] << 8) | reg_data[0]
      feature_16bit &= ~(BMI3_TAP_DETECTOR_S_TAP_EN_MASK | BMI3_TAP_DETECTOR_D_TAP_EN_MASK | BMI3_TAP_DETECTOR_T_TAP_EN_MASK)
      if enableSingle:
        feature_16bit |= (BMI3_ENABLE << BMI3_TAP_DETECTOR_S_TAP_EN_POS) & BMI3_TAP_DETECTOR_S_TAP_EN_MASK
      if enableDouble:
        feature_16bit |= (BMI3_ENABLE << BMI3_TAP_DETECTOR_D_TAP_EN_POS) & BMI3_TAP_DETECTOR_D_TAP_EN_MASK
      if enableTriple:
        feature_16bit |= (BMI3_ENABLE << BMI3_TAP_DETECTOR_T_TAP_EN_POS) & BMI3_TAP_DETECTOR_T_TAP_EN_MASK

      feature_data = [feature_16bit & 0xFF, (feature_16bit >> 8) & 0xFF]
      rslt = self._write_regs(BMI3_REG_FEATURE_IO0, feature_data)
      if rslt != BMI323_OK:
        return False

      gp_status = [0x01, 0x00]
      rslt = self._write_regs(BMI3_REG_FEATURE_IO_STATUS, gp_status)
      return rslt == BMI323_OK

    except Exception as e:
      logger.error("Enable tap feature failed: %s", str(e))
      return False

  def _setTiltConfig(self, config):
    """Internal: set tilt config via feature engine."""
    try:
      base_addr = [BMI3_BASE_ADDR_TILT, 0x00]
      rslt = self._write_regs(BMI3_REG_FEATURE_DATA_ADDR, base_addr)
      if rslt != BMI323_OK:
        return False

      tilt_config = [0] * 4

      value16 = (tilt_config[1] << 8) | tilt_config[0]
      value16 = (value16 & ~BMI3_TILT_SEGMENT_SIZE_MASK) | (config.segment_size & BMI3_TILT_SEGMENT_SIZE_MASK)
      value16 = (value16 & ~BMI3_TILT_MIN_TILT_ANGLE_MASK) | ((config.min_tilt_angle << BMI3_TILT_MIN_TILT_ANGLE_POS) & BMI3_TILT_MIN_TILT_ANGLE_MASK)
      tilt_config[0] = value16 & 0xFF
      tilt_config[1] = (value16 >> 8) & 0xFF

      beta_val = config.beta_acc_mean & BMI3_TILT_BETA_ACC_MEAN_MASK
      tilt_config[2] = beta_val & 0xFF
      tilt_config[3] = (beta_val >> 8) & 0xFF

      rslt = self._write_regs(BMI3_REG_FEATURE_DATA_TX, tilt_config)
      return rslt == BMI323_OK

    except Exception as e:
      logger.error("Set tilt config failed: %s", str(e))
      return False

  def _enableTiltFeature(self):
    """Internal: enable tilt feature."""
    try:
      reg_data = self._read_regs(BMI3_REG_FEATURE_IO0, 2)
      if reg_data is None or len(reg_data) < 2:
        logger.error("Read Feature IO0 failed")
        return False

      feature_value = (reg_data[1] << 8) | reg_data[0]
      feature_value &= ~BMI3_TILT_EN_MASK
      feature_value |= (BMI3_ENABLE << BMI3_TILT_EN_POS) & BMI3_TILT_EN_MASK
      feature_data = [feature_value & 0xFF, (feature_value >> 8) & 0xFF]
      rslt = self._write_regs(BMI3_REG_FEATURE_IO0, feature_data)
      if rslt != BMI323_OK:
        return False

      gp_status = [0x01, 0x00]
      rslt = self._write_regs(BMI3_REG_FEATURE_IO_STATUS, gp_status)
      return rslt == BMI323_OK

    except Exception as e:
      logger.error("Enable tilt feature failed: %s", str(e))
      return False

  def _enableStepCounterFeature(self):
    """Internal: enable step_counter and step_detector features."""
    try:
      reg_data = self._read_regs(BMI3_REG_FEATURE_IO0, 2)
      if reg_data is None or len(reg_data) < 2:
        logger.error("Read Feature IO0 failed")
        return False

      feature_16bit = (reg_data[1] << 8) | reg_data[0]
      feature_16bit &= ~(BMI3_STEP_DETECTOR_EN_MASK | BMI3_STEP_COUNTER_EN_MASK)
      feature_16bit |= (BMI3_ENABLE << BMI3_STEP_DETECTOR_EN_POS) & BMI3_STEP_DETECTOR_EN_MASK
      feature_16bit |= (BMI3_ENABLE << BMI3_STEP_COUNTER_EN_POS) & BMI3_STEP_COUNTER_EN_MASK

      feature_data = [feature_16bit & 0xFF, (feature_16bit >> 8) & 0xFF]
      rslt = self._write_regs(BMI3_REG_FEATURE_IO0, feature_data)
      if rslt != BMI323_OK:
        return False

      gp_status = [0x01, 0x00]
      rslt = self._write_regs(BMI3_REG_FEATURE_IO_STATUS, gp_status)
      return rslt == BMI323_OK

    except Exception as e:
      logger.error("Enable step_counter feature failed: %s", str(e))
      return False

  def _setAxisRemap(self):
    """Internal: Set axis remap configuration (YXZ axis mapping with inverted X, Y, Z axes).
    @details This function configures the axis remapping as: YXZ axis mapping with inverted X, Y, Z axes
    @n @note: XYZ axis denotes x = x, y = y, z = z
    @n Similarly, YXZ means x = y, y = x, z = z
    @return bool type, indicates the configuration status
    @retval True Configuration successful
    @retval False Configuration failed
    """
    try:
      if not self._initialized:
        return False

      # Set feature engine address to axis remap base address
      base_addr = [BMI3_BASE_ADDR_AXIS_REMAP, 0x00]
      rslt = self._write_regs(BMI3_REG_FEATURE_DATA_ADDR, base_addr)
      if rslt != BMI323_OK:
        logger.error("Failed to set feature data addr")
        return False

      # Initialize remap data array (following C code: uint8_t remap_data[4] = { 0 })
      remap_data = [0] * 4

      # @note: XYZ axis denotes x = x, y = y, z = z
      # Similarly, YXZ means x = y, y = x, z = z
      axis_map = BMI3_MAP_YXZ_AXIS

      # Invert the x, y, z axis of accelerometer and gyroscope
      invert_x = BMI3_MAP_NEGATIVE
      invert_y = BMI3_MAP_NEGATIVE
      invert_z = BMI3_MAP_NEGATIVE

      # Pack the configuration byte (following C code logic)
      # Set the value of re-mapped axis
      remap_data[0] = (remap_data[0] & ~BMI3_XYZ_AXIS_MASK) | (axis_map & BMI3_XYZ_AXIS_MASK)

      # Set the value of re-mapped x-axis sign
      remap_data[0] = (remap_data[0] & ~BMI3_X_AXIS_SIGN_MASK) | ((invert_x << BMI3_X_AXIS_SIGN_POS) & BMI3_X_AXIS_SIGN_MASK)

      # Set the value of re-mapped y-axis sign
      remap_data[0] = (remap_data[0] & ~BMI3_Y_AXIS_SIGN_MASK) | ((invert_y << BMI3_Y_AXIS_SIGN_POS) & BMI3_Y_AXIS_SIGN_MASK)

      # Set the value of re-mapped z-axis sign
      remap_data[0] = (remap_data[0] & ~BMI3_Z_AXIS_SIGN_MASK) | ((invert_z << BMI3_Z_AXIS_SIGN_POS) & BMI3_Z_AXIS_SIGN_MASK)

      # Write remap configuration back (2 bytes)
      remap_config = [remap_data[0], remap_data[1]]
      rslt = self._write_regs(BMI3_REG_FEATURE_DATA_TX, remap_config)
      if rslt != BMI323_OK:
        logger.error("Failed to write remap config")
        return False

      # Send axis map update command (following axes_remap_acc_power_mode_status logic)
      # Since accel may not be configured at this point, we use the simpler path
      cmd_data = [0x00, 0x03]  # BMI3_CMD_AXIS_MAP_UPDATE (low byte first)
      rslt = self._write_regs(BMI3_REG_CMD, cmd_data)
      if rslt != BMI323_OK:
        logger.error("Failed to send axis map update command")
        return False

      # Wait for axis mapping to complete (poll feature engine error status)
      # According to C code, feature engine error status is read from BMI3_REG_FEATURE_IO1
      time_out = 20
      axis_remap_delay_us = 5000  # 5ms
      for index in range(time_out):
        self._delay_us(axis_remap_delay_us)

        # Read feature engine error status (from FEATURE_IO1 register)
        err_data = self._read_regs(BMI3_REG_FEATURE_IO1, 2)
        if err_data is not None and len(err_data) >= 2:
          feature_engine_err_reg_lsb = err_data[0]
          feature_engine_err_reg_msb = err_data[1]

          # Check if no error and axis map is complete
          # BMI3_NO_ERROR_MASK = 0x05, BMI3_AXIS_MAP_COMPLETE_MASK = 0x0400 (bit 10, so msb bit 2)
          if (feature_engine_err_reg_lsb & BMI3_NO_ERROR_MASK) == BMI3_NO_ERROR_MASK:
            if (feature_engine_err_reg_msb & (BMI3_AXIS_MAP_COMPLETE_MASK >> 8)) != 0:
              logger.info("Axis remap completed")
              return True

      logger.warning("Axis remap timeout, but command was sent")
      return True  # Continue anyway as the command was sent

    except Exception as e:
      logger.error("Set axis remap failed: %s", str(e))
      return False
