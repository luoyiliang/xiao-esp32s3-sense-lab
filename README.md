# XIAO ESP32-S3 Sense Lab

Reusable handoff package for the XIAO ESP32-S3 Sense camera, onboard microphone, and two DFRobot SEN0693 BMI323 IMUs.

## What Is Verified

| Layer | State | Evidence |
|---|---|---|
| USB serial | verified-current | XIAO appears at `/dev/cu.usbmodem1101` |
| Camera | verified | 640×480 JPEG over serial and host-encoded video |
| Microphone | verified | 16 kHz mono PCM recording over serial |
| Dual BMI323 I2C | verified | independent addresses `0x68` and `0x69`, chip response `0x1143` |
| Dual IMU raw data | verified | independent six-axis streams at approximately 5 Hz |
| Host plotting | verified | 2×2 / 12-axis matplotlib viewer launched successfully |
| Motion-difference algorithm | pending | intentionally not implemented yet |
| Android Wi-Fi/BLE viewer | planned | intentionally not implemented on this Mac |

## Hardware Contract

```text
XIAO 3V3          -> BMI323 #1 3V3, BMI323 #2 3V3
XIAO GND          -> BMI323 #1 GND, BMI323 #2 GND
XIAO D4 / GPIO5   -> BMI323 #1 SDA, BMI323 #2 SDA
XIAO D5 / GPIO6   -> BMI323 #1 SCL, BMI323 #2 SCL
```

- Configure one SEN0693 address pad as `0x68` and the other as `0x69`.
- `0x7E` is an I3C broadcast/reserved response, not a third sensor.
- The BMI323 modules operate at 3.3 V. Do not use a 5 V I2C host.
- `INT1` / `INT2` remain disconnected for the current polling experiment.

## Project Layout

```text
firmware/
  xiao_camera/            camera JPEG serial protocol
  xiao_microphone/        microphone PCM serial protocol
  xiao_dual_bmi323/       active dual-IMU firmware
  bmi323_raw_probe/       chip identity diagnostic
host/
  camera/                 JPEG and frame-video capture scripts
  microphone/             WAV recorder
  dual-bmi323/            2x2 / 12-axis live plot viewer
vendor/
  DFRobot_BMI323-upstream/ ordinary source snapshot with upstream commit record
  DFRobot_BMI323-patched/  local dual-device fix snapshot
docs/                      evidence and historical spike notes
build/                     compiled artifacts for all four sketches
```

## Build

Prerequisites used for the verified build:

```text
arduino-cli
esp32:esp32 2.0.17
FQBN: esp32:esp32:XIAO_ESP32S3:PSRAM=opi
```

Compile a sketch from the project root:

```bash
arduino-cli compile \
  --libraries ~/Documents/Arduino/libraries/DFRobot_BMI323 \
  --build-path build/xiao_dual_bmi323 \
  --fqbn 'esp32:esp32:XIAO_ESP32S3:PSRAM=opi' \
  firmware/xiao_dual_bmi323
```

Flash the active dual-IMU firmware:

```bash
arduino-cli upload \
  -p /dev/cu.usbmodem1101 \
  --fqbn 'esp32:esp32:XIAO_ESP32S3:PSRAM=opi' \
  firmware/xiao_dual_bmi323
```

## Host Tools

The host Python environment is intentionally external to this project:

```text
.venv
pyserial 3.5
numpy 2.5.2
matplotlib 3.11.1
```

It is not copied into source control. Recreate it on another machine with:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install pyserial numpy matplotlib
```

Run the dual-IMU viewer after the serial port is otherwise idle:

```bash
.venv/bin/python \
  host/dual-bmi323/live_plot.py \
  --port /dev/cu.usbmodem1101
```

The viewer uses a rolling 30-second 2×2 layout:

```text
0x68 Ax/Ay/Az | 0x69 Ax/Ay/Az
0x68 Gx/Gy/Gz | 0x69 Gx/Gy/Gz
```

X is red, Y is green, and Z is blue. It intentionally performs no filtering, axis remapping, difference calculation, or event detection.

## Local Library Patch

The project vendors both the untouched upstream DFRobot library and the patched snapshot. The active local Arduino library lives at:

```text
~/Documents/Arduino/libraries/DFRobot_BMI323
```

The patch is required for two devices on one `Wire` bus because upstream uses a single global callback instance and calls pinless `Wire.begin()` internally. Read [LOCAL_PATCH.md](vendor/DFRobot_BMI323-patched/LOCAL_PATCH.md) before moving this work into another repository.

For a different computer, install the vendored patched library into that machine's Arduino library location before compiling the dual-IMU sketch, or fold the patch into the target project's dependency workflow.

## Next Decision

**Decision:** whether the two IMU streams can support reliable relative-motion detection.

**Next smallest experiment:** physically hold one IMU fixed, rotate or shake only the other, and record the axis-specific change. Do not implement a difference formula until the raw axis mapping and mounting orientation are observed.

**Success:** the moved module shows a materially larger gyro peak than the fixed module.

**Stop condition:** if both modules show comparable peaks, inspect mechanical coupling or shared cable movement before changing software.

## Android Viewer Direction

The target experience is an Android display showing these raw curves and later relative orientation. This project deliberately stops at the wired USB truth layer. Choose Wi-Fi or BLE only after the raw relative-motion experiment is validated on the company computer; the mobile transport should not become a substitute for sensor validation.

## Notes

- `build/` is generated locally as handoff evidence for the current toolchain and is excluded from Git; source under `firmware/` remains authoritative.
- `bmi323_raw_probe` compiles with an Arduino `Wire.requestFrom` overload warning; its binary was produced successfully. Treat it as a diagnostic only.
- The repository is intended as a reusable public handoff package; replace local paths when moving the workflow to another computer.
