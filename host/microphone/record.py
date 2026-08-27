#!/usr/bin/env python3
import argparse
import pathlib
import re
import struct
import sys
import time
import wave

import serial


def read_line(port, deadline):
    data = bytearray()
    while time.monotonic() < deadline:
        byte = port.read(1)
        if not byte:
            continue
        if byte == b"\n":
            return bytes(data).rstrip(b"\r")
        data.extend(byte)
    raise TimeoutError(f"Timed out waiting for line; partial={data!r}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="/dev/cu.usbmodem1101")
    parser.add_argument("--output", default="/tmp/xiao-mic.wav")
    args = parser.parse_args()

    with serial.Serial(args.port, 115200, timeout=0.1) as port:
        port.dtr = False
        port.rts = False
        time.sleep(1.5)
        port.reset_input_buffer()
        port.write(b"RECORD\n")
        port.flush()
        deadline = time.monotonic() + 20

        while True:
            line = read_line(port, deadline)
            print(line.decode("ascii", errors="replace"))
            match = re.fullmatch(rb"PCM (\d+) (\d+) (\d+)", line)
            if match:
                length, rate, bits = map(int, match.groups())
                if bits != 16:
                    raise RuntimeError(f"Unsupported PCM width: {bits}")
                pcm = bytearray()
                while len(pcm) < length and time.monotonic() < deadline:
                    pcm.extend(port.read(length - len(pcm)))
                if len(pcm) != length:
                    raise RuntimeError(f"Expected {length} PCM bytes, received {len(pcm)}")
                if read_line(port, deadline) != b"":
                    raise RuntimeError("Missing newline after PCM")
                if read_line(port, deadline) != b"ENDPCM":
                    raise RuntimeError("Missing ENDPCM marker")

                path = pathlib.Path(args.output)
                with wave.open(str(path), "wb") as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(bits // 8)
                    wav.setframerate(rate)
                    wav.writeframes(pcm)

                sample_count = length // 2
                samples = struct.unpack(f"<{sample_count}h", pcm)
                peak = max(abs(x) for x in samples)
                rms = (sum(x * x for x in samples) / sample_count) ** 0.5
                nonzero = sum(x != 0 for x in samples)
                print(f"SAVED {path} bytes={path.stat().st_size} seconds={sample_count / rate:.3f} peak={peak} rms={rms:.1f} nonzero={nonzero}/{sample_count}")
                return
            if line.startswith(b"ERR"):
                raise RuntimeError(line.decode(errors="replace"))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
