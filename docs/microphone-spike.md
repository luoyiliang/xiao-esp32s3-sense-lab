# XIAO ESP32S3 Sense microphone spike

## Question

Does the installed Sense expansion board contain a working onboard microphone that can deliver real audio to the Mac?

## Observed result

- PDM microphone initialized on clock GPIO42 and data GPIO41.
- Captured 5.000 seconds of mono PCM at 16 kHz / 16-bit.
- WAV output: 160,044 bytes; 79,999 of 80,000 samples were non-zero.
- RMS amplitude: 7,668; peak reached full scale.
- Spectrogram shows time-varying broadband acoustic energy rather than silence or a constant corrupt value.

## Verdict: VALIDATED

The board has a working digital microphone and the USB recording path works.

## Current limitation

The test firmware applies 4× gain and clipped some samples. The next single-variable experiment should reduce gain to 2× or 1× and compare intelligibility and clipping.

The experimental MP4 with an audio track was muxed from separately recorded video and audio. It proves both media streams are playable, but it is not synchronized capture. The standalone microphone firmware is the final firmware restored to the board for tonight.

## Residue

This directory and generated `/tmp/xiao-*` media are throwaway experiment artifacts. Keep until Roy reviews the delivered media; delete only after explicit confirmation.
