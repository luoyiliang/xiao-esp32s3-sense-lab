#!/usr/bin/env python3
import argparse
import pathlib
import re
import subprocess
import time

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


def read_frame(port, deadline):
    while True:
        line = read_line(port, deadline)
        match = re.fullmatch(rb"JPEG (\d+)", line)
        if match:
            length = int(match.group(1))
            payload = bytearray()
            while len(payload) < length and time.monotonic() < deadline:
                payload.extend(port.read(length - len(payload)))
            if len(payload) != length:
                raise RuntimeError(f"Expected {length} JPEG bytes, received {len(payload)}")
            if read_line(port, deadline) != b"":
                raise RuntimeError("Missing newline after JPEG payload")
            if read_line(port, deadline) != b"ENDJPEG":
                raise RuntimeError("Missing ENDJPEG marker")
            if not payload.startswith(b"\xff\xd8") or not payload.endswith(b"\xff\xd9"):
                raise RuntimeError("Incomplete JPEG payload")
            return bytes(payload)
        if line.startswith(b"ERR"):
            raise RuntimeError(line.decode(errors="replace"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="/dev/cu.usbmodem1101")
    parser.add_argument("--frames", type=int, default=20)
    parser.add_argument("--fps", type=float, default=5.0)
    parser.add_argument("--dir", default="/tmp/xiao-video-frames")
    parser.add_argument("--output", default="/tmp/xiao-video.mp4")
    args = parser.parse_args()

    frame_dir = pathlib.Path(args.dir)
    frame_dir.mkdir(parents=True, exist_ok=True)
    for old in frame_dir.glob("frame-*.jpg"):
        old.unlink()

    timestamps = []
    with serial.Serial(args.port, 115200, timeout=0.1) as port:
        port.dtr = False
        port.rts = False
        time.sleep(1.5)
        port.reset_input_buffer()
        start = time.monotonic()
        for index in range(args.frames):
            target = start + index / args.fps
            delay = target - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            port.write(b"CAPTURE\n")
            port.flush()
            payload = read_frame(port, time.monotonic() + 10)
            captured = time.monotonic()
            timestamps.append(captured)
            path = frame_dir / f"frame-{index:03d}.jpg"
            path.write_bytes(payload)
            print(f"FRAME {index + 1}/{args.frames} {len(payload)} bytes t={captured - start:.3f}s")

    elapsed = timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 0.0
    achieved_fps = (len(timestamps) - 1) / elapsed if elapsed > 0 else args.fps
    output = pathlib.Path(args.output)
    command = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-framerate", f"{achieved_fps:.6f}",
        "-i", str(frame_dir / "frame-%03d.jpg"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(output),
    ]
    subprocess.run(command, check=True)
    print(f"VIDEO {output} frames={args.frames} achieved_fps={achieved_fps:.3f} duration={args.frames / achieved_fps:.3f}s")


if __name__ == "__main__":
    main()
