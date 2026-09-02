#!/usr/bin/env python3
"""
AmbiWiz - Windows

Captures the Windows desktop, calculates one average ambient color,
enhances/smooths it, and sends the exact same RGB value to every
configured WiZ light.

This version uses dxcam for Windows desktop capture.
"""

import colorsys
import json
import socket
import sys
import threading
import time

try:
    import dxcam
except ImportError:
    print("ERROR: dxcam is not installed.")
    print("Run: python -m pip install -r requirements.txt")
    sys.exit(1)

# ============================================================
# CONFIGURATION
# ============================================================

# ------------------------------------------------------------
# WIZ LIGHTS
# ------------------------------------------------------------

# These lights form ONE illumination zone.
# Both lights always receive the exact same RGB value.
WIZ_LIGHTS = [
    "10.0.0.153",
    "10.0.0.50",
]

WIZ_PORT = 38899

# ------------------------------------------------------------
# UPDATE / RESPONSE
# ------------------------------------------------------------

UPDATE_INTERVAL = 0.05       # 20 color calculations/sec
SMOOTHING = 0.25

# ------------------------------------------------------------
# COLOR PROCESSING
# ------------------------------------------------------------

COLOR_THRESHOLD = 2
DARK_THRESHOLD = 10

SATURATION_BOOST = 1.60
BRIGHTNESS_BOOST = 1.35
MIN_BRIGHTNESS = 0.08
CONTRAST = 1.20

BLACK_SCREEN_THRESHOLD = 8

# ------------------------------------------------------------
# SCREEN CAPTURE
# ------------------------------------------------------------

# DXGI output index. 0 is normally the primary monitor.
# Use 1, 2, etc. for another monitor if needed.
CAPTURE_MONITOR = 0

SAMPLE_COLUMNS = 32
SAMPLE_ROWS = 18

# ============================================================
# GLOBAL STATE
# ============================================================

ambient_color = [0.0, 0.0, 0.0]
last_sent_color = [-100, -100, -100]

capture_lock = threading.Lock()
latest_frame = None


# ============================================================
# UTILITY
# ============================================================

def clamp(value, minimum=0.0, maximum=255.0):
    return max(minimum, min(maximum, value))


def clamp_rgb(values):
    return tuple(int(round(clamp(value))) for value in values)


def color_changed(old, new):
    return any(
        abs(old[index] - new[index]) >= COLOR_THRESHOLD
        for index in range(3)
    )


# ============================================================
# COLOR ENHANCEMENT
# ============================================================

def enhance_color(rgb):
    r, g, b = rgb

    r /= 255.0
    g /= 255.0
    b /= 255.0

    h, s, v = colorsys.rgb_to_hsv(r, g, b)

    s *= SATURATION_BOOST
    s = max(0.0, min(1.0, s))

    v *= BRIGHTNESS_BOOST

    if v > 0.0:
        v = max(v, MIN_BRIGHTNESS)

    v = max(0.0, min(1.0, v))

    r, g, b = colorsys.hsv_to_rgb(h, s, v)

    r = ((r - 0.5) * CONTRAST) + 0.5
    g = ((g - 0.5) * CONTRAST) + 0.5
    b = ((b - 0.5) * CONTRAST) + 0.5

    r = max(0.0, min(1.0, r))
    g = max(0.0, min(1.0, g))
    b = max(0.0, min(1.0, b))

    return r * 255.0, g * 255.0, b * 255.0


# ============================================================
# WINDOWS CAPTURE
# ============================================================

def capture_frame(camera):
    global latest_frame

    frame = camera.grab()

    if frame is not None:
        with capture_lock:
            latest_frame = frame.copy()


