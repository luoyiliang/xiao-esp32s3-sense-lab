#!/usr/bin/env python3
import argparse
import pathlib
import re
import sys
import time

import serial


def read_line(port, timeout_at):
    data = bytearray()
    while time.monotonic() < timeout_at:
        b = port.read(1)
        if not b:
            continue
        if b == b"\n":
            return bytes(data).rstrip(b"\r")
        data.extend(b)
    raise TimeoutError(f"Timed out waiting for a line; partial={data!r}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="/dev/cu.usbmodem1101")
    parser.add_argument("--output", default="/tmp/xiao-capture.jpg")
    args = parser.parse_args()

    output = pathlib.Path(args.output)
    with serial.Serial(args.port, 115200, timeout=0.25) as port:
        time.sleep(1.5)
        port.reset_input_buffer()
        port.write(b"CAPTURE\n")
        port.flush()

        deadline = time.monotonic() + 15
        while True:
            line = read_line(port, deadline)
            text = line.decode("ascii", errors="replace")
            print(text)
            match = re.fullmatch(r"JPEG (\d+)", text)
            if match:
                length = int(match.group(1))
                payload = port.read(length)
                while len(payload) < length and time.monotonic() < deadline:
                    payload += port.read(length - len(payload))
                if len(payload) != length:
                    raise RuntimeError(f"Expected {length} JPEG bytes, received {len(payload)}")
                marker = read_line(port, deadline)
                if marker != b"":
                    # The JPEG write is followed by a newline, so the first line is empty.
                    raise RuntimeError(f"Unexpected post-JPEG separator: {marker!r}")
                end = read_line(port, deadline)
                if end != b"ENDJPEG":
                    raise RuntimeError(f"Missing ENDJPEG marker: {end!r}")
                if not payload.startswith(b"\xff\xd8") or not payload.endswith(b"\xff\xd9"):
                    raise RuntimeError("Captured payload is not a complete JPEG")
                output.write_bytes(payload)
                print(f"SAVED {output} {length} bytes")
                return 0
            if text.startswith("ERR"):
                raise RuntimeError(text)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
