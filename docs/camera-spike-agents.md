# XIAO Camera Spike

- Purpose: throwaway feasibility probe for controlling the XIAO ESP32S3 Sense camera from a Mac over USB.
- Run: compile/upload `xiao_camera_spike.ino` with `esp32:esp32:XIAO_ESP32S3:PSRAM=opi`, then run `capture.py` or `capture_video.py` from the pyserial venv.
- Stack: Arduino-ESP32 2.0.17, ESP32-S3 camera driver, Python/pyserial, FFmpeg.
- Layout: firmware and host scripts stay together; generated frames and media remain under `/tmp` and are disposable.
- Verified state: single JPEG and a 20-frame host-encoded video worked. At closeout the board has the standalone microphone firmware flashed, so reflash this firmware before another camera capture. The non-synchronized A/V mux is valid. True simultaneous capture remains unvalidated: the Arduino 2.0.17 legacy `I2S` path was followed by first-frame camera failure; exact resource attribution is pending, and the next controlled experiment should use direct ESP-IDF channel APIs.
