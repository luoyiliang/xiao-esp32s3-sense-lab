# XIAO Microphone Spike

- Purpose: throwaway feasibility probe for recording the XIAO ESP32S3 Sense onboard PDM microphone to a Mac over USB.
- Run: compile/upload `xiao_mic_spike.ino` with `esp32:esp32:XIAO_ESP32S3:PSRAM=opi`, then run `record.py` from the pyserial venv.
- Stack: Arduino-ESP32 2.0.17, Arduino I2S/PDM, Python/pyserial, WAV, FFmpeg.
- Layout: firmware and host script stay together; generated audio/media remain under `/tmp` and are disposable.
- Verified state: 5 seconds of 16 kHz mono 16-bit PCM recorded with real varying signal. The current 4x gain clips; next experiment should compare 1x and 2x gain before judging audio quality. This standalone microphone firmware is the final image restored to the board for tonight.
