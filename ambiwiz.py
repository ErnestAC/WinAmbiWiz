#!/usr/bin/env python3
"""
AmbiWiz - Windows

Windows desktop capture -> average screen color -> enhanced color
-> identical RGB value sent to every configured WiZ light.

Uses DXcam / Windows Desktop Duplication.

Both WiZ lights are treated as ONE illumination zone.
"""

import colorsys
import json
import socket
import sys
import time

import dxcam


# ============================================================
# CONFIGURATION
# ============================================================

# ------------------------------------------------------------
# WIZ LIGHTS
# ------------------------------------------------------------

WIZ_LIGHTS = [
    "10.0.0.153",
    "10.0.0.50",
]

WIZ_PORT = 38899


# ------------------------------------------------------------
# CAPTURE
# ------------------------------------------------------------

# DXGI monitor/output index.
# 0 = primary monitor
CAPTURE_MONITOR = 0

CAPTURE_FPS = 30

# Number of pixels sampled horizontally/vertically.
SAMPLE_COLUMNS = 32
SAMPLE_ROWS = 18


# ------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------

UPDATE_INTERVAL = 0.05

# Higher = follows screen changes faster.
SMOOTHING = 0.25

# Only send to WiZ if RGB changed by this amount.
COLOR_THRESHOLD = 2


# ------------------------------------------------------------
# COLOR PROCESSING
# ------------------------------------------------------------

DARK_THRESHOLD = 10

SATURATION_BOOST = 1.60
BRIGHTNESS_BOOST = 1.35
MIN_BRIGHTNESS = 0.08
CONTRAST = 1.20

BLACK_SCREEN_THRESHOLD = 8


# ------------------------------------------------------------
# DEBUG
# ------------------------------------------------------------

# Print calculated colors.
SHOW_COLOR = True

# How often to print color information.
DEBUG_INTERVAL = 1.0


# ============================================================
# GLOBAL STATE
# ============================================================

ambient_color = [0.0, 0.0, 0.0]

last_sent_color = [-100, -100, -100]

last_debug_time = 0.0

last_frame_time = 0.0


# ============================================================
# UTILITY
# ============================================================

def clamp(value, minimum=0.0, maximum=255.0):
    return max(minimum, min(maximum, value))


def clamp_rgb(values):
    return tuple(
        int(round(clamp(value)))
        for value in values
    )


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

    # Saturation
    s *= SATURATION_BOOST
    s = max(0.0, min(1.0, s))

    # Brightness
    v *= BRIGHTNESS_BOOST

    if v > 0.0:
        v = max(v, MIN_BRIGHTNESS)

    v = max(0.0, min(1.0, v))

    r, g, b = colorsys.hsv_to_rgb(h, s, v)

    # Contrast
    r = ((r - 0.5) * CONTRAST) + 0.5
    g = ((g - 0.5) * CONTRAST) + 0.5
    b = ((b - 0.5) * CONTRAST) + 0.5

    r = max(0.0, min(1.0, r))
    g = max(0.0, min(1.0, g))
    b = max(0.0, min(1.0, b))

    return (
        r * 255.0,
        g * 255.0,
        b * 255.0,
    )


# ============================================================
# SCREEN COLOR
# ============================================================

