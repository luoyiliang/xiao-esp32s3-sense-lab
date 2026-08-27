#!/usr/bin/env python3
"""Live 2x2 plots for two BMI323 sensors over USB serial."""

import argparse
import queue
import re
import threading
import time
from collections import deque

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import serial

DATA_RE = re.compile(
    r"^DATA 0x(?P<addr>[0-9A-Fa-f]{2})"
    r" A (?P<ax>-?\d+(?:\.\d+)?) (?P<ay>-?\d+(?:\.\d+)?) (?P<az>-?\d+(?:\.\d+)?)"
    r" G (?P<gx>-?\d+(?:\.\d+)?) (?P<gy>-?\d+(?:\.\d+)?) (?P<gz>-?\d+(?:\.\d+)?)"
    r" T (?P<temp>-?\d+(?:\.\d+)?)$"
)

AXES = ("x", "y", "z")
COLORS = {"x": "tab:red", "y": "tab:green", "z": "tab:blue"}
ADDRESSES = (0x68, 0x69)


def serial_reader(port_name, output, stop_event):
    try:
        with serial.Serial(port_name, 115200, timeout=0.2) as port:
            port.dtr = False
            port.rts = False
            time.sleep(1.0)
            port.reset_input_buffer()
            while not stop_event.is_set():
                raw = port.readline()
                if not raw:
                    continue
                line = raw.decode("ascii", errors="replace").strip()
                match = DATA_RE.match(line)
                if not match:
                    continue
                values = {key: float(value) for key, value in match.groupdict().items()}
                values["addr"] = int(match.group("addr"), 16)
                values["time"] = time.monotonic()
                output.put(values)
    except Exception as exc:
        output.put({"error": str(exc)})


def make_history():
    fields = ("time", "ax", "ay", "az", "gx", "gy", "gz", "temp")
    return {address: {field: deque(maxlen=2000) for field in fields} for address in ADDRESSES}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", default="/dev/cu.usbmodem1101")
    parser.add_argument("--seconds", type=float, default=30.0, help="Visible history window")
    args = parser.parse_args()

    data_queue = queue.Queue()
    stop_event = threading.Event()
    reader = threading.Thread(
        target=serial_reader,
        args=(args.port, data_queue, stop_event),
        daemon=True,
    )
    reader.start()

    history = make_history()
    latest = {address: None for address in ADDRESSES}
    started = time.monotonic()
    error_message = None

    fig, axes = plt.subplots(2, 2, figsize=(13, 8), sharex=True)
    fig.canvas.manager.set_window_title("Dual BMI323 Live Plot — 12 Signals")
    fig.subplots_adjust(left=0.07, right=0.98, top=0.91, bottom=0.11, hspace=0.28, wspace=0.18)
    fig.suptitle("Dual BMI323 | USB Serial | Independent Axis Signals")

    line_sets = {}
    for column, address in enumerate(ADDRESSES):
        accel_axis = axes[0, column]
        gyro_axis = axes[1, column]
        accel_axis.set_title(f"0x{address:02X} — Accelerometer")
        gyro_axis.set_title(f"0x{address:02X} — Gyroscope")
        accel_axis.set_ylabel("g")
        gyro_axis.set_ylabel("dps")
        gyro_axis.set_xlabel("Seconds")
        for axis in (accel_axis, gyro_axis):
            axis.grid(True, alpha=0.25)
        line_sets[address] = {"accel": {}, "gyro": {}}
        for name in AXES:
            line_sets[address]["accel"][name] = accel_axis.plot(
                [], [], color=COLORS[name], linewidth=1.4, label=f"A{name}"
            )[0]
            line_sets[address]["gyro"][name] = gyro_axis.plot(
                [], [], color=COLORS[name], linewidth=1.4, label=f"G{name}"
            )[0]
        accel_axis.legend(loc="upper left", ncol=3, fontsize=8)
        gyro_axis.legend(loc="upper left", ncol=3, fontsize=8)

    status = fig.text(0.07, 0.025, "Waiting for BMI323 data...", fontsize=9)

    def update(_frame):
        nonlocal error_message
        while True:
            try:
                sample = data_queue.get_nowait()
            except queue.Empty:
                break
            if "error" in sample:
                error_message = sample["error"]
                continue
            address = sample["addr"]
            if address not in history:
                continue
            for field in history[address]:
                history[address][field].append(sample[field])
            latest[address] = sample

        all_times = [value for address in ADDRESSES for value in history[address]["time"]]
        if all_times:
            right = max(all_times)
            left = right - args.seconds
            for address in ADDRESSES:
                times = list(history[address]["time"])
                first = next((index for index, value in enumerate(times) if value >= left), len(times))
                if first >= len(times):
                    continue
                x = [value - started for value in times[first:]]
                for name in AXES:
                    accel_field = history[address][f"a{name}"]
                    gyro_field = history[address][f"g{name}"]
                    line_sets[address]["accel"][name].set_data(x, list(accel_field)[first:])
                    line_sets[address]["gyro"][name].set_data(x, list(gyro_field)[first:])

            x_right = max(args.seconds, right - started)
            x_left = max(0.0, x_right - args.seconds)
            for axis in axes.flat:
                axis.set_xlim(x_left, x_right)
                axis.relim()
                axis.autoscale_view(scalex=False, scaley=True)

            parts = []
            for address in ADDRESSES:
                sample = latest[address]
                if sample:
                    parts.append(
                        f"0x{address:02X} A={sample['ax']:.2f},{sample['ay']:.2f},{sample['az']:.2f}g"
                    )
            status.set_text(" | ".join(parts))
        if error_message:
            status.set_text(f"Serial error: {error_message}")
        return tuple(line for groups in line_sets.values() for kind in groups.values() for line in kind.values()) + (status,)

    animation = FuncAnimation(fig, update, interval=100, blit=False, cache_frame_data=False)

    def close(_event):
        stop_event.set()

    fig.canvas.mpl_connect("close_event", close)
    try:
        plt.show()
    finally:
        stop_event.set()
        reader.join(timeout=1.0)
        del animation


if __name__ == "__main__":
    main()