# DFRobot_BMI323 local patch

This directory is a local Arduino library installation based on the upstream DFRobot_BMI323 library.

## Why it differs from upstream

The upstream implementation uses one process-global `DFRobot_BMI323*` callback target. Constructing a second sensor object overwrites that target, which is unsafe for two BMI323 devices sharing one `TwoWire` bus. It also calls `Wire.begin()` without pins during initialization, which can overwrite the sketch's explicit ESP32 GPIO selection.

## Local changes

- I2C callbacks route by the per-instance `intf_ptr` address.
- The sketch owns `Wire.begin(SDA, SCL)` and bus clock setup.
- The low-level callback keeps the shared `TwoWire*` bus but no longer depends on a global sensor object.

## Verification

With two SEN0693 modules on GPIO5/GPIO6 at `0x68` and `0x69`, both addresses initialized and returned independent data. A raw probe returned `0x1143` from both devices; the BMI323 chip ID byte is `0x43`.

## Caution

This is a local working patch, not an upstream contribution or a general compatibility guarantee. Preserve the vendored upstream snapshot at `vendor/DFRobot_BMI323-upstream` for diff/reference. Re-test after changing Arduino-ESP32 core versions.