def calculate_screen_color(frame):

    if frame is None:
        return None

    try:
        height, width = frame.shape[:2]
    except Exception:
        return None

    if width <= 0 or height <= 0:
        return None

    step_x = max(1, width // SAMPLE_COLUMNS)
    step_y = max(1, height // SAMPLE_ROWS)

    total_r = 0.0
    total_g = 0.0
    total_b = 0.0

    count = 0

    for y in range(0, height, step_y):

        for x in range(0, width, step_x):

            pixel = frame[y, x]

            # DXcam BGRA
            b = int(pixel[0])
            g = int(pixel[1])
            r = int(pixel[2])

            # Ignore almost-black pixels.
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
# WIZ
# ============================================================

def send_wiz_color(rgb):

    r = int(rgb[0])
    g = int(rgb[1])
    b = int(rgb[2])

    # ONE command.
    # Both lights receive the exact same values.
    command = {
        "method": "setPilot",
        "params": {
            "state": True,
            "r": r,
            "g": g,
            "b": b,
        },
    }

    data = json.dumps(command).encode("utf-8")

    for ip in WIZ_LIGHTS:

        try:

            with socket.socket(
                socket.AF_INET,
                socket.SOCK_DGRAM
            ) as sock:

                sock.settimeout(1.0)

                sock.sendto(
                    data,
                    (ip, WIZ_PORT)
                )

        except OSError as error:

            print(
                f"WiZ error ({ip}): {error}",
                flush=True
            )


# ============================================================
# SMOOTHING
# ============================================================

def smooth_color(current, target):

    for channel in range(3):

        current[channel] += (
            target[channel] - current[channel]
        ) * SMOOTHING


# ============================================================
# CREATE CAMERA
# ============================================================

def create_camera():

    print(
        "Creating Windows desktop capture...",
        flush=True
    )

    camera = dxcam.create(
        output_idx=CAPTURE_MONITOR,
        output_color="BGRA",
        processor_backend="numpy",
        max_buffer_len=8,
    )

    print(
        "Capture: Windows Desktop Duplication",
        flush=True
    )

    print(
        f"DXGI monitor/output index: "
        f"{CAPTURE_MONITOR}",
        flush=True
    )

    return camera


# ============================================================
# START CAMERA
# ============================================================

def start_camera():

    camera = create_camera()

    camera.start(
        target_fps=CAPTURE_FPS,
        video_mode=True,
    )

    # Give DXcam a moment to obtain the first frame.
    time.sleep(0.25)

    return camera


# ============================================================
# STOP CAMERA
# ============================================================

def stop_camera(camera):

    if camera is None:
        return

    try:
        camera.stop()
    except Exception:
        pass

    try:
        camera.release()
    except Exception:
        pass


# ============================================================
# GET FRAME
# ============================================================

def get_frame(camera):

    try:

        frame = camera.get_latest_frame()

        if frame is not None:
            return frame

    except Exception as error:

        print(
            f"Capture read error: {error}",
            flush=True
        )

    return None


# ============================================================
# UPDATE LIGHTS
# ============================================================

def update_lights(frame):

    global last_sent_color
    global last_debug_time

    target_color = calculate_screen_color(frame)

    if target_color is None:
        return

    screen_brightness = (
        sum(target_color) / 3.0
    )

    # Completely black screen.
    if screen_brightness <= BLACK_SCREEN_THRESHOLD:

        target_color = (
            0.0,
            0.0,
            0.0,
        )

    else:

        target_color = enhance_color(
            target_color
        )

    # Smooth toward target.
    smooth_color(
        ambient_color,
        target_color
    )

    rgb = clamp_rgb(
        ambient_color
    )

    # Debug output.
    now = time.monotonic()

    if (
        SHOW_COLOR
        and now - last_debug_time >= DEBUG_INTERVAL
    ):

        print(
            f"SCREEN={tuple(round(x) for x in target_color)} "
            f"OUTPUT={rgb}",
            flush=True
        )

        last_debug_time = now

    # Only send if color changed enough.
    if color_changed(
        last_sent_color,
        rgb
    ):

        send_wiz_color(rgb)

        last_sent_color = list(rgb)


# ============================================================
# MAIN
# ============================================================

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

    print(
        "Both lights will always receive "
        "the exact same RGB value."
    )

    print()

    print("Color enhancement:")
    print(
        f"  Saturation boost  : "
        f"{SATURATION_BOOST:.2f}x"
    )
    print(
        f"  Brightness boost  : "
        f"{BRIGHTNESS_BOOST:.2f}x"
    )
    print(
        f"  Minimum brightness: "
        f"{MIN_BRIGHTNESS:.2f}"
    )
    print(
        f"  Contrast          : "
        f"{CONTRAST:.2f}x"
    )

    print()

    camera = None

    try:

        while True:

            # ------------------------------------------------
            # Create/recreate camera
            # ------------------------------------------------

            if camera is None:

                try:

                    camera = start_camera()

                    print()
                    print(
                        "AmbiWiz capture is active."
                    )
                    print()

                except Exception as error:

                    print()
                    print(
                        "ERROR starting Windows "
                        "screen capture:"
                    )
                    print(error)
                    print(
                        "Retrying in 2 seconds..."
                    )

                    time.sleep(2)

                    continue

            # ------------------------------------------------
            # Get latest frame
            # ------------------------------------------------

            frame = get_frame(camera)

            if frame is None:

                # The DXGI device may have been lost,
                # the monitor may have changed, or Windows
                # may temporarily have interrupted capture.

                print(
                    "No frame available. "
                    "Reinitializing capture...",
                    flush=True
                )

                stop_camera(camera)

                camera = None

                time.sleep(1)

                continue

            # ------------------------------------------------
            # Process
            # ------------------------------------------------

            try:

                update_lights(frame)

            except Exception as error:

                print(
                    f"Color processing error: {error}",
                    flush=True
                )

            time.sleep(
                UPDATE_INTERVAL
            )

    except KeyboardInterrupt:

        print()
        print("Stopping AmbiWiz...")

    finally:

        stop_camera(camera)

        print(
            "AmbiWiz stopped."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()