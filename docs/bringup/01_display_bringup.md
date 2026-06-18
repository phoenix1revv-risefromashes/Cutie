# Display Bring-Up — 7-Inch Cutie Face Screen

## Purpose

This document records the first hardware bring-up test for Cutie’s 7-inch face display.

The goal was to verify that the NVIDIA Jetson Orin Nano can detect the HDMI touchscreen display through the DisplayPort-to-HDMI adapter and run it at the correct native resolution.

This matters because the display will later become Cutie’s expressive face interface.

---

## Hardware Used

| Component | Role |
|---|---|
| NVIDIA Jetson Orin Nano | Main robot compute unit |
| 7-inch HDMI 1024×600 capacitive touchscreen | Cutie face display |
| DisplayPort-to-HDMI adapter | Converts Jetson DisplayPort output to HDMI input |
| HDMI cable | Carries video signal to the display |
| USB cable | Provides touch interface and/or display power depending on wiring |

---

## Display Connection Path

```text
Jetson DisplayPort
→ DisplayPort-to-HDMI adapter
→ HDMI cable
→ 7-inch HDMI display
```

---

## Debugging Goal

Before building the ROS2 face-display node, the display must be verified at the Linux hardware level.

The main debugging question was:

```text
Does Linux detect Cutie’s physical display correctly?
```

---

## Display Session Debugging and Discovery Procedure

The first display test used:

```bash
export DISPLAY=:0
xrandr --listmonitors
```

This failed because the active graphical display session was not exposed as `X0`.

To check which X11 display sockets were available, the following command was used:

```bash
ls /tmp/.X11-unix/
```

Observed result:

```text
X1
```

This confirmed that the active graphical display session was:

```bash
DISPLAY=:1
```

For future SSH-based display debugging, graphical commands should target:

```bash
export DISPLAY=:1
```

---

## Display Verification Command

After selecting the correct display session, the monitor configuration was checked with:

```bash
export DISPLAY=:1
xrandr
```

Observed output:

```text
Screen 0: minimum 8 x 8, current 1024 x 600, maximum 32767 x 32767
DP-0 disconnected (normal left inverted right x axis y axis)
DP-1 connected primary 1024x600+0+0 (normal left inverted right x axis y axis) 154mm x 86mm
   1024x600      59.82*+
   1920x1080     60.00    59.94    50.00
   1440x900      74.98    59.89
   1280x1024     75.02    60.02
   1280x720      60.00    59.94    50.00
   1024x768      75.03    70.07    60.00
   800x600       75.00    72.19    60.32    56.25
   800x450       60.01
   720x576       50.00
   720x480       59.94
   640x480       75.00    72.81    59.94
```

---

## Result

The display was successfully detected by Linux.

Key confirmed values:

| Item | Result |
|---|---|
| Active display output | `DP-1` |
| Display status | Connected |
| Primary display | Yes |
| Current resolution | `1024x600` |
| Native/preferred mode | `1024x600` |
| Active graphical session | `DISPLAY=:1` |

The line below confirms that the display is connected and running as the primary screen:

```text
DP-1 connected primary 1024x600+0+0
```

The line below confirms that `1024x600` is both the active and preferred display mode:

```text
1024x600 59.82*+
```

---

## Debugging Notes

The initial `DISPLAY=:0` test failed because the active X11 display socket was not `X0`.

The system exposed:

```text
/tmp/.X11-unix/X1
```

So the correct display environment variable is:

```bash
export DISPLAY=:1
```

This is useful when launching graphical tools or future face-display applications from SSH.

---

## Current Status

Completed:

```text
Physical display connection
Linux display detection
Correct display output identified
Correct native resolution confirmed
Correct X11 display session identified
Touchscreen input test working
```

Not completed yet:

```text

GUI window launch confirmation from SSH
ROS2 face display node
Automatic startup of Cutie face application
```

---

## Next Steps

1. Confirm whether graphical windows can be launched onto the display from SSH.
2. Create the first Cutie face display application.
4. Wrap the face display application into a ROS2 node.
5. Configure automatic startup for the Cutie face application.