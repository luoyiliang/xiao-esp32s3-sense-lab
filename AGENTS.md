# XIAO ESP32-S3 Sense Lab

- Purpose: portable hardware bring-up package for XIAO camera, microphone, and dual BMI323 IMUs.
- Board: `esp32:esp32:XIAO_ESP32S3:PSRAM=opi`; current Mac port is `/dev/cu.usbmodem1101`.
- I2C: XIAO `GPIO5` is SDA, `GPIO6` is SCL; BMI323 addresses must be `0x68` and `0x69`.
- Vendor: keep upstream and patched DFRobot_BMI323 snapshots separate. The patched version is required for dual instances because it routes callbacks by the instance address and preserves explicit Wire pin configuration.
- Active firmware: `firmware/xiao_dual_bmi323/xiao_dual_bmi323.ino`; it emits two `DATA` serial rows approximately every 200 ms.
- Host: `host/dual-bmi323/live_plot.py` requires pyserial, numpy, matplotlib and plots 12 raw axis signals in a 2×2 grid. Close it before upload or another serial reader.
- Scope: raw data and visualization are validated. Difference logic, axis calibration, Wi-Fi/BLE transport, Android UI, and GitHub publishing are separate future decisions.
- Build evidence: `build/` contains artifacts compiled with Arduino ESP32 core 2.0.17; source under `firmware/` remains authoritative.
- Safety: BMI323 is 3.3 V only. Do not attach servo/motor power to the XIAO or sensor 3.3 V rail.
