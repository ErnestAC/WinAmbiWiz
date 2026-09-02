# AmbiWiz for Windows

AmbiWiz is a small Python application that makes WiZ smart lights react to the colors displayed on a Windows desktop.

The lights are treated as a single illumination zone. Every configured WiZ light receives the exact same RGB value.

## Features

- Windows desktop capture using DXGI Desktop Duplication through `dxcam`
- One shared ambient color
- Multiple WiZ lights can be controlled together
- Same RGB value sent to every light
- Saturation enhancement
- Brightness enhancement
- Contrast enhancement
- Smooth color transitions
- Dark-pixel filtering
- Black-screen detection
- Configurable sampling density
- UDP communication directly with WiZ lights
- No WSL, PipeWire, D-Bus, GNOME or GStreamer required

## Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer
- WiZ lights reachable on the local network
- WiZ lights with their IP addresses configured in `ambiwiz.py`

## Installation

Open Command Prompt in the AmbiWiz directory and run:

    install.bat

Or install the dependencies manually:

    python -m pip install -r requirements.txt

## Configuration

Open:

    ambiwiz.py

The WiZ lights are configured near the top of the file:

    WIZ_LIGHTS = [
        "10.0.0.153",
        "10.0.0.50",
    ]

Replace those addresses with the IP addresses of the lights you want AmbiWiz to control.

The lights are intentionally treated as one zone. They do not have separate left/right colors.

### Color response

These values control how noticeable and responsive the lighting is:

    UPDATE_INTERVAL = 0.05
    SMOOTHING = 0.25

    SATURATION_BOOST = 1.60
    BRIGHTNESS_BOOST = 1.35
    MIN_BRIGHTNESS = 0.08
    CONTRAST = 1.20

    COLOR_THRESHOLD = 2
    DARK_THRESHOLD = 10
    BLACK_SCREEN_THRESHOLD = 8

### Monitor selection

The initial Windows version captures one DXGI monitor output at a time.

The default is:

    CAPTURE_MONITOR = 0

Use `1`, `2`, etc. to select another display exposed by DXGI.

A later version can combine multiple monitor outputs into one shared color if desired.

### Screen sampling

The screen is sampled rather than processing every pixel:

    SAMPLE_COLUMNS = 32
    SAMPLE_ROWS = 18

Increasing these values analyzes more pixels but uses more CPU.

## Running

Run:

    python ambiwiz.py

You should see something similar to:

    ==========================================
     AmbiWiz - Windows
    ==========================================

    Illumination zone:
      -> 10.0.0.153
      -> 10.0.0.50

    Both lights will always receive the same RGB value.

    Capture: Windows Desktop Duplication

    AmbiWiz is running.
    Mode: Single illumination zone
    Lights: 2

Stop with:

    Ctrl+C

## Network

AmbiWiz sends WiZ UDP commands directly to each configured light.

The default WiZ control port is:

    38899

The computer and WiZ lights must be able to communicate with each other over the local network.

If the lights do not react, check:

1. The IP addresses in `WIZ_LIGHTS`.
2. That the lights are powered on.
3. That the Windows PC can reach the lights.
4. That UDP traffic to port 38899 is not being blocked.

## Screen capture

The Windows version uses DXGI Desktop Duplication through `dxcam`.

This avoids the GNOME ScreenCast / PipeWire / D-Bus system used by the Linux version.

The capture runs continuously in memory and AmbiWiz only keeps the most recent frame for color analysis.

## Important monitor note

The initial Windows version captures one DXGI monitor output at a time.

The default is:

    CAPTURE_MONITOR = 0

If you have multiple monitors, set this to the desired DXGI output index.

If you want the Windows version to combine all monitors into one shared color, that can be added without changing the WiZ/color-processing portion of the program.

## Troubleshooting

### `dxcam` cannot be installed

Make sure you are using a supported 64-bit Windows Python installation.

Then try:

    python -m pip install --upgrade pip
    python -m pip install dxcam numpy

### Python is not recognized

Install Python and enable the option to add Python to PATH.

Then open a new Command Prompt.

### Lights do not respond

Verify the IP addresses and test network connectivity.

For example:

    ping 10.0.0.153
    ping 10.0.0.50

Ping availability does not guarantee that UDP port 38899 is permitted, but it is a useful first network check.

### Colors are too weak

Increase:

    SATURATION_BOOST
    BRIGHTNESS_BOOST

You can also increase:

    CONTRAST

### Colors change too slowly

Increase:

    SMOOTHING

For example:

    SMOOTHING = 0.35

Higher values make the lights follow the screen more aggressively.

### Colors change too quickly

Decrease:

    SMOOTHING

For example:

    SMOOTHING = 0.15

## Project structure

    AmbiWiz/
    ├── ambiwiz.py
    ├── requirements.txt
    ├── install.bat
    └── README.md

## License

Use and modify the project as needed for your own AmbiWiz setup.
