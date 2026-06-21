# USB Speaker Audio Bring-Up

This document records the USB speaker bring-up for Cutie.

## Hardware

* Jetson Orin Nano
* GEMBIRD Buildwin Media-Player USB speaker

## Device Detection

The speaker was detected with:

```bash
lsusb
```

Detected device:

```text
Bus 001 Device 009: ID 1908:2220 GEMBIRD Buildwin Media-Player
```

ALSA playback devices were checked with:

```bash
aplay -L
```

The speaker appeared as:

```text
CARD=Device
USB2.0 Device, USB Audio
```

Useful ALSA output address:

```text
plughw:CARD=Device,DEV=0
```

## Test Method 1: Speaker Test

```bash
speaker-test -D plughw:CARD=Device,DEV=0 -c 2 -t wav
```

Result: speaker played left/right test audio.

## Test Method 2: WAV Playback

```bash
aplay -D plughw:CARD=Device,DEV=0 /usr/share/sounds/alsa/Front_Center.wav
```

Result: speaker played the WAV file successfully.

## Final Output Device

```text
plughw:CARD=Device,DEV=0
```

## Cutie Mapping

```text
cutie_mouth -> GEMBIRD Buildwin Media-Player USB speaker
```

## Status

USB speaker bring-up completed successfully.
