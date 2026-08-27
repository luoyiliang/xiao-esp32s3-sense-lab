# XIAO ESP32-S3 Sense dual BMI323 spike

## Purpose

Validate two DFRobot SEN0693 BMI323 IMUs on one XIAO ESP32-S3 Sense I2C bus and visualize their independently measured motion on the Mac.

## Hardware contract

| XIAO | BMI323 #1 | BMI323 #2 |
|---|---|---|
| 3V3 | 3V3 | 3V3 |
| GND | GND | GND |
| D4 / GPIO5 | SDA | SDA |
| D5 / GPIO6 | SCL | SCL |

- Module addresses: `0x68` and `0x69`.
- `0x7E` is an I3C broadcast/reserved address response, not a third IMU.
- Do not connect or merge `INT1`/`INT2` until an interrupt experiment explicitly needs them.

## Live state verified on 2026-08-27

- Board port: `/dev/cu.usbmodem1101`.
- Both I2C addresses acknowledged reliably: `0x68`, `0x69`.
- Raw register probe returned `0x1143` from both chips; the BMI323 chip ID is low byte `0x43`, while the high byte carries revision information.
- Both devices independently initialized and produced six-axis readings at 5 Hz.
- Their static gravity vectors differed, proving the output is not a duplicated stream:
  - `0x68`: approximately `0.135, -0.007, -0.980 g`
  - `0x69`: approximately `0.879, -0.475, -0.054 g`

## Current firmware

`xiao_imu_spike.ino` is flashed to the XIAO. It outputs two machine-readable serial rows every 200 ms:

```text
DATA 0x68 A ax ay az G gx gy gz T temp
DATA 0x69 A ax ay az G gx gy gz T temp
```

It configures both IMUs for 50 Hz, +/-8 g acceleration and +/-500 dps gyroscope range, then emits data at about 5 Hz.

Compile and flash:

```bash
arduino-cli compile --fqbn 'esp32:esp32:XIAO_ESP32S3:PSRAM=opi' firmware/xiao_dual_bmi323
arduino-cli upload -p /dev/cu.usbmodemXXXX --fqbn 'esp32:esp32:XIAO_ESP32S3:PSRAM=opi' firmware/xiao_dual_bmi323
```

## Live plot

`live_plot.py` shows a rolling 30-second 2×2 view:

```text
┌─────────────────────┬─────────────────────┐
│ 0x68 accelerometer  │ 0x69 accelerometer  │
│ Ax / Ay / Az        │ Ax / Ay / Az        │
├─────────────────────┼─────────────────────┤
│ 0x68 gyroscope      │ 0x69 gyroscope      │
│ Gx / Gy / Gz        │ Gx / Gy / Gz        │
└─────────────────────┴─────────────────────┘
```

Axis colors are fixed: X=red, Y=green, Z=blue. The plot is intentionally raw
per-axis data; no difference, filtering, or event logic is applied yet.

Run:

```bash
.venv/bin/python host/dual-bmi323/live_plot.py --port /dev/cu.usbmodemXXXX
```

Close the window to release the serial port before any other reader, monitor, or upload.

## Current visualization state

- `changed-and-verified`: the viewer parses the existing `DATA` protocol and
  has passed Python syntax validation.
- `pending`: live 12-line rendering should be visually checked during the next
  window run; the previous magnitude viewer was already run successfully.
- Next experiment: hold one IMU still and rotate only the other, then add a
  separate difference view after the raw axes are visually trusted.

## Local library patch

The installed DFRobot library had two issues for this setup:

1. a single global instance pointer routed both sensor objects through the last constructed instance;
2. `Wire.begin()` inside the library could overwrite the sketch's custom GPIO5/GPIO6 I2C selection.

The local patch at `~/Documents/Arduino/libraries/DFRobot_BMI323` routes callbacks through each instance's `intf_ptr` address and leaves bus setup to the sketch. This patch is required for reliable dual-device reads.

## Verdict: VALIDATED

The shared I2C wiring, dual-address configuration, identity probe, independent six-axis streams, and Mac-hosted real-time plotting path are validated.

## Next smallest experiment

Keep one IMU physically still. Move only the other through a clear 90-degree rotation or short shake, then capture the per-address delta. Success: the moved address has a materially larger gyro peak than the stationary address. Stop if the supposedly stationary sensor has a comparable peak; first inspect mounting/cable coupling before changing code.

## Residue

- Keep: this directory, a project-local `.venv`, and the installed patched library for upcoming IMU work.
- Review-only candidates are external local clones and generated artifacts; do not delete them without a separate confirmation.