def calculate_screen_color():
    with capture_lock:
        if latest_frame is None:
            return None
        frame = latest_frame.copy()

    height, width = frame.shape[:2]

    if width <= 0 or height <= 0:
        return None

    # dxcam returns BGRA/BGR depending on configuration.
    # The camera below is configured for BGR.
    step_x = max(1, width // SAMPLE_COLUMNS)
    step_y = max(1, height // SAMPLE_ROWS)

    total_r = 0.0
    total_g = 0.0
    total_b = 0.0
    count = 0

    for y in range(0, height, step_y):
        for x in range(0, width, step_x):
            b, g, r = frame[y, x][:3]

            r = int(r)
            g = int(g)
            b = int(b)

            if r + g + b < DARK_THRESHOLD:
                continue

            total_r += r
            total_g += g
            total_b += b
            count += 1

    if count == 0:
        return 0.0, 0.0, 0.0

    return (
        total_r / count,
        total_g / count,
        total_b / count,
    )


# ============================================================
# WIZ CONTROL
# ============================================================

def send_wiz_color(rgb):
    """
    Send the EXACT SAME RGB value to every configured light.
    """

    command = {
        "method": "setPilot",
        "params": {
            "state": True,
            "r": int(rgb[0]),
            "g": int(rgb[1]),
            "b": int(rgb[2]),
        },
    }

    data = json.dumps(command).encode("utf-8")

    sockets = []

    try:
        for ip in WIZ_LIGHTS:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sockets.append((ip, sock))

        for ip, sock in sockets:
            try:
                sock.sendto(data, (ip, WIZ_PORT))
            except OSError as error:
                print(f"WiZ error ({ip}): {error}", flush=True)

    finally:
        for _, sock in sockets:
            try:
                sock.close()
            except Exception:
                pass


# ============================================================
# LIGHT UPDATE
# ============================================================

def smooth_color(current, target):
    for channel in range(3):
        current[channel] += (
            target[channel] - current[channel]
        ) * SMOOTHING


def update_lights():
    global last_sent_color

    try:
        target_color = calculate_screen_color()

        if target_color is None:
            return

        screen_brightness = sum(target_color) / 3.0

        if screen_brightness <= BLACK_SCREEN_THRESHOLD:
            target_color = 0.0, 0.0, 0.0
        else:
            target_color = enhance_color(target_color)

        smooth_color(ambient_color, target_color)

        rgb = clamp_rgb(ambient_color)

        if color_changed(last_sent_color, rgb):
            send_wiz_color(rgb)
            last_sent_color = list(rgb)

    except Exception as error:
        print(f"Color processing error: {error}", flush=True)


# ============================================================
# MAIN
# ============================================================

def create_camera():
    print("Initializing Windows desktop capture...", flush=True)

    monitor = int(CAPTURE_MONITOR)
    camera = dxcam.create(output_idx=monitor, output_color="BGR")

    print("Capture: Windows Desktop Duplication", flush=True)
    print(f"DXGI monitor/output index: {monitor}", flush=True)

    return camera


def main():
    print()
    print("==========================================")
    print(" AmbiWiz - Windows")
    print("==========================================")
    print()

    print("Illumination zone:")
    for ip in WIZ_LIGHTS:
        print(f"  -> {ip}")

    print()
    print("Both lights will always receive the same RGB value.")
    print()

    print("Color enhancement:")
    print(f"  Saturation boost  : {SATURATION_BOOST:.2f}x")
    print(f"  Brightness boost  : {BRIGHTNESS_BOOST:.2f}x")
    print(f"  Minimum brightness: {MIN_BRIGHTNESS:.2f}")
    print(f"  Contrast          : {CONTRAST:.2f}x")
    print()

    try:
        camera = create_camera()
    except Exception as error:
        print()
        print("ERROR starting Windows screen capture:")
        print(error)
        print()
        print("Make sure you are running this on Windows with")
        print("a supported DXGI desktop capture environment.")
        sys.exit(1)

    try:
        camera.start(
            target_fps=30,
            video_mode=False,
        )
    except Exception as error:
        print()
        print("ERROR starting capture:")
        print(error)
        sys.exit(1)

    print()
    print("AmbiWiz is running.")
    print("Mode: Single illumination zone")
    print(f"Lights: {len(WIZ_LIGHTS)}")
    print()
    print("Press Ctrl+C to stop.")
    print()

    try:
        while True:
            update_lights()
            time.sleep(UPDATE_INTERVAL)

    except KeyboardInterrupt:
        print()
        print("Stopping AmbiWiz...")

    finally:
        try:
            camera.stop()
        except Exception:
            pass

        print("AmbiWiz stopped.")


if __name__ == "__main__":
    main()
