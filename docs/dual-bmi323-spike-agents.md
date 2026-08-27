# XIAO Dual BMI323 Spike

- Purpose: temporary but active dual-IMU bring-up and Mac plot experiment for the XIAO ESP32-S3 Sense.
- Flash: use `esp32:esp32:XIAO_ESP32S3:PSRAM=opi` and `/dev/cu.usbmodem1101`.
- Hardware: BMI323 I2C is `GPIO5` SDA / `GPIO6` SCL; both modules share 3V3/GND/SDA/SCL with addresses `0x68` and `0x69`.
- Tooling: a project-local `.venv` owns `pyserial`, `numpy`, and `matplotlib`; run `live_plot.py` only when no other process owns the serial port. The viewer is a 2×2 grid with 12 independent axis lines.
- Library: the local `~/Documents/Arduino/libraries/DFRobot_BMI323` patch is required for two instances. It routes callbacks by each instance address and does not call pinless `Wire.begin()`.
- Current state: independent six-axis readings and the raw serial stream are validated; the 2×2 independent-axis viewer is implemented and syntax-checked. Next experiment moves one IMU while the other remains fixed, measuring the address-specific gyro delta before adding difference logic.
