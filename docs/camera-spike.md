# XIAO ESP32S3 Sense camera/video spike

## Question

Can the Mac command the XIAO ESP32S3 Sense camera over USB, receive real JPEG frames, and turn them into a playable video?

## Observed result

- Device port: `/dev/cu.usbmodem1101`
- Camera initialized with OPI PSRAM available.
- Single capture: valid 640×480 JPEG, 26,726 bytes.
- Video capture: 20 valid 640×480 JPEG frames collected over USB.
- Host output: H.264 MP4, 3.666 seconds, measured 5.455 fps, 191,325 bytes.
- A decoded middle frame was visually coherent and uncorrupted.

## Verdict: VALIDATED

The camera-to-Mac automation path works. This spike creates video by collecting JPEG frames and encoding them on the Mac; it is not an onboard hardware video encoder.

## Current limitation

The board was subsequently restored to the standalone microphone spike, so it currently accepts `RECORD`, not `CAPTURE`. Reflash `xiao_camera_spike.ino` before another camera run.

The audio/video mux artifact is explicitly **non-synchronized**: the camera and microphone were captured in separate runs and joined afterward on the Mac. In the simultaneous Arduino 2.0.17 attempt, starting its legacy `I2S` PDM path was consistently followed by failure of the first `esp_camera_fb_get()` call. This strongly points to an I2S/DMA resource interaction, but the exact cause was not fully attributed. A direct ESP-IDF channel-based implementation is the next controlled experiment, but was stopped for tonight by user choice.

## Residue

This directory and generated `/tmp/xiao-*` media are throwaway experiment artifacts. Keep until Roy reviews the delivered media; delete only after explicit confirmation.
